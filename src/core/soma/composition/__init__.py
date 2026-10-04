"""Compose only providers implemented by this build."""

from soma.foundation.errors import ValidationError


class CapabilityRegistry:
    def __init__(self):
        self.items = {}

    def register(self, identity, state, *, provider=None, reason=None):
        if identity in self.items or state not in {"available", "unavailable", "development"} or not identity:
            raise ValidationError("Invalid or conflicting capability registration.")
        if state == "available" and provider is None:
            raise ValidationError("Available capabilities require a composed provider.")
        self.items[identity] = {"id": identity, "state": state, "reason": reason}

    def snapshot(self):
        return [self.items[key] for key in sorted(self.items)]


def capabilities():
    return [
        {"id": "foundation.runtime", "state": "available", "reason": None},
        {"id": "foundation.diagnostics", "state": "available", "reason": None},
    ]
