import asyncio
import math
import os
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from soma.foundation.build import BuildIdentity, current_build
from soma.foundation.config import RuntimeConfig, local_app_data
from soma.foundation.context import correlation_scope, current_correlation
from soma.foundation.contracts import validate_contract
from soma.foundation.errors import FieldError, SomaError, ValidationError, error_envelope
from soma.foundation.filesystem import (
    OwnedArtifact,
    atomic_write,
    publish_directory,
    remove_owned,
    safe_path,
    temporary_workspace,
)
from soma.foundation.identity import new_uuid4, require_uuid4
from soma.foundation.strict_json import (
    canonical_json_bytes,
    canonical_json_bytes_bounded,
    loads_strict,
    loads_strict_bytes,
    sha256_canonical_json,
)
from soma.foundation.testing import ManualClocks, SequenceUuids
from soma.foundation.time import Deadline, normalize_utc

UUID = "4d204e28-3a66-43cb-81ca-a31cc94c9b11"


@pytest.mark.parametrize(
    "text",
    ['{"a":1,"a":2}', '{"v":NaN}', '{"v":Infinity}', '{"v":-Infinity}', '{"v":1e999}', '"\\ud800"'],
)
def test_beta_strict_json_regressions(text):
    with pytest.raises(ValidationError):
        loads_strict(text)


@pytest.mark.parametrize(
    "value",
    [(1, 2), {1: "coercible"}, {"v": (1,)}, {"v": math.nan}, {"v": {1, 2}}, {"v": "\ud800"}],
)
def test_canonicalization_never_silently_coerces_containers(value):
    with pytest.raises(ValidationError):
        canonical_json_bytes(value)


def test_beta_canonical_hash_and_bounds():
    left, right = {"z": [2, 1], "a": {"x": "é"}}, {"a": {"x": "é"}, "z": [2, 1]}
    assert sha256_canonical_json(left) == sha256_canonical_json(right)
    assert canonical_json_bytes(left) == b'{"a":{"x":"\xc3\xa9"},"z":[2,1]}'
    for value, limits in [([0] * 11, (1000, 8, 10)), ([[[0]]], (1000, 2, 100)), ("é", (3, 8, 100))]:
        with pytest.raises(ValidationError):
            canonical_json_bytes_bounded(
                value, max_bytes=limits[0], max_depth=limits[1], max_collection_items=limits[2]
            )
    with pytest.raises(ValidationError):
        loads_strict_bytes(b'"\xff"')
    cyclic = []
    cyclic.append(cyclic)
    with pytest.raises(ValidationError):
        canonical_json_bytes(cyclic)


@pytest.mark.parametrize(
    "value",
    [UUID.upper(), UUID.replace("-", ""), "no", None, "4d204e28-3a66-13cb-81ca-a31cc94c9b11"],
)
def test_uuid_canonical_external_validation(value):
    with pytest.raises(ValidationError):
        require_uuid4(value)


def test_nested_operation_error_contract_and_safe_unknown_failures():
    def adapter():
        assert current_correlation() == UUID
        raise OSError("SELECT secret FROM C:/customer/passwords token=private")

    with correlation_scope(uuid_provider=SequenceUuids([UUID])) as correlation:
        assert correlation == UUID
        with correlation_scope():
            assert current_correlation() == correlation
            try:
                adapter()
            except Exception as exc:
                failure = error_envelope(exc)
        assert failure == {
            "code": "INTERNAL_ERROR",
            "summary": "The operation could not be completed.",
            "recoverability": "none",
            "safe_next_action": None,
            "correlation_id": UUID,
        }
        handled = SomaError(
            "VALIDATION_FAILED",
            "Check input.",
            "correct_input",
            "Correct the field.",
            (FieldError("name", "VALUE_REQUIRED", "A name is required."),),
        )
        assert error_envelope(handled)["fields"][0]["path"] == "name"
    with pytest.raises(RuntimeError):
        current_correlation()
    with pytest.raises(ValidationError):
        with correlation_scope("bad\nmetadata"):
            pass


def test_async_correlations_are_isolated():
    async def operation(identifier):
        with correlation_scope(identifier):
            await asyncio.sleep(0)
            return current_correlation()

    async def run():
        ids = [new_uuid4(), new_uuid4()]
        assert await asyncio.gather(*(operation(identifier) for identifier in ids)) == ids

    asyncio.run(run())


