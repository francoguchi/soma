"""Selected Beta Customer/replay/NO_CHANGE vectors on encrypted Foundation APIs."""

import pytest

from soma.foundation.errors import SomaError
from soma.foundation.identity import new_uuid4, require_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.transactions import UnitOfWork
from soma.modules.reference.adapters.persistence import customer as store


def read(factory, sql, parameters=()):
    with ReadSnapshot(factory) as snapshot:
        return snapshot.connection.execute(sql, parameters).fetchall()


def create(service, name="Customer", code=None):
    return service.create_customer_organization(
        command_id=new_uuid4(), name=name, account_code=code
    )["target_id"]


def state(factory):
    return [
        read(factory, sql)
        for sql in (
            "SELECT * FROM customer_organizations ORDER BY customer_org_id",
            "SELECT * FROM customer_org_identifiers ORDER BY customer_org_identifier_id",
            "SELECT * FROM reference_lifecycle_events ORDER BY reference_lifecycle_event_id",
            "SELECT * FROM reference_metadata",
            "SELECT * FROM audit_events ORDER BY audit_event_id",
        )
    ]


def test_equal_names_distinct_identity_creation_replay_lifecycle_and_privacy(reference):
    ref, factory, _ = reference
    command = new_uuid4()
    request = dict(command_id=command, name="Private Customer", account_code="RAW-CODE")
    first = ref.customers.create_customer_organization(**request)
    assert ref.customers.create_customer_organization(**request) == first
    other = create(ref.customers, "Private Customer")
    assert first["target_id"] != other
    require_uuid4(other)
    assert len(read(factory, "SELECT * FROM reference_lifecycle_events")) == 2
    payloads = str(read(factory, "SELECT payload_json FROM audit_events"))
    assert "Private Customer" not in payloads and "RAW-CODE" not in payloads


def test_descriptive_update_no_change_and_exact_replay_skip_owner_and_preflight(
    reference, monkeypatch
):
    ref, factory, _ = reference
    identity = create(ref.customers, "Acme", "CODE")
    before = state(factory)
    command = new_uuid4()
    request = dict(command_id=command, customer_org_id=identity, base_revision=1, name="Acme")
    no_change = ref.customers.update_descriptive_data(**request)
    assert no_change["outcome"] == "NO_CHANGE"
    assert state(factory) == before
    ref.customers.update_descriptive_data(
        command_id=new_uuid4(), customer_org_id=identity, base_revision=1, name="Later"
    )
    monkeypatch.setattr(store, "active_customer", lambda *args: pytest.fail("owner read on replay"))
    monkeypatch.setattr(
        "soma.modules.reference.application.customer.validate_customer_name",
        lambda *args: pytest.fail("preflight on replay"),
    )
    assert ref.customers.update_descriptive_data(**request) == no_change
    with pytest.raises(SomaError, match="different request"):
        ref.customers.update_descriptive_data(**(request | {"name": "Changed request"}))
    assert len(read(factory, "SELECT * FROM reference_lifecycle_events")) == 2


def test_code_replace_history_normalized_no_change_and_conflict_rollback(reference):
    ref, factory, _ = reference
    identity = create(ref.customers, code="CODE-1")
    before = state(factory)
    assert (
        ref.customers.set_customer_account_code(
            command_id=new_uuid4(),
            customer_org_id=identity,
            base_revision=1,
            account_code=" code-1 ",
        )["outcome"]
        == "NO_CHANGE"
    )
    assert state(factory) == before
    ref.customers.set_customer_account_code(
        command_id=new_uuid4(), customer_org_id=identity, base_revision=1, account_code="CODE-2"
    )
    claims = read(
        factory,
        "SELECT lifecycle_state,superseded_command_id FROM customer_org_identifiers WHERE customer_org_id=? ORDER BY lifecycle_state",
        (identity,),
    )
    assert claims[0] == ("active", None) and claims[1][0] == "superseded" and claims[1][1]
    target = create(ref.customers)
    before = state(factory)
    command = new_uuid4()
    with pytest.raises(SomaError) as exc:
        ref.customers.set_customer_account_code(
            command_id=command, customer_org_id=target, base_revision=1, account_code="code-2"
        )
    assert exc.value.code == "ACCOUNT_CODE_CONFLICT_REVIEW"
    assert state(factory) == before
    assert read(factory, "SELECT 1 FROM command_receipts WHERE command_id=?", (command,)) == []


