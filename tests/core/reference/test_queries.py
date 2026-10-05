"""Current snapshot/cursor rewrites of pinned Reference query/provider regressions."""

import pytest
from soma.foundation.errors import SomaError
from soma.foundation.identity import new_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.transactions import UnitOfWork
from soma.modules.reference.composition import compose
from soma.modules.reference.ports.dispatch import SiteDispatchLink, DispatchCommandContext
from soma.modules.reference.domain.dispatch import validate_dispatch_name
from .test_customer import create as customer, read
from .test_contact import create as contact
from .test_settings import definition


def test_customer_matching_union_ambiguity_signed_pages_and_no_writes(reference):
    ref, factory, _ = reference
    first = customer(ref.customers, "One", "CODE")
    other = customer(ref.customers, "Other")
    before = read(factory, "SELECT * FROM command_receipts")
    with ReadSnapshot(factory) as snapshot:
        assert ref.queries.match_customer_organization(
            snapshot, dict(raw_name="One")
        ).state == "UNIQUE_CANDIDATE"
        match = ref.queries.match_customer_organization(
            snapshot, dict(raw_account_code="code", raw_name="Other", limit=1)
        )
        assert (
            match.state == "AMBIGUOUS"
            and match.candidate_count == 2
            and match.explanation == "ACCOUNT_CODE_NAME_CONFLICT"
        )
        assert len(match.candidate_ids) == 1 and match.continuation
        second = ref.queries.match_customer_organization(
            snapshot,
            dict(raw_account_code="CODE", raw_name="other", limit=1, after=match.continuation),
        )
        assert second.state == "AMBIGUOUS" and set(match.candidate_ids + second.candidate_ids) == {
            first,
            other,
        }
        with pytest.raises(SomaError):
            ref.queries.match_customer_organization(
                snapshot, dict(raw_name="other", after=match.continuation)
            )
        assert (
            ref.queries.match_customer_organization(snapshot, dict(raw_name="unknown")).state
            == "UNRESOLVED"
        )
    assert read(factory, "SELECT * FROM command_receipts") == before
    customer(ref.customers, "One")
    with ReadSnapshot(factory) as snapshot:
        assert (
            ref.queries.match_customer_organization(snapshot, dict(raw_name="One")).state
            == "AMBIGUOUS"
        )


def test_contact_matching_is_scoped_union_deduplicated_and_injection_rejected(reference):
    ref, factory, _ = reference
    org = customer(ref.customers)
    other_org = customer(ref.customers, "Other")
    first = contact(ref, initial_email="same@example.com", initial_customer_org_id=org)
    contact(ref, initial_email="same@example.com", initial_customer_org_id=other_org)
    unbound = contact(ref, initial_email="same@example.com")
    with ReadSnapshot(factory) as snapshot:
        match = ref.queries.match_contact(
            snapshot, dict(scope=org, raw_name="Private Contact", raw_email="SAME@example.com")
        )
        assert match.candidate_count == 1 and match.candidate_ids == (first,)
        assert ref.queries.match_contact(
            snapshot, dict(scope="UNBOUND", raw_email="same@example.com")
        ).candidate_ids == (unbound,)
        for scope in (None, "contacts; DROP TABLE contacts", "all"):
            with pytest.raises(SomaError):
                ref.queries.match_contact(snapshot, dict(scope=scope, raw_email="same@example.com"))
    contact(ref, initial_email="same@example.com", initial_customer_org_id=org)
    with ReadSnapshot(factory) as snapshot:
        match = ref.queries.match_contact(
            snapshot, dict(scope=org, raw_email="same@example.com", limit=1)
        )
        assert match.state == "AMBIGUOUS" and match.candidate_count == 2 and match.continuation


