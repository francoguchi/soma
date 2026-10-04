"""Typed append-only audit; sensitivity policy belongs to the registered owner."""

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Callable

from soma.foundation.errors import ValidationError
from soma.foundation.identity import require_uuid4
from soma.foundation.time import utc_epoch_seconds
from soma.foundation.transactions import canonical


@dataclass(frozen=True)
class AuditContract:
    action: str
    version: int
    payload_schema: str
    payload_version: int
    validate: Callable
    classify_sensitive: Callable
    max_bytes: int = 16384
    max_results: int = 128


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    action: str
    version: int
    actor_kind: str
    target_type: str
    command_id: str
    payload: object
    actor_id: str | None = None
    target_id: str | None = None
    correlation_id: str | None = None
    job_id: str | None = None
    results: tuple[tuple[str, str], ...] = field(default_factory=tuple)


class AuditWriter:
    def __init__(self, contracts, *, utc_clock=utc_epoch_seconds):
        self.clock = utc_clock
        self.contracts = {}
        for contract in contracts:
            key = (contract.action, contract.version)
            if (
                key in self.contracts
                or not contract.action
                or type(contract.version) is not int
                or contract.version < 1
            ):
                raise ValidationError("Invalid or duplicate audit action ownership.")
            if (
                not callable(contract.validate)
                or not callable(contract.classify_sensitive)
                or not 1 <= contract.max_bytes <= 524288
                or not 0 <= contract.max_results <= 512
            ):
                raise ValidationError("Invalid audit bounds or sensitivity policy.")
            self.contracts[key] = contract

    def append(self, uow, event):
        require_uuid4(event.event_id)
        require_uuid4(event.command_id)
        for identity in (event.actor_id, event.job_id):
            if identity is not None:
                require_uuid4(identity)
        contract = self.contracts.get((event.action, event.version))
        if contract is None:
            raise ValidationError("Audit action contract is unavailable.")
        raw = canonical(event.payload, max_bytes=contract.max_bytes)
        contract.validate(event.payload)
        if contract.classify_sensitive(event.payload) is not False:
            raise ValidationError("Sensitive audit payload is forbidden.")
        if canonical(event.payload, max_bytes=contract.max_bytes) != raw:
            raise ValidationError("Audit validation changed the payload.")
        if (
            not event.actor_kind
            or not event.target_type
            or len(event.results) > contract.max_results
        ):
            raise ValidationError("Invalid audit context or result bound.")
        results = sorted(event.results)
        if len(set(results)) != len(results) or any(
            not t or not i or len(t.encode()) > 256 or len(i.encode()) > 256 for t, i in results
        ):
            raise ValidationError("Invalid audit result identity.")
        uow.connection.execute(
            "INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                event.event_id,
                event.action,
                event.version,
                event.actor_kind,
                event.actor_id,
                event.target_type,
                event.target_id,
                event.command_id,
                event.correlation_id,
                event.job_id,
                contract.payload_schema,
                contract.payload_version,
                raw.decode(),
                sha256(raw).hexdigest(),
                len(raw),
                self.clock(),
            ),
        )
        for ordinal, (kind, identity) in enumerate(results):
            uow.connection.execute(
                "INSERT INTO audit_event_results VALUES (?,?,?,?)",
                (event.event_id, ordinal, kind, identity),
            )
