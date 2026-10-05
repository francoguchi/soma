from soma.foundation.errors import SomaError


def active(connection, identity, base_revision):
    row = connection.execute(
        "SELECT name,name_match_key,address_mode,standalone_address_text,lifecycle_state,revision "
        "FROM dispatch_locations WHERE dispatch_location_id=?",
        (identity,),
    ).fetchone()
    if row is None:
        raise SomaError("NOT_FOUND", "Dispatch Location does not exist.", "refresh")
    if row[4] != "active":
        raise SomaError("REFERENCE_ARCHIVED", "Dispatch Location is archived.", "refresh")
    if row[5] != base_revision:
        raise SomaError("STALE_REVISION", "Dispatch Location revision changed.", "refresh")
    return row


def insert(connection, identity, name, key, mode, address, now):
    connection.execute(
        "INSERT INTO dispatch_locations VALUES (?,?,?,?,?,'active',1,?,?)",
        (identity, name, key, mode, address, now, now),
    )


def update(connection, identity, name, key, address, now):
    connection.execute(
        "UPDATE dispatch_locations SET name=?,name_match_key=?,standalone_address_text=?,"
        "revision=revision+1,updated_at_utc=? WHERE dispatch_location_id=?",
        (name, key, address, now, identity),
    )


def lifecycle_event(connection, event_id, identity, kind, now, command_id):
    connection.execute(
        "INSERT INTO reference_lifecycle_events VALUES (?,'dispatch_location',?,?,?,?,NULL)",
        (event_id, identity, kind, now, command_id),
    )
