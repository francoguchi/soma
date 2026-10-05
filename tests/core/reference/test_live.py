"""Assembled Scope-01 same-origin setup; synthetic credentials stay disposable."""

import json
import shutil
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

from soma.foundation.config import RuntimeConfig
from soma.foundation.identity import new_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.runtime.host import Host

ROOT = Path(__file__).resolve().parents[3]


def test_live_reference_composition_auth_setup_customer_workflow_restart(tmp_path):
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "src/main/dist", checkout / "src/main/dist")
    config = RuntimeConfig(tmp_path / "instance", checkout, "test")
    host = Host(config, tray=False, reference=True)
    host.start()
    try:
        browser = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(CookieJar())
        )
        password = "Synthetic Scope 01 password"
        request = urllib.request.Request(
            host.origin + "/api/v1/auth/setup",
            data=json.dumps(
                dict(run_id=host.run_id, password=password, confirmation=password)
            ).encode(),
            headers={
                "Origin": host.origin,
                "Content-Type": "application/json",
                "X-SOMA-Run": host.run_id,
            },
        )
        with browser.open(request, timeout=5) as response:
            assert json.loads(response.read())["auth_state"] == "authenticated"
        actor = host.browser.auth.credential()[0]
        profile = host.reference.profile.get_singleton()
        assert profile["local_user_profile_id"] == actor
        customers = host.reference.customers
        identity = customers.create_customer_organization(
            command_id=new_uuid4(), name="Live synthetic Customer", actor_id=actor
        )["target_id"]
        customers.set_customer_account_code(
            command_id=new_uuid4(),
            customer_org_id=identity,
            base_revision=1,
            account_code="LIVE-01",
            actor_id=actor,
        )
        host.reference.profile.update_display_name(
            command_id=new_uuid4(),
            actor_id=actor,
            base_revision=1,
            display_name="Synthetic Operator",
        )
        contacts = host.reference.contacts
        contact = contacts.create_contact(
            command_id=new_uuid4(),
            name="Live synthetic Contact",
            initial_email="live@example.com",
            initial_customer_org_id=identity,
            actor_id=actor,
        )["target_id"]
        contacts.change_contact_affiliation(
            command_id=new_uuid4(),
            contact_id=contact,
            base_revision=1,
            new_customer_org_id=None,
            reason_category="role_changed",
            actor_id=actor,
        )
        with ReadSnapshot(host.reference.customers.factory) as snapshot:
            use = host.reference.communication.validate_channel_for_use(
                snapshot, contact, "AUTO", "msg_recipient"
            )
            assert use.state == "USABLE" and use.value_text == "live@example.com"
        dispatch_request = dict(
            command_id=new_uuid4(),
            name="Live synthetic Dispatch",
            address_text="Synthetic address",
            actor_id=actor,
        )
        dispatch_result = host.reference.dispatch.create_standalone(**dispatch_request)
        lifecycle_request = dict(
            command_id=new_uuid4(),
            target_type="dispatch_location",
            target_id=dispatch_result["target_id"],
            base_revision=1,
            reason_category="operator_archive",
            actor_id=actor,
        )
        archived = host.reference.lifecycle.archive_reference(**lifecycle_request)
        host.reference.lifecycle.reactivate_reference(
            **(
                lifecycle_request
                | dict(
                    command_id=new_uuid4(), base_revision=2, reason_category="operator_reactivate"
                )
            )
        )
        assert host.state == "READY"
    finally:
        assert host.stop()
    restarted = Host(config, tray=False, reference=True)
    restarted.start()
    try:
        assert restarted.reference.profile.get_singleton()["display_name"] == "Synthetic Operator"
        assert restarted.manifest.generation == 9
        assert restarted.reference.dispatch.create_standalone(**dispatch_request) == dispatch_result
        assert restarted.reference.lifecycle.archive_reference(**lifecycle_request) == archived
        preview = restarted.reference.lifecycle.preview(
            operation="archive",
            target_type="dispatch_location",
            target_id=dispatch_result["target_id"],
            base_revision=3,
        )
        assert preview.would_be_eligible
        with ReadSnapshot(restarted.reference.customers.factory) as snapshot:
            assert (
                restarted.reference.communication.validate_contact(snapshot, contact, 2) == "ACTIVE"
            )
            assert (
                restarted.reference.communication.match_email_candidates(
                    snapshot, "LIVE@example.com"
                )
                .candidates[0]
                .contact_id
                == contact
            )
    finally:
        assert restarted.stop()
