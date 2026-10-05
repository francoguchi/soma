import os
import time

from starlette.responses import JSONResponse

from soma.composition import CapabilityRegistry
from soma.foundation.contracts import validate_contract
from soma.foundation.errors import SomaError
from soma.foundation.jobs import Coordinator
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.security.auth import Authentication
from soma.foundation.security.sessions import COOKIE, Sessions
from soma.foundation.security.deliberate_action import DeliberateProofs
from soma.foundation.working_copy import WorkingCopies, BOUNDS
from soma.foundation.strict_json import canonical_json_bytes_bounded, loads_strict
from soma.foundation.strict_json import loads_strict_bytes


class Browser:
    def __init__(self, host):
        self.host = host
        self.sessions = Sessions(host.run_id, host.origin)
        self.auth = Authentication(
            host.factory,
            self.sessions,
            host.log,
            profile_participant=host.profile_participant,
        )
        self.proofs = DeliberateProofs(host.run_id, host.proof_actions)
        copy_contracts = host.copy_contracts
        if getattr(host, "reference", None) is not None:
            copy_contracts = (*copy_contracts, *host.reference.recovery_contracts())
        self.copies = WorkingCopies(host.factory, copy_contracts)
        registry = CapabilityRegistry()
        for name, provider in (
            ("foundation.runtime", host),
            ("foundation.diagnostics", self),
            ("foundation.auth", self.auth),
        ):
            registry.register(name, "available", provider=provider)
        self.registry = registry
        self.reference_transport = None
        if getattr(host, "reference", None) is not None:
            from soma.modules.reference.transport.routes import ReferenceTransport

            self.reference_transport = ReferenceTransport(
                host.reference, host.factory, self.sessions
            )
            registry.register("reference.identity", "available", provider=host.reference)
            registry.register("settings", "available", provider=host.reference.settings)
        registry.register("foundation.working_copies", "available", provider=self.copies)
        registry.register("foundation.confirmation", "available", provider=self.proofs)

    def bootstrap(self, request):
        state = self.auth.state()
        csrf = None
        if state == "login_required":
            try:
                context = self.sessions.validate(request)
                state = "authenticated"
                csrf = self.sessions.refresh_csrf(context)
            except SomaError:
                pass
        return {
            "run_id": self.host.run_id,
            "build": self.host.health()["build"],
            "auth_state": state,
            "csrf_token": csrf,
            "capabilities": self.registry.snapshot(),
        }

    def diagnostics(self):
        partial = []
        counts = None
        try:
            with ReadSnapshot(self.host.factory) as snapshot:
                counts = Coordinator.counts(snapshot)
        except Exception:
            partial.append("jobs")
        return {
            "health": self.host.health(),
            "uptime_ms": max(0, int((time.monotonic() - self.host.started_monotonic) * 1000)),
            "capabilities": self.registry.snapshot(),
            "job_counts": counts,
            "request_tasks": len(self.host.requests.futures),
            "background_tasks": len(self.host.jobs.executor.futures),
            "open_connections": None,
            "active_transactions": None,
            "current_log": "diagnostics/" + self.host.log.path.name,
            "logging_available": self.host.log.available,
            **self.host.log.snapshot(),
            "partial": partial,
        }

    def handle(self, request, raw):
        path = request.url.path
        if self.reference_transport is not None and path.startswith(
            ("/api/v1/reference/", "/api/v1/settings/", "/api/v1/local-user-profile")
        ):
            return self.reference_transport.handle(request, raw)
        if path.startswith("/api/v1/confirmation/") and request.method == "POST":
            context = self.sessions.validate(request, mutation=True)
            body = loads_strict_bytes(raw, max_bytes=8192)
            if path == "/api/v1/confirmation/challenge":
                validate_contract("urn:soma:00:proof-binding:v1", body)
                return self.response("proof-challenge", self.proofs.issue(context, body))
            if path == "/api/v1/confirmation/complete":
                validate_contract("urn:soma:00:proof-completion-request:v1", body)
                return self.response(
                    "proof-result",
                    self.proofs.complete(context, body["challenge_id"], body["binding"]),
                )
            if path == "/api/v1/confirmation/abandon":
                validate_contract("urn:soma:00:proof-abandon-request:v1", body)
                self.proofs.abandon(context, body["challenge_id"])
                return self.response("empty-request", {})
        if path.startswith("/api/v1/working-copies/") and request.method == "POST":
            context = self.sessions.validate(request, mutation=True)
            body = loads_strict_bytes(raw, max_bytes=2097152)
            if path == "/api/v1/working-copies/checkpoint":
                validate_contract("urn:soma:00:working-copy-checkpoint-request:v1", body)
                request_input = {key: value for key, value in body.items() if key != "draft_json"}
                request_input["draft"] = loads_strict(body["draft_json"], max_bytes=262144)
                return self.response(
                    "working-copy-result",
                    self.copies.checkpoint(request_input, context["actor_id"]),
                )
            if path == "/api/v1/working-copies/restore":
                validate_contract("urn:soma:00:working-copy-key:v1", body)
                result = self.copies.restore(body)
                draft = result.pop("draft")
                result["draft_json"] = canonical_json_bytes_bounded(draft, **BOUNDS).decode()
                return self.response("working-copy-restore", result)
            if path == "/api/v1/working-copies/discard":
                validate_contract("urn:soma:00:working-copy-discard-request:v1", body)
                return self.response(
                    "working-copy-result",
                    self.copies.discard(
                        body["command_id"],
                        body["working_copy_id"],
                        body["expected_generation"],
                        context["actor_id"],
                    ),
                )
        if path == "/api/v1/bootstrap" and request.method == "GET":
            return self.response("bootstrap", self.bootstrap(request))
        if path in {"/api/v1/auth/setup", "/api/v1/auth/login"} and request.method == "POST":
            self.sessions.mutation_origin(request)
            kind = "auth-setup-request" if path.endswith("setup") else "auth-login-request"
            body = loads_strict_bytes(raw, max_bytes=8192)
            validate_contract("urn:soma:00:" + kind + ":v1", body)
            if body["run_id"] != self.host.run_id:
                raise SomaError(
                    "RUN_CHANGED", "SOMA restarted. Reload this page before continuing.", "refresh"
                )
            token, csrf = (
                self.auth.setup(body["password"], body["confirmation"])
                if kind == "auth-setup-request"
                else self.auth.login(body["password"])
            )
            response = self.response(
                "auth-result",
                {"run_id": self.host.run_id, "auth_state": "authenticated", "csrf_token": csrf},
            )
            response.set_cookie(
                COOKIE, token, httponly=True, samesite="strict", path="/", secure=False
            )
            return response
        if path == "/api/v1/auth/logout" and request.method == "POST":
            context = self.sessions.validate(request, mutation=True)
            validate_contract(
                "urn:soma:00:empty-request:v1", loads_strict_bytes(raw, max_bytes=4096)
            )
            self.sessions.logout(context)
            response = self.response(
                "auth-result",
                {"run_id": self.host.run_id, "auth_state": "login_required", "csrf_token": None},
            )
            response.delete_cookie(COOKIE, path="/", httponly=True, samesite="strict")
            return response
        if path == "/api/v1/diagnostics" and request.method == "GET":
            self.sessions.validate(request)
            return self.response("diagnostics", self.diagnostics())
        if (
            path in {"/api/v1/diagnostics/open-log", "/api/v1/diagnostics/open-folder"}
            and request.method == "POST"
        ):
            self.sessions.validate(request, mutation=True)
            validate_contract(
                "urn:soma:00:empty-request:v1", loads_strict_bytes(raw, max_bytes=4096)
            )
            os.startfile(
                self.host.log.path
                if path.endswith("open-log")
                else self.host.config.path("diagnostics")
            )
            return self.response("empty-request", {})
        raise SomaError("NOT_FOUND", "This API operation is not available.")

    @staticmethod
    def response(kind, value):
        validate_contract("urn:soma:00:" + kind + ":v1", value)
        return JSONResponse(
            value, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
        )
