import pytest

from soma.foundation.errors import SomaError
from soma.modules.reference.domain.matching import (
    normalize_match_key,
    unicode_match_asset_metadata,
)
from soma.modules.reference.domain.validation import (
    validate_account_code,
    validate_customer_name,
    validate_display_name,
)


def test_unicode_match_v1_asset_is_pinned_to_unicode_17():
    metadata = unicode_match_asset_metadata()
    assert metadata["profile_id"] == "UNICODE_MATCH_V1"
    assert metadata["unicode_version"] == "17.0.0"
    assert (
        metadata["asset_sha256"]
        == "ec78bcbdf7afa6621dfe342790227e052a55f5913395bc69d92b1bf910a76aca"
    )
    assert len(metadata["casefold_sha256"]) == 64
    assert len(metadata["proplist_sha256"]) == 64


def test_unicode_match_v1_nfkc_whitespace_and_full_casefold():
    assert normalize_match_key(
        "  ＦＵＳＳ\u00a0Straße  ", raw_max_utf8_bytes=1024
    ) == "fuss strasse"
    assert normalize_match_key("İ", raw_max_utf8_bytes=16) == "i\u0307"


def test_unicode_match_v1_preserves_accents_and_punctuation():
    assert normalize_match_key("Éxample-Co.", raw_max_utf8_bytes=64) == "éxample-co."
    assert normalize_match_key("Example.Co", raw_max_utf8_bytes=64) != normalize_match_key(
        "Example-Co", raw_max_utf8_bytes=64
    )


@pytest.mark.parametrize(
    "validator,value",
    [
        (validate_display_name, ""),
        (validate_display_name, "x" * 513),
        (validate_customer_name, "customer\nname"),
        (validate_account_code, "x" * 513),
    ],
)
def test_scope01_current_bounds_reject_without_truncation(validator, value):
    with pytest.raises(SomaError):
        validator(value)


def test_customer_and_account_code_keys_use_same_governed_profile():
    assert validate_customer_name("  Ａcme\u00a0Straße  ")[1] == "acme strasse"
    assert validate_account_code("  WID-１２３  ")[1] == "wid-123"
