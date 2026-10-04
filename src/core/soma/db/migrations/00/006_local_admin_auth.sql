CREATE TABLE local_admin_credentials (
 singleton_key INTEGER PRIMARY KEY CHECK(singleton_key=1), actor_id TEXT NOT NULL UNIQUE, password_phc TEXT NOT NULL, credential_version INTEGER NOT NULL DEFAULT 1 CHECK(credential_version>=1), created_at_utc INTEGER NOT NULL CHECK(created_at_utc>=0), updated_at_utc INTEGER NOT NULL CHECK(updated_at_utc>=created_at_utc)
) STRICT;
