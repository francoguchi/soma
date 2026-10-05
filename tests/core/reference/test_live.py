"""Assembled Scope-01 same-origin setup; synthetic credentials stay disposable."""

import json
import shutil
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

from soma.foundation.config import RuntimeConfig
from soma.foundation.identity import new_uuid4
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
        assert host.state == "READY"
    finally:
        assert host.stop()
    restarted = Host(config, tray=False, reference=True)
    restarted.start()
    try:
        assert restarted.reference.profile.get_singleton()["display_name"] == "Synthetic Operator"
        assert restarted.manifest.generation == 7
    finally:
        assert restarted.stop()
