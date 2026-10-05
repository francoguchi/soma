from __future__ import annotations

import string

from soma.foundation.audit import AuditContract, AuditWriter
from soma.foundation.errors import ValidationError
from soma.foundation.identity import require_uuid4


def _dict(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValidationError("Invalid Reference audit payload.")
    return value


def _revision(value):
    if type(value) is not int or value < 1:
        raise ValidationError("Invalid Reference audit revision.")
    return value


def _optional_uuid(value):
    if value is not None:
        require_uuid4(value)


def _reason(value):
    if value is not None and (
        type(value) is not str
        or not value
        or len(value.encode("utf-8", errors="strict")) > 128
        or any(character in value for character in ("\x00", "\r", "\n"))
    ):
        raise ValidationError("Invalid Reference audit reason category.")


def _hash(value):
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in string.hexdigits for character in value)
    ):
        raise ValidationError("Invalid Reference review fingerprint.")


def _profile_created(value):
    value = _dict(value, {"local_user_profile_id", "metadata_revision"})
    require_uuid4(value["local_user_profile_id"])
    if value["metadata_revision"] != 1:
        raise ValidationError("Invalid Local User Profile creation revision.")


def _profile_updated(value):
    value = _dict(
        value,
        {"local_user_profile_id", "prior_revision", "new_revision", "changed_field"},
    )
    require_uuid4(value["local_user_profile_id"])
    prior = _revision(value["prior_revision"])
    if value["new_revision"] != prior + 1 or value["changed_field"] != "display_name":
        raise ValidationError("Invalid Local User Profile update evidence.")


def _customer_created(value):
    value = _dict(
        value,
        {
            "customer_org_id",
            "new_revision",
            "account_code_claim_created",
            "reason_category",
        },
    )
    require_uuid4(value["customer_org_id"])
    if value["new_revision"] != 1 or type(value["account_code_claim_created"]) is not bool:
        raise ValidationError("Invalid Customer creation evidence.")
    _reason(value["reason_category"])


def _descriptive_updated(value, target_type):
    value = _dict(
        value,
        {
            "target_type",
            "target_id",
            "prior_revision",
            "new_revision",
            "changed_fields",
            "lifecycle_event_id",
        },
    )
    if value["target_type"] != target_type:
        raise ValidationError("Invalid Reference descriptive target.")
    require_uuid4(value["target_id"])
    require_uuid4(value["lifecycle_event_id"])
    prior = _revision(value["prior_revision"])
    if _revision(value["new_revision"]) != prior + 1 or value["changed_fields"] != ["name"]:
        raise ValidationError("Invalid Customer descriptive update evidence.")


def _customer_descriptive_updated(value):
    _descriptive_updated(value, "customer_organization")


def _contact_descriptive_updated(value):
    _descriptive_updated(value, "contact")


def _account_code_set(value):
    value = _dict(
        value,
        {
            "customer_org_id",
            "customer_org_identifier_id",
            "superseded_identifier_id",
            "prior_revision",
            "new_revision",
            "change_kind",
            "reason_category",
        },
    )
    require_uuid4(value["customer_org_id"])
    require_uuid4(value["customer_org_identifier_id"])
    _optional_uuid(value["superseded_identifier_id"])
    prior = _revision(value["prior_revision"])
    if value["new_revision"] != prior + 1 or value["change_kind"] not in {"SET", "REPLACE"}:
        raise ValidationError("Invalid Customer Account Code change evidence.")
    if (value["change_kind"] == "SET") != (value["superseded_identifier_id"] is None):
        raise ValidationError("Customer Account Code change classification is inconsistent.")
    _reason(value["reason_category"])


def _review_validator(expected_action):
    def validate(value):
        value = _dict(
            value,
            {
                "proposed_action",
                "review_snapshot_hash",
                "review_context_id",
                "from_customer_org_id",
                "to_customer_org_id",
                "changed_identifier_ids",
                "changed_customer_org_ids",
                "reason_category",
            },
        )
        if value["proposed_action"] != expected_action:
            raise ValidationError("Invalid Customer Account Code review action.")
        _hash(value["review_snapshot_hash"])
        if value["review_context_id"] is not None and (
            type(value["review_context_id"]) is not str
            or not value["review_context_id"]
            or len(value["review_context_id"].encode("utf-8", errors="strict")) > 256
        ):
            raise ValidationError("Invalid Account Code review context identity.")
        _optional_uuid(value["from_customer_org_id"])
        require_uuid4(value["to_customer_org_id"])
        for key in ("changed_identifier_ids", "changed_customer_org_ids"):
            items = value[key]
            if type(items) is not list or not items or len(items) > 128:
                raise ValidationError("Invalid bounded Account Code review result identities.")
            for identity in items:
                require_uuid4(identity)
            if len(set(items)) != len(items):
                raise ValidationError("Duplicate Account Code review result identity.")
        _reason(value["reason_category"])

    return validate


