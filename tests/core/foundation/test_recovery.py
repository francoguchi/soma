# ruff: noqa: F811 -- shared native pytest fixtures

import pytest

from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import new_uuid4
from soma.foundation.security.deliberate_action import DeliberateProofs, ProofAction
from soma.foundation.transactions import UnitOfWork
from soma.foundation.working_copy import CopyContract, WorkingCopies
from test_persistence import database  # noqa: F401


def copy_contract(revision):
    def target(value):
        if not value.startswith("probe-"):
            raise ValidationError()

    return CopyContract(
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
        target,
        lambda snapshot, identity, scope: revision[0],
    )


def request(**overrides):
    return dict(
        command_id=new_uuid4(),
        contract_id="ProbeEditV1",
        contract_version=1,
        target_type="probe",
        target_id="probe-a",
        scope_key="notes",
        base_revision="rev-1",
        expected_generation=0,
        draft={"note": "Working intent"},
        dirty_paths=["/note"],
        **overrides,
    )


def test_copy_checkpoint_nochange_generation_restore_conflict_and_exact_replay(database):
    _, _, factory, _ = database
    revision, clock, actor = ["rev-1"], [1000], new_uuid4()
    copies = WorkingCopies(factory, [copy_contract(revision)], clock=lambda: clock[0])
    first = request()
    result = copies.checkpoint(first, actor)
    assert result["generation"] == 1 and result["outcome"] == "CHECKPOINTED"
    nochange = dict(first, command_id=new_uuid4(), expected_generation=1)
    assert copies.checkpoint(nochange, actor)["outcome"] == "NO_CHANGE"
    changed = dict(
        first, command_id=new_uuid4(), expected_generation=1, draft={"note": "Changed intent"}
    )
    assert copies.checkpoint(changed, actor)["generation"] == 2
    with pytest.raises(SomaError) as error:
        copies.checkpoint(dict(first, command_id=new_uuid4()), actor)
    assert error.value.code == "WORKING_COPY_GENERATION_CONFLICT"
    restored = copies.restore(first)
    assert restored["draft"] == {"note": "Changed intent"} and not restored["conflict"]
    revision[0] = "rev-2"
    restored = copies.restore(first)
    assert (
        restored["conflict"]
        and restored["base_revision"] == "rev-1"
        and restored["current_revision"] == "rev-2"
    )
    with pytest.raises(SomaError) as error:
        copies.checkpoint(
            dict(changed, command_id=new_uuid4(), expected_generation=2, base_revision="rev-2"),
            actor,
        )
    assert error.value.code == "WORKING_COPY_BASE_CONFLICT"
    discard_command = new_uuid4()
    discarded = copies.discard(discard_command, result["working_copy_id"], 2, actor)
    assert discarded["outcome"] == "DISCARDED"
    assert copies.discard(discard_command, result["working_copy_id"], 2, actor) == discarded
    # Historical checkpoint survives discard and unavailable current owner registry.
    assert WorkingCopies(factory, clock=lambda: 9000).checkpoint(first, actor) == result


@pytest.mark.parametrize(
    "change",
    [
        {"draft": {"unknown": "x"}},
        {"dirty_paths": ["/unregistered"]},
        {"dirty_paths": ["/note", "/note"]},
        {"target_id": "foreign"},
        {"contract_version": 2},
        {"draft": {"note": "é" * 131073}},
    ],
)
def test_invalid_copy_contract_fields_paths_target_and_bytes_preserve_truth(database, change):
    _, _, factory, _ = database
    copies = WorkingCopies(factory, [copy_contract(["rev-1"])])
    with pytest.raises(SomaError):
        copies.checkpoint(dict(request(), **change), new_uuid4())
    c = factory.open()
    assert c.execute("SELECT count(*) FROM ui_working_copies").fetchone() == (0,)
    assert c.execute("SELECT count(*) FROM command_receipts").fetchone() == (0,)
    c.close()


