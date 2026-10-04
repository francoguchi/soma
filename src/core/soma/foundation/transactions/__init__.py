"""Application-owned transactions and exact command replay."""

from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
from typing import Callable

from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import require_uuid4
from soma.foundation.persistence.connections import persistence_failure
from soma.foundation.strict_json import canonical_json_bytes_bounded, loads_canonical_json
from soma.foundation.time import utc_epoch_seconds

_active = ContextVar("soma_write_transaction", default=False)
BOUNDS = dict(max_bytes=524288, max_depth=8, max_collection_items=512)


def canonical(value, *, max_bytes=524288):
    return canonical_json_bytes_bounded(value, **(BOUNDS | {"max_bytes": max_bytes}))


class Participant:
    """SQL participants cannot control the application transaction or return raw cursors."""

    def __init__(self, connection):
        self.__connection = connection

    def execute(self, sql, parameters=()):
        if not sql.lstrip().split() or sql.lstrip().split()[0].upper() not in {
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "WITH",
        }:
            raise ValidationError("Transaction participants may only query or mutate records.")
        cursor = self.__connection.execute(sql, parameters)
        return Result(cursor)


class Result:
    def __init__(self, cursor):
        self.__cursor = cursor
        self.rowcount = cursor.rowcount

    def fetchone(self):
        return self.__cursor.fetchone()

    def fetchall(self):
        return self.__cursor.fetchall()


class UnitOfWork:
    def __init__(self, factory):
        self.factory = factory
        self.__connection = None

    def __enter__(self):
        if _active.get() or self.__connection is not None:
            raise ValidationError("Nested write transactions are forbidden.")
        self.__token = _active.set(True)
        try:
            self.__connection = self.factory.open()
            self.__connection.execute("BEGIN IMMEDIATE")
            self.connection = Participant(self.__connection)
            return self
        except BaseException as exc:
            if self.__connection is not None:
                self.__connection.close()
                self.__connection = None
            _active.reset(self.__token)
            if isinstance(exc, SomaError) or not isinstance(exc, Exception):
                raise
            raise persistence_failure(exc) from None

    def __exit__(self, kind, value, traceback):
        try:
            self.__connection.execute("ROLLBACK" if kind else "COMMIT")
        except Exception as exc:
            if not kind:
                raise persistence_failure(exc) from None
        finally:
            self.__connection.close()
            self.__connection = None
            del self.connection
            _active.reset(self.__token)


@dataclass(frozen=True)
class ResultContract:
    schema: str
    version: int
    validate: Callable


class CommandBoundary:
    def __init__(self, factory, result_contracts, audit_writer, *, utc_clock=utc_epoch_seconds, request_bounds=None):
        self.factory = factory
        self.audit = audit_writer
        self.clock = utc_clock
        self.request_bounds = dict(request_bounds or BOUNDS)
        self.contracts = {}
        for contract in result_contracts:
            key = (contract.schema, contract.version)
            if (
                key in self.contracts
                or not contract.schema
                or type(contract.version) is not int
                or contract.version < 1
            ):
                raise ValidationError("Invalid or duplicate command result contract.")
            self.contracts[key] = contract

    def execute(
        self, command_id, command_type, request, result_contract, operation, *, correlation_id=None
    ):
        """operation(uow) returns exact result and required owner audit inputs."""
        require_uuid4(command_id)
        if not command_type or len(command_type.encode()) > 256:
            raise ValidationError("Invalid command type.")
        digest = sha256(canonical_json_bytes_bounded(request, **self.request_bounds)).hexdigest()
        with UnitOfWork(self.factory) as uow:
            # Replay must precede owner preparation, current-state reads, and authorization.
            receipt = uow.connection.execute(
                "SELECT command_type,request_sha256 FROM command_receipts WHERE command_id=?",
                (command_id,),
            ).fetchone()
            if receipt is not None:
                if receipt != (command_type, digest):
                    raise SomaError(
                        "COMMAND_ID_CONFLICT",
                        "Command identity was already used for a different request.",
                    )
                row = uow.connection.execute(
                    "SELECT result_schema,result_version,result_json,result_sha256,result_bytes FROM command_receipt_results WHERE command_id=?",
                    (command_id,),
                ).fetchone()
                try:
                    contract = self.contracts[(row[0], row[1])]
                    raw = row[2].encode("utf-8")
                    if sha256(raw).hexdigest() != row[3] or len(raw) != row[4]:
                        raise ValueError()
                    result = loads_canonical_json(row[2], **BOUNDS)
                    before = canonical(result)
                    contract.validate(result)
                    if canonical(result) != before:
                        raise ValueError()
                    return result
                except Exception:
                    raise SomaError(
                        "COMMAND_REPLAY_UNAVAILABLE",
                        "The exact historical command result is unavailable.",
                    ) from None
            contract = self.contracts.get(result_contract)
            if contract is None:
                raise ValidationError("Command result contract is unavailable.")
            uow.connection.execute(
                "INSERT INTO command_receipts VALUES (?,?,?,?,?)",
                (command_id, command_type, digest, correlation_id, self.clock()),
            )
            result, events = operation(uow)
            raw = canonical(result)
            contract.validate(result)
            if canonical(result) != raw:
                raise ValidationError("Contract validation changed the result.")
            if not events:
                raise ValidationError("Authoritative commands require owner audit evidence.")
            for event in events:
                if event.command_id != command_id:
                    raise ValidationError("Audit command identity does not match.")
                self.audit.append(uow, event)
            uow.connection.execute(
                "INSERT INTO command_receipt_results VALUES (?,?,?,?,?,?)",
                (
                    command_id,
                    contract.schema,
                    contract.version,
                    raw.decode(),
                    sha256(raw).hexdigest(),
                    len(raw),
                ),
            )
            return loads_canonical_json(raw.decode(), **BOUNDS)
