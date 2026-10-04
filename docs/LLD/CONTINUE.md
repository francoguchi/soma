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
| Mode | Foundation implementation checkpoint complete; PR #1 reconciliation is the only remaining branch-hygiene step before `IMP-01-01` |
| Implementation note | `IMP-00-01..07` are working and pushed. PR #1 (`feat/00-foundation` → `main`) is currently non-mergeable/dirty because `main` contains later accepted design/docs. Reconcile `main` into this branch surgically, preserve both implementation and accepted docs, rerun affected checks, then merge. |
| Design blocker | none; IMP-00-07 passed focused checks and required live review; Scope 02 may resume when selected |
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

Current checkpoint: IMP-00-07 is working and pushed; no Foundation behavior work remains. PR #1 is currently `dirty`, so the next action is branch reconciliation only: merge/reconcile current `main` into `feat/00-foundation`, resolve documentation conflicts in favor of the latest accepted baseline while preserving all Scope-00 implementation/evidence, rerun directly affected checks, and update PR #1. After it merges, start `IMP-01-01` from the merged `main`.

### Design lane

1. Read the active design scope README and migration ledger.
2. Read only the named Beta donor packet/files required for the behavior cluster being migrated.
3. Translate behavior into current ownership; do not reproduce Beta packet/file structure merely because it existed.
4. Record every donor behavior/code slice as reused, rewritten, rejected, deferred, or new.
5. Update the design scope backend/frontend/checks/contracts/migrations and create implementation goals only after ownership and behavior are clear.

Current next action: the Foundation style-library prerequisite is satisfied. Resume `design/02-tickets-core` only when selected; no Scope-02 work was made in this pass.

## Do not

Do not reconstruct project status by rereading Alpha/Beta or the whole repository. Do not copy Beta wholesale, preserve its old directory ownership, or treat compiled/static artifacts as authority.

Do not merge implementation-in-progress from `feat/00-foundation` into design branches merely to inspect it. Foundation convergence updates the owning Scope-00 LLD first, then Codex reconciles those changes into its local implementation. The accepted style-library checkpoint has been live-reviewed; subsequent design remains a separately selected lane.

Do not create a branch/PR/certification packet per goal, run unrelated full suites, perform release packaging/signing, or block design on future implementation details. A `working` goal is a development checkpoint, not certification.

Do not add another handover/progress/status file. Update this pointer instead.

## Checkpoint rule

An implementation-goal transition changes only the goal file, its scope migration rows, and this pointer unless behavior itself changed.

A design-scope transition changes the active scope's LLD/migration files, the global migration map when ownership/closure changes, and this pointer. If a design decision changes Foundation behavior, update scope 00 explicitly rather than duplicating the rule in scope 01.
