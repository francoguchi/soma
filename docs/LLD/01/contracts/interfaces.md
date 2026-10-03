<!-- soma-meta
{
  "version": 1,
  "id": "LLD-01-CONTRACTS",
  "scope": "01",
  "items": [
    {
      "id": "PROFILE.AUTH_PARTICIPANT",
      "anchor": "profile-auth-participant",
      "depends_on": ["PROFILE.LOCAL_USER", "AUTH.LOCAL_ADMIN", "TX.UOW"],
      "code_paths": ["src/core/soma/modules/reference/ports/profile.py"]
    },
    {
      "id": "DISPATCH.SITE_PARTICIPANT",
      "anchor": "dispatch-site-participant",
      "depends_on": ["DISPATCH.LOCATION", "TX.UOW"],
      "code_paths": ["src/core/soma/modules/reference/ports/dispatch.py"]
    },
    {
      "id": "REF.MATCH_PROVIDER",
      "anchor": "ref-match-provider",
      "depends_on": ["REF.MATCHING"],
      "code_paths": ["src/core/soma/modules/reference/ports/matching.py"]
    },
    {
      "id": "CONTACT.COMM_PROVIDER",
      "anchor": "contact-comm-provider",
      "depends_on": ["CONTACT.CHANNEL", "CONTACT.MASTER"],
      "code_paths": ["src/core/soma/modules/reference/ports/contact.py"]
    },
    {
      "id": "CUSTOMER.SCOPE_PROVIDER",
      "anchor": "customer-scope-provider",
      "depends_on": ["CUSTOMER.ORGANIZATION", "REF.QUERY"],
      "code_paths": ["src/core/soma/modules/reference/ports/customer_scope.py"]
    },
    {
      "id": "SETTING.PROVIDER",
      "anchor": "setting-provider",
      "depends_on": ["SETTING.REGISTRY", "SETTING.VALUE"],
      "code_paths": ["src/core/soma/modules/reference/ports/settings.py"]
    },
    {
      "id": "REF.DEPENDENCY_PROVIDER",
      "anchor": "ref-dependency-provider",
      "depends_on": ["REF.DEPENDENCY_GUARD"],
      "code_paths": ["src/core/soma/modules/reference/ports/dependencies.py"]
    },
    {
      "id": "DISPATCH.SITE_ADDRESS_PROVIDER",
      "anchor": "dispatch-site-address-provider",
      "depends_on": ["DISPATCH.LOCATION"],
      "code_paths": ["src/core/soma/modules/reference/ports/dispatch.py"]
    }
  ],
  "tags": ["identity", "reference", "contracts"]
}
-->

# Identity / Reference interfaces

<a id="profile-auth-participant"></a>
## PROFILE.AUTH_PARTICIPANT

Scope 01 provides an in-process same-UnitOfWork participant for first-run Local Administrator setup:

`create_for_local_admin(uow, parent_command_id, actor_id, display_name='Local Administrator') -> local_user_profile_id`

Rules:

- `actor_id` and `local_user_profile_id` are the same immutable installation-local person/actor identity in the single-user product phase.
- Scope 01 inserts descriptive profile metadata/audit evidence but never verifier/session/security rows and never commits independently.
- Foundation authentication remains usable while scope 01 is not composed during early development. Once scope 01 is part of the assembled product, composition requires this participant for fresh first-run setup.
- Enabling scope 01 against a disposable development database that was already configured without the participant requires explicit dev reset/reseed rather than hidden profile creation during a read.
- A future multi-user model would require a new accepted contract instead of stretching this singleton participant.

<a id="dispatch-site-participant"></a>
## DISPATCH.SITE_PARTICIPANT

Scope 01 provides:

`create_dedicated_for_site(uow, parent_command_id, name, precomputed_name_match_key, command_context) -> dispatch_location_id`

The future Infrastructure coordinator owns the outer command/receipt/UoW and subsequent Site↔Dispatch relation. Scope 01 verifies the key/name/profile, inserts the `site_derived` Dispatch Location + lifecycle evidence and returns without committing.

