"""PII detection and replacement — placeholder.

Uses spaCy NER to detect and redact names, emails, phone numbers,
and other personal identifiers before text is sent to any LLM.
"""


def strip_pii(text: str) -> str:
    """Return text with PII replaced by placeholder tokens.

    E.g. "Hi, I'm John Smith — john@example.com" →
         "Hi, I'm [NAME] — [EMAIL]"
    """
    raise NotImplementedError