def test_copy_audit_failure_rolls_back_and_draft_never_enters_evidence(database, monkeypatch):
    _, _, factory, _ = database
    copies = WorkingCopies(factory, [copy_contract(["rev-1"])], clock=lambda: 1000)
    actor, first = new_uuid4(), request()
    writer = copies.boundary.audit
    original = writer.append

    def fail(*args):
        raise RuntimeError("injected required audit failure")

    monkeypatch.setattr(writer, "append", fail)
    with pytest.raises(RuntimeError):
        copies.checkpoint(first, actor)
    c = factory.open()
    assert c.execute("SELECT count(*) FROM ui_working_copies").fetchone() == (0,)
    c.close()
    monkeypatch.setattr(writer, "append", original)
    saved = copies.checkpoint(first, actor)
    c = factory.open()
    evidence = repr(c.execute("SELECT * FROM audit_events").fetchall()) + repr(
        c.execute("SELECT * FROM command_receipt_results").fetchall()
    )
    assert "Working intent" not in evidence
    c.close()
    monkeypatch.setattr(writer, "append", fail)
    with pytest.raises(RuntimeError):
        copies.discard(new_uuid4(), saved["working_copy_id"], 1, actor)
    assert copies.restore(first)["draft"] == first["draft"]


def test_copy_capacity_refresh_expiry_and_bounded_prune(database):
    _, _, factory, _ = database
    clock, actor = [1000], new_uuid4()
    copies = WorkingCopies(factory, [copy_contract(["rev-1"])], clock=lambda: clock[0])
    for index in range(256):
        copies.checkpoint(dict(request(), target_id="probe-" + str(index)), actor)
    with pytest.raises(SomaError) as error:
        copies.checkpoint(dict(request(), target_id="probe-overflow"), actor)
    assert error.value.code == "WORKING_COPY_CAPACITY"
    copies.checkpoint(
        dict(request(), target_id="probe-0", expected_generation=1, draft={"note": "Updated"}),
        actor,
    )
    clock[0] += 604800
    with pytest.raises(SomaError) as error:
        copies.restore(dict(request(), target_id="probe-0"))
    assert error.value.code == "WORKING_COPY_EXPIRED"
    assert copies.prune() == 100 and copies.prune() == 100 and copies.prune() == 56
    assert copies.prune() == 0
    assert copies.checkpoint(request(), actor)["generation"] == 1


def test_copy_restore_is_observational_and_detects_corrupt_bytes(database):
    config, _, factory, _ = database
    copies = WorkingCopies(factory, [copy_contract(["rev-1"])], clock=lambda: 1000)
    first = request()
    copies.checkpoint(first, new_uuid4())
    c = factory.open()
    before = c.execute("SELECT * FROM ui_working_copies").fetchall()
    copies.restore(first)
    assert c.execute("SELECT * FROM ui_working_copies").fetchall() == before
    c.execute("UPDATE ui_working_copies SET draft_sha256=?", ("0" * 64,))
    c.close()
    with pytest.raises(SomaError) as error:
        copies.restore(first)
    assert error.value.code == "WORKING_COPY_INTEGRITY_FAILURE"


def context(run=None):
    return {"run_id": run or new_uuid4(), "actor_id": new_uuid4(), "session_fingerprint": "a" * 64}


def binding(**changes):
    return dict(
        action_code="probe.remove",
        target_type="probe",
        target_id="probe-a",
        base_revision="rev-1",
        preview_fingerprint="1" * 64,
        **changes,
    )


