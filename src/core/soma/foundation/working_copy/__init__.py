"""Recoverable working intent, never accepted owner truth."""

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Callable

from jsonschema import Draft202012Validator

from soma.foundation.audit import AuditContract, AuditEvent, AuditWriter
from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import new_uuid4, require_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.strict_json import (
    canonical_json_bytes_bounded,
    loads_canonical_json,
    loads_strict_bytes,
)
from soma.foundation.time import utc_epoch_seconds
from soma.foundation.transactions import CommandBoundary, ResultContract

BOUNDS = dict(max_bytes=262144, max_depth=32, max_collection_items=65536)
COLUMNS = "working_copy_id contract_id contract_version target_type target_id scope_key base_revision draft_json draft_sha256 draft_bytes generation created_at_utc updated_at_utc expires_at_utc".split()


@dataclass(frozen=True)
class CopyContract:
    contract_id: str
    version: int
    target_type: str
    scope_key: str
    draft_schema: dict
    allowed_dirty_paths: frozenset[str]
    validate_target: Callable
    current_revision: Callable


def bounded_text(value, maximum=256):
    if type(value) is not str or not 1 <= len(value.encode("utf-8")) <= maximum or "\x00" in value:
        raise ValidationError("Working-copy identity exceeds its contract.")
    return value


