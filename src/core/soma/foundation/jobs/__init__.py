"""Durable coordination; registered owners decide retry, cancellation and recovery."""

from dataclasses import dataclass
from hashlib import sha256
import re
from typing import Callable

from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import new_uuid4, require_uuid4
from soma.foundation.strict_json import loads_canonical_json
from soma.foundation.time import utc_epoch_seconds
from soma.foundation.transactions import UnitOfWork, canonical

ACTIVE = frozenset({"queued", "running", "waiting_review", "retry_wait"})
BOUNDS = dict(max_bytes=65536, max_depth=8, max_collection_items=512)


@dataclass(frozen=True)
class Recovery:
    state: str
    retry_at: int | None = None
    error_code: str | None = None


@dataclass(frozen=True)
class JobContract:
    job_type: str
    version: int
    validate_payload: Callable
    validate_checkpoint: Callable
    derive_dedupe_key: Callable
    validate_failure: Callable
    validate_cancellation: Callable
    recover_stale: Callable
    coalesce_states: frozenset = ACTIVE


@dataclass(frozen=True)
class Claim:
    job_id: str
    job_type: str
    version: int
    run_id: str
    ordinal: int
    started_at: int
    payload_sha256: str
    dedupe_sha256: str
    payload_json: str
    checkpoint_json: str | None


def error_code(value):
    if type(value) is not str or re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", value) is None:
        raise ValidationError("Invalid safe job error code.")


def timestamp(value):
    if type(value) is not int or value < 0:
        raise ValidationError("Job time must be UTC whole seconds.")


def validated(value, callback):
    raw = canonical(value, max_bytes=65536)
    # The registry cannot mutate a caller's payload or silently rewrite persisted truth.
    clone = loads_canonical_json(raw.decode(), **BOUNDS)
    callback(clone)
    if canonical(clone, max_bytes=65536) != raw:
        raise ValidationError("Job policy changed the payload.")
    return raw.decode()


