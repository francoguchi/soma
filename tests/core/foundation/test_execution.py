# ruff: noqa: F811 -- pytest discovers imported native fixtures by name
from dataclasses import replace

import pytest

from soma.foundation.audit import AuditContract, AuditEvent, AuditWriter
from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import new_uuid4
from soma.foundation.jobs import Coordinator, JobContract, Recovery
from soma.foundation.transactions import CommandBoundary, ResultContract, UnitOfWork
from test_persistence import database  # noqa: F401 -- shared native encrypted fixture


def validate(value):
    if type(value) is not dict or set(value) != {"value"} or type(value["value"]) is not int:
        raise ValidationError("Invalid probe value.")


def boundary(factory, **policy):
    contract = AuditContract("probe.changed", 1, "ProbeV1", 1, validate, lambda p: False)
    writer = AuditWriter([replace(contract, **policy)])
    return CommandBoundary(factory, [ResultContract("ProbeResultV1", 1, validate)], writer)


def event(command, **overrides):
    return replace(
        AuditEvent(new_uuid4(), "probe.changed", 1, "system", "probe", command, {"value": 1}),
        **overrides,
    )


def count(factory, table):
    c = factory.open()
    try:
        return c.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    finally:
        c.close()


def test_replay_precedes_owner_reads_and_returns_exact_historical_result(database):
    _, _, factory, _ = database
    command = new_uuid4()
    calls = []

    def operation(uow):
        calls.append(True)
        return {"value": 1}, [event(command)]

    b = boundary(factory)
    first = b.execute(command, "probe", {"value": 1}, ("ProbeResultV1", 1), operation)
    first["value"] = 999
    replay = b.execute(
        command,
        "probe",
        {"value": 1},
        ("unavailable-current-contract", 2),
        lambda u: pytest.fail("owner ran on replay"),
        correlation_id="new-correlation",
    )
    assert replay == {"value": 1} and calls == [True]
    assert count(factory, "audit_events") == 1
    for kind, request in [("different", {"value": 1}), ("probe", {"value": 2})]:
        with pytest.raises(SomaError, match="different request"):
            b.execute(command, kind, request, ("ProbeResultV1", 1), operation)


def test_explicit_no_change_commits_exact_result_without_audit(database):
    _, _, factory, _ = database
    command = new_uuid4()
    b = boundary(factory)

    result = b.execute(
        command,
        "probe-no-change",
        {"value": 1},
        ("ProbeResultV1", 1),
        lambda uow: ({"value": 1}, [], False),
    )
    assert result == {"value": 1}
    assert count(factory, "command_receipts") == 1
    assert count(factory, "command_receipt_results") == 1
    assert count(factory, "audit_events") == 0

    with UnitOfWork(factory) as uow:
        uow.connection.execute("UPDATE instance_metadata SET created_at_utc=901")

    replay = b.execute(
        command,
        "probe-no-change",
        {"value": 1},
        ("ProbeResultV1", 1),
        lambda uow: pytest.fail("owner ran on NO_CHANGE replay"),
    )
    assert replay == {"value": 1}
    assert count(factory, "audit_events") == 0


def test_null_exact_result_is_replayed_without_preflight_or_owner_execution(database):
    _, _, factory, _ = database
    command = new_uuid4()
    b = CommandBoundary(factory, [ResultContract("NullV1", 1, lambda value: None)], AuditWriter([]))
    assert b.execute(command, "null", {}, ("NullV1", 1), lambda uow: (None, [], False)) is None
    assert (
        b.execute(
            command,
            "null",
            {},
            ("NullV1", 1),
            lambda uow: pytest.fail("owner ran on null replay"),
            preflight=lambda: pytest.fail("preflight ran on null replay"),
        )
        is None
    )


@pytest.mark.parametrize(
    "outcome",
    [
        ({"value": 1}, [], True),
        ({"value": 1}, [None], False),
        ({"value": 1}, [], "no-change"),
    ],
)
def test_command_change_state_and_audit_evidence_are_consistent(database, outcome):
    _, _, factory, _ = database
    command = new_uuid4()
    with pytest.raises(ValidationError):
        boundary(factory).execute(
            command,
            "probe-outcome",
            {},
            ("ProbeResultV1", 1),
            lambda uow: outcome,
        )
    assert count(factory, "command_receipts") == 0
    assert count(factory, "command_receipt_results") == 0
    assert count(factory, "audit_events") == 0


