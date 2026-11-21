from investwatch_common.custody import build_custody, canonical_json, verify_custody


def test_untouched_files_verify():
    files = {"page.html": b"<html>", "computed_styles.json": canonical_json({"b": 1, "a": 2.5})}
    custody = build_custody("https://x.pl", "abc", files)
    assert verify_custody(custody, files)["verified"] is True


def test_modified_and_missing_files_are_reported():
    files = {"page.html": b"<html>", "screenshot.png": b"png"}
    custody = build_custody("https://x.pl", "abc", files)
    result = verify_custody(custody, {"page.html": b"<html>tampered"})
    assert result["files"]["page.html"]["status"] == "modified"
    assert result["files"]["screenshot.png"]["status"] == "missing"
    assert result["verified"] is False


def test_tampered_manifest_is_detected():
    files = {"page.html": b"<html>"}
    custody = build_custody("https://x.pl", "abc", files)
    custody["captured_at"] = "2020-01-01T00:00:00+00:00"
    assert verify_custody(custody, files)["manifest_ok"] is False
