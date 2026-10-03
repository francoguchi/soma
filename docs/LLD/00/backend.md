<!-- soma-meta
{
  "version": 1,
  "id": "LLD-00-BACKEND",
  "scope": "00",
  "items": [
    {
      "id": "RUNTIME.INSTANCE",
      "anchor": "runtime-instance",
      "depends_on": ["CONFIG.RUNTIME", "FS.SAFE"],
      "code_paths": ["src/core/soma/runtime/", "src/core/soma/foundation/persistence/"]
    },
    {
      "id": "RUNTIME.TRUSTED_CONTROL",
      "anchor": "runtime-trusted-control",
      "depends_on": ["RUNTIME.INSTANCE", "RUNTIME.HEALTH", "SECURITY.LIVE_DATA_KEY"],
      "code_paths": ["src/core/soma/runtime/control.py", "src/core/soma/runtime/trust.py"]
    },
    {
      "id": "DEV.SOURCE_LAUNCHERS",
      "anchor": "dev-source-launchers",
      "depends_on": ["RUNTIME.TRUSTED_CONTROL", "RUNTIME.LIFECYCLE", "PERSISTENCE.CONNECTION", "DIAGNOSTICS.OPERATOR_LOGS", "BUILD.IDENTITY"],
      "code_paths": ["soma_setup.bat", "soma_run.bat", "soma_run_console.bat", "soma_stop.bat", "soma_reset_dev.bat", "tools/source_launcher.py"]
    },
    {
      "id": "PLATFORM.BASELINE",
      "anchor": "platform-baseline",
      "code_paths": ["pyproject.toml", "src/main/package.json"]
    },
    {
      "id": "CONFIG.RUNTIME",
      "anchor": "config-runtime",
      "depends_on": ["FS.SAFE"],
      "code_paths": ["src/core/soma/foundation/config/"]
    },
    {
      "id": "BUILD.IDENTITY",
      "anchor": "build-identity",
      "code_paths": ["src/core/soma/foundation/build/", "src/main/shared/build/"]
    },
    {
      "id": "IDENTITY.UUID",
      "anchor": "identity-uuid",
      "code_paths": ["src/core/soma/foundation/identity/"]
    },
    {
      "id": "TRACE.CORRELATION",
      "anchor": "trace-correlation",
      "depends_on": ["IDENTITY.UUID"],
      "code_paths": ["src/core/soma/foundation/context/"]
    },
    {
      "id": "ERROR.CONTRACT",
      "anchor": "error-contract",
      "depends_on": ["TRACE.CORRELATION"],
      "code_paths": ["src/core/soma/foundation/errors/", "docs/LLD/00/contracts/"]
    },
    {
      "id": "TIME.UTC",
      "anchor": "time-utc",
      "code_paths": ["src/core/soma/foundation/time/"]
    },
    {
      "id": "TIME.MONOTONIC",
      "anchor": "time-monotonic",
      "code_paths": ["src/core/soma/foundation/time/"]
    },
    {
      "id": "FS.SAFE",
      "anchor": "fs-safe",
      "code_paths": ["src/core/soma/foundation/filesystem/"]
    },
    {
      "id": "FS.TEMP",
      "anchor": "fs-temp",
      "depends_on": ["FS.SAFE", "RUNTIME.INSTANCE"],
      "code_paths": ["src/core/soma/foundation/filesystem/"]
    },
    {
      "id": "RUNTIME.LIFECYCLE",
      "anchor": "runtime-lifecycle",
      "depends_on": ["RUNTIME.INSTANCE", "TIME.MONOTONIC", "BUILD.IDENTITY", "PERSISTENCE.SCHEMA_VERIFY", "STATIC.ASSETS"],
      "code_paths": ["src/core/soma/runtime/host.py", "src/core/soma/runtime/lifecycle.py"]
    },
    {
      "id": "CAPABILITY.REGISTRY",
      "anchor": "capability-registry",
      "depends_on": ["BUILD.IDENTITY"],
      "code_paths": ["src/core/soma/composition/capabilities.py"]
    },
    {
      "id": "RUNTIME.HEALTH",
      "anchor": "runtime-health",
      "depends_on": ["RUNTIME.LIFECYCLE", "CAPABILITY.REGISTRY", "BUILD.IDENTITY"],
      "code_paths": ["src/core/soma/runtime/health.py", "docs/LLD/00/contracts/"]
    },
    {
      "id": "RUNTIME.SHUTDOWN",
      "anchor": "runtime-shutdown",
      "depends_on": ["RUNTIME.LIFECYCLE", "JOBS.COORDINATOR", "PERSISTENCE.CONNECTION"],
      "code_paths": ["src/core/soma/runtime/host.py", "src/core/soma/runtime/control.py"]
    },
    {
      "id": "SECURITY.LIVE_DATA_KEY",
      "anchor": "security-live-data-key",
      "depends_on": ["RUNTIME.INSTANCE"],
      "code_paths": ["src/core/soma/foundation/security/"]
    },
    {
      "id": "SECURITY.BROWSER_SESSION",
      "anchor": "security-browser-session",
      "depends_on": ["RUNTIME.INSTANCE", "TIME.MONOTONIC", "IDENTITY.UUID"],
      "code_paths": ["src/core/soma/foundation/security/browser_session.py", "src/core/soma/transport/security.py"]
    },
    {
      "id": "AUTH.LOCAL_ADMIN",
      "anchor": "auth-local-admin",
      "depends_on": ["PERSISTENCE.CONNECTION", "TX.UOW", "SECURITY.BROWSER_SESSION", "TIME.MONOTONIC", "IDENTITY.UUID"],
      "code_paths": ["src/core/soma/foundation/security/local_admin.py", "src/core/soma/transport/auth.py"]
    },
    {
      "id": "SECURITY.DELIBERATE_PROOF",
      "anchor": "security-deliberate-proof",
      "depends_on": ["SECURITY.BROWSER_SESSION", "TIME.MONOTONIC", "IDENTITY.UUID", "TX.UOW"],
      "code_paths": ["src/core/soma/foundation/security/deliberate_action.py"]
    },
    {
      "id": "PERSISTENCE.CONNECTION",
      "anchor": "persistence-connection",
      "depends_on": ["RUNTIME.INSTANCE", "SECURITY.LIVE_DATA_KEY"],
      "code_paths": ["src/core/soma/foundation/persistence/"]
    },
    {
      "id": "PERSISTENCE.READ_SNAPSHOT",
      "anchor": "persistence-read-snapshot",
      "depends_on": ["PERSISTENCE.CONNECTION"],
      "code_paths": ["src/core/soma/foundation/persistence/read_snapshot.py"]
    },
    {
      "id": "PERSISTENCE.SCHEMA_VERIFY",
      "anchor": "persistence-schema-verify",
      "depends_on": ["PERSISTENCE.CONNECTION", "MIGRATION.MANIFEST"],
      "code_paths": ["src/core/soma/foundation/persistence/schema_verify.py", "src/core/soma/db/schema_manifest.json"]
    },
    {
      "id": "MIGRATION.STATUS",
      "anchor": "migration-status",
      "depends_on": ["MIGRATION.MANIFEST", "PERSISTENCE.SCHEMA_VERIFY", "RUNTIME.TRUSTED_CONTROL"],
      "code_paths": ["src/core/soma/foundation/persistence/migration_status.py"]
    },
    {
      "id": "PERSISTENCE.SNAPSHOT",
      "anchor": "persistence-snapshot",
      "depends_on": ["PERSISTENCE.CONNECTION", "FS.SAFE", "RUNTIME.INSTANCE"],
      "code_paths": ["src/core/soma/foundation/persistence/snapshot.py"]
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
      "depends_on": ["RUNTIME.INSTANCE", "MIGRATION.MANIFEST", "DEV.SEED"],
      "code_paths": ["src/core/soma/foundation/persistence/", "src/core/soma/db/"]
    },
    {
      "id": "SERIALIZATION.STRICT_JSON",
      "anchor": "serialization-strict-json",
      "code_paths": ["src/core/soma/foundation/"]
    },
    {
      "id": "AUDIT.APPEND_ONLY",
      "anchor": "audit-append-only",
      "depends_on": ["TX.UOW", "SERIALIZATION.STRICT_JSON", "TRACE.CORRELATION", "TIME.UTC"],
      "code_paths": ["src/core/soma/foundation/audit/"]
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
      "id": "JOBS.EXECUTION",
      "anchor": "jobs-execution",
      "depends_on": ["JOBS.COORDINATOR", "RUNTIME.LIFECYCLE", "TIME.MONOTONIC"],
      "code_paths": ["src/core/soma/foundation/jobs/executor.py", "src/core/soma/runtime/workers.py"]
    },
    {
      "id": "DEV.SEED",
      "anchor": "dev-seed",
      "depends_on": ["MIGRATION.MANIFEST", "TX.UOW"],
      "code_paths": ["src/core/soma/foundation/development/seed.py"]
    },
    {
      "id": "QUERY.PAGE",
      "anchor": "query-page",
      "depends_on": ["SERIALIZATION.STRICT_JSON"],
      "code_paths": ["src/core/soma/foundation/query/"]
    },
    {
      "id": "STATIC.ASSETS",
      "anchor": "static-assets",
      "depends_on": ["BUILD.IDENTITY", "FS.SAFE"],
      "code_paths": ["src/core/soma/runtime/static_assets.py", "src/main/"]
    },
    {
      "id": "TEST.SEAMS",
      "anchor": "test-seams",
      "depends_on": ["TIME.UTC", "TIME.MONOTONIC", "IDENTITY.UUID", "FS.SAFE"],
      "code_paths": ["tests/core/foundation/", "src/core/soma/foundation/testing/"]
    },
    {
      "id": "WORKING_COPY.STORE",
      "anchor": "working-copy-store",
      "depends_on": ["TX.UOW", "SERIALIZATION.STRICT_JSON", "TIME.UTC", "COMMAND.REPLAY"],
      "code_paths": ["src/core/soma/foundation/working_copy/"]
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

<a id="platform-baseline"></a>
## PLATFORM.BASELINE

**Trigger/input:** SOMA source setup, build, or runtime composition.

**Result:** Use one pinned local-first technology baseline that is compatible with the proven Beta architecture while remaining replaceable through an explicit LLD revision.

**Rules:**
- Core runtime is CPython x64 on supported Windows; initial supported interpreter lines are Python 3.13 and 3.14.
- Local HTTP host uses Starlette + Uvicorn as a single-worker programmatic ASGI host bound only to `127.0.0.1`; proxy headers, reload, server banner, and websockets are disabled unless a later LLD item proves a need.
- Authoritative persistence uses the `sqlcipher3` DB-API-compatible provider with SQLCipher 4.17.0 semantics, raw bound-parameter SQL, no ORM, and a SOMA-owned migration runner.
- Main is a prebuilt static React + TypeScript SPA built with Vite; Node is development/build-only and is not required by a running SOMA instance.
- Local Administrator password verification uses Argon2id through `argon2-cffi`; the accepted initial profile is version 19, 65536 KiB memory, time cost 3, parallelism 4, 16-byte random salt, and 32-byte output.
- No Electron, SSR, React Server Components, external CDN modules/styles/fonts, runtime package downloads, `eval`, or dynamically downloaded executable dependencies.
- Exact dependency versions/hashes live in dependency/build metadata rather than being duplicated in behavioral prose.

**Failure:** Unsupported interpreter/platform, unavailable pinned dependency, or runtime requirement that violates this baseline blocks setup/build rather than silently changing architecture.

**Side effects:** none.

Reuse provenance: Beta LLD-01/10/12 technology baselines.

<a id="config-runtime"></a>
## CONFIG.RUNTIME

**Trigger/input:** Composition, launcher, runtime, persistence, diagnostics, or tests request installation/runtime configuration.

**Result:** Return one validated immutable runtime configuration object and canonical owned paths.

**Rules:**
- Configuration discovery is centralized; modules do not independently read environment variables, current working directory, registry values, or LocalAppData.
- Initial source-development instance root is Windows KnownFolder LocalAppData + `SOMA/Development/instance-v1`; future packaged-release roots may differ without changing domain code.
- Owned relative roots include `data/`, `runtime/`, `diagnostics/`, `tmp/`, and `backups/`; feature-specific subpaths must remain beneath their declared owner root.
- Repository checkout paths are code/build inputs only and never become authoritative data-instance paths.
- Development overrides are explicit, validated, test-scoped/config-scoped, and cannot silently redirect an existing canonical instance.
- Configuration values that affect trust, storage, or contracts are resolved before application composition and then treated as immutable for that run.

**Failure:** Missing, conflicting, unsafe, unsupported, or path-escaping configuration blocks composition with ERROR.CONTRACT output.

**Side effects:** none.

<a id="build-identity"></a>
## BUILD.IDENTITY

**Trigger/input:** Host startup, diagnostics, API bootstrap, static asset verification, or support output requests build identity.

**Result:** Supply a non-secret immutable identity for the running application/build.

**Rules:**
- Expose application version, runtime protocol version, contract/schema generation identifiers, and source commit/build identity when available.
- A dirty/source build is identified honestly; it is never presented as a release-certified build.
- Build identity is consistent across runtime health, diagnostics, main bootstrap, and logs for one run.
- Missing optional source-control metadata does not prevent development startup; required protocol/schema identity does.

**Failure:** Contradictory required build/protocol metadata blocks readiness rather than publishing ambiguous identity.

**Side effects:** none.

<a id="identity-uuid"></a>
## IDENTITY.UUID

**Trigger/input:** Foundation needs a new technical identity such as command, correlation, run, job, audit, or temporary operation identity.

**Result:** Generate and validate lowercase canonical UUIDv4 technical identifiers.

**Rules:**
- Use OS-CSPRNG-backed UUID generation.
- Foundation technical IDs use one canonical textual representation.
- Domain-visible identifiers remain owned by their domain LLD and are not replaced by UUIDs merely for convenience.
- Tests may inject a deterministic generator through TEST.SEAMS.

**Failure:** Invalid externally supplied UUID text fails validation before authoritative work.

**Side effects:** none.

<a id="trace-correlation"></a>
## TRACE.CORRELATION

**Trigger/input:** Browser request, launcher operation, application command/query, durable job, or nested internal operation enters SOMA.

**Result:** Establish one bounded non-secret correlation context that can be carried through transport, application, logs, audit, jobs, and returned failures.

**Rules:**
- A missing external correlation ID causes SOMA to generate one; untrusted arbitrary values are not accepted as authoritative internal IDs without validation.
- Correlation propagates across synchronous boundaries and is copied explicitly into durable job/audit records when their contract supports it.
- Correlation is diagnostic linkage only; it never grants identity, authorization, replay, or transaction authority.
- Raw secrets/customer bodies are not added merely because correlation exists.

**Failure:** Invalid inbound correlation metadata is replaced or rejected according to the closed transport contract; it never becomes executable/log-injection content.

**Side effects:** context/log/audit metadata only.

<a id="error-contract"></a>
## ERROR.CONTRACT

**Trigger/input:** Any transport/application/foundation operation returns a handled failure across an ownership boundary.

**Result:** Produce one stable safe error envelope.

**Required shape:** `code`, bounded operator-safe `summary`, `recoverability`, optional `safe_next_action`, and `correlation_id`; field-level validation details may be added only by their closed contract.

**Rules:**
- Stable machine code is the API contract; HTTP status is transport mapping only.
- Raw SQL/Starlette/Uvicorn/OS/Python exception text, file paths, secrets, tokens, and unbounded provider text never cross the application boundary.
- Foundation defines common categories such as validation, unauthenticated, forbidden, not-found, stale/conflict, persistence, migration, readiness, busy/retry, integrity, and internal error.
- Domain scopes define domain-specific codes while preserving this envelope.
- Retryability/recoverability is explicit; UI does not infer it from HTTP status.

**Failure:** An unknown internal exception maps to bounded `INTERNAL_ERROR` with correlation; diagnostic classification may be retained safely out of band.

**Side effects:** diagnostic emission only where configured.

<a id="time-monotonic"></a>
## TIME.MONOTONIC

**Trigger/input:** SOMA measures an elapsed duration, timeout, idle/absolute session deadline, debounce, retry delay, hold duration, shutdown budget, or runtime interval.

**Result:** Measure elapsed time using a monotonic clock independent of wall-clock changes.

**Rules:**
- Python elapsed timing uses `time.monotonic_ns()` or an injected equivalent.
- Browser elapsed interaction timing uses `performance.now()`.
- Monotonic values are process-local measurements and are never stored as business chronology.
- TIME.UTC remains the only authoritative wall-clock chronology mechanism.
- Tests can inject deterministic monotonic clocks through TEST.SEAMS.

**Failure:** Unsupported/invalid timer configuration fails before the timed operation begins.

**Side effects:** none.

<a id="fs-safe"></a>
## FS.SAFE

**Trigger/input:** Foundation/runtime needs to read, create, publish, replace, or delete owned local files/directories.

**Result:** Provide canonical-path, ownership-aware, crash-resistant filesystem primitives.

**Rules:**
- Canonicalize beneath an explicit owned root and reject path traversal or unexpected symlink/reparse redirection where ownership/security depends on the path.
- Provide same-directory atomic file publication using temporary file + flush/fsync where supported + replace.
- Provide atomic same-parent directory publication for complete artifact sets when required by the owning feature.
- Deletion requires exact-owned target validation; unknown/replaced artifacts are preserved rather than blindly removed.
- Security-sensitive files use owner-appropriate ACL enforcement through the platform adapter.
- Callers define semantic content; Foundation owns only safe filesystem mechanics.

**Failure:** Unsafe path, ownership ambiguity, replacement race, ACL failure, or partial publication fails closed and leaves recoverable evidence where safe.

**Side effects:** bounded owned filesystem mutation.

<a id="fs-temp"></a>
## FS.TEMP

**Trigger/input:** A SOMA operation needs scratch/staging space for parsing, generation, snapshots, or atomic publication.

**Result:** Allocate an operation-scoped directory beneath the canonical instance `tmp/` root with explicit ownership and cleanup semantics.

**Rules:**
- Runtime temp is distinct from repository `.tmp/`; repository `.tmp/` remains ignored human/agent scratch material.
- Temporary workspaces use unpredictable operation identities and never become authoritative merely by existing.
- Successful operations clean exact-owned scratch state; crash leftovers may be pruned only after ownership/age/activity checks.
- Secrets are not written to temp unless an owning security contract explicitly permits a protected representation.

**Failure:** Temp allocation/ownership failure aborts the operation before authoritative mutation.

**Side effects:** temporary local files/directories only.

<a id="runtime-lifecycle"></a>
## RUNTIME.LIFECYCLE

**Trigger/input:** The SOMA host process starts, progresses toward readiness, fails, or shuts down.

**Result:** Maintain one authoritative host state machine:

`STOPPED -> STARTING -> MIGRATING -> VERIFYING -> LISTENING_NOT_READY -> READY -> QUIESCING -> STOPPED`

Any active startup/ready state may enter `FAILED` on unrecoverable host failure; retry/cleanup is explicit.

**Rules:**
- `READY` means canonical instance ownership is held; live DEK/cipher verification succeeded; accepted migrations/schema/integrity checks succeeded; required foundation providers are composed; the retained loopback socket is serving; runtime control is valid; and required static/main bootstrap assets verify.
- Only `READY` accepts ordinary application queries/mutations.
- `LISTENING_NOT_READY` may expose only explicitly allowed authenticated control/status routes.
- State transitions are one-way per startup/shutdown attempt except explicit failed-cleanup/retry.
- State changes are observable through RUNTIME.HEALTH and tray/console presentation; they do not fabricate domain facts.
- Host runtime owns one request executor (initial max 4 workers) and one background executor (initial max 2 workers); blocking DB/file/application work never blocks the ASGI event loop.

**Failure:** Illegal transition or failed required readiness check enters `FAILED`, preserves sanitized diagnostics, and never publishes false READY.

**Side effects:** runtime/process state only.

Reuse provenance: Beta `LocalHostLifecycle`.

<a id="capability-registry"></a>
## CAPABILITY.REGISTRY

**Trigger/input:** Application composition finishes or main/diagnostics asks what this build can actually perform.

**Result:** Return a deterministic registry of assembled capability IDs and availability state.

**Rules:**
- A capability is `available` only when its required provider/transport contract is actually composed; placeholders/stubs are never advertised as working.
- Registry may distinguish `available`, `unavailable`, and `development` with an optional safe reason/remediation identifier.
- Capability state does not alter domain truth and is not business authorization.
- Main uses this registry to avoid fake routes/actions while iterative implementation is incomplete.
- IDs are stable capability names owned by their scope; Foundation owns registry mechanics only.

**Failure:** Duplicate/conflicting registrations fail composition; unknown capability consumers treat it as unavailable.

**Side effects:** none.

<a id="runtime-health"></a>
## RUNTIME.HEALTH

**Trigger/input:** Authenticated run-control health request or authenticated browser diagnostics request.

**Result:** Report truthful bounded technical state for the current run.

**Run-control health includes:** protocol version, `run_id`, `data_instance_id`, host state, build identity, PID/process birth identity, current migration identity/schema state, integrity state, and startup UTC.

**Browser diagnostics may additionally include:** capability registry, executor queue-depth categories, open connection/active transaction counts, durable jobs by technical state, last migration identity, and sanitized recent foundation error codes.

**Rules:**
- No credential, DEK, run secret, CSRF/session token, customer body, raw exception, or unrestricted filesystem path is returned.
- Health never redirects.
- READY is reported only when RUNTIME.LIFECYCLE readiness invariants hold.
- Health is observational and cannot create defaults, repair, migrate, checkpoint, or mutate domain state.

**Failure:** If truthful health cannot be produced, return a stable bounded failure; never default to READY.

**Side effects:** none.

<a id="runtime-shutdown"></a>
## RUNTIME.SHUTDOWN

**Trigger/input:** Freshly authenticated exact-run shutdown command, console Ctrl+C, or equivalent owned host-stop request.

**Result:** Quiesce and stop the exact current host without losing committed state or granting stale workers/control artifacts authority.

**Sequence:**
1. Revalidate exact run/data identity and transition to `QUIESCING`.
2. Reject new ordinary mutations and stop new durable-job claims.
3. Allow bounded in-flight request transactions to finish; signal cooperative job cancellation/checkpoint behavior.
4. Close request/background executors after their governed budget.
5. Checkpoint/close persistence resources as required without fabricating domain completion.
6. Remove tray and exact-owned runtime registry/secret artifacts only after ownership is proven.
7. Release canonical instance lock and enter `STOPPED`.

**Rules:**
- Graceful shutdown budget is initially 10 seconds for launcher/tray control.
- Repeated exact shutdown is idempotent.
- Timeout never authorizes process-name/PID/port-only termination; any future forced termination requires fresh exact process-birth/image validation.
- Unknown or replaced runtime artifacts are preserved.

**Failure:** Partial shutdown returns explicit failure/timeout state with safe diagnostics; it never reports graceful completion falsely.

**Side effects:** runtime quiescence/cleanup only.

<a id="security-browser-session"></a>
## SECURITY.BROWSER_SESSION

**Trigger/input:** AUTH.LOCAL_ADMIN or a later accepted authentication provider proves an operator and requests a browser session, or a browser query/mutation presents existing session context.

**Result:** Provide same-origin loopback browser-session and CSRF mechanics independent of run-control authentication.

**Rules:**
- Session store is host-memory only; persist only SHA-256(session-token) lookup material, never raw reusable tokens.
- Issue independent random 32-byte session and CSRF tokens; bind session to current `run_id`, actor identity, canonical origin, and monotonic issue/last-seen deadlines.
- Session cookie is opaque, HttpOnly, SameSite=Strict, host-only, Path=/, with no Domain. Loopback HTTP means the cookie is not `Secure`; exact Host/Origin/CSRF rules are mandatory compensating controls.
- Query validation requires exact current Host, valid current-run session, and valid deadlines.
- Mutation validation additionally requires exact current Origin, constant-time matching `X-SOMA-CSRF`, and same-origin/none Fetch Metadata when present.
- CORS is disabled; forwarded/proxy headers do not influence trust.
- Initial inherited bounds are 12-hour idle, 24-hour absolute lifetime, and maximum 4 sessions; a later credential-management/security decision may tighten them.
- Run end invalidates all sessions. Authentication/password changes may invalidate sessions through the provider contract.
- This item does not define password verification, local profile semantics, or business authorization; AUTH.LOCAL_ADMIN owns the minimal password setup/login/logout provider while this item owns the transport/session substrate.

**Failure:** Missing/stale/wrong-run/cross-origin/session/CSRF context fails before application dispatch.

**Side effects:** bounded in-memory session state only.

Reuse provenance: Beta `BrowserSessionAndCsrfV1`.

<a id="persistence-snapshot"></a>
## PERSISTENCE.SNAPSHOT

**Trigger/input:** Backup/recovery/dev tooling requests a transactionally consistent database snapshot.

**Result:** Produce a verified consistent snapshot of the authoritative encrypted database through Foundation-owned persistence mechanics without transferring backup-format ownership to Foundation.

**Rules:**
- Snapshot acquisition proves canonical instance/data identity and uses SQLite/SQLCipher-supported consistent snapshot mechanics.
- Snapshot creation is bounded with respect to writer authority; expensive compression/encryption/export occurs after the database-consistency step.
- Snapshot output is staged/published through FS.SAFE and is never declared a complete portable backup by this mechanism alone.
- Future backup/recovery scopes own artifact envelope, retention, recovery secrets, restore policy, and UX.

**Failure:** Busy/integrity/cipher/snapshot/publication failure yields no apparently complete snapshot artifact.

**Side effects:** owned snapshot/staging files only.

<a id="audit-append-only"></a>
## AUDIT.APPEND_ONLY

**Trigger/input:** An authoritative command declares a required audit event inside its existing UnitOfWork.

**Result:** Validate and append one immutable typed audit event plus bounded resulting-event references atomically with the owning command.

**Rules:**
- Required core context includes audit event ID, action type/version, actor kind/ID when applicable, target type/ID, command ID, payload schema/version, canonical payload, correlation ID when present, and Foundation-assigned recording UTC.
- Action/payload contracts are statically registered by the owning scope; Foundation never invents domain audit payload meaning.
- Sensitive-field classification and canonical byte bounds are validated before insert.
- Audit repository exposes no update/delete API; database guards reject UPDATE/DELETE.
- Correction/reversal uses a new event referencing prior identity; prior audit bytes are never edited.
- Any required audit validation/persistence failure rolls back the owning authoritative command.
- Audit is evidence, not a mutable business-state store.

**Failure:** Unknown action contract, invalid/oversized/sensitive payload, duplicate identity, or append-only integrity failure fails the whole owning mutation.

**Side effects:** append-only technical evidence inside caller UoW.

Reuse provenance: Beta `AuditWriter`.

<a id="jobs-execution"></a>
## JOBS.EXECUTION

**Trigger/input:** Runtime becomes READY, durable work is available, or shutdown begins.

**Result:** Execute registered durable jobs through a bounded host-owned background executor while JOBS.COORDINATOR remains the durable authority.

**Rules:**
- Initial background executor maximum is 2 workers; the bound is configuration-controlled but not unbounded.
- Handler execution never holds a database transaction during external/file/CPU-heavy work.
- Each accepted domain mutation performed by a job uses the owning application command/UoW.
- Cancellation signal is cooperative optimization only; persisted claim/state validation is authoritative.
- QUIESCING stops new claims; running handlers finish a safe checkpoint/terminal result within budget or remain recoverable on next startup.
- Retry/backoff classification comes from each registered job contract; Foundation never invents domain lifecycle outcomes.

**Failure:** Handler crash/timeout is converted to bounded stable job error state without persisting raw exception/provider secret text.

**Side effects:** technical job attempts/checkpoints and owner-command effects.

<a id="dev-seed"></a>
## DEV.SEED

**Trigger/input:** Explicit development reset/reseed operation after current migrations are applied.

**Result:** Populate a deterministic useful development dataset through registered scope seed contributors.

**Rules:**
- Ordinary startup never seeds data.
- Seed execution is explicit, development-only, versioned with the current design, and safe to discard.
- Foundation owns seed orchestration/order and deterministic technical helpers; each domain scope owns its seed facts/invariants.
- Seed contributors use application/domain interfaces or declared development-loading interfaces, never raw cross-module table writes.
- Seed data is clearly synthetic and must not be confused with imported/customer evidence.
- Reset/reseed may change freely during development; no Alpha/Beta data carryover is implied.

**Failure:** Any required seed contributor failure marks reset/reseed incomplete and is reported explicitly; no false READY-with-seed-success claim.

**Side effects:** development database population only.

<a id="query-page"></a>
## QUERY.PAGE

**Trigger/input:** A module exposes a bounded collection/list/query surface.

**Result:** Supply shared typed keyset-page/cursor mechanics while the module owns filter/order/business semantics.

**Rules:**
- Default page size 100; hard maximum 200 unless an owning LLD explicitly defines a stricter bound.
- Cursor is versioned, filter/order-bound, opaque to UI, and validated against the exact query contract.
- Collection ordering is deterministic and includes a unique tie-breaker.
- A page/projection captures one `as_of_utc` or equivalent read-snapshot reference when derived ages/counts require consistency.
- No silent truncation: partial/additional-results/capacity state is explicit.
- Foundation does not invent domain filters, ranking, eligibility, or SQL across another module's private tables.

**Failure:** Malformed/stale/wrong-filter cursor fails validation instead of returning a different page silently.

**Side effects:** none.

<a id="static-assets"></a>
## STATIC.ASSETS

**Trigger/input:** Local host starts or browser requests Main application/static assets.

**Result:** Serve the verified prebuilt Main SPA from the local Python application with no Node/runtime network dependency.

**Rules:**
- Production-format runtime serves only locally built/packaged assets whose manifest/hash set matches BUILD.IDENTITY.
- Source development may rebuild assets explicitly during setup/build; normal runtime does not invoke npm/Vite.
- SPA fallback is allowed only for registered Main application routes; API/static-missing paths do not silently return HTML.
- Static responses use safe content types/headers and a Content Security Policy compatible with no remote code/style/font dependency and no unsafe eval.
- Asset verification is a readiness prerequisite when the user plane is required by the assembled build.

**Failure:** Missing/tampered/incompatible required assets block READY or return explicit static-asset failure; no CDN fallback.

**Side effects:** HTTP static responses only.

<a id="test-seams"></a>
## TEST.SEAMS

**Trigger/input:** Focused automated/integration tests need deterministic control over foundation mechanisms.

**Result:** Allow composition to inject bounded test providers without weakening production/source runtime contracts.

**Rules:**
- Injectable seams include UTC clock, monotonic clock, UUID generator, filesystem root/provider, process/runtime probes, browser opener, and test database/config factories.
- Production composition uses concrete providers explicitly; tests do not mutate module globals to replace security/time/filesystem behavior.
- Security/adversarial integration tests still exercise real Windows/DPAPI/SQLCipher providers where their behavior is under test.
- A test seam cannot become a runtime configuration switch that bypasses authentication/encryption/trust in ordinary source execution.

**Failure:** Missing required provider fails composition explicitly.

**Side effects:** test-only dependency substitution.

<a id="runtime-instance"></a>
## RUNTIME.INSTANCE

**Trigger/input:** SOMA host startup, shutdown, or an operation requiring the authoritative development instance.

**Result:** Resolve one canonical local SOMA instance, its runtime identity, database location, and owned runtime resources before authoritative access.

**Rules:**
- One running authoritative instance owns its configured database at a time.
- The initial source-development instance root comes from CONFIG.RUNTIME and defaults to LocalAppData `SOMA/Development/instance-v1`; source checkout location never becomes the data root.
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

**Result:** Provide five stable, human-friendly development entry points backed by one launcher implementation:

| Entry point | Required behavior |
|---|---|
| `soma_setup.bat` | Create/reuse the repository-local development environment, install/verify declared development dependencies and native prerequisites, and validate the source checkout. It does not fabricate runtime state, start SOMA, reset the database, or silently substitute insecure dependencies. |
| `soma_run.bat` | Reuse and open an already verified READY instance, or start SOMA detached, capture an owner-only run log, wait up to 30 seconds for authenticated READY, then open only the verified origin. |
| `soma_run_console.bat` | Start the real SOMA host in the foreground, mirror sanitized runtime logging to the terminal, print the verified READY origin, and perform graceful owned shutdown on Ctrl+C. If a verified instance already runs, report/open that instance instead of creating a second host. |
| `soma_stop.bat` | Freshly verify the current run, request graceful authenticated shutdown, and wait up to 10 seconds. No valid running instance is an idempotent success. Timeout reports failure and does not kill by process name, stale PID, or port alone. |
| `soma_reset_dev.bat` | Resolve and display the exact development instance, require the operator to type literal `RESET`, gracefully stop a verified live host if required, recreate only the disposable development database from the current migration manifest, run DEV.SEED, and leave SOMA stopped. It never resets a packaged/non-development instance and never treats a double-click alone as confirmation. |

**Rules:**
- The BAT files are intentionally thin adapters. Runtime/setup/trust logic lives in `tools/source_launcher.py` and shared core providers; do not duplicate security logic across scripts.
- Runtime actions never install or update dependencies. Environment mutation belongs only to explicit setup.
- `soma_reset_dev.bat` is the only root-level destructive development button; it requires the explicit typed confirmation above and refuses a target whose CONFIG.RUNTIME mode/root is not the canonical development instance.
- Source launchers operate against the canonical development instance, not a database under the checkout.
- Concurrent run attempts converge on the single instance lock; the losing launcher waits for/verifies the winning host rather than creating a second authoritative instance.
- Setup is rerunnable and preserves unrelated checkout/user data.
- Source launchers are development controls, not the future production installer contract; production shortcuts may later call the same trusted control capabilities.

**Failure:** Missing/unsupported environment, unsafe checkout/runtime path, failed native dependency verification, startup crash, READY timeout, or trust failure produces a nonzero exit and an actionable diagnostic/log location. No fake success or plaintext fallback is allowed.

**Side effects:** Setup may create/update the repository-local environment. Run/console/stop operate the local runtime through RUNTIME.TRUSTED_CONTROL. Reset may destroy and recreate only the explicitly confirmed canonical development database and seed state.

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

<a id="auth-local-admin"></a>
## AUTH.LOCAL_ADMIN

**Trigger/input:** First-run credential setup, password login, logout, or browser bootstrap asks whether the singleton Local Administrator is configured/authenticated.

**Result:** Provide one password-authenticated local actor for the current SOMA installation and issue/destroy SECURITY.BROWSER_SESSION state after successful authentication.

**Rules:**
- SOMA has one Local Administrator credential record in the current single-user product phase. Login requires no username.
- Initial database state contains zero credential rows and reports `setup_required`; normal domain/application routes remain gated until first-run setup completes, while trusted runtime/diagnostic/setup routes remain available as explicitly allowed.
- First-run setup requires password + confirmation. Validate at least 12 Unicode scalar values and at most 1024 UTF-8 bytes, with no trimming, Unicode normalization, case conversion, or hidden mutation. Confirmation requires exact UTF-8 byte equality.
- Setup creates one stable technical `actor_id` and Argon2id PHC verifier using PLATFORM.BASELINE's accepted profile inside one TX.UOW. The raw password/confirmation never enters audit, diagnostics, correlation context, repr/debug text, browser storage, command replay payloads, or logs.
- Login accepts password only, applies the current in-memory failure-delay gate before expensive hashing, verifies through the pinned Argon2 provider, and on success clears the failure counter and issues a current-run browser session.
- After 5 consecutive failures, per-run login delay follows 1, 2, 4, then 8 seconds and remains capped at 8 seconds. Delay uses TIME.MONOTONIC, occurs outside database transactions, and creates no durable account lockout.
- Public credential failure is uniform `AUTH_INVALID_CREDENTIALS`; malformed/unsupported persisted verifier shape is recorded only as bounded security diagnostic evidence and never reveals verifier details to the browser.
- Logout invalidates the presented browser session and returns to `login_required`; it does not alter the password verifier.
- Password authentication never derives/wraps the live DEK, run-control secret, session/CSRF token, or future backup recovery material.
- Password change/reset/recovery UI and profile/display-name semantics are not owned by this minimal foundation contract and may be added by a later scope without changing the login/session boundary.

**Failure:** A second setup attempt, invalid setup password/confirmation, invalid credentials, unsupported verifier, persistence failure, or session-issuance failure returns a stable safe error and never creates a partial credential/session state.

**Side effects:** First-run setup creates the singleton credential row; successful login/logout mutates only in-memory session state plus bounded authentication-throttle state.

Reuse provenance: Beta `PasswordAuthenticationV1`, narrowed to minimal setup/login/logout foundation ownership.

<a id="security-deliberate-proof"></a>
## SECURITY.DELIBERATE_PROOF

**Trigger/input:** UI begins/completes an action registered for `deliberate_hold` or `impact_preview_plus_hold`, then the owning command consumes the resulting proof.

**Result:** Provide server-timed, session/run/target-bound, single-use friction evidence without replacing domain authorization or freshness guards.

**Rules:**
- Challenge issuance requires a valid authenticated browser mutation context and a registered action code/target/base revision plus preview fingerprint when the tier requires one.
- Challenge state is memory-only, bound to current run/session/action/target/revision/preview, and initially expires after 15 seconds.
- Completion uses server TIME.MONOTONIC and requires elapsed >= 3000 ms and <= challenge expiry; client-reported elapsed time is never authority.
- Successful completion returns one random 32-byte opaque proof token and stores only its SHA-256 plus exact bindings.
- Proof initially expires after 30 seconds, is single-use, and is validated/consumed only inside the owning command's existing UnitOfWork at the owner-declared pre-mutation boundary.
- Owning domain still performs all business/permission/dependency/freshness/preview guards. Proof means deliberate friction occurred, not that the action is authorized.
- Failed owner transaction does not make a consumed proof reusable.

**Failure:** wrong run/session/action/target/revision/preview, too-early/expired challenge, bad token, or reused proof fails closed before protected mutation.

**Side effects:** bounded in-memory challenge/proof state and one proof-consumption marker during owner command execution.

Reuse provenance: Beta `DeliberateActionProofV1`.

<a id="persistence-read-snapshot"></a>
## PERSISTENCE.READ_SNAPSHOT

**Trigger/input:** A query/projection needs multiple reads to represent one coherent point of authoritative state.

**Result:** Provide a short keyed verified read-only SQLite snapshot context shared by all participating owner reads for that projection.

**Rules:**
- Open a dedicated verified read connection, enable query-only mode, begin a read transaction, perform bounded reads, then commit/close.
- Snapshot never includes operator think-time, network waits, external parsing, or unrelated work.
- Connections never cross threads and are always cleaned up even if BEGIN/read/commit setup fails.
- Cross-module projections call exported owner readers using the same snapshot mechanism/coordination contract; they never join another module's private tables.
- One captured `as_of_utc` may accompany the snapshot for consistent derived ages/durations.

**Failure:** Snapshot begin/read/cleanup failure returns a stable query failure and no partially mixed multi-generation result.

**Side effects:** read transaction only.

Reuse provenance: Beta LLD-01 consistent read snapshot and audit fix for BEGIN-failure cleanup.

<a id="persistence-schema-verify"></a>
## PERSISTENCE.SCHEMA_VERIFY

**Trigger/input:** Migrations finish, an authoritative database opens for readiness, or explicit deep verification is requested.

**Result:** Compare the actual encrypted database against a committed expected schema manifest and required integrity invariants before READY.

**Rules:**
- Expected truth is generated from accepted current migration/design lineage and committed with the application; it is never regenerated from the database being verified.
- Verify authoritative tables/indexes/triggers, columns/types/null/default/PK shape, foreign keys/actions, index uniqueness/ordered key columns, and declared append-only triggers.
- Unknown/missing/structurally different authoritative objects block readiness unless explicitly classified SQLite-owned/internal.
- Verify every child foreign-key column sequence has an effective leading-prefix index unless an explicit measured accepted exception exists.
- Ordinary readiness runs `foreign_key_check`, `quick_check`, exact migration-ledger/manifest reconciliation, and append-only-trigger probes inside rolled-back verification where needed.
- Deep/restore verification may additionally require full `integrity_check`.
- Verification is observational except controlled rolled-back probes.

**Failure:** Drift, missing/extra authoritative object, FK/index gap, ledger mismatch, append-only failure, or integrity failure blocks READY with ERROR.CONTRACT identity.

**Side effects:** read-only verification and rolled-back probes only.

Reuse provenance: Beta LLD-01 schema verification contract.

<a id="migration-status"></a>
## MIGRATION.STATUS

**Trigger/input:** Setup/diagnostics requests current migration/schema status either through a verified live host or through safe offline inspection.

**Result:** Return a strictly observational migration classification without creating/repairing/migrating anything.

**Rules:**
- Prefer authenticated live-host status when a verified current runtime owns the instance.
- Offline inspection must prove exclusive inspection safety using the canonical instance lock; if another process may own it, return a limited/locked status rather than opening directly.
- Existing WAL/SHM sidecars without verified live ownership make immutable offline inspection unsafe.
- Offline database open is read-only/immutable and never creates parent/database/lock/default/log files.
- Status distinguishes at least: not initialized, current, pending, drift, ledger mismatch, unsupported future schema, invalid database/layout, integrity failure, verified live current/pending, locked/unverified, unsafe sidecar state, and inspection failure.
- No status path invokes repair, migration, WAL checkpoint, defaults, or diagnostic emission merely by being queried.

**Failure:** Inability to prove a safe truthful view is itself an explicit status, never guessed CURRENT.

**Side effects:** none.

Reuse provenance: Beta `GetMigrationStatus`.

<a id="working-copy-store"></a>
## WORKING_COPY.STORE

**Trigger/input:** A registered edit surface checkpoints, fetches/restores, discards, or prunes recoverable UI working intent.

**Result:** Persist bounded technical draft state separately from accepted domain truth while retaining exact owner contract, target, base revision, generation, chronology, and conflict identity.

**Rules:**
- Only immutable statically registered working-copy contracts may store draft payloads; each declares contract/version, target/scope keys, closed draft schema, and allowed dirty paths.
- Checkpoint validates strict canonical JSON <=262144 UTF-8 bytes and exact expected generation; changed checkpoint increments generation, identical current content is NO_CHANGE.
- New recoverable copies are capped at 256 nonexpired installation-wide; expiry is initially 7 days.
- Main may checkpoint after 5 seconds idle but no more frequently than one successful checkpoint per 30 seconds for the same copy.
- One checkpoint/discard uses one short existing Foundation UnitOfWork with command replay/audit metadata; it never invokes the owning domain mutation.
- Restore reads the stored draft plus current owner revision/freshness context; restoration never accepts it.
- Discard/prune deletes only technical working-copy state. Pruning is bounded to 100 rows per pass.
- A stale base revision enters owner conflict review; last-write-wins over accepted owner truth is prohibited.

**Failure:** Unknown contract, invalid/oversized draft, generation conflict, capacity, missing copy, or stale owner context returns explicit working-copy failure and preserves accepted truth.

**Side effects:** `ui_working_copies` technical state plus required command/audit metadata only.

Reuse provenance: Beta LLD-10 working-copy command/query mechanics.

<a id="persistence-connection"></a>
## PERSISTENCE.CONNECTION

**Trigger/input:** Foundation requests an authoritative database connection.

**Result:** Return a verified SQLCipher connection for the canonical instance.

**Rules:**
- SQLCipher is mandatory for authoritative production-format storage; development does not silently substitute plaintext SQLite.
- Apply the raw live DEK before schema access.
- Verify the expected SQLCipher/provider/cipher profile before migrations or authoritative reads.
- Required connection setup includes `foreign_keys=ON`, `busy_timeout=5000`, `trusted_schema=OFF`, `temp_store=MEMORY`, `synchronous=FULL`, `secure_delete=FAST`, disabled extension loading, and verified WAL runtime mode; initial WAL autocheckpoint is 1000 pages.
- Write UnitOfWork uses explicit `BEGIN IMMEDIATE`; bounded busy/snapshot conflicts map to retryable persistence-busy failure with no accepted partial write.
- Connection lifetime is explicit; failed begin/open paths clean up resources.
- Repositories receive connection/transaction context; they do not create independent commits or unmanaged connections.
- SQL values are driver-bound parameters; one execute call contains one SQL statement and domain services never use `executescript`.
- Connection/driver row objects do not escape repository boundaries or cross thread boundaries.

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

**Result:** Stop/quiesce that instance, destroy only its disposable database state, recreate from the current manifest, and execute DEV.SEED.

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
