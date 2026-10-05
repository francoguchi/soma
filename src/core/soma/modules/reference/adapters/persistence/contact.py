"""Contact persistence in the caller's snapshot or UnitOfWork."""

from soma.foundation.errors import SomaError


def contact(connection, identity):
    return connection.execute(
        "SELECT contact_id,name,name_match_key,lifecycle_state,revision FROM contacts WHERE contact_id=?",
        (identity,),
    ).fetchone()


def active_contact(connection, identity, revision):
    row = contact(connection, identity)
    if row is None:
        raise SomaError("NOT_FOUND", "Contact does not exist.", "refresh")
    if row[3] != "active":
        raise SomaError("REFERENCE_ARCHIVED", "Contact is inactive.", "refresh")
    if row[4] != revision:
        raise SomaError("STALE_REVISION", "Contact revision changed.", "refresh")
    return row


def channel(connection, contact_id, identity):
    row = connection.execute(
        "SELECT contact_channel_id,contact_id,channel_kind,value_text,match_key,lifecycle_state,revision FROM contact_channels WHERE contact_channel_id=?",
        (identity,),
    ).fetchone()
    if row is None:
        raise SomaError("NOT_FOUND", "Channel does not exist.", "refresh")
    if row[1] != contact_id:
        raise SomaError("CHANNEL_NOT_OWNED", "Channel belongs to another Contact.", "refresh")
    return row


def active_channel(connection, contact_id, identity, revision):
    row = channel(connection, contact_id, identity)
    if row[5] != "active":
        raise SomaError("CHANNEL_NOT_USABLE", "Channel is inactive.", "refresh")
    if row[6] != revision:
        raise SomaError("STALE_REVISION", "Channel revision changed.", "refresh")
    return row


def current_affiliation(connection, identity):
    return connection.execute(
        "SELECT contact_affiliation_id,customer_org_id FROM contact_affiliations WHERE contact_id=? AND is_current=1",
        (identity,),
    ).fetchone()


def insert_contact(connection, identity, name, key, now):
    connection.execute(
        "INSERT INTO contacts VALUES (?,?,?,'active',1,?,?)", (identity, name, key, now, now)
    )


def bump_revision(connection, identity, now):
    connection.execute(
        "UPDATE contacts SET revision=revision+1,updated_at_utc=? WHERE contact_id=?",
        (now, identity),
    )


def update_name(connection, identity, name, key, now):
    connection.execute(
        "UPDATE contacts SET name=?,name_match_key=?,revision=revision+1,updated_at_utc=? WHERE contact_id=?",
        (name, key, now, identity),
    )


def insert_channel(connection, identity, contact_id, value, key, now):
    connection.execute(
        "INSERT INTO contact_channels VALUES (?,?,'email',?,?,'active',1,?,?)",
        (identity, contact_id, value, key, now, now),
    )


def update_channel(connection, identity, value, key, now):
    connection.execute(
        "UPDATE contact_channels SET value_text=?,match_key=?,revision=revision+1,updated_at_utc=? WHERE contact_channel_id=?",
        (value, key, now, identity),
    )


def archive_channel(connection, identity, now):
    connection.execute(
        "UPDATE contact_channels SET lifecycle_state='archived',revision=revision+1,updated_at_utc=? WHERE contact_channel_id=?",
        (now, identity),
    )


def insert_affiliation(connection, identity, contact_id, customer_id, now, command):
    connection.execute(
        "INSERT INTO contact_affiliations VALUES (?,?,?,1,?,NULL,?,NULL)",
        (identity, contact_id, customer_id, now, command),
    )


def close_affiliation(connection, identity, now, command):
    connection.execute(
        "UPDATE contact_affiliations SET is_current=0,closed_at_utc=?,closed_command_id=? WHERE contact_affiliation_id=?",
        (now, command, identity),
    )


def lifecycle_event(connection, identity, contact_id, kind, now, command):
    connection.execute(
        "INSERT INTO reference_lifecycle_events VALUES (?,'contact',?,?,?, ?,NULL)",
        (identity, contact_id, kind, now, command),
    )