@pytest.mark.parametrize(
    "patch",
    [
        {"surprise": True},
        {"recoverability": "maybe"},
        {"summary": ""},
        {"summary": "x" * 513},
        {"safe_next_action": ""},
        {"correlation_id": UUID.upper()},
        {"fields": [{"path": "x", "code": "OK", "summary": "x", "extra": 1}]},
        {"fields": [{"path": "x", "code": "OK", "summary": "x"}] * 65},
    ],
)
def test_exact_error_envelope_shape(patch):
    value = {
        "code": "INTERNAL_ERROR",
        "summary": "Safe.",
        "recoverability": "none",
        "safe_next_action": None,
        "correlation_id": UUID,
        **patch,
    }
    with pytest.raises(ValidationError):
        validate_contract("urn:soma:00:error-envelope:v1", value)


def test_wall_clock_changes_do_not_change_timeout():
    clocks = ManualClocks(utc_s=100)
    deadline = Deadline.after_ms(3000, clocks.monotonic)
    clocks.advance_ms(2999)
    clocks.utc_s = -10000
    assert not deadline.expired()
    clocks.utc_s = 9999999
    clocks.advance_ms(1)
    assert deadline.expired()
    with pytest.raises(ValidationError):
        Deadline.after_ms(True)
    assert normalize_utc(datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=-5)))) == datetime(
        2026, 1, 1, 5, tzinfo=UTC
    )
    with pytest.raises(ValidationError):
        normalize_utc(datetime(2026, 1, 1))


def config_for(tmp_path):
    return RuntimeConfig(tmp_path / "instance", tmp_path / "checkout", "test")


def test_config_paths_default_and_explicit_override(tmp_path):
    config = config_for(tmp_path)
    for owner in ("data", "runtime", "diagnostics", "tmp", "backups"):
        assert config.path(owner).is_relative_to(config.instance_root)
    assert not config.instance_root.exists()  # Resolution has no mutation side effects.
    with pytest.raises(ValidationError):
        config.path("data", "../runtime/other")
    with pytest.raises(ValidationError):
        config.path("data", "thing:alternate")
    with pytest.raises(ValidationError):
        RuntimeConfig(tmp_path / "checkout/data", tmp_path / "checkout")
    with pytest.raises(ValidationError):
        RuntimeConfig(Path("relative"), tmp_path / "checkout")
    if os.name == "nt":
        default = RuntimeConfig.discover(tmp_path / "checkout")
        assert (
            default.instance_root == (local_app_data() / "SOMA/Development/instance-v1").resolve()
        )
        explicit = RuntimeConfig.discover(
            tmp_path / "checkout", instance_override=tmp_path / "explicit", mode="test"
        )
        assert explicit.instance_root == tmp_path / "explicit"


def test_atomic_file_directory_publication_and_exact_deletion(tmp_path):
    first = atomic_write(tmp_path, "record", b"first")
    second = atomic_write(tmp_path, "record", b"second")
    assert second.path.read_bytes() == b"second"
    assert not remove_owned(tmp_path, first)
    assert remove_owned(tmp_path, second)
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / "part").write_bytes(b"complete")
    artifact = OwnedArtifact.capture(tmp_path, "stage")
    published = publish_directory(tmp_path, artifact, "complete")
    assert (published.path / "part").read_bytes() == b"complete"
    assert remove_owned(tmp_path, published)
    assert list(tmp_path.iterdir()) == []


def test_acl_failure_prevents_publication(tmp_path):
    atomic_write(tmp_path, "record", b"original")

    def deny(path):
        raise PermissionError("denied")

    with pytest.raises(PermissionError):
        atomic_write(tmp_path, "record", b"replacement", protect=deny)
    assert (tmp_path / "record").read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [tmp_path / "record"]


def test_publication_rejects_replaced_target(tmp_path):
    atomic_write(tmp_path, "record", b"original")

    def race(path):
        (tmp_path / "record").write_bytes(b"foreign change")

    with pytest.raises(ValidationError):
        atomic_write(tmp_path, "record", b"replacement", protect=race)
    assert (tmp_path / "record").read_bytes() == b"foreign change"


