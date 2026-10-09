"""Phase B synthetic presentation on an isolated native host; canonical DB untouched."""
from pathlib import Path
import shutil
import subprocess

from soma.foundation.config import RuntimeConfig
from soma.foundation.working_copy import CopyContract
from soma.runtime.host import Host
from tools.static_manifest import generate

ROOT = Path(__file__).resolve().parents[3]


def test_operational_fixture(tmp_path):
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "src/main/dist", checkout / "src/main/dist")
    shutil.copytree(ROOT / ".tmp/interaction-dist", checkout / "src/main/dist/test")
    generate(checkout)
    owner = CopyContract(
        "OperationalEditV1", 1, "probe", "edit",
        {"type": "object", "properties": {"name": {"type": "string", "maxLength": 1024}},
         "required": ["name"], "additionalProperties": False},
        frozenset({"/name"}), lambda value: None, lambda snapshot, identity, scope: "rev-1",
    )
    host = Host(RuntimeConfig(tmp_path / "instance", checkout, "test"), tray=False, copy_contracts=(owner,))
    host.start()
    try:
        node = shutil.which("node")
        assert node, "Put pinned Node 24 on PATH."
        result = subprocess.run([node, "browser-tests/operational.mjs", host.origin],
                                cwd=ROOT / "src/main", capture_output=True, text=True, timeout=180)
        assert result.returncode == 0, result.stdout + result.stderr
        print(result.stdout)
    finally:
        assert host.stop()
