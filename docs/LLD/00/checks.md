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
      "covers": ["PLATFORM.BASELINE", "BUILD.IDENTITY", "STATIC.ASSETS", "BRAND.ASSETS"]
    },
    {
      "id": "CHK00.ERROR.TRACE",
      "anchor": "chk-error-trace",
      "covers": ["ERROR.CONTRACT", "TRACE.CORRELATION", "IDENTITY.UUID", "SERIALIZATION.STRICT_JSON"]
    },
    {
      "id": "CHK00.CLOCKS.SEAMS",
      "anchor": "chk-clocks-seams",
      "covers": ["TIME.MONOTONIC", "TEST.SEAMS"]
    },
    {
      "id": "CHK00.AUTH.LOCAL_ADMIN",
      "anchor": "chk-auth-local-admin",
      "covers": ["AUTH.LOCAL_ADMIN", "SECURITY.BROWSER_SESSION", "UI.AUTH_GATE", "M00.006"]
    },
    {
      "id": "CHK00.SESSION.CSRF",
      "anchor": "chk-session-csrf",
      "covers": ["SECURITY.BROWSER_SESSION"]
    },
    {
      "id": "CHK00.READ.SNAPSHOT",
      "anchor": "chk-read-snapshot",
      "covers": ["PERSISTENCE.READ_SNAPSHOT"]
    },
    {
      "id": "CHK00.SNAPSHOT",
      "anchor": "chk-snapshot",
      "covers": ["PERSISTENCE.SNAPSHOT"]
    },
    {
      "id": "CHK00.AUDIT.APPEND",
      "anchor": "chk-audit-append",
      "covers": ["AUDIT.APPEND_ONLY", "TX.UOW", "M00.003"]
    },
    {
      "id": "CHK00.JOB.EXECUTION",
      "anchor": "chk-job-execution",
      "covers": ["JOBS.EXECUTION", "JOBS.COORDINATOR", "RUNTIME.SHUTDOWN", "M00.004"]
    },
    {
      "id": "CHK00.SEED.RESET",
      "anchor": "chk-seed-reset",
      "covers": ["DEV.SEED", "DEV.DB_RESET", "MIGRATION.MANIFEST"]
    },
    {
      "id": "CHK00.RUNTIME.OBSERVATION",
      "anchor": "chk-runtime-observation",
      "covers": ["RUNTIME.CONTROL_OBSERVATION", "RUNTIME.TRUSTED_CONTROL", "RUNTIME.HEALTH"]
    },
    {
      "id": "CHK00.CAPABILITIES",
      "anchor": "chk-capabilities",
      "covers": ["CAPABILITY.REGISTRY", "UI.BOOTSTRAP", "UI.CAPABILITY_STATE"]
    },
    {
      "id": "CHK00.UI.WORKSPACES",
      "anchor": "chk-ui-workspaces",
      "covers": ["UI.WORKSPACE_REGISTRY", "UI.CAPABILITY_STATE", "UI.ROUTING"]
    },
    {
      "id": "CHK00.UI.VISUAL_GRAMMAR",
      "anchor": "chk-ui-visual-grammar",
      "covers": ["UI.VISUAL_GRAMMAR", "UI.SHELL", "UI.RESPONSIVE", "UI.BRAND", "UI.TOKENS"]
    },
    {
      "id": "CHK00.UI.TEXT_INTEGRITY",
      "anchor": "chk-ui-text-integrity",
      "covers": ["UI.TEXT_INTEGRITY"]
    },
    {
      "id": "CHK00.UI.PANE_FOCUS",
      "anchor": "chk-ui-pane-focus",
      "covers": ["UI.PANE_FOCUS", "UI.SELECTION", "UI.SCROLL"]
    },
    {
      "id": "CHK00.UI.STATUS_STRIP",
      "anchor": "chk-ui-status-strip",
      "covers": ["UI.OPERATOR_STATUS_STRIP"]
    },
    {
      "id": "CHK00.UI.STYLE_LIBRARY",
      "anchor": "chk-ui-style-library",
      "covers": ["UI.STYLE_LIBRARY"]
    },
    {
      "id": "CHK00.UI.SCROLLBAR",
      "anchor": "chk-ui-scrollbar",
      "covers": ["UI.SCROLLBAR"]
    },
    {
      "id": "CHK00.PAGE.COLLECTION",
      "anchor": "chk-page-collection",
      "covers": ["QUERY.PAGE", "API.CLIENT"]
    },
    {
      "id": "CHK00.UI.ROUTING",
      "anchor": "chk-ui-routing",
      "covers": ["UI.ROUTING"]
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
      "covers": ["UI.DIAGNOSTICS_STATE", "UI.ERROR_STATE", "RUNTIME.HEALTH", "DIAGNOSTICS.OPERATOR_LOGS", "DIAGNOSTICS.SAFE"]
    },
    {
      "id": "CHK00.UI.APPEARANCE",
      "anchor": "chk-ui-appearance",
      "covers": ["UI.APPEARANCE", "UI.BRAND", "UI.TOKENS"]
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
      "covers": ["MIGRATION.MANIFEST", "PERSISTENCE.SCHEMA_VERIFY", "M00.001"]
    },
    {
      "id": "CHK00.MIGRATION.STATUS",
      "anchor": "chk-migration-status",
      "covers": ["MIGRATION.STATUS"]
    },
    {
      "id": "CHK00.REPLAY.EXACT",
      "anchor": "chk-replay-exact",
      "covers": ["COMMAND.REPLAY", "M00.002"]
    },
    {
      "id": "CHK00.JOB.RECOVERY",
      "anchor": "chk-job-recovery",
      "covers": ["JOBS.COORDINATOR"]
    },
    {
      "id": "CHK00.CONTRACT.SYNC",
      "anchor": "chk-contract-sync",
      "covers": ["CONTRACT.SOURCE"]
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
      "covers": ["UI.RESPONSIVE", "UI.WORKING_COPY", "WORKING_COPY.STORE", "M00.005"]
    },
    {
      "id": "CHK00.UI.HOLD",
      "anchor": "chk-ui-hold",
      "covers": ["UI.CONFIRMATION", "SECURITY.DELIBERATE_PROOF"]
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

Start one real host process and observe the process-local startup sequence `BOOTSTRAPPING -> MIGRATING -> BINDING -> SERVING_NOT_READY -> READY`. Verify readiness verification does not fabricate a durable `VERIFYING` state, ordinary application routes reject before READY, and the process never reports controller-only absence/trust states as its own lifecycle. Trigger graceful shutdown and verify `QUIESCING -> EXITING` rejects new mutations, stops new job claims, drains bounded work, removes exact-owned runtime/tray artifacts and releases the instance lock before process exit. Inject a required readiness failure and verify FAILED is truthful and never reported as READY.

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

<a id="chk-auth-local-admin"></a>
## CHK00.AUTH.LOCAL_ADMIN

On a freshly migrated unseeded credential table, bootstrap shows `setup_required` and ordinary workspaces remain gated. Reject passwords shorter than 12 Unicode scalars, larger than 1024 UTF-8 bytes, mismatched confirmation, or any setup attempt after the singleton exists. Verify exact password bytes are hashed with the accepted Argon2id profile, only the PHC verifier is persisted, one stable actor UUID is created, and no raw password/confirmation reaches logs, diagnostics, audit, replay, browser storage, or errors.

Then verify password-only login: correct password issues a current-run session, wrong password returns the same public `AUTH_INVALID_CREDENTIALS` response, the per-run delay begins after five consecutive failures with 1/2/4/8-second monotonic steps and no durable lockout, successful login clears the failure counter, and logout invalidates the presented session. A new process run requires a fresh browser session but reuses the persisted credential. Password/profile management remains absent.

<a id="chk-session-csrf"></a>
## CHK00.SESSION.CSRF

Using a test authentication provider, issue a browser session and verify exact Host, current-run binding, idle/absolute deadlines, host-only HttpOnly SameSite cookie behavior, and mutation CSRF + exact Origin checks. Reject wrong run, expired session, missing/null/cross-origin Origin, wrong CSRF, proxy/forwarded substitution, and invalid Fetch Metadata before application dispatch. Confirm browser never receives run-control secret.

<a id="chk-read-snapshot"></a>
## CHK00.READ.SNAPSHOT

Within one projection, read several related facts while a concurrent writer commits between individual SELECT opportunities. Verify every participating read observes the same snapshot generation and one captured as-of reference. Inject BEGIN/read/commit setup failures and verify the read connection/transaction is always cleaned up and no mixed-generation projection is returned.

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

<a id="chk-runtime-observation"></a>
## CHK00.RUNTIME.OBSERVATION

From the launcher/controller side, exercise each observation independently from the host lifecycle: no registry/process -> `absent`; plausible registry before trust -> `candidate`; trusted host before READY -> `verified_not_ready`; trusted READY host -> `verified_ready`; dead/replaced prior run -> `stale`; wrong ACL/origin/secret/process birth/image/protocol -> `untrusted`; plausible exact host with unreachable authenticated health -> `unreachable`.

Verify only `verified_ready` authorizes ordinary Open/reuse, verified states use exact current-run trust, and no observation changes the host state machine. Human-facing launcher text may say “Stopped” for `absent`, but the authenticated host API never returns STOPPED as a process state.

<a id="chk-ui-workspaces"></a>
## CHK00.UI.WORKSPACES

Render the shell with all product capabilities unavailable, then make selected capabilities available/development. Primary navigation must contain exactly, in order: **Overview, Tickets, Objectives, Inventory, Infrastructure, Settings**. Diagnostics remains a distinct System/Foundation destination.

Assert that capability IDs or module names such as `customers`, `products`, `sla`, `workflows`, `finance`, or arbitrary registered test capabilities do **not** create primary workspace labels. In particular, the shell must never show invented top-level **Finance**, **Products**, **Service levels**, **Workflows**, or **Customers** entries unless UI.WORKSPACE_REGISTRY is deliberately revised.

Direct navigation to unavailable declared workspaces remains understandable and sends no owner API request. Deep feature routes may exist without becoming primary navigation entries.

<a id="chk-ui-visual-grammar"></a>
## CHK00.UI.VISUAL_GRAMMAR

Perform a Foundation shell convergence review at three representative widths: wide desktop, around the initial `1040 CSS px` split threshold, and phone/narrow width.

At wide desktop verify:
- operational hierarchy is primarily alignment, compact spacing, typography and thin pane separators rather than large rounded floating dashboard cards;
- Diagnostics current-run/runtime/capability/log information reads as a dense operational console with compact rows and panes;
- the working pane system owns/fills the available application height below top chrome and above the status strip without inventing fake content; facts remain top-aligned and pane-local scrolling owns overflow;
- pane sizing may be intentionally asymmetric when information density differs; an equal four-card dashboard is not required;
- navigation/status/data chrome uses the intended monospace hierarchy while long explanatory/help text remains readable;
- page title, pane heading and compact label/value/evidence text are visibly distinct hierarchy levels;
- Electric-blue-derived accent identifies the current interaction locus sparingly rather than decorating every heading;
- normal controls are compact/flat enough to read as operational actions and large full-width CTA treatment is limited to genuine gates/consequential narrow actions;
- no decorative whitespace occupies more visual attention than the facts/actions it separates.

At narrow width verify:
- the desktop grid is **recomposed**, not copied into one extremely long stack;
- product navigation is a compact labelled tab/command strip with bounded horizontal/overflow behavior;
- Diagnostics/workbench panes can be switched deliberately one-at-a-time while preserving access to all facts/actions;
- selected pane, navigation state, working copies, warnings and focus survive threshold changes.

Capture development screenshots under ignored scratch output for review; screenshots are evidence only and never runtime/design authority. Compare structure/density against the approved directional references without copying their branding/trade dress.

<a id="chk-ui-pane-focus"></a>
## CHK00.UI.PANE_FOCUS

Build a synthetic three-pane shell with a selectable list, evidence pane and activity pane. Exercise pointer activation, Tab/Shift+Tab traversal, arrows/page/scroll commands, row selection, modal open/close and responsive pane switching.

Verify exactly one logical pane owns pane-local keyboard/scroll commands at a time; active pane, DOM focus, row selection, opened record and hover remain distinguishable. Activating a pane must not create a record selection. Pointer or programmatic activation after prior keyboard use must never produce the current full-pane rectangular focus-outline regression; pane focus is localized to the rail/header treatment and nested controls still receive normal focus-visible rings. Modal focus temporarily supersedes and then restores the surviving invoker pane. Crossing the responsive threshold preserves the logical active pane where possible and otherwise chooses a deterministic labelled fallback without losing filters/working copies.

At least one non-color structural cue plus the restrained current-locus treatment identifies the active pane under normal and forced-color/high-contrast presentation. No visible `ACTIVE` word/badge is required in the pane heading; screen-reader active-pane status remains available.

<a id="chk-ui-status-strip"></a>
## CHK00.UI.STATUS_STRIP

Render the authenticated shell against healthy READY, pre-ready/degraded and partially unavailable provider states. Verify the persistent bottom strip presents bounded current run/readiness/schema/build/trust facts without becoming a second event log or navigation area.

At wide width the strip remains one compact line. At phone/narrow width it preserves run identity + readiness and exposes secondary facts through a labelled overflow/detail affordance rather than wrapping into a tall footer. Exact canonical details remain available through Diagnostics.

Assert no secrets, full tokens, unrestricted filesystem paths or domain data appear; actual degraded/failed conditions are distinguishable from normal READY state without relying on color alone.

<a id="chk-ui-style-library"></a>
## CHK00.UI.STYLE_LIBRARY

Inspect/build the Main style entry and prove the shared style system has one declared cascade order and no append-only override dependency. Shared Foundation controls/panes/navigation/forms/collections/status consume semantic tokens/primitives; feature-local styles do not override global body/button/input/shell/pane selectors.

Fail the check on duplicate raw palette declarations outside the token owner, ordinary `!important`, selector-order overrides that cross owning layers, or a feature copy of an existing shared primitive. Verify the stable `soma.css` entry can import/re-export the layered library without changing feature import paths.

Exercise the shared metric grid with 6 and 7 items. Equal columns remain aligned; the odd final metric is intentionally centered/spanned rather than visually stranded.

<a id="chk-ui-scrollbar"></a>
## CHK00.UI.SCROLLBAR

Render governed vertical/horizontal scroll owners in Core Dark using Chromium/WebKit-compatible styling and standards `scrollbar-color`/`scrollbar-width` behavior where supported. Verify shared semantic scrollbar tokens produce a visible themed thumb/track across shell, panes, lists, navigation and modal overflow without per-feature CSS.

At hover/active state the thumb gains contrast without using warning/destructive/success semantics. At 200% zoom scrollbars remain usable. In forced-colors/high-contrast mode, branded scrollbar forcing is disabled so the system can provide appropriate colors. Where custom scrollbar theming is unsupported, native scrolling remains fully usable.

<a id="chk-ui-text-integrity"></a>
## CHK00.UI.TEXT_INTEGRITY

Build and load the local Main bundle with representative separators, SOMA brand text, dates and diagnostics footer/status strings. Assert UTF-8 source/transport rendering and fail on visible mojibake/replacement patterns including `Â·`, `Ã`, or `�` in governed shell fixtures.

Verify the intended separator renders consistently across supported browser/Windows environments; when a glyph/font path is unavailable the presentation falls back to readable ASCII rather than mis-decoded text.

<a id="chk-capabilities"></a>
## CHK00.CAPABILITIES

Compose a build with one real feature provider, one development capability, and one absent future workspace owner. Verify the registry advertises only actually registered descriptors, duplicate/conflicting registration fails composition, and Foundation does not synthesize speculative `finance/products/sla/workflows/customers` entries. UI.WORKSPACE_REGISTRY still renders declared product workspaces unavailable when their owner capability is absent. Directly navigating to an unavailable workspace produces an understandable unavailable surface rather than a stub request/500.

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

Open the System/Diagnostics surface on a healthy and partially failing host. Verify build/run/schema/capability/job/executor/connection/transaction/log state is visible, local time is readable, and canonical evidence remains inspectable where appropriate. Durable-job metrics remain horizontally balanced for the current odd number of states rather than leaving the final state stranded in one half-column. Normal lifecycle transitions render as runtime/event chronology; warning/error codes remain a separate list and READY/TRAY_READY-style normal events never masquerade as errors. Capability rows correspond to actually registered descriptors; absent future workspace owners do not appear as synthetic capability entries. Repeated unavailable state remains concise while its full meaning is accessible. Provider failure produces partial/unavailable panels without mutating jobs/migrations/domain state or exposing secrets/raw bodies.

<a id="chk-ui-appearance"></a>
## CHK00.UI.APPEARANCE

Load a first-run and authenticated shell with no stored appearance preference and verify SOMA Core Dark is selected deterministically. Verify shared components consume semantic tokens rather than raw theme colors and retain readable brand, focus, selection, warning, destructive, disabled, and unavailable states. Inject an invalid future appearance preference and verify deterministic fallback to Core Dark without feature-specific CSS branching.

<a id="chk-ui-accessibility"></a>
## CHK00.UI.ACCESSIBILITY

Exercise shared shell/list/dialog/autocomplete/confirmation controls using keyboard only, pointer, touch-equivalent input, 200% text zoom, reduced motion, forced colors/high contrast, and screen-reader semantics where automated/manual tooling permits. Verify visible focus, non-color state meaning, equivalent command result, safe dialog behavior, and labelled alternatives for icon-only actions.


<a id="chk-runtime-trust"></a>
## CHK00.RUNTIME.TRUST

Start a real local host, verify its registry/DPAPI run secret/process birth/origin/health identity, and control it successfully. Then independently test malformed registry shape, alternate/non-literal loopback host, wrong run secret, wrong run/data/protocol identity, stale PID, PID birth reuse, unexpected process image, redirect/proxy behavior, and replaced runtime artifacts. Every adversarial case fails closed without opening or stopping the wrong process.

<a id="chk-launchers-lifecycle"></a>
## CHK00.LAUNCHERS.LIFECYCLE

From a clean supported Windows source checkout, run `soma_setup.bat`, then `soma_run_console.bat`; verify foreground sanitized logging, READY origin, tray presence, and Ctrl+C graceful shutdown. Then execute `soma_run.bat` twice, `soma_stop.bat` twice, and a fresh run/stop cycle. The second run reuses the verified host, the second stop is idempotent, each new run receives a new run identity, no runtime action installs dependencies, and all detached startup/runtime logs are available under the canonical diagnostics root.

Exercise `soma_reset_dev.bat`: verify it prints the exact LocalAppData development instance, does nothing when confirmation is absent/wrong, refuses a non-development target, gracefully stops a verified live host only after literal `RESET` confirmation, rebuilds migrations + DEV.SEED, leaves SOMA stopped, and never deletes the checkout or an unrelated/packaged instance.

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

Build a fresh disposable database from the manifest and verify declared owner order/dependencies/hashes plus committed schema tables/indexes/triggers, columns, foreign keys, effective FK indexes, ledger agreement, quick/FK checks, and append-only probes. Rebuild a fresh test instance again from zero. A tampered SQL hash, unresolved dependency, extra/missing authoritative schema object, ledger mismatch, or FK-index gap blocks readiness.

<a id="chk-migration-status"></a>
## CHK00.MIGRATION.STATUS

With no live host, safely inspect a locked development instance and distinguish not-initialized/current/pending/drift/future/unsafe-sidecar/inspection-failure states without creating or repairing anything. Then start a verified host and confirm status prefers authenticated live state. A potentially owned or unsafe offline database never gets opened as though exclusive access were proven.

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

Populate synthetic workbench state with filters, active/selected record, active pane, scroll positions, dirty working copy, evidence pane, and operator status strip. Cross the initial 1040 CSS px split threshold in both directions and verify equivalent capability/state survives. Narrow composition must switch/recompose panes rather than merely append every desktop pane into one page-length vertical stack; status strip remains compact and active-pane identity remains understandable.

<a id="chk-ui-hold"></a>
## CHK00.UI.HOLD

Exercise a synthetic registered deliberate action. Verify continuous 3000 ms client monotonic hold plus the session/run/target-bound server challenge cannot complete before the server's 3000 ms minimum, returns at most one short-lived single-use proof, and dispatches once. Release, route/target/revision/preview change, stale dependency, visibility invalidation, challenge expiry, or scroll-classified movement resets/abandons and dispatches zero commands. Reuse/wrong-binding proof fails closed and never substitutes for owner eligibility/freshness checks.

<a id="chk-doc-impact"></a>
## CHK00.DOC.IMPACT

Validate metadata/index creation, modify one item and one mapped source path, and verify direct/indirect impact paths. Remove an edge and verify baseline/current union still reports the former dependent. Unmapped changed code is reported as a gap. Verify `docs/LLD/CONTINUE.md` resolves to an existing scope/goal/ledger, duplicate or malformed migration-row IDs fail validation, and a goal marked `working` fails while any matching `RNN.KK-*` row remains unchecked/PENDING.
