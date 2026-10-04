# ruff: noqa: F811 -- pytest discovers imported native fixtures by name
import os
from pathlib import Path
import shutil
import threading
import time
import urllib.error
import urllib.request

import pytest

from soma.composition import CapabilityRegistry
from soma.foundation.config import RuntimeConfig
from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.filesystem import atomic_write
from soma.foundation.filesystem.windows_acl import protect_owner
from soma.foundation.persistence.status import migration_status
from soma.foundation.strict_json import canonical_json_bytes
from soma.runtime.control import direct_request, stop_current, verify_current
from soma.runtime.executor import BoundedExecutor, JobWorkers
from soma.runtime.host import Host
from soma.runtime.windows import verify_owner
from test_execution import coordinator, enqueue
from test_persistence import database  # noqa: F401 -- native encrypted fixture

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def runtime_config(tmp_path):
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "src/main/dist", checkout / "src/main/dist")
    shutil.copytree(ROOT / "src/main/assets/brand", checkout / "src/main/assets/brand")
    return RuntimeConfig(tmp_path / "instance", checkout, "test")


@pytest.fixture
def host(runtime_config):
    runtime = Host(runtime_config, tray=False)
    runtime.start()
    yield runtime
    assert runtime.stop()


def get(origin, path):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(origin + path, timeout=2)


def test_real_host_ready_trust_and_exact_cleanup(host):
    verified = verify_current(host.config)
    assert verified[0]["run_id"] == host.run_id
    assert host.health()["host_state"] == "READY"
    assert migration_status(host.config) == {"status": "verified_live_current"}
    assert host.secret not in host.config.path("runtime", "runtime.json").read_bytes()
    verify_owner(host.config.path("runtime", "runtime.json"))
    with get(host.origin, "/") as response:
        assert (
            response.status == 200
            and "unsafe-eval" not in response.headers["Content-Security-Policy"]
        )
    for path in ("/api/unknown", "/assets/missing.js", "/unregistered"):
        with pytest.raises(urllib.error.HTTPError) as error:
            get(host.origin, path)
        assert error.value.code == 404
    with pytest.raises(urllib.error.HTTPError) as error:
        get(host.origin, "/api/v1/runtime/health")
    assert error.value.code == 403


@pytest.mark.parametrize(
    "field,value",
    [
        ("origin", "http://localhost:1234"),
        ("origin", "http://127.0.0.1:0"),
        ("pid", 99999999),
        ("process_birth_id", "1"),
        ("run_id", "00000000-0000-4000-8000-000000000001"),
        ("data_instance_id", "00000000-0000-4000-8000-000000000002"),
        ("protocol_version", 2),
        ("protected_secret", "../foreign"),
        ("extra", "foreign"),
    ],
)
def test_registry_adversaries_fail_closed_and_preserve_artifacts(host, field, value):
    record = dict(host.record)
    record[field] = value
    path = host.config.path("runtime", "runtime.json")
    original = path.read_bytes()
    atomic_write(
        host.config.instance_root,
        "runtime/runtime.json",
        canonical_json_bytes(record),
        protect=protect_owner,
    )
    with pytest.raises(SomaError):
        verify_current(host.config)
    assert path.exists() and path.read_bytes() == canonical_json_bytes(record)
    # Replaced artifacts must survive host cleanup; clean only our exact test file.
    assert host.stop() and path.exists()
    path.unlink()
    assert original != canonical_json_bytes(record)


def test_wrong_secret_run_identity_and_proxy_headers_are_denied(host):
    with pytest.raises(SomaError) as error:
        direct_request(host.record, os.urandom(32), "/api/v1/runtime/health")
    assert error.value.code == "RUNTIME_TRUST_FAILED"
    request = urllib.request.Request(
        host.origin + "/api/v1/runtime/health",
        headers={"Host": "foreign.invalid", "Forwarded": "for=127.0.0.1"},
    )
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request)
    assert error.value.code == 403