def test_active_keysets_archived_detail_and_scopes(reference):
    ref, factory, _ = reference
    ids = [customer(ref.customers, name) for name in ("Zulu", "Alpha", "Alpha")]
    with ReadSnapshot(factory) as snapshot:
        first = ref.queries.active(snapshot, "customer_organization", limit=1, count_exact=True)
        assert first.exact_count == 3 and first.items[0]["name"] == "Alpha"
        second = ref.queries.active(
            snapshot, "customer_organization", limit=2, after=first.continuation
        )
        assert len(second.items) == 2 and not second.continuation
        assert {row["reference_id"] for row in first.items + second.items} == set(ids)
        for kind in ("contact", "dispatch_location", "contacts; DELETE"):
            with pytest.raises(SomaError):
                ref.queries.active(snapshot, kind, after=first.continuation)
        assert ref.queries.resolve_scope(snapshot, dict(kind="all")).kind == "all"
        assert ref.queries.resolve_scope(snapshot, dict(kind="unassigned")).customer_org_id is None
        with pytest.raises(SomaError):
            ref.queries.resolve_scope(snapshot, dict(kind="specific", customer_org_id=new_uuid4()))
    ref.lifecycle.archive_reference(
        command_id=new_uuid4(),
        target_type="customer_organization",
        target_id=ids[0],
        base_revision=1,
        reason_category="operator_archive",
    )
    with ReadSnapshot(factory) as snapshot:
        assert (
            ref.queries.detail(snapshot, "customer_organization", ids[0])["lifecycle_state"]
            == "archived"
        )
        assert (
            ref.queries.resolve_scope(
                snapshot, dict(kind="specific", customer_org_id=ids[0])
            ).lifecycle_state
            == "archived"
        )
        assert len(ref.queries.active(snapshot, "customer_organization").items) == 2


def test_history_pages_preserve_codes_affiliations_and_channels(reference):
    ref, factory, _ = reference
    org = customer(ref.customers, "Customer", "ONE")
    other = customer(ref.customers, "Other")
    ref.customers.set_customer_account_code(
        command_id=new_uuid4(), customer_org_id=org, base_revision=1, account_code="TWO"
    )
    identity = contact(ref, initial_email="one@example.com", initial_customer_org_id=org)
    ref.contacts.add_contact_channel(
        command_id=new_uuid4(),
        contact_id=identity,
        contact_base_revision=1,
        channel_kind="email",
        value_text="two@example.com",
    )
    ref.contacts.change_contact_affiliation(
        command_id=new_uuid4(),
        contact_id=identity,
        base_revision=2,
        new_customer_org_id=other,
        reason_category="role_changed",
    )
    with ReadSnapshot(factory) as snapshot:
        for kind, target in (
            ("account_code", org),
            ("affiliation", identity),
            ("channels", identity),
        ):
            first = ref.queries.history(snapshot, kind, target, limit=1, count_exact=True)
            second = ref.queries.history(
                snapshot, kind, target, limit=1, after=first.continuation, count_exact=True
            )
            assert (
                first.exact_count == second.exact_count == 2
                and len(second.items) == 1
                and not second.continuation
            )
        detail = ref.queries.detail(snapshot, "contact", identity)
        assert (
            "channels" not in detail and detail["current_affiliation"]["customer_org_id"] == other
        )
        page = ref.queries.channel_use(snapshot, identity, "AUTO", "msg_recipient", limit=1)
        assert (
            page["state"] == "MULTIPLE_USABLE"
            and page["usable_count"] == 2
            and page["continuation"]
        )
        rest = ref.queries.channel_use(
            snapshot, identity, "AUTO", "msg_recipient", limit=1, after=page["continuation"]
        )
        assert len(rest["candidate_channel_ids"]) == 1 and not rest["continuation"]
        with pytest.raises(SomaError):
            ref.queries.channel_use(snapshot, identity, "AUTO", "other", after=page["continuation"])


