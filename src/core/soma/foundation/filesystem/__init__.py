"""Owned path mechanics. Callers serialize mutations under their instance ownership."""

import os
import shutil
import stat
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from soma.foundation.errors import ValidationError
from soma.foundation.identity import UuidProvider, new_uuid4, require_uuid4


def _check_components(path: Path) -> None:
    for component in (*reversed(path.parents), path):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            raise ValidationError(
                "Owned filesystem authority cannot be inspected safely."
            ) from None
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
        ):
            raise ValidationError("Redirected filesystem authority is forbidden.")


def safe_path(root: Path, relative: str | Path) -> Path:
    root = Path(root)
    relative = Path(relative)
    if not root.is_absolute() or ".." in root.parts or relative.is_absolute():
        raise ValidationError("An absolute owned root and relative path are required.")
    if ".." in relative.parts or relative.drive or any(":" in part for part in relative.parts):
        raise ValidationError("Path traversal or alternate streams are forbidden.")
    candidate = root / relative
    _check_components(candidate)
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValidationError("Path escapes its owner root.")
    return resolved


@dataclass(frozen=True, slots=True)
class OwnedArtifact:
    path: Path
    device: int
    inode: int
    modified_ns: int
    size: int

    @classmethod
    def capture(cls, root: Path, relative: str | Path) -> "OwnedArtifact":
        path = safe_path(root, relative)
        info = path.stat(follow_symlinks=False)
        return cls(path, info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size)

    def matches(self, root: Path) -> bool:
        try:
            return self == self.capture(root, self.path.relative_to(root))
        except (OSError, ValueError, ValidationError):
            return False


def remove_owned(root: Path, artifact: OwnedArtifact) -> bool:
    if artifact.path == root.resolve() or not artifact.matches(root):
        return False
    if artifact.path.is_dir():
        # Preserve the whole workspace when any descendant redirects authority.
        for parent, dirs, files in os.walk(artifact.path, followlinks=False):
            for name in dirs + files:
                safe_path(root, (Path(parent) / name).relative_to(root))
        if not artifact.matches(root):
            return False
        shutil.rmtree(artifact.path)
    else:
        artifact.path.unlink()
    return True


def atomic_write(
    root: Path, relative: str, content: bytes, *, protect: Callable[[Path], None] | None = None
) -> OwnedArtifact:
    target = safe_path(root, relative)
    if not target.parent.is_dir():
        raise ValidationError("Publication parent must already exist.")
    original = OwnedArtifact.capture(root, relative) if target.exists() else None
    fd, name = tempfile.mkstemp(prefix=".soma-publish-", dir=target.parent)
    temporary = Path(name)
    created = os.fstat(fd)
    staged = None
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        staged = OwnedArtifact.capture(root, temporary.relative_to(root))
        if (staged.device, staged.inode) != (created.st_dev, created.st_ino):
            raise ValidationError("Publication temporary ownership changed.")
        if protect is not None:
            protect(temporary)  # Required ACL adapter failure prevents publication.
        if not staged.matches(root):
            raise ValidationError("Publication temporary ownership changed.")
        safe_path(root, relative)
        if original is not None:
            if not original.matches(root):
                raise ValidationError("Publication target ownership changed.")
            os.replace(temporary, target)
        elif os.name == "nt":
            os.rename(temporary, target)  # Windows rename refuses an existing target.
        else:
            os.link(temporary, target)
            temporary.unlink()
        return OwnedArtifact.capture(root, relative)
    finally:
        # Never remove a foreign replacement of our staging artifact.
        if staged is not None and staged.matches(root):
            remove_owned(root, staged)
        elif staged is None and temporary.exists():
            remaining = OwnedArtifact.capture(root, temporary.relative_to(root))
            if (remaining.device, remaining.inode) == (created.st_dev, created.st_ino):
                remove_owned(root, remaining)


def publish_directory(root: Path, staged: OwnedArtifact, relative: str) -> OwnedArtifact:
    target = safe_path(root, relative)
    if target.parent != staged.path.parent or not staged.path.is_dir() or not staged.matches(root):
        raise ValidationError("Directory publication requires an exact-owned same-parent stage.")
    if target.exists():
        raise ValidationError("Directory publication target already exists.")
    for parent, dirs, files in os.walk(staged.path, followlinks=False):
        for name in dirs + files:
            safe_path(root, (Path(parent) / name).relative_to(root))
    os.rename(staged.path, target)
    return OwnedArtifact.capture(root, relative)


@contextmanager
def temporary_workspace(config, *, uuid_provider: UuidProvider = new_uuid4) -> Iterator[Path]:
    root = config.path("tmp")
    root.mkdir(parents=True, exist_ok=True)
    path = safe_path(root, "op-" + require_uuid4(uuid_provider()))
    path.mkdir(mode=0o700)  # Exclusive create; never claims an existing directory.
    identity = OwnedArtifact.capture(root, path.name)
    succeeded = False
    try:
        yield path
        succeeded = True
    finally:
        if succeeded:
            # Directory mtime/size changes with legitimate work; inode ownership must persist.
            current = OwnedArtifact.capture(root, path.name)
            if (current.device, current.inode) != (identity.device, identity.inode):
                raise ValidationError("Temporary workspace ownership changed.")
            if not remove_owned(root, current):
                raise ValidationError("Temporary workspace cleanup failed.")
