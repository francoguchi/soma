"""Bind explicitly built Main assets to the current shared build identity."""

import hashlib
import json
from pathlib import Path
from soma.foundation.build import current_build


def generate(root=Path(__file__).resolve().parents[1]):
    dist = root / "src/main/dist"
    assets = {
        p.relative_to(dist).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(dist.rglob("*"))
        if p.is_file() and p.name != "manifest.json"
    }
    if "index.html" not in assets:
        raise ValueError("Build Main before generating its manifest")
    (dist / "manifest.json").write_text(
        json.dumps(
            {"version": 1, "build": current_build().as_dict(), "files": assets},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    generate()
