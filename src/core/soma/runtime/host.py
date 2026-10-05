import os
import secrets
import socket
import threading
import time

import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from soma.foundation.build import current_build
from soma.foundation.context import correlation_scope
from soma.foundation.contracts import validate_contract
from soma.foundation.development.database import factory_for_lease
from soma.foundation.diagnostics import RunLog
from soma.foundation.errors import SomaError, error_envelope
from soma.foundation.filesystem import OwnedArtifact, atomic_write, remove_owned
from soma.foundation.filesystem.windows_acl import protect_owner
from soma.foundation.identity import new_uuid4
from soma.foundation.jobs import Coordinator
from soma.foundation.persistence.instance import InstanceLease
from soma.foundation.persistence.manifest import MigrationManifest
from soma.foundation.persistence.migrations import MigrationRunner
from soma.foundation.persistence.schema_verify import verify_schema
from soma.foundation.security.dpapi import WindowsDpapiProvider
from soma.foundation.strict_json import canonical_json_bytes, loads_strict_bytes
from soma.foundation.time import utc_epoch_seconds
from soma.runtime.control import authenticate, guard_request, verify_current
from soma.runtime.executor import BoundedExecutor, JobWorkers
from soma.runtime.static import StaticAssets, CSP
from soma.runtime.windows import process_identity

from soma.runtime.lifecycle import TRANSITIONS


