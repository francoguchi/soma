# SOMA migration map

Track which SOMA Beta design packets still need migration into the new capability-owned LLD model. This file is the cross-scope queue only; detailed donor/code dispositions belong in each active scope's `migration.md`, and implementation results belong in `docs/implementation/`.

**Pins:** Beta design `9a0e891127a771251afccca1a281b7ef7dde9e5f`; Beta implementation donor `fbe3821ac0b52802ba8265f979590e75c3ac1209`.

The pinned Beta LLD inventory contains 657 design files. Packet file counts below are used only as a completeness guard; SOMA migrates behavior/algorithms by current ownership rather than copying packet/file layout.

## Queue

- [x] **LLD-01 Foundation Runtime — 36 files — mapped to scope 00.** Current design is closed in `00/{backend,frontend,checks,migrations}.md`; implementation donor decisions remain open in `00/migration.md`.
- [x] **LLD-02 Identity / Reference — 40 files — mapped to scope 01.** Four-pass design audit and owner approval completed 2026-10-03; all useful behavior is owned/rejected/deferred in `01/migration.md`. Implementation donor decisions remain open by `IMP-01-xx` goal.
- [ ] **LLD-03 Tickets Core — 66 files — migrating into scope 02.** Permanent owner allocated as `02 — Tickets Core`; active design branch is `design/02-tickets-core`, with detailed disposition tracked in `02/migration.md`.
- [ ] **LLD-04 RFC / WFM Import — 57 files — pending owner scope.** Expected capability: source imports, staging, reconciliation, source-presence evidence and import-facing workflows.
- [ ] **LLD-05 Objectives / Tasks — 68 files — pending owner scope.** Expected capability: Objectives, Tasks/WFM, grouping, execution, reviews/retries and owner workbenches.
- [ ] **LLD-06 Product Line / SLA — 40 files — pending owner scope.** Expected capability: product catalog/classification, contracts, SLA calculations and reporting.
- [ ] **LLD-07 Inventory — 56 files — pending owner scope.** Expected capability: Spare Need/Request, stock, RMA, Fault Tag, physical units/logistics and owner workbenches.
- [ ] **LLD-08 Infrastructure — 99 files — pending owner scope.** Expected capability: Customer -> Cloud -> Site -> Room -> Rack -> Network Element -> Components plus workbook/import workflows.
- [ ] **LLD-09 Communications — 68 files — pending owner scope.** Expected capability: sources/messages, identity/linking, proposals, communications jobs, retention and communications UI.
- [ ] **LLD-10 UI Workbenches — 42 files — split migration.** Shared interaction/runtime UI mechanics are mapped to scope 00; domain-surface definitions migrate with their owning future scopes; persistent appearance/settings semantics migrate with the future settings owner.
- [ ] **LLD-11 Overview — 26 files — pending owner scope.** Expected capability: consistent cross-domain overview projections, weekly metrics, timeline and attention surfaces.
- [ ] **LLD-12 Security / Packaging — 54 files — split migration.** Live key, trusted runtime, minimal local-admin auth/session/proof and diagnostics mechanics are mapped to scope 00. Backup/recovery, password-management product UX, support bundle, installer/signing/packaging and release concerns remain pending future owners.

Shared Beta root packet/governance files (`_index`, integrity/packet contracts, exceptions and global migration catalogue) are reference material only unless a future current LLD explicitly adopts a behavior from them.

## When a scope starts

1. Allocate the next permanent two-digit scope only when that capability's current LLD work begins.
2. Create `docs/LLD/NN/{README,backend,frontend,checks,migration}.md` as actually needed.
3. Enumerate the useful Beta design behaviors and implementation donor slices in that scope's `migration.md`; do not create a 1:1 file-copy checklist.
4. For every donor row, inspect the pinned source before copying and close it as exactly one of:
   - `REUSED` — substantial donor implementation survives after relocation/adaptation;
   - `REWRITTEN` — current behavior is retained but implementation is newly written for the current architecture;
   - `REJECTED` — donor implementation/behavior is intentionally not carried forward because the current LLD supersedes it;
   - `DEFERRED` — useful work belongs to a named later owner/goal and is not silently dropped;
   - `NEW` — required current behavior has no donor implementation to migrate.
5. A packet is globally closed only when every useful behavior is owned by a current scope or explicitly rejected/deferred. Reading or copying files is not closure.

## Anti-gap rule

Reuse is an optimization, never authority. Before a donor row is marked `REUSED`, compare the donor behavior against the current LLD, identify incompatible dependencies/ownership, port or replace the focused regression evidence, and run the current goal's relevant checks.

If a donor file/behavior becomes necessary during implementation but is not represented by the active scope ledger, add a migration row before relying on it. If a row reveals work owned elsewhere, record the future owner/dependency rather than smuggling it into the active scope.

Do not add another global progress ledger. `docs/LLD/CONTINUE.md` is the single continuation pointer, this file is the cross-scope migration queue, each `NN/migration.md` is that scope's donor ledger, and implementation goal files are the only execution-status records.
