# 00 — Foundation migration ledger

Track migration decisions from SOMA Beta into the current Foundation implementation. This is a reuse ledger, not behavioral authority; current behavior is defined by the scope-00 LLD.

**Pins:** Beta design `9a0e891127a771251afccca1a281b7ef7dde9e5f`; Beta implementation donor `fbe3821ac0b52802ba8265f979590e75c3ac1209`.

A checked box means the **migration decision is closed**, not that the implementation goal is complete. For donor rows, check the row only after the agent records whether the slice was reused, rewritten, rejected, or intentionally deferred. Goal completion remains in `docs/implementation/00/`.

## Design migration closure

The pinned Beta donor inventory contains 132 design files: LLD-01 Foundation Runtime (36), LLD-12 Security/Packaging (54), and LLD-10 UI Workbenches (42). The current scope-00 design accounts for them by behavior rather than preserving their packet/file layout.

### LLD-01 — Foundation Runtime

- [x] Runtime host, instance ownership, loopback, health/status, start/stop and runtime types/routes -> `RUNTIME.INSTANCE`, `RUNTIME.LIFECYCLE`, `RUNTIME.HEALTH`, `RUNTIME.SHUTDOWN`.
- [x] Connections, UnitOfWork, read consistency and backup snapshot mechanics -> `PERSISTENCE.CONNECTION`, `PERSISTENCE.READ_SNAPSHOT`, `PERSISTENCE.SNAPSHOT`, `TX.UOW`.
- [x] Migration runner, manifest, status, schema verification and FK/index coverage -> `MIGRATION.MANIFEST`, `MIGRATION.STATUS`, `PERSISTENCE.SCHEMA_VERIFY`, `DEV.DB_RESET`.
- [x] Strict JSON, common interfaces/bounds/errors -> `SERIALIZATION.STRICT_JSON`, `CONTRACT.SOURCE`, `ERROR.CONTRACT`, `TRACE.CORRELATION`.
- [x] Command boundary/receipt/exact stored results -> `COMMAND.REPLAY`.
- [x] Audit registry/writer/actions -> `AUDIT.APPEND_ONLY`.
- [x] Durable jobs, recovery, claim/checkpoint/terminal state -> `JOBS.COORDINATOR`, `JOBS.EXECUTION`.
- [x] Beta module maps, traceability and acceptance/failure suites are historical/regression donors only; they are not copied as current certification machinery.

### LLD-12 — Security / Packaging

- [x] DPAPI, live DEK and SQLCipher security handoff -> `SECURITY.LIVE_DATA_KEY`, `PERSISTENCE.CONNECTION`.
- [x] Trusted local instance/runtime registry/control -> `RUNTIME.TRUSTED_CONTROL`.
- [x] Password setup/login subset -> `AUTH.LOCAL_ADMIN`; password change/reset/recovery product UX is deferred.
- [x] Browser session/CSRF -> `SECURITY.BROWSER_SESSION`.
- [x] Deliberate-action challenge/proof -> `SECURITY.DELIBERATE_PROOF`.
- [x] Diagnostic sanitization -> `DIAGNOSTICS.SAFE`, `DIAGNOSTICS.OPERATOR_LOGS`.
- [x] Package lifecycle split: source launcher/tray/runtime-control behavior moved into Foundation; installer, signing, release packaging and release matrices are deferred.
- [x] Portable/managed backup, restore verification, backup jobs/history/retention are deferred to a later recovery/security owner; only `PERSISTENCE.SNAPSHOT` remains in Foundation.
- [x] Support-bundle artifact/export is deferred; current Foundation owns safe diagnostics only.
- [x] Auto-login, password management settings and broader security-status product UX are deferred.
- [x] Beta security packaging/traceability/acceptance suites are selective regression donors, not per-goal certification requirements.

### LLD-10 — UI Workbenches

- [x] Selection/open, scroll ownership, autocomplete, deliberate hold, responsive composition and safe Undo -> shared Foundation interaction items.
- [x] Working-copy contracts/schema/commands/queries/migration -> `WORKING_COPY.STORE`, `UI.WORKING_COPY`, `M00.005`.
- [x] Shell, routing, dialog focus, semantic tokens and error/loading states -> current user-plane Foundation.
- [x] Appearance semantics stay Foundation-owned: `UI.APPEARANCE` defines Core Dark default plus `core_dark | system | light`. Once the typed ordinary-setting store exists, Foundation may register/persist that preference through the generic store without transferring semantic ownership. Beta terminal green/amber/violet skins are deferred and are not part of the current contract.
- [x] Beta domain-surface definitions are deferred to their owning future scopes; Foundation provides only the reusable shell/interactions.
- [x] Visual fixture/golden-baseline governance is deferred until the UI stabilizes. Focused component/browser assertions are enough during rapid implementation.
- [x] Beta LLD-10 acceptance/traceability suites are selective regression donors only; do not recreate the Beta certification packet.

