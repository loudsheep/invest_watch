from app.registry.knf import _lines
from app.registry.names import normalize, short_alias


def test_normalize_drops_legal_form_and_accents():
    assert normalize("XTB S.A.") == "xtb"
    assert normalize("Dom Maklerski BOŚ S.A.") == normalize("DOM MAKLERSKI BOŚ SPÓŁKA AKCYJNA")
    assert normalize("Plus500CY Ltd") == "plus500cy"


def test_short_alias_requires_distinctive_name():
    assert short_alias("CASPAR ASSET MANAGEMENT S.A.") == "CASPAR ASSET MANAGEMENT"
    assert short_alias("XTB S.A.") is None


def test_short_alias_cuts_brokerage_department():
    assert short_alias("BANK MILLENNIUM S.A. Biuro Maklerskie Banku Millennium") == "BANK MILLENNIUM"


def test_lines_splits_numbered_multi_entity_cell():
    assert _lines("1. Alfa sp. z o.o.\n2. Beta Ltd") == ["Alfa sp. z o.o.", "Beta Ltd"]


def test_short_alias_rejects_generic_phrases():
    assert short_alias("DOM MAKLERSKI INC S.A.") is None
    assert short_alias("TRIGON DOM MAKLERSKI S.A.") == "TRIGON DOM MAKLERSKI"