def reference_audit_contracts() -> tuple[AuditContract, ...]:
    def safe(value):
        return False

    return (
        AuditContract(
            "reference.dispatch_location.created",
            1,
            "DispatchLocationAuditV1",
            1,
            _dispatch_created,
            safe,
        ),
        AuditContract(
            "reference.dispatch_location.descriptive_updated",
            1,
            "ReferenceDescriptiveAuditV1",
            1,
            _dispatch_updated,
            safe,
        ),
        AuditContract(
            "reference.archived",
            1,
            "ReferenceLifecycleAuditV1",
            1,
            _lifecycle_validator("archived"),
            safe,
        ),
        AuditContract(
            "reference.reactivated",
            1,
            "ReferenceLifecycleAuditV1",
            1,
            _lifecycle_validator("active"),
            safe,
        ),
        AuditContract("reference.contact.created", 1, "ContactAuditV1", 1, _contact_created, safe),
        AuditContract(
            "reference.contact.descriptive_updated",
            1,
            "ReferenceDescriptiveAuditV1",
            1,
            _contact_descriptive_updated,
            safe,
        ),
        AuditContract(
            "reference.contact_channel.added",
            1,
            "ContactChannelAuditV1",
            1,
            _channel_validator("ADD"),
            safe,
        ),
        AuditContract(
            "reference.contact_channel.updated",
            1,
            "ContactChannelAuditV1",
            1,
            _channel_validator("UPDATE"),
            safe,
        ),
        AuditContract(
            "reference.contact_channel.archived",
            1,
            "ContactChannelArchiveAuditV1",
            1,
            _channel_validator("ARCHIVE"),
            safe,
        ),
        AuditContract(
            "reference.contact_affiliation.changed",
            1,
            "ContactAffiliationAuditV1",
            1,
            _affiliation_changed,
            safe,
        ),
        AuditContract(
            "local_user_profile.created",
            1,
            "LocalUserProfileAuditV1",
            1,
            _profile_created,
            safe,
        ),
        AuditContract(
            "local_user_profile.display_name_updated",
            1,
            "LocalUserProfileDisplayNameAuditV1",
            1,
            _profile_updated,
            safe,
        ),
        AuditContract(
            "reference.customer_organization.created",
            1,
            "CustomerOrganizationAuditV1",
            1,
            _customer_created,
            safe,
        ),
        AuditContract(
            "reference.customer_organization.descriptive_updated",
            1,
            "ReferenceDescriptiveAuditV1",
            1,
            _customer_descriptive_updated,
            safe,
        ),
        AuditContract(
            "reference.customer_account_code.set",
            1,
            "CustomerAccountCodeAuditV1",
            1,
            _account_code_set,
            safe,
        ),
        AuditContract(
            "reference.customer_account_code.shared_claim_confirmed",
            1,
            "CustomerAccountCodeReviewAuditV1",
            1,
            _review_validator("CONFIRM_SHARED_CLAIM"),
            safe,
        ),
        AuditContract(
            "reference.customer_account_code.reassigned",
            1,
            "CustomerAccountCodeReviewAuditV1",
            1,
            _review_validator("REASSIGN_CLAIM"),
            safe,
        ),
    )


def reference_audit_writer() -> AuditWriter:
    return AuditWriter(reference_audit_contracts())


def _contact_created(value):
    value = _dict(
        value, {"contact_id", "new_revision", "initial_channel_id", "initial_affiliation_id"}
    )
    require_uuid4(value["contact_id"])
    _optional_uuid(value["initial_channel_id"])
    _optional_uuid(value["initial_affiliation_id"])
    if type(value["new_revision"]) is not int or value["new_revision"] != 1:
        raise ValidationError("Invalid Contact creation revision.")


