"""Email storage/use validation without network access."""

from dataclasses import dataclass
from email.errors import HeaderParseError
from email.headerregistry import Address

from soma.foundation.errors import SomaError
from .matching import normalize_match_key, trim_match_whitespace


def validate_email(value):
    def invalid():
        return SomaError("CHANNEL_INVALID", "Email channel is invalid.", "correct_input")

    if type(value) is not str:
        raise invalid()
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        raise invalid() from exc
    if size > 2048:
        raise SomaError("FIELD_BOUND_EXCEEDED", "Email exceeds its byte bound.", "correct_input")
    # Reject controls before trimming, including edge CR/LF and tabs.
    if any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value):
        raise invalid()
    stored = trim_match_whitespace(value)
    if not stored:
        raise invalid()
    try:
        parsed = Address(addr_spec=stored)
        if not parsed.username or not parsed.domain:
            raise invalid()
    except (ValueError, HeaderParseError) as exc:
        raise invalid() from exc
    return stored, normalize_match_key(stored, raw_max_utf8_bytes=2048)


@dataclass(frozen=True)
class ChannelUseValidation:
    state: str
    contact_id: str
    contact_channel_id: str | None = None
    channel_kind: str = "email"
    value_text: str | None = None
    usable_count: int = 0
    candidate_channel_ids: tuple[str, ...] = ()
    continuation_after_id: str | None = None
