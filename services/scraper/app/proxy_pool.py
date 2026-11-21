"""ProxyPool (ADR-0015): round-robin / sticky-per-domain proxy selection with a
circuit breaker. Empty PROXY_URLS means direct connection - safe default for
environments with no proxies configured.
"""
import itertools
import threading
import time
from urllib.parse import urlparse

from investwatch_common.config import settings
from investwatch_common.logging import get_logger
from investwatch_common.redis_client import PROXY_CIRCUIT_KEY, PROXY_FAILURES_KEY, get_redis

logger = get_logger(__name__)

FAILURE_THRESHOLD = 3
COOLDOWN_SECONDS = 60


class ProxyPool:
    def __init__(self, proxy_urls: list[str]):
        self.proxy_urls = proxy_urls
        self._cycle = itertools.cycle(proxy_urls) if proxy_urls else None
        self._sticky: dict[str, str] = {}
        self._failures: dict[str, int] = {url: 0 for url in proxy_urls}
        self._disabled_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def _is_available(self, proxy_url: str) -> bool:
        until = self._disabled_until.get(proxy_url, 0)
        return time.time() >= until

    def get_proxy(self, url: str) -> str | None:
        if not self.proxy_urls:
            return None

        domain = urlparse(url).netloc
        with self._lock:
            sticky = self._sticky.get(domain)
            if sticky and self._is_available(sticky):
                return sticky

            for _ in range(len(self.proxy_urls)):
                candidate = next(self._cycle)
                if self._is_available(candidate):
                    self._sticky[domain] = candidate
                    return candidate
        logger.warning("proxy_pool_exhausted", domain=domain)
        return None

    def report_failure(self, proxy_url: str) -> None:
        with self._lock:
            self._failures[proxy_url] = self._failures.get(proxy_url, 0) + 1
            get_redis().hincrby(PROXY_FAILURES_KEY, proxy_url, 1)
            if self._failures[proxy_url] >= FAILURE_THRESHOLD:
                self._disabled_until[proxy_url] = time.time() + COOLDOWN_SECONDS
                self._failures[proxy_url] = 0
                get_redis().hset(PROXY_CIRCUIT_KEY, proxy_url, self._disabled_until[proxy_url])
                logger.warning("proxy_circuit_open", proxy=proxy_url, cooldown=COOLDOWN_SECONDS)

    def report_success(self, proxy_url: str) -> None:
        with self._lock:
            self._failures[proxy_url] = 0


def build_default_pool() -> ProxyPool:
    urls = [u.strip() for u in settings.proxy_urls.split(",") if u.strip()]
    return ProxyPool(urls)
