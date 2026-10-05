from soma.foundation.errors import SomaError, ValidationError

# Only closed owner identifiers can select a SQL path.
TABLES = {
    "customer_organization": ("customer_organizations", "customer_org_id"),
    "contact": ("contacts", "contact_id"),
    "dispatch_location": ("dispatch_locations", "dispatch_location_id"),
}


def validate_type(target_type):
    if type(target_type) is not str or target_type not in TABLES:
        raise ValidationError("Invalid Reference target type.")


def load(connection, target):
    validate_type(target.target_type)
    table, key = TABLES[target.target_type]
    row = connection.execute(
        f"SELECT lifecycle_state,revision FROM {table} WHERE {key}=?", (target.target_id,)
    ).fetchone()
    if row is None:
        raise SomaError("NOT_FOUND", "Reference does not exist.", "refresh")
    return row


def transition(connection, target, state, now, lifecycle, kind, command_id, reason):
    validate_type(target.target_type)
    table, key = TABLES[target.target_type]
    connection.execute(
        f"UPDATE {table} SET lifecycle_state=?,revision=revision+1,updated_at_utc=? WHERE {key}=?",
        (state, now, target.target_id),
    )
    connection.execute(
        "INSERT INTO reference_lifecycle_events VALUES (?,?,?,?,?,?,?)",
        (lifecycle, target.target_type, target.target_id, kind, now, command_id, reason),
    )