def test_temporary_success_cleanup_failure_evidence_and_collision(tmp_path):
    config = config_for(tmp_path)
    with temporary_workspace(config, uuid_provider=lambda: UUID) as stage:
        assert stage.parent == config.path("tmp")
        (stage / "part").write_bytes(b"scratch")
    assert not stage.exists()
    with pytest.raises(RuntimeError):
        with temporary_workspace(config, uuid_provider=lambda: UUID) as stage:
            raise RuntimeError("failed operation")
    assert stage.exists()
    with pytest.raises(FileExistsError):
        with temporary_workspace(config, uuid_provider=lambda: UUID):
            pass


def test_windows_junction_redirection_rejected(tmp_path):
    import subprocess

    outside = tmp_path / "outside"
    outside.mkdir()
    owned = tmp_path / "owned"
    owned.mkdir()
    link = owned / "redirected"
    if os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True
        )
        assert result.returncode == 0, result.stderr
    else:
        link.symlink_to(outside, target_is_directory=True)
    try:
        with pytest.raises(ValidationError):
            safe_path(owned, "redirected/new")
        with pytest.raises(ValidationError):
            RuntimeConfig(link, tmp_path / "checkout", "test")
    finally:
        if os.name == "nt":
            os.rmdir(link)
        else:
            link.unlink()


def test_build_identity_consistency_and_invalid_protocol():
    value = current_build()
    assert value.application_version == "0.1.0.dev0"
    assert value.build_kind == "source"
    with pytest.raises(ValidationError):
        BuildIdentity(**{**value.as_dict(), "runtime_protocol_version": True})


def test_foreign_publication_temporary_is_preserved(tmp_path):
    def replace_staging(path):
        path.unlink()
        path.write_bytes(b"foreign temporary")

    with pytest.raises(ValidationError):
        atomic_write(tmp_path, "record", b"intended content", protect=replace_staging)
    assert not (tmp_path / "record").exists()
    assert len(list(tmp_path.iterdir())) == 1
    assert next(tmp_path.iterdir()).read_bytes() == b"foreign temporary"


def test_native_owner_acl_applied_before_publication(tmp_path):
    from soma.foundation.filesystem.windows_acl import protect_owner

    if os.name != "nt":
        with pytest.raises(ValidationError):
            protect_owner(tmp_path)
        return
    artifact = atomic_write(tmp_path, "protected", b"nonsecret fixture", protect=protect_owner)
    assert artifact.path.read_bytes() == b"nonsecret fixture"
    import subprocess

    result = subprocess.run(["icacls", str(artifact.path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert "(I)" not in result.stdout  # The protected DACL has no inherited entries.
    assert "SYSTEM" in result.stdout


@pytest.mark.parametrize(
    "patch",
    [
        {"code": "INTERNAL_ERROR\n"},
        {"correlation_id": UUID + "\n"},
        {"fields": [{"path": "x", "code": "VALUE_REQUIRED\n", "summary": "Safe."}]},
    ],
)
def test_error_identifiers_reject_trailing_newline(patch):
    value = {
        "code": "INTERNAL_ERROR",
        "summary": "Safe.",
        "recoverability": "none",
        "safe_next_action": None,
        "correlation_id": UUID,
        **patch,
    }
    with pytest.raises(ValidationError):
        validate_contract("urn:soma:00:error-envelope:v1", value)


def test_foreign_new_publication_target_is_preserved(tmp_path):
    def concurrent_target(path):
        (tmp_path / "record").write_bytes(b"foreign target")

    with pytest.raises(FileExistsError):
        atomic_write(tmp_path, "record", b"replacement", protect=concurrent_target)
    assert (tmp_path / "record").read_bytes() == b"foreign target"
    assert list(tmp_path.iterdir()) == [tmp_path / "record"]


def test_path_inspection_failure_returns_safe_validation():
    from soma.foundation.filesystem import _check_components

    class Inaccessible:
        parents = ()

        def lstat(self):
            raise PermissionError("private filesystem path")

    with pytest.raises(ValidationError) as caught:
        _check_components(Inaccessible())
    assert "private filesystem" not in str(caught.value)
