"""Crawls the local demo-sites fixtures: deterministic content used for the
demo fallback and E2E tests (ADR-0017). Pages are fetched with the same browser
pipeline as the open web so screenshots and computed styles are captured too.
"""
from collections.abc import Iterator

import httpx

from .open_web import OpenWebCollector


class DemoSitesCollector(OpenWebCollector):
    name = "demo_sites"

    def __init__(self, config: dict):
        super().__init__({**config, "respect_robots": False})

    def discover(self) -> Iterator[str]:
        base_url = self.config.get("base_url", "http://demo-sites:8080")
        index = httpx.get(f"{base_url}/index.json", timeout=10)
        index.raise_for_status()
        for page in index.json():
            yield base_url + page
