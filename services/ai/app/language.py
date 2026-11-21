"""Language detection. Non-Polish pages are translated to Polish so the Polish rule
set (M2 criteria, M3 phrases, promo patterns) applies to them."""
from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0

MIN_TEXT_LENGTH = 60
SAMPLE_LENGTH = 3000


def detect_language(text: str) -> str | None:
    """ISO 639-1 code, or None when the text is too short or undecidable."""
    sample = (text or "").strip()[:SAMPLE_LENGTH]
    if len(sample) < MIN_TEXT_LENGTH:
        return None
    try:
        return detect(sample)
    except LangDetectException:
        return None