def test_exact_authenticated_shutdown_and_repeated_stop(host):
    worker = threading.Thread(target=lambda: (host.shutdown_requested.wait(3), host.stop()))
    worker.start()
    # This host lives inside pytest; its process deliberately remains alive.
    direct_request(
        host.record,
        host.secret,
        "/api/v1/runtime/shutdown",
        body={"run_id": host.run_id, "data_instance_id": host.lease.instance_id},
    )
    worker.join(3)
    assert host.state == "EXITING" and stop_current(host.config)
    assert not host.config.path("runtime", "runtime.json").exists()


def test_failed_static_start_never_ready_and_releases_owned_resources(runtime_config):
    (runtime_config.checkout_root / "src/main/dist/index.html").write_text("tampered")
    runtime = Host(runtime_config, tray=False)
    with pytest.raises(SomaError) as caught:
        runtime.start()
    assert caught.value.code == "STATIC_ASSETS_INVALID"
    assert runtime.state == "FAILED" and runtime.lease is None
    assert not runtime_config.path("runtime", "runtime.json").exists()


def test_native_tray_is_one_owned_icon_and_failure_is_optional(runtime_config, monkeypatch):
    runtime = Host(runtime_config)
    runtime.start()
    assert runtime.tray.registered
    assert "TRAY_READY" not in runtime.log.snapshot()["recent_codes"]
    assert "TRAY_READY" in [event["code"] for event in runtime.log.snapshot()["runtime_events"]]
    runtime.tray.update("QUIESCING")
    assert runtime.stop() and not runtime.tray.registered
    from soma.runtime.tray import Tray

    def failure(self):
        self.host.log.emit("TRAY_UNAVAILABLE")
        self.ready.set()

    monkeypatch.setattr(Tray, "_loop", failure)
    runtime = Host(runtime_config)
    runtime.start()
    assert not runtime.tray.registered and verify_current(runtime_config)
    assert "TRAY_UNAVAILABLE" in runtime.log.snapshot()["recent_codes"]
    assert runtime.stop()


def test_diagnostic_events_and_failures_are_bounded_separate_and_schema_valid(host):
    from soma.foundation.contracts import validate_contract

    host.log.emit("TRAY_READY", kind="event")
    host.log.emit("RUNTIME_SHUTDOWN_TIMEOUT")
    host.log.emit("JOB_RECOVERY_REQUIRED", kind="warning")
    result = host.browser.diagnostics()
    validate_contract("urn:soma:00:diagnostics:v1", result)
    assert "RUNTIME_READY" in [event["code"] for event in result["runtime_events"]]
    assert "TRAY_READY" in [event["code"] for event in result["runtime_events"]]
    assert result["recent_codes"] == ["RUNTIME_SHUTDOWN_TIMEOUT", "JOB_RECOVERY_REQUIRED"]
    for _ in range(25):
        host.log.emit("RUNTIME_READY", kind="event")
    assert len(host.log.snapshot()["runtime_events"]) == 20
    assert host.log.snapshot()["recent_codes"] == result["recent_codes"]


def test_diagnostic_partial_provider_preserves_safe_facts(host, monkeypatch):
    from soma.foundation.contracts import validate_contract
    from soma.foundation.jobs import Coordinator

    def failure(*args):
        raise RuntimeError("Sensitive raw exception SQL or credential must not escape")

    monkeypatch.setattr(Coordinator, "counts", failure)
    result = host.browser.diagnostics()
    validate_contract("urn:soma:00:diagnostics:v1", result)
    assert result["partial"] == ["jobs"] and result["job_counts"] is None
    assert result["health"]["host_state"] == "READY"
    assert "Sensitive" not in repr(result)
    assert result["logging_available"] and result["runtime_events"]