@pytest.mark.parametrize(
    "damage",
    [
        "DELETE FROM command_receipt_results",
        "UPDATE command_receipt_results SET result_json='{}'",
        "UPDATE command_receipt_results SET result_bytes=0",
        "UPDATE command_receipt_results SET result_schema='unknown'",
    ],
)
def test_corrupt_or_missing_replay_never_reruns(database, damage):
    _, _, factory, _ = database
    command = new_uuid4()
    b = boundary(factory)
    b.execute(
        command, "probe", {}, ("ProbeResultV1", 1), lambda u: ({"value": 1}, [event(command)])
    )
    with UnitOfWork(factory) as uow:
        uow.connection.execute(damage)
    with pytest.raises(SomaError) as caught:
        b.execute(command, "probe", {}, ("ProbeResultV1", 1), lambda u: pytest.fail("reran"))
    assert caught.value.code == "COMMAND_REPLAY_UNAVAILABLE"


def test_second_audit_failure_rolls_back_receipts_mutation_and_first_audit(database):
    _, _, factory, _ = database
    command = new_uuid4()

    def operation(uow):
        uow.connection.execute("UPDATE instance_metadata SET created_at_utc=900")
        return {"value": 1}, [event(command), event(command, action="unknown")]

    with pytest.raises(ValidationError):
        boundary(factory).execute(command, "probe", {}, ("ProbeResultV1", 1), operation)
    assert all(
        count(factory, table) == 0
        for table in ("command_receipts", "command_receipt_results", "audit_events")
    )
    c = factory.open()
    assert c.execute("SELECT created_at_utc FROM instance_metadata").fetchone()[0] != 900
    c.close()


def test_nested_commit_and_participant_transaction_control_are_rejected(database):
    _, _, factory, _ = database
    with UnitOfWork(factory) as uow:
        with pytest.raises(ValidationError):
            with UnitOfWork(factory):
                pass
        for sql in ("COMMIT", "ROLLBACK", "PRAGMA foreign_keys=OFF", "BEGIN", "SAVEPOINT bypass"):
            with pytest.raises(ValidationError):
                uow.connection.execute(sql)
        assert not hasattr(uow.connection, "commit")
        assert not hasattr(uow.connection.execute("SELECT 1"), "connection")
    with UnitOfWork(factory) as uow:
        assert uow.connection.execute("SELECT 1").fetchone() == (1,)


@pytest.mark.parametrize(
    "policy", [{"classify_sensitive": lambda p: True}, {"max_bytes": 1}, {"max_results": 0}]
)
def test_audit_sensitivity_and_owner_bounds_roll_back(database, policy):
    _, _, factory, _ = database
    command = new_uuid4()
    with pytest.raises(ValidationError):
        boundary(factory, **policy).execute(
            command,
            "probe",
            {},
            ("ProbeResultV1", 1),
            lambda u: ({"value": 1}, [event(command, results=(("probe", "a"),))]),
        )
    assert count(factory, "command_receipts") == 0


def test_audit_is_database_append_only_and_ordinals_are_deterministic(database):
    _, _, factory, manifest = database
    command = new_uuid4()
    e = event(command, results=(("probe", "z"), ("probe", "a")))
    boundary(factory).execute(
        command, "probe", {}, ("ProbeResultV1", 1), lambda u: ({"value": 1}, [e])
    )
    c = factory.open()
    try:
        assert c.execute(
            "SELECT ordinal,result_id FROM audit_event_results ORDER BY ordinal"
        ).fetchall() == [(0, "a"), (1, "z")]
        for table in ("audit_events", "audit_event_results"):
            for sql in (
                f"DELETE FROM {table}",
                f"UPDATE {table} SET "
                + ("action_type='x'" if table == "audit_events" else "result_id='x'"),
            ):
                with pytest.raises(Exception) as error:
                    c.execute(sql)
                assert error.value.sqlite_errorcode & 255 == 19
        from soma.foundation.persistence.schema_verify import verify_schema

        verify_schema(c, manifest)
        assert c.execute("SELECT count(*) FROM audit_events").fetchone() == (1,)
    finally:
        c.close()


def coordinator(factory, clock, **overrides):
    def failure(code, retry, attempt):
        if code != "PROBE_FAILED" or (retry is not None and attempt > 2):
            raise ValidationError("Retry denied.")

    def cancel(context, state):
        if context != {"allow": True}:
            raise ValidationError("Cancellation denied.")

    contract = JobContract(
        "probe",
        1,
        validate,
        validate,
        lambda p: str(p["value"]),
        failure,
        cancel,
        lambda p, checkpoint, attempt, now: Recovery("queued")
        if checkpoint
        else Recovery("failed", error_code="JOB_INTERRUPTED"),
    )
    return Coordinator(factory, [replace(contract, **overrides)], utc_clock=lambda: clock[0])


