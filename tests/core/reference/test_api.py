"""Real authenticated HTTP exercises the accepted Scope-01 public surface."""

import json
import shutil
import urllib.request
import urllib.error
from http.cookiejar import CookieJar
from pathlib import Path
import pytest

from soma.foundation.config import RuntimeConfig
from soma.foundation.errors import SomaError
from soma.foundation.identity import new_uuid4
from soma.foundation.contracts import validate_contract
from soma.modules.reference.transport.routes import SPECS, resolve
from soma.runtime.host import Host

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def http_api(tmp_path):
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "src/main/dist", checkout / "src/main/dist")
    host = Host(RuntimeConfig(tmp_path / "instance", checkout, "test"), tray=False, reference=True)
    host.start()
    browser = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(CookieJar())
    )
    context = {}

    def call(method, path, body=None, csrf=True, anonymous=False, headers=None):
        request_headers = {
            "Origin": host.origin,
            "X-SOMA-Run": host.run_id,
            "Content-Type": "application/json",
        }
        if csrf and "csrf" in context:
            request_headers["X-SOMA-CSRF"] = context["csrf"]
        request_headers.update(headers or {})
        req = urllib.request.Request(
            host.origin + "/api/v1" + path,
            method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers=request_headers,
        )
        opener = (
            urllib.request.build_opener(urllib.request.ProxyHandler({})) if anonymous else browser
        )
        try:
            with opener.open(req, timeout=5) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    status, auth = call(
        "POST",
        "/auth/setup",
        dict(
            run_id=host.run_id,
            password="Synthetic API password",
            confirmation="Synthetic API password",
        ),
    )
    assert status == 200
    context["csrf"] = auth["csrf_token"]
    try:
        yield host, call
    finally:
        assert host.stop()


def applied(call, method, path, **body):
    status, result = call(method, path, dict(command_id=new_uuid4(), **body))
    assert status == 200, result
    assert result["outcome"] in ("APPLIED", "NO_CHANGE")
    return result


def test_ui_metadata_and_batched_identity_reads_are_closed_and_pure(http_api):
    host, call = http_api
    identity = applied(call, "POST", "/reference/customer-organizations", name="Customer")[
        "target_id"
    ]
    connection = host.factory.open()
    before = connection.execute("SELECT count(*) FROM command_receipts").fetchone()[0]
    connection.close()
    status, definitions = call("GET", "/settings/registry/definitions")
    assert status == 200 and definitions["items"] == [
        dict(
            setting_key="foundation.appearance",
            semantic_owner="foundation",
            contract_name="AppearancePreferenceV1",
            contract_version=1,
        )
    ]
    status, profile = call("GET", "/local-user-profile")
    assert status == 200 and profile["display_name"] == "Local Administrator"
    assert profile["local_user_profile_id"] == host.browser.auth.credential()[0]
    status, result = call(
        "POST",
        "/reference/identities",
        dict(reference_type="customer_organization", ids=[identity]),
        csrf=False,
    )
    assert status == 200 and result["items"][0]["name"] == "Customer"
    for request in (
        dict(reference_type="customer_organizations; DELETE", ids=[identity]),
        dict(reference_type="contact", ids=[identity] * 201),
        dict(reference_type="contact", ids=[identity, identity]),
        dict(reference_type="contact", ids=[identity], actor_id=identity),
    ):
        assert call("POST", "/reference/identities", request)[0] == 400
    connection = host.factory.open()
    try:
        assert connection.execute("SELECT count(*) FROM command_receipts").fetchone()[0] == before
        assert connection.execute("SELECT count(*) FROM setting_values").fetchone()[0] == 0
    finally:
        connection.close()


