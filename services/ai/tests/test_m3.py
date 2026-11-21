from app.classifiers import m3


def test_registered_domain_strips_subdomains():
    assert m3.registered_domain("www.ing.pl") == "ing.pl"
    assert m3.registered_domain("secure.example.co.uk") == "example.co.uk"


def test_parse_date_handles_pl_registry_and_iso():
    assert m3._parse_date("2000.01.17 12:00:00").year == 2000
    assert m3._parse_date("1995-08-14T04:00:00Z").year == 1995


def test_created_regex_ignores_option_created():
    text = "option created:   2025.07.26 09:56:46\ncreated:   2000.08.08 13:00:00\n"
    assert m3.CREATED_RE.search(text).group(1).startswith("2000")


def test_detect_language_distinguishes_polish_and_english():
    from app.language import detect_language

    polish = "Zarabiaj z nami na rynkach finansowych. Otwórz konto i zacznij inwestować już dziś bez ryzyka."
    english = "Earn money with us on the financial markets. Open an account and start investing today with no risk."
    assert detect_language(polish) == "pl"
    assert detect_language(english) == "en"
    assert detect_language("krótki") is None
