<!-- soma-meta
{
  "version": 1,
  "id": "LLD-00-MIGRATIONS",
  "scope": "00",
  "items": [
    {
      "id": "M00.001",
      "anchor": "m00-001",
      "depends_on": ["MIGRATION.MANIFEST"],
      "code_paths": ["src/core/soma/db/migrations/00/001_bootstrap.sql"]
    },
    {
      "id": "M00.002",
      "anchor": "m00-002",
      "depends_on": ["COMMAND.REPLAY", "M00.001"],
      "code_paths": ["src/core/soma/db/migrations/00/002_command_replay.sql"]
    },
    {
      "id": "M00.003",
      "anchor": "m00-003",
      "depends_on": ["AUDIT.APPEND_ONLY", "M00.002"],
      "code_paths": ["src/core/soma/db/migrations/00/003_audit.sql"]
    },
    {
      "id": "M00.004",
      "anchor": "m00-004",
      "depends_on": ["JOBS.COORDINATOR", "M00.003"],
      "code_paths": ["src/core/soma/db/migrations/00/004_durable_jobs.sql"]
    },
    {
      "id": "M00.005",
      "anchor": "m00-005",
      "depends_on": ["WORKING_COPY.STORE", "UI.WORKING_COPY", "M00.006"],
      "code_paths": ["src/core/soma/db/migrations/00/005_working_copies.sql"]
    },
    {
      "id": "M00.006",
      "anchor": "m00-006",
      "depends_on": ["AUTH.LOCAL_ADMIN", "M00.004"],
      "code_paths": ["src/core/soma/db/migrations/00/006_local_admin_auth.sql"]
    }
  ],
  "tags": ["foundation", "migration", "persistence"]
}
-->

# Foundation schema

These are the current development migration allocations. Because the development database is disposable, the SQL may be revised before release; IDs remain owner-scoped and the manifest is the only execution-order authority. The planned implementation order is M00.001 -> M00.002 -> M00.003 -> M00.004 -> M00.006 -> M00.005; numeric identity does not imply execution order.

<a id="m00-001"></a>
## M00.001 — Bootstrap and migration ledger

Creates the minimum schema needed to identify applied migrations safely.

### `instance_metadata`

- `singleton INTEGER PRIMARY KEY CHECK(singleton = 1)`.
- `data_instance_id TEXT NOT NULL UNIQUE` — canonical UUIDv4 matching the owned instance identity, persisted during bootstrap and retained across ordinary reopen.
- `created_at_utc INTEGER NOT NULL` — canonical UTC whole seconds.

The runner inserts this row in the bootstrap transaction. Persistence/snapshot verification requires exactly this singleton and rejects a mismatched instance. This is technical data identity, not an operator or domain identity.

### `schema_migrations`

- `migration_id TEXT PRIMARY KEY` — exact owner migration ID such as `M00.001`.
- `owner_scope TEXT NOT NULL` — two-digit scope.
- `content_sha256 TEXT NOT NULL` — lowercase SHA-256 of the exact normalized executable SQL bytes declared by the manifest.
- `applied_at_utc INTEGER NOT NULL` — canonical UTC whole seconds.
- `application_version TEXT NOT NULL` — build/application version that applied it.

Rules:

- One row is inserted only in the same governed migration transaction that successfully applies that migration.
- Existing row hash/owner mismatch is drift and blocks readiness.
- The runner never repairs/relabels ledger rows silently.
- The ledger is technical schema history, not domain/audit evidence.

<a id="m00-002"></a>
## M00.002 — Exact command replay

Creates immutable command identity/result persistence used by COMMAND.REPLAY.

### `command_receipts`

- `command_id TEXT PRIMARY KEY` — canonical UUIDv4.
- `command_type TEXT NOT NULL`.
- `request_sha256 TEXT NOT NULL` — canonical request identity.
- `correlation_id TEXT NULL`.
- `committed_at_utc INTEGER NOT NULL` — canonical UTC whole seconds.

### `command_receipt_results`

- `command_id TEXT PRIMARY KEY REFERENCES command_receipts(command_id)`.
- `result_schema TEXT NOT NULL`.
- `result_version INTEGER NOT NULL`.
- `result_json TEXT NOT NULL` — exact canonical versioned result.
- `result_sha256 TEXT NOT NULL`.
- `result_bytes INTEGER NOT NULL CHECK(result_bytes >= 0)`.

Rules:

- Never-before-seen command inserts receipt before dependent result/audit rows inside the caller UnitOfWork.
- Exactly one immutable result exists for a committed command that uses Foundation replay.
- No UPDATE/DELETE repository surface is exposed for committed replay identity/result.
- Replay verifies type + request hash + stored-result integrity before returning it.

<a id="m00-003"></a>
## M00.003 — Append-only audit

Creates typed immutable evidence storage used by AUDIT.APPEND_ONLY.

### `audit_events`

Required columns include:

- `audit_event_id TEXT PRIMARY KEY`.
- `action_type TEXT NOT NULL`, `action_version INTEGER NOT NULL`.
- `actor_kind TEXT NOT NULL`, `actor_id TEXT NULL`.
- `target_type TEXT NOT NULL`, `target_id TEXT NULL`.
- `command_id TEXT NOT NULL REFERENCES command_receipts(command_id)`.
- `correlation_id TEXT NULL`, `job_id TEXT NULL`.
- `payload_schema TEXT NOT NULL`, `payload_version INTEGER NOT NULL`.
- `payload_json TEXT NOT NULL`, `payload_sha256 TEXT NOT NULL`, `payload_bytes INTEGER NOT NULL`.
- `recorded_at_utc INTEGER NOT NULL`.

