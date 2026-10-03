<!-- soma-meta
{
  "version": 1,
  "id": "LLD-00-BACKEND",
  "scope": "00",
  "items": [
    {
      "id": "RUNTIME.INSTANCE",
      "anchor": "runtime-instance",
      "code_paths": ["src/core/soma/runtime/", "src/core/soma/foundation/persistence/"]
    },
    {
      "id": "RUNTIME.TRUSTED_CONTROL",
      "anchor": "runtime-trusted-control",
      "depends_on": ["RUNTIME.INSTANCE"],
      "code_paths": ["src/core/soma/runtime/control.py", "src/core/soma/runtime/trust.py"]
    },
    {
      "id": "DEV.SOURCE_LAUNCHERS",
      "anchor": "dev-source-launchers",
      "depends_on": ["RUNTIME.TRUSTED_CONTROL", "PERSISTENCE.CONNECTION", "DIAGNOSTICS.OPERATOR_LOGS"],
      "code_paths": ["soma_setup.bat", "soma_run.bat", "soma_run_console.bat", "soma_stop.bat", "tools/source_launcher.py"]
    },
    {
      "id": "TIME.UTC",
      "anchor": "time-utc",
      "code_paths": ["src/core/soma/foundation/time/"]
    },
    {
      "id": "SECURITY.LIVE_DATA_KEY",
      "anchor": "security-live-data-key",
      "depends_on": ["RUNTIME.INSTANCE"],
      "code_paths": ["src/core/soma/foundation/security/"]
    },
    {
      "id": "PERSISTENCE.CONNECTION",
      "anchor": "persistence-connection",
      "depends_on": ["RUNTIME.INSTANCE", "SECURITY.LIVE_DATA_KEY"],
      "code_paths": ["src/core/soma/foundation/persistence/"]
    },
    {
      "id": "TX.UOW",
      "anchor": "tx-uow",
      "depends_on": ["PERSISTENCE.CONNECTION"],
      "code_paths": ["src/core/soma/foundation/transactions/"]
    },
    {
      "id": "MIGRATION.MANIFEST",
      "anchor": "migration-manifest",
      "depends_on": ["PERSISTENCE.CONNECTION"],
      "code_paths": ["src/core/soma/db/migrations/manifest.json", "src/core/soma/foundation/persistence/"]
    },
    {
      "id": "DEV.DB_RESET",
      "anchor": "dev-db-reset",
      "depends_on": ["RUNTIME.INSTANCE", "MIGRATION.MANIFEST"],
      "code_paths": ["src/core/soma/foundation/persistence/", "src/core/soma/db/"]
    },
    {
      "id": "SERIALIZATION.STRICT_JSON",
      "anchor": "serialization-strict-json",
      "code_paths": ["src/core/soma/foundation/"]
    },
    {
      "id": "COMMAND.REPLAY",
      "anchor": "command-replay",
      "depends_on": ["TX.UOW", "SERIALIZATION.STRICT_JSON"],
      "code_paths": ["src/core/soma/foundation/transactions/", "src/core/soma/foundation/persistence/"]
    },
    {
      "id": "JOBS.COORDINATOR",
      "anchor": "jobs-coordinator",
      "depends_on": ["TX.UOW", "SERIALIZATION.STRICT_JSON"],
      "code_paths": ["src/core/soma/foundation/jobs/"]
    },
    {
      "id": "DIAGNOSTICS.SAFE",
      "anchor": "diagnostics-safe",
      "code_paths": ["src/core/soma/foundation/diagnostics/"]
    },
    {
      "id": "DIAGNOSTICS.OPERATOR_LOGS",
      "anchor": "diagnostics-operator-logs",
      "depends_on": ["DIAGNOSTICS.SAFE", "RUNTIME.INSTANCE"],
      "code_paths": ["src/core/soma/foundation/diagnostics/runtime_logs.py"]
    },
    {
      "id": "CONTRACT.SOURCE",
      "anchor": "contract-source",
      "code_paths": ["docs/LLD/00/contracts/", "src/core/soma/"]
    },
    {
      "id": "TOOLING.IMPACT",
      "anchor": "tooling-impact",
      "depends_on": ["SERIALIZATION.STRICT_JSON"],
      "code_paths": ["tools/"]
    }
  ],
  "tags": ["foundation", "system-plane"]
}
-->

