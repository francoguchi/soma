CREATE TABLE reference_metadata (
    singleton_guard INTEGER PRIMARY KEY CHECK(singleton_guard=1),
    matching_profile_id TEXT NOT NULL CHECK(length(matching_profile_id)>0),
    customer_reference_generation INTEGER NOT NULL DEFAULT 0 CHECK(customer_reference_generation>=0)
) STRICT;
INSERT INTO reference_metadata VALUES (1,'UNICODE_MATCH_V1',0);

CREATE TABLE local_user_profiles (
    local_user_profile_id TEXT PRIMARY KEY REFERENCES local_admin_credentials(actor_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    singleton_guard INTEGER NOT NULL UNIQUE CHECK(singleton_guard=1),
    display_name TEXT NOT NULL CHECK(length(display_name)>0),
    revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
    created_at_utc INTEGER NOT NULL CHECK(created_at_utc>=0),
    updated_at_utc INTEGER NOT NULL CHECK(updated_at_utc>=created_at_utc)
) STRICT;

CREATE TABLE customer_organizations (
    customer_org_id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK(length(name)>0),
    name_match_key TEXT NOT NULL CHECK(length(name_match_key)>0),
    lifecycle_state TEXT NOT NULL CHECK(lifecycle_state IN ('active','archived')),
    revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
    created_at_utc INTEGER NOT NULL CHECK(created_at_utc>=0),
    updated_at_utc INTEGER NOT NULL CHECK(updated_at_utc>=created_at_utc)
) STRICT;

CREATE TABLE customer_org_identifiers (
    customer_org_identifier_id TEXT PRIMARY KEY,
    customer_org_id TEXT NOT NULL REFERENCES customer_organizations(customer_org_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    identifier_type TEXT NOT NULL CHECK(identifier_type='customer_account_code'),
    value_text TEXT NOT NULL CHECK(length(value_text)>0),
    match_key TEXT NOT NULL CHECK(length(match_key)>0),
    lifecycle_state TEXT NOT NULL CHECK(lifecycle_state IN ('active','superseded')),
    created_at_utc INTEGER NOT NULL CHECK(created_at_utc>=0),
    superseded_at_utc INTEGER NULL,
    created_command_id TEXT NOT NULL REFERENCES command_receipts(command_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    superseded_command_id TEXT NULL REFERENCES command_receipts(command_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CHECK((lifecycle_state='active' AND superseded_at_utc IS NULL AND superseded_command_id IS NULL)
       OR (lifecycle_state='superseded' AND superseded_at_utc IS NOT NULL AND superseded_command_id IS NOT NULL))
) STRICT;

CREATE TABLE reference_lifecycle_events (
    reference_lifecycle_event_id TEXT PRIMARY KEY,
    target_type TEXT NOT NULL CHECK(target_type IN ('customer_organization','contact','dispatch_location')),
    target_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('created','archived','reactivated','descriptive_corrected')),
    occurred_at_utc INTEGER NOT NULL CHECK(occurred_at_utc>=0),
    command_id TEXT NOT NULL REFERENCES command_receipts(command_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    reason_category TEXT NULL
) STRICT;

CREATE INDEX idx_customer_org_active_name_match ON customer_organizations(lifecycle_state,name_match_key,customer_org_id);
CREATE UNIQUE INDEX uq_customer_org_active_identifier_type ON customer_org_identifiers(customer_org_id,identifier_type) WHERE lifecycle_state='active';
CREATE INDEX idx_customer_active_identifier_value ON customer_org_identifiers(identifier_type,match_key,customer_org_id) WHERE lifecycle_state='active';
CREATE INDEX idx_customer_identifier_history ON customer_org_identifiers(customer_org_id,identifier_type,created_at_utc,customer_org_identifier_id);
CREATE INDEX idx_customer_identifier_created_command ON customer_org_identifiers(created_command_id);
CREATE INDEX idx_customer_identifier_superseded_command ON customer_org_identifiers(superseded_command_id) WHERE superseded_command_id IS NOT NULL;
CREATE INDEX idx_reference_lifecycle_target ON reference_lifecycle_events(target_type,target_id,occurred_at_utc,reference_lifecycle_event_id);
CREATE INDEX idx_reference_lifecycle_command ON reference_lifecycle_events(command_id);

CREATE TRIGGER reference_metadata_delete_forbidden BEFORE DELETE ON reference_metadata
BEGIN SELECT RAISE(ABORT,'REFERENCE_METADATA_DELETE_FORBIDDEN'); END;
CREATE TRIGGER local_user_profile_update_guard BEFORE UPDATE ON local_user_profiles
WHEN NEW.local_user_profile_id IS NOT OLD.local_user_profile_id OR NEW.singleton_guard IS NOT OLD.singleton_guard OR NEW.created_at_utc IS NOT OLD.created_at_utc
BEGIN SELECT RAISE(ABORT,'LOCAL_USER_PROFILE_IDENTITY_IMMUTABLE'); END;
CREATE TRIGGER local_user_profile_delete_forbidden BEFORE DELETE ON local_user_profiles
BEGIN SELECT RAISE(ABORT,'LOCAL_USER_PROFILE_DELETE_FORBIDDEN'); END;
CREATE TRIGGER reference_customer_organizations_update_guard BEFORE UPDATE ON customer_organizations
WHEN NEW.customer_org_id IS NOT OLD.customer_org_id OR NEW.created_at_utc IS NOT OLD.created_at_utc
BEGIN SELECT RAISE(ABORT,'REFERENCE_IDENTITY_IMMUTABLE'); END;
CREATE TRIGGER reference_customer_organizations_delete_forbidden BEFORE DELETE ON customer_organizations
BEGIN SELECT RAISE(ABORT,'REFERENCE_DELETE_FORBIDDEN'); END;
CREATE TRIGGER customer_identifier_history_update_guard BEFORE UPDATE ON customer_org_identifiers
WHEN OLD.lifecycle_state<>'active' OR NEW.lifecycle_state<>'superseded'
 OR NEW.customer_org_identifier_id IS NOT OLD.customer_org_identifier_id
 OR NEW.customer_org_id IS NOT OLD.customer_org_id OR NEW.identifier_type IS NOT OLD.identifier_type
 OR NEW.value_text IS NOT OLD.value_text OR NEW.match_key IS NOT OLD.match_key
 OR NEW.created_at_utc IS NOT OLD.created_at_utc OR NEW.created_command_id IS NOT OLD.created_command_id
 OR NEW.superseded_at_utc IS NULL OR NEW.superseded_command_id IS NULL
BEGIN SELECT RAISE(ABORT,'CUSTOMER_IDENTIFIER_HISTORY_APPEND_ONLY'); END;
CREATE TRIGGER customer_identifier_history_delete_forbidden BEFORE DELETE ON customer_org_identifiers
BEGIN SELECT RAISE(ABORT,'CUSTOMER_IDENTIFIER_HISTORY_APPEND_ONLY'); END;
CREATE TRIGGER reference_lifecycle_events_update_forbidden BEFORE UPDATE ON reference_lifecycle_events
BEGIN SELECT RAISE(ABORT,'REFERENCE_LIFECYCLE_APPEND_ONLY'); END;
CREATE TRIGGER reference_lifecycle_events_delete_forbidden BEFORE DELETE ON reference_lifecycle_events
BEGIN SELECT RAISE(ABORT,'REFERENCE_LIFECYCLE_APPEND_ONLY'); END;
CREATE TRIGGER customer_reference_generation_after_customer_insert AFTER INSERT ON customer_organizations
BEGIN UPDATE reference_metadata SET customer_reference_generation=customer_reference_generation+1 WHERE singleton_guard=1; END;
CREATE TRIGGER customer_reference_generation_after_customer_update AFTER UPDATE ON customer_organizations
BEGIN UPDATE reference_metadata SET customer_reference_generation=customer_reference_generation+1 WHERE singleton_guard=1; END;
CREATE TRIGGER customer_reference_generation_after_identifier_insert AFTER INSERT ON customer_org_identifiers
BEGIN UPDATE reference_metadata SET customer_reference_generation=customer_reference_generation+1 WHERE singleton_guard=1; END;
CREATE TRIGGER customer_reference_generation_after_identifier_update AFTER UPDATE ON customer_org_identifiers
BEGIN UPDATE reference_metadata SET customer_reference_generation=customer_reference_generation+1 WHERE singleton_guard=1; END;
