"""SSRF guard: the browser only fetches public http(s) addresses, so a submitted URL
cannot read local files or reach services on the internal network. Hosts listed in
FETCH_ALLOWED_PRIVATE_HOSTS (the demo-sites sandbox) are the only private exception."""
import ipaddress
import socket
from urllib.parse import urlparse

from investwatch_common.config import settings


class BlockedUrlError(ValueError):
    pass


def ensure_fetchable(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise BlockedUrlError(f"unsupported URL: {url}")
    if parsed.hostname in settings.fetch_allowed_private_hosts:
        return
    try:
        resolved = socket.getaddrinfo(parsed.hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise BlockedUrlError(f"cannot resolve host: {parsed.hostname}") from exc
    for *_, sockaddr in resolved:
        address = ipaddress.ip_address(sockaddr[0].split("%")[0])
        if not address.is_global:
            raise BlockedUrlError(f"non-public address for host: {parsed.hostname}")
