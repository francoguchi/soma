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
| Implementation note | IMP-01-06 is reopened for final usability/polish acceptance. R01.06-A..D remain closed; R01.06-E is the active refinement. The Browse/Create/Open ownership model is accepted, but search consistency, discoverability, copy, empty states, collection-row state, action placement and workbench-level navigation still require polish. Scope-01 remains at its final goal; no Scope-02 implementation is started. |
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

Current checkpoint: pushed UI checkpoint `20dfdcdaa72f1c47858e21dac3bc6f464e8b1650` completed R01.06-D's visual-grammar restoration, but subsequent review found remaining usability friction. R01.06-E is now the active Scope-01 implementation refinement.

Accepted and preserved:
- Browse is collection/search oriented and renders no empty Work/Evidence panes.
- Create is a focused pre-identity form.
- Open alone owns the three-pane collection / Details / Evidence & history workbench.
- collection/filter/selection/page/scroll/working-copy context survives accepted navigation and return paths.
- current Foundation navigation/icon/accent/action grammar remains the baseline.

R01.06-E must standardize shared owner-backed search placement/state, remove duplicate or technical operator copy, correct collection-row selected/open/focus presentation, clarify command versus navigation hierarchy, resolve redundant Back/Cancel semantics, move whole-workbench navigation outside child panes, improve empty/no-result states, and preserve vivid but restrained SOMA Core Dark hierarchy.

Foundation now records `UI.SEARCH` as the common search contract. A future shell-like SOMA command surface is also recorded as **deferred design only**: examples such as `operator@soma:~$ cd settings/profile` and `operator@soma:~$ find <term>` may later map onto closed routing and owner search contracts. It is not arbitrary OS shell execution and no fake/disabled command bar is required in this refinement.

Do not start Scope-02 implementation. Do not change Scope-01 domain/query/API/schema semantics merely for presentation.

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
