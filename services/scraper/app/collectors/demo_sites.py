"""Crawls the local demo-sites fixtures: deterministic content used for the
demo fallback and E2E tests (ADR-0017), reached through the same Collector
interface so the pipeline doesn't need to special-case it.
"""
from collections.abc import Iterator

import httpx
from investwatch_common.schemas import RawDocument

from .base import Collector

KNOWN_PAGES = [
    "/finfluencer-aurum",
    "/landing-aurum-cfd",
    "/shadow-advisory-pwm",
]


class DemoSitesCollector(Collector):
    name = "demo_sites"

    def discover(self) -> Iterator[str]:
        base_url = self.config.get("base_url", "http://demo-sites:8080")
        for page in KNOWN_PAGES:
            yield base_url + page

    def fetch(self, candidate: str) -> RawDocument | None:
        try:
            resp = httpx.get(candidate, timeout=10)
            resp.raise_for_status()
        except httpx.HTTPError:
            return None

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        title = soup.title.string if soup.title else None

        return RawDocument(
            source_name="demo_sites",
            url=candidate,
            platform="web",
            title=title,
            content=text,
            html=resp.text,
        )
