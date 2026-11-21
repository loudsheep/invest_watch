"""Open web collector: SearXNG for discovery, Playwright for fetch + screenshot +
computed styles (needed for M2 visual prominence), httpx as a cheap fallback when
Playwright is not required. Respects robots.txt by default (ADR per CONCEPT ch.9).
"""
from collections.abc import Iterator
from urllib.parse import unquote, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from investwatch_common.config import settings
from investwatch_common.logging import get_logger
from investwatch_common.schemas import RawDocument
from playwright.sync_api import sync_playwright

from ..proxy_pool import build_default_pool
from ..url_guard import BlockedUrlError, ensure_fetchable
from ..user_agents import random_profile
from .base import Collector

logger = get_logger(__name__)

PROFIT_CLAIM_HINTS = ["zysk", "zarabiaj", "zwrot", "rentowność", "rentownosc"]

RISK_WARNING_SELECTOR_HINTS = [
    "disclaimer", "risk", "ryzyk", "ostrzezenie", "ostrzeżenie", "cfd-warning",
]


HISTORICAL_HINTS = ["wyniki historyczne", "wyniki osiągnięte", "stopa zwrotu", "osiągnęli", "zwrot z ostatnich"]

VIEWPORTS = [("tablet", 768, 1024), ("telefon", 375, 812)]

STYLE_EXTRACTION_SCRIPT = """
([riskHints, profitHints, historicalHints]) => {
    const parseAlpha = (c) => {
        const m = c.match(/rgba?\\(([^)]+)\\)/);
        if (!m) return 1;
        const parts = m[1].split(/[,/ ]+/).filter(Boolean);
        return parts.length > 3 ? parseFloat(parts[3]) : 1;
    };
    const effectiveBackground = (el) => {
        for (let node = el; node; node = node.parentElement) {
            const bg = window.getComputedStyle(node).backgroundColor;
            if (parseAlpha(bg) > 0.05) return bg;
        }
        return 'rgb(255, 255, 255)';
    };
    const effectiveOpacity = (el) => {
        let o = 1;
        for (let node = el; node; node = node.parentElement) o *= parseFloat(window.getComputedStyle(node).opacity || '1');
        return o;
    };
    const collect = (hints) => {
        const results = [];
        for (const el of document.querySelectorAll('body *')) {
            const txt = (el.innerText || '').toLowerCase();
            if (!txt || txt.length > 2000 || !hints.some(h => txt.includes(h))) continue;
            if ([...el.children].some(c => hints.some(h => (c.innerText || '').toLowerCase().includes(h)))) continue;
            const style = window.getComputedStyle(el);
            const box = el.getBoundingClientRect();
            results.push({
                tag: el.tagName,
                rect: { x: box.left + window.scrollX, y: box.top + window.scrollY, w: box.width, h: box.height },
                text: (el.innerText || '').trim().slice(0, 160),
                fontSize: style.fontSize,
                color: style.color,
                backgroundColor: style.backgroundColor,
                effectiveBackground: effectiveBackground(el),
                opacity: effectiveOpacity(el),
                inFooter: !!el.closest('footer, [class*=legal], [id*=legal], [class*=footnote], [class*=przypis], sup'),
                clipped: el.scrollWidth > el.clientWidth + 1 && ['hidden', 'clip'].includes(style.overflowX) || style.textOverflow === 'ellipsis',
                textLength: txt.length,
            });
        }
        return results.slice(0, 10);
    };
    let maxFont = 0;
    for (const el of document.querySelectorAll('body *')) {
        const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
        if (!own) continue;
        maxFont = Math.max(maxFont, parseFloat(window.getComputedStyle(el).fontSize) || 0);
    }
    const riskLinks = [...document.querySelectorAll('a, button, summary')]
        .map(a => (a.innerText || '').trim())
        .filter(t => t && /ryzyk|ostrze/i.test(t))
        .slice(0, 5);
    const textBlocks = [];
    for (const el of document.querySelectorAll('body *')) {
        const txt = (el.innerText || '').trim();
        if (txt.length < 12 || txt.length > 400) continue;
        if ([...el.children].some(c => (c.innerText || '').trim().length >= 12)) continue;
        const box = el.getBoundingClientRect();
        if (box.width === 0 || box.height === 0) continue;
        textBlocks.push({ text: txt, rect: { x: box.left + window.scrollX, y: box.top + window.scrollY, w: box.width, h: box.height } });
        if (textBlocks.length >= 250) break;
    }
    return {
        text_blocks: textBlocks,
        risk_warning_elements: collect(riskHints),
        profit_claim_elements: collect(profitHints),
        historical_elements: collect(historicalHints),
        risk_links: riskLinks,
        max_font_px: maxFont,
    };
}
"""


def _playwright_proxy(proxy_url: str | None) -> dict | None:
    """Chromium ignores credentials embedded in the proxy URL, so they are passed separately."""
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    proxy = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
    if parsed.username:
        proxy["username"] = unquote(parsed.username)
        proxy["password"] = unquote(parsed.password or "")
    return proxy


class OpenWebCollector(Collector):
    name = "open_web"

    def __init__(self, config: dict):
        super().__init__(config)
        self.proxy_pool = build_default_pool()
        self.respect_robots = config.get("respect_robots", True)

    def discover(self) -> Iterator[str]:
        yield from self.config.get("seed_urls", [])
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
        try:
            ensure_fetchable(candidate)
        except BlockedUrlError as exc:
            logger.warning("fetch_blocked", url=candidate, reason=str(exc))
            return None

        if not self._allowed_by_robots(candidate):
            logger.info("robots_disallowed", url=candidate)
            return None

        proxy_url = self.proxy_pool.get_proxy(candidate)
        profile = random_profile()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    proxy=_playwright_proxy(proxy_url),
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
                computed_styles["viewports"], device_screenshots = self._extract_viewport_styles(page)
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
                device_screenshots=device_screenshots,
                computed_styles=computed_styles,
            )
        except Exception as exc:
            if proxy_url:
                self.proxy_pool.report_failure(proxy_url)
            logger.warning("open_web_fetch_failed", url=candidate, error=str(exc))
            return None

    @staticmethod
    def _extract_risk_warning_styles(page) -> dict:
        """Collects risk-warning and profit-claim element styles (font, colors,
        opacity, footer placement, clipping) plus risk links and historical-result
        elements, so M2 can score size, contrast, visibility and dominance."""
        try:
            return page.evaluate(
                STYLE_EXTRACTION_SCRIPT, [RISK_WARNING_SELECTOR_HINTS, PROFIT_CLAIM_HINTS, HISTORICAL_HINTS]
            )
        except Exception:
            return {}

    def _extract_viewport_styles(self, page) -> tuple[dict, dict[str, bytes]]:
        """Risk-warning styles and a full-page screenshot per tablet/phone viewport."""
        viewports: dict[str, dict] = {}
        screenshots: dict[str, bytes] = {}
        for name, width, height in VIEWPORTS:
            try:
                page.set_viewport_size({"width": width, "height": height})
                page.wait_for_timeout(150)
                data = self._extract_risk_warning_styles(page)
                viewports[name] = {"risk_warning_elements": data.get("risk_warning_elements", [])}
                screenshots[name] = page.screenshot(full_page=True)
            except Exception:
                continue
        return viewports, screenshots
