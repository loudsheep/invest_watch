import socket

import pytest
from app.url_guard import BlockedUrlError, ensure_fetchable


def _resolve_to(monkeypatch, address: str) -> None:
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, 443))],
    )


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.com/x", "javascript:alert(1)", "http://"])
def test_rejects_non_http_urls(url):
    with pytest.raises(BlockedUrlError):
        ensure_fetchable(url)


@pytest.mark.parametrize("address", ["127.0.0.1", "10.0.0.5", "172.18.0.3", "192.168.1.1", "169.254.169.254", "::1"])
def test_rejects_hosts_resolving_to_non_public_addresses(monkeypatch, address):
    _resolve_to(monkeypatch, address)
    with pytest.raises(BlockedUrlError):
        ensure_fetchable("http://internal.example/")


def test_accepts_public_address(monkeypatch):
    _resolve_to(monkeypatch, "93.184.216.34")
    ensure_fetchable("https://example.com/oferta")


def test_allows_demo_sandbox_host_without_resolving(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("allowlisted host must not be resolved")

    monkeypatch.setattr(socket, "getaddrinfo", fail)
    ensure_fetchable("http://demo-sites:8080/landing-aurum-cfd")
