"""Memory-only deliberate friction; no authorization or accepted domain writer."""

from dataclasses import dataclass
import hashlib
import re
import secrets
import threading
import time
from types import MappingProxyType

from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import new_uuid4, require_uuid4
from soma.foundation.transactions import UnitOfWork
from soma.runtime.control import encode_secret


@dataclass(frozen=True)
class ProofAction:
    action_code: str
    target_type: str
    tier: str


class DeliberateProofs:
    def __init__(self, run_id, registrations=(), *, clock=time.monotonic):
        self.run_id, self.clock = require_uuid4(run_id), clock
        actions = {}
        for action in registrations:
            if (
                not action.action_code
                or not action.target_type
                or action.action_code in actions
                or action.tier not in {"deliberate_hold", "impact_preview_plus_hold"}
            ):
                raise ValidationError("Invalid or duplicate deliberate action registration.")
            actions[action.action_code] = action
        self.actions = MappingProxyType(actions)
        self.challenges, self.proofs = {}, {}
        self.lock = threading.Lock()

    def _binding(self, context, binding):
        if context["run_id"] != self.run_id or not context.get("session_fingerprint"):
            raise self.invalid()
        if type(binding) is not dict or set(binding) != {
            "action_code",
            "target_type",
            "target_id",
            "base_revision",
            "preview_fingerprint",
        }:
            raise self.invalid()
        action = self.actions.get(binding["action_code"])
        if action is None or action.target_type != binding["target_type"]:
            raise self.invalid()
        for name in ("target_id", "base_revision"):
            if type(binding[name]) is not str or not 1 <= len(binding[name].encode("utf-8")) <= 256:
                raise self.invalid()
        preview = binding["preview_fingerprint"]
        if (
            preview is not None
            and (type(preview) is not str or re.fullmatch(r"[0-9a-f]{64}", preview) is None)
            or action.tier == "impact_preview_plus_hold"
            and preview is None
        ):
            raise self.invalid()
        return (
            self.run_id,
            context["session_fingerprint"],
            context["actor_id"],
            *[
                binding[k]
                for k in (
                    "action_code",
                    "target_type",
                    "target_id",
                    "base_revision",
                    "preview_fingerprint",
                )
            ],
        )

    @staticmethod
    def invalid():
        return SomaError(
            "DELIBERATE_PROOF_INVALID",
            "Deliberate confirmation is unavailable, expired, or no longer matches this action.",
            "refresh",
        )

    def _expire(self):
        now = self.clock()
        for store in (self.challenges, self.proofs):
            for key, row in list(store.items()):
                if now >= row["expires"]:
                    del store[key]

    def issue(self, context, binding):
        bound = self._binding(context, binding)
        with self.lock:
            self._expire()
            if (
                len(self.challenges) + len(self.proofs) >= 256
                or sum(
                    row["bound"][1] == bound[1]
                    for store in (self.challenges, self.proofs)
                    for row in store.values()
                )
                >= 64
            ):
                raise SomaError(
                    "DELIBERATE_PROOF_CAPACITY",
                    "Too many pending confirmations. Wait and try again.",
                    "retry",
                )
            identity, now = new_uuid4(), self.clock()
            self.challenges[identity] = {"bound": bound, "issued": now, "expires": now + 15}
            return {"challenge_id": identity, "expires_in_ms": 15000}

    def complete(self, context, challenge_id, binding):
        bound = self._binding(context, binding)
        with self.lock:
            self._expire()
            row = self.challenges.get(challenge_id)
            if row is None or row["bound"] != bound or self.clock() - row["issued"] < 3:
                raise self.invalid()
            del self.challenges[challenge_id]
            token = encode_secret(secrets.token_bytes(32))
            self.proofs[hashlib.sha256(token.encode()).digest()] = {
                "bound": bound,
                "expires": self.clock() + 30,
            }
            return {"proof_token": token, "expires_in_ms": 30000}

    def abandon(self, context, challenge_id):
        with self.lock:
            row = self.challenges.get(challenge_id)
            if row and row["bound"][:3] == (
                self.run_id,
                context["session_fingerprint"],
                context["actor_id"],
            ):
                del self.challenges[challenge_id]

    def consume(self, uow, context, binding, token):
        if not isinstance(uow, UnitOfWork) or not hasattr(uow, "connection"):
            raise ValidationError("Deliberate proof consumption requires the owner transaction.")
        bound = self._binding(context, binding)
        if type(token) is not str or not token.isascii() or len(token) != 44:
            raise self.invalid()
        key = hashlib.sha256(token.encode()).digest()
        with self.lock:
            self._expire()
            row = self.proofs.get(key)
            if row is None or row["bound"] != bound:
                raise self.invalid()
            # Deliberately irreversible in-memory consumption, even on TX rollback.
            del self.proofs[key]

    def clear(self):
        with self.lock:
            self.challenges.clear()
            self.proofs.clear()
