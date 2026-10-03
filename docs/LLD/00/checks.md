<!-- soma-meta
{
  "version": 1,
  "id": "LLD-00-CHECKS",
  "scope": "00",
  "items": [
    {
      "id": "CHK00.RUNTIME.TRUST",
      "anchor": "chk-runtime-trust",
      "covers": ["RUNTIME.TRUSTED_CONTROL"]
    },
    {
      "id": "CHK00.LAUNCHERS.LIFECYCLE",
      "anchor": "chk-launchers-lifecycle",
      "covers": ["DEV.SOURCE_LAUNCHERS", "RUNTIME.TRUSTED_CONTROL", "DIAGNOSTICS.OPERATOR_LOGS"]
    },
    {
      "id": "CHK00.TRAY.CONTROL",
      "anchor": "chk-tray-control",
      "covers": ["UI.SYSTEM_TRAY", "RUNTIME.TRUSTED_CONTROL", "DIAGNOSTICS.OPERATOR_LOGS"]
    },
    {
      "id": "CHK00.RUNTIME.LIFECYCLE",
      "anchor": "chk-runtime-lifecycle",
      "covers": ["RUNTIME.INSTANCE", "RUNTIME.LIFECYCLE", "RUNTIME.HEALTH", "RUNTIME.SHUTDOWN"]
    },
    {
      "id": "CHK00.CONFIG.PATHS",
      "anchor": "chk-config-paths",
      "covers": ["CONFIG.RUNTIME", "FS.SAFE", "FS.TEMP"]
    },
    {
      "id": "CHK00.BUILD.STATIC",
      "anchor": "chk-build-static",
      "covers": ["PLATFORM.BASELINE", "BUILD.IDENTITY", "STATIC.ASSETS", "UI.BOOTSTRAP", "UI.BRAND"]
    },
    {
      "id": "CHK00.ERROR.TRACE",
      "anchor": "chk-error-trace",
      "covers": ["ERROR.CONTRACT", "TRACE.CORRELATION", "IDENTITY.UUID", "SERIALIZATION.STRICT_JSON", "UI.ERROR_STATE"]
    },
    {
      "id": "CHK00.CLOCKS.SEAMS",
      "anchor": "chk-clocks-seams",
      "covers": ["TIME.MONOTONIC", "TEST.SEAMS"]
    },
    {
      "id": "CHK00.SESSION.CSRF",
      "anchor": "chk-session-csrf",
      "covers": ["SECURITY.BROWSER_SESSION"]
    },
    {
      "id": "CHK00.SNAPSHOT",
      "anchor": "chk-snapshot",
      "covers": ["PERSISTENCE.SNAPSHOT"]
    },
    {
      "id": "CHK00.AUDIT.APPEND",
      "anchor": "chk-audit-append",
      "covers": ["AUDIT.APPEND_ONLY", "TX.UOW"]
    },
    {
      "id": "CHK00.JOB.EXECUTION",
      "anchor": "chk-job-execution",
      "covers": ["JOBS.EXECUTION", "JOBS.COORDINATOR", "RUNTIME.SHUTDOWN"]
    },
    {
      "id": "CHK00.SEED.RESET",
      "anchor": "chk-seed-reset",
      "covers": ["DEV.SEED", "DEV.DB_RESET", "MIGRATION.MANIFEST"]
    },
    {
      "id": "CHK00.CAPABILITIES",
      "anchor": "chk-capabilities",
      "covers": ["CAPABILITY.REGISTRY", "UI.CAPABILITY_STATE"]
    },
    {
      "id": "CHK00.PAGE.COLLECTION",
      "anchor": "chk-page-collection",
      "covers": ["QUERY.PAGE", "UI.COLLECTIONS", "API.CLIENT"]
    },
    {
      "id": "CHK00.UI.ROUTING",
      "anchor": "chk-ui-routing",
      "covers": ["UI.ROUTING", "UI.SELECTION"]
    },
    {
      "id": "CHK00.UI.AUTOCOMPLETE",
      "anchor": "chk-ui-autocomplete",
      "covers": ["UI.AUTOCOMPLETE", "UI.COLLECTIONS", "UI.SCROLL"]
    },
    {
      "id": "CHK00.UI.DIALOG",
      "anchor": "chk-ui-dialog",
      "covers": ["UI.DIALOG_FOCUS", "UI.SCROLL"]
    },
    {
      "id": "CHK00.UI.UNDO",
      "anchor": "chk-ui-undo",
      "covers": ["UI.SAFE_UNDO", "UI.CONFIRMATION"]
    },
    {
      "id": "CHK00.UI.DIAGNOSTICS",
      "anchor": "chk-ui-diagnostics",
      "covers": ["UI.DIAGNOSTICS_STATE", "RUNTIME.HEALTH", "DIAGNOSTICS.OPERATOR_LOGS", "DIAGNOSTICS.SAFE"]
    },
    {
      "id": "CHK00.UI.ACCESSIBILITY",
      "anchor": "chk-ui-accessibility",
      "covers": ["UI.ACCESSIBILITY", "UI.TOKENS", "UI.DIALOG_FOCUS", "UI.SELECTION", "UI.SHELL"]
    },
    {
      "id": "CHK00.TIME.ROUNDTRIP",
      "anchor": "chk-time-roundtrip",
      "covers": ["TIME.UTC", "TIME.DISPLAY"]
    },
    {
      "id": "CHK00.DB.PROTECTED_OPEN",
      "anchor": "chk-db-protected-open",
      "covers": ["SECURITY.LIVE_DATA_KEY", "PERSISTENCE.CONNECTION"]
    },
    {
      "id": "CHK00.TX.ROLLBACK",
      "anchor": "chk-tx-rollback",
      "covers": ["TX.UOW"]
    },
    {
      "id": "CHK00.MIGRATION.REBUILD",
      "anchor": "chk-migration-rebuild",
      "covers": ["MIGRATION.MANIFEST", "DEV.DB_RESET"]
    },
    {
      "id": "CHK00.REPLAY.EXACT",
      "anchor": "chk-replay-exact",
      "covers": ["COMMAND.REPLAY"]
    },
    {
      "id": "CHK00.JOB.RECOVERY",
      "anchor": "chk-job-recovery",
      "covers": ["JOBS.COORDINATOR"]
    },
    {
      "id": "CHK00.CONTRACT.SYNC",
      "anchor": "chk-contract-sync",
      "covers": ["CONTRACT.SOURCE", "API.CLIENT"]
    },
    {
      "id": "CHK00.UI.SELECTION",
      "anchor": "chk-ui-selection",
      "covers": ["UI.SELECTION"]
    },
    {
      "id": "CHK00.UI.SCROLL",
      "anchor": "chk-ui-scroll",
      "covers": ["UI.SCROLL"]
    },
    {
      "id": "CHK00.UI.REFLOW",
      "anchor": "chk-ui-reflow",
      "covers": ["UI.RESPONSIVE", "UI.WORKING_COPY"]
    },
    {
      "id": "CHK00.UI.HOLD",
      "anchor": "chk-ui-hold",
      "covers": ["UI.CONFIRMATION"]
    },
    {
      "id": "CHK00.DOC.IMPACT",
      "anchor": "chk-doc-impact",
      "covers": ["TOOLING.IMPACT"]
    }
  ],
  "tags": ["foundation", "checks"]
}
-->

