import hashlib
import mimetypes

from soma.foundation.build import current_build
from soma.foundation.errors import SomaError
from soma.foundation.filesystem import safe_path
from soma.foundation.strict_json import loads_strict_bytes

MAIN_ROUTES = frozenset({"/", "/system/diagnostics", "/tickets", "/objectives", "/inventory", "/infrastructure", "/settings"})
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"


class StaticAssets:
    def __init__(self, checkout):
        self.root = checkout / "src/main/dist"
        try:
            manifest = loads_strict_bytes(
                (self.root / "manifest.json").read_bytes(), max_bytes=1048576
            )
            if (
                set(manifest) != {"version", "build", "files"}
                or manifest["version"] != 1
                or manifest["build"] != current_build().as_dict()
                or "index.html" not in manifest["files"]
            ):
                raise ValueError()
            actual = {
                p.relative_to(self.root).as_posix()
                for p in self.root.rglob("*")
                if p.is_file() and p.name != "manifest.json"
            }
            if actual != set(manifest["files"]):
                raise ValueError()
            self.assets = {}
            for name, digest in manifest["files"].items():
                path = safe_path(self.root, name)
                body = path.read_bytes()
                if hashlib.sha256(body).hexdigest() != digest:
                    raise ValueError()
                mime = (
                    "text/javascript"
                    if name.endswith(".js")
                    else mimetypes.guess_type(name)[0] or "application/octet-stream"
                )
                self.assets[name] = (body, mime)
        except Exception:
            raise SomaError(
                "STATIC_ASSETS_INVALID",
                "Main assets are missing, changed, or incompatible. Run source setup/build.",
                "restart",
            ) from None

    def resolve(self, path):
        if path in MAIN_ROUTES:
            return self.assets["index.html"]
        if any(value in path for value in ("..", "\\", "%", "//", "\x00")) or path.startswith(
            "/api/"
        ):
            return None
        return self.assets.get(path.lstrip("/"))
