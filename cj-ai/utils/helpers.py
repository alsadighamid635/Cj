import re
import unicodedata
from datetime import datetime


def now_iso() -> str:
    return datetime.utcnow().isoformat(sep=" ", timespec="seconds")


def clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, max_len: int = 200) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "…"


def normalize_arabic(text: str) -> str:
    """Remove diacritics (tashkeel) from Arabic text."""
    return "".join(
        ch for ch in text
        if unicodedata.category(ch) != "Mn"
    )


def is_arabic(text: str) -> bool:
    arabic_chars = sum(1 for ch in text if "\u0600" <= ch <= "\u06ff")
    return arabic_chars > len(text) * 0.3


def safe_strip(value) -> str:
    if value is None:
        return ""
    return str(value).strip()
