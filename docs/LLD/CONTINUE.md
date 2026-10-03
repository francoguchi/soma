# Continue SOMA

This is the single current-state entry point for humans and agents. Do not append history here; completed evidence stays in implementation goals and migration dispositions.

| Field | Current value |
|---|---|
| Active scope | `00 — Foundation` |
| Active branch | `feat/00-foundation` |
| Active goal | `IMP-00-01 — Foundation primitives and tooling` |
| Goal file | `docs/implementation/00/00.01.md` |
| Scope migration ledger | `docs/LLD/00/migration.md` |
| Overall migration map | `docs/LLD/MIGRATION.md` |
| Mode | fast iterative implementation |
| Blockers | none |
| Certification | deferred until whole-application implementation and live testing |

## Resume

The intended handoff can be as small as: **“Read `docs/LLD/CONTINUE.md` and continue.”** A coding agent may use the same instruction; `AGENTS.md` supplies the standing implementation rules.

1. Read the active goal file.
2. Read only the LLD items referenced by that goal and the matching active-goal rows in the scope migration ledger.
3. Reuse/restructure donor code only where the current LLD still wants the same behavior.
4. Implement, run the goal's focused checks plus directly affected tests, and fix failures.
5. Update the goal's Run/Remaining/status, close its migration rows, then change this file to the next goal.

The current next action is to begin `IMP-00-01` on `feat/00-foundation`.

## Do not

Do not reconstruct project status by rereading Alpha/Beta or the whole repository. Do not copy Beta wholesale, preserve its old directory ownership, or treat its compiled/static artifacts as authority.

Do not create a branch/PR/certification packet per goal, run unrelated full suites, perform release packaging/signing, or block progress on future scopes. A `working` goal is a development checkpoint, not certification.

Do not add another handover/progress/status file. Update this pointer instead.

## Checkpoint rule

A goal transition changes only three current-state places unless behavior itself changed:

1. the goal file under `docs/implementation/NN/`;
2. the scope migration ledger when donor rows were processed;
3. this file, pointing to the next active goal.

If behavior changes, update the owning LLD item as part of the same iteration.
