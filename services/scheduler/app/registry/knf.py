"""Providers for the public KNF lists: investment firms, banks with brokerage,
foreign branches, notified foreign firms (the Polish view of the ESMA/MiFID
passport register) and the public warnings list."""
import re
import time
from collections.abc import Callable, Iterator
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from investwatch_common.logging import get_logger

from .names import short_alias

logger = get_logger(__name__)

BASE = "https://www.knf.gov.pl"
FIRMS = f"{BASE}/podmioty/Podmioty_rynku_kapitalowego/Firmy_inwestycyjne_i_Agenci_firm_inwestycyjnych"
WARNINGS_URL = f"{BASE}/dla_konsumenta/ostrzezenia_publiczne"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; InvestWatch registry sync)"}
MAX_PAGES = 200
PAGE_DELAY_SECONDS = 0.3

URL_RE = re.compile(r"https?://[^\s,;)]+", re.IGNORECASE)
KRS_RE = re.compile(r"KRS\s*(\d{10})", re.IGNORECASE)
NIP_RE = re.compile(r"NIP\s*([\d-]{10,13})", re.IGNORECASE)


def _domain(url: str) -> str | None:
    host = urlparse(url if "://" in url else f"http://{url}").hostname
    return host.removeprefix("www.") if host else None


def _record(name: str, entity_type: str, authorized: bool, source: str, **extra) -> dict:
    aliases = [alias] if (alias := short_alias(name)) and alias != name else []
    return {
        "name": name,
        "aliases": aliases,
        "type": entity_type,
        "authorized": authorized,
        "source": source,
        **extra,
    }


def _get(client: httpx.Client, url: str) -> str:
    response = client.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    response.raise_for_status()
    return response.text


def _paged_tables(client: httpx.Client, url: str) -> Iterator[dict[str, str]]:
    """Yields one dict per registry table; stops when a page repeats (the site clamps past the last page)."""
    first_names: set[str] = set()
    for page in range(1, MAX_PAGES + 1):
        soup = BeautifulSoup(_get(client, f"{url}?page={page}"), "html.parser")
        tables = soup.select("table.rounded-default")
        rows = []
        for table in tables:
            row = {
                th.get_text(" ", strip=True): td.get_text("\n", strip=True)
                for tr in table.find_all("tr")
                if (th := tr.find("th")) and (td := tr.find("td"))
            }
            if row:
                rows.append(row)
        key = next(iter(rows[0].values()), "") if rows else ""
        if not rows or key in first_names:
            return
        first_names.add(key)
        yield from rows
        time.sleep(PAGE_DELAY_SECONDS)


def _name(row: dict[str, str]) -> str | None:
    return row.get("Nazwa") or row.get("Nazwa podmiotu")


NUMBERING_RE = re.compile(r"^\s*\d+\s*[.)]\s*")


def _lines(cell: str | None) -> list[str]:
    """A table cell can hold several entities, one per line, optionally numbered."""
    lines = (NUMBERING_RE.sub("", line).strip(" „”\"\u00a0,;") for line in (cell or "").splitlines())
    return [line for line in lines if len(line) >= 3]


def _firms(
    url: str, entity_type: str, source: str, first_line_only: bool = False
) -> Callable[[httpx.Client], list[dict]]:
    def fetch(client: httpx.Client) -> list[dict]:
        records = []
        for row in _paged_tables(client, url):
            names = _lines(_name(row))
            for name in names[:1] if first_line_only else names:
                records.append(_record(name, entity_type, True, source))
        return records

    return fetch


def _warnings(client: httpx.Client) -> list[dict]:
    soup = BeautifulSoup(_get(client, WARNINGS_URL), "html.parser")
    records = []
    for tr in soup.find_all("tr"):
        cells = [td.get_text("\n", strip=True) for td in tr.find_all("td")]
        if len(cells) < 3 or not re.fullmatch(r"\d+\s*\.", cells[0].strip()):
            continue
        names, ident = _lines(cells[1]), cells[2]
        single = len(names) == 1
        for line in names:
            urls = URL_RE.findall(line) + (URL_RE.findall(ident) if single else [])
            name = re.split(r",?\s*(?:prowadzący|działając\w*|działający|administrator)\b", line, maxsplit=1)[0].strip(" ,")
            records.append(
                _record(
                    name,
                    "unauthorized_entity",
                    False,
                    "knf_warning",
                    krs=(m.group(1) if single and (m := KRS_RE.search(ident)) else None),
                    nip=(re.sub(r"\D", "", m.group(1)) if single and (m := NIP_RE.search(ident)) else None),
                    domains=sorted({d for u in urls if (d := _domain(u))}),
                )
            )
    return records


PROVIDERS: dict[str, Callable[[httpx.Client], list[dict]]] = {
    "knf_investment_firms": _firms(f"{FIRMS}/domy_maklerskie", "investment_firm", "knf"),
    "knf_brokerage_banks": _firms(
        f"{FIRMS}/Banki_prowadzace_dzialalnosc_maklerska", "investment_firm", "knf", first_line_only=True
    ),
    "knf_foreign_branches": _firms(
        f"{FIRMS}/notyfikowane_firmy_inwestycyjne_oddzialy", "foreign_investment_firm", "knf_branch"
    ),
    "knf_foreign_notified": _firms(
        f"{FIRMS}/notyfikowane_zagraniczne_firmy_inwestycyjne", "foreign_investment_firm", "esma_passport"
    ),
    "knf_warnings": _warnings,
}