def test_ui_owner_recovery_contracts_preserve_intent_without_domain_writes(http_api):
    _, call = http_api
    identity = applied(call, "POST", "/reference/customer-organizations", name="Original")[
        "target_id"
    ]
    key = dict(
        contract_id="reference.edit.customer_organization",
        contract_version=1,
        target_type="customer_organization",
        target_id=identity,
        scope_key="metadata",
        base_revision="1",
    )
    status, checkpoint = call(
        "POST",
        "/working-copies/checkpoint",
        dict(
            **key,
            command_id=new_uuid4(),
            expected_generation=0,
            draft_json=json.dumps(dict(name="Safe intent", account_code="")),
            dirty_paths=["/name"],
        ),
    )
    assert status == 200
    assert call("GET", "/reference/customer-organizations/" + identity)[1]["name"] == "Original"
    applied(
        call,
        "PATCH",
        "/reference/customer-organizations/" + identity,
        name="Concurrent",
        base_revision=1,
    )
    status, restored = call("POST", "/working-copies/restore", key)
    assert status == 200 and restored["conflict"] is True and restored["current_revision"] == "2"
    assert json.loads(restored["draft_json"])["name"] == "Safe intent"
    assert (
        call(
            "POST",
            "/working-copies/checkpoint",
            dict(
                **{
                    **key,
                    "contract_id": "reference.edit.setting",
                    "target_type": "setting",
                    "target_id": "unregistered.key",
                },
                command_id=new_uuid4(),
                expected_generation=0,
                draft_json='{"value_json":"null"}',
                dirty_paths=["/value_json"],
            ),
        )[0]
        == 400
    )
    status, _ = call(
        "POST",
        "/working-copies/discard",
        dict(
            command_id=new_uuid4(),
            working_copy_id=checkpoint["working_copy_id"],
            expected_generation=checkpoint["generation"],
        ),
    )
    assert status == 200
    assert call("POST", "/working-copies/restore", key)[0] == 400


def test_http_customer_matching_review_share_reassign_history(http_api):
    host, call = http_api
    first = applied(
        call, "POST", "/reference/customer-organizations", name="First", account_code="CODE"
    )["target_id"]
    second = applied(call, "POST", "/reference/customer-organizations", name="Second")["target_id"]
    status, match = call(
        "POST",
        "/reference/match/customer-organization",
        dict(raw_account_code="code", raw_name="Second", limit=1),
        csrf=False,
    )
    assert (
        status == 200
        and match["state"] == "AMBIGUOUS"
        and match["candidate_count"] == 2
        and match["continuation"]
    )
    status, page = call("GET", "/reference/customer-organizations?limit=1&count_exact=true")
    assert status == 200 and page["exact_count"] == 2 and page["continuation"]
    assert (
        call("GET", "/reference/customer-organizations/" + first)[1]["current_account_code"][
            "value_text"
        ]
        == "CODE"
    )
    review = call(
        "POST",
        "/reference/customer-account-code/review-preview",
        dict(
            raw_account_code="CODE",
            proposed_action="CONFIRM_SHARED_CLAIM",
            target_customer_org_id=second,
        ),
        csrf=False,
    )[1]
    applied(
        call,
        "POST",
        f"/reference/customer-organizations/{second}/customer-account-code/confirm-shared-claim",
        base_revision=1,
        account_code="CODE",
        review_snapshot_hash=review["review_snapshot_hash"],
        reason_category="confirmed",
    )
    assert (
        call(
            "POST",
            "/reference/match/customer-organization",
            dict(raw_account_code="CODE"),
            csrf=False,
        )[1]["explanation"]
        == "ACCOUNT_CODE_MULTIPLE_CLAIMS"
    )
    third = applied(call, "POST", "/reference/customer-organizations", name="Third")["target_id"]
    review = call(
        "POST",
        "/reference/customer-account-code/review-preview",
        dict(
            raw_account_code="CODE",
            proposed_action="REASSIGN_CLAIM",
            target_customer_org_id=third,
            from_customer_org_id=first,
        ),
        csrf=False,
    )[1]
    # Reviewed reassignment preserves unrelated shared claimants and matching ambiguity.
    status, result = call(
        "POST",
        "/reference/customer-account-code/reassign",
        dict(
            command_id=new_uuid4(),
            from_customer_org_id=first,
            from_base_revision=1,
            to_customer_org_id=third,
            to_base_revision=1,
            account_code="CODE",
            review_snapshot_hash=review["review_snapshot_hash"],
            reason_category="reassign",
        ),
    )
    assert status == 200 and result["revision"] == 2
    candidates = call(
        "POST",
        "/reference/match/customer-organization",
        dict(raw_account_code="CODE"),
        csrf=False,
    )[1]
    assert candidates["state"] == "AMBIGUOUS"
    assert set(candidates["candidate_ids"]) == {second, third}
    applied(
        call,
        "PUT",
        f"/reference/customer-organizations/{third}/customer-account-code",
        base_revision=2,
        account_code="NEW",
    )
    updated = applied(
        call, "PATCH", f"/reference/customer-organizations/{third}", base_revision=3, name="Renamed"
    )
    assert updated["revision"] == 4
    status, page = call(
        "GET",
        f"/reference/customer-organizations/{third}/customer-account-code/history?limit=1&count_exact=true",
    )
    assert status == 200 and page["exact_count"] == 2
    # Every mutation audit uses the authenticated actor, never a body-selected actor.
    assert (
        host.browser.auth.credential()[0]
        == host.reference.profile.get_singleton()["local_user_profile_id"]
    )