# Foundation checks

These are development checks, not release certification. Each scenario becomes executable when its covered behavior is implemented.

<a id="chk-runtime-lifecycle"></a>
## CHK00.RUNTIME.LIFECYCLE

Start from no running instance and observe the exact startup sequence through STARTING, MIGRATING, VERIFYING, LISTENING_NOT_READY, and READY. Verify ordinary application routes reject before READY. Trigger graceful shutdown and verify QUIESCING rejects new mutations, stops new job claims, drains bounded work, removes exact-owned runtime/tray artifacts, releases the instance lock, and reaches STOPPED. Inject a required readiness failure and verify FAILED is truthful and never reported as READY.

<a id="chk-config-paths"></a>
## CHK00.CONFIG.PATHS

Resolve default development configuration and verify all authoritative roots remain beneath the canonical LocalAppData development instance, while checkout paths remain code-only. Exercise explicit test/development override, path traversal, symlink/reparse redirection, atomic replacement, exact-owned deletion, and runtime temp allocation/cleanup. Unsafe/ambiguous paths fail before authoritative mutation and repository `.tmp/` is never used as application temp state.

<a id="chk-build-static"></a>
## CHK00.BUILD.STATIC

Build Main using the pinned source toolchain, record build/protocol/contract identity, start SOMA without Node present, and verify the local Python host serves only the verified static bundle and registered SPA routes. Tamper/mismatch the asset manifest or required protocol identity and verify READY is blocked or bootstrap displays explicit incompatibility; no remote/CDN fallback occurs.

