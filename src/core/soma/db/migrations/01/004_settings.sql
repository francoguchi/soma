CREATE TABLE setting_values (
 setting_key TEXT PRIMARY KEY,
 contract_name TEXT NOT NULL,
 contract_version INTEGER NOT NULL CHECK(contract_version>0),
 value_json TEXT NOT NULL CHECK(json_valid(value_json)),
 revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
 updated_at_utc INTEGER NOT NULL CHECK(updated_at_utc>=0),
 command_id TEXT NOT NULL REFERENCES command_receipts(command_id) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;
CREATE INDEX idx_setting_values_command ON setting_values(command_id);
CREATE TRIGGER setting_key_update_guard BEFORE UPDATE ON setting_values
WHEN NEW.setting_key IS NOT OLD.setting_key
BEGIN SELECT RAISE(ABORT,'setting_key_update_guard'); END;