def _channel_validator(action):
    def validate(value):
        keys = {
            "contact_id",
            "contact_channel_id",
            "prior_channel_revision",
            "new_channel_revision",
            "prior_contact_revision",
            "new_contact_revision",
        }
        value = _dict(
            value,
            keys
            | ({"reason_category"} if action == "ARCHIVE" else {"channel_kind", "change_kind"}),
        )
        require_uuid4(value["contact_id"])
        require_uuid4(value["contact_channel_id"])
        prior_contact = _revision(value["prior_contact_revision"])
        if _revision(value["new_contact_revision"]) != prior_contact + 1:
            raise ValidationError("Invalid Contact channel owner revision.")
        prior = value["prior_channel_revision"]
        new = _revision(value["new_channel_revision"])
        if action == "ADD":
            if prior is not None or new != 1:
                raise ValidationError("Invalid channel creation revision.")
        elif new != _revision(prior) + 1:
            raise ValidationError("Invalid channel revision transition.")
        if action == "ARCHIVE":
            _reason(value["reason_category"])
            if value["reason_category"] is None:
                raise ValidationError("Missing channel archive reason.")
        elif value["channel_kind"] != "email" or value["change_kind"] != action:
            raise ValidationError("Invalid channel classification.")

    return validate


def _affiliation_changed(value):
    value = _dict(
        value,
        {
            "contact_id",
            "prior_affiliation_id",
            "new_affiliation_id",
            "prior_customer_org_id",
            "new_customer_org_id",
            "prior_contact_revision",
            "new_contact_revision",
            "reason_category",
        },
    )
    require_uuid4(value["contact_id"])
    for key in (
        "prior_affiliation_id",
        "new_affiliation_id",
        "prior_customer_org_id",
        "new_customer_org_id",
    ):
        _optional_uuid(value[key])
    for prefix in ("prior", "new"):
        if (value[prefix + "_affiliation_id"] is None) != (
            value[prefix + "_customer_org_id"] is None
        ):
            raise ValidationError("Invalid affiliation relationship evidence.")
    if value["prior_customer_org_id"] == value["new_customer_org_id"]:
        raise ValidationError("Unchanged affiliation cannot append audit.")
    if _revision(value["new_contact_revision"]) != _revision(value["prior_contact_revision"]) + 1:
        raise ValidationError("Invalid affiliation revision transition.")
    _reason(value["reason_category"])
    if value["reason_category"] is None:
        raise ValidationError("Missing affiliation reason.")


def _dispatch_created(value):
    value = _dict(
        value, {"dispatch_location_id", "address_mode", "new_revision", "lifecycle_event_id"}
    )
    require_uuid4(value["dispatch_location_id"])
    require_uuid4(value["lifecycle_event_id"])
    if (
        value["address_mode"] not in {"standalone", "site_derived"}
        or type(value["new_revision"]) is not int
        or value["new_revision"] != 1
    ):
        raise ValidationError("Invalid Dispatch creation evidence.")


def _dispatch_updated(value):
    value = _dict(
        value,
        {
            "target_type",
            "target_id",
            "prior_revision",
            "new_revision",
            "changed_fields",
            "lifecycle_event_id",
        },
    )
    require_uuid4(value["target_id"])
    require_uuid4(value["lifecycle_event_id"])
    if (
        value["target_type"] != "dispatch_location"
        or _revision(value["new_revision"]) != _revision(value["prior_revision"]) + 1
    ):
        raise ValidationError("Invalid Dispatch descriptive evidence.")
    if value["changed_fields"] not in (
        ["name"],
        ["standalone_address_text"],
        ["name", "standalone_address_text"],
    ):
        raise ValidationError("Invalid Dispatch changed fields.")


def _lifecycle_validator(new_state):
    def validate(value):
        value = _dict(
            value,
            {
                "target_type",
                "target_id",
                "prior_state",
                "new_state",
                "prior_revision",
                "new_revision",
                "lifecycle_event_id",
                "reason_category",
            },
        )
        require_uuid4(value["target_id"])
        require_uuid4(value["lifecycle_event_id"])
        if (
            value["target_type"] not in {"customer_organization", "contact", "dispatch_location"}
            or value["new_state"] != new_state
            or value["prior_state"] != ("active" if new_state == "archived" else "archived")
        ):
            raise ValidationError("Invalid lifecycle state evidence.")
        if _revision(value["new_revision"]) != _revision(value["prior_revision"]) + 1:
            raise ValidationError("Invalid lifecycle revision evidence.")
        from soma.modules.reference.domain.validation import validate_reason_category

        if validate_reason_category(value["reason_category"]) is None:
            raise ValidationError("Lifecycle reason is required.")

    return validate
