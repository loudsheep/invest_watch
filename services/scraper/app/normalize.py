import hashlib
import re


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"https?://\S+", "<url>", text)
    return text


def content_hash(normalized_text: str) -> str:
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
