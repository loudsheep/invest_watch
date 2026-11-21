from app.entity_resolution import extract_registry_ids


def test_extracts_krs_and_nip_in_common_notations():
    text = "Spółka KRS 0000999999, NIP: 773-237-39-68. Dodatkowo KRS nr 0000123456."
    ids = extract_registry_ids(text)
    assert ids["krs"] == {"0000999999", "0000123456"}
    assert ids["nip"] == {"7732373968"}


def test_ignores_numbers_without_a_label_or_with_wrong_length():
    assert extract_registry_ids("Kod 0000999999, NIP 123") == {"krs": set(), "nip": set()}