def test_shutdown_timeout_retains_instance_ownership(host):
    release = threading.Event()
    future = host.requests.submit(release.wait, 3)
    assert not host.stop(budget=0.01)
    assert host.state == "QUIESCING" and host.lease.held
    assert host.config.path("runtime", "runtime.json").exists()
    release.set()
    future.result(3)
    assert host.stop()


def test_offline_status_does_not_create_or_repair(runtime_config):
    assert migration_status(runtime_config) == {"status": "not_initialized"}
    assert not runtime_config.instance_root.exists()
    runtime = Host(runtime_config, tray=False)
    runtime.start()
    runtime.stop()
    paths = {
        p.relative_to(runtime_config.instance_root): (p.stat().st_mtime_ns, p.read_bytes())
        for p in runtime_config.instance_root.rglob("*")
        if p.is_file()
    }
    assert migration_status(runtime_config) == {"status": "current"}
    assert paths == {
        p.relative_to(runtime_config.instance_root): (p.stat().st_mtime_ns, p.read_bytes())
        for p in runtime_config.instance_root.rglob("*")
        if p.is_file()
    }
    runtime_config.path("data", "soma.db-wal").touch()
    assert migration_status(runtime_config) == {"status": "unsafe_sidecars"}


def test_executor_is_bounded_and_quiesces():
    executor = BoundedExecutor(1, 1)
    release = threading.Event()
    futures = [executor.submit(release.wait, 3) for _ in range(2)]
    with pytest.raises(SomaError):
        executor.submit(lambda: None)
    assert not executor.drain(0.01)
    with pytest.raises(SomaError):
        executor.submit(lambda: None)
    release.set()
    for future in futures:
        future.result(3)
    assert executor.drain(1)
    executor.close()


def test_background_handler_has_no_open_transaction_and_checkpoints_on_quiesce(database):
    _, _, factory, _ = database
    jobs = coordinator(factory, [100], validate_failure=lambda *a: None)
    identity = enqueue(jobs, factory)
    started = threading.Event()

    class Log:
        def emit(self, code):
            pass

    def handler(claim, cancel, coordinator):
        from soma.foundation.transactions import UnitOfWork

        with UnitOfWork(factory) as uow:
            assert coordinator.assert_current(uow, claim)["job_id"] == identity
        started.set()
        cancel.wait(3)
        coordinator.checkpoint(claim, {"value": 9})

    workers = JobWorkers(
        jobs, {("probe", 1): handler}, "00000000-0000-4000-8000-000000000001", Log()
    )
    workers.start()
    assert started.wait(2)
    assert workers.stop(2)
    assert jobs.recover("00000000-0000-4000-8000-000000000002") == 1


def test_capabilities_require_real_provider_and_reject_conflicts():
    registry = CapabilityRegistry()
    with pytest.raises(ValidationError):
        registry.register("stub", "available")
    registry.register("real", "available", provider=object())
    registry.register("absent", "unavailable", reason="NOT_IMPLEMENTED")
    registry.register("dev", "development")
    with pytest.raises(ValidationError):
        registry.register("real", "unavailable")
    assert [item["id"] for item in registry.snapshot()] == ["absent", "dev", "real"]


def test_composition_does_not_fabricate_future_capabilities():
    from soma.composition import capabilities

    assert {item["id"] for item in capabilities()} == {
        "foundation.runtime", "foundation.diagnostics"
    }


def test_host_lifecycle_is_one_way_and_normal_events_are_not_errors(runtime_config):
    runtime = Host(runtime_config, tray=False)
    states = [runtime.state]
    transition = runtime.transition

    def track(state):
        transition(state)
        states.append(state)

    runtime.transition = track
    runtime.start()
    assert list(runtime.log.errors) == []
    assert runtime.stop() and runtime.stop()
    assert states == ["BOOTSTRAPPING", "MIGRATING", "BINDING", "SERVING_NOT_READY", "READY", "QUIESCING", "EXITING"]
    with pytest.raises(SomaError):
        runtime.transition("BOOTSTRAPPING")


