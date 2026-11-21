"""Name normalization shared by the registry providers and the entity matcher."""
import re
import unicodedata

LEGAL_FORMS = [
    r"spółka akcyjna", r"spolka akcyjna", r"spółka z ograniczoną odpowiedzialnością",
    r"sp\.? ?z ?o\.? ?o\.?", r"s\.? ?a\.?", r"s\.? ?a\.? ?k", r"sp\.? ?k\.?", r"ltd\.?", r"limited", r"plc",
    r"gmbh", r"ag", r"a/s", r"uab", r"s\.? ?r\.? ?l\.?", r"b\.? ?v\.?", r"ab", r"oy", r"inc\.?", r"llc",
    r"s\.? ?e\.?", r"n\.? ?v\.?", r"as", r"sas", r"spa", r"s\.? ?p\.? ?a\.?",
]
_LEGAL_RE = re.compile(r"\b(?:" + "|".join(LEGAL_FORMS) + r")(?=[\s,.]|$)", re.IGNORECASE)
GENERIC_WORDS = {
    "dom", "maklerski", "maklerskie", "inwestycyjny", "inwestycyjne", "bank", "banku", "securities", "investment",
    "investments", "management", "asset", "capital", "group", "financial", "finance", "services", "service", "trading",
    "markets", "market", "europe", "european", "holding", "partners", "polska", "polish", "international", "global",
    "brokers", "broker", "invest", "wealth", "advisory", "consulting", "fund", "funds", "eu", "i", "and", "oraz",
}
_DEPARTMENT_RE = re.compile(r"\s+(?:b ?iuro maklerskie|departament maklerski)\b.*$", re.IGNORECASE)
_SITE_RE = re.compile(r"\s+(?:z siedzibą|prowadzący działalność|działający)\b.*$", re.IGNORECASE)


def strip_ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def normalize(name: str) -> str:
    """Lowercase, accent-free, legal form and punctuation removed."""
    text = _SITE_RE.sub("", name)
    text = strip_ascii(_LEGAL_RE.sub(" ", text.lower()))
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def short_alias(name: str) -> str | None:
    """Display-name alias without the legal form; None when too generic to be a safe alias."""
    text = _SITE_RE.sub("", name)
    text = re.sub(r"\(.*?\)", " ", text)
    text = _DEPARTMENT_RE.sub("", text)
    text = _LEGAL_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", re.sub(r"[,;]+", " ", text)).strip(" .-")
    words = text.split()
    distinctive = [w for w in words if w.lower() not in GENERIC_WORDS]
    return text if len(words) >= 2 and len(text) >= 10 and distinctive else None