def test_review_provider_uses_caller_snapshot_and_writer_revalidates(reference):
    ref, factory, _ = reference
    source = customer(ref.customers, "Source", "CODE")
    target = customer(ref.customers, "Target")
    args = dict(
        raw_account_code="CODE",
        proposed_action="CONFIRM_SHARED_CLAIM",
        target_customer_org_id=target,
    )
    with ReadSnapshot(factory) as snapshot:
        preview = ref.queries.preview_customer_account_code_conflict(snapshot, args)
        assert preview["claimant_count"] == 1
    with UnitOfWork(factory) as uow:
        assert (
            ref.queries.validate_customer_account_code_review(
                uow, args, preview["review_snapshot_hash"]
            )["target_revision"]
            == 1
        )
    ref.customers.update_descriptive_data(
        command_id=new_uuid4(), customer_org_id=source, base_revision=1, name="Renamed"
    )
    with pytest.raises(SomaError):
        with UnitOfWork(factory) as uow:
            ref.queries.validate_customer_account_code_review(
                uow, args, preview["review_snapshot_hash"]
            )


def test_site_address_future_provider_no_private_coupling(reference):
    ref, factory, _ = reference
    with UnitOfWork(factory) as uow:
        command = new_uuid4()
        uow.connection.execute(
            "INSERT INTO command_receipts VALUES (?,'site.probe',?,NULL,0)", (command, "0" * 64)
        )
        identity = ref.dispatch.create_dedicated_for_site(
            uow,
            parent_command_id=command,
            name="Site",
            precomputed_name_match_key=validate_dispatch_name("Site")[1],
            command_context=DispatchCommandContext(),
        )

    class Provider:
        def site_link_for(self, snapshot, target):
            assert target == identity and snapshot.connection.in_transaction
            return SiteDispatchLink(site_id=new_uuid4())

        def current_site_address(self, snapshot, site):
            assert snapshot.connection.in_transaction
            return "Derived address"

    with ReadSnapshot(factory) as snapshot:
        assert (
            ref.queries.detail(snapshot, "dispatch_location", identity)["current_address"]["state"]
            == "UNAVAILABLE"
        )
        queries = compose(factory, site_address_provider=Provider()).queries
        assert (
            queries.detail(snapshot, "dispatch_location", identity)["current_address"][
                "address_text"
            ]
            == "Derived address"
        )


def test_query_cost_constant_bounded_and_indexed_large_candidates(reference, monkeypatch):
    ref, factory, _ = reference
    connection = factory.open()
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.executemany(
            "INSERT INTO customer_organizations VALUES (?,'Same','same','active',1,0,0)",
            ((new_uuid4(),) for _ in range(3000)),
        )
        connection.execute("COMMIT")
        plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT customer_org_id FROM customer_organizations WHERE lifecycle_state='active' AND name_match_key='same'"
        ).fetchall()
        assert any(
            "idx_customer_org_active_name_match" in row[3] and "SEARCH" in row[3] for row in plan
        )
    finally:
        connection.close()
    for limit in (1, 50, 200):
        with ReadSnapshot(factory) as snapshot:
            trace = []
            snapshot.connection.set_trace_callback(trace.append)
            page = ref.queries.match_customer_organization(
                snapshot, dict(raw_name="Same", limit=limit)
            )
            assert page.candidate_count == 3000 and len(page.candidate_ids) == limit
            assert len(trace) == 3
            trace.clear()
            ref.queries.active(snapshot, "customer_organization", limit=limit)
            assert len(trace) == 1
    with ReadSnapshot(factory) as snapshot:
        with pytest.raises(SomaError):
            ref.queries.active(snapshot, "customer_organization", limit=201)
    before = read(factory, "SELECT * FROM setting_values")
    settings = compose(factory, setting_definitions=(definition(),)).settings
    with ReadSnapshot(factory) as snapshot:
        trace = []
        snapshot.connection.set_trace_callback(trace.append)
        assert len(settings.list_for_owner(snapshot, "synthetic")) == 1 and len(trace) == 1
    assert read(factory, "SELECT * FROM setting_values") == before
