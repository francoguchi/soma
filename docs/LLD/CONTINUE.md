# Continue SOMA

This is the single current-state entry point for humans and agents. Do not append history here; completed evidence stays in implementation goals and migration dispositions.

## Active lanes

| Lane | Current value |
|---|---|
| Implementation scope | `01 — Identity / Reference` |
| Implementation branch | `feat/01-identity-reference` |
| Implementation goal | `IMP-01-06 — Reference and Settings workspaces` |
| Implementation goal file | `docs/implementation/01/01.06.md` |
| Implementation migration ledger | `docs/LLD/01/migration.md` |
| Queued next implementation | `02 — Tickets Core`, after Scope-02 design approval and required Scope-01 dependencies |
| Design scope | `02 — Tickets Core` |
| Design branch | `design/02-tickets-core` |
| Design source | `SOMA Beta LLD-03 — Service Requests, RFCs, Device References, Ticket Relationships` |
| Design migration ledger | `docs/LLD/02/migration.md` |
| Overall migration map | `docs/LLD/MIGRATION.md` |
| Mode | parallel design N+1 / implementation N |
| Implementation note | IMP-01-06 is working; R01.06-A..B are closed. Settings-owned Reference, Profile and registered Preferences surfaces are implemented and exercised. Scope-01 implementation is at its final goal checkpoint; no later goal is allocated or started. |
| Design blocker | none; Scope 02 design resumes from the merged Foundation baseline |
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

Current checkpoint: IMP-01-06 is working. All 203 affected Reference/recovery/runtime/browser checks passed across the focused run and corrected shared-browser rerun; all 60 Main tests, typecheck/build, contracts/Ruff/diff/impact passed. Real authenticated Chrome exercised Customer/Contact/Dispatch, conflict review, explicit ambiguity and bounded paging/history, lifecycle, Profile/registered Preferences, recovery/stale intent and responsive/forced-color panes. Schema remains generation 10 / M01.004; no reset was required and the canonical instance remains stopped. Generated identity/assets are synchronized. Scope-01 implementation ends at this checkpoint. Do not broaden into Scope-02 implementation; its design approval and goal allocation remain separate.

### Design lane

1. Read the active design scope README and migration ledger.
2. Read only the named Beta donor packet/files required for the behavior cluster being migrated.
3. Translate behavior into current ownership; do not reproduce Beta packet/file structure merely because it existed.
4. Record every donor behavior/code slice as reused, rewritten, rejected, deferred, or new.
5. Update the design scope backend/frontend/checks/contracts/migrations and create implementation goals only after ownership and behavior are clear.

Current next action: resume `design/02-tickets-core` with D02-A through D02-C first: Service Request identity/adoption, Customer/Contact relationship ownership, and accepted Advanced Search source authority. Continue recording every Beta LLD-03 behavior as reused, rewritten, rejected, deferred, or new; do not allocate Scope-02 implementation goals until its pre-approval audit is complete.

## Do not

Do not reconstruct project status by rereading Alpha/Beta or the whole repository. Do not copy Beta wholesale, preserve its old directory ownership, or treat compiled/static artifacts as authority.

Do not merge implementation-in-progress from `feat/01-identity-reference` into the Scope-02 design branch merely to design Tickets. Scope 02 consumes accepted contracts from `main`; if Scope-01 implementation proves an accepted contract wrong, update the owning LLD explicitly and reconcile dependents.

Do not create a branch/PR/certification packet per goal, run unrelated full suites, perform release packaging/signing, or block design on future implementation details. A `working` goal is a development checkpoint, not certification.

Do not add another handover/progress/status file. Update this pointer instead.

## Checkpoint rule

An implementation-goal transition changes only the goal file, its scope migration rows, and this pointer unless behavior itself changed.

A design-scope transition changes the active scope's LLD/migration files, the global migration map when ownership/closure changes, and this pointer. If a design decision changes Foundation behavior, update scope 00 explicitly rather than duplicating the rule in scope 01.
