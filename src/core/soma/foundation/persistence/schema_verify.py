"""Observational exact schema/lineage/integrity checks against committed truth."""

import hashlib
from importlib.resources import files

from soma.foundation.errors import SomaError
from soma.foundation.identity import require_uuid4
from soma.foundation.strict_json import loads_strict


def integrity_error():
    return SomaError(
        "PERSISTENCE_SCHEMA_MISMATCH",
        "Database structure or integrity verification failed.",
        "restart",
    )


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def schema_shape(connection) -> dict:
    """Used only for accepted-migration generation and observational comparison."""
    objects = [
        list(row)
        for row in connection.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT GLOB 'sqlite_*' ORDER BY type,name"
        ).fetchall()
    ]
    for row in objects:
        row[3] = None if row[3] is None else hashlib.sha256(row[3].encode()).hexdigest()
    tables = {}
    indexes = {}
    for row in connection.execute("PRAGMA table_list").fetchall():
        name = row[1]
        if row[0] != "main" or name.startswith("sqlite_"):
            continue
        tables[name] = {
            "flags": list(row[2:]),
            "columns": [
                list(value)
                for value in connection.execute(
                    f"PRAGMA table_xinfo({quote_identifier(name)})"
                ).fetchall()
            ],
            "foreign_keys": [
                list(value)
                for value in connection.execute(
                    f"PRAGMA foreign_key_list({quote_identifier(name)})"
                ).fetchall()
            ],
        }
        index_rows = connection.execute(f"PRAGMA index_list({quote_identifier(name)})").fetchall()
        for index in index_rows:
            index_name = index[1]
            indexes[index_name] = {
                "table": name,
                "flags": list(index[2:]),
                "keys": [
                    list(value)
                    for value in connection.execute(
                        f"PRAGMA index_xinfo({quote_identifier(index_name)})"
                    ).fetchall()
                ],
            }
    return {"objects": objects, "tables": tables, "indexes": indexes}


def verify_fk_indexes(connection) -> None:
    tables = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT GLOB 'sqlite_*'"
        ).fetchall()
    ]
    for table in tables:
        groups = {}
        for row in connection.execute(
            f"PRAGMA foreign_key_list({quote_identifier(table)})"
        ).fetchall():
            groups.setdefault(row[0], []).append((row[1], row[3]))
        indexes = connection.execute(f"PRAGMA index_list({quote_identifier(table)})").fetchall()
        for parts in groups.values():
            columns = tuple(column for _, column in sorted(parts))
            covered = False
            for index in indexes:
                # Initial schema has no measured exceptions or partial FK indexes.
                # Future owners may add a proved closed partial policy when required.
                if index[4]:
                    continue
                keys = [
                    row[2]
                    for row in connection.execute(
                        f"PRAGMA index_xinfo({quote_identifier(index[1])})"
                    ).fetchall()
                    if row[5]
                ]
                if tuple(keys[: len(columns)]) != columns:
                    continue
                where = " AND ".join(f"{quote_identifier(column)}=?" for column in columns)
                plan = connection.execute(
                    f"EXPLAIN QUERY PLAN SELECT 1 FROM {quote_identifier(table)} INDEXED BY {quote_identifier(index[1])} WHERE {where} LIMIT 1",
                    (None,) * len(columns),
                ).fetchall()
                if any(
                    "SEARCH " in row[3].upper() and index[1].upper() in row[3].upper()
                    for row in plan
                ):
                    covered = True
                    break
            if not covered:
                raise integrity_error()


def reconcile_ledger(connection, manifest, *, complete: bool = True) -> int:
    try:
        rows = connection.execute(
            "SELECT migration_id,owner_scope,content_sha256 FROM schema_migrations"
        ).fetchall()
        actual = {row[0]: list(row) for row in rows}
        expected = manifest.lineage()
        if (
            len(actual) != len(rows)
            or len(rows) > len(expected)
            or set(actual) != {row[0] for row in expected[: len(rows)]}
        ):
            raise integrity_error()
        if (
            any(actual[row[0]] != row for row in expected[: len(rows)])
            or complete
            and len(rows) != len(expected)
        ):
            raise integrity_error()
        return len(rows)
    except Exception:
        raise integrity_error() from None


def verify_schema(
    connection,
    manifest,
    *,
    instance_id: str | None = None,
    expected: dict | None = None,
    deep: bool = False,
) -> None:
    try:
        manifest.validate()
        expected = (
            expected
            if expected is not None
            else loads_strict(
                files("soma.db").joinpath("schema_manifest.json").read_text(encoding="utf-8")
            )
        )
        if (
            set(expected) != {"version", "generation", "lineage", "shape", "append_only_probes"}
            or type(expected["version"]) is not int
            or expected["version"] != 1
            or type(expected["generation"]) is not int
            or expected["generation"] != manifest.generation
            or expected["lineage"] != manifest.lineage()
        ):
            raise integrity_error()
        if schema_shape(connection) != expected["shape"]:
            raise integrity_error()
        reconcile_ledger(connection, manifest)
        if connection.execute("PRAGMA foreign_key_check").fetchall() != [] or connection.execute(
            "PRAGMA quick_check"
        ).fetchall() != [("ok",)]:
            raise integrity_error()
        if deep and connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise integrity_error()
        verify_fk_indexes(connection)
        rows = connection.execute(
            "SELECT singleton,data_instance_id FROM instance_metadata"
        ).fetchall()
        if (
            len(rows) != 1
            or rows[0][0] != 1
            or require_uuid4(rows[0][1]) != rows[0][1]
            or instance_id is not None
            and rows[0][1] != instance_id
        ):
            raise integrity_error()
        probes = expected["append_only_probes"]
        # A verified read-only snapshot cannot perform destructive probes. Exact
        # trigger SQL is still compared above; startup verifies behavior writable.
        if probes and connection.execute("PRAGMA query_only").fetchone() != (1,):
            connection.execute("SAVEPOINT soma_verify_append_only")
            try:
                for probe in probes:
                    for sql, params in probe["setup"]:
                        connection.execute(sql, params)
                    for sql, params in probe["reject"]:
                        try:
                            connection.execute(sql, params)
                        except Exception as rejection:
                            code = getattr(rejection, "sqlite_errorcode", None)
                            if type(code) is not int or code & 0xFF != 19:
                                raise integrity_error() from None
                            continue
                        raise integrity_error()
            finally:
                connection.execute("ROLLBACK TO soma_verify_append_only")
                connection.execute("RELEASE soma_verify_append_only")
    except SomaError:
        raise
    except Exception:
        raise integrity_error() from None
