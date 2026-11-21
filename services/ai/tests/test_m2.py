from pathlib import Path

import pytest
from app.classifiers import m2

RULES = Path(__file__).resolve().parents[3] / "config" / "m2_rules.yaml"


@pytest.fixture(autouse=True)
def rules_path(monkeypatch):
    monkeypatch.setattr(m2, "RULES_PATH", RULES)
    m2.load_rules.cache_clear()


def result(text, styles=None):
    return {c["id"]: c for c in m2.evaluate(text, styles)["criteria"]}


def test_all_attachment_criteria_present():
    refs = {c["ref"] for c in m2.load_rules()["criteria"]}
    assert {str(i) for i in range(1, 19)} - {"12"} | {"12a", "12b"} <= refs


def test_company_identification_ignores_polish_word_sa():
    assert result("zyski sa wysokie")["company_identification"]["score"] == 0.0
    assert result("Fikcyjny Dom Maklerski Nordik S.A.")["company_identification"]["score"] == 1.0


def test_regulator_approval_flagged():
    r = result("Nasza oferta jest zatwierdzona przez KNF.")
    assert r["regulator_approval"]["score"] == 0.0


def test_supervision_as_safety_flagged():
    r = result("Inwestycja jest w pełni bezpieczna, spełniamy rygorystyczne wymogi nadzorcze KNF.")
    assert r["supervision_as_safety"]["score"] == 0.0


def test_regulator_rules_not_applicable_without_mention():
    r = result("Handluj akcjami.")
    assert r["regulator_approval"]["applicable"] is False


def test_english_risk_warning_in_polish_text():
    r = result("Zyskaj więcej z nami. Capital at risk.")
    assert r["risk_language_consistency"]["score"] == 0.0


def test_tax_disclaimer():
    ok = result("IKE bez podatku. Traktowanie podatkowe zależy od indywidualnej sytuacji klienta i może ulec zmianie.")
    bad = result("IKE bez podatku Belki.")
    assert ok["tax_information"]["score"] == 1.0
    assert bad["tax_information"]["score"] == 0.0


def test_contrast_low_fails():
    styles = {"risk_warning_elements": [{"text": "Ryzyko", "color": "rgb(200,200,200)", "backgroundColor": "rgb(255,255,255)", "fontSize": "12px"}]}
    r = result("Ryzyko utraty kapitału", styles)
    assert r["risk_contrast"]["score"] < 0.5


def test_hidden_in_footer():
    styles = {"risk_warning_elements": [{"text": "Ryzyko", "inFooter": True, "fontSize": "9px", "color": "rgb(0,0,0)", "backgroundColor": "rgb(255,255,255)"}]}
    assert result("x", styles)["risk_hidden"]["score"] == 0.0


def test_visual_criteria_not_applicable_without_styles():
    r = result("tekst bez stylów")
    assert r["risk_contrast"]["applicable"] is False
    assert r["risk_responsive"]["applicable"] is False


def test_historical_dominance():
    styles = {"historical_elements": [{"fontSize": "48px"}], "max_font_px": 48}
    assert result("Wyniki historyczne: stopa zwrotu 40%", styles)["historical_dominance"]["score"] == 0.0


def test_removed_disclaimer_raises_risk():
    styles = {"change_detection": {"removed_risk_statements": ["Inwestowanie wiąże się z ryzykiem."]}}
    assert m2.evaluate("Zarabiaj z nami.", styles)["risk_score"] >= 0.9


def test_risk_warning_wording_variants():
    assert result("Inwestowanie w CFD wiąże się z ryzykiem.")["risk_warning_present"]["score"] == 1.0
