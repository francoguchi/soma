# SOMA agent instructions

Implement the current user request in runnable increments. `src/main` is the user plane; `src/core` is the system plane. Formal whole-application certification occurs only after implementation and live testing.

## Start

1. Inspect branch and working tree; preserve unrelated changes.
2. Read `docs/LLD/CONTINUE.md`. It is the only current-state/handover pointer and names the active scope, branch, goal, and migration ledger.
3. Read the active implementation goal, then only its linked LLD items, consumed interfaces, migration rows, affected source and directly relevant tests.
4. Read `docs/architecture.md` only when the active work needs a repository-wide coding rule or when changing architecture/documentation mechanics; do not reread it mechanically for every goal.
5. Expand reading only when dependencies or the requested change require it. Do not reread unrelated LLD scopes or run repository-wide archaeology for a focused goal.
6. Treat SOMA Alpha/Beta as reference sources only. Follow donor rows/references named by the scope migration ledger or current LLD/goal; do not recursively inspect Beta unless required behavior is missing or contradictory.
7. Read `docs/LLD/MIGRATION.md` only when allocating/migrating a new scope or checking cross-scope donor coverage; ordinary focused implementation does not reread the global queue.

The user can revise design. Current LLD items define behavior; goals define the active increment. README files state purpose. Beta material supplies reuse references.

## Implement

- Write code once the relevant behavior and boundaries are clear.
- Keep business ownership inside its module; consume other modules through exported interfaces.
- Application operations own transactions; repositories do not commit independently.
- Use shared frontend interactions, API contracts, and time formatting.
- Make internal choices that preserve stated behavior. Ask for a missing material product decision and continue independent work.
- Record unfinished behavior in the goal; do not present a stub as a completed operation.
- Reuse and revise existing code. For Beta donor code, process the current goal's rows in the scope migration ledger and record `REUSED`, `REWRITTEN`, `REJECTED`, or `DEFERRED` before marking the goal working. Never mark `REUSED` from file-copy success alone; compare the donor behavior to the current LLD and carry over/rewrite the focused regression evidence. Create abstractions/documents only when actual work requires them.
- Do not make `.tmp/` content an application dependency or source of truth.

## Development database

The designated SOMA development database is disposable. Edit schema/migrations and recreate it as required. Set `reset_db` on the active goal. Resolve the configured instance and stop its runtime before reset; use foundation's reset entry point when available. Ordinary startup does not erase records.

## Fast development lane

- Work on the current scope branch (for Foundation: `feat/00-foundation`) and advance its implementation goals in order unless the user explicitly redirects priority.
- Do not create a sub-branch, PR, certification packet, design freeze, release artifact, support bundle, coverage campaign, or full-repository test run for each goal.
- For an increment, run the goal's listed checks plus the smallest directly affected unit/integration tests needed to make the change trustworthy. Add a focused regression test when a real defect is found.
- Do not run unrelated suites, cross-platform matrices, packaging/signing checks, exhaustive security audits, performance campaigns, or release validation unless the active goal explicitly requires them or a failure indicates they are relevant.
- Lint/type/build only the affected plane/package when useful. A clean focused run is sufficient to continue iterative development.
- Do not block coding on future-scope docs, future CI, optional refactors, or release hardening.
- Commit/checkpoint discipline may be used for recoverability, but implementation progress is not gated on opening or merging a PR between goals.

## Finish

Run relevant focused checks and exercise the changed workflow when possible. Record actual results and remaining work. Use the impact checker when available; otherwise search item IDs and code-path references and follow the same relationships.

Update affected LLD items and the current goal. Keep IDs/paths stable. Use `working` only when the stated outcome has been exercised, required remaining work is none, and all migration-ledger rows for that goal are closed. Reopen a goal when another iteration requires it.

At a goal checkpoint, update exactly the goal file, relevant migration rows, and `docs/LLD/CONTINUE.md` unless behavior itself changed. Do not create another handover/status/progress file.

Skip formal certification, release-readiness claims, exhaustive unrelated rereading/testing, and duplicate progress ledgers during development. Keep each README to a precise purpose of at most 40 words, plus necessary navigation links.
