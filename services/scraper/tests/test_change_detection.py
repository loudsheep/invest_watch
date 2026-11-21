from app.tasks import _removed_risk_statements


def test_detects_removed_risk_sentence():
    old = "Zarabiaj z nami. Inwestowanie wiąże się z ryzykiem utraty kapitału. Zapisz się."
    new = "Zarabiaj z nami. Zapisz się."
    assert _removed_risk_statements(old, new) == ["Inwestowanie wiąże się z ryzykiem utraty kapitału."]


def test_unchanged_text_has_no_removals():
    text = "Handluj. Ryzyko utraty kapitału."
    assert _removed_risk_statements(text, text) == []
