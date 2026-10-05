"""Contact descriptive validation; identity is never inferred from names/channels."""

from .matching import normalize_match_key
from .validation import validate_single_line_text


def validate_contact_name(value):
    stored = validate_single_line_text(value, field="contact.name", max_utf8_bytes=1024)
    return stored, normalize_match_key(stored, raw_max_utf8_bytes=1024)