def share(ref, identity, code, rev=1):
    preview = ref.customers.preview_account_code_review(
        raw_account_code=code,
        proposed_action="CONFIRM_SHARED_CLAIM",
        target_customer_org_id=identity,
    )
    return ref.customers.confirm_customer_account_code_shared_claim(
        command_id=new_uuid4(),
        customer_org_id=identity,
        base_revision=rev,
        account_code=code,
        review_snapshot_hash=preview["review_snapshot_hash"],
        reason_category="verified_shared",
    )


@pytest.mark.parametrize("already_shared", [False, True])
def test_reviewed_reassignment_preserves_third_party_and_exact_replay(
    reference, already_shared, monkeypatch
):
    ref, factory, _ = reference
    source = create(ref.customers, "Source", "ACC")
    third = create(ref.customers, "Third")
    share(ref, third, "ACC")
    target = create(ref.customers, "Destination", None if already_shared else "OLD")
    if already_shared:
        share(ref, target, "ACC")
    preview = ref.customers.preview_account_code_review(
        raw_account_code="ACC",
        proposed_action="REASSIGN_CLAIM",
        target_customer_org_id=target,
        from_customer_org_id=source,
    )
    assert preview["claimant_count"] == (3 if already_shared else 2)
    request = dict(
        command_id=new_uuid4(),
        from_customer_org_id=source,
        from_base_revision=1,
        to_customer_org_id=target,
        to_base_revision=2 if already_shared else 1,
        account_code="ACC",
        review_snapshot_hash=preview["review_snapshot_hash"],
        reason_category="ownership_corrected",
    )
    accepted = ref.customers.reassign_customer_account_code(**request)
    assert accepted["outcome"] == "APPLIED" and accepted["revision"] == 2
    assert {
        row[0]
        for row in read(
            factory,
            "SELECT customer_org_id FROM customer_org_identifiers WHERE match_key='acc' AND lifecycle_state='active'",
        )
    } == {third, target}
    ref.customers.update_descriptive_data(
        command_id=new_uuid4(), customer_org_id=target, base_revision=2, name="Later"
    )
    monkeypatch.setattr(
        store, "review_context", lambda *args: pytest.fail("review read during replay")
    )
    assert ref.customers.reassign_customer_account_code(**request) == accepted


def test_review_staleness_revision_and_source_guards_before_receipt(reference):
    ref, factory, _ = reference
    source = create(ref.customers, "Source", "ACC")
    target = create(ref.customers, "Target")
    preview = ref.customers.preview_account_code_review(
        raw_account_code="ACC",
        proposed_action="CONFIRM_SHARED_CLAIM",
        target_customer_org_id=target,
    )
    create(ref.customers, "Unrelated generation")
    command = new_uuid4()
    with pytest.raises(SomaError) as exc:
        ref.customers.confirm_customer_account_code_shared_claim(
            command_id=command,
            customer_org_id=target,
            base_revision=1,
            account_code="ACC",
            review_snapshot_hash=preview["review_snapshot_hash"],
            reason_category="shared",
        )
    assert exc.value.code == "REVIEW_CONTEXT_STALE"
    assert read(factory, "SELECT 1 FROM command_receipts WHERE command_id=?", (command,)) == []
    with pytest.raises(SomaError) as exc:
        ref.customers.preview_account_code_review(
            raw_account_code="OTHER",
            proposed_action="REASSIGN_CLAIM",
            target_customer_org_id=target,
            from_customer_org_id=source,
        )
    assert exc.value.code == "ACCOUNT_CODE_SOURCE_NOT_OWNER"
    with pytest.raises(SomaError) as exc:
        ref.customers.update_descriptive_data(
            command_id=new_uuid4(), customer_org_id=source, base_revision=2, name="Source"
        )
    assert exc.value.code == "STALE_REVISION"


