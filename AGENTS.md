# SOMA agent instructions

Implement the current user request in runnable increments. `main` is the user plane; `core` is the system plane. Formal certification occurs after whole-application implementation and live testing.

## Start

1. Inspect branch and working tree; preserve unrelated changes.
2. Read `docs/architecture.md` for coding rules, then the goal selected by the current request under `docs/implementation/NN/`. If none exists, create it from that outcome before substantial implementation.
3. Read linked LLD items, consumed interfaces, and affected source/tests.
4. Expand reading only when dependencies or the requested change require it.
5. Treat SOMA Alpha/Beta as reference sources only. Follow Beta references named by the current LLD/goal; do not recursively inspect Beta unless required behavior is missing or contradictory.

The user can revise design. Current LLD items define behavior; goals define the active increment. README files state purpose. Beta material supplies reuse references.

## Implement

- Write code once the relevant behavior and boundaries are clear.
- Keep business ownership inside its module; consume other modules through exported interfaces.
- Application operations own transactions; repositories do not commit independently.
- Use shared frontend interactions, API contracts, and time formatting.
- Make internal choices that preserve stated behavior. Ask for a missing material product decision and continue independent work.
- Record unfinished behavior in the goal; do not present a stub as a completed operation.
- Reuse and revise existing code. Create abstractions/documents when actual work requires them.
- Do not make `.tmp/` content an application dependency or source of truth.

## Development database

The designated SOMA development database is disposable. Edit schema/migrations and recreate it as required. Set `reset_db` on the active goal. Resolve the configured instance and stop its runtime before reset; use foundation's reset entry point when available. Ordinary startup does not erase records.

## Finish

Run relevant focused checks and exercise the changed workflow when possible. Record actual results and remaining work. Use the impact checker when available; otherwise search item IDs and code-path references and follow the same relationships.

Update affected LLD items and the current goal. Keep IDs/paths stable. Use `working` only when the stated outcome has been exercised and required remaining work is none. Reopen a goal when another iteration requires it.

Skip formal certification, exhaustive unrelated rereading, and duplicate progress ledgers during development. Keep each README to a precise purpose of at most 40 words, plus necessary navigation links.
