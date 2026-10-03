# SOMA Beta reuse map

Beta is a donor of proven behavior, algorithms, edge cases, tests, and implementation slices. It is not the current architecture. Agents follow these references only when the current LLD/goal requires them.

Reference design pin: `9a0e891127a771251afccca1a281b7ef7dde9e5f`.

Observed Beta implementation head during architecture review: `fbe3821ac0b52802ba8265f979590e75c3ac1209`.

| New ownership | Beta donor | Reuse focus |
|---|---|---|
| Scope 00 backend | LLD-01 Foundation Runtime | canonical instance, SQLCipher connection boundary, one outer UnitOfWork, migrations, exact command replay, durable jobs, strict JSON |
| Scope 00 frontend | LLD-10 shared UI | selection/open distinction, scroll ownership, responsive panes, working copies, confirmation tiers, semantic tokens |
| Scope 00 security mechanisms | LLD-12 shared security | DPAPI-protected live DEK, SQLCipher verification, diagnostic sanitization, trust-boundary separation |
| Future identity/settings scope | LLD-02 | organizations, contacts, locations, local profile/settings |
| Future tickets scope | LLD-03 | SR/RFC/device-reference identity, lifecycle and relationships |
| Future import scope | LLD-04 | Advanced Search SR, Enhanced RFC, Service Provider WFM import/reconciliation |
| Future objectives/tasks scope | LLD-05 | Objectives, Tasks, grouping, execution, review/retry |
| Future product/SLA scope | LLD-06 | product classification, contracts, SLA/reporting |
| Future inventory scope | LLD-07 | Spare Need/Request, Stock, RMA, Fault Tag, physical consequence |
| Future infrastructure scope | LLD-08 | Customer -> Cloud -> Site -> Room -> Rack -> Network Element -> Components |
| Future communications scope | LLD-09 | source/message identity, linking, proposals, coverage/retention |
| Future overview scope | LLD-11 | consistent cross-domain read snapshot, metrics/timeline/attention projections |
| Future security/recovery/package scope | remainder of LLD-12 | operator authentication/session, trusted launcher/runtime, backup/recovery, packaging |

High-value Beta UI references:

- `spec/lld/ui-workbenches/algorithms/selection-open.json`
- `spec/lld/ui-workbenches/algorithms/scroll-ownership.json`
- `spec/lld/ui-workbenches/ui/workbench-shell.json`
- `spec/lld/ui-workbenches/ui/domain-surfaces.json`
- `docs/UI_UX_CONTRACT.md`

High-value Beta security/foundation references:

- `spec/lld/foundation-runtime/`
- `spec/lld/security-packaging/technology.json`
- `spec/lld/security-packaging/`

Implementation reuse rule: copy no slice merely because it exists. Verify its current LLD owner, dependencies, and behavior first; then transplant/revise it into the new capability/layer structure and preserve useful regression cases.
