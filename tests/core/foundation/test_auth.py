# ruff: noqa: F811 -- shared native pytest fixtures
import json
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

import pytest
from argon2 import PasswordHasher, Type

from soma.foundation.errors import SomaError
from soma.foundation.identity import new_uuid4
from soma.foundation.query import CursorCodec
from soma.foundation.security.passwords import Passwords, AuthenticationThrottle
from soma.foundation.security.sessions import Sessions
from test_runtime import host, runtime_config  # noqa: F401


def client():
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(CookieJar())
    )


def request(client, host, path, body=None, **headers):
    if body is not None:
        headers = {
            "Origin": host.origin,
            "Content-Type": "application/json",
            "X-SOMA-Run": host.run_id,
            **headers,
        }
    req = urllib.request.Request(
        host.origin + path,
        data=None if body is None else json.dumps(body).encode(),
        headers=headers,
    )
    with client.open(req, timeout=3) as response:
        return json.loads(response.read()), response.headers


def test_exact_unicode_password_profile_and_no_hidden_normalization():
    passwords = Passwords()
    value = "  éabcdefghijk  "
    phc = passwords.hash(value, value)
    assert phc.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    assert passwords.verify(phc, value)
    assert not passwords.verify(phc, value.strip())
    assert not passwords.verify(phc, "  e\u0301abcdefghijk  ")
    alternate = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1, type=Type.ID).hash(
        value
    )
    assert not passwords.verify(alternate, value)
    assert not passwords.verify("malformed", value)


@pytest.mark.parametrize("password", ["short", "x" * 1025, "é" * 513, "\ud800" * 12, None])
def test_password_policy_never_echoes_input(password):
    with pytest.raises(SomaError) as error:
        Passwords().hash(password, password)
    assert error.value.code == "AUTH_PASSWORD_POLICY"


def test_throttle_monotonic_bound_and_success_reset():
    now = [100]
    throttle = AuthenticationThrottle(monotonic=lambda: now[0])
    for attempt in range(1, 10):
        throttle.check()
        throttle.record(False)
        delay = min(8, 2 ** (attempt - 5)) if attempt >= 5 else 0
        assert throttle.next_allowed == now[0] + delay
        if delay:
            with pytest.raises(SomaError) as error:
                throttle.check()
            assert error.value.code == "AUTH_INVALID_CREDENTIALS"
        now[0] += delay
    throttle.record(True)
    assert throttle.failures == 0 and throttle.next_allowed == now[0]


def test_setup_login_logout_real_http_keeps_secrets_out_of_evidence(host):
    browser = client()
    bootstrap, _ = request(browser, host, "/api/v1/bootstrap")
    assert bootstrap["auth_state"] == "setup_required"
    password = "Foundation test password 42"
    result, headers = request(
        browser,
        host,
        "/api/v1/auth/setup",
        {"run_id": host.run_id, "password": password, "confirmation": password},
    )
    assert result["auth_state"] == "authenticated"
    cookie = headers["Set-Cookie"]
    assert (
        "HttpOnly" in cookie
        and "samesite=strict" in cookie.lower()
        and "Path=/" in cookie
        and "Domain=" not in cookie
        and "Secure" not in cookie
    )
    bootstrap, _ = request(browser, host, "/api/v1/bootstrap")
    assert bootstrap["auth_state"] == "authenticated"
    diagnostics, _ = request(browser, host, "/api/v1/diagnostics")
    assert diagnostics["health"]["run_id"] == host.run_id
    with pytest.raises(urllib.error.HTTPError) as error:
        request(browser, host, "/api/v1/auth/logout", {})
    assert error.value.code == 403
    request(browser, host, "/api/v1/auth/logout", {}, **{"X-SOMA-CSRF": bootstrap["csrf_token"]})
    assert request(browser, host, "/api/v1/bootstrap")[0]["auth_state"] == "login_required"
    with pytest.raises(urllib.error.HTTPError) as error:
        request(
            browser,
            host,
            "/api/v1/auth/login",
            {"run_id": host.run_id, "password": "not the correct password"},
        )
    assert json.loads(error.value.read())["code"] == "AUTH_INVALID_CREDENTIALS"
    request(browser, host, "/api/v1/auth/login", {"run_id": host.run_id, "password": password})
    with pytest.raises(urllib.error.HTTPError) as error:
        request(
            browser,
            host,
            "/api/v1/auth/setup",
            {"run_id": host.run_id, "password": password, "confirmation": password},
        )
    assert json.loads(error.value.read())["code"] == "AUTH_ALREADY_CONFIGURED"
    c = host.factory.open()
    try:
        phc = c.execute("SELECT password_phc FROM local_admin_credentials").fetchone()[0]
        evidence = (
            repr(c.execute("SELECT * FROM command_receipts").fetchall())
            + repr(c.execute("SELECT * FROM command_receipt_results").fetchall())
            + repr(c.execute("SELECT * FROM audit_events").fetchall())
        )
        assert password not in evidence and phc not in evidence and "$argon2" not in evidence
        assert c.execute("SELECT count(*) FROM local_admin_credentials").fetchone() == (1,)
    finally:
        c.close()
    assert password not in host.log.path.read_text()
    assert cookie.split(";")[0].split("=")[1] not in repr(host.browser.sessions.entries)


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": "http://foreign.invalid"},
        {"Sec-Fetch-Site": "cross-site"},
        {"X-SOMA-Run": "00000000-0000-4000-8000-000000000001"},
    ],
)
def test_browser_context_rejects_before_auth_dispatch(host, headers):
    browser = client()
    with pytest.raises(urllib.error.HTTPError):
        request(
            browser,
            host,
            "/api/v1/auth/setup",
            {
                "run_id": "00000000-0000-4000-8000-000000000001",
                "password": "Foundation password 42",
                "confirmation": "Foundation password 42",
            },
            **headers,
        )
    assert host.browser.auth.state() == "setup_required"


