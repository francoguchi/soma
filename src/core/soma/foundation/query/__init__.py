"""Owner-independent signed keyset cursor mechanics."""

import base64
import hashlib
import hmac
import secrets

from soma.foundation.errors import ValidationError
from soma.foundation.strict_json import canonical_json_bytes, loads_strict_bytes


class CursorCodec:
    def __init__(self, key=None):
        self.key = key or secrets.token_bytes(32)

    @staticmethod
    def limit(value=None):
        if value is None:
            return 100
        if type(value) is not int or not 1 <= value <= 200:
            raise ValidationError("Page size must be between 1 and 200.")
        return value

    def encode(self, contract, filters, order, position, as_of_utc_s):
        raw = canonical_json_bytes(
            {
                "version": 1,
                "contract": contract,
                "query": hashlib.sha256(canonical_json_bytes([filters, order])).hexdigest(),
                "position": position,
                "as_of_utc_s": as_of_utc_s,
            }
        )
        if len(raw) > 4096:
            raise ValidationError("Cursor exceeds its bound.")
        return base64.urlsafe_b64encode(raw + hmac.digest(self.key, raw, "sha256")).decode()

    def decode(self, token, contract, filters, order):
        try:
            if type(token) is not str or len(token) > 6000:
                raise ValueError()
            raw = base64.b64decode(token, altchars=b"-_", validate=True)
            body, signature = raw[:-32], raw[-32:]
            if not hmac.compare_digest(hmac.digest(self.key, body, "sha256"), signature):
                raise ValueError()
            value = loads_strict_bytes(body, max_bytes=4096)
            if (
                set(value) != {"version", "contract", "query", "position", "as_of_utc_s"}
                or type(value["version"]) is not int
                or value["version"] != 1
                or type(value["as_of_utc_s"]) is not int
                or value["as_of_utc_s"] < 0
                or value["contract"] != contract
                or value["query"]
                != hashlib.sha256(canonical_json_bytes([filters, order])).hexdigest()
            ):
                raise ValueError()
            return value["position"], value["as_of_utc_s"]
        except Exception:
            raise ValidationError("Cursor is invalid for this query or run.") from None