Failure in Infrastructure relation/audit must roll back the inserted Dispatch Location through the shared outer UoW.

<a id="ref-match-provider"></a>
## REF.MATCH_PROVIDER

Scope 01 provides read-only matching operations:

- `match_customer_organization(snapshot, input) -> CandidateResult`
- `match_contact(snapshot, input) -> CandidateResult`
- `preview_customer_account_code_conflict(snapshot, input) -> ReviewPreview`
- `validate_customer_account_code_review(uow, input, review_snapshot_hash) -> validation`

Candidate/review output is evidence only. Consumers rerun their own authoritative freshness/eligibility checks before accepting links or operational mutations.

<a id="contact-comm-provider"></a>
## CONTACT.COMM_PROVIDER

Scope 01 provides read-only Contact communication lookup:

- `match_email_candidates(snapshot, raw_address) -> ordered bounded candidate Contact identities/revisions`
- `validate_contact(snapshot, contact_id, revision) -> ACTIVE|ARCHIVED|MISSING`
- `validate_channel_for_use(snapshot, contact_id, channel_or_auto, purpose) -> ChannelUseValidation`

The provider validates/bounds and normalizes `raw_address` under the current scope-01 email/matching profile itself; consumers never manufacture a supposedly-normalized key. It never sends mail, chooses among multiple candidates/usable channels without owning authority, or mutates Contact state.

<a id="customer-scope-provider"></a>
## CUSTOMER.SCOPE_PROVIDER

Scope 01 provides one read-only Customer scope resolver for cross-domain projections such as Overview:

`resolve_scope(snapshot, CustomerScopeV1) -> CustomerScopeResolutionV1`

Accepted request variants are exactly:

- `all`
- `specific { customer_org_id }`
- `unassigned`

Resolution returns the same closed kind plus `customer_org_id|null` and bounded display name where applicable. A specific Customer must resolve by immutable identity under the supplied snapshot; missing/invalid identity fails rather than degrading to `all` or `unassigned`.

The provider performs no mutation and grants no authorization to downstream projections. Each consuming domain applies the resolved scope to its own data and never joins scope-01 private tables.

<a id="setting-provider"></a>
## SETTING.PROVIDER

Scope 01 provides the typed setting registry/store boundary:

- `get_definition(key)`
- `definitions_for_owner(owner)`
- `get(snapshot, key) -> effective/default-or-persisted value`
- `write(uow/application command, validated request) -> accepted setting result`

Semantic owners register definitions at composition time. Registration requires a closed contract and ordinary-nonsecret storage classification. Runtime plugins/arbitrary keys are not accepted.

The Beta-specific `ImportSettingsReader` is not retained as a scope-01 semantic interface. Future Import owns its directory-setting definitions and may expose an import-local typed facade over this generic provider; this avoids making scope 01 understand import workflow semantics. Foundation `UI.APPEARANCE` likewise owns appearance semantics and may register its ordinary preference here when the store is available.

<a id="ref-dependency-provider"></a>
## REF.DEPENDENCY_PROVIDER

Later owner domains implement `ReferenceDependencyValidator` contracts for the reference types they depend on:

- `guard_archive(uow, target)`
- `guard_reactivate(uow, target)`
- `count_*_blockers(snapshot, target)`
- `list_*_blockers(snapshot, target, cursor, limit)`

Composition registers validators deterministically. Guard methods are bounded indexed reads using the caller UnitOfWork and never mutate/commit. Detailed count/list queries are read-only and paginated.

<a id="dispatch-site-address-provider"></a>
## DISPATCH.SITE_ADDRESS_PROVIDER

Scope 01 consumes a future Infrastructure-owned provider:

- `site_link_for(snapshot, dispatch_location_id) -> SiteDispatchLink | None`
- `current_site_address(snapshot, site_id) -> str`

This provider is presentation/query context only. Scope 01 never directly queries Infrastructure tables and never writes Site-derived address text.