class WorkingCopies:
    def __init__(self, factory, contracts=(), *, clock=utc_epoch_seconds):
        self.factory, self.clock = factory, clock
        registrations, validators = {}, {}
        for c in contracts:
            key = (bounded_text(c.contract_id), c.version)
            if (
                type(c.version) is not int
                or c.version < 1
                or key in registrations
                or not callable(c.validate_target)
                or not callable(c.current_revision)
                or type(c.allowed_dirty_paths) is not frozenset
                or any(
                    not path.startswith("/") or len(path) > 512 for path in c.allowed_dirty_paths
                )
            ):
                raise ValidationError("Invalid or duplicate working-copy owner registration.")
            schema = loads_strict_bytes(canonical_json_bytes_bounded(c.draft_schema, **BOUNDS))
            if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
                raise ValidationError("Working-copy draft requires a closed object schema.")
            Draft202012Validator.check_schema(schema)

            def closed(node):
                if isinstance(node, dict):
                    if (
                        "$ref" in node
                        or (
                            node.get("type") == "object"
                            or isinstance(node.get("type"), list)
                            and "object" in node["type"]
                        )
                        and node.get("additionalProperties") is not False
                    ):
                        raise ValidationError(
                            "Working-copy draft schemas must be closed and local."
                        )
                    for value in node.values():
                        closed(value)
                elif isinstance(node, list):
                    for value in node:
                        closed(value)

            closed(schema)
            registrations[key] = (c, canonical_json_bytes_bounded(schema, **BOUNDS))
            validators[key] = Draft202012Validator(schema)
        self.contracts, self.validators = (
            MappingProxyType(registrations),
            MappingProxyType(validators),
        )

        def audit_validate(value):
            if type(value) is not dict or set(value) != {
                "working_copy_id",
                "contract_id",
                "generation",
                "outcome",
            }:
                raise ValidationError()
            require_uuid4(value["working_copy_id"])

        def result_validate(value):
            from soma.foundation.contracts import validate_contract

            validate_contract("urn:soma:00:working-copy-result:v1", value)

        def prune_validate(value):
            if (
                type(value) is not dict
                or set(value) != {"deleted_count"}
                or type(value["deleted_count"]) is not int
                or not 0 <= value["deleted_count"] <= 100
            ):
                raise ValidationError("Invalid working-copy prune metadata.")

        writer = AuditWriter(
            [
                AuditContract(
                    "foundation.working_copy_changed",
                    1,
                    "WorkingCopyAuditV1",
                    1,
                    audit_validate,
                    lambda value: False,
                ),
                AuditContract(
                    "foundation.working_copies_pruned",
                    1,
                    "WorkingCopyPruneV1",
                    1,
                    prune_validate,
                    lambda value: False,
                ),
            ]
        )
        self.boundary = CommandBoundary(
            factory,
            [
                ResultContract("WorkingCopyResultV1", 1, result_validate),
                ResultContract("WorkingCopyPruneV1", 1, prune_validate),
            ],
            writer,
            utc_clock=clock,
            request_bounds=BOUNDS | {"max_bytes": 524288, "max_depth": 34},
        )

    def require(self, request):
        key = (request["contract_id"], request["contract_version"])
        row = self.contracts.get(key)
        if row is None or type(request["contract_version"]) is not int:
            raise SomaError(
                "WORKING_COPY_CONTRACT_UNAVAILABLE",
                "This edit surface has no registered recovery contract.",
            )
        c = row[0]
        if (request["target_type"], request["scope_key"]) != (c.target_type, c.scope_key):
            raise ValidationError("Working-copy target does not match its registered owner.")
        bounded_text(request["target_id"])
        c.validate_target(request["target_id"])
        bounded_text(request["base_revision"])
        return c, self.validators[key]

    def payload(self, request):
        c, validator = self.require(request)
        paths = request["dirty_paths"]
        if (
            type(paths) is not list
            or any(type(p) is not str for p in paths)
            or paths != sorted(set(paths))
            or not set(paths) <= c.allowed_dirty_paths
        ):
            raise ValidationError("Dirty fields must match the registered edit surface.")
        value = {"draft": request["draft"], "dirty_paths": paths}
        raw = canonical_json_bytes_bounded(value, **BOUNDS)
        if not validator.is_valid(request["draft"]):
            raise ValidationError("Draft does not satisfy its closed owner contract.")
        return raw

    @staticmethod
    def _row(reader, where, params):
        row = reader.connection.execute(
            "SELECT " + ",".join(COLUMNS) + " FROM ui_working_copies WHERE " + where, params
        ).fetchone()
        return dict(zip(COLUMNS, row, strict=True)) if row else None

    @staticmethod
    def _key(request):
        return tuple(
            request[k]
            for k in ("contract_id", "contract_version", "target_type", "target_id", "scope_key")
        )

    def _evidence(self, command, actor, row, outcome):
        result = {
            "working_copy_id": row["working_copy_id"],
            "generation": row["generation"],
            "draft_sha256": row["draft_sha256"],
            "updated_at_utc_s": row["updated_at_utc"],
            "expires_at_utc_s": row["expires_at_utc"],
            "outcome": outcome,
        }
        event = AuditEvent(
            new_uuid4(),
            "foundation.working_copy_changed",
            1,
            "local_admin",
            "working_copy",
            command,
            {
                "working_copy_id": row["working_copy_id"],
                "contract_id": row["contract_id"],
                "generation": row["generation"],
                "outcome": outcome,
            },
            actor_id=actor,
            target_id=row["working_copy_id"],
        )
        return result, [event]

    def checkpoint(self, request, actor):
        require_uuid4(actor)
        command = require_uuid4(request["command_id"])
        # Pure bounded parsing is outside the write. Replay still precedes owner reads.
        raw = canonical_json_bytes_bounded(
            {"draft": request["draft"], "dirty_paths": request["dirty_paths"]}, **BOUNDS
        )
        digest = sha256(raw).hexdigest()

        def operation(uow):
            self.payload(request)  # owner validation only after replay lookup
            now = self.clock()
            row = self._row(
                uow,
                "contract_id=? AND contract_version=? AND target_type=? AND target_id=? AND scope_key=?",
                self._key(request),
            )
            if row is not None and row["expires_at_utc"] <= now:
                if request["expected_generation"] != 0:
                    raise SomaError(
                        "WORKING_COPY_EXPIRED", "This recoverable copy has expired.", "refresh"
                    )
                uow.connection.execute(
                    "DELETE FROM ui_working_copies WHERE working_copy_id=?",
                    (row["working_copy_id"],),
                )
                row = None
            if type(request["expected_generation"]) is not int or request[
                "expected_generation"
            ] != (row["generation"] if row else 0):
                raise SomaError(
                    "WORKING_COPY_GENERATION_CONFLICT",
                    "Another checkpoint changed this copy. Review the recoverable copy before continuing.",
                    "refresh",
                )
            if row:
                if now < row["updated_at_utc"] or request["base_revision"] != row["base_revision"]:
                    raise SomaError(
                        "WORKING_COPY_BASE_CONFLICT",
                        "The copy retains its original base revision. Review before starting a new edit.",
                        "refresh",
                    )
                if (
                    row["draft_json"] == raw.decode()
                    and row["draft_sha256"] == digest
                    and row["draft_bytes"] == len(raw)
                ):
                    return self._evidence(command, actor, row, "NO_CHANGE")
                uow.connection.execute(
                    "UPDATE ui_working_copies SET draft_json=?,draft_sha256=?,draft_bytes=?,generation=generation+1,updated_at_utc=?,expires_at_utc=? WHERE working_copy_id=?",
                    (raw.decode(), digest, len(raw), now, now + 604800, row["working_copy_id"]),
                )
            else:
                if (
                    uow.connection.execute(
                        "SELECT count(*) FROM ui_working_copies WHERE expires_at_utc>?", (now,)
                    ).fetchone()[0]
                    >= 256
                ):
                    raise SomaError(
                        "WORKING_COPY_CAPACITY",
                        "Recoverable copy capacity is reached. Discard unused copies before continuing.",
                    )
                identity = new_uuid4()
                uow.connection.execute(
                    "INSERT INTO ui_working_copies VALUES (?,?,?,?,?,?,?,?,?,?,1,?,?,?)",
                    (
                        identity,
                        *self._key(request),
                        request["base_revision"],
                        raw.decode(),
                        digest,
                        len(raw),
                        now,
                        now,
                        now + 604800,
                    ),
                )
            row = self._row(
                uow,
                "contract_id=? AND contract_version=? AND target_type=? AND target_id=? AND scope_key=?",
                self._key(request),
            )
            return self._evidence(command, actor, row, "CHECKPOINTED")

        return self.boundary.execute(
            command,
            "foundation.checkpoint_working_copy",
            request | {"actor_id": actor},
            ("WorkingCopyResultV1", 1),
            operation,
        )

    def restore(self, request):
        self.require(request)
        with ReadSnapshot(self.factory) as snapshot:
            row = self._row(
                snapshot,
                "contract_id=? AND contract_version=? AND target_type=? AND target_id=? AND scope_key=?",
                self._key(request),
            )
            if row is None:
                raise SomaError(
                    "WORKING_COPY_NOT_FOUND", "No recoverable copy exists for this edit surface."
                )
            if row["expires_at_utc"] <= self.clock():
                raise SomaError("WORKING_COPY_EXPIRED", "This recoverable copy has expired.")
            value = loads_canonical_json(row["draft_json"], **BOUNDS)
            check = dict(request, base_revision=row["base_revision"], **value)
            raw = self.payload(check)
            if sha256(raw).hexdigest() != row["draft_sha256"] or len(raw) != row["draft_bytes"]:
                raise SomaError(
                    "WORKING_COPY_INTEGRITY_FAILURE", "The recoverable copy could not be verified."
                )
            owner = self.contracts[(row["contract_id"], row["contract_version"])][0]
            current = bounded_text(
                owner.current_revision(snapshot, row["target_id"], row["scope_key"])
            )
            return {
                "working_copy_id": row["working_copy_id"],
                "generation": row["generation"],
                "draft": value["draft"],
                "dirty_paths": value["dirty_paths"],
                "base_revision": row["base_revision"],
                "current_revision": current,
                "conflict": current != row["base_revision"],
                "updated_at_utc_s": row["updated_at_utc"],
                "expires_at_utc_s": row["expires_at_utc"],
            }

    def discard(self, command, identity, generation, actor):
        require_uuid4(command)
        require_uuid4(identity)
        require_uuid4(actor)

        def operation(uow):
            row = self._row(uow, "working_copy_id=?", (identity,))
            if row is None:
                raise SomaError("WORKING_COPY_NOT_FOUND", "This recoverable copy is unavailable.")
            self.require(row)
            if type(generation) is not int or row["generation"] != generation:
                raise SomaError(
                    "WORKING_COPY_GENERATION_CONFLICT",
                    "The recoverable copy changed. Review before discarding.",
                    "refresh",
                )
            uow.connection.execute(
                "DELETE FROM ui_working_copies WHERE working_copy_id=?", (identity,)
            )
            return self._evidence(command, actor, row, "DISCARDED")

        return self.boundary.execute(
            command,
            "foundation.discard_working_copy",
            {"working_copy_id": identity, "generation": generation, "actor_id": actor},
            ("WorkingCopyResultV1", 1),
            operation,
        )

    def prune(self, *, batch_size=100, command_id=None):
        if type(batch_size) is not int or not 1 <= batch_size <= 100:
            raise ValidationError("Pruning is bounded to at most 100 copies.")
        command = require_uuid4(command_id) if command_id is not None else new_uuid4()

        def operation(uow):
            result = uow.connection.execute(
                "DELETE FROM ui_working_copies WHERE working_copy_id IN (SELECT working_copy_id FROM ui_working_copies WHERE expires_at_utc<=? ORDER BY expires_at_utc,working_copy_id LIMIT ?)",
                (self.clock(), batch_size),
            )
            metadata = {"deleted_count": result.rowcount}
            event = AuditEvent(
                new_uuid4(),
                "foundation.working_copies_pruned",
                1,
                "system",
                "working_copy_batch",
                command,
                metadata,
                target_id=command,
            )
            return metadata, [event]

        return self.boundary.execute(
            command,
            "foundation.prune_working_copies",
            {"batch_size": batch_size},
            ("WorkingCopyPruneV1", 1),
            operation,
        )["deleted_count"]
