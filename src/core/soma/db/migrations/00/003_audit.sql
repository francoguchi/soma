CREATE TABLE audit_events (
 audit_event_id TEXT PRIMARY KEY, action_type TEXT NOT NULL, action_version INTEGER NOT NULL CHECK(action_version>=1), actor_kind TEXT NOT NULL, actor_id TEXT, target_type TEXT NOT NULL, target_id TEXT, command_id TEXT NOT NULL REFERENCES command_receipts(command_id), correlation_id TEXT, job_id TEXT, payload_schema TEXT NOT NULL, payload_version INTEGER NOT NULL CHECK(payload_version>=1), payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL CHECK(length(payload_sha256)=64), payload_bytes INTEGER NOT NULL CHECK(payload_bytes>=0), recorded_at_utc INTEGER NOT NULL CHECK(recorded_at_utc>=0)
) STRICT;
CREATE INDEX audit_command ON audit_events(command_id);
CREATE TABLE audit_event_results (
 audit_event_id TEXT NOT NULL REFERENCES audit_events(audit_event_id), ordinal INTEGER NOT NULL CHECK(ordinal>=0), result_type TEXT NOT NULL, result_id TEXT NOT NULL, PRIMARY KEY(audit_event_id,ordinal)
) STRICT;
CREATE TRIGGER audit_events_no_update BEFORE UPDATE ON audit_events BEGIN SELECT RAISE(ABORT,'audit is append only'); END;
CREATE TRIGGER audit_events_no_delete BEFORE DELETE ON audit_events BEGIN SELECT RAISE(ABORT,'audit is append only'); END;
CREATE TRIGGER audit_results_no_update BEFORE UPDATE ON audit_event_results BEGIN SELECT RAISE(ABORT,'audit is append only'); END;
CREATE TRIGGER audit_results_no_delete BEFORE DELETE ON audit_event_results BEGIN SELECT RAISE(ABORT,'audit is append only'); END;
