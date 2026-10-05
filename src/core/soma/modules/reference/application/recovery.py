"""Reference-owned draft schemas/freshness supplied to Foundation recovery."""

from soma.foundation.errors import SomaError
from soma.foundation.identity import require_uuid4
from soma.foundation.working_copy import CopyContract
from soma.modules.reference.domain.settings import identifier


def contracts(reference):
    fields = [
        ("customer_organization", "metadata", {"name": 1024, "account_code": 512}),
        ("contact", "metadata", {"name": 1024, "email": 2048, "customer_id": 36}),
        ("dispatch_location", "metadata", {"name": 1024, "address": 8192}),
        ("local_user_profile", "metadata", {"display_name": 512}),
        ("setting", "metadata", {"value_json": 16384}),
        (
            "customer_organization",
            "account_code",
            {"code": 512, "mode": 32, "source": 36, "reason": 128},
        ),
        ("contact", "channel", {"email": 2048, "channel_id": 36, "channel_revision": 16}),
        ("contact", "affiliation", {"customer_id": 36, "reason": 128}),
        *(
            (kind, "lifecycle", {"reason": 128})
            for kind in ("customer_organization", "contact", "dispatch_location")
        ),
    ]
    result = []
    for kind, scope, limits in fields:

        def current(snapshot, target, scope, kind=kind):
            if kind == "setting":
                value = reference.settings.get(snapshot, target)
                return "ABSENT" if value.revision is None else str(value.revision)
            if kind == "local_user_profile":
                value = reference.profile.get(snapshot)
                return (
                    "MISSING"
                    if value is None or value["local_user_profile_id"] != target
                    else str(value["revision"])
                )
            try:
                value = reference.queries.detail(snapshot, kind, target)
                return str(value["revision"])
            except SomaError as error:
                if error.code == "NOT_FOUND":
                    return "NEW"
                raise

        result.append(
            CopyContract(
                contract_id="reference.edit." + kind + ("" if scope == "metadata" else "." + scope),
                version=1,
                target_type=kind,
                scope_key=scope,
                draft_schema={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        name: {"type": "string", "maxLength": limit}
                        for name, limit in limits.items()
                    },
                    "required": list(limits),
                },
                allowed_dirty_paths=frozenset("/" + name for name in limits),
                validate_target=(lambda key: reference.settings.get_definition(identifier(key)))
                if kind == "setting"
                else require_uuid4,
                current_revision=current,
            )
        )
    return tuple(result)
