"""Foundation UI.APPEARANCE semantics; generic storage registration data only."""

from soma.foundation.errors import ValidationError

APPEARANCE_KEY = "foundation.appearance"
APPEARANCE_MODES = ("core_dark", "system", "light")


def validate_appearance(value):
    if type(value) is not str or value not in APPEARANCE_MODES:
        raise ValidationError("Invalid appearance preference.")
    return value


def default_appearance():
    return "core_dark"


def appearance_equals(left, right):
    return left == right


def setting_registration():
    return dict(
        setting_key=APPEARANCE_KEY,
        semantic_owner="foundation",
        contract_name="AppearancePreferenceV1",
        current_version=1,
        default_provider=default_appearance,
        validator=validate_appearance,
        semantic_equals=appearance_equals,
        max_utf8_bytes=256,
        max_depth=1,
        max_collection_items=1,
    )