def test_controller_observations_are_independent_and_fail_closed(host, monkeypatch):
    from soma.runtime.observation import observe
    import soma.runtime.control as control

    assert observe(host.config, verify=False).state == "candidate"
    result = observe(host.config)
    assert result.state == "verified_ready" and result.host_state == "READY"
    assert host.secret.hex() not in repr(result)
    host.state = "SERVING_NOT_READY"
    assert observe(host.config).state == "verified_not_ready"
    with pytest.raises(SomaError):
        verify_current(host.config)
    assert verify_current(host.config, allow_starting=True)
    host.state = "READY"
    original = control.direct_request

    def unreachable(*args, **kwargs):
        raise SomaError("RUNTIME_UNREACHABLE", "Unavailable")

    monkeypatch.setattr(control, "direct_request", unreachable)
    assert observe(host.config).state == "unreachable"
    assert host.state == "READY"
    monkeypatch.setattr(control, "direct_request", original)
    assert host.stop()
    assert observe(host.config).state == "absent"


def test_owned_instance_without_registry_is_candidate_not_absent(host):
    from soma.runtime.observation import observe

    registry = host.config.path("runtime", "runtime.json")
    held = registry.with_name("held-registry.json")
    registry.rename(held)
    try:
        assert observe(host.config).state == "candidate"
        with pytest.raises(SomaError):
            verify_current(host.config)
    finally:
        held.rename(registry)


@pytest.mark.parametrize("field,value,state", [
    ("pid", 99999999, "stale"),
    ("process_birth_id", "1", "untrusted"),
    ("origin", "http://localhost:1234", "untrusted"),
    ("protocol_version", 2, "untrusted"),
])
def test_controller_preserves_stale_and_untrusted_candidates(host, field, value, state):
    from soma.runtime.observation import observe

    record = dict(host.record)
    record[field] = value
    atomic_write(host.config.instance_root, "runtime/runtime.json", canonical_json_bytes(record), protect=protect_owner)
    assert observe(host.config).state == state
    assert host.config.path("runtime", "runtime.json").read_bytes() == canonical_json_bytes(record)
    assert host.stop()
    host.config.path("runtime", "runtime.json").unlink()


def test_real_browser_foundation_convergence(runtime_config):
    import subprocess

    runtime = Host(runtime_config, tray=False)
    runtime.start()
    try:
        node = shutil.which("node")
        assert node, "Put the pinned Node 24 development installation on PATH."
        completed = subprocess.run(
            [node, "browser-tests/foundation.mjs", runtime.origin],
            cwd=ROOT / "src/main", capture_output=True, text=True, timeout=120,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        print(completed.stdout)
    finally:
        assert runtime.stop()


@pytest.mark.parametrize("mode", ["redirect", "slow_body", "proxy"])
def test_control_http_is_direct_and_obeys_absolute_deadline(mode, monkeypatch):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    calls = []

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def do_GET(self):
            calls.append(self.path)
            self.send_response(302 if mode == "redirect" else 200)
            if mode == "redirect":
                self.send_header("Location", "/foreign")
            self.end_headers()
            if mode == "slow_body":
                time.sleep(0.5)
            try:
                self.wfile.write(b"{}")
            except OSError:
                pass

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    record = {
        "origin": f"http://127.0.0.1:{server.server_port}",
        "run_id": "00000000-0000-4000-8000-000000000001",
        "data_instance_id": "00000000-0000-4000-8000-000000000002",
    }
    try:
        monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
        started = time.monotonic()
        if mode == "proxy":
            assert (
                direct_request(record, os.urandom(32), "/api/v1/runtime/health", timeout=0.1) == {}
            )
        else:
            with pytest.raises(SomaError):
                direct_request(record, os.urandom(32), "/api/v1/runtime/health", timeout=0.1)
            assert time.monotonic() - started < 0.4
        assert calls == ["/api/v1/runtime/health"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(1)
