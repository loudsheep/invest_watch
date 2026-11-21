"""YouTube collector via yt-dlp: pulls descriptions and transcripts without
needing cookies or a logged-in session. TikTok shares the same yt-dlp pipeline.
"""
from collections.abc import Iterator

import yt_dlp
from investwatch_common.schemas import RawDocument

from .base import Collector


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
            "subtitleslangs": ["pl"],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(candidate, download=False)
        except Exception:
            return None

        transcript = ""
        for sub in (info.get("automatic_captions", {}).get("pl") or []):
            if sub.get("ext") == "json3":
                transcript = "(transcript available, not parsed in this pass)"
                break

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
