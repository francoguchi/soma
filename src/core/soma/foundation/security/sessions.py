import hashlib
import hmac
from http.cookies import SimpleCookie, CookieError
import secrets
import threading
import time

from soma.foundation.errors import SomaError
from soma.foundation.identity import require_uuid4
from soma.runtime.control import encode_secret, guard_request

COOKIE = "soma_session"


class Sessions:
    def __init__(self, run_id, origin, *, clock=time.monotonic):
        self.run_id, self.origin, self.clock = require_uuid4(run_id), origin, clock
        self.entries = {}
        self.lock = threading.Lock()

    def expire(self):
        now = self.clock()
        for key, entry in list(self.entries.items()):
            if now >= entry["absolute"] or now - entry["last_seen"] >= 43200:
                del self.entries[key]

    def issue(self, actor_id):
        require_uuid4(actor_id)
        with self.lock:
            self.expire()
            if len(self.entries) >= 4:
                raise SomaError(
                    "SESSION_CAPACITY",
                    "Close an existing session or restart SOMA before signing in again.",
                )
            token, csrf = (
                encode_secret(secrets.token_bytes(32)),
                encode_secret(secrets.token_bytes(32)),
            )
            key = hashlib.sha256(token.encode()).hexdigest()
            now = self.clock()
            self.entries[key] = {
                "actor_id": actor_id,
                "issued": now,
                "last_seen": now,
                "absolute": now + 86400,
                "csrf_hash": hashlib.sha256(csrf.encode()).digest(),
            }
            return token, csrf

    def mutation_origin(self, request):
        guard_request(request, self.origin)
        headers = request.headers
        if headers.getlist("origin") != [self.origin] or headers.get("sec-fetch-site") not in {
            None,
            "same-origin",
            "none",
        }:
            raise SomaError("FORBIDDEN", "Browser request origin is invalid.")

    def validate(self, request, *, mutation=False):
        guard_request(request, self.origin)
        try:
            values = request.headers.getlist("cookie")
            if len(values) != 1 or len(values[0]) > 4096 or values[0].count(COOKIE + "=") != 1:
                raise ValueError()
            cookies = SimpleCookie()
            cookies.load(values[0])
            token = cookies[COOKIE].value
            if not token.isascii() or len(token) != 44:
                raise ValueError()
            key = hashlib.sha256(token.encode()).hexdigest()
        except (ValueError, KeyError, CookieError):
            raise SomaError("UNAUTHENTICATED", "Sign in to continue.", "reauthenticate") from None
        with self.lock:
            self.expire()
            entry = self.entries.get(key)
            if entry is None:
                raise SomaError("UNAUTHENTICATED", "Sign in to continue.", "reauthenticate")
            if request.headers.get("x-soma-run") not in {None, self.run_id}:
                raise SomaError(
                    "RUN_CHANGED", "SOMA restarted. Reload this page before continuing.", "refresh"
                )
            if mutation:
                self.mutation_origin(request)
                csrf = request.headers.getlist("x-soma-csrf")
                if (
                    len(csrf) != 1
                    or not csrf[0].isascii()
                    or not hmac.compare_digest(
                        hashlib.sha256(csrf[0].encode()).digest(), entry["csrf_hash"]
                    )
                ):
                    raise SomaError("FORBIDDEN", "Browser confirmation context is invalid.")
                if request.headers.get("x-soma-run") != self.run_id:
                    raise SomaError(
                        "RUN_CHANGED",
                        "SOMA restarted. Reload this page before continuing.",
                        "refresh",
                    )
            entry["last_seen"] = self.clock()
            return {
                "actor_id": entry["actor_id"],
                "run_id": self.run_id,
                "session_fingerprint": key,
            }

    def refresh_csrf(self, context):
        with self.lock:
            token = encode_secret(secrets.token_bytes(32))
            self.entries[context["session_fingerprint"]]["csrf_hash"] = hashlib.sha256(
                token.encode()
            ).digest()
            return token

    def revoke(self, token):
        with self.lock:
            self.entries.pop(hashlib.sha256(token.encode()).hexdigest(), None)

    def logout(self, context):
        with self.lock:
            self.entries.pop(context["session_fingerprint"], None)

    def clear(self):
        with self.lock:
            self.entries.clear()
