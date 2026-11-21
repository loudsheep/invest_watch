"""M1 - finfluencers and third parties advertising a registered investment firm
without disclosure. Affiliate-link / promo-code / missing-#reklama detection
plus the embedding classifier score are combined into one finding candidate.
"""
import re

AFFILIATE_PATTERNS = [
    r"[?&](ref|aff|affid|partner)=[\w-]+",
    r"utm_[a-z]+=[\w-]+",
    r"z\s+kod(em|u)\s+[\w-]{3,20}",
    r"kod\s+promocyjny[:\s]+[\w-]{3,20}",
]

DISCLOSURE_PATTERNS = [r"#reklama", r"#współpraca", r"#wspolpraca", r"materiał sponsorowany"]


def detect_affiliate_evidence(text: str) -> list[str]:
    evidence = []
    for pattern in AFFILIATE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            evidence.append(match.group(0))
    return evidence


def has_disclosure(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in DISCLOSURE_PATTERNS)


def extract_promo_code(text: str) -> str | None:
    match = re.search(r"kod\s+promocyjny[:\s]+([\w-]{3,20})", text, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"z\s+kod(?:em|u)\s+([\w-]{3,20})", text, re.IGNORECASE)
    return match.group(1) if match else None


def build_details(text: str) -> dict:
    affiliate_evidence = detect_affiliate_evidence(text)
    disclosed = has_disclosure(text)
    return {
        "affiliate_evidence": affiliate_evidence,
        "has_cooperation_disclosure": disclosed,
        "promo_code": extract_promo_code(text),
        "undisclosed_cooperation": bool(affiliate_evidence) and not disclosed,
    }
