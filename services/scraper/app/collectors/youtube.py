"""YouTube collector via yt-dlp: pulls descriptions and transcripts without
needing cookies or a logged-in session. TikTok shares the same yt-dlp pipeline.
"""
import json
import re
from collections.abc import Iterator

import httpx
import yt_dlp
from investwatch_common.logging import get_logger
from investwatch_common.schemas import RawDocument

from .base import Collector

logger = get_logger(__name__)

CAPTION_LANGUAGES = ("pl", "pl-orig", "en", "en-orig")
CAPTION_FORMATS = ("json3", "vtt")
MAX_TRANSCRIPT_CHARS = 20000


def parse_json3(payload: str) -> str:
    events = json.loads(payload).get("events", [])
    pieces = ("".join(seg.get("utf8", "") for seg in event.get("segs", [])) for event in events)
    return re.sub(r"\s+", " ", " ".join(pieces)).strip()


def parse_vtt(payload: str) -> str:
    lines = []
    for line in payload.splitlines():
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or "-->" in line:
            continue
        if not lines or lines[-1] != line:
            lines.append(line)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def _caption_track(info: dict) -> dict | None:
    """Manual captions first, then the automatic track in the video's original language.
    Machine-translated tracks (`tlang=` in the URL) are skipped: YouTube rate-limits them."""
    for source in ("subtitles", "automatic_captions"):
        tracks = info.get(source) or {}
        original_languages = [key for key in tracks if key.endswith("-orig") and key not in CAPTION_LANGUAGES]
        for language in (*CAPTION_LANGUAGES, *original_languages):
            for fmt in CAPTION_FORMATS:
                for track in tracks.get(language) or []:
                    if track.get("ext") == fmt and track.get("url") and "tlang=" not in track["url"]:
                        return track
    return None


def fetch_transcript(info: dict) -> str:
    """Caption text (manual captions first, then automatic) in Polish or English; empty when none."""
    track = _caption_track(info)
    if track is None:
        return ""
    try:
        response = httpx.get(track["url"], timeout=20, follow_redirects=True)
        response.raise_for_status()
        parser = parse_json3 if track["ext"] == "json3" else parse_vtt
        return parser(response.text)[:MAX_TRANSCRIPT_CHARS]
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("transcript_fetch_failed", error=str(exc))
        return ""


class YouTubeCollector(Collector):
    name = "youtube"
    platform = "youtube"

    def discover(self) -> Iterator[str]:
        search_terms = self.config.get("search_terms", [])
        seed_channels = self.config.get("seed_channels", [])

        ydl_opts = {"quiet": True, "extract_flat": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for term in search_terms:
                try:
                    result = ydl.extract_info(f"ytsearch10:{term}", download=False)
                    for entry in result.get("entries", []):
                        yield f"https://www.youtube.com/watch?v={entry['id']}"
                except Exception:
                    continue
            for channel_url in seed_channels:
                try:
                    result = ydl.extract_info(channel_url, download=False)
                    for entry in result.get("entries", [])[:10]:
                        yield f"https://www.youtube.com/watch?v={entry['id']}"
                except Exception:
                    continue

    def fetch(self, candidate: str) -> RawDocument | None:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["pl", "en"],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(candidate, download=False)
        except Exception:
            return None

        transcript = fetch_transcript(info)

        content = "\n".join(filter(None, [info.get("description", ""), transcript]))

        return RawDocument(
            source_name=self.name,
            url=candidate,
            platform=self.platform,
            author=info.get("uploader"),
            title=info.get("title"),
            content=content,
            extra={"video_id": info.get("id"), "channel_id": info.get("channel_id")},
        )


class TikTokCollector(YouTubeCollector):
    """Public TikTok profiles and videos through yt-dlp's TikTok extractor."""

    name = "tiktok"
    platform = "tiktok"

    def discover(self) -> Iterator[str]:
        ydl_opts = {"quiet": True, "extract_flat": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for profile_url in self.config.get("seed_profiles", []):
                try:
                    result = ydl.extract_info(profile_url, download=False)
                    for entry in (result.get("entries") or [])[:10]:
                        if entry.get("url"):
                            yield entry["url"]
                except Exception:
                    continue
