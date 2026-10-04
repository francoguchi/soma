"""Owner-scoped ordered manifest; normalized accepted SQL bytes define identity."""

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from soma.foundation.errors import SomaError
from soma.foundation.filesystem import safe_path
from soma.foundation.strict_json import loads_strict_bytes


def migration_error(code="MIGRATION_MANIFEST_INVALID"):
    return SomaError(code, "Migration authority or database lineage is incompatible.", "restart")


@dataclass(frozen=True, slots=True)
class MigrationEntry:
    migration_id: str
    owner_scope: str
    path: str
    content_sha256: str
    depends_on: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MigrationManifest:
    directory: Path
    generation: int
    entries: tuple[MigrationEntry, ...]

    @classmethod
    def load(cls, directory: Path | None = None):
        directory = (
            directory
            if directory is not None
            else Path(str(files("soma.db").joinpath("migrations")))
        )
        try:
            parsed = loads_strict_bytes(
                (directory / "manifest.json").read_bytes(), max_bytes=1048576
            )
            if (
                type(parsed) is not dict
                or set(parsed) != {"version", "generation", "migrations"}
                or type(parsed["version"]) is not int
                or parsed["version"] != 1
                or type(parsed["generation"]) is not int
                or parsed["generation"] < 1
                or type(parsed["migrations"]) is not list
                or not parsed["migrations"]
            ):
                raise migration_error()
            entries = []
            for item in parsed["migrations"]:
                if type(item) is not dict or set(item) != {
                    "migration_id",
                    "owner_scope",
                    "path",
                    "content_sha256",
                    "depends_on",
                }:
                    raise migration_error()
                if type(item["depends_on"]) is not list or any(
                    type(value) is not str for value in item["depends_on"]
                ):
                    raise migration_error()
                entries.append(MigrationEntry(**{**item, "depends_on": tuple(item["depends_on"])}))
            manifest = cls(directory.resolve(), parsed["generation"], tuple(entries))
            manifest.validate()
            return manifest
        except (OSError, ValueError, TypeError):
            raise migration_error() from None

    def validate(self) -> None:
        seen_ids, seen_paths = set(), set()
        for entry in self.entries:
            if (
                type(entry.owner_scope) is not str
                or not re.fullmatch(r"[0-9]{2}", entry.owner_scope)
                or not re.fullmatch(rf"M{entry.owner_scope}\.[0-9]{{3}}", entry.migration_id)
            ):
                raise migration_error()
            if type(entry.path) is not str or not re.fullmatch(
                rf"{entry.owner_scope}/[0-9]{{3}}_[a-z0-9_]+\.sql", entry.path
            ):
                raise migration_error()
            if (
                entry.migration_id in seen_ids
                or entry.path in seen_paths
                or len(entry.depends_on) != len(set(entry.depends_on))
            ):
                raise migration_error()
            if not set(entry.depends_on) <= seen_ids:
                raise migration_error("MIGRATION_DEPENDENCY_INVALID")
            if type(entry.content_sha256) is not str or not re.fullmatch(
                r"[0-9a-f]{64}", entry.content_sha256
            ):
                raise migration_error()
            self.raw_bytes(entry)
            seen_ids.add(entry.migration_id)
            seen_paths.add(entry.path)
        actual_paths = {
            path.relative_to(self.directory).as_posix() for path in self.directory.rglob("*.sql")
        }
        if actual_paths != seen_paths:
            raise migration_error()

    def raw_bytes(self, entry: MigrationEntry) -> bytes:
        try:
            raw = safe_path(self.directory, entry.path).read_bytes().replace(b"\r\n", b"\n")
            text = raw.decode("utf-8", errors="strict")
            if (
                raw.startswith(b"\xef\xbb\xbf")
                or b"\r" in raw
                or not raw.endswith(b"\n")
                or raw.endswith(b"\n\n")
                or unicodedata.normalize("NFC", text) != text
            ):
                raise migration_error("MIGRATION_BYTES_INVALID")
            if hashlib.sha256(raw).hexdigest() != entry.content_sha256:
                raise migration_error("MIGRATION_HASH_MISMATCH")
            return raw
        except (OSError, UnicodeError):
            raise migration_error("MIGRATION_FILE_INVALID") from None

    def lineage(self) -> list[list[str]]:
        return [
            [entry.migration_id, entry.owner_scope, entry.content_sha256] for entry in self.entries
        ]
