# 02 — Tickets Core migration ledger

Track migration decisions from SOMA Beta LLD-03 into current scope-02 design and later implementation. Current behavior belongs in scope-02 LLD files, not this ledger.

**Pins:** Beta design `9a0e891127a771251afccca1a281b7ef7dde9e5f`; Beta implementation donor `fbe3821ac0b52802ba8265f979590e75c3ac1209`.

Beta LLD-03 contains 66 design files. Migrate by current capability ownership rather than Beta file layout.

## Design behavior clusters

- [ ] **D02-A — PENDING:** Service Request internal/local/official identity lifecycle, canonical exact SR number grammar, adoption without identity replacement, revision/history and explicit local-vs-official identity state.
- [ ] **D02-B — PENDING:** canonical SR Customer relationship and role-specific Contact relationships with preserved history, organization-at-use context, exact handler-source alignment and scope-01 provider revalidation.
- [ ] **D02-C — PENDING:** accepted current Advanced Search SR source projection, field-independent authority, exact opaque source-evidence binding and deterministic base tokens; import discovery/parsing/proposals remain future Import ownership.
- [ ] **D02-D — PENDING:** reviewed SR source-disappearance/reappearance warning-history authority, bounded durable reappearance processing and no implicit source-field/ticket-lifecycle mutation.
- [ ] **D02-E — PENDING:** RFC exact identity and source/lifecycle projection, including terminal epoch semantics without conflating provider terminal state with local archive state.
- [ ] **D02-F — PENDING:** strict two-level RFC forest, governing-root resolution, hierarchy freshness/review, direct SR-to-root-RFC relationships and subordinate-origin provenance without fabricated direct links.
- [ ] **D02-G — PENDING:** RFC Customer ownership plus atomic downstream classification/task/communication consequences through declared owner participants; scope 02 never writes owner-private tables.
- [ ] **D02-H — PENDING:** operational Device Reference identity and SR/RFC links, independent from future Infrastructure Network Element regularization.
- [ ] **D02-I — PENDING:** Working Notes with immutable creator provenance, bounded editable body, stale-revision protection and no import writer authority.
- [ ] **D02-J — PENDING:** restart-persistent RFC terminal-cascade proposal/preview/execution with exact scope/fingerprints, deliberate proof, revalidation and bounded same-UoW owner summaries.
- [ ] **D02-K — PENDING:** operation-scoped RFC archive/restore history plus narrow untouched-manual-draft hard delete; archive is not provider terminality and hard delete is never generic deletion.
- [ ] **D02-L — PENDING:** bounded ticket queries/API/workbench projections using Foundation interactions and current scope-01 reference providers; reject Beta stale pagination/transport ownership where Foundation now governs it.

## Beta design donor packet

Primary packet: `spec/lld/tickets-core/`.

High-value groups already identified from the pinned index:

- identities/relationships/schema: `schema/{allocators,tickets,device-references,relationships}.json`, `algorithms/identifiers.json`;
- SR source authority: `schema/sr-source-*.json`, `algorithms/sr-source-{current,presence}.json`, `commands/sr-reference.json`;
- RFC authority: `schema/rfc-*.json`, `algorithms/rfc-*.json`, `commands/rfc-*.json`, `queries/rfc-*.json`;
- transport/bounds/errors/routes/types: `bounds.json`, `interfaces*.json`, `errors.json`, `routes*.json`, `types/*.json`;
- UI handoff: `ui/workbench-state.json`;
- migrations: `migrations/{0003-tickets-core,0007-sr-source-presence}.json`;
- acceptance/failure/traceability suites under `tests/`.

## Known current ownership boundaries

- Scope 00 owns technical IDs/clocks/UoW/replay/audit/jobs/query-page/browser proof/shared UI interactions.
- Scope 01 owns Customer/Contact/Local User Profile masters, matching, typed ordinary settings and reusable reference lifecycle. Scope 02 owns only ticket references/history to those identities.
- Future scope 03 Import owns discovery/parsing/staging/source evidence/proposals and calls scope-02 import participants using the existing outer UoW.
- Future Objectives/Tasks, Product/SLA, Infrastructure and Communications scopes own their private lifecycle/consequence state and expose bounded providers/participants to scope 02.
- Device Reference remains a scope-02 operational identity even after future Infrastructure regularization; Network Element identity never replaces historical ticket relationship identity.
- Ticket frontend behavior belongs to scope 02, but shared shell/selection/scroll/working-copy/confirmation/accessibility behavior remains Foundation-owned.

## Initial donor observations

- Beta page maxima of 500 for RFC children/root links/device references/notes conflict with current Foundation `QUERY.PAGE` hard maximum 200 and must be reconciled rather than copied.
- Beta packet assumes deliberate proof implementation in old LLD-12; current Foundation `SECURITY.DELIBERATE_PROOF` is the owner.
- Beta packet uses LLD-01/02 names for Foundation/reference providers; current scope numbers/IDs must replace provenance names without changing owner boundaries.
- Terminal cascade, archive and hard-delete preview fingerprints are potentially high-risk carryovers and require exact canonical-byte review before reuse.
- The two-level RFC hierarchy invariant remains a Stage-0/current product invariant unless owner review explicitly changes it.

## Completion rule

Every useful Beta behavior must end as `REUSED`, `REWRITTEN`, `REJECTED`, `DEFERRED`, or `NEW` in this ledger before scope 02 is approved. Implementation donor rows are created only after behavior ownership and the four-pass pre-approval audit are complete.