<a id="chk-error-trace"></a>
## CHK00.ERROR.TRACE

Issue one request that succeeds and one that fails inside a nested application/adapter path. Verify a single correlation identity is available across safe logs/audit/job metadata and the failure envelope while remaining non-authoritative. Inject raw SQL/OS/framework exception text, paths, and secret-like values and verify none cross the application boundary; the client receives a stable code/recoverability/summary/correlation contract.

<a id="chk-clocks-seams"></a>
## CHK00.CLOCKS.SEAMS

Use injected UTC, monotonic, and UUID providers to deterministically exercise a timeout/retry/session scenario. Change wall-clock UTC during elapsed timing and verify timeout semantics do not change. Verify production/source composition cannot enable test providers through ordinary runtime configuration.

<a id="chk-session-csrf"></a>
## CHK00.SESSION.CSRF

Using a test authentication provider, issue a browser session and verify exact Host, current-run binding, idle/absolute deadlines, host-only HttpOnly SameSite cookie behavior, and mutation CSRF + exact Origin checks. Reject wrong run, expired session, missing/null/cross-origin Origin, wrong CSRF, proxy/forwarded substitution, and invalid Fetch Metadata before application dispatch. Confirm browser never receives run-control secret.

<a id="chk-snapshot"></a>
## CHK00.SNAPSHOT

Create authoritative data, take a Foundation snapshot while the real encrypted database is active, and verify the snapshot represents one consistent committed point without becoming a portable-backup artifact by itself. Inject busy/cipher/integrity/publication failures and verify no apparently complete snapshot is published.

<a id="chk-audit-append"></a>
## CHK00.AUDIT.APPEND

Execute a command requiring audit evidence and verify domain mutation, command receipt/result, and typed audit event/results commit in the same outer UnitOfWork. Inject unknown action schema, sensitive/oversized payload, duplicate audit identity, and persistence failure and verify the entire mutation rolls back. Attempt audit UPDATE/DELETE through repository and database paths and verify append-only enforcement.

<a id="chk-job-execution"></a>
## CHK00.JOB.EXECUTION

Run more registered durable work than the background worker bound, verify at most the configured concurrent handlers execute, no handler holds a writer transaction during long file/CPU work, and accepted domain effects go through owner commands. Enter QUIESCING while jobs run and verify no new claims occur; safe checkpoint/terminal completion or next-start recovery preserves authority and stale handlers cannot commit.

<a id="chk-seed-reset"></a>
## CHK00.SEED.RESET

Against only the designated development instance, execute reset -> migrations -> registered deterministic seed contributors -> startup. Repeat and verify useful synthetic identity is deterministic where declared and no Alpha/Beta/customer evidence is imported. Inject one seed-contributor failure and verify reset/reseed reports incomplete state rather than claiming seed success.

<a id="chk-capabilities"></a>
## CHK00.CAPABILITIES

