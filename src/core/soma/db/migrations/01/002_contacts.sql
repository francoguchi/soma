CREATE TABLE contacts (
 contact_id TEXT PRIMARY KEY,
 name TEXT NOT NULL CHECK(length(name)>0),
 name_match_key TEXT NOT NULL CHECK(length(name_match_key)>0),
 lifecycle_state TEXT NOT NULL CHECK(lifecycle_state IN ('active','archived')),
 revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
 created_at_utc INTEGER NOT NULL CHECK(created_at_utc>=0),
 updated_at_utc INTEGER NOT NULL CHECK(updated_at_utc>=created_at_utc)
) STRICT;
CREATE TABLE contact_channels (
 contact_channel_id TEXT PRIMARY KEY,
 contact_id TEXT NOT NULL REFERENCES contacts(contact_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
 channel_kind TEXT NOT NULL CHECK(channel_kind='email'),
 value_text TEXT NOT NULL CHECK(length(value_text)>0),
 match_key TEXT NOT NULL CHECK(length(match_key)>0),
 lifecycle_state TEXT NOT NULL CHECK(lifecycle_state IN ('active','archived')),
 revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
 created_at_utc INTEGER NOT NULL CHECK(created_at_utc>=0),
 updated_at_utc INTEGER NOT NULL CHECK(updated_at_utc>=created_at_utc)
) STRICT;
CREATE TABLE contact_affiliations (
 contact_affiliation_id TEXT PRIMARY KEY,
 contact_id TEXT NOT NULL REFERENCES contacts(contact_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
 customer_org_id TEXT NOT NULL REFERENCES customer_organizations(customer_org_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
 is_current INTEGER NOT NULL CHECK(is_current IN (0,1)),
 opened_at_utc INTEGER NOT NULL CHECK(opened_at_utc>=0),
 closed_at_utc INTEGER CHECK(closed_at_utc IS NULL OR closed_at_utc>=opened_at_utc),
 opened_command_id TEXT NOT NULL REFERENCES command_receipts(command_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
 closed_command_id TEXT REFERENCES command_receipts(command_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
 CHECK((is_current=1 AND closed_at_utc IS NULL AND closed_command_id IS NULL) OR
       (is_current=0 AND closed_at_utc IS NOT NULL AND closed_command_id IS NOT NULL))
) STRICT;
CREATE INDEX idx_contacts_active_name_match ON contacts(lifecycle_state,name_match_key,contact_id);
CREATE INDEX idx_contact_channels_contact ON contact_channels(contact_id,lifecycle_state,channel_kind,created_at_utc,contact_channel_id);
CREATE INDEX idx_contact_channels_match ON contact_channels(channel_kind,lifecycle_state,match_key,contact_id);
CREATE UNIQUE INDEX uq_contact_current_affiliation ON contact_affiliations(contact_id) WHERE is_current=1;
CREATE INDEX idx_contact_affiliation_customer_current ON contact_affiliations(customer_org_id,is_current,contact_id);
CREATE INDEX idx_contact_affiliation_history ON contact_affiliations(contact_id,opened_at_utc,contact_affiliation_id);
CREATE INDEX idx_contact_affiliation_opened_command ON contact_affiliations(opened_command_id);
CREATE INDEX idx_contact_affiliation_closed_command ON contact_affiliations(closed_command_id) WHERE closed_command_id IS NOT NULL;
CREATE TRIGGER reference_contacts_update_guard BEFORE UPDATE ON contacts
WHEN NEW.contact_id IS NOT OLD.contact_id OR NEW.created_at_utc IS NOT OLD.created_at_utc
BEGIN SELECT RAISE(ABORT,'reference_contacts_update_guard'); END;
CREATE TRIGGER reference_contacts_delete_forbidden BEFORE DELETE ON contacts
BEGIN SELECT RAISE(ABORT,'reference_contacts_delete_forbidden'); END;
CREATE TRIGGER contact_channels_update_guard BEFORE UPDATE ON contact_channels
WHEN NEW.contact_channel_id IS NOT OLD.contact_channel_id OR NEW.contact_id IS NOT OLD.contact_id
 OR NEW.channel_kind IS NOT OLD.channel_kind OR NEW.created_at_utc IS NOT OLD.created_at_utc
 OR OLD.lifecycle_state<>'active' OR NEW.revision<>OLD.revision+1
 OR NEW.updated_at_utc<OLD.updated_at_utc
 OR (NEW.lifecycle_state='archived' AND (NEW.value_text IS NOT OLD.value_text OR NEW.match_key IS NOT OLD.match_key))
BEGIN SELECT RAISE(ABORT,'contact_channels_update_guard'); END;
CREATE TRIGGER contact_channels_delete_forbidden BEFORE DELETE ON contact_channels
BEGIN SELECT RAISE(ABORT,'contact_channels_delete_forbidden'); END;
CREATE TRIGGER contact_affiliation_history_update_guard BEFORE UPDATE ON contact_affiliations
WHEN OLD.is_current<>1 OR NEW.is_current<>0
 OR NEW.contact_affiliation_id IS NOT OLD.contact_affiliation_id OR NEW.contact_id IS NOT OLD.contact_id
 OR NEW.customer_org_id IS NOT OLD.customer_org_id OR NEW.opened_at_utc IS NOT OLD.opened_at_utc
 OR NEW.opened_command_id IS NOT OLD.opened_command_id
 OR NEW.closed_at_utc IS NULL OR NEW.closed_command_id IS NULL
BEGIN SELECT RAISE(ABORT,'contact_affiliation_history_update_guard'); END;
CREATE TRIGGER contact_affiliation_history_delete_forbidden BEFORE DELETE ON contact_affiliations
BEGIN SELECT RAISE(ABORT,'contact_affiliation_history_delete_forbidden'); END;
