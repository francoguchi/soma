# Continue SOMA

This is the single current-state entry point for humans and agents. Do not append history here; completed evidence stays in implementation goals and migration dispositions.

## Active lanes

| Lane | Current value |
|---|---|
| Implementation scope | `00 — Foundation` |
| Implementation branch | `feat/00-foundation` |
| Implementation goal | `IMP-00-01 — Foundation primitives and tooling` |
| Implementation goal file | `docs/implementation/00/00.01.md` |
| Implementation migration ledger | `docs/LLD/00/migration.md` |
| Design scope | `01 — Identity / Reference` |
| Design branch | `design/01-identity-reference` |
| Design source | `SOMA Beta LLD-02 — Identity, Settings, Contacts, Organizations, Locations` |
| Design migration ledger | `docs/LLD/01/migration.md` |
| Overall migration map | `docs/LLD/MIGRATION.md` |
| Mode | parallel design N+1 / implementation N |
| Implementation blockers | none known in this design branch |
| Design blockers | none; scope 01 remains unapproved until PASS-1..PASS-4 in `docs/LLD/01/migration.md` complete |
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

Current next action: continue `IMP-00-01` on `feat/00-foundation`.

### Design lane

1. Read the active design scope README and migration ledger.
2. Read only the named Beta donor packet/files required for the behavior cluster being migrated.
3. Translate behavior into current ownership; do not reproduce Beta packet/file structure merely because it existed.
4. Record every donor behavior/code slice as reused, rewritten, rejected, deferred, or new.
5. Update the design scope backend/frontend/checks/contracts/migrations and create implementation goals only after ownership and behavior are clear.

Current next action: run scope-01 pre-approval PASS-1 through PASS-4 from `docs/LLD/01/migration.md`; only after all four pass should the design be approved and partitioned into `IMP-01-xx` goals.

## Do not

Do not reconstruct project status by rereading Alpha/Beta or the whole repository. Do not copy Beta wholesale, preserve its old directory ownership, or treat compiled/static artifacts as authority.

Do not merge implementation-in-progress from `feat/00-foundation` into the design branch merely to design scope 01. Scope 01 consumes accepted Foundation contracts from `main`; if implementation later proves a contract wrong, update the owning LLD and reconcile dependents.

Do not create a branch/PR/certification packet per goal, run unrelated full suites, perform release packaging/signing, or block design on future implementation details. A `working` goal is a development checkpoint, not certification.

Do not add another handover/progress/status file. Update this pointer instead.

## Checkpoint rule

An implementation-goal transition changes only the goal file, its scope migration rows, and this pointer unless behavior itself changed.

A design-scope transition changes the active scope's LLD/migration files, the global migration map when ownership/closure changes, and this pointer. If a design decision changes Foundation behavior, update scope 00 explicitly rather than duplicating the rule in scope 01.