Compose a build with one real feature provider, one development capability, and one absent feature. Verify the registry advertises exactly those states, duplicate/conflicting registration fails composition, Main exposes available/development/unavailable states truthfully, and directly navigating to the unavailable feature produces an understandable unavailable surface rather than a stub request/500.

<a id="chk-page-collection"></a>
## CHK00.PAGE.COLLECTION

Create a deterministic collection larger than 200 rows. Verify default 100/max 200 server keyset pages, stable unique ordering, opaque filter/order-bound cursor, consistent as-of reference, explicit continuation, and no silent truncation. Change filter while a prior request is in flight and verify stale results cannot mix/replace the newer collection state.

<a id="chk-ui-routing"></a>
## CHK00.UI.ROUTING

Navigate a synthetic list -> detail -> nested tab/pane and back/forward. Verify closed route registry, filters, active/selected record, scroll anchor, pane/tab, and focus restore when targets survive. Remove/unregister the target capability and verify bookmarked/history navigation becomes explicit unavailable state without owner API dispatch.

<a id="chk-ui-autocomplete"></a>
## CHK00.UI.AUTOCOMPLETE

Exercise minimum-input, debounce, bounded results, continuation/partial state, stale query cancellation, keyboard/pointer/touch selection, popup scroll ownership, and no-match/error states. Focus alone must not enumerate an unbounded population; typed/highlighted text must never create an entity/relationship.

<a id="chk-ui-dialog"></a>
## CHK00.UI.DIALOG

Open a long consequential modal from a scrolled workbench. Verify safe initial focus, focus containment, background inertness/scroll isolation, internal dialog scrolling, Escape cancellation without acceptance, and invoker/fallback focus restoration. If isolation is deliberately broken in a test harness, consequential acceptance remains unavailable.

<a id="chk-ui-undo"></a>
## CHK00.UI.UNDO

Register a synthetic reversible owner action with exact preview/fingerprint and one unrelated reversible action. Verify both may retain independent bounded Undo opportunities, fresh owner revalidation precedes inverse dispatch, and stale/unregistered/blocked inverse becomes unavailable with reason. Confirm no generic database/global rollback path exists.

<a id="chk-ui-diagnostics"></a>
## CHK00.UI.DIAGNOSTICS

Open the System/Diagnostics surface on a healthy and partially failing host. Verify build/run/schema/capability/job/executor/connection/transaction/log/recent-safe-error state is visible, local time is readable, and canonical evidence remains inspectable where appropriate. Provider failure produces partial/unavailable panels without mutating jobs/migrations/domain state or exposing secrets/raw bodies.

<a id="chk-ui-accessibility"></a>
## CHK00.UI.ACCESSIBILITY

Exercise shared shell/list/dialog/autocomplete/confirmation controls using keyboard only, pointer, touch-equivalent input, 200% text zoom, reduced motion, forced colors/high contrast, and screen-reader semantics where automated/manual tooling permits. Verify visible focus, non-color state meaning, equivalent command result, safe dialog behavior, and labelled alternatives for icon-only actions.


<a id="chk-runtime-trust"></a>
## CHK00.RUNTIME.TRUST

Start a real local host, verify its registry/DPAPI run secret/process birth/origin/health identity, and control it successfully. Then independently test malformed registry shape, alternate/non-literal loopback host, wrong run secret, wrong run/data/protocol identity, stale PID, PID birth reuse, unexpected process image, redirect/proxy behavior, and replaced runtime artifacts. Every adversarial case fails closed without opening or stopping the wrong process.

<a id="chk-launchers-lifecycle"></a>
## CHK00.LAUNCHERS.LIFECYCLE

From a clean supported Windows source checkout, run `soma_setup.bat`, then `soma_run_console.bat`; verify foreground sanitized logging, READY origin, tray presence, and Ctrl+C graceful shutdown. Then execute `soma_run.bat` twice, `soma_stop.bat` twice, and a fresh run/stop cycle. The second run reuses the verified host, the second stop is idempotent, each new run receives a new run identity, no runtime action installs dependencies, and all detached startup/runtime logs are available under the canonical diagnostics root.

