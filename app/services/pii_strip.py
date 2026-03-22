"""PII detection and replacement using spaCy NER + regex fallbacks."""
import re
from functools import lru_cache

import spacy

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(
    r"(?<!\d)(\+?1[\s.\-]?)?(\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})(?!\d)"
)
_URL_RE = re.compile(r"https?://\S+|www\.\S+")

# spaCy entity labels to redact
_PII_LABELS = {"PERSON"}


@lru_cache(maxsize=1)
def _load_nlp():
    return spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])


def strip_pii(text: str) -> str:
    """Return text with PII replaced by placeholder tokens.

    Replaces:
    - Email addresses → [EMAIL]
    - Phone numbers   → [PHONE]
    - URLs            → [URL]
    - Person names (spaCy PERSON entities) → [NAME]
    """
    # Regex passes first (order matters for overlapping spans)
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _URL_RE.sub("[URL]", text)

    # spaCy NER pass — process in reverse to preserve char offsets
    nlp = _load_nlp()
    doc = nlp(text)
    for ent in sorted(doc.ents, key=lambda e: e.start_char, reverse=True):
        if ent.label_ in _PII_LABELS:
            text = text[: ent.start_char] + "[NAME]" + text[ent.end_char :]

    return text
