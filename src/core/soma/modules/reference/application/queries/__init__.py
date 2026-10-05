"""Snapshot providers and signed Foundation paging over Reference-owned reads."""

from dataclasses import dataclass

from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import require_uuid4
from soma.foundation.query import CursorCodec
from soma.modules.reference.adapters.persistence import reference_reader as store
from soma.modules.reference.adapters.persistence.customer import (
    active_customer,
    current_claim,
    review_context,
)
from soma.modules.reference.adapters.persistence.matching_profile import (
    require_persisted_matching_profile,
)
from soma.modules.reference.domain.account_code import review_fingerprint, require_fresh_review
from soma.modules.reference.domain.validation import validate_account_code, validate_customer_name
from soma.modules.reference.domain.contact import validate_contact_name
from soma.modules.reference.domain.channels import validate_email
from soma.modules.reference.domain.dispatch import validate_standalone_address
from soma.modules.reference.ports.matching import CandidateResult
from soma.modules.reference.ports.customer_scope import CustomerScopeResolution


@dataclass(frozen=True)
class ReferencePage:
    items: tuple[dict, ...]
    continuation: str | None
    exact_count: int | None
    as_of_utc_s: int


def closed(value, allowed, required=()):
    if type(value) is not dict or set(value) - set(allowed) or set(required) - set(value):
        raise ValidationError("Invalid Reference query fields.")