Inject startup failure and READY timeout: launcher returns nonzero with an actionable current log path and never opens an unverified origin. Inject a graceful-stop timeout: no process-name/PID-only termination occurs.

<a id="chk-tray-control"></a>
## CHK00.TRAY.CONTROL

Run SOMA in both detached and console modes. Verify exactly one branded tray icon, state tooltip/menu, Open SOMA, Open Current Log, Open Logs Folder, and Stop SOMA. Each control that affects the host freshly verifies the same run identity. Tray Stop and console Ctrl+C converge on graceful shutdown. Simulate tray initialization failure and verify the host remains controllable through BAT/console paths with a sanitized warning.

<a id="chk-time-roundtrip"></a>
## CHK00.TIME.ROUNDTRIP

Create a known UTC instant in core, pass it through the authoritative transport contract, and render it through shared main formatting in at least two effective timezones. The instant remains identical while presentation changes correctly; no feature-local formatter is required.

<a id="chk-db-protected-open"></a>
## CHK00.DB.PROTECTED_OPEN

Create a fresh development instance, protect a random live DEK, open the SQLCipher database, verify cipher/provider/settings before schema access, restart, and reopen. Wrong/unavailable key material blocks readiness and never falls back to plaintext.

<a id="chk-tx-rollback"></a>
## CHK00.TX.ROLLBACK

Execute one application operation with multiple persistence participants, inject a failure before commit, and verify no participant/audit/result state commits. Verify repositories cannot independently commit a partial result.

<a id="chk-migration-rebuild"></a>
## CHK00.MIGRATION.REBUILD

Build a fresh disposable database from the manifest, verify declared owner order/dependencies/hashes, then reset the exact configured development instance and rebuild it again. A tampered SQL hash or unresolved dependency blocks application.

<a id="chk-replay-exact"></a>
## CHK00.REPLAY.EXACT

Run a command once, capture its committed result, repeat the exact identity/request, and verify byte/semantic-equivalent replay without owner re-execution. Reuse the ID with different request identity and verify failure before owner preparation.

<a id="chk-job-recovery"></a>
## CHK00.JOB.RECOVERY

Enqueue a registered durable job, claim/checkpoint it, simulate process interruption, restart, recover from the registered checkpoint, and finish. A stale claim token cannot checkpoint/complete/fail the job.

<a id="chk-contract-sync"></a>
## CHK00.CONTRACT.SYNC

Change a test contract in its authority, regenerate/validate both plane bindings, and verify drift is detected when either consumer/provider shape is stale.

<a id="chk-ui-selection"></a>
## CHK00.UI.SELECTION

In a synthetic dense list, verify click selects without opening; Enter and double-click open the same target; arrows navigate without opening; nested controls do not trigger row-open; touch has an explicit Open action.

<a id="chk-ui-scroll"></a>
## CHK00.UI.SCROLL

Create nested/sibling scroll panes and verify pointer, keyboard, touch, horizontal, autocomplete, and modal ownership. Reaching one pane's boundary does not scroll an unrelated pane and scrolling triggers no selection/open/command side effect.

<a id="chk-ui-reflow"></a>
## CHK00.UI.REFLOW

Populate synthetic workbench state with filters, active/selected record, scroll positions, dirty working copy, and evidence pane. Cross the initial 1040 CSS px split threshold in both directions and verify equivalent capability/state survives.

<a id="chk-ui-hold"></a>
## CHK00.UI.HOLD

Exercise a synthetic registered deliberate action. Verify continuous 3000 ms monotonic hold dispatches once; release, route/target change, stale dependency, or scroll-classified movement resets and dispatches zero commands.

<a id="chk-doc-impact"></a>
## CHK00.DOC.IMPACT

Validate metadata/index creation, modify one item and one mapped source path, and verify direct/indirect impact paths. Remove an edge and verify baseline/current union still reports the former dependent. Unmapped changed code is reported as a gap.
