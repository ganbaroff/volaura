"""PII redactor for LLM trace metadata.

Strips personal identifiers before sending prompt snippets to
observability backends (Langfuse, etc.). Runs on every trace —
must be fast and never raise.
"""

import re

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"\+\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{2,4}")
_AZ_ID_RE = re.compile(r"\b[A-Z]{2,3}\d{6,8}\b")
_CREDIT_CARD_RE = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")
_UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


def redact(text: str | None) -> str | None:
    """Remove PII patterns from text. Returns None if input is None."""
    if not text:
        return text
    text = _UUID_RE.sub("[UUID]", text)
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _CREDIT_CARD_RE.sub("[CARD]", text)
    text = _AZ_ID_RE.sub("[ID]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    return text
