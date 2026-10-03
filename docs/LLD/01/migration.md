# 01 — Identity / Reference migration ledger

Track migration decisions from SOMA Beta LLD-02 into the current scope-01 design and later implementation. Current behavior is owned by scope-01 LLD files, not by this ledger.

**Pins:** Beta design `9a0e891127a771251afccca1a281b7ef7dde9e5f`; Beta implementation donor `fbe3821ac0b52802ba8265f979590e75c3ac1209`.

Beta LLD-02 contains 40 design files. The migration is organized by behavior ownership rather than one row per donor file.

## Design behavior clusters

- [ ] **D01-A — PENDING:** immutable opaque reference identities and shared ID convention; reconcile with Foundation `IDENTITY.UUID` so scope 01 does not duplicate technical UUID generation.
- [ ] **D01-B — PENDING:** singleton Local User Profile identity + descriptive `display_name`; preserve separation from Foundation `AUTH.LOCAL_ADMIN` credentials/session authority.
- [ ] **D01-C — PENDING:** Customer Organization identity, descriptive metadata, lifecycle, external Customer Account Code claims/history, reviewed shared-claim/reassignment workflow.
- [ ] **D01-D — PENDING:** Contact identity, lifecycle, optional channels, channel validation/use, current affiliation + affiliation history.
- [ ] **D01-E — PENDING:** Dispatch Location identity/lifecycle, standalone addresses, Site-derived address boundary and cross-scope ownership with Infrastructure.
- [ ] **D01-F — PENDING:** deterministic Unicode matching/candidate semantics for organizations/contacts; unresolved/unique/ambiguous are evidence states only and never implicit identity mutation.
- [ ] **D01-G — PENDING:** archive/reactivation dependency-validator registry and bounded blocker previews; owner domains validate their own dependencies in the caller UnitOfWork.
- [ ] **D01-H — PENDING:** typed SettingDefinition registry/store, code-defined defaults, bounded strict values, and ownership split between shared storage and semantic setting owners.
- [ ] **D01-I — PENDING:** semantic NO_CHANGE, revisions, replay/audit/error contracts, pagination/bounds and current/reference history queries.
- [ ] **D01-J — PENDING:** UI handoff/workbench behavior for references, conflicts, channels, settings and profile metadata using Foundation shared interactions instead of importing Beta LLD-10 component ownership.

## Beta design donors

Primary packet: `spec/lld/identity-reference/`.

High-value leaves include:

- `_index.json`, `technology.json`, `bounds.json`, `interfaces.json`, `interfaces/cross-packet-v2.json`
- `schema/reference-{core,customer,contact-dispatch}.json`, `schema/settings.json`, `schema/fk-index-coverage.json`
- `commands/reference*.json`, `queries/reference.json`
- `algorithms/{account-code-review,archive-validation,contact-channel,matching,no-change,route-policy}.json`
- `transitions/reference-lifecycle.json`, `ui/reference-state.json`, `errors.json`, `audit/actions.json`
- `migrations/0002-identity-reference.json` and focused acceptance/failure/traceability files

## Beta implementation donors

Primary donor module: `src/soma/reference/`.

Candidate slices include:

- `application/{contact_service,customer_service,dispatch_service,lifecycle_service,profile_service,settings_service}.py`
- `domain/{account_code_review,dependencies,matching,settings,validation}.py`
- `queries/{channels,history,matching,references,_cursor}.py`
- `api/routes_reference.py`, `audit_registry.py`, `results.py`
- `assets/unicode_match_v1.json`
- `src/soma/migrations/0002_identity_reference.sql`
- focused `tests/test_reference_*.py`

Do not migrate domain workspace React components from other Beta packets into scope 01 merely because they render reference data.

## Cross-scope decisions already known

- Foundation owns technical UUID generation, UnitOfWork/replay/audit mechanics, strict JSON/error/query primitives, browser auth/session, working-copy/confirmation interactions, and shared shell components.
- Scope 01 owns Local User Profile descriptive identity metadata but not password verifier/login/session behavior.
- Infrastructure owns Site persistence and Site↔Dispatch Location relationship/address source; scope 01 consumes an explicit provider.
- Inventory and later owner domains provide bounded dependency validators; scope 01 must not query their private tables.
- Ticket/import/logistics domains consume reference identities but do not redefine them.

## Completion rule

Each design row becomes `REUSED`, `REWRITTEN`, `REJECTED`, `DEFERRED`, or `NEW` only after the current owner behavior is explicit in the scope-01 LLD.

Implementation donor rows will be added only after design clusters are stable enough to partition into `IMP-01-xx` goals. Do not pre-allocate goals merely to mirror Beta files.
