"""M2 - risk-disclosure compliance, driven entirely by config/m2_rules.yaml
(ADR-0009). Each criterion carries its legal basis so the UI can show it next
to the finding. Changing the rules means editing YAML, not this file.
"""
import re
from functools import lru_cache
from pathlib import Path

import yaml

RULES_PATH = Path("/app/config/m2_rules.yaml")

PROFIT_HINTS = ["zysk", "zarabiaj", "zwrot", "wysoka rentowność", "wysoki zwrot"]
RISK_HINTS = ["ryzyk", "strat", "mozesz stracic", "możesz stracić"]


@lru_cache
def load_rules() -> dict:
    return yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))


def _regex_criterion_score(text: str, criterion: dict) -> tuple[float, str | None]:
    for pattern in criterion.get("patterns", []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return 1.0, match.group(0)
    return 0.0, None


def _profit_risk_balance_score(text: str, criterion: dict) -> tuple[float, str | None]:
    lowered = text.lower()
    profit_count = sum(lowered.count(h) for h in PROFIT_HINTS)
    risk_count = sum(lowered.count(h) for h in RISK_HINTS)
    if profit_count == 0:
        return 1.0, None
    ratio = profit_count / max(risk_count, 1)
    max_ratio = criterion.get("max_profit_to_risk_ratio", 3.0)
    score = 1.0 if ratio <= max_ratio else max(0.0, 1 - (ratio - max_ratio) / max_ratio)
    return score, f"profit_mentions={profit_count} risk_mentions={risk_count} ratio={ratio:.1f}"


def _visual_prominence_score(computed_styles: dict | None, criterion: dict) -> tuple[float, str | None]:
    if not computed_styles or not computed_styles.get("risk_warning_elements"):
        return 0.0, "no risk-warning element detected on page"

    elements = computed_styles["risk_warning_elements"]
    font_sizes = []
    for el in elements:
        try:
            font_sizes.append(float(str(el.get("fontSize", "0px")).replace("px", "")))
        except ValueError:
            continue

    if not font_sizes:
        return 0.3, "risk warning present but font size unreadable"

    avg_font = sum(font_sizes) / len(font_sizes)
    # Without a measured profit-claim font size (would need separate selector
    # pass), fall back to an absolute-legibility heuristic: assume ~16px body
    # text is "normal" and anything meaningfully smaller looks suppressed.
    score = min(1.0, avg_font / 16.0)
    return score, f"avg_risk_warning_font_px={avg_font:.1f}"


def evaluate(text: str, computed_styles: dict | None = None) -> dict:
    rules = load_rules()
    criteria_results = []
    total_score = 0.0
    total_weight = 0.0

    for criterion in rules["criteria"]:
        detector = criterion["detector"]
        if detector == "regex":
            score, evidence = _regex_criterion_score(text, criterion)
        elif detector == "classifier":
            score, evidence = _profit_risk_balance_score(text, criterion)
        elif detector == "visual":
            score, evidence = _visual_prominence_score(computed_styles, criterion)
        else:
            score, evidence = 0.0, None

        weight = criterion["weight"]
        total_score += score * weight
        total_weight += weight

        criteria_results.append(
            {
                "id": criterion["id"],
                "description": criterion["description"],
                "legal_basis": criterion["legal_basis"],
                "score": score,
                "weight": weight,
                "evidence": evidence,
            }
        )

    # Final score here is "risk of non-compliance": invert compliance score.
    compliance_score = total_score / total_weight if total_weight else 0.0
    return {
        "compliance_score": compliance_score,
        "risk_score": 1 - compliance_score,
        "criteria": criteria_results,
    }