# Foundation backend

<a id="runtime-instance"></a>
## RUNTIME.INSTANCE

**Trigger/input:** SOMA host startup, shutdown, or an operation requiring the authoritative development instance.

**Result:** Resolve one canonical local SOMA instance, its runtime identity, database location, and owned runtime resources before authoritative access.

**Rules:**
- One running authoritative instance owns its configured database at a time.
- The initial Windows canonical instance root is the LocalAppData known folder plus `SOMA/instance-v1`; source checkout location never becomes the data root.
- Runtime identity and database paths are configuration-derived, never inferred from the current working directory.
- Startup must prove ownership before migrations or authoritative reads/writes.
- Ordinary startup never destroys or resets data.

**Failure:** Ambiguous, missing, stale, or conflicting ownership blocks authoritative startup with a stable diagnostic result.

**Side effects:** Runtime registration/cleanup only; no business mutation.

Reuse provenance: Beta LLD-01 runtime host and canonical data-instance ownership.

<a id="runtime-trusted-control"></a>
## RUNTIME.TRUSTED_CONTROL

**Trigger/input:** A local launcher, tray action, or operator-control request needs to discover, open, inspect, or stop the running SOMA host.

**Result:** Establish a fresh cryptographic/process-identity proof for exactly one current local run before treating it as controllable.

**Rules:**
- The host binds only to literal loopback `127.0.0.1` on an OS-selected port during development.
- Each run has a fresh UUID `run_id` and independent random 32-byte run-control secret.
- The run-control secret is CurrentUser-DPAPI protected in an owner-only runtime file; it never appears in the registry JSON, URL, browser state, audit, or diagnostics.
- The atomically published runtime registry contains exactly: registry version, canonical origin, PID, Windows process creation identity, `run_id`, protocol version, `data_instance_id`, relative protected-secret locator, and UTC publication time.
- A controller validates canonical path/ACL shape, literal loopback origin, live PID, exact process birth identity, expected SOMA/source interpreter image, protected secret, and an authenticated direct no-proxy/no-redirect `GET /api/v1/runtime/health`.
- Health identity must exactly match registry run/data/PID/birth/protocol values before the instance may be opened or controlled.
- `POST /api/v1/runtime/shutdown` requires the same fresh run-control proof and exact run identity.
- Browser session/CSRF credentials and run-control credentials are independent and never substitute for each other.
- Loopback reachability alone is never authentication.

**Failure:** Malformed, stale, foreign, PID-reused, redirected, proxy-routed, unauthenticated, or identity-mismatched runtime state fails closed. Unknown artifacts are preserved for inspection rather than blindly deleted or used as kill authority.

**Side effects:** Publication/cleanup of exact-owned runtime-control artifacts and authenticated host-control requests; no domain mutation.

Reuse provenance: Beta LLD-12 `RuntimeRegistryV2` and `TrustedLocalInstanceV1`.

<a id="dev-source-launchers"></a>
## DEV.SOURCE_LAUNCHERS

**Trigger/input:** Developer/operator invokes one of the repository-root Windows source buttons.

**Result:** Provide four stable, human-friendly development entry points backed by one launcher implementation:

| Entry point | Required behavior |
|---|---|
| `soma_setup.bat` | Create/reuse the repository-local development environment, install/verify declared development dependencies and native prerequisites, and validate the source checkout. It does not fabricate runtime state, start SOMA, reset the database, or silently substitute insecure dependencies. |
| `soma_run.bat` | Reuse and open an already verified READY instance, or start SOMA detached, capture an owner-only run log, wait up to 30 seconds for authenticated READY, then open only the verified origin. |
| `soma_run_console.bat` | Start the real SOMA host in the foreground, mirror sanitized runtime logging to the terminal, print the verified READY origin, and perform graceful owned shutdown on Ctrl+C. If a verified instance already runs, report/open that instance instead of creating a second host. |
| `soma_stop.bat` | Freshly verify the current run, request graceful authenticated shutdown, and wait up to 10 seconds. No valid running instance is an idempotent success. Timeout reports failure and does not kill by process name, stale PID, or port alone. |

