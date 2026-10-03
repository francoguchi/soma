# 01 — Identity / Reference migration ledger

Track migration decisions from SOMA Beta LLD-02 into the current scope-01 design and later implementation. Current behavior is owned by scope-01 LLD files, not by this ledger.

**Pins:** Beta design `9a0e891127a771251afccca1a281b7ef7dde9e5f`; Beta implementation donor `fbe3821ac0b52802ba8265f979590e75c3ac1209`.

Beta LLD-02 contains 40 design files. The migration is organized by behavior ownership rather than one row per donor file.

## Design behavior clusters

- [x] **D01-A — REWRITTEN:** immutable opaque reference identity is retained, but allocation now consumes Foundation `IDENTITY.UUID`; scope 01 owns reference identity semantics, not a duplicate `DomainIdFactory` implementation.
- [x] **D01-B — REWRITTEN:** singleton Local User Profile metadata remains scope 01, while password/login/session authority is Foundation `AUTH.LOCAL_ADMIN`; first-run creation is an injected same-UoW participant and no username/login-name returns.
- [x] **D01-C — REWRITTEN:** Customer Organization and Account Code semantics, history, reviewed shared-claim/reassignment and conservative conflict freshness are carried into `CUSTOMER.ORGANIZATION` / `CUSTOMER.ACCOUNT_CODE` under current Foundation mechanics.
- [x] **D01-D — REWRITTEN:** Contact, optional channels, just-in-time email usability and append-preserving affiliation history are carried into the current scope-01 ownership model.
- [x] **D01-E — REWRITTEN:** Dispatch Location remains Customer-neutral; standalone address stays scope 01 while Site-derived relationship/address authority remains explicitly deferred to the future Infrastructure owner.
- [x] **D01-F — REWRITTEN:** deterministic `UNICODE_MATCH_V1` and unresolved/unique/ambiguous candidate evidence are retained; matching continues to forbid fuzzy/implicit merge authority.
- [x] **D01-G — REWRITTEN:** dependency-validator registry, same-UoW fail-closed guards and bounded read-only blocker previews are retained while concrete validators stay with their future owner domains.
- [x] **D01-H — REWRITTEN:** typed registry/store mechanics and no-write defaults are retained. Scope 01 owns ordinary nonsecret setting persistence; semantic definitions remain with their capability owners.
- [x] **D01-I — REWRITTEN:** semantic NO_CHANGE, revisions/history, privacy-minimized audit, bounded keyset queries and stable errors are translated onto current Foundation replay/audit/query/error contracts.
- [x] **D01-J — REWRITTEN:** reference/profile/settings UI behavior is now scope 01 while selection/scroll/dialog/working-copy/confirmation components remain Foundation-owned; Beta domain component ownership is not copied.

## Beta packet coverage audit

All 40 Beta LLD-02 design files are accounted for by the current behavior clusters; this is a completeness guard, not a copy checklist.

| Donor group | Files | Current destination |
|---|---:|---|
| packet/technology/bounds/interfaces/errors/routes | 8 | scope README, backend contracts/bounds/error/route semantics |
| algorithms | 6 | matching, Account Code review, lifecycle/dependency, channel, NO_CHANGE backend items |
| commands | 4 | backend application behavior |
| queries | 1 | `REF.QUERY` and provider contracts |
| schema | 5 | `migrations/schema.md` + backend invariants |
| types | 2 | current contracts/backend/frontend DTO semantics |
| audit | 1 | privacy-minimized scope audit rules on Foundation audit mechanism |
| migration allocation | 1 | `M01.001..M01.004` current schema allocation |
| implementation map | 1 | implementation donor section below |
| transitions | 1 | `REF.LIFECYCLE`, Account Code/channel/affiliation state rules |
| UI handoff | 1 | `frontend.md` using Foundation interaction primitives |
| acceptance/failure/traceability suites | 9 | `checks.md` + future focused implementation donor rows |
| **Total** | **40** | **complete source-packet accounting** |

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

## Owner decisions — resolved

- **Q01-1 — Customer Account Code shared claims: YES.** Multiple Customers may retain one active Account Code only after explicit reviewed acceptance; matching remains `AMBIGUOUS` while multiple eligible claimants survive.
- **Q01-2 — Contact channel kinds: EMAIL ONLY for the first scope-01 implementation.** Additional kinds require an explicit versioned policy/schema decision when a real consuming workflow needs them.
- **Q01-3 — Appearance preference: Foundation-owned, not scope-01-owned.** `UI.APPEARANCE` in scope 00 owns SOMA Core Dark as default and the accepted future modes `core_dark | system | light`. Scope 01 supplies only the generic ordinary-nonsecret typed setting store. Beta terminal-green/amber/violet skins are intentionally deferred and are not migrated into scope 01.
- **Q01-4 — Local User Profile identity: YES.** `local_user_profile_id == AUTH.LOCAL_ADMIN actor_id` in the current singleton model; default display name is `Local Administrator`, editable descriptively, with no username/login-name authority.
- **Q01-5 — Operator wording: YES.** Domain/backend remains `CustomerOrganization`; ordinary UI labels it **Customer**.

## Pre-approval audit gates

Scope 01 is **not approved** until all four passes are complete. Keep the results here rather than creating another status document.

- [ ] **PASS-1 — Foundation ownership/conflict audit:** prove scope 01 consumes scope 00 mechanisms instead of re-owning auth/session, appearance semantics, UUID generation, UoW/replay/audit, paging, working-copy/confirmation, runtime or shell behavior.
- [ ] **PASS-2 — Beta completeness/minimality audit:** account for all 40 LLD-02 design files and verify every retained behavior is needed by current SOMA; reject/defer obsolete Beta ownership rather than carrying it forward by inertia.
- [ ] **PASS-3 — Internal coherence audit:** verify metadata graph, migrations/schema/FK indexes, cross-scope contracts, error/audit/privacy rules, bounds/pagination, transaction ordering and development checks agree with one another.
- [ ] **PASS-4 — Adversarial implementation-readiness audit:** walk failure/race/stale/replay/ambiguity/large-data/cross-domain scenarios and verify the resulting implementation can be partitioned into clean goals without temporary architecture or hidden dependencies.

## Completion rule

Each design row becomes `REUSED`, `REWRITTEN`, `REJECTED`, `DEFERRED`, or `NEW` only after the current owner behavior is explicit in the scope-01 LLD.

Design behavior clusters are now mapped into the current backend/frontend/check/migration documents. Implementation donor rows remain intentionally unallocated until implementation goals are partitioned from the completed design rather than from Beta file layout.
