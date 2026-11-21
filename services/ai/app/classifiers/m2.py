"""M2 - risk-disclosure compliance, driven entirely by config/m2_rules.yaml
(ADR-0009). Each criterion carries its legal basis so the UI can show it next
to the finding. Changing the rules means editing YAML, not this file.
"""
import re
from collections.abc import Callable
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


def _parse_color(value: str | None) -> tuple[float, float, float, float] | None:
    match = re.match(r"rgba?\(([^)]+)\)", value or "")
    if not match:
        return None
    parts = [p.strip() for p in re.split(r"[,/ ]+", match.group(1).strip()) if p.strip()]
    try:
        channels = [float(p) for p in parts[:3]]
        alpha = float(parts[3]) if len(parts) > 3 else 1.0
    except ValueError:
        return None
    return channels[0], channels[1], channels[2], alpha


def _luminance(rgb: tuple[float, float, float]) -> float:
    def channel(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(foreground: str | None, background: str | None) -> float | None:
    fg, bg = _parse_color(foreground), _parse_color(background)
    if fg is None or bg is None:
        return None
    if bg[3] < 1:
        bg = (255, 255, 255, 1.0)
    lf, lb = _luminance(fg[:3]), _luminance(bg[:3])
    lighter, darker = max(lf, lb), min(lf, lb)
    return (lighter + 0.05) / (darker + 0.05)


def _risk_elements(computed_styles: dict | None) -> list[dict]:
    return (computed_styles or {}).get("risk_warning_elements") or []


def _contrast_score(text, computed_styles, criterion):
    elements = _risk_elements(computed_styles)
    if not elements:
        return None
    minimum = criterion.get("min_contrast_ratio", 4.5)
    worst, worst_el = None, None
    for el in elements:
        ratio = contrast_ratio(el.get("color"), el.get("effectiveBackground") or el.get("backgroundColor"))
        if ratio is None:
            continue
        opacity = float(el.get("opacity", 1) or 1)
        ratio = 1 + (ratio - 1) * min(opacity, 1.0)
        if worst is None or ratio < worst:
            worst, worst_el = ratio, el
    if worst is None:
        return None
    score = min(1.0, worst / minimum)
    return score, f"contrast={worst:.1f}:1 (min {minimum}:1) \"{(worst_el.get('text') or '')[:60]}\""


def _is_low_visibility(el: dict) -> bool:
    try:
        font = float(str(el.get("fontSize", "16")).replace("px", ""))
    except ValueError:
        font = 16.0
    return bool(el.get("inFooter")) or float(el.get("opacity", 1) or 1) < 0.6 or font < 10 or bool(el.get("clipped"))


def _hidden_score(text, computed_styles, criterion):
    elements = _risk_elements(computed_styles)
    if not elements:
        return None
    visible = [el for el in elements if not _is_low_visibility(el)]
    if visible:
        return 1.0, None
    sample = elements[0]
    where = "stopka/sekcja legal" if sample.get("inFooter") else "niska widoczność"
    return 0.0, f"{where}: \"{(sample.get('text') or '')[:80]}\""


def _one_click_score(text, computed_styles, criterion):
    for pattern in criterion.get("violation_patterns", []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return 0.0, match.group(0)
    if computed_styles is None:
        return None
    links = computed_styles.get("risk_links") or []
    inline = [el for el in _risk_elements(computed_styles) if len(el.get("text") or "") >= 40]
    if links and not inline:
        return 0.0, f"ryzyko tylko pod linkiem: \"{links[0][:80]}\""
    return 1.0, None


def _responsive_score(text, computed_styles, criterion):
    viewports = (computed_styles or {}).get("viewports") or {}
    if not viewports:
        return None
    minimum = criterion.get("min_font_px", 11)
    problems = []
    for name, data in viewports.items():
        elements = data.get("risk_warning_elements") or []
        if not elements:
            problems.append(f"{name}: brak widocznego ostrzeżenia")
            continue
        for el in elements:
            try:
                font = float(str(el.get("fontSize", "16")).replace("px", ""))
            except ValueError:
                continue
            if font < minimum:
                problems.append(f"{name}: czcionka {font:.0f}px")
                break
            if el.get("clipped"):
                problems.append(f"{name}: tekst ucięty")
                break
    if not problems:
        return 1.0, None
    return max(0.0, 1 - len(problems) / (len(viewports) * 1.0)), "; ".join(problems)


def _risk_sentences(text: str, computed_styles: dict | None) -> list[str]:
    elements = _risk_elements(computed_styles)
    source = " ".join(el.get("text") or "" for el in elements) if elements else text
    sentences = re.split(r"(?<=[.!?])\s+", source)
    return [s for s in sentences if re.search(r"ryzyk|strat|traci", s, re.IGNORECASE)]


def _readability_score(text, computed_styles, criterion):
    sentences = _risk_sentences(text, computed_styles)
    if not sentences:
        return None
    words = sum(len(s.split()) for s in sentences) / len(sentences)
    max_words = criterion.get("max_words_per_sentence", 30)
    joined = " ".join(sentences)
    jargon = [j for j in criterion.get("jargon", []) if re.search(j, joined, re.IGNORECASE)]
    score = 1.0 if words <= max_words else max(0.0, 1 - (words - max_words) / max_words)
    if len(jargon) >= 3:
        score = min(score, 0.4)
    elif jargon:
        score = min(score, 0.8)
    return score, f"avg_words={words:.0f} jargon={len(jargon)}"


def _dominance_score(text, computed_styles, criterion):
    if not computed_styles:
        return None
    historical = [
        el for el in (computed_styles.get("historical_elements") or [])
    ]
    max_font = computed_styles.get("max_font_px")
    if not historical or not max_font:
        return None
    try:
        largest = max(float(str(el.get("fontSize", "0")).replace("px", "")) for el in historical)
    except ValueError:
        return None
    if largest >= max_font * 0.95:
        return 0.0, f"wyniki historyczne: {largest:.0f}px = największy tekst ({max_font:.0f}px)"
    return 1.0, f"wyniki historyczne: {largest:.0f}px, największy tekst {max_font:.0f}px"


def _comparison_score(text, computed_styles, criterion):
    return _regex_criterion_score(text, criterion)


def _violation_score(text, computed_styles, criterion):
    for pattern in criterion.get("patterns", []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return 0.0, match.group(0)
    return 1.0, None


DETECTORS = {
    "regex": lambda text, styles, c: _regex_criterion_score(text, c),
    "regex_violation": _violation_score,
    "classifier": lambda text, styles, c: _profit_risk_balance_score(text, c),
    "visual": lambda text, styles, c: _visual_prominence_score(styles, c),
    "contrast": _contrast_score,
    "hidden": _hidden_score,
    "one_click": _one_click_score,
    "responsive": _responsive_score,
    "readability": _readability_score,
    "dominance": _dominance_score,
    "comparison": _comparison_score,
}


def _result(criterion: dict, applicable: bool, score: float, evidence: str | None, detector: str | None = None) -> dict:
    return {
        "id": criterion["id"],
        "ref": criterion.get("ref"),
        "name": criterion.get("name"),
        "detector": detector or criterion["detector"],
        "description": criterion["description"],
        "legal_basis": criterion["legal_basis"],
        "applicable": applicable,
        "score": score,
        "weight": criterion["weight"],
        "evidence": evidence,
    }


JudgeFn = Callable[[dict, str], dict | None]


def _llm_outcome(judge: JudgeFn, criterion: dict, text: str, computed_styles: dict | None):
    """(score, evidence) from the LLM judge for criteria marked `llm_judge`; None to use the heuristic."""
    if criterion["id"] == "risk_readability":
        subject = " ".join(_risk_sentences(text, computed_styles))
    else:
        subject = text
    if not subject.strip():
        return None
    verdict = judge(criterion, subject)
    if verdict is None:
        return None
    detail = verdict["reason"] + (f" \u201e{verdict['evidence']}\u201d" if verdict["evidence"] else "")
    return (1.0 if verdict["pass"] else 0.0), detail.strip()


def evaluate(text: str, computed_styles: dict | None = None, judge: JudgeFn | None = None) -> dict:
    rules = load_rules()
    criteria_results = []
    total_score = 0.0
    total_weight = 0.0

    for criterion in rules["criteria"]:
        applies_when = criterion.get("applies_when")
        if applies_when and not re.search(applies_when, text, re.IGNORECASE):
            criteria_results.append(_result(criterion, False, 1.0, None))
            continue

        detector = criterion["detector"]
        outcome = None
        if judge is not None and criterion.get("llm_judge"):
            outcome = _llm_outcome(judge, criterion, text, computed_styles)
            detector = "llm" if outcome is not None else detector
        if outcome is None:
            outcome = DETECTORS[criterion["detector"]](text, computed_styles, criterion)
        if outcome is None:
            criteria_results.append(_result(criterion, False, 1.0, None))
            continue

        score, evidence = outcome
        total_score += score * criterion["weight"]
        total_weight += criterion["weight"]
        criteria_results.append(_result(criterion, True, score, evidence, detector))

    compliance_score = total_score / total_weight if total_weight else 0.0
    change = (computed_styles or {}).get("change_detection")
    risk_score = 1 - compliance_score
    if change:
        risk_score = max(risk_score, 0.9)
    return {
        "compliance_score": compliance_score,
        "risk_score": risk_score,
        "change_detection": change,
        "criteria": criteria_results,
        "font_comparison": font_comparison(computed_styles),
        "forecast_detected": bool(re.search(r"prognoz|symulacj", text, re.IGNORECASE)),
    }
