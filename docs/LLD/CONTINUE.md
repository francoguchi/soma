# Continue SOMA

This is the single current-state entry point for humans and agents. Do not append history here; completed evidence stays in implementation goals and migration dispositions.

## Active lanes

| Lane | Current value |
|---|---|
| Implementation scope | `00 — Foundation` |
| Implementation branch | `feat/00-foundation` |
| Implementation goal | `IMP-00-07 — Foundation shell and runtime convergence` |
| Implementation goal file | `docs/implementation/00/00.07.md` |
| Implementation migration ledger | `docs/LLD/00/migration.md` |
| Queued next implementation | `01 — Identity / Reference` (`IMP-01-01..06`), after required Foundation checkpoints |
| Design scope | `00 — Foundation convergence` |
| Design branch | `design/00-foundation-convergence` |
| Design source | live Foundation desktop/mobile review + accepted SOMA/init.Habits directional references |
| Design migration ledger | `docs/LLD/00/migration.md` |
| Overall migration map | `docs/LLD/MIGRATION.md` |
| Mode | Foundation convergence checkpoint; Scope 02 design is paused, not discarded |
| Implementation note | local `feat/00-foundation` may contain completed/unpushed Foundation work; reconcile the accepted docs surgically and preserve local implementation before starting 00.07 |
| Design blocker | none; second live visual refinement is accepted on `main`, awaiting `IMP-00-07` implementation/live review before Scope 02 resumes |
| Certification | deferred until whole-application implementation and live testing |

## Resume

The intended handoff can be as small as:

- **Implementation:** “Read `docs/LLD/CONTINUE.md` and continue the implementation lane.”
- **Design:** “Read `docs/LLD/CONTINUE.md` and continue the design lane.”

`AGENTS.md` supplies the standing implementation rules.

### Implementation lane

1. Read the active implementation goal.
2. Read only the LLD items referenced by that goal and the matching active-goal rows in the implementation scope migration ledger.
3. Reuse/restructure donor code only where the current LLD still wants the same behavior.
4. Implement, run the goal's focused checks plus directly affected tests, and fix failures.
5. Update the goal's Run/Remaining/status, close its migration rows, then advance this file to the next implementation goal.

Current next action: reconcile the latest accepted Scope-00/`IMP-00-07` refinement into local `feat/00-foundation` without overwriting completed work. Make detached Run windowless; make Stop clean only proven-dead exact-owned stale runtime artifacts; keep untrusted/unreachable/live ambiguity fail-closed. Then apply the final style-library refinement: richer semantic terminal accents, muted-green READY, shared `$` / `--` / `>` cues, active-title tint, fixed pane header + scrollable body, and vertically centered Durable-job contents with the odd final cell left in natural asymmetric grid order. Rerun launcher/runtime/style/focus/scroll/live checks before resuming Scope 02.

### Design lane

1. Read the active design scope README and migration ledger.
2. Read only the named Beta donor packet/files required for the behavior cluster being migrated.
3. Translate behavior into current ownership; do not reproduce Beta packet/file structure merely because it existed.
4. Record every donor behavior/code slice as reused, rewritten, rejected, deferred, or new.
5. Update the design scope backend/frontend/checks/contracts/migrations and create implementation goals only after ownership and behavior are clear.

Current next action: keep `design/02-tickets-core` frozen; implement and live-review `IMP-00-07`. Resume Scope 02 only after that convergence goal is working.

## Do not

Do not reconstruct project status by rereading Alpha/Beta or the whole repository. Do not copy Beta wholesale, preserve its old directory ownership, or treat compiled/static artifacts as authority.

Do not merge implementation-in-progress from `feat/00-foundation` into design branches merely to inspect it. Foundation convergence updates the owning Scope-00 LLD first, then Codex reconciles those changes into its local implementation. Scope 02 remains frozen until the convergence checkpoint is live-reviewed.

Do not create a branch/PR/certification packet per goal, run unrelated full suites, perform release packaging/signing, or block design on future implementation details. A `working` goal is a development checkpoint, not certification.

Do not add another handover/progress/status file. Update this pointer instead.

## Checkpoint rule

An implementation-goal transition changes only the goal file, its scope migration rows, and this pointer unless behavior itself changed.

A design-scope transition changes the active scope's LLD/migration files, the global migration map when ownership/closure changes, and this pointer. If a design decision changes Foundation behavior, update scope 00 explicitly rather than duplicating the rule in scope 01.