**Rules:**
- The BAT files are intentionally thin adapters. Runtime/setup/trust logic lives in `tools/source_launcher.py` and shared core providers; do not duplicate security logic across scripts.
- Runtime actions never install or update dependencies. Environment mutation belongs only to explicit setup.
- Source launchers operate against the canonical development instance, not a database under the checkout.
- Concurrent run attempts converge on the single instance lock; the losing launcher waits for/verifies the winning host rather than creating a second authoritative instance.
- Setup is rerunnable and preserves unrelated checkout/user data.
- Source launchers are development controls, not the future production installer contract; production shortcuts may later call the same trusted control capabilities.

**Failure:** Missing/unsupported environment, unsafe checkout/runtime path, failed native dependency verification, startup crash, READY timeout, or trust failure produces a nonzero exit and an actionable diagnostic/log location. No fake success or plaintext fallback is allowed.

**Side effects:** Setup may create/update the repository-local environment. Run/console/stop operate the local runtime through RUNTIME.TRUSTED_CONTROL.

Reuse provenance: Beta implementation `fbe3821ac0b52802ba8265f979590e75c3ac1209` source launchers and `tools/source_launcher.py`, revised into the new scope-00 architecture.

<a id="time-utc"></a>
## TIME.UTC

**Trigger/input:** Creation or normalization of an application chronology value.

**Result:** Core stores and transports authoritative application chronology as UTC with an explicit unit and representation.

**Rules:**
- Application chronology uses UTC. A local timezone is presentation context, not authoritative stored chronology.
- Every numeric epoch field states its unit in the field name or contract. Whole-second and millisecond values are never interchangeable.
- Source/provider timestamps may retain source precision/provenance, but do not replace normalized application chronology.
- Core never formats an operator-facing local date/time string.

**Failure:** Missing timezone where normalization is required, invalid instant, overflow, or unit ambiguity fails validation rather than guessing.

**Side effects:** none.

Reuse provenance: Beta LLD-01 chronology rules plus LLD-09 chronology refinement.

<a id="security-live-data-key"></a>
## SECURITY.LIVE_DATA_KEY

**Trigger/input:** Creation or opening of the authoritative local database.

**Result:** Supply the persistence layer with the installation's protected live database key without exposing it to domain code.

**Rules:**
- Use a randomly generated 32-byte live DEK, not an operator password/passphrase, as the SQLCipher raw key.
- On Windows, protect installation secret material with CurrentUser DPAPI; never silently fall back to plaintext.
- Secret material is never logged, audited, serialized into command results, or exposed through ordinary API responses.
- Operator authentication/session behavior is a separate concern and must not collapse into the database-key boundary.

**Failure:** Key creation, protection, unprotection, or verification failure blocks protected database readiness.

**Side effects:** creation/update of owned protected secret material only when explicitly required.

Reuse provenance: Beta LLD-12 live-data key and DPAPI boundaries.

<a id="persistence-connection"></a>
## PERSISTENCE.CONNECTION

**Trigger/input:** Foundation requests an authoritative database connection.

**Result:** Return a verified SQLCipher connection for the canonical instance.

**Rules:**
- SQLCipher is mandatory for authoritative production-format storage; development does not silently substitute plaintext SQLite.
- Apply the raw live DEK before schema access.
- Verify the expected SQLCipher/provider/cipher profile before migrations or authoritative reads.
- Foreign keys are enabled on every authoritative connection.
- Connection lifetime is explicit; failed begin/open paths clean up resources.
- Repositories receive connection/transaction context; they do not create independent commits.

**Failure:** Key/cipher/provider mismatch, integrity failure, unsupported profile, or database-open failure blocks authoritative access.

**Side effects:** connection/session setup only.

Reuse provenance: Beta LLD-01 connection factory and LLD-12 SQLCipher profile.

<a id="tx-uow"></a>
## TX.UOW

**Trigger/input:** An authoritative application command begins.

**Result:** Execute the command and all participating owner/adaptor writes inside exactly one outer UnitOfWork.

**Rules:**
- The application operation owns the transaction.
- Nested commits/transactions are prohibited.
- Participants use the caller's transaction context.
- Operator interaction, expensive parsing, file/network work, and long-running background computation stay outside write transactions.
- Commit publishes the authoritative state, audit/receipt/result work required by that command atomically.

**Failure:** Any required participant/commit failure rolls back the whole authoritative mutation and reports no false success.

