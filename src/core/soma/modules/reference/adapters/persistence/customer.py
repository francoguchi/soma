"""Bounded Customer reads and caller-owned writes; no transaction ownership."""

from soma.foundation.errors import SomaError
from soma.modules.reference.domain.account_code import AccountCodeReviewContext, CustomerCodeState
from .matching_profile import require_persisted_matching_profile


def active_customer(connection, identity, revision=None):
    row = connection.execute(
        "SELECT customer_org_id,name,name_match_key,lifecycle_state,revision FROM customer_organizations WHERE customer_org_id=?",
        (identity,),
    ).fetchone()
    if row is None:
        raise SomaError("NOT_FOUND", "Customer does not exist.", "refresh")
    if row[3] != "active":
        raise SomaError("CUSTOMER_ORG_INACTIVE", "Customer is inactive.", "refresh")
    if revision is not None and row[4] != revision:
        raise SomaError("STALE_REVISION", "Customer revision changed.", "refresh")
    return row


def current_claim(connection, identity):
    return connection.execute(
        "SELECT customer_org_identifier_id,value_text,match_key FROM customer_org_identifiers WHERE customer_org_id=? AND identifier_type='customer_account_code' AND lifecycle_state='active'",
        (identity,),
    ).fetchone()


def claimant_count(connection, key, exclude=None):
    return connection.execute(
        "SELECT count(*) FROM customer_org_identifiers WHERE identifier_type='customer_account_code' AND match_key=? AND lifecycle_state='active' AND (? IS NULL OR customer_org_id<>?)",
        (key, exclude, exclude),
    ).fetchone()[0]


def review_context(connection, key, action, target_id, source_id=None):
    require_persisted_matching_profile(connection)
    profile, generation = connection.execute(
        "SELECT matching_profile_id,customer_reference_generation FROM reference_metadata WHERE singleton_guard=1"
    ).fetchone()

    def state(identity):
        row = active_customer(connection, identity)
        claim = current_claim(connection, identity)
        return CustomerCodeState(identity, row[4], None if claim is None else claim[2])

    return AccountCodeReviewContext(
        profile,
        generation,
        key,
        action,
        state(target_id),
        None if source_id is None else state(source_id),
        claimant_count(connection, key),
    )


def insert_customer(connection, identity, name, key, now):
    connection.execute(
        "INSERT INTO customer_organizations VALUES (?,?,?,'active',1,?,?)",
        (identity, name, key, now, now),
    )


def update_name(connection, identity, name, key, now):
    connection.execute(
        "UPDATE customer_organizations SET name=?,name_match_key=?,revision=revision+1,updated_at_utc=? WHERE customer_org_id=?",
        (name, key, now, identity),
    )


def bump_revision(connection, identity, now):
    connection.execute(
        "UPDATE customer_organizations SET revision=revision+1,updated_at_utc=? WHERE customer_org_id=?",
        (now, identity),
    )


def insert_claim(connection, identity, customer_id, value, key, now, command):
    connection.execute(
        "INSERT INTO customer_org_identifiers(customer_org_identifier_id,customer_org_id,identifier_type,value_text,match_key,lifecycle_state,created_at_utc,created_command_id) VALUES (?,?,'customer_account_code',?,?,'active',?,?)",
        (identity, customer_id, value, key, now, command),
    )


def supersede_claim(connection, identity, now, command):
    connection.execute(
        "UPDATE customer_org_identifiers SET lifecycle_state='superseded',superseded_at_utc=?,superseded_command_id=? WHERE customer_org_identifier_id=?",
        (now, command, identity),
    )


def lifecycle_event(connection, identity, customer_id, kind, now, command):
    connection.execute(
        "INSERT INTO reference_lifecycle_events VALUES (?,'customer_organization',?,?,?, ?,NULL)",
        (identity, customer_id, kind, now, command),
    )
