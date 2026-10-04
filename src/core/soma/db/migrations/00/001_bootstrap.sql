CREATE TABLE schema_migrations (
    migration_id TEXT PRIMARY KEY,
    owner_scope TEXT NOT NULL CHECK(length(owner_scope) = 2),
    content_sha256 TEXT NOT NULL CHECK(length(content_sha256) = 64),
    applied_at_utc INTEGER NOT NULL CHECK(applied_at_utc >= 0),
    application_version TEXT NOT NULL
) STRICT;

CREATE TABLE instance_metadata (
    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
    data_instance_id TEXT NOT NULL UNIQUE,
    created_at_utc INTEGER NOT NULL CHECK(created_at_utc >= 0)
) STRICT;
