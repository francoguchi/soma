from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import new_uuid4, require_uuid4
from soma.foundation.time import utc_epoch_seconds
from soma.foundation.transactions import CommandBoundary
from soma.modules.reference.adapters.persistence import dispatch as store
from soma.modules.reference.adapters.persistence.matching_profile import (
    require_persisted_matching_profile,
)
from soma.modules.reference.domain.dispatch import (
    validate_dispatch_name,
    validate_standalone_address,
)
from soma.modules.reference.ports.dispatch import DispatchCommandContext
from .commands import RESULT, event, result, revision


class DispatchLocations:
    def __init__(self, factory, audit_writer):
        self.audit = audit_writer
        self.boundary = CommandBoundary(factory, [RESULT], audit_writer)

    def _execute(self, command_id, action, request, preflight, prepare):
        def guarded(uow):
            require_persisted_matching_profile(uow.connection)
            return prepare(uow)

        return self.boundary.execute(
            command_id,
            action,
            request,
            (RESULT.schema, RESULT.version),
            None,
            preflight=preflight,
            prepare=guarded,
        )

    @staticmethod
    def _created(command_id, identity, lifecycle, mode, actor_id):
        return event(
            "reference.dispatch_location.created",
            command_id,
            identity,
            dict(
                dispatch_location_id=identity,
                address_mode=mode,
                new_revision=1,
                lifecycle_event_id=lifecycle,
            ),
            actor_id,
            target_type="dispatch_location",
            results=(("dispatch_location", identity), ("reference_lifecycle_event", lifecycle)),
        )

    def create_standalone(self, *, command_id, name, address_text, actor_id=None):
        data = {}

        def preflight():
            data["name"] = validate_dispatch_name(name)
            data["address"] = validate_standalone_address(address_text)
            if actor_id is not None:
                require_uuid4(actor_id)

        def prepare(uow):
            identity, lifecycle, now = new_uuid4(), new_uuid4(), utc_epoch_seconds()
            audit = self._created(command_id, identity, lifecycle, "standalone", actor_id)

            def apply(inner):
                store.insert(
                    inner.connection, identity, *data["name"], "standalone", data["address"], now
                )
                store.lifecycle_event(
                    inner.connection, lifecycle, identity, "created", now, command_id
                )
                return result(identity, 1), [audit]

            return apply

        return self._execute(
            command_id,
            "reference.create_dispatch",
            dict(name=name, address_text=address_text, actor_id=actor_id),
            preflight,
            prepare,
        )

    def create_dedicated_for_site(
        self, uow, *, parent_command_id, name, precomputed_name_match_key, command_context
    ):
        require_uuid4(parent_command_id)
        if type(command_context) is not DispatchCommandContext:
            raise ValidationError("Invalid Dispatch command context.")
        if command_context.actor_id is not None:
            require_uuid4(command_context.actor_id)
        stored, key = validate_dispatch_name(name)
        if key != precomputed_name_match_key:
            raise ValidationError("Precomputed Dispatch key is invalid.")
        require_persisted_matching_profile(uow.connection)
        if (
            uow.connection.execute(
                "SELECT 1 FROM command_receipts WHERE command_id=?", (parent_command_id,)
            ).fetchone()
            is None
        ):
            raise SomaError("PERSISTENCE_FAILURE", "Parent command receipt is required.", "none")
        identity, lifecycle, now = new_uuid4(), new_uuid4(), utc_epoch_seconds()
        store.insert(uow.connection, identity, stored, key, "site_derived", None, now)
        store.lifecycle_event(
            uow.connection, lifecycle, identity, "created", now, parent_command_id
        )
        self.audit.append(
            uow,
            self._created(
                parent_command_id, identity, lifecycle, "site_derived", command_context.actor_id
            ),
        )
        return identity

    def update_descriptive_data(
        self,
        *,
        command_id,
        dispatch_location_id,
        base_revision,
        name,
        address_text=None,
        actor_id=None,
    ):
        data = {}

        def preflight():
            require_uuid4(dispatch_location_id)
            revision(base_revision)
            if actor_id is not None:
                require_uuid4(actor_id)
            data["name"] = validate_dispatch_name(name)
            data["address"] = (
                None if address_text is None else validate_standalone_address(address_text)
            )

        def prepare(uow):
            row = store.active(uow.connection, dispatch_location_id, base_revision)
            if row[2] == "site_derived" and data["address"] is not None:
                raise ValidationError("Site-derived address is owned by Infrastructure.")
            if row[2] == "standalone" and data["address"] is None:
                raise ValidationError("Standalone address is required.")
            fields = []
            if tuple(row[:2]) != data["name"]:
                fields.append("name")
            if row[3] != data["address"]:
                fields.append("standalone_address_text")
            if not fields:
                return lambda inner: (result(dispatch_location_id, base_revision, False), [], False)
            lifecycle, now = new_uuid4(), utc_epoch_seconds()
            audit = event(
                "reference.dispatch_location.descriptive_updated",
                command_id,
                dispatch_location_id,
                dict(
                    target_type="dispatch_location",
                    target_id=dispatch_location_id,
                    prior_revision=base_revision,
                    new_revision=base_revision + 1,
                    changed_fields=fields,
                    lifecycle_event_id=lifecycle,
                ),
                actor_id,
                target_type="dispatch_location",
                results=(("reference_lifecycle_event", lifecycle),),
            )

            def apply(inner):
                store.update(
                    inner.connection, dispatch_location_id, *data["name"], data["address"], now
                )
                store.lifecycle_event(
                    inner.connection,
                    lifecycle,
                    dispatch_location_id,
                    "descriptive_corrected",
                    now,
                    command_id,
                )
                return result(dispatch_location_id, base_revision + 1), [audit]

            return apply

        return self._execute(
            command_id,
            "reference.update_dispatch",
            dict(
                dispatch_location_id=dispatch_location_id,
                base_revision=base_revision,
                name=name,
                address_text=address_text,
                actor_id=actor_id,
            ),
            preflight,
            prepare,
        )
