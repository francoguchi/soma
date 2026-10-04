"""Five thin source buttons use this single trusted lifecycle implementation."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
import venv
import webbrowser

ROOT = Path(__file__).resolve().parents[1]


def check_python():
    if os.name != "nt" or sys.version_info[:2] not in {(3, 13), (3, 14)}:
        raise RuntimeError("Source development requires Windows Python 3.13 or 3.14.")


def setup():
    check_python()
    interpreter = ROOT / ".venv/Scripts/python.exe"
    if not interpreter.exists():
        venv.EnvBuilder(with_pip=True).create(ROOT / ".venv")
    probe = "import importlib.metadata as m,json,tomllib; from pathlib import Path; p=tomllib.loads(Path('pyproject.toml').read_text()); pins=p['project']['dependencies']+p['project']['optional-dependencies']['dev']; assert all(m.version(x.split('==')[0])==x.split('==')[1] for x in pins); d=json.loads(m.distribution('soma').read_text('direct_url.json')); assert d['dir_info']['editable'] and d['url']==Path.cwd().as_uri()"
    installed = (
        subprocess.run(
            [str(interpreter), "-I", "-c", probe],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )
    if not installed:
        subprocess.run(
            [str(interpreter), "-m", "pip", "install", "-e", ".[dev]"], cwd=ROOT, check=True
        )
    # Exact mandatory native provider must already be installable; no fallback.
    subprocess.run(
        [
            str(interpreter),
            "-c",
            "import sqlcipher3; c=sqlcipher3.connect(':memory:'); assert c.execute('PRAGMA cipher_version').fetchone()==('4.17.0 community',); c.close()",
        ],
        cwd=ROOT,
        check=True,
    )
    npm = __import__("shutil").which("npm.cmd")
    if npm is None:
        raise RuntimeError("Install Node 24/npm, then rerun setup.")
    subprocess.run([npm, "ci"], cwd=ROOT / "src/main", check=True)
    subprocess.run([str(interpreter), str(ROOT / "tools/contracts.py")], cwd=ROOT, check=True)
    subprocess.run([npm, "run", "build"], cwd=ROOT / "src/main", check=True)
    subprocess.run(
        [
            str(interpreter),
            str(ROOT / "tools/impact.py"),
            "--output",
            str(ROOT / ".tmp/setup-impact.json"),
        ],
        cwd=ROOT,
        check=True,
    )
    return 0


def wait_ready(config, child=None, *, seconds=30):
    from soma.runtime.observation import observe

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        observation = observe(config)
        if observation.state == "verified_ready":
            return observation.verified
        if observation.state in {"stale", "untrusted", "unreachable"}:
            raise RuntimeError("Runtime observation: " + observation.state + ". Inspect the exact instance before retrying.")
        if child is not None and child.poll() is not None:
            raise RuntimeError(
                "Host startup failed. Inspect the run logs in " + str(config.path("diagnostics"))
            )
        time.sleep(0.1)
    raise RuntimeError("READY timeout. Inspect the run logs in " + str(config.path("diagnostics")))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["setup", "run", "console", "stop", "reset", "host"])
    args = parser.parse_args(argv)
    check_python()
    if args.action == "setup":
        return setup()
    from soma.foundation.config import RuntimeConfig
    from soma.foundation.errors import SomaError
    from soma.runtime.control import stop_current
    from soma.runtime.observation import observe
    from soma.runtime.host import Host

    config = RuntimeConfig.discover(ROOT)
    try:
        if args.action == "reset":
            canonical = RuntimeConfig.discover(ROOT)
            if config.mode != "development" or config.instance_root != canonical.instance_root:
                raise RuntimeError("Reset button requires the canonical development instance.")
            print("Disposable development instance: " + str(config.instance_root), flush=True)
            if input("Type RESET to rebuild and leave SOMA stopped: ") != "RESET":
                raise RuntimeError("Reset confirmation was not accepted; data preserved.")
            if not stop_current(config):
                raise RuntimeError("Graceful stop timed out; data preserved.")
            from soma.foundation.development.database import rebuild

            rebuild(config, confirmation="RESET")
            print("Development database rebuilt; SOMA remains stopped.")
            return 0
        if args.action == "stop":
            if not stop_current(config):
                raise RuntimeError("Graceful shutdown timed out; no process was terminated.")
            return 0
        if args.action != "host":
            observation = observe(config)
            if observation.state in {"stale", "untrusted", "unreachable"}:
                raise RuntimeError("Runtime observation: " + observation.state + ". No control action authorized.")
            verified = observation.verified if observation.state == "verified_ready" else None
            if observation.state in {"candidate", "verified_not_ready"}:
                verified = wait_ready(config)
            if verified:
                print("Verified SOMA READY " + verified[0]["origin"], flush=True)
                webbrowser.open(verified[0]["origin"])
                return 0
        if args.action == "run":
            child = subprocess.Popen(
                [
                    str(ROOT / ".venv/Scripts/python.exe"),
                    "-I",
                    str(Path(__file__).resolve()),
                    "host",
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            verified = wait_ready(config, child)
            print("Verified SOMA READY " + verified[0]["origin"], flush=True)
            webbrowser.open(verified[0]["origin"])
            return 0
        host = Host(config, console=args.action == "console")
        try:
            host.start()
        except SomaError as exc:
            if exc.code == "INSTANCE_OWNED":
                verified = wait_ready(config)
                print("Verified SOMA READY " + verified[0]["origin"], flush=True)
                if args.action != "host":
                    webbrowser.open(verified[0]["origin"])
                return 0
            raise
        try:
            while not host.shutdown_requested.wait(0.1):
                if not host.thread.is_alive():
                    raise RuntimeError("Local server stopped unexpectedly.")
        except KeyboardInterrupt:
            host.shutdown_requested.set()
        finally:
            if not host.stop():
                raise RuntimeError("Shutdown incomplete; exact ownership retained.")
        return 0
    except SomaError as exc:
        print(exc.code + ": " + exc.summary, file=sys.stderr)
        return 1
    except (RuntimeError, subprocess.CalledProcessError, EOFError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