def test_audit_failure_rolls_back_receipt_history_generation_and_master(reference, monkeypatch):
    ref, factory, _ = reference
    before = state(factory)
    command = new_uuid4()
    monkeypatch.setattr(
        ref.customers.boundary.audit,
        "append",
        lambda *args: (_ for _ in ()).throw(SomaError("AUDIT_FAILED", "Injected failure.")),
    )
    with pytest.raises(SomaError):
        ref.customers.create_customer_organization(
            command_id=command, name="Rollback", account_code="ROLLBACK"
        )
    assert state(factory) == before
    assert read(factory, "SELECT 1 FROM command_receipts WHERE command_id=?", (command,)) == []


def test_generation_trigger_failure_rolls_back_everything(reference):
    ref, factory, _ = reference
    identity = create(ref.customers)
    connection = factory.open()
    try:
        connection.execute(
            "CREATE TRIGGER fail_generation BEFORE UPDATE ON reference_metadata BEGIN SELECT RAISE(ABORT,'injected'); END"
        )
    finally:
        connection.close()
    before = state(factory)
    with pytest.raises(SomaError):
        ref.customers.set_customer_account_code(
            command_id=new_uuid4(), customer_org_id=identity, base_revision=1, account_code="FAIL"
        )
    assert state(factory) == before


def test_unsupported_profile_and_archived_identity_fail_closed(reference):
    ref, factory, _ = reference
    identity = create(ref.customers)
    with UnitOfWork(factory) as uow:
        uow.connection.execute(
            "UPDATE customer_organizations SET lifecycle_state='archived' WHERE customer_org_id=?",
            (identity,),
        )
    with pytest.raises(SomaError) as exc:
        ref.customers.update_descriptive_data(
            command_id=new_uuid4(), customer_org_id=identity, base_revision=1, name="Customer"
        )
    assert exc.value.code == "CUSTOMER_ORG_INACTIVE"
    with UnitOfWork(factory) as uow:
        uow.connection.execute("UPDATE reference_metadata SET matching_profile_id='unsupported'")
    with pytest.raises(SomaError) as exc:
        create(ref.customers)
    assert exc.value.code == "MATCH_PROFILE_UNSUPPORTED"


def test_large_claimant_review_returns_only_bounded_snapshot_and_indexed_count(reference):
    ref, factory, _ = reference
    target = create(ref.customers)
    command = new_uuid4()
    with UnitOfWork(factory) as uow:
        uow.connection.execute(
            "INSERT INTO command_receipts VALUES (?,'synthetic',?,NULL,0)", (command, "0" * 64)
        )
        for i in range(1000):
            identity = new_uuid4()
            store.insert_customer(uow.connection, identity, "Synthetic", "synthetic", 0)
            store.insert_claim(uow.connection, new_uuid4(), identity, "SCALE", "scale", 0, command)
    preview = ref.customers.preview_account_code_review(
        raw_account_code="SCALE",
        proposed_action="CONFIRM_SHARED_CLAIM",
        target_customer_org_id=target,
    )
    assert preview["claimant_count"] == 1000 and len(preview) == 4
    connection = factory.open(read_only=True)
    try:
        plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT count(*) FROM customer_org_identifiers WHERE identifier_type='customer_account_code' AND match_key=? AND lifecycle_state='active'",
            ("scale",),
        ).fetchall()
        assert any(
            "SEARCH" in row[3] and "idx_customer_active_identifier_value" in row[3] for row in plan
        )
    finally:
        connection.close()
