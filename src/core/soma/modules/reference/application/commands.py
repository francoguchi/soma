from soma.foundation.audit import AuditEvent
from soma.foundation.errors import ValidationError
from soma.foundation.identity import new_uuid4, require_uuid4
from soma.foundation.transactions import ResultContract


def revision(value):
    if type(value) is not int or value < 1:
        raise ValidationError("Revision must be a positive integer.")
    return value


def validate_result(value):
    if type(value) is not dict or set(value) != {"outcome", "target_id", "revision"}:
        raise ValidationError("Invalid Reference mutation result.")
    if value["outcome"] not in {"APPLIED", "NO_CHANGE"}:
        raise ValidationError("Invalid Reference mutation outcome.")
    require_uuid4(value["target_id"])
    revision(value["revision"])


RESULT = ResultContract("ReferenceMutationResultV1", 1, validate_result)


def result(identity, rev, changed=True):
    return {
        "outcome": "APPLIED" if changed else "NO_CHANGE",
        "target_id": identity,
        "revision": rev,
    }


def event(
    action,
    command,
    identity,
    payload,
    actor_id=None,
    *,
    target_type="customer_organization",
    results=(),
):
    return AuditEvent(
        new_uuid4(),
        action,
        1,
        "local_admin" if actor_id else "system",
        target_type,
        command,
        payload,
        actor_id=actor_id,
        target_id=identity,
        results=results,
    )