class Host:
    def __init__(
        self,
        config,
        *,
        console=False,
        job_contracts=(),
        job_handlers=None,
        tray=True,
        copy_contracts=(),
        proof_actions=(),
        profile_participant=None,
        reference=False,
    ):
        self.config, self.console, self.with_tray = config, console, tray
        self.job_contracts, self.job_handlers = job_contracts, job_handlers or {}
        self.copy_contracts, self.proof_actions = copy_contracts, proof_actions
        self.profile_participant = profile_participant
        self.with_reference = reference
        self.state = "BOOTSTRAPPING"
        self.shutdown_requested = threading.Event()
        self.lease = None
        self.resources = []
        self.log = None
        self.server = self.thread = self.socket = self.requests = self.jobs = self.tray = None

    def transition(self, state):
        if state not in TRANSITIONS[self.state]:
            raise SomaError("RUNTIME_TRANSITION_INVALID", "Invalid runtime state transition.")
        self.state = state
        if self.log:
            self.log.emit("RUNTIME_" + state, state=state)
        if self.tray:
            self.tray.update(state)

    def start(self):
        if self.state != "BOOTSTRAPPING" or hasattr(self, "run_id"):
            raise SomaError("RUNTIME_TRANSITION_INVALID", "A host process starts only once.")
        self.run_id = new_uuid4()
        self.startup = utc_epoch_seconds()
        self.started_monotonic = time.monotonic()
        try:
            self.lease = InstanceLease(self.config).__enter__()
            self.log = RunLog(self.config, self.run_id, console=self.console)
            if self.with_tray:
                from soma.runtime.tray import Tray

                self.tray = Tray(self)
                self.tray.start()
            self.process = process_identity(os.getpid())
            # Stale/foreign runtime resources are never replaced silently.
            if self.config.path("runtime", "runtime.json").exists():
                raise SomaError(
                    "RUNTIME_ARTIFACT_CONFLICT",
                    "Existing runtime state requires explicit inspection.",
                    "restart",
                )
            self.factory = factory_for_lease(self.lease)
            self.manifest = MigrationManifest.load()
            self.transition("MIGRATING")
            MigrationRunner(self.factory, self.manifest).initialize_or_migrate()
            connection = self.factory.open()
            try:
                verify_schema(connection, self.manifest, instance_id=self.lease.instance_id)
            finally:
                connection.close()
            if self.with_reference:
                from soma.composition import reference

                self.reference = reference(self.factory)
                self.profile_participant = self.reference.profile
            route_matchers = ()
            if self.with_reference:
                from soma.modules.reference.transport.routes import main_route

                route_matchers = (main_route,)
            self.static = StaticAssets(self.config.checkout_root, route_matchers=route_matchers)
            self.requests = BoundedExecutor(4)
            self.jobs = JobWorkers(
                Coordinator(self.factory, self.job_contracts),
                self.job_handlers,
                self.run_id,
                self.log,
            )
            self.secret = secrets.token_bytes(32)
            secret_path = self.config.path("runtime", f"run-{self.run_id}.dpapi")
            atomic_write(
                self.config.instance_root,
                secret_path.relative_to(self.config.instance_root),
                WindowsDpapiProvider().protect_current_user(
                    self.secret, "run_control", self.run_id
                ),
                protect=protect_owner,
            )
            self.resources.append(
                OwnedArtifact.capture(
                    self.config.instance_root, secret_path.relative_to(self.config.instance_root)
                )
            )
            self.transition("BINDING")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            self.socket.bind(("127.0.0.1", 0))
            self.origin = "http://127.0.0.1:" + str(self.socket.getsockname()[1])
            from soma.transport.browser import Browser

            self.browser = Browser(self)
            self.server = uvicorn.Server(
                uvicorn.Config(
                    self.app(),
                    host="127.0.0.1",
                    log_config=None,
                    access_log=False,
                    proxy_headers=False,
                    ws="none",
                    server_header=False,
                    lifespan="off",
                    timeout_graceful_shutdown=10,
                )
            )
            self.thread = threading.Thread(target=self._serve, name="soma-http", daemon=True)
            self.thread.start()
            deadline = time.monotonic() + 5
            while not self.server.started:
                if not self.thread.is_alive() or time.monotonic() >= deadline:
                    raise SomaError(
                        "RUNTIME_LISTEN_FAILED", "The local server failed to listen.", "restart"
                    )
                time.sleep(0.02)
            self.transition("SERVING_NOT_READY")
            self.record = {
                "registry_version": 1,
                "origin": self.origin,
                "pid": self.process.pid,
                "process_birth_id": self.process.process_birth_id,
                "run_id": self.run_id,
                "protocol_version": 1,
                "data_instance_id": self.lease.instance_id,
                "protected_secret": secret_path.name,
                "published_at_utc_s": utc_epoch_seconds(),
            }
            registry = self.config.path("runtime", "runtime.json")
            atomic_write(
                self.config.instance_root,
                registry.relative_to(self.config.instance_root),
                canonical_json_bytes(self.record),
                protect=protect_owner,
            )
            self.resources.append(
                OwnedArtifact.capture(
                    self.config.instance_root, registry.relative_to(self.config.instance_root)
                )
            )
            verify_current(self.config, allow_starting=True)
            self.jobs.start()
            self.transition("READY")
            verify_current(self.config)
            if self.console:
                print("SOMA READY " + self.origin, flush=True)
            return self.health()
        except BaseException:
            self.transition("FAILED")
            self._cleanup(5)
            raise

    def _serve(self):
        try:
            self.server.run(sockets=[self.socket])
        except BaseException:
            if self.log:
                self.log.emit("RUNTIME_SERVER_FAILED")
            self.shutdown_requested.set()

    def health(self):
        result = {
            "protocol_version": 1,
            "run_id": self.run_id,
            "data_instance_id": self.lease.instance_id,
            "host_state": self.state,
            "build": current_build().as_dict(),
            "pid": self.process.pid,
            "process_birth_id": self.process.process_birth_id,
            "migration_generation": self.manifest.generation,
            "last_migration_id": self.manifest.entries[-1].migration_id,
            "schema_state": "current",
            "integrity_state": "verified",
            "startup_utc_s": self.startup,
        }
        return validate_contract("urn:soma:00:runtime-health:v1", result)

    def app(self):
        async def route(request):
            correlation = None
            try:
                guard_request(request, self.origin)
                with correlation_scope(request.headers.get("x-correlation-id")) as correlation:
                    if request.url.path == "/api/v1/runtime/health":
                        authenticate(request, self)
                        return JSONResponse(self.health())
                    if request.url.path == "/api/v1/runtime/shutdown":
                        authenticate(request, self)
                        raw = await bounded_body(request)
                        body = loads_strict_bytes(raw, max_bytes=4096)
                        validate_contract("urn:soma:00:runtime-shutdown-request:v1", body)
                        if body != {
                            "run_id": self.run_id,
                            "data_instance_id": self.lease.instance_id,
                        }:
                            raise SomaError(
                                "RUNTIME_TRUST_FAILED", "Shutdown identity does not match."
                            )
                        self.shutdown_requested.set()
                        return JSONResponse(
                            {"run_id": self.run_id, "data_instance_id": self.lease.instance_id}
                        )
                    if self.state != "READY":
                        raise SomaError("HOST_NOT_READY", "SOMA is not ready.", "retry")
                    if request.url.path.startswith("/api/"):
                        raw = (
                            await bounded_body(
                                request,
                                max_bytes=2097152
                                if request.url.path == "/api/v1/working-copies/checkpoint"
                                else 16384
                                if request.url.path.startswith("/api/v1/settings/")
                                else 8192,
                            )
                            if request.method != "GET"
                            else b""
                        )
                        return await self.requests.run(self.browser.handle, request, raw)
                    if request.method != "GET":
                        return Response(status_code=405)
                    asset = self.static.resolve(request.url.path)
                    if asset is None:
                        return Response(status_code=404)
                    return Response(
                        asset[0],
                        media_type=asset[1],
                        headers={
                            "Content-Security-Policy": CSP,
                            "X-Content-Type-Options": "nosniff",
                            "Cache-Control": "no-store",
                        },
                    )
            except Exception as exc:
                with correlation_scope():
                    code = exc.code if isinstance(exc, SomaError) else "INTERNAL_ERROR"
                    status = {
                        "UNAUTHENTICATED": 401,
                        "FORBIDDEN": 403,
                        "RUNTIME_TRUST_FAILED": 403,
                        "NOT_FOUND": 404,
                        "INTERNAL_ERROR": 500,
                    }.get(code, 400)
                    return JSONResponse(
                        error_envelope(exc, correlation),
                        status_code=status,
                        headers={"Cache-Control": "no-store"},
                    )

        return Starlette(
            routes=[Route("/{path:path}", route, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])]
        )

    def stop(self, *, budget=10):
        if self.state == "EXITING":
            return True
        if self.state not in {"QUIESCING", "FAILED"}:
            self.transition("QUIESCING")
        complete = self._cleanup(budget)
        if complete and self.state != "FAILED":
            self.transition("EXITING")
        return complete

    def _cleanup(self, budget):
        deadline = time.monotonic() + budget
        if self.requests:
            self.requests.quiesce()
        if self.jobs and not self.jobs.stop(max(0, deadline - time.monotonic())):
            if self.log:
                self.log.emit("RUNTIME_SHUTDOWN_TIMEOUT")
            return False  # retain ownership while handlers may still mutate
        if self.server:
            self.server.should_exit = True
        if self.thread:
            self.thread.join(max(0, deadline - time.monotonic()))
            if self.thread.is_alive():
                return False
        if self.requests and not self.requests.drain(max(0, deadline - time.monotonic())):
            return False
        if self.requests:
            self.requests.close()
        if hasattr(self, "browser"):
            self.browser.sessions.clear()
            self.browser.proofs.clear()
        if self.tray:
            self.tray.close()
        if self.socket:
            self.socket.close()
        for artifact in reversed(self.resources):
            remove_owned(self.config.instance_root, artifact)
        self.resources.clear()
        if self.lease:
            self.lease.__exit__(None, None, None)
            self.lease = None
        self.secret = None
        return True


async def bounded_body(request, max_bytes=1048576):
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > max_bytes:
            raise SomaError("VALIDATION_ERROR", "Request exceeds its byte bound.")
    return bytes(body)
