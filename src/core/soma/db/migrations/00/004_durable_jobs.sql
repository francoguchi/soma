CREATE TABLE durable_jobs (
 job_id TEXT PRIMARY KEY, job_type TEXT NOT NULL, contract_version INTEGER NOT NULL CHECK(contract_version>=1), state TEXT NOT NULL CHECK(state IN ('queued','running','waiting_review','retry_wait','completed','failed','cancelled')), payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL CHECK(length(payload_sha256)=64), dedupe_sha256 TEXT, checkpoint_json TEXT, checkpoint_sha256 TEXT, attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count>=0), claimed_run_id TEXT, claim_started_at_utc INTEGER, next_attempt_at_utc INTEGER, last_error_code TEXT, correlation_id TEXT, created_at_utc INTEGER NOT NULL CHECK(created_at_utc>=0), updated_at_utc INTEGER NOT NULL CHECK(updated_at_utc>=created_at_utc), CHECK((state='running')=(claimed_run_id IS NOT NULL AND claim_started_at_utc IS NOT NULL)), CHECK((checkpoint_json IS NULL)=(checkpoint_sha256 IS NULL))
) STRICT;
CREATE UNIQUE INDEX durable_jobs_active_dedupe ON durable_jobs(job_type,contract_version,dedupe_sha256) WHERE state IN ('queued','running','waiting_review','retry_wait');
CREATE INDEX durable_jobs_due ON durable_jobs(state,next_attempt_at_utc,created_at_utc);
CREATE TABLE job_attempts (
 job_id TEXT NOT NULL REFERENCES durable_jobs(job_id), attempt_ordinal INTEGER NOT NULL CHECK(attempt_ordinal>=1), run_id TEXT NOT NULL, started_at_utc INTEGER NOT NULL, finished_at_utc INTEGER NOT NULL CHECK(finished_at_utc>=started_at_utc), outcome TEXT NOT NULL CHECK(outcome IN ('completed','failed','cancelled','interrupted')), error_code TEXT, PRIMARY KEY(job_id,attempt_ordinal)
) STRICT;