### `audit_event_results`

- `audit_event_id TEXT NOT NULL REFERENCES audit_events(audit_event_id)`.
- `ordinal INTEGER NOT NULL CHECK(ordinal >= 0)`.
- `result_type TEXT NOT NULL`.
- `result_id TEXT NOT NULL`.
- Primary key: `(audit_event_id, ordinal)`.

Rules:

- Database triggers reject UPDATE and DELETE on both audit tables.
- Repository exposes append/read only.
- Result ordinals are deterministic and bounded by the registered action contract.
- Corrections append new audit identity and never rewrite prior bytes.

<a id="m00-004"></a>
## M00.004 — Durable jobs

Creates Foundation technical job coordination state. Domain/workflow meaning remains in registered owner contracts.

### `durable_jobs`

Includes:

- `job_id TEXT PRIMARY KEY`.
- `job_type TEXT NOT NULL`, `contract_version INTEGER NOT NULL`.
- `state TEXT NOT NULL` constrained to Foundation technical job states.
- `payload_json TEXT NOT NULL`, `payload_sha256 TEXT NOT NULL`.
- `dedupe_sha256 TEXT NULL`.
- `checkpoint_json TEXT NULL`, `checkpoint_sha256 TEXT NULL`.
- `attempt_count INTEGER NOT NULL DEFAULT 0`.
- `claimed_run_id TEXT NULL`, `claim_started_at_utc INTEGER NULL`.
- `next_attempt_at_utc INTEGER NULL`, `last_error_code TEXT NULL`.
- `correlation_id TEXT NULL`.
- `created_at_utc INTEGER NOT NULL`, `updated_at_utc INTEGER NOT NULL`.

### `job_attempts`

Includes exact `job_id`, `attempt_ordinal`, `run_id`, start/finish UTC, and bounded terminal outcome/error identity. Primary key is `(job_id, attempt_ordinal)`.

Rules:

- Active/coalescing uniqueness is indexed by exact registered job type/version + semantic dedupe hash for the contract's active states.
- Claim/checkpoint/complete/fail/cancel always revalidate the complete current claim tuple.
- Raw exception/provider text and raw semantic dedupe keys are not persisted merely for coordination.
- Unknown persisted job type/version is never guessed.

<a id="m00-005"></a>
## M00.005 — Recoverable UI working copies

Creates the shared recoverable working-copy mechanism without owning any feature's accepted domain data.

### `ui_working_copies`

Includes:

- `working_copy_id TEXT PRIMARY KEY`.
- `contract_id TEXT NOT NULL`, `contract_version INTEGER NOT NULL`.
- `target_type TEXT NOT NULL`, `target_id TEXT NOT NULL`, `scope_key TEXT NOT NULL`.
- `base_revision TEXT NOT NULL`.
- `draft_json TEXT NOT NULL`, `draft_sha256 TEXT NOT NULL`, `draft_bytes INTEGER NOT NULL` - canonical recovery envelope containing the closed owner draft and sorted registered dirty paths.
- `generation INTEGER NOT NULL CHECK(generation >= 1)` - exact checkpoint concurrency identity; changed content increments it, identical content preserves it.
- `created_at_utc INTEGER NOT NULL`, `updated_at_utc INTEGER NOT NULL`, `expires_at_utc INTEGER NOT NULL`.
- Unique active identity: `(contract_id, contract_version, target_type, target_id, scope_key)`.

Rules:

- Working-copy bytes are never accepted domain truth.
- Only statically registered owner contracts may checkpoint/restore a copy.
- A restored copy retains its original base revision and must pass owner conflict review before accepted save.
- Expiry/pruning removes only working-copy technical state; it never deletes accepted owner records.
- Initial shared bounds remain 256 active recoverable copies per installation, 262144 canonical draft bytes per copy, 7-day expiry, 5-second idle checkpoint delay, minimum 30 seconds between successful checkpoints, and pruning batches of at most 100.

<a id="m00-006"></a>
## M00.006 — Local Administrator credential

Creates the minimal singleton credential authority for AUTH.LOCAL_ADMIN. It does not create a profile, display name, settings record, or alternate user/account model.

### `local_admin_credentials`

- `singleton_key INTEGER PRIMARY KEY CHECK(singleton_key = 1)`.
- `actor_id TEXT NOT NULL UNIQUE` — stable canonical Foundation technical UUID created once during first-run setup.
- `password_phc TEXT NOT NULL` — Argon2id PHC verifier only; raw password is never persisted.
- `credential_version INTEGER NOT NULL DEFAULT 1 CHECK(credential_version >= 1)`.
- `created_at_utc INTEGER NOT NULL` — canonical UTC whole seconds.
- `updated_at_utc INTEGER NOT NULL` — canonical UTC whole seconds.

Rules:

- A freshly migrated development database contains the table but zero rows; this means `setup_required`.
- First-run setup may insert exactly one row with `singleton_key=1`; a second setup attempt is rejected rather than replacing credentials.
- Login reads the single verifier and never writes successful/failed attempt history to this table.
- Authentication throttle state and browser sessions are run-memory state, not durable account lockout.
- Password/profile management added later may update this row only through an explicit governing contract; Foundation setup/login never edits it after successful creation.
- The PHC/verifier, raw password, and confirmation never appear in audit payloads, command replay bodies/results, diagnostics, or support exports.
