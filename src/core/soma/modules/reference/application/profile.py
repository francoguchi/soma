from soma.foundation.errors import SomaError
from soma.foundation.identity import require_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.time import utc_epoch_seconds
from soma.foundation.transactions import CommandBoundary
from soma.modules.reference.adapters.persistence import profile as store
from soma.modules.reference.domain.validation import validate_display_name
from .commands import RESULT, event, result, revision


class Profile:
    def __init__(self, factory, audit_writer):
        self.factory, self.audit = factory, audit_writer
        self.boundary = CommandBoundary(factory, [RESULT], audit_writer)

    def create_for_local_admin(
        self, uow, *, parent_command_id, actor_id, display_name="Local Administrator"
    ):
        require_uuid4(actor_id)
        require_uuid4(parent_command_id)
        name = validate_display_name(display_name)
        store.create(uow.connection, actor_id, name, utc_epoch_seconds(), parent_command_id)
        self.audit.append(
            uow,
            event(
                "local_user_profile.created",
                parent_command_id,
                actor_id,
                {"local_user_profile_id": actor_id, "metadata_revision": 1},
                actor_id,
                target_type="local_user_profile",
            ),
        )
        return actor_id

    def get_singleton(self):
        with ReadSnapshot(self.factory) as snapshot:
            return self.get(snapshot)

    def get(self, snapshot):
        row = store.singleton(snapshot.connection)
        return (
            None
            if row is None
            else dict(zip(("local_user_profile_id", "display_name", "revision"), row))
        )

    def update_display_name(self, *, command_id, actor_id, base_revision, display_name):
        request = dict(actor_id=actor_id, base_revision=base_revision, display_name=display_name)
        prepared = {}

        def preflight():
            require_uuid4(actor_id)
            revision(base_revision)
            name = validate_display_name(display_name)
            prepared["name"] = name

        def prepare(uow):
            row = store.singleton(uow.connection)
            if row is None or row[0] != actor_id:
                raise SomaError("NOT_FOUND", "Local User Profile does not exist.", "refresh")
            if row[2] != base_revision:
                raise SomaError("STALE_REVISION", "Profile metadata revision changed.", "refresh")
            if row[1] == prepared["name"]:
                return lambda inner: (result(actor_id, base_revision, False), [], False)
            now = utc_epoch_seconds()
            audit = event(
                "local_user_profile.display_name_updated",
                command_id,
                actor_id,
                {
                    "local_user_profile_id": actor_id,
                    "prior_revision": base_revision,
                    "new_revision": base_revision + 1,
                    "changed_field": "display_name",
                },
                actor_id,
                target_type="local_user_profile",
            )

            def apply(inner):
                store.update(inner.connection, actor_id, prepared["name"], now)
                return result(actor_id, base_revision + 1), [audit]

            return apply

        return self.boundary.execute(
            command_id,
            "reference.update_profile",
            request,
            (RESULT.schema, RESULT.version),
            None,
            preflight=preflight,
            prepare=prepare,
        )