def test_session_bounds_hash_storage_and_restart_invalidation():
    from starlette.requests import Request

    now = [100.0]
    run, actor = new_uuid4(), new_uuid4()
    sessions = Sessions(run, "http://127.0.0.1:1234", clock=lambda: now[0])
    token, csrf = sessions.issue(actor)
    assert token not in repr(sessions.entries) and csrf not in repr(sessions.entries)

    def req(**extras):
        headers = {
            "host": "127.0.0.1:1234",
            "cookie": "soma_session=" + token,
            "origin": sessions.origin,
            "x-soma-run": run,
            "x-soma-csrf": csrf,
            **extras,
        }
        return Request(
            {"type": "http", "headers": [(k.encode(), v.encode()) for k, v in headers.items()]}
        )

    assert sessions.validate(req(), mutation=True)["actor_id"] == actor
    for _ in range(3):
        sessions.issue(actor)
    with pytest.raises(SomaError):
        sessions.issue(actor)
    now[0] += 43200
    with pytest.raises(SomaError):
        sessions.validate(req())
    sessions.issue(actor)
    sessions.clear()
    assert sessions.entries == {}
    with pytest.raises(SomaError):
        Sessions(new_uuid4(), sessions.origin).validate(req())


def test_setup_session_failure_leaves_credentials_unconfigured(host, monkeypatch):
    def fail(actor):
        raise SomaError("SESSION_CAPACITY", "Session issuance unavailable.")

    monkeypatch.setattr(host.browser.sessions, "issue", fail)
    with pytest.raises(SomaError):
        host.browser.auth.setup("Foundation password 42", "Foundation password 42")
    assert host.browser.auth.state() == "setup_required"


def test_setup_calls_same_uow_profile_participant_and_rolls_back_on_failure(runtime_config):
    from soma.runtime.host import Host

    calls = []

    class Participant:
        def __init__(self, *, fail=False):
            self.fail = fail

        def create_for_local_admin(
            self, uow, *, parent_command_id, actor_id, display_name="Local Administrator"
        ):
            assert uow.connection.execute(
                "SELECT command_id FROM command_receipts WHERE command_id=?",
                (parent_command_id,),
            ).fetchone() == (parent_command_id,)
            assert uow.connection.execute(
                "SELECT actor_id FROM local_admin_credentials WHERE actor_id=?",
                (actor_id,),
            ).fetchone() == (actor_id,)
            calls.append((parent_command_id, actor_id, display_name))
            if self.fail:
                raise SomaError("PROFILE_PARTICIPANT_FAILED", "Synthetic participant failure.")
            return actor_id

    runtime = Host(runtime_config, tray=False, profile_participant=Participant())
    runtime.start()
    try:
        runtime.browser.auth.setup("Foundation password 42", "Foundation password 42")
        assert len(calls) == 1 and calls[0][2] == "Local Administrator"
        assert runtime.browser.auth.state() == "login_required"
    finally:
        assert runtime.stop()

    from soma.foundation.config import RuntimeConfig

    failed_config = RuntimeConfig(
        runtime_config.instance_root.parent / "participant-failure",
        runtime_config.checkout_root,
        "test",
    )
    runtime = Host(failed_config, tray=False, profile_participant=Participant(fail=True))
    runtime.start()
    try:
        with pytest.raises(SomaError) as caught:
            runtime.browser.auth.setup("Foundation password 42", "Foundation password 42")
        assert caught.value.code == "PROFILE_PARTICIPANT_FAILED"
        assert runtime.browser.auth.state() == "setup_required"
        assert runtime.browser.sessions.entries == {}
        connection = runtime.factory.open()
        try:
            assert connection.execute(
                "SELECT count(*) FROM local_admin_credentials"
            ).fetchone() == (0,)
            assert connection.execute("SELECT count(*) FROM command_receipts").fetchone() == (0,)
            assert connection.execute("SELECT count(*) FROM audit_events").fetchone() == (0,)
        finally:
            connection.close()
    finally:
        assert runtime.stop()


def test_keyset_pages_larger_than_200_are_filter_bound_without_truncation():
    cursor = CursorCodec()
    rows = [(index // 3, index) for index in range(513)]
    seen, token = [], None
    while True:
        last, as_of = (
            cursor.decode(token, "ProbePageV1", {"active": True}, ["group", "id"])
            if token
            else ([-1, -1], 100)
        )
        candidates = [row for row in rows if row > tuple(last)]
        page = candidates[: cursor.limit()]
        seen.extend(page)
        token = (
            cursor.encode("ProbePageV1", {"active": True}, ["group", "id"], list(page[-1]), as_of)
            if len(candidates) > len(page)
            else None
        )
        if token is None:
            break
    assert seen == rows
    token = cursor.encode("ProbePageV1", {}, ["id"], [1], 100)
    for bad, filters, order in [
        (token, {"active": False}, ["id"]),
        (token, {}, ["other"]),
        (token[:-4] + "AAAA", {}, ["id"]),
    ]:
        with pytest.raises(SomaError):
            cursor.decode(bad, "ProbePageV1", filters, order)
    assert cursor.limit(200) == 200
    with pytest.raises(SomaError):
        cursor.limit(201)
