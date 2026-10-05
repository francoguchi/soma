"""Static owner SQL. Every collection fetch has an explicit LIMIT."""

from soma.foundation.errors import SomaError, ValidationError

MASTERS = {
    "customer_organization": ("customer_organizations", "customer_org_id"),
    "contact": ("contacts", "contact_id"),
    "dispatch_location": ("dispatch_locations", "dispatch_location_id"),
}
HISTORY = {
    "account_code": (
        "customer_org_identifiers",
        "customer_org_id",
        "created_at_utc",
        "customer_org_identifier_id",
        "customer_org_identifier_id,customer_org_id,identifier_type,value_text,match_key,lifecycle_state,created_at_utc,created_command_id,superseded_at_utc,superseded_command_id",
    ),
    "affiliation": (
        "contact_affiliations",
        "contact_id",
        "opened_at_utc",
        "contact_affiliation_id",
        "contact_affiliation_id,contact_id,customer_org_id,is_current,opened_at_utc,closed_at_utc,opened_command_id,closed_command_id",
    ),
    "channels": (
        "contact_channels",
        "contact_id",
        "created_at_utc",
        "contact_channel_id",
        "contact_channel_id,contact_id,channel_kind,value_text,match_key,lifecycle_state,revision,created_at_utc,updated_at_utc",
    ),
}


def master(kind):
    if type(kind) is not str or kind not in MASTERS:
        raise ValidationError("Invalid reference type.")
    return MASTERS[kind]


def identities(connection, kind, ids):
    table, key = master(kind)
    if not ids:
        return []
    rows = connection.execute(
        f"SELECT {key},name,lifecycle_state,revision FROM {table} WHERE {key} IN ({','.join('?' for _ in ids)}) ORDER BY name_match_key,{key} LIMIT 200",
        tuple(ids),
    ).fetchall()
    return [dict(zip(("reference_id", "name", "lifecycle_state", "revision"), row)) for row in rows]


def detail(connection, kind, identity):
    table, key = master(kind)
    extra = ",address_mode,standalone_address_text" if kind == "dispatch_location" else ""
    row = connection.execute(
        f"SELECT {key},name,name_match_key,lifecycle_state,revision,created_at_utc,updated_at_utc{extra} FROM {table} WHERE {key}=?",
        (identity,),
    ).fetchone()
    if row is None:
        raise SomaError("NOT_FOUND", "Reference does not exist.", "refresh")
    fields = "reference_id,name,name_match_key,lifecycle_state,revision,created_at_utc,updated_at_utc".split(
        ","
    )
    if extra:
        fields += ["address_mode", "standalone_address_text"]
    return dict(zip(fields, row))


def active_page(connection, kind, position, limit):
    table, key = master(kind)
    rows = connection.execute(
        f"SELECT {key},name,name_match_key,lifecycle_state,revision FROM {table} WHERE lifecycle_state='active' AND (name_match_key,{key})>(?,?) ORDER BY name_match_key,{key} LIMIT ?",
        (*position, limit + 1),
    ).fetchall()
    return [
        dict(zip(("reference_id", "name", "name_match_key", "lifecycle_state", "revision"), row))
        for row in rows
    ]


def active_count(connection, kind):
    table, _ = master(kind)
    return connection.execute(
        f"SELECT count(*) FROM {table} WHERE lifecycle_state='active'"
    ).fetchone()[0]


def history(connection, kind, identity, position, limit, include_archived=True):
    if kind not in HISTORY:
        raise ValidationError("Invalid history kind.")
    table, owner, chronology, key, columns = HISTORY[kind]
    predicate = (
        " AND lifecycle_state='active'" if kind == "channels" and not include_archived else ""
    )
    rows = connection.execute(
        f"SELECT {columns} FROM {table} WHERE {owner}=?{predicate} AND ({chronology},{key})>(?,?) ORDER BY {chronology},{key} LIMIT ?",
        (identity, *position, limit + 1),
    ).fetchall()
    return [dict(zip(columns.split(","), row)) for row in rows]


def history_count(connection, kind, identity, include_archived):
    table, owner, _, _, _ = HISTORY[kind]
    predicate = (
        " AND lifecycle_state='active'" if kind == "channels" and not include_archived else ""
    )
    return connection.execute(
        f"SELECT count(*) FROM {table} WHERE {owner}=?{predicate}", (identity,)
    ).fetchone()[0]


CUSTOMER_MATCH = """WITH evidence AS (
 SELECT c.customer_org_id AS id, 'code' AS source FROM customer_org_identifiers i
 JOIN customer_organizations c ON c.customer_org_id=i.customer_org_id
 WHERE i.identifier_type='customer_account_code' AND i.lifecycle_state='active'
 AND i.match_key=? AND c.lifecycle_state='active'
 UNION ALL
 SELECT customer_org_id AS id, 'name' AS source FROM customer_organizations
 WHERE lifecycle_state='active' AND name_match_key=?
), candidates AS (SELECT DISTINCT id FROM evidence) """
CONTACT_MATCH = """WITH evidence AS (
 SELECT c.contact_id AS id FROM contacts c WHERE c.lifecycle_state='active' AND c.name_match_key=?
 AND ((?='UNBOUND' AND NOT EXISTS(SELECT 1 FROM contact_affiliations a WHERE a.contact_id=c.contact_id AND a.is_current=1))
 OR EXISTS(SELECT 1 FROM contact_affiliations a WHERE a.contact_id=c.contact_id AND a.is_current=1 AND a.customer_org_id=?))
 UNION
 SELECT c.contact_id AS id FROM contact_channels ch JOIN contacts c ON c.contact_id=ch.contact_id
 WHERE ch.channel_kind='email' AND ch.lifecycle_state='active' AND ch.match_key=? AND c.lifecycle_state='active'
 AND ((?='UNBOUND' AND NOT EXISTS(SELECT 1 FROM contact_affiliations a WHERE a.contact_id=c.contact_id AND a.is_current=1))
 OR EXISTS(SELECT 1 FROM contact_affiliations a WHERE a.contact_id=c.contact_id AND a.is_current=1 AND a.customer_org_id=?))
), candidates AS (SELECT id FROM evidence) """


def match(connection, kind, keys, scope, after, limit):
    if kind == "customer_organization":
        sql, parameters = CUSTOMER_MATCH, (keys["account_code"], keys["name"])
        total, code_count = connection.execute(
            sql
            + "SELECT (SELECT count(*) FROM candidates),(SELECT count(*) FROM evidence WHERE source='code')",
            parameters,
        ).fetchone()
    elif kind == "contact":
        sql, parameters = CONTACT_MATCH, (keys["name"], scope, scope, keys["email"], scope, scope)
        total = connection.execute(sql + "SELECT count(*) FROM candidates", parameters).fetchone()[
            0
        ]
        code_count = 0
    else:
        raise ValidationError("Invalid candidate kind.")
    rows = connection.execute(
        sql + "SELECT id FROM candidates WHERE id>? ORDER BY id LIMIT ?",
        (*parameters, after, limit + 1),
    ).fetchall()
    return total, code_count, tuple(row[0] for row in rows)
