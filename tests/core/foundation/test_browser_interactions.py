"""Focused real Chrome fixture; no synthetic owners enter the product runtime."""

from pathlib import Path
import shutil
import subprocess

from soma.foundation.audit import AuditContract, AuditEvent, AuditWriter
from soma.foundation.config import RuntimeConfig
from soma.foundation.contracts import validate_contract
from soma.foundation.errors import ValidationError
from soma.foundation.identity import new_uuid4
from soma.foundation.security.deliberate_action import ProofAction
from soma.foundation.strict_json import loads_strict_bytes
from soma.foundation.transactions import CommandBoundary, ResultContract
from soma.foundation.working_copy import CopyContract
from soma.runtime.host import Host
from tools.static_manifest import generate

ROOT = Path(__file__).resolve().parents[3]


def test_real_browser_shared_interactions(tmp_path):
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "src/main/dist", checkout / "src/main/dist")
    shutil.copytree(ROOT / ".tmp/interaction-dist", checkout / "src/main/dist/test")
    generate(checkout)
    owner = CopyContract(
        "ProbeEditV1",
        1,
        "probe",
        "notes",
        {
            "type": "object",
            "properties": {"note": {"type": "string", "maxLength": 262144}},
            "required": ["note"],
            "additionalProperties": False,
        },
        frozenset({"/note"}),
        lambda value: None if value == "probe-a" else reject(),
        lambda snapshot, identity, scope: "rev-1",
    )
    host = Host(
        RuntimeConfig(tmp_path / "instance", checkout, "test"),
        tray=False,
        copy_contracts=(owner,),
        proof_actions=(
            ProofAction("probe.hold", "probe", "deliberate_hold"),
            ProofAction("probe.preview", "probe", "impact_preview_plus_hold"),
        ),
    )
    host.start()
    try:

        def empty(value):
            validate_contract("urn:soma:00:empty-request:v1", value)

        boundary = CommandBoundary(
            host.factory,
            [ResultContract("ProbeAcceptV1", 1, empty)],
            AuditWriter(
                [AuditContract("probe.accept", 1, "ProbeAcceptV1", 1, empty, lambda value: False)]
            ),
        )
        original = host.browser.handle

        def handle(request, raw):
            if request.url.path != "/api/v1/probe/accept":
                return original(request, raw)
            context = host.browser.sessions.validate(request, mutation=True)
            body = loads_strict_bytes(raw)
            validate_contract("urn:soma:00:proof-authorization:v1", body)
            command_id = new_uuid4()

            def operation(uow):
                # Owner freshness/eligibility is an independent predicate before proof consumption.
                if (
                    body["binding"]["target_id"] != "probe-a"
                    or body["binding"]["base_revision"] != "rev-1"
                    or body["binding"]["action_code"] == "probe.preview"
                    and body["binding"]["preview_fingerprint"] != "a" * 64
                ):
                    reject()
                host.browser.proofs.consume(uow, context, body["binding"], body["proof_token"])
                event = AuditEvent(
                    new_uuid4(),
                    "probe.accept",
                    1,
                    "local_admin",
                    "probe",
                    command_id,
                    {},
                    actor_id=context["actor_id"],
                    target_id="probe-a",
                )
                return {}, [event]

            result = boundary.execute(
                command_id, "probe.accept", body["binding"], ("ProbeAcceptV1", 1), operation
            )
            return host.browser.response("empty-request", result)

        host.browser.handle = handle
        node = shutil.which("node")
        assert node, "Put the pinned Node 24 development installation on PATH."
        completed = subprocess.run(
            [node, "browser-tests/interactions.mjs", host.origin],
            cwd=ROOT / "src/main",
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        print(completed.stdout)
        connection = host.factory.open()
        try:
            assert connection.execute(
                "SELECT count(*) FROM command_receipts WHERE command_type='probe.accept'"
            ).fetchone() == (3,)
            assert connection.execute(
                "SELECT count(*) FROM audit_events WHERE action_type='probe.accept'"
            ).fetchone() == (3,)
            assert connection.execute("SELECT count(*) FROM ui_working_copies").fetchone() == (0,)
        finally:
            connection.close()
    finally:
        assert host.stop()


def reject():
    raise ValidationError("Synthetic owner target is unavailable.")