## Implementation donor checklist

When closing a donor row, replace **PENDING** with `REUSED`, `REWRITTEN`, `REJECTED`, or `DEFERRED`, and append the new destination path(s) plus commit/check result when available. `REUSED` requires behavior comparison against the current LLD plus focused regression evidence; copying/importing a donor file is never sufficient by itself. `NEW` rows are already closed because no donor implementation exists.

### IMP-00-01 — Foundation primitives and tooling

- [ ] **R00.01-A — PENDING:** inspect/restructure `src/soma/foundation/{errors.py,identifiers.py,strict_json.py,runtime/paths.py}` into current errors/identity/serialization/config primitives. Preserve useful focused regression cases from `tests/test_foundation_json.py` and runtime-primitives tests.
- [ ] **R00.01-B — PENDING:** inspect Beta `pyproject.toml` plus `src/web/{package.json,package-lock.json,tsconfig.json,vite.config.mjs}` for compatible dependency/build pins; rewrite package paths/names for `src/core` + `src/main`.
- [x] **R00.01-C — NEW:** `FS.SAFE`, `FS.TEMP`, build identity, correlation context, JSON-Schema contract tooling, documentation impact checker and explicit test seams are new/current-architecture work; no Beta code migration is required.

### IMP-00-02 — Protected persistence bootstrap

- [ ] **R00.02-A — PENDING:** inspect/restructure `src/soma/security/crypto/{dpapi.py,live_key.py,sqlcipher_provider.py}` into Foundation security/persistence adapters; reuse only behavior compatible with current paths/trust boundaries.
- [ ] **R00.02-B — PENDING:** inspect/restructure `src/soma/foundation/persistence/{connections.py,backup_snapshot.py}`, `src/soma/foundation/migrations/{manifest.py,runner.py,verification.py}`, `src/soma/foundation/queries/status.py`, `src/soma/migrations/{0001_foundation.sql,0013_fk_index_coverage.sql,manifest.json}`, and `src/soma/schema_manifest.json` into current persistence/migration ownership, including read-snapshot cleanup and schema verification.
- [ ] **R00.02-C — PENDING:** selectively migrate focused regressions from `tests/test_foundation_{connection_safety,persistence,backup_snapshot,schema_verification,fk_index_coverage}.py` and `tests/test_security_{sqlcipher_native,windows_native}.py`; do not transplant unrelated Beta suite scaffolding.

### IMP-00-03 — Authoritative execution mechanics

- [ ] **R00.03-A — PENDING:** inspect/restructure `persistence/uow.py`, `application/{command_boundary.py,command_receipts.py}`, `audit/{registry.py,writer.py}`, `jobs/coordinator.py`, `queries/jobs.py`, and donor schema slices `src/soma/migrations/{0001_foundation.sql,0005_command_replay_results.sql,0008_durable_job_coalescing.sql}`; preserve one-outer-UoW, exact replay, append-only audit and claim/checkpoint invariants.
- [ ] **R00.03-B — PENDING:** selectively migrate focused replay/audit/job regressions from `tests/test_foundation_{replay_results,exact_response_guard,audit_allocations,multi_audit,durable_jobs,durable_job_claim_guard,durable_job_terminal_cancel}.py`.

### IMP-00-04 — Trusted local runtime

- [ ] **R00.04-A — PENDING:** inspect/restructure `src/soma/foundation/runtime/{host.py,instance_lock.py,loopback.py,registry.py,server.py}`, `src/soma/foundation/{contracts/foundation.py,queries/status.py,queries/data_instance_identity.py,api/routes_foundation.py}`, and composition hints in `src/soma/application.py` into current runtime/lifecycle/health composition.
- [ ] **R00.04-B — PENDING:** inspect/restructure `src/soma/security/runtime/{control.py,trust.py,source_control.py,windows.py,installation.py}`, `tools/source_launcher.py`, and the four Beta BAT launchers. Add the new guarded `soma_reset_dev.bat`; do not preserve Beta path/packet ownership.
- [ ] **R00.04-C — PENDING:** migrate an approved SOMA logo/icon master from ignored `.tmp/` into `src/main/assets/brand/` and derive deterministic tray/runtime variants. The ignored design files are references, never runtime dependencies.
- [ ] **R00.04-D — PENDING:** inspect `src/soma/ui/assets.py` and static-manifest logic only for useful serving/integrity behavior. **Do not copy** Beta's compiled `src/soma/ui/static/*` bundle; Main is rebuilt from current source.
- [x] **R00.04-E — NEW:** Beta had tray design but no completed tray implementation in the pinned donor slice; implement current native `Shell_NotifyIconW` behavior from the new LLD rather than inventing a compatibility wrapper.
- [ ] **R00.04-F — PENDING:** selectively migrate runtime/trust/launcher regressions from `tests/test_foundation_runtime_*.py`, `tests/test_foundation_failed_start_ownership.py`, `tests/test_security_{runtime_trust,control_http}.py`, `tests/test_source_launchers.py`, and `tests/source_runtime_browser.mjs`.