def test_server_timed_hold_exact_bindings_single_use_even_after_owner_rollback(database):
    _, _, factory, _ = database
    ctx, now = context(), [100.0]
    proofs = DeliberateProofs(
        ctx["run_id"],
        [ProofAction("probe.remove", "probe", "impact_preview_plus_hold")],
        clock=lambda: now[0],
    )
    challenge = proofs.issue(ctx, binding())
    now[0] += 2.999
    with pytest.raises(SomaError):
        proofs.complete(ctx, challenge["challenge_id"], binding())
    now[0] += 0.001
    proof = proofs.complete(ctx, challenge["challenge_id"], binding())
    assert proof["proof_token"] not in repr(proofs.proofs)
    with pytest.raises(RuntimeError):
        with UnitOfWork(factory) as uow:
            proofs.consume(uow, ctx, binding(), proof["proof_token"])
            raise RuntimeError("owner mutation rolled back")
    with UnitOfWork(factory) as uow:
        with pytest.raises(SomaError):
            proofs.consume(uow, ctx, binding(), proof["proof_token"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("action_code", "foreign"),
        ("target_type", "foreign"),
        ("target_id", "probe-other"),
        ("base_revision", "rev-2"),
        ("preview_fingerprint", "2" * 64),
    ],
)
def test_proof_binding_mismatch_never_consumes_authority(database, field, value):
    _, _, factory, _ = database
    ctx, now = context(), [100.0]
    proofs = DeliberateProofs(
        ctx["run_id"],
        [ProofAction("probe.remove", "probe", "impact_preview_plus_hold")],
        clock=lambda: now[0],
    )
    challenge = proofs.issue(ctx, binding())
    now[0] += 3
    token = proofs.complete(ctx, challenge["challenge_id"], binding())["proof_token"]
    bad = dict(binding(), **{field: value})
    with UnitOfWork(factory) as uow:
        with pytest.raises(SomaError):
            proofs.consume(uow, ctx, bad, token)
        proofs.consume(uow, ctx, binding(), token)


def test_proof_expiry_cross_session_run_preview_and_abandon():
    ctx, now = context(), [100.0]
    proofs = DeliberateProofs(
        ctx["run_id"],
        [ProofAction("probe.remove", "probe", "impact_preview_plus_hold")],
        clock=lambda: now[0],
    )
    with pytest.raises(SomaError):
        proofs.issue(ctx, dict(binding(), preview_fingerprint=None))
    challenge = proofs.issue(ctx, binding())
    now[0] += 3
    for bad in [
        dict(ctx, run_id=new_uuid4()),
        dict(ctx, session_fingerprint="b" * 64),
        dict(ctx, actor_id=new_uuid4()),
    ]:
        with pytest.raises(SomaError):
            proofs.complete(bad, challenge["challenge_id"], binding())
    proofs.abandon(ctx, challenge["challenge_id"])
    with pytest.raises(SomaError):
        proofs.complete(ctx, challenge["challenge_id"], binding())
    challenge = proofs.issue(ctx, binding())
    now[0] += 15
    with pytest.raises(SomaError):
        proofs.complete(ctx, challenge["challenge_id"], binding())
    challenge = proofs.issue(ctx, binding())
    now[0] += 3
    proofs.complete(ctx, challenge["challenge_id"], binding())
    now[0] += 30
    proofs._expire()
    assert proofs.proofs == {}
    with pytest.raises(ValidationError):
        proofs.consume(None, ctx, binding(), "x" * 44)


def test_prune_has_atomic_metadata_and_exact_replay(database, monkeypatch):
    _, _, factory, _ = database
    now, actor = [1000], new_uuid4()
    copies = WorkingCopies(factory, [copy_contract(["rev-1"])], clock=lambda: now[0])
    copies.checkpoint(request(), actor)
    now[0] += 604800
    original = copies.boundary.audit.append

    def fail(*args):
        raise RuntimeError("required maintenance audit failed")

    monkeypatch.setattr(copies.boundary.audit, "append", fail)
    with pytest.raises(RuntimeError):
        copies.prune()
    c = factory.open()
    assert c.execute("SELECT count(*) FROM ui_working_copies").fetchone() == (1,)
    c.close()
    monkeypatch.setattr(copies.boundary.audit, "append", original)
    command = new_uuid4()
    assert copies.prune(command_id=command) == 1
    assert copies.prune(command_id=command) == 1
    c = factory.open()
    assert c.execute(
        "SELECT payload_json FROM audit_events WHERE action_type='foundation.working_copies_pruned'"
    ).fetchall() == [('{"deleted_count":1}',)]
    c.close()


def test_nested_nullable_object_contract_requires_closed_schema(database):
    from dataclasses import replace

    _, _, factory, _ = database
    contract = copy_contract(["rev-1"])
    schema = {**contract.draft_schema, "properties": {"note": {"type": ["object", "null"]}}}
    with pytest.raises(ValidationError):
        WorkingCopies(factory, [replace(contract, draft_schema=schema)])
