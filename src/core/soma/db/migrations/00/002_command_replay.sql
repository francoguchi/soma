CREATE TABLE command_receipts (
 command_id TEXT PRIMARY KEY, command_type TEXT NOT NULL, request_sha256 TEXT NOT NULL CHECK(length(request_sha256)=64), correlation_id TEXT, committed_at_utc INTEGER NOT NULL CHECK(committed_at_utc>=0)
) STRICT;
CREATE TABLE command_receipt_results (
 command_id TEXT PRIMARY KEY REFERENCES command_receipts(command_id), result_schema TEXT NOT NULL, result_version INTEGER NOT NULL CHECK(result_version>=1), result_json TEXT NOT NULL, result_sha256 TEXT NOT NULL CHECK(length(result_sha256)=64), result_bytes INTEGER NOT NULL CHECK(result_bytes>=0)
) STRICT;
