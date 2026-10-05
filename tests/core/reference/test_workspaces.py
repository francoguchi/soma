"""Live Main with Reference composition, encrypted persistence and real Chrome."""

import shutil
import subprocess
from pathlib import Path

from soma.foundation.config import RuntimeConfig
from soma.runtime.host import Host
from soma.foundation.identity import new_uuid4
from soma.foundation.transactions import UnitOfWork
from soma.modules.reference.domain.dispatch import validate_dispatch_name
from soma.modules.reference.ports.dispatch import DispatchCommandContext

ROOT = Path(__file__).resolve().parents[3]


def test_real_reference_settings_workspaces(tmp_path):
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "src/main/dist", checkout / "src/main/dist")
    host = Host(RuntimeConfig(tmp_path / "instance", checkout, "test"), tray=False, reference=True)
    host.start()
    try:
        # The accepted internal participant supplies a Site-derived fixture, never an HTTP route.
        with UnitOfWork(host.factory) as uow:
            command = new_uuid4()
            uow.connection.execute(
                "INSERT INTO command_receipts VALUES (?,'site.ui-fixture',?,NULL,0)",
                (command, "0" * 64),
            )
            site_dispatch = host.reference.dispatch.create_dedicated_for_site(
                uow,
                parent_command_id=command,
                name="Site-derived fixture",
                precomputed_name_match_key=validate_dispatch_name("Site-derived fixture")[1],
                command_context=DispatchCommandContext(),
            )
        node = shutil.which("node")
        assert node
        result = subprocess.run(
            [node, "browser-tests/reference.mjs", host.origin, site_dispatch],
            cwd=ROOT / "src/main",
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        print(result.stdout)
    finally:
        assert host.stop()
