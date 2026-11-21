"""Open web collector: SearXNG for discovery, Playwright for fetch + screenshot +
computed styles (needed for M2 visual prominence), httpx as a cheap fallback when
Playwright is not required. Respects robots.txt by default (ADR per CONCEPT ch.9).
"""
from collections.abc import Iterator
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import httpx
from investwatch_common.config import settings
from investwatch_common.logging import get_logger
from investwatch_common.schemas import RawDocument
from playwright.sync_api import sync_playwright

from ..proxy_pool import build_default_pool
from ..user_agents import random_profile
from .base import Collector

logger = get_logger(__name__)

PROFIT_CLAIM_HINTS = ["zysk", "zarabiaj", "zwrot", "rentowność", "rentownosc"]

RISK_WARNING_SELECTOR_HINTS = [
    "disclaimer", "risk", "ryzyk", "ostrzezenie", "ostrzeżenie", "cfd-warning",
]


class OpenWebCollector(Collector):
    name = "open_web"

    def __init__(self, config: dict):
        super().__init__(config)
        self.proxy_pool = build_default_pool()
        self.respect_robots = config.get("respect_robots", True)

    def discover(self) -> Iterator[str]:
        queries = self.config.get("queries", [])
        for query in queries:
            try:
                resp = httpx.get(
                    f"{settings.searxng_url}/search",
                    params={"q": query, "format": "json"},
                    timeout=15,
                )
                resp.raise_for_status()
                for result in resp.json().get("results", [])[:20]:
                    yield result["url"]
            except httpx.HTTPError as exc:
                logger.warning("searxng_query_failed", query=query, error=str(exc))

    def _allowed_by_robots(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        try:
            parsed_robots_url = urljoin(url, "/robots.txt")
            parser = RobotFileParser()
            parser.set_url(parsed_robots_url)
            parser.read()
            return parser.can_fetch("*", url)
        except Exception:
            return True

    def fetch(self, candidate: str) -> RawDocument | None:
        if not self._allowed_by_robots(candidate):
            logger.info("robots_disallowed", url=candidate)
            return None

        proxy_url = self.proxy_pool.get_proxy(candidate)
        profile = random_profile()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    proxy={"server": proxy_url} if proxy_url else None,
                )
                page = browser.new_page(
                    user_agent=profile["user_agent"],
                    extra_http_headers=profile["headers"],
                )
                page.goto(candidate, timeout=20000, wait_until="networkidle")
                html = page.content()
                title = page.title()
                text = page.inner_text("body")
                screenshot = page.screenshot(full_page=True)
                computed_styles = self._extract_risk_warning_styles(page)
                author = page.evaluate("document.querySelector('meta[name=author]')?.content || null")
                browser.close()

            if proxy_url:
                self.proxy_pool.report_success(proxy_url)

            return RawDocument(
                source_name="open_web",
                url=candidate,
                platform="web",
                title=title,
                author=author,
                content=text,
                html=html,
                screenshot_png=screenshot,
                computed_styles=computed_styles,
            )
        except Exception as exc:
            if proxy_url:
                self.proxy_pool.report_failure(proxy_url)
            logger.warning("open_web_fetch_failed", url=candidate, error=str(exc))
            return None

    @staticmethod
    def _extract_risk_warning_styles(page) -> dict:
        """Grabs font-size/color for the smallest elements that look like risk
        disclaimers and for profit claims, so M2 can compare the two."""
        script = """
        ([riskHints, profitHints]) => {
            const collect = (hints) => {
                const results = [];
                for (const el of document.querySelectorAll('body *')) {
                    const txt = (el.innerText || '').toLowerCase();
                    if (!txt || txt.length > 2000 || !hints.some(h => txt.includes(h))) continue;
                    // keep leaf-most matches only
                    if ([...el.children].some(c => hints.some(h => (c.innerText || '').toLowerCase().includes(h)))) continue;
                    const style = window.getComputedStyle(el);
                    results.push({
                        tag: el.tagName,
                        text: (el.innerText || '').trim().slice(0, 160),
                        fontSize: style.fontSize,
                        color: style.color,
                        backgroundColor: style.backgroundColor,
                        textLength: txt.length,
                    });
                }
                return results.slice(0, 10);
            };
            return { risk_warning_elements: collect(riskHints), profit_claim_elements: collect(profitHints) };
        }
        """
        try:
            return page.evaluate(script, [RISK_WARNING_SELECTOR_HINTS, PROFIT_CLAIM_HINTS])
        except Exception:
            return {}