**Side effects:** bounded authoritative transaction.

Reuse provenance: Beta LLD-01 one-outer-UoW invariant.

<a id="migration-manifest"></a>
## MIGRATION.MANIFEST

**Trigger/input:** Startup/status/reset requests schema construction or verification.

**Result:** One manifest declares the current migration execution order, owner IDs, dependencies, executable paths, and content hashes.

**Rules:**
- Migration identity is owner-scoped: `MNN.KKK`.
- Executable SQL exists once under `src/core/soma/db/migrations/NN/`.
- Directory/file lexical order never defines execution order.
- DDL ownership follows schema ownership; cross-owner changes are split when practical and linked by dependencies.
- During development, migrations may be rewritten/reordered when the disposable database is rebuilt.
- Manifest, owning LLD item, and executable SQL change together.

**Failure:** Missing file, duplicate ID, dependency cycle, hash mismatch, ledger/schema drift, or future unknown migration blocks application of migrations.

**Side effects:** governed schema mutation and migration-ledger advancement.

Reuse provenance: Beta migration manifest lessons; new owner-scoped identity replaces global historical numbering.

<a id="dev-db-reset"></a>
## DEV.DB_RESET

**Trigger/input:** Explicit development reset operation for the configured SOMA development instance.

**Result:** Stop/quiesce that instance, destroy only its disposable database state, recreate from the current manifest, and apply the declared development seed.

**Rules:**
- Reset is never implicit in normal startup.
- Resolve and verify the target instance before deletion.
- Reset affects only the designated development instance.
- The active implementation goal sets `reset_db: true` whenever its schema change requires this operation.
- No Alpha/Beta record migration is performed in the current development phase.

**Failure:** Unproven target identity, active unquiesced runtime, migration failure, or seed failure stops the reset and reports the incomplete stage.

**Side effects:** destructive recreation of the designated development database.

<a id="serialization-strict-json"></a>
## SERIALIZATION.STRICT_JSON

**Trigger/input:** Foundation serializes or parses a machine contract, command identity, persisted result, job payload/checkpoint, or metadata document.

**Result:** Canonical, deterministic JSON suitable for hashing, replay identity, and strict validation.

**Rules:**
- Reject duplicate object keys, unsupported values, and schema-invalid structures.
- Canonicalization is deterministic for equivalent accepted values.
- Tuple/list and other collection forms are normalized only when the owning contract explicitly allows them.
- Unknown fields fail where a closed contract is required.

**Failure:** Invalid or ambiguous content fails closed; do not coerce into a different semantic value.

**Side effects:** none.

Reuse provenance: Beta LLD-01 strict JSON and audit findings around incomplete container validation.

<a id="command-replay"></a>
## COMMAND.REPLAY

**Trigger/input:** Authoritative command carrying command identity and canonical request identity.

**Result:** Execute a never-seen command once, or return the exact immutable stored result of the matching committed command.

**Rules:**
- Replay lookup occurs before owner reads/preparation.
- A committed command is never re-executed merely to reconstruct a result.
- Receipt, canonical request identity, exact result, audit work, and domain mutation commit in the same UnitOfWork when required.
- Reuse of a command ID with a different command type/request identity fails closed.
- If an exact historical result cannot be proven, return an explicit unavailable result; never fabricate from current state.

**Failure:** identity mismatch, corrupted stored result, unavailable exact legacy result, or persistence failure returns a stable error without rerun.

**Side effects:** first execution may mutate through the owning application operation; replay itself does not.

Reuse provenance: Beta LLD-01 exact command replay invariant.

<a id="jobs-coordinator"></a>
## JOBS.COORDINATOR

**Trigger/input:** Application module enqueues or operates a registered durable background job contract.

**Result:** Foundation provides durable enqueue, dedupe/coalescing identity, claim, checkpoint, complete/fail, cancellation, shutdown, and recovery mechanics.

**Rules:**
- Foundation owns job mechanics, never domain-specific job meaning.
- Workflow modules register versioned job contracts and invoke owning application operations for accepted domain mutations.
- Claims/checkpoints/completion/failure are bounded technical transactions.
- Current-claim assertions and checkpoint/terminal transition occur atomically where required.
- Restart recovery resumes only from registered durable checkpoints; arbitrary in-memory position is never authoritative.
- Unknown/stale claim identity fails closed.