def test_http_contact_channel_affiliation_and_scoped_matching(http_api):
    _, call = http_api
    org = applied(call, "POST", "/reference/customer-organizations", name="Customer")["target_id"]
    contact = applied(
        call, "POST", "/reference/contacts", name="Contact", initial_customer_org_id=org
    )["target_id"]
    channel = applied(
        call,
        "POST",
        f"/reference/contacts/{contact}/channels",
        contact_base_revision=1,
        channel_kind="email",
        value_text="private@example.com",
    )["target_id"]
    applied(
        call,
        "PATCH",
        f"/reference/contacts/{contact}/channels/{channel}",
        contact_base_revision=2,
        channel_base_revision=1,
        value_text="updated@example.com",
    )
    status, use = call(
        "POST",
        f"/reference/contacts/{contact}/channels/validate-for-use",
        dict(channel_or_auto="AUTO", purpose="msg_recipient"),
        csrf=False,
    )
    assert status == 200 and use["state"] == "USABLE" and use["contact_channel_id"] == channel
    status, match = call(
        "POST",
        "/reference/match/contact",
        dict(scope=org, raw_email="UPDATED@example.com"),
        csrf=False,
    )
    assert status == 200 and match["candidate_ids"] == [contact]
    applied(
        call, "PATCH", f"/reference/contacts/{contact}", base_revision=3, name="Renamed Contact"
    )
    applied(
        call,
        "POST",
        f"/reference/contacts/{contact}/channels/{channel}/archive",
        contact_base_revision=4,
        channel_base_revision=2,
        reason_category="invalidated",
    )
    applied(
        call,
        "POST",
        f"/reference/contacts/{contact}/affiliation",
        base_revision=5,
        new_customer_org_id=None,
        reason_category="unbound",
    )
    assert call("GET", f"/reference/contacts/{contact}")[1]["current_affiliation"] is None
    assert call("GET", "/reference/contacts?limit=200")[0] == 200
    assert (
        call("GET", f"/reference/contacts/{contact}/channels?count_exact=true")[1]["exact_count"]
        == 1
    )
    assert (
        call("GET", f"/reference/contacts/{contact}/affiliation-history?count_exact=true")[1][
            "items"
        ][0]["is_current"]
        == 0
    )