def enqueue(jobs, factory, value=1):
    with UnitOfWork(factory) as uow:
        return jobs.enqueue(uow, "probe", 1, {"value": value})


def test_job_coalescing_and_transaction_rollback(database):
    _, _, factory, _ = database
    jobs = coordinator(factory, [100])
    identity = enqueue(jobs, factory)
    assert enqueue(jobs, factory) == identity
    with pytest.raises(RuntimeError):
        with UnitOfWork(factory) as uow:
            jobs.enqueue(uow, "probe", 1, {"value": 2})
            raise RuntimeError("owner failed")
    assert count(factory, "durable_jobs") == 1
    claim = jobs.claim_next(new_uuid4())
    assert claim.job_id == identity and jobs.claim_next(new_uuid4()) is None
    jobs.complete(claim)
    assert enqueue(jobs, factory) != identity


@pytest.mark.parametrize(
    "field,value",
    [
        ("run_id", None),
        ("ordinal", 2),
        ("started_at", 101),
        ("version", 2),
        ("job_type", "other"),
        ("dedupe_sha256", "0" * 64),
        ("payload_sha256", "0" * 64),
        ("payload_json", "{}"),
    ],
)
def test_every_claim_component_is_revalidated_before_checkpoint_policy(database, field, value):
    _, _, factory, _ = database
    jobs = coordinator(factory, [100])
    enqueue(jobs, factory)
    claim = jobs.claim_next(new_uuid4())
    forged = replace(claim, **{field: new_uuid4() if value is None else value})
    for operation in (
        lambda: jobs.checkpoint(forged, {"invalid": True}),
        lambda: jobs.complete(forged),
        lambda: jobs.fail(forged, "invalid"),
    ):
        with pytest.raises(SomaError) as caught:
            operation()
        assert caught.value.code == "JOB_CLAIM_CONFLICT"
    assert count(factory, "job_attempts") == 0


def test_checkpoint_recovery_revokes_stale_worker_without_guessing(database):
    _, _, factory, _ = database
    clock = [100]
    jobs = coordinator(factory, clock)
    enqueue(jobs, factory)
    stale = jobs.claim_next(new_uuid4())
    jobs.checkpoint(stale, {"value": 3})
    clock[0] = 101
    new_run = new_uuid4()
    assert jobs.recover(new_run) == 1
    with pytest.raises(SomaError) as caught:
        jobs.complete(stale)
    assert caught.value.code == "JOB_CLAIM_CONFLICT"
    resumed = jobs.claim_next(new_run)
    assert resumed.ordinal == 2 and resumed.checkpoint_json == '{"value":3}'
    jobs.complete(resumed)
    assert count(factory, "job_attempts") == 2 and jobs.recover(new_run) == 0


@pytest.mark.parametrize(
    "damage",
    [
        "UPDATE durable_jobs SET contract_version=9",
        "UPDATE durable_jobs SET checkpoint_json='{}',checkpoint_sha256='" + "0" * 64 + "'",
        "UPDATE durable_jobs SET payload_sha256='" + "0" * 64 + "'",
    ],
)
def test_unknown_or_corrupt_job_fails_before_handler(database, damage):
    _, _, factory, _ = database
    jobs = coordinator(factory, [100])
    enqueue(jobs, factory)
    with UnitOfWork(factory) as uow:
        uow.connection.execute(damage)
    assert jobs.claim_next(new_uuid4()) is None
    c = factory.open()
    assert c.execute("SELECT state FROM durable_jobs").fetchone() == ("failed",)
    c.close()


def test_retry_cancel_and_terminal_cancel_precedence(database):
    _, _, factory, _ = database
    clock = [100]
    jobs = coordinator(factory, clock)
    identity = enqueue(jobs, factory)
    claim = jobs.claim_next(new_uuid4())
    jobs.fail(claim, "PROBE_FAILED", 105)
    assert jobs.claim_next(new_uuid4()) is None
    clock[0] = 105
    claim = jobs.claim_next(new_uuid4())
    assert claim.ordinal == 2
    with UnitOfWork(factory) as uow:
        assert jobs.cancel(uow, identity, {"allow": True}, claim=claim) == "cancelled"
    with pytest.raises(SomaError):
        jobs.checkpoint(claim, {"value": 2})
    with UnitOfWork(factory) as uow:
        assert jobs.cancel(uow, identity, {"deny": True}) == "cancelled"
    assert count(factory, "job_attempts") == 2
