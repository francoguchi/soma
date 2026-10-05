"""Contact commands: replay, bounded preflight, state guards, receipt, writes, audit."""

from soma.foundation.errors import SomaError
from soma.foundation.identity import new_uuid4, require_uuid4
from soma.foundation.time import utc_epoch_seconds
from soma.foundation.transactions import CommandBoundary
from soma.modules.reference.adapters.persistence import contact as store
from soma.modules.reference.adapters.persistence.customer import active_customer
from soma.modules.reference.adapters.persistence.matching_profile import (
    require_persisted_matching_profile,
)
from soma.modules.reference.domain.contact import validate_contact_name
from soma.modules.reference.domain.channels import validate_email
from soma.modules.reference.domain.validation import validate_reason_category
from .commands import RESULT, event, result, revision


class Contacts:
    def __init__(self, factory, audit_writer):
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
    def _identity(contact_id, base_revision, actor_id):
        require_uuid4(contact_id)
        revision(base_revision)
        if actor_id is not None:
            require_uuid4(actor_id)

    @staticmethod
    def _reason(value):
        reason = validate_reason_category(value)
        if reason is None:
            raise SomaError("MATCH_INPUT_INVALID", "Reason category is required.", "correct_input")
        return reason

    def create_contact(
        self, *, command_id, name, initial_email=None, initial_customer_org_id=None, actor_id=None
    ):
        data = {}

        def preflight():
            data["name"] = validate_contact_name(name)
            data["email"] = None if initial_email is None else validate_email(initial_email)
            if initial_customer_org_id is not None:
                require_uuid4(initial_customer_org_id)
            if actor_id is not None:
                require_uuid4(actor_id)

        def prepare(uow):
            if initial_customer_org_id is not None:
                active_customer(uow.connection, initial_customer_org_id)
            identity, lifecycle, now = new_uuid4(), new_uuid4(), utc_epoch_seconds()
            channel = new_uuid4() if data["email"] else None
            affiliation = new_uuid4() if initial_customer_org_id else None
            audit = event(
                "reference.contact.created",
                command_id,
                identity,
                dict(
                    contact_id=identity,
                    new_revision=1,
                    initial_channel_id=channel,
                    initial_affiliation_id=affiliation,
                ),
                actor_id,
                target_type="contact",
                results=tuple(
                    [("contact", identity), ("reference_lifecycle_event", lifecycle)]
                    + ([("contact_channel", channel)] if channel else [])
                    + ([("contact_affiliation", affiliation)] if affiliation else [])
                ),
            )

            def apply(inner):
                store.insert_contact(inner.connection, identity, *data["name"], now)
                if channel:
                    store.insert_channel(inner.connection, channel, identity, *data["email"], now)
                if affiliation:
                    store.insert_affiliation(
                        inner.connection,
                        affiliation,
                        identity,
                        initial_customer_org_id,
                        now,
                        command_id,
                    )
                store.lifecycle_event(
                    inner.connection, lifecycle, identity, "created", now, command_id
                )
                return result(identity, 1), [audit]

            return apply

        return self._execute(
            command_id,
            "reference.create_contact",
            dict(
                name=name,
                initial_email=initial_email,
                initial_customer_org_id=initial_customer_org_id,
                actor_id=actor_id,
            ),
            preflight,
            prepare,
        )

    def update_descriptive_data(
        self, *, command_id, contact_id, base_revision, name, actor_id=None
    ):
        data = {}

        def preflight():
            self._identity(contact_id, base_revision, actor_id)
            data["name"] = validate_contact_name(name)

        def prepare(uow):
            row = store.active_contact(uow.connection, contact_id, base_revision)
            if tuple(row[1:3]) == data["name"]:
                return lambda inner: (result(contact_id, base_revision, False), [], False)
            lifecycle, now = new_uuid4(), utc_epoch_seconds()
            audit = event(
                "reference.contact.descriptive_updated",
                command_id,
                contact_id,
                dict(
                    target_type="contact",
                    target_id=contact_id,
                    prior_revision=base_revision,
                    new_revision=base_revision + 1,
                    changed_fields=["name"],
                    lifecycle_event_id=lifecycle,
                ),
                actor_id,
                target_type="contact",
                results=(("reference_lifecycle_event", lifecycle),),
            )

            def apply(inner):
                store.update_name(inner.connection, contact_id, *data["name"], now)
                store.lifecycle_event(
                    inner.connection,
                    lifecycle,
                    contact_id,
                    "descriptive_corrected",
                    now,
                    command_id,
                )
                return result(contact_id, base_revision + 1), [audit]

            return apply

        return self._execute(
            command_id,
            "reference.update_contact",
            dict(contact_id=contact_id, base_revision=base_revision, name=name, actor_id=actor_id),
            preflight,
            prepare,
        )

    def add_contact_channel(
        self,
        *,
        command_id,
        contact_id,
        contact_base_revision,
        channel_kind,
        value_text,
        actor_id=None,
    ):
        return self._channel_command(
            command_id=command_id,
            contact_id=contact_id,
            contact_base_revision=contact_base_revision,
            action="ADD",
            channel_kind=channel_kind,
            value_text=value_text,
            actor_id=actor_id,
        )

    def update_contact_channel(
        self,
        *,
        command_id,
        contact_id,
        contact_base_revision,
        contact_channel_id,
        channel_base_revision,
        value_text,
        actor_id=None,
    ):
        return self._channel_command(
            command_id=command_id,
            contact_id=contact_id,
            contact_base_revision=contact_base_revision,
            action="UPDATE",
            contact_channel_id=contact_channel_id,
            channel_base_revision=channel_base_revision,
            value_text=value_text,
            actor_id=actor_id,
        )

    def archive_contact_channel(
        self,
        *,
        command_id,
        contact_id,
        contact_base_revision,
        contact_channel_id,
        channel_base_revision,
        reason_category,
        actor_id=None,
    ):
        return self._channel_command(
            command_id=command_id,
            contact_id=contact_id,
            contact_base_revision=contact_base_revision,
            action="ARCHIVE",
            contact_channel_id=contact_channel_id,
            channel_base_revision=channel_base_revision,
            reason_category=reason_category,
            actor_id=actor_id,
        )

    def _channel_command(
        self,
        *,
        command_id,
        contact_id,
        contact_base_revision,
        action,
        channel_kind="email",
        value_text=None,
        contact_channel_id=None,
        channel_base_revision=None,
        reason_category=None,
        actor_id=None,
    ):
        data = {}

        def preflight():
            self._identity(contact_id, contact_base_revision, actor_id)
            if action != "ADD":
                require_uuid4(contact_channel_id)
                revision(channel_base_revision)
            if channel_kind != "email":
                raise SomaError(
                    "CHANNEL_INVALID", "Only email channels are supported.", "correct_input"
                )
            if action == "ARCHIVE":
                data["reason"] = self._reason(reason_category)
            else:
                data["email"] = validate_email(value_text)

        def prepare(uow):
            store.active_contact(uow.connection, contact_id, contact_base_revision)
            row = (
                None
                if action == "ADD"
                else store.active_channel(
                    uow.connection, contact_id, contact_channel_id, channel_base_revision
                )
            )
            if action == "UPDATE" and tuple(row[3:5]) == data["email"]:
                return lambda inner: (
                    result(contact_channel_id, channel_base_revision, False),
                    [],
                    False,
                )
            identity = new_uuid4() if action == "ADD" else contact_channel_id
            prior = None if row is None else channel_base_revision
            rev, now = 1 if prior is None else prior + 1, utc_epoch_seconds()
            payload = dict(
                contact_id=contact_id,
                contact_channel_id=identity,
                prior_channel_revision=prior,
                new_channel_revision=rev,
                prior_contact_revision=contact_base_revision,
                new_contact_revision=contact_base_revision + 1,
            )
            if action == "ARCHIVE":
                payload["reason_category"] = data["reason"]
            else:
                payload.update(channel_kind="email", change_kind=action)
            verb = {"ADD": "added", "UPDATE": "updated", "ARCHIVE": "archived"}[action]
            audit = event(
                "reference.contact_channel." + verb,
                command_id,
                identity,
                payload,
                actor_id,
                target_type="contact_channel",
                results=(("contact_channel", identity),),
            )

            def apply(inner):
                if action == "ADD":
                    store.insert_channel(
                        inner.connection, identity, contact_id, *data["email"], now
                    )
                elif action == "UPDATE":
                    store.update_channel(inner.connection, identity, *data["email"], now)
                else:
                    store.archive_channel(inner.connection, identity, now)
                store.bump_revision(inner.connection, contact_id, now)
                return result(identity, rev), [audit]

            return apply

        return self._execute(
            command_id,
            "reference.contact_channel." + action,
            dict(
                contact_id=contact_id,
                contact_base_revision=contact_base_revision,
                channel_kind=channel_kind,
                value_text=value_text,
                contact_channel_id=contact_channel_id,
                channel_base_revision=channel_base_revision,
                reason_category=reason_category,
                actor_id=actor_id,
            ),
            preflight,
            prepare,
        )

    def change_contact_affiliation(
        self,
        *,
        command_id,
        contact_id,
        base_revision,
        new_customer_org_id,
        reason_category,
        actor_id=None,
    ):
        data = {}

        def preflight():
            self._identity(contact_id, base_revision, actor_id)
            if new_customer_org_id is not None:
                require_uuid4(new_customer_org_id)
            data["reason"] = self._reason(reason_category)

        def prepare(uow):
            store.active_contact(uow.connection, contact_id, base_revision)
            if new_customer_org_id is not None:
                active_customer(uow.connection, new_customer_org_id)
            prior = store.current_affiliation(uow.connection, contact_id)
            old_customer = None if prior is None else prior[1]
            if old_customer == new_customer_org_id:
                return lambda inner: (result(contact_id, base_revision, False), [], False)
            identity, now = (new_uuid4() if new_customer_org_id else None), utc_epoch_seconds()
            audit = event(
                "reference.contact_affiliation.changed",
                command_id,
                contact_id,
                dict(
                    contact_id=contact_id,
                    prior_affiliation_id=None if prior is None else prior[0],
                    new_affiliation_id=identity,
                    prior_customer_org_id=old_customer,
                    new_customer_org_id=new_customer_org_id,
                    prior_contact_revision=base_revision,
                    new_contact_revision=base_revision + 1,
                    reason_category=data["reason"],
                ),
                actor_id,
                target_type="contact",
                results=tuple(
                    ("contact_affiliation", i)
                    for i in ([prior[0]] if prior else []) + ([identity] if identity else [])
                ),
            )

            def apply(inner):
                if prior:
                    store.close_affiliation(inner.connection, prior[0], now, command_id)
                if identity:
                    store.insert_affiliation(
                        inner.connection, identity, contact_id, new_customer_org_id, now, command_id
                    )
                store.bump_revision(inner.connection, contact_id, now)
                return result(contact_id, base_revision + 1), [audit]

            return apply

        return self._execute(
            command_id,
            "reference.change_contact_affiliation",
            dict(
                contact_id=contact_id,
                base_revision=base_revision,
                new_customer_org_id=new_customer_org_id,
                reason_category=reason_category,
                actor_id=actor_id,
            ),
            preflight,
            prepare,
        )