def test_http_dispatch_lifecycle_setting_profile_and_exact_replay(http_api):
    _, call = http_api
    identity = applied(
        call, "POST", "/reference/dispatch-locations", name="Dispatch", address_text="Address"
    )["target_id"]
    applied(
        call,
        "PATCH",
        f"/reference/dispatch-locations/{identity}",
        base_revision=1,
        name="Renamed",
        address_text="New Address",
    )
    assert call("GET", "/reference/dispatch-locations")[0] == 200
    assert (
        call("GET", f"/reference/dispatch-locations/{identity}")[1]["current_address"]["source"]
        == "STANDALONE"
    )
    preview = call(
        "POST",
        f"/reference/dispatch_location/{identity}/archive-preview",
        dict(base_revision=2),
        csrf=False,
    )[1]
    assert preview["would_be_eligible"]
    req = dict(command_id=new_uuid4(), base_revision=2, reason_category="operator_archive")
    original = call("POST", f"/reference/dispatch_location/{identity}/archive", req)
    assert original[0] == 200 and original[1]["revision"] == 3
    applied(
        call,
        "POST",
        f"/reference/dispatch_location/{identity}/reactivate",
        base_revision=3,
        reason_category="operator_reactivate",
    )
    assert call("POST", f"/reference/dispatch_location/{identity}/archive", req) == original
    status, default = call("GET", "/settings/foundation.appearance")
    assert (
        status == 200
        and default["source"] == "DEFAULT"
        and json.loads(default["value_json"]) == "core_dark"
    )
    result = applied(
        call,
        "PUT",
        "/settings/foundation.appearance",
        semantic_owner="foundation",
        contract_name="AppearancePreferenceV1",
        contract_version=1,
        base_revision=None,
        value_json='"light"',
    )
    assert result["source"] == "PERSISTED" and result["revision"] == 1
    applied(
        call,
        "PATCH",
        "/local-user-profile/display-name",
        base_revision=1,
        display_name="Synthetic Operator",
    )


def test_http_auth_csrf_unknown_fields_bounds_injection_and_internal_routes(http_api):
    host, call = http_api
    assert call("GET", "/reference/contacts", anonymous=True)[0] == 401
    assert (
        call("POST", "/reference/contacts", dict(command_id=new_uuid4(), name="Name"), csrf=False)[
            0
        ]
        == 403
    )
    for query in ("limit=201", "limit=500", "limit=1&limit=2", "sort=DROP", "after=forged"):
        assert call("GET", "/reference/contacts?" + query)[0] == 400
    for body in (
        dict(command_id=new_uuid4(), name="Name", actor_id=new_uuid4()),
        dict(command_id=new_uuid4(), name="\u00e9" * 513),
    ):
        assert call("POST", "/reference/contacts", body)[0] == 400
    assert (
        call(
            "POST",
            "/reference/contacts",
            dict(command_id=new_uuid4(), name="Name"),
            headers={"Origin": "http://evil.invalid"},
        )[0]
        == 403
    )
    assert (
        call(
            "POST",
            "/reference/contacts",
            dict(command_id=new_uuid4(), name="Name"),
            headers={"Content-Type": "text/plain"},
        )[0]
        == 400
    )
    assert (
        call(
            "POST",
            f"/reference/contacts/{new_uuid4()}/archive",
            dict(command_id=new_uuid4(), base_revision=1, reason_category="reason"),
        )[0]
        == 404
    )
    assert call("POST", "/reference/dispatch-locations/create-dedicated-for-site", {})[0] == 404
    assert call("POST", "/local-user-profile/create", {})[0] == 404
    assert call("DELETE", "/reference/contacts")[0] == 404
    assert call("GET", "/settings/unknown")[1]["code"] == "SETTING_UNKNOWN"
    # Read-only POST does not insert receipts or ask for mutation CSRF.
    connection = host.factory.open(read_only=True)
    try:
        before = connection.execute("SELECT count(*) FROM command_receipts").fetchone()[0]
    finally:
        connection.close()
    assert (
        call(
            "POST", "/reference/match/customer-organization", dict(raw_name="No match"), csrf=False
        )[0]
        == 200
    )
    connection = host.factory.open(read_only=True)
    try:
        assert (
            len(connection.execute("SELECT command_id FROM command_receipts").fetchall()) == before
        )
    finally:
        connection.close()


def test_route_contracts_closed_and_no_internal_authority():
    assert len({(s["method"], s["path"]) for s in SPECS}) == len(SPECS)
    assert all(s["method"] != "DELETE" for s in SPECS)
    assert resolve("POST", "/api/v1/reference/contact/" + new_uuid4() + "/archive") is not None
    assert resolve("POST", "/api/v1/reference/contacts/" + new_uuid4() + "/archive") is None
    for spec in SPECS:
        with pytest.raises(SomaError):
            validate_contract("urn:soma:01:" + spec["request"] + ":v1", dict(unexpected=True))