class Coordinator:
    @staticmethod
    def counts(snapshot):
        states = sorted(ACTIVE | {"completed", "failed", "cancelled"})
        result = dict.fromkeys(states, 0)
        for state, count in snapshot.connection.execute("SELECT state,count(*) FROM durable_jobs GROUP BY state").fetchall():
            if state not in result:
                raise ValidationError("Unknown durable job state.")
            result[state] = count
        return result

    def __init__(
        self, factory, contracts=(), *, utc_clock=utc_epoch_seconds, uuid_provider=new_uuid4
    ):
        self.factory, self.clock, self.uuid = factory, utc_clock, uuid_provider
        self.contracts = {}
        for c in contracts:
            key = (c.job_type, c.version)
            if (
                key in self.contracts
                or not c.job_type
                or len(c.job_type.encode()) > 256
                or type(c.version) is not int
                or c.version < 1
                or not ACTIVE <= c.coalesce_states
                or not c.coalesce_states <= ACTIVE | {"completed"}
            ):
                raise ValidationError("Invalid or duplicate job ownership.")
            if any(
                not callable(getattr(c, name))
                for name in (
                    "validate_payload",
                    "validate_checkpoint",
                    "derive_dedupe_key",
                    "validate_failure",
                    "validate_cancellation",
                    "recover_stale",
                )
            ):
                raise ValidationError("Job policy is incomplete.")
            self.contracts[key] = c

    def require(self, kind, version):
        contract = self.contracts.get((kind, version))
        if contract is None:
            raise SomaError(
                "JOB_CONTRACT_UNAVAILABLE", "The registered job contract is unavailable."
            )
        return contract

    def _dedupe(self, contract, payload):
        before = canonical(payload, max_bytes=65536)
        key = contract.derive_dedupe_key(payload)
        if (
            type(key) is not str
            or not key
            or len(key.encode()) > 4096
            or canonical(payload, max_bytes=65536) != before
        ):
            raise ValidationError("Invalid semantic job deduplication key.")
        return sha256(
            canonical([contract.job_type, contract.version, key], max_bytes=65536)
        ).hexdigest()

    def enqueue(self, uow, kind, version, payload, *, correlation_id=None):
        c = self.require(kind, version)
        raw = validated(payload, c.validate_payload)
        dedupe = self._dedupe(c, loads_canonical_json(raw, **BOUNDS))
        states = sorted(c.coalesce_states)
        rows = uow.connection.execute(
            "SELECT job_id,payload_json,payload_sha256 FROM durable_jobs WHERE job_type=? AND contract_version=? AND dedupe_sha256=? AND state IN ("
            + ",".join("?" for _ in states)
            + ") ORDER BY created_at_utc,job_id LIMIT 2",
            (kind, version, dedupe, *states),
        ).fetchall()
        if rows:
            # Same semantic key may coalesce only equivalent canonical payload.
            if (
                len(rows) != 1
                or rows[0][1] != raw
                or rows[0][2] != sha256(raw.encode()).hexdigest()
            ):
                raise SomaError(
                    "JOB_DEDUPE_CONFLICT",
                    "Job deduplication identity conflicts with existing work.",
                )
            return rows[0][0]
        identity, now = self.uuid(), self.clock()
        require_uuid4(identity)
        timestamp(now)
        uow.connection.execute(
            "INSERT INTO durable_jobs(job_id,job_type,contract_version,state,payload_json,payload_sha256,dedupe_sha256,correlation_id,created_at_utc,updated_at_utc) VALUES (?,?,?,'queued',?,?,?,?,?,?)",
            (
                identity,
                kind,
                version,
                raw,
                sha256(raw.encode()).hexdigest(),
                dedupe,
                correlation_id,
                now,
                now,
            ),
        )
        return identity

    def _load(self, row):
        c = self.require(row["job_type"], row["contract_version"])
        require_uuid4(row["job_id"])
        raw = row["payload_json"]
        payload = loads_canonical_json(raw, **BOUNDS)
        if (
            validated(payload, c.validate_payload) != raw
            or sha256(raw.encode()).hexdigest() != row["payload_sha256"]
            or self._dedupe(c, payload) != row["dedupe_sha256"]
        ):
            raise ValidationError("Stored job payload identity is invalid.")
        checkpoint = None
        if row["checkpoint_json"] is not None:
            checkpoint = loads_canonical_json(row["checkpoint_json"], **BOUNDS)
            if (
                validated(checkpoint, c.validate_checkpoint) != row["checkpoint_json"]
                or sha256(row["checkpoint_json"].encode()).hexdigest() != row["checkpoint_sha256"]
            ):
                raise ValidationError("Stored job checkpoint identity is invalid.")
        elif row["checkpoint_sha256"] is not None:
            raise ValidationError("Stored job checkpoint identity is invalid.")
        return c, payload, checkpoint

    @staticmethod
    def _rows(uow, where, params=()):
        # Fixed projection remains independent of the native driver's row factory.
        fields = "job_id job_type contract_version state payload_json payload_sha256 dedupe_sha256 checkpoint_json checkpoint_sha256 attempt_count claimed_run_id claim_started_at_utc next_attempt_at_utc last_error_code correlation_id created_at_utc updated_at_utc".split()
        rows = uow.connection.execute(
            "SELECT " + ",".join(fields) + " FROM durable_jobs " + where, params
        ).fetchall()
        return [dict(zip(fields, row, strict=True)) for row in rows]

    def claim_next(self, run_id):
        require_uuid4(run_id)
        now = self.clock()
        timestamp(now)
        with UnitOfWork(self.factory) as uow:
            rows = self._rows(
                uow,
                "WHERE state='queued' OR (state='retry_wait' AND next_attempt_at_utc<=?) ORDER BY created_at_utc,job_id LIMIT 1",
                (now,),
            )
            if not rows:
                return None
            row = rows[0]
            try:
                self._load(row)
                if now < row["updated_at_utc"]:
                    raise ValidationError("Job clock regressed.")
            except Exception:
                self._unclaimable(
                    uow,
                    row["job_id"],
                    max(now, row["updated_at_utc"]),
                    "JOB_CONTRACT_UNAVAILABLE"
                    if (row["job_type"], row["contract_version"]) not in self.contracts
                    else "JOB_PAYLOAD_INVALID",
                )
                return None
            ordinal = row["attempt_count"] + 1
            uow.connection.execute(
                "UPDATE durable_jobs SET state='running',attempt_count=?,claimed_run_id=?,claim_started_at_utc=?,next_attempt_at_utc=NULL,updated_at_utc=? WHERE job_id=?",
                (ordinal, run_id, now, now, row["job_id"]),
            )
            return Claim(
                row["job_id"],
                row["job_type"],
                row["contract_version"],
                run_id,
                ordinal,
                now,
                row["payload_sha256"],
                row["dedupe_sha256"],
                row["payload_json"],
                row["checkpoint_json"],
            )

    def assert_current(self, uow, claim):
        rows = self._rows(uow, "WHERE job_id=?", (claim.job_id,))
        expected = (
            claim.job_type,
            claim.version,
            "running",
            claim.run_id,
            claim.ordinal,
            claim.started_at,
            claim.payload_sha256,
            claim.dedupe_sha256,
            claim.payload_json,
        )
        if (
            not rows
            or tuple(
                rows[0][k]
                for k in (
                    "job_type",
                    "contract_version",
                    "state",
                    "claimed_run_id",
                    "attempt_count",
                    "claim_started_at_utc",
                    "payload_sha256",
                    "dedupe_sha256",
                    "payload_json",
                )
            )
            != expected
        ):
            raise SomaError("JOB_CLAIM_CONFLICT", "The durable job claim is no longer current.")
        self._load(rows[0])
        return rows[0]

    def checkpoint(self, claim, value):
        with UnitOfWork(self.factory) as uow:
            self.checkpoint_in_uow(uow, claim, value)

    def checkpoint_in_uow(self, uow, claim, value):
        row = self.assert_current(uow, claim)
        now = self._now(row)
        raw = validated(value, self.require(claim.job_type, claim.version).validate_checkpoint)
        uow.connection.execute(
            "UPDATE durable_jobs SET checkpoint_json=?,checkpoint_sha256=?,updated_at_utc=? WHERE job_id=?",
            (raw, sha256(raw.encode()).hexdigest(), now, claim.job_id),
        )

    def _now(self, row):
        now = self.clock()
        timestamp(now)
        if now < row["updated_at_utc"]:
            raise ValidationError("Job clock regressed.")
        return now

    @staticmethod
    def _attempt(uow, row, now, outcome, code=None):
        uow.connection.execute(
            "INSERT INTO job_attempts VALUES (?,?,?,?,?,?,?)",
            (
                row["job_id"],
                row["attempt_count"],
                row["claimed_run_id"],
                row["claim_started_at_utc"],
                now,
                outcome,
                code,
            ),
        )

    @staticmethod
    def _terminal(uow, identity, now, state, code=None, retry_at=None):
        uow.connection.execute(
            "UPDATE durable_jobs SET state=?,claimed_run_id=NULL,claim_started_at_utc=NULL,next_attempt_at_utc=?,last_error_code=?,updated_at_utc=? WHERE job_id=?",
            (state, retry_at, code, now, identity),
        )

    def complete(self, claim):
        with UnitOfWork(self.factory) as uow:
            self.complete_in_uow(uow, claim)

    def complete_in_uow(self, uow, claim):
        row = self.assert_current(uow, claim)
        now = self._now(row)
        self._attempt(uow, row, now, "completed")
        self._terminal(uow, claim.job_id, now, "completed")

    def fail(self, claim, code, retry_at=None):
        with UnitOfWork(self.factory) as uow:
            row = self.assert_current(uow, claim)
            now = self._now(row)
            error_code(code)
            if retry_at is not None:
                timestamp(retry_at)
                if retry_at <= now:
                    raise ValidationError("Retry must be scheduled after the current time.")
            self.require(claim.job_type, claim.version).validate_failure(
                code, retry_at, claim.ordinal
            )
            self._attempt(uow, row, now, "failed", code)
            self._terminal(
                uow,
                claim.job_id,
                now,
                "failed" if retry_at is None else "retry_wait",
                code,
                retry_at,
            )

    def cancel(self, uow, identity, context, *, claim=None):
        require_uuid4(identity)
        rows = self._rows(uow, "WHERE job_id=?", (identity,))
        if not rows:
            raise ValidationError("Job identity is unavailable.")
        row = rows[0]
        # Terminal cancellation is idempotent and precedes current owner policy.
        if row["state"] not in ACTIVE:
            return row["state"]
        if row["state"] == "running":
            if claim is None or claim.job_id != identity:
                raise SomaError(
                    "JOB_CLAIM_CONFLICT", "Cancellation requires the current job claim."
                )
            row = self.assert_current(uow, claim)
        self.require(row["job_type"], row["contract_version"]).validate_cancellation(
            context, row["state"]
        )
        now = self._now(row)
        if row["state"] == "running":
            self._attempt(uow, row, now, "cancelled")
        self._terminal(uow, identity, now, "cancelled")
        return "cancelled"

    def _unclaimable(self, uow, identity, now, code):
        self._terminal(uow, identity, now, "failed", code)

    def recover(self, current_run_id, *, batch_size=100):
        require_uuid4(current_run_id)
        if type(batch_size) is not int or not 1 <= batch_size <= 100:
            raise ValidationError("Invalid recovery batch bound.")
        recovered = 0
        with UnitOfWork(self.factory) as uow:
            rows = self._rows(
                uow,
                "WHERE state='running' AND claimed_run_id<>? ORDER BY job_id LIMIT ?",
                (current_run_id, batch_size),
            )
            for row in rows:
                now = max(self.clock(), row["updated_at_utc"])
                timestamp(now)
                try:
                    c, payload, checkpoint = self._load(row)
                    disposition = c.recover_stale(payload, checkpoint, row["attempt_count"], now)
                    if canonical(payload, max_bytes=65536).decode() != row["payload_json"] or (
                        checkpoint is not None
                        and canonical(checkpoint, max_bytes=65536).decode()
                        != row["checkpoint_json"]
                    ):
                        raise ValidationError("Recovery changed durable evidence.")
                    if disposition.state not in {
                        "queued",
                        "retry_wait",
                        "waiting_review",
                        "failed",
                    }:
                        raise ValidationError("Invalid owner recovery state.")
                    if disposition.state == "retry_wait":
                        timestamp(disposition.retry_at)
                        if disposition.retry_at <= now:
                            raise ValidationError("Invalid recovery retry time.")
                    elif disposition.retry_at is not None:
                        raise ValidationError("Unexpected recovery retry time.")
                    if disposition.error_code is not None:
                        error_code(disposition.error_code)
                except Exception:
                    disposition = Recovery("failed", error_code="JOB_RECOVERY_UNAVAILABLE")
                self._attempt(uow, row, now, "interrupted", disposition.error_code)
                self._terminal(
                    uow,
                    row["job_id"],
                    now,
                    disposition.state,
                    disposition.error_code,
                    disposition.retry_at,
                )
                recovered += 1
        return recovered
