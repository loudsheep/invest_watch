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


def _font_px(elements: list[dict], pick) -> tuple[float, dict] | None:
    sized = []
    for el in elements:
        try:
            sized.append((float(str(el.get("fontSize", "")).replace("px", "")), el))
        except ValueError:
            continue
    return pick(sized, key=lambda item: item[0]) if sized else None


def font_comparison(computed_styles: dict | None) -> dict | None:
    """Smallest risk-warning font vs largest profit-claim font on the page."""
    if not computed_styles:
        return None
    risk = _font_px(computed_styles.get("risk_warning_elements") or [], min)
    profit = _font_px(computed_styles.get("profit_claim_elements") or [], max)
    if risk is None:
        return None
    result = {"risk_px": risk[0], "risk_text": risk[1].get("text")}
    if profit is not None:
        result.update(
            profit_px=profit[0], profit_text=profit[1].get("text"), ratio=round(risk[0] / profit[0], 2)
        )
    return result


def _visual_prominence_score(computed_styles: dict | None, criterion: dict) -> tuple[float, str | None]:
    comparison = font_comparison(computed_styles)
    if comparison is None:
        return 0.0, "no risk-warning element detected on page"

    if "ratio" not in comparison:
        # No profit claim measured: absolute-legibility heuristic against ~16px body text.
        return min(1.0, comparison["risk_px"] / 16.0), f"risk_warning_font_px={comparison['risk_px']:.1f}"

    min_ratio = criterion.get("min_font_ratio", 0.8)
    score = min(1.0, comparison["ratio"] / min_ratio)
    return score, f"risk_font={comparison['risk_px']:.0f}px profit_font={comparison['profit_px']:.0f}px ratio={comparison['ratio']}"


def evaluate(text: str, computed_styles: dict | None = None) -> dict:
    rules = load_rules()
    criteria_results = []
    total_score = 0.0
    total_weight = 0.0

    for criterion in rules["criteria"]:
        applies_when = criterion.get("applies_when")
        if applies_when and not re.search(applies_when, text, re.IGNORECASE):
            criteria_results.append(
                {
                    "id": criterion["id"],
                    "description": criterion["description"],
                    "legal_basis": criterion["legal_basis"],
                    "applicable": False,
                    "score": 1.0,
                    "weight": criterion["weight"],
                    "evidence": None,
                }
            )
            continue

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
                "applicable": True,
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
        "font_comparison": font_comparison(computed_styles),
    }
