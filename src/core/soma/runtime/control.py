import base64
import hmac
import re
import sys

from soma.foundation.errors import SomaError
from soma.foundation.filesystem import OwnedArtifact, safe_path
from soma.foundation.identity import require_uuid4
from soma.foundation.security.dpapi import WindowsDpapiProvider
from soma.foundation.strict_json import canonical_json_bytes, loads_strict_bytes
from soma.runtime.windows import process_identity, verify_owner, VerifiedProcessWait

FIELDS = {
    "registry_version",
    "origin",
    "pid",
    "process_birth_id",
    "run_id",
    "protocol_version",
    "data_instance_id",
    "protected_secret",
    "published_at_utc_s",
}


def trust_failure():
    return SomaError(
        "RUNTIME_TRUST_FAILED", "The exact local SOMA run could not be verified.", "restart"
    )


def encode_secret(secret):
    return base64.urlsafe_b64encode(secret).decode("ascii")


def guard_request(request, origin):
    headers = request.headers
    if (
        len(headers.getlist("host")) != 1
        or headers["host"] != origin.removeprefix("http://")
        or any(
            name.lower()
            in {"forwarded", "x-forwarded-host", "x-forwarded-for", "x-forwarded-proto"}
            for name, value in headers.items()
        )
    ):
        raise trust_failure()


def owned_read(config, relative, limit=65536):
    path = safe_path(config.instance_root, relative)
    verify_owner(path.parent)
    verify_owner(path)
    artifact = OwnedArtifact.capture(config.instance_root, path.relative_to(config.instance_root))
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit or not artifact.matches(config.instance_root):
        raise trust_failure()
    return raw


def direct_request(record, secret, route, *, body=None, timeout=2):
    import http.client
    import socket
    import threading
    import time

    match = re.fullmatch(r"http://127\.0\.0\.1:([1-9][0-9]{0,4})", record["origin"])
    if (
        match is None
        or int(match[1]) > 65535
        or not 0 < timeout <= 2
        or len(secret) != 32
        or route not in {"/api/v1/runtime/health", "/api/v1/runtime/shutdown"}
    ):
        raise trust_failure()
    connection = http.client.HTTPConnection("127.0.0.1", int(match[1]), timeout=timeout)
    timer = None
    deadline = time.monotonic() + timeout
    try:
        connection.connect()
        retained = connection.sock
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise trust_failure()
        retained.settimeout(remaining)

        def expire():
            try:
                retained.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        timer = threading.Timer(remaining, expire)
        timer.daemon = True
        timer.start()
        headers = {
            "Authorization": "SomaRun " + encode_secret(secret),
            "X-Soma-Run": record["run_id"],
            "X-Soma-Data": record["data_instance_id"],
            "Host": record["origin"].removeprefix("http://"),
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        connection.request(
            "GET" if body is None else "POST",
            route,
            body=None if body is None else canonical_json_bytes(body),
            headers=headers,
        )
        response = connection.getresponse()
        if response.status != 200 or response.getheader("Location") is not None:
            raise trust_failure()
        raw = response.read(65537)
        if time.monotonic() >= deadline:
            raise trust_failure()
        return loads_strict_bytes(raw, max_bytes=65536)
    except (OSError, http.client.HTTPException):
        raise SomaError("RUNTIME_UNREACHABLE", "The exact local host is unreachable.", "retry") from None
    finally:
        if timer is not None:
            timer.cancel()
        connection.close()


def inspect_candidate(config):
    registry = config.path("runtime", "runtime.json")
    if not registry.exists():
        # An owned instance can be bootstrapping before registry publication.
        # Inspect the existing lock without creating files or altering its bytes.
        import msvcrt

        lock = config.path("data", "soma.instance.lock")
        if lock.exists():
            path = safe_path(config.instance_root, "data/soma.instance.lock")
            verify_owner(path.parent)
            verify_owner(path)
            with path.open("r+b", buffering=0) as handle:
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError:
                    raise SomaError("RUNTIME_CANDIDATE", "Instance ownership is not yet verified.") from None
                else:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return None
    try:
        record = loads_strict_bytes(
            owned_read(config, "runtime/runtime.json", 16384), max_bytes=16384
        )
        if (
            type(record) is not dict
            or set(record) != FIELDS
            or type(record["registry_version"]) is not int
            or record["registry_version"] != 1
            or type(record["protocol_version"]) is not int
            or record["protocol_version"] != 1
        ):
            raise trust_failure()
        match = re.fullmatch(r"http://127\.0\.0\.1:([1-9][0-9]{0,4})", record["origin"])
        if (
            match is None
            or int(match[1]) > 65535
            or type(record["published_at_utc_s"]) is not int
            or record["published_at_utc_s"] < 0
        ):
            raise trust_failure()
        require_uuid4(record["run_id"])
        require_uuid4(record["data_instance_id"])
        if record["protected_secret"] != "run-" + record["run_id"] + ".dpapi":
            raise trust_failure()
        process = process_identity(record["pid"])
        # Windows venv launchers run the base interpreter executable.
        expected = {
            __import__("pathlib").Path(sys.executable).resolve(),
            __import__("pathlib").Path(sys._base_executable).resolve(),
        }
        if process.process_birth_id != record["process_birth_id"] or process.image not in expected:
            raise trust_failure()
        return record, process
    except SomaError as exc:
        if exc.code == "RUNTIME_PROCESS_STALE":
            raise
        raise trust_failure() from None
    except Exception:
        raise trust_failure() from None


def verify_candidate(config, candidate):
    record, process = candidate
    try:
        raw = owned_read(config, "runtime/" + record["protected_secret"], 65664)
        secret = WindowsDpapiProvider().unprotect_current_user(raw, "run_control", record["run_id"])
        health = direct_request(record, secret, "/api/v1/runtime/health")
        from soma.foundation.contracts import validate_contract

        validate_contract("urn:soma:00:runtime-health:v1", health)
        if any(
            health[key] != record[key]
            for key in ("run_id", "data_instance_id", "pid", "process_birth_id", "protocol_version")
        ):
            raise trust_failure()
        return (record, secret, process), health
    except SomaError as exc:
        if exc.code == "RUNTIME_UNREACHABLE":
            raise
        raise trust_failure() from None
    except Exception:
        raise trust_failure() from None


def verify_current(config, *, allow_starting=False):
    from soma.runtime.observation import observe

    result = observe(config)
    if result.state == "absent":
        return None
    allowed = {"verified_ready", "verified_not_ready"} if allow_starting else {"verified_ready"}
    if result.state not in allowed:
        raise trust_failure()
    return result.verified


def stop_current(config):
    verified = verify_current(config, allow_starting=True)
    if verified is None:
        return True
    record, secret, process = verified
    # Retained process handle prevents PID reuse from satisfying the stop wait.
    wait = VerifiedProcessWait(process)
    try:
        direct_request(
            record,
            secret,
            "/api/v1/runtime/shutdown",
            body={"run_id": record["run_id"], "data_instance_id": record["data_instance_id"]},
        )
        return wait.wait(10)
    finally:
        wait.close()


def authenticate(request, host):
    guard_request(request, host.origin)
    headers = request.headers
    expected = "SomaRun " + encode_secret(host.secret)
    if (
        len(headers.getlist("authorization")) != 1
        or not hmac.compare_digest(headers.get("authorization", ""), expected)
        or headers.get("x-soma-run") != host.run_id
        or headers.get("x-soma-data") != host.lease.instance_id
    ):
        raise trust_failure()
