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