### IMP-00-05 — Runnable user-plane shell

- [ ] **R00.05-A — PENDING:** inspect/restructure `src/soma/security/auth/{passwords.py,sessions.py}`, `src/soma/security/{services/auth.py,contracts/security.py}`, and the auth portion of `src/soma/application.py` for minimal setup/login/logout only. Reject Beta password-management/auto-login behavior that current Foundation intentionally defers.
- [ ] **R00.05-B — PENDING:** inspect/restructure `src/web/app/{main.tsx,router.ts}`, `src/web/components/SomaShell.tsx`, `src/web/data/{http.ts,query-controller.ts}`, `src/web/state/{appearance.ts,ui-store.ts}`, `src/web/styles/soma.css`, and `src/web/index.html` into current `src/main` shell/API/appearance ownership.
- [ ] **R00.05-C — PENDING:** selectively reuse auth/navigation/appearance assertions from `tests/test_security_passwords.py`, `src/web/browser-tests/{navigation.spec.mjs,appearance.spec.mjs}`, and relevant source-runtime browser checks.
- [x] **R00.05-D — DEFERRED:** Beta domain workspace React components are not Foundation donors. Their useful layouts/behaviors migrate later with the owning domain scopes; future workspaces remain visible but disabled in the Foundation shell.

### IMP-00-06 — Shared interaction system

- [ ] **R00.06-A — PENDING:** inspect/restructure `src/soma/ui/{contracts.py,repository.py,commands.py,queries.py,routes.py,audit.py,composition.py}` plus working-copy portions of `registry.json`; `settings.py` remains a presentation-settings donor for the later settings owner rather than Foundation persistence into `WORKING_COPY.STORE` and its transport/application boundaries.
- [ ] **R00.06-B — PENDING:** inspect/restructure `src/web/interactions/{selection-open.ts,scroll-owner.ts,autocomplete.tsx,deliberate-hold.ts,safe-undo.ts,HoldButton.tsx}`, `layout/responsive.ts`, `working-copy/client.ts`, and shared components such as `BoundedCollection.tsx`, `SelectableCollection.tsx`, `Modal.tsx`, `UndoOpportunity.tsx`, and `WorkbenchShell.tsx`.
- [ ] **R00.06-C — PENDING:** selectively migrate `tests/test_ui_working_copies.py`, `src/web/tests/interactions.test.mjs`, and only the browser-workbench assertions that exercise shared interactions.
- [x] **R00.06-D — DEFERRED:** Beta visual fixture manifests/pixel baselines are not required for rapid Foundation implementation. Revisit visual-regression governance after the shared shell is stable.

## Cross-scope reconciliation

Scope-01 design review exposed three accepted Foundation clarifications:

- narrowed `DEV.DB_RESET`, `STATIC.ASSETS`, and `CONTRACT.SOURCE` impact `code_paths` so scope 00 does not falsely claim future domain code;
- allowed an optional composition-provided same-UoW descriptive-profile participant during Local Administrator first-run setup without moving credential/session ownership out of Foundation;
- confirmed appearance semantics remain Foundation-owned while later generic settings persistence is only storage.

These changes are design corrections, not new scope-01 ownership.

## Completion rule

Before an implementation goal becomes `working`, every migration row for that goal must be checked and carry an explicit disposition. Reuse is never assumed: reading a donor may result in `REWRITTEN` or `REJECTED`.

A donor-path audit against Beta implementation tree `710d975e38519ccd73ac048bbc8a07e8d1e88cca` verified the paths referenced above after correcting the old migration/frontend namespace locations. If a necessary donor is discovered outside these rows, add it here before relying on it.

Do not create another migration/progress ledger for Foundation. This file is the migration tracker; `docs/LLD/CONTINUE.md` is the current-state pointer; implementation goal files hold execution results.