class ReferenceQueries:
    def __init__(self, cursor_codec=None, site_address_provider=None):
        self.cursor = cursor_codec or CursorCodec()
        self.site_addresses = site_address_provider

    def _position(self, snapshot, contract, filters, order, after, initial):
        if after is None:
            return initial, snapshot.as_of_utc_s
        position, as_of = self.cursor.decode(after, contract, filters, order)
        if type(initial) is list:
            if (
                type(position) is not list
                or len(position) != 2
                or type(position[0]) is not type(initial[0])
                or type(position[1]) is not str
            ):
                raise ValidationError("Invalid Reference cursor position.")
            if position[1]:
                require_uuid4(position[1])
        elif type(position) is not str:
            raise ValidationError("Invalid candidate cursor position.")
        elif position:
            require_uuid4(position)
        return position, as_of

    def active(self, snapshot, kind, *, after=None, limit=50, count_exact=False):
        store.master(kind)
        limit = self.cursor.limit(limit)
        if type(count_exact) is not bool:
            raise ValidationError("Invalid count option.")
        filters, order = dict(kind=kind), ["name_match_key", "reference_id"]
        position, as_of = self._position(
            snapshot, "ReferenceActiveV1", filters, order, after, ["", ""]
        )
        rows = store.active_page(snapshot.connection, kind, position, limit)
        token = (
            None
            if len(rows) <= limit
            else self.cursor.encode(
                "ReferenceActiveV1",
                filters,
                order,
                [rows[limit - 1]["name_match_key"], rows[limit - 1]["reference_id"]],
                as_of,
            )
        )
        count = store.active_count(snapshot.connection, kind) if count_exact else None
        return ReferencePage(tuple(rows[:limit]), token, count, as_of)

    def identities(self, snapshot, reference_type, ids):
        store.master(reference_type)
        if type(ids) is not list or len(ids) > 200:
            raise ValidationError("Invalid bounded identity lookup.")
        for identity in ids:
            require_uuid4(identity)
        if len(set(ids)) != len(ids):
            raise ValidationError("Identity lookup cannot repeat an identity.")
        return dict(items=store.identities(snapshot.connection, reference_type, ids))

    def detail(self, snapshot, kind, identity):
        require_uuid4(identity)
        result = store.detail(snapshot.connection, kind, identity)
        result["reference_type"] = kind
        if kind == "customer_organization":
            claim = current_claim(snapshot.connection, identity)
            result["current_account_code"] = (
                None
                if claim is None
                else dict(zip(("customer_org_identifier_id", "value_text", "match_key"), claim))
            )
        elif kind == "contact":
            row = snapshot.connection.execute(
                "SELECT contact_affiliation_id,customer_org_id FROM contact_affiliations WHERE contact_id=? AND is_current=1",
                (identity,),
            ).fetchone()
            result["current_affiliation"] = (
                None
                if row is None
                else dict(zip(("contact_affiliation_id", "customer_org_id"), row))
            )
        else:
            result["current_address"] = self._address(snapshot, identity, result)
        return result

    def _address(self, snapshot, identity, row):
        if row["address_mode"] == "standalone":
            return dict(
                source="STANDALONE",
                state="AVAILABLE",
                address_text=row["standalone_address_text"],
                site_id=None,
            )
        unavailable = dict(source="SITE", state="UNAVAILABLE", address_text=None, site_id=None)
        if self.site_addresses is None:
            return unavailable
        try:
            link = self.site_addresses.site_link_for(snapshot, identity)
            if link is None:
                return unavailable
            require_uuid4(link.site_id)
            address = validate_standalone_address(
                self.site_addresses.current_site_address(snapshot, link.site_id)
            )
            return dict(
                source="SITE", state="AVAILABLE", address_text=address, site_id=link.site_id
            )
        except Exception:
            return unavailable

    def history(
        self,
        snapshot,
        kind,
        identity,
        *,
        after=None,
        limit=50,
        count_exact=False,
        include_archived=True,
    ):
        if kind not in store.HISTORY:
            raise ValidationError("Invalid history query.")
        require_uuid4(identity)
        if type(count_exact) is not bool or type(include_archived) is not bool:
            raise ValidationError("Invalid history options.")
        store.detail(
            snapshot.connection,
            "customer_organization" if kind == "account_code" else "contact",
            identity,
        )
        limit = self.cursor.limit(limit)
        filters = dict(kind=kind, identity=identity, include_archived=include_archived)
        _, _, chronology, key, _ = store.HISTORY[kind]
        order = [chronology, key]
        position, as_of = self._position(
            snapshot, "ReferenceHistoryV1", filters, order, after, [-1, ""]
        )
        rows = store.history(snapshot.connection, kind, identity, position, limit, include_archived)
        token = (
            None
            if len(rows) <= limit
            else self.cursor.encode(
                "ReferenceHistoryV1",
                filters,
                order,
                [rows[limit - 1][chronology], rows[limit - 1][key]],
                as_of,
            )
        )
        count = (
            store.history_count(snapshot.connection, kind, identity, include_archived)
            if count_exact
            else None
        )
        return ReferencePage(tuple(rows[:limit]), token, count, as_of)

    def resolve_scope(self, snapshot, input):
        closed(input, ("kind", "customer_org_id"), ("kind",))
        kind = input["kind"]
        if kind in ("all", "unassigned") and set(input) == {"kind"}:
            return CustomerScopeResolution(kind, None, None, None)
        if kind != "specific" or set(input) != {"kind", "customer_org_id"}:
            raise ValidationError("Invalid Customer scope.")
        require_uuid4(input["customer_org_id"])
        row = store.detail(snapshot.connection, "customer_organization", input["customer_org_id"])
        return CustomerScopeResolution(
            kind, row["reference_id"], row["name"], row["lifecycle_state"]
        )

    def _match(self, snapshot, kind, input):
        fields = (
            ("raw_name", "raw_account_code", "limit", "after")
            if kind == "customer_organization"
            else ("scope", "raw_name", "raw_email", "limit", "after")
        )
        closed(input, fields)
        name, secondary = (
            input.get("raw_name"),
            input.get("raw_account_code" if kind == "customer_organization" else "raw_email"),
        )
        if name is None and secondary is None:
            raise SomaError(
                "MATCH_INPUT_INVALID", "At least one match value is required.", "correct_input"
            )
        require_persisted_matching_profile(snapshot.connection)
        scope = "ALL" if kind == "customer_organization" else input.get("scope")
        if kind == "contact" and scope != "UNBOUND":
            require_uuid4(scope)
            active_customer(snapshot.connection, scope)
        keys = dict(
            name=None
            if name is None
            else (
                validate_customer_name(name)
                if kind == "customer_organization"
                else validate_contact_name(name)
            )[1]
        )
        keys["account_code" if kind == "customer_organization" else "email"] = (
            None
            if secondary is None
            else (
                validate_account_code(secondary)
                if kind == "customer_organization"
                else validate_email(secondary)
            )[1]
        )
        limit = self.cursor.limit(input.get("limit", 50))
        filters, order = dict(kind=kind, keys=keys, scope=scope), ["candidate_id"]
        position, as_of = self._position(
            snapshot, "ReferenceCandidatesV1", filters, order, input.get("after"), ""
        )
        total, code_count, rows = store.match(
            snapshot.connection, kind, keys, scope, position, limit
        )
        token = (
            None
            if len(rows) <= limit
            else self.cursor.encode("ReferenceCandidatesV1", filters, order, rows[limit - 1], as_of)
        )
        state = "UNRESOLVED" if total == 0 else "UNIQUE_CANDIDATE" if total == 1 else "AMBIGUOUS"
        if total == 0:
            explanation = "NO_CANONICAL_CANDIDATE"
        elif code_count > 1:
            explanation = "ACCOUNT_CODE_MULTIPLE_CLAIMS"
        elif code_count == 1:
            explanation = "ACCOUNT_CODE_NAME_CONFLICT" if total > 1 else "ACCOUNT_CODE_MATCH"
        elif kind == "customer_organization" and secondary is not None:
            explanation = (
                "ACCOUNT_CODE_UNRESOLVED_NAME_CANDIDATE"
                if total == 1
                else "ACCOUNT_CODE_UNRESOLVED_NAME_AMBIGUOUS"
            )
        else:
            explanation = "NAME_EMAIL_MATCH" if kind == "contact" else "NAME_MATCH"
        return CandidateResult(
            state, explanation, total, rows[:limit], token, "UNICODE_MATCH_V1", keys, scope
        )

    def match_customer_organization(self, snapshot, input):
        return self._match(snapshot, "customer_organization", input)

    def match_contact(self, snapshot, input):
        return self._match(snapshot, "contact", input)

    def _review(self, reader, input):
        closed(
            input,
            (
                "raw_account_code",
                "proposed_action",
                "target_customer_org_id",
                "from_customer_org_id",
            ),
            ("raw_account_code", "proposed_action", "target_customer_org_id"),
        )
        _, key = validate_account_code(input["raw_account_code"])
        require_uuid4(input["target_customer_org_id"])
        source = input.get("from_customer_org_id")
        if source is not None:
            require_uuid4(source)
        if input["proposed_action"] not in ("CONFIRM_SHARED_CLAIM", "REASSIGN_CLAIM"):
            raise ValidationError("Invalid Account Code review action.")
        context = review_context(
            reader.connection,
            key,
            input["proposed_action"],
            input["target_customer_org_id"],
            source,
        )
        return context

    def preview_customer_account_code_conflict(self, snapshot, input):
        context = self._review(snapshot, input)
        return dict(
            review_snapshot_hash=review_fingerprint(context),
            claimant_count=context.claimant_count,
            target_revision=context.target.revision,
            source_revision=None if context.source is None else context.source.revision,
        )

    def validate_customer_account_code_review(self, uow, input, review_snapshot_hash):
        context = self._review(uow, input)
        require_fresh_review(context, review_snapshot_hash)
        return dict(
            target_revision=context.target.revision,
            source_revision=None if context.source is None else context.source.revision,
            claimant_count=context.claimant_count,
        )

    def channel_use(self, snapshot, contact_id, channel_or_auto, purpose, *, limit=50, after=None):
        from dataclasses import asdict
        from soma.modules.reference.adapters.communication import Communication

        require_uuid4(contact_id)
        limit = self.cursor.limit(limit)
        filters = dict(contact_id=contact_id, channel_or_auto=channel_or_auto, purpose=purpose)
        order = ["contact_channel_id"]
        position, as_of = self._position(
            snapshot, "ReferenceChannelUseV1", filters, order, after, ""
        )
        value = Communication().validate_channel_for_use(
            snapshot,
            contact_id,
            channel_or_auto,
            purpose,
            limit=limit,
            after_channel_id=position or None,
        )
        result = asdict(value)
        next_id = result.pop("continuation_after_id")
        result["continuation"] = (
            None
            if next_id is None
            else self.cursor.encode("ReferenceChannelUseV1", filters, order, next_id, as_of)
        )
        return result