**Failure:** unknown contract, malformed payload/checkpoint, claim mismatch, ambiguous dedupe match, or invalid recovery state prevents handler execution.

**Side effects:** durable technical job state; domain changes only through owner commands.

Reuse provenance: Beta LLD-01 durable-job coordinator and pre-LLD-08 closure invariants.

<a id="diagnostics-safe"></a>
## DIAGNOSTICS.SAFE

**Trigger/input:** Runtime/component emits diagnostic or support information.

**Result:** Record operationally useful diagnostics without leaking secret material or silently changing authoritative behavior.

**Rules:**
- Diagnostics are non-authoritative.
- Sanitization happens before persistence/export.
- Known secrets, credentials, live keys, CSRF/session/run-control material, and sensitive raw payloads are excluded.
- Sanitizer uncertainty omits the field/record rather than emitting raw fallback.
- Diagnostic write failure may lose diagnostics but does not rewrite a successful domain result.

**Failure:** unsafe/unsanitizable content is omitted and locally noted when possible.

**Side effects:** diagnostic output only.

Reuse provenance: Beta LLD-12 diagnostic sanitizer boundary.

<a id="diagnostics-operator-logs"></a>
## DIAGNOSTICS.OPERATOR_LOGS

**Trigger/input:** SOMA starts, runs, fails, or the operator requests current diagnostic logs.

**Result:** Maintain a predictable per-run sanitized log stream that is available from console mode and the system tray without searching the checkout or exposing secrets.

**Rules:**
- Runtime logs live under the canonical instance `diagnostics/` directory, never under the source checkout.
- Every run log is bound to its `run_id`; startup and runtime events share the same sanitized logging pipeline.
- Console mode mirrors the same sanitized events to stdout/stderr; detached mode writes them to the owned run log.
- The current log path is discoverable through trusted runtime state, not guessed from newest filesystem timestamp alone.
- Retention is bounded to at most 20 runtime log files, each at most 10 MB. Rotation/deletion touches only closed diagnostics-owned runtime log files; the current log, support bundles, and operator-exported artifacts are never removed by this policy.
- Log timestamps use canonical UTC facts; presentation tools may additionally show operator-local time.
- Secrets prohibited by DIAGNOSTICS.SAFE remain prohibited even when console verbosity is enabled.

**Failure:** Log creation/rotation/access failure is visible to the launcher/tray and falls back to the safest available sanitized sink. Diagnostic failure does not change an otherwise valid domain result.

**Side effects:** Creation, rotation, and bounded cleanup of owned runtime log files.

Reuse provenance: Beta source-launcher owner-only startup logging plus LLD-12 diagnostic sanitization, with bounded retention added for the new application.

<a id="contract-source"></a>
## CONTRACT.SOURCE

**Trigger/input:** A runtime API/request/response contract is introduced or changed.

**Result:** One machine-readable authoritative contract definition drives or validates both core transport types and main consumer bindings.

**Rules:**
- Python and TypeScript do not independently invent equivalent DTOs.
- Provider owns field names, enum values, null meaning, units, identity, bounds, and version.
- Generated artifacts are outputs, not second authorities.
- Contract generation/validation is deterministic and runnable without network access.
- A behavior-changing contract edit updates the owning LLD item and affected implementation goal in the same iteration.

**Failure:** divergence between authority and generated/validated binding fails a focused check.

**Side effects:** generated/validated source only.

<a id="tooling-impact"></a>
## TOOLING.IMPACT

**Trigger/input:** Agent/human requests documentation validation or impact for repository changes relative to a Git baseline.

**Result:** Validate the SOMA metadata graph and report direct/indirect impacted IDs with explanation paths and mapping gaps.

**Rules:**
- Implement the parser and traversal rules in `docs/architecture.md`.
- Use baseline/current graph union when relationships are removed.
- Consider both old/new paths for moves.
- Report unmapped changed code explicitly.
- Sort output deterministically by stable ID.
- The tool reports impact; it does not rewrite documents automatically.

**Failure:** invalid metadata, unresolved IDs, duplicate IDs/anchors, illegal paths, or graph errors produce actionable failure and no misleading clean result.

**Side effects:** none unless an explicit generated index/output target is requested.
