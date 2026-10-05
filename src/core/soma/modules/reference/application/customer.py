"""Customer mutations and exact reviewed Account Code ownership changes."""

from soma.foundation.errors import SomaError
from soma.foundation.identity import new_uuid4, require_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.time import utc_epoch_seconds
from soma.foundation.transactions import CommandBoundary
from soma.modules.reference.adapters.persistence import customer as store
from soma.modules.reference.adapters.persistence.matching_profile import (
    require_persisted_matching_profile,
)
from soma.modules.reference.domain.account_code import require_fresh_review, review_fingerprint
from soma.modules.reference.domain.validation import (
    validate_account_code,
    validate_customer_name,
    validate_reason_category,
    validate_review_context_id,
)
from .commands import RESULT, event, result, revision


class Customers:
    def __init__(self, factory, audit_writer):
        self.factory = factory
        self.boundary = CommandBoundary(factory, [RESULT], audit_writer)

    def _execute(self, command, action, request, preflight, prepare):
        return self.boundary.execute(
            command,
            action,
            request,
            (RESULT.schema, RESULT.version),
            None,
            preflight=preflight,
            prepare=prepare,
        )

    def create_customer_organization(self, *, command_id, name, account_code=None, actor_id=None):
        data = {}

        def preflight():
            data["name"], data["name_key"] = validate_customer_name(name)
            data["code"] = None if account_code is None else validate_account_code(account_code)
            if actor_id is not None:
                require_uuid4(actor_id)

        def prepare(uow):
            require_persisted_matching_profile(uow.connection)
            code = data["code"]
            if code and store.claimant_count(uow.connection, code[1]):
                raise SomaError(
                    "ACCOUNT_CODE_CONFLICT_REVIEW",
                    "Account Code requires conflict review.",
                    "refresh",
                )
            identity, lifecycle = new_uuid4(), new_uuid4()
            claim = new_uuid4() if code else None
            now = utc_epoch_seconds()
            audit = event(
                "reference.customer_organization.created",
                command_id,
                identity,
                {
                    "customer_org_id": identity,
                    "new_revision": 1,
                    "account_code_claim_created": claim is not None,
                    "reason_category": None,
                },
                actor_id,
                results=(
                    ("customer_organization", identity),
                    ("reference_lifecycle_event", lifecycle),
                ),
            )

            def apply(inner):
                store.insert_customer(
                    inner.connection, identity, data["name"], data["name_key"], now
                )
                if claim:
                    store.insert_claim(inner.connection, claim, identity, *code, now, command_id)
                store.lifecycle_event(
                    inner.connection, lifecycle, identity, "created", now, command_id
                )
                return result(identity, 1), [audit]

            return apply

        return self._execute(
            command_id,
            "reference.create_customer",
            dict(name=name, account_code=account_code, actor_id=actor_id),
            preflight,
            prepare,
        )

    def update_descriptive_data(
        self, *, command_id, customer_org_id, base_revision, name, actor_id=None
    ):
        data = {}

        def preflight():
            require_uuid4(customer_org_id)
            revision(base_revision)
            if actor_id is not None:
                require_uuid4(actor_id)
            data["name"], data["key"] = validate_customer_name(name)

        def prepare(uow):
            require_persisted_matching_profile(uow.connection)
            row = store.active_customer(uow.connection, customer_org_id, base_revision)
            if (row[1], row[2]) == (data["name"], data["key"]):
                return lambda inner: (result(customer_org_id, base_revision, False), [], False)
            lifecycle, now = new_uuid4(), utc_epoch_seconds()
            audit = event(
                "reference.customer_organization.descriptive_updated",
                command_id,
                customer_org_id,
                {
                    "target_type": "customer_organization",
                    "target_id": customer_org_id,
                    "prior_revision": base_revision,
                    "new_revision": base_revision + 1,
                    "changed_fields": ["name"],
                    "lifecycle_event_id": lifecycle,
                },
                actor_id,
                results=(("reference_lifecycle_event", lifecycle),),
            )

            def apply(inner):
                store.update_name(inner.connection, customer_org_id, data["name"], data["key"], now)
                store.lifecycle_event(
                    inner.connection,
                    lifecycle,
                    customer_org_id,
                    "descriptive_corrected",
                    now,
                    command_id,
                )
                return result(customer_org_id, base_revision + 1), [audit]

            return apply

        return self._execute(
            command_id,
            "reference.update_customer",
            dict(
                customer_org_id=customer_org_id,
                base_revision=base_revision,
                name=name,
                actor_id=actor_id,
            ),
            preflight,
            prepare,
        )

    def set_customer_account_code(
        self,
        *,
        command_id,
        customer_org_id,
        base_revision,
        account_code,
        reason_category=None,
        actor_id=None,
    ):
        return self._change_code(
            command_id=command_id,
            customer_org_id=customer_org_id,
            base_revision=base_revision,
            account_code=account_code,
            reason_category=reason_category,
            actor_id=actor_id,
        )

    def confirm_customer_account_code_shared_claim(
        self,
        *,
        command_id,
        customer_org_id,
        base_revision,
        account_code,
        review_snapshot_hash,
        reason_category,
        review_context_id=None,
        actor_id=None,
    ):
        return self._change_code(
            command_id=command_id,
            customer_org_id=customer_org_id,
            base_revision=base_revision,
            account_code=account_code,
            reason_category=reason_category,
            actor_id=actor_id,
            action="CONFIRM_SHARED_CLAIM",
            review_snapshot_hash=review_snapshot_hash,
            review_context_id=review_context_id,
        )

    def reassign_customer_account_code(
        self,
        *,
        command_id,
        from_customer_org_id,
        from_base_revision,
        to_customer_org_id,
        to_base_revision,
        account_code,
        review_snapshot_hash,
        reason_category,
        review_context_id=None,
        actor_id=None,
    ):
        return self._change_code(
            command_id=command_id,
            customer_org_id=to_customer_org_id,
            base_revision=to_base_revision,
            account_code=account_code,
            reason_category=reason_category,
            actor_id=actor_id,
            action="REASSIGN_CLAIM",
            review_snapshot_hash=review_snapshot_hash,
            review_context_id=review_context_id,
            source_id=from_customer_org_id,
            source_revision=from_base_revision,
        )

    def preview_account_code_review(
        self,
        *,
        raw_account_code,
        proposed_action,
        target_customer_org_id,
        from_customer_org_id=None,
    ):
        _, key = validate_account_code(raw_account_code)
        require_uuid4(target_customer_org_id)
        if from_customer_org_id is not None:
            require_uuid4(from_customer_org_id)
        with ReadSnapshot(self.factory) as snapshot:
            context = store.review_context(
                snapshot.connection,
                key,
                proposed_action,
                target_customer_org_id,
                from_customer_org_id,
            )
            return {
                "review_snapshot_hash": review_fingerprint(context),
                "claimant_count": context.claimant_count,
                "target_revision": context.target.revision,
                "source_revision": None if context.source is None else context.source.revision,
            }

    def _change_code(
        self,
        *,
        command_id,
        customer_org_id,
        base_revision,
        account_code,
        reason_category,
        actor_id,
        action=None,
        review_snapshot_hash=None,
        review_context_id=None,
        source_id=None,
        source_revision=None,
    ):
        request = dict(
            customer_org_id=customer_org_id,
            base_revision=base_revision,
            account_code=account_code,
            reason_category=reason_category,
            actor_id=actor_id,
            action=action,
            review_snapshot_hash=review_snapshot_hash,
            review_context_id=review_context_id,
            source_id=source_id,
            source_revision=source_revision,
        )
        data = {}

        def preflight():
            require_uuid4(customer_org_id)
            revision(base_revision)
            if actor_id is not None:
                require_uuid4(actor_id)
            data["code"] = validate_account_code(account_code)
            data["reason"] = validate_reason_category(reason_category)
            validate_review_context_id(review_context_id)
            if action and data["reason"] is None:
                raise SomaError(
                    "MATCH_INPUT_INVALID",
                    "Reviewed assignment requires a reason category.",
                    "correct_input",
                )
            if source_id is not None:
                require_uuid4(source_id)
                revision(source_revision)

        def prepare(uow):
            connection = uow.connection
            require_persisted_matching_profile(connection)
            value, key = data["code"]
            if action:
                context = store.review_context(connection, key, action, customer_org_id, source_id)
                require_fresh_review(context, review_snapshot_hash)
            store.active_customer(connection, customer_org_id, base_revision)
            current = store.current_claim(connection, customer_org_id)
            same = current is not None and current[2] == key
            source = None
            if source_id is not None:
                store.active_customer(connection, source_id, source_revision)
                source = store.current_claim(connection, source_id)
                if source is None or source[2] != key:
                    raise SomaError(
                        "ACCOUNT_CODE_SOURCE_NOT_OWNER",
                        "Source no longer owns the Account Code.",
                        "refresh",
                    )
            if source is None and same:
                return lambda inner: (result(customer_org_id, base_revision, False), [], False)
            if action is None and store.claimant_count(connection, key, customer_org_id):
                raise SomaError(
                    "ACCOUNT_CODE_CONFLICT_REVIEW",
                    "Account Code requires conflict review.",
                    "refresh",
                )
            new_claim = None if same else new_uuid4()
            changed_claims = (
                ([source[0]] if source else [])
                + ([current[0]] if current and not same else [])
                + ([new_claim] if new_claim else [])
            )
            changed_customers = ([source_id] if source else []) + (
                [] if same else [customer_org_id]
            )
            now = utc_epoch_seconds()
            if action:
                payload = dict(
                    proposed_action=action,
                    review_snapshot_hash=review_snapshot_hash.lower(),
                    review_context_id=review_context_id,
                    from_customer_org_id=source_id,
                    to_customer_org_id=customer_org_id,
                    changed_identifier_ids=changed_claims,
                    changed_customer_org_ids=changed_customers,
                    reason_category=data["reason"],
                )
                audit_action = "reference.customer_account_code." + (
                    "reassigned" if source else "shared_claim_confirmed"
                )
            else:
                payload = dict(
                    customer_org_id=customer_org_id,
                    customer_org_identifier_id=new_claim,
                    superseded_identifier_id=None if current is None else current[0],
                    prior_revision=base_revision,
                    new_revision=base_revision + 1,
                    change_kind="SET" if current is None else "REPLACE",
                    reason_category=data["reason"],
                )
                audit_action = "reference.customer_account_code.set"
            audit = event(
                audit_action,
                command_id,
                customer_org_id,
                payload,
                actor_id,
                results=tuple(("customer_org_identifier", identity) for identity in changed_claims),
            )

            def apply(inner):
                if source:
                    store.supersede_claim(inner.connection, source[0], now, command_id)
                    store.bump_revision(inner.connection, source_id, now)
                if not same:
                    if current:
                        store.supersede_claim(inner.connection, current[0], now, command_id)
                    store.insert_claim(
                        inner.connection, new_claim, customer_org_id, value, key, now, command_id
                    )
                    store.bump_revision(inner.connection, customer_org_id, now)
                return result(customer_org_id, base_revision if same else base_revision + 1), [
                    audit
                ]

            return apply

        return self._execute(
            command_id, "reference.account_code." + (action or "SET"), request, preflight, prepare
        )
