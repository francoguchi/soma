<!-- soma-meta
{
  "version": 1,
  "id": "LLD-01-CHECKS",
  "scope": "01",
  "items": [
    {"id":"CHK01.IDENTITY","anchor":"chk01-identity","covers":["REF.IDENTITY","PROFILE.LOCAL_USER","PROFILE.AUTH_PARTICIPANT","M01.001"]},
    {"id":"CHK01.BOUNDS.API","anchor":"chk01-bounds-api","covers":["REF.BOUNDS","REF.ERRORS","REF.API"]},
    {"id":"CHK01.COMMAND.ATOMICITY","anchor":"chk01-command-atomicity","covers":["REF.COMMAND_ORDER","REF.AUDIT"]},
    {"id":"CHK01.MATCH.PROFILE","anchor":"chk01-match-profile","covers":["REF.UNICODE_MATCH","REF.MATCHING","REF.MATCH_PROVIDER"]},
    {"id":"CHK01.CUSTOMER","anchor":"chk01-customer","covers":["CUSTOMER.ORGANIZATION","CUSTOMER.ACCOUNT_CODE"]},
    {"id":"CHK01.CONTACT","anchor":"chk01-contact","covers":["CONTACT.MASTER","CONTACT.CHANNEL","CONTACT.AFFILIATION","CONTACT.COMM_PROVIDER","M01.002"]},
    {"id":"CHK01.DISPATCH","anchor":"chk01-dispatch","covers":["DISPATCH.LOCATION","DISPATCH.SITE_PARTICIPANT","DISPATCH.SITE_ADDRESS_PROVIDER","M01.003"]},
    {"id":"CHK01.LIFECYCLE","anchor":"chk01-lifecycle","covers":["REF.LIFECYCLE","REF.DEPENDENCY_GUARD","REF.DEPENDENCY_PROVIDER"]},
    {"id":"CHK01.SETTINGS","anchor":"chk01-settings","covers":["SETTING.REGISTRY","SETTING.VALUE","SETTING.PROVIDER","M01.004"]},
    {"id":"CHK01.NO_CHANGE","anchor":"chk01-no-change","covers":["REF.NO_CHANGE"]},
    {"id":"CHK01.QUERY","anchor":"chk01-query","covers":["REF.QUERY","CUSTOMER.SCOPE_PROVIDER"]},
    {"id":"CHK01.SCHEMA","anchor":"chk01-schema","covers":["M01.001","M01.002","M01.003","M01.004"]},
    {"id":"CHK01.ADVERSARIAL","anchor":"chk01-adversarial","covers":[]},
    {"id":"CHK01.UI.REFERENCE","anchor":"chk01-ui-reference","covers":["UI.REF.WORKSPACE","UI.REF.CANDIDATES","UI.REF.ACCOUNT_CODE_REVIEW","UI.REF.CONTACT","UI.REF.DISPATCH","UI.REF.LIFECYCLE"]},
    {"id":"CHK01.UI.SETTINGS","anchor":"chk01-ui-settings","covers":["UI.PROFILE.METADATA","UI.SETTINGS.REGISTRY"]}
  ],
  "tags": ["identity", "reference", "settings", "checks"]
}
-->

# Identity / Reference checks

These are development checks for scope-01 behavior. They are not release certification.

<a id="chk01-identity"></a>
## CHK01.IDENTITY

Create distinct Customer/Contact/Dispatch identities with equal descriptive values and prove equality never collapses identity. Verify all new IDs are canonical UUIDv4 from Foundation. During first-run Local Administrator setup, create the singleton profile inside the same outer UnitOfWork with `local_user_profile_id == actor_id`; a direct mismatched profile FK insert must fail. Then update only display-name metadata without changing authentication/session authority.

<a id="chk01-bounds-api"></a>
## CHK01.BOUNDS.API

Exercise every scope-01 semantic field at valid boundary, one-byte/line overflow, forbidden-control and malformed-input cases. Require rejection without truncation. Verify display-name 512, names 1024, Account Code 512, email 2048, standalone address 8192/32 lines, normalized key 2048, reason category 128 and review context 256 UTF-8-byte contracts.

Exercise list/history/candidate/channel/blocker APIs with omitted/default, 50, 200 and >200 limits; >200 rejects/clamps according to the typed contract and no path accepts Beta's stale 500 maximum. Fuzz generic reference type, cursor, path and sort/filter inputs and prove they never become SQL identifiers/fragments. Confirm no ordinary DELETE route exists and internal profile/Site participants are not remotely callable. Every failure crosses only stable REF.ERRORS/Foundation ERROR.CONTRACT data.

<a id="chk01-command-atomicity"></a>
## CHK01.COMMAND.ATOMICITY

Instrument representative Customer, Contact, lifecycle, setting and profile mutations. Prove bounded normalization/syntax checks happen before the writer transaction, state/revision/review/dependency facts are revalidated inside one outer UnitOfWork, one receipt precedes owner writes, required audit is appended in the same UnitOfWork, and exactly one commit occurs.

Inject repository/constraint/audit failure after receipt insertion and require rollback of receipt plus every partial owner/history row. Cross-scope participants must use the caller UoW/parent receipt and never commit independently. Inspect audit payloads and verify names, emails, addresses, setting values, display name, credentials and unrestricted source bodies are absent.

<a id="chk01-match-profile"></a>
## CHK01.MATCH.PROFILE

Run the pinned Unicode normalization vector corpus across supported Python lines and require byte-identical keys. Reject unsupported stored profile IDs rather than interpreting them with current runtime Unicode behavior. Exercise Customer and scoped Contact matching for unresolved, unique and ambiguous unions, including multiple reviewed Account Code claimants.

<a id="chk01-customer"></a>
## CHK01.CUSTOMER

Create/update Customers, set/replace Account Code and preserve superseded history. Create a real conflicting code, verify ordinary assignment returns review-required with no mutation, then exercise shared-claim and reassignment using the exact reviewed snapshot. Change Customer reference state between preview/commit and require stale-review failure before receipt/mutation.

<a id="chk01-contact"></a>
## CHK01.CONTACT

Create Contacts with zero channels/affiliation and with optional email/Customer. Validate complete email syntax without network access, archive/update channels with revision guards, and verify equal email does not merge Contacts. Move affiliation while preserving one Contact ID and append-only prior relationship history. Auto-select zero/one/multiple usable channels and never pick an implicit winner for multiple.

<a id="chk01-dispatch"></a>
## CHK01.DISPATCH

Create/edit standalone Dispatch Locations and verify Customer ownership/role fields do not exist. Exercise the internal Site-derived creation participant in a synthetic caller-owned UnitOfWork and roll back its row when the coordinating Site operation fails. Site-derived address updates must remain unavailable through scope 01.

<a id="chk01-lifecycle"></a>
## CHK01.LIFECYCLE

Register multiple synthetic dependency validators and archive/reactivate references. Verify all write-path guards use the caller UnitOfWork, blockers/indeterminate fail closed with no receipt/mutation, detailed preview is bounded/read-only, and archive never cascades dependent deletion. Preserve lifecycle event history across reactivation.

<a id="chk01-settings"></a>
## CHK01.SETTINGS

Read absent registered settings and prove defaults create no row. Write/update one setting with exact revision, reject unknown/secret/mismatched contracts, exercise semantic equality NO_CHANGE, and verify explicit upgrader failure leaves prior bytes unchanged. Register settings from multiple semantic owners without transferring their business meaning to scope 01. In particular, register Foundation's appearance preference through the generic provider and verify scope 01 persists the typed value without owning/duplicating the `core_dark|system|light` semantic enum.

<a id="chk01-no-change"></a>
## CHK01.NO_CHANGE

For descriptive, Account Code, Contact channel/affiliation and setting updates, submit an already-current accepted state after valid preconditions. Verify only the command receipt commits, domain revisions/history/audit do not change, and replay of the same command remains the original NO_CHANGE even after later unrelated mutations.

<a id="chk01-query"></a>
## CHK01.QUERY

Exercise active lists, historical detail, Account Code history, Contact channels/affiliation history, lifecycle preview and setting queries over datasets larger than one page. Require stable keyset order, bounded nested collections, no N+1 query explosion, no side-effecting default materialization, and exact counts only where semantics require them. Resolve Customer scopes `all`, `specific`, and `unassigned` in one read snapshot; a missing specific Customer fails rather than silently broadening scope, and archived identity remains explicit rather than being rewritten.

<a id="chk01-schema"></a>
## CHK01.SCHEMA

Build a fresh disposable database through the Foundation migration manifest and exact-schema verifier. Require every scope-01 table to be SQLite STRICT with the documented columns/checks, every declared index/partial unique constraint, all 22 named protection/generation triggers, and leading-prefix coverage for every FK child path.

Drop/rename one required index or trigger, weaken STRICT/channel-kind/current-affiliation/profile-FK protection, or tamper the stored matching-profile singleton and require readiness/schema verification to fail. No scope-01 migration may use SQLite wall-clock functions to invent accepted chronology.

<a id="chk01-adversarial"></a>
## CHK01.ADVERSARIAL

Run the high-risk Beta regressions against current ownership rather than reproducing old tests mechanically:

- duplicate/equal names or email keys never merge identity;
- unsupported matching profile and normalization expansion fail closed;
- reviewed Account Code context stale/very-large claimant sets never stream bodies under the writer lock;
- source claim disappears or a third claimant exists during reassignment without corrupting unrelated claims;
- stale Contact/channel/affiliation revisions never last-write-wins;
- CR/LF/control email injection never persists or reaches recipient output;
- direct SQL attempts to violate immutable profile/master identities, one-current-affiliation, history append-only, channel-kind=email, master-delete or lifecycle guards fail;
- 100000 dependency blockers change preview cost only, not archive writer-path materialization;
- malformed/duplicate-key/nonfinite/oversized setting JSON and unsafe state-dependent validators fail before accepted mutation;
- candidate evidence that was UNIQUE becomes stale when another candidate appears; consumers must revalidate rather than treating the old preview as authority;
- replay after lost NO_CHANGE response never turns into a later mutation, and same command ID with a different request hash fails idempotency integrity;
- injected SQL/cursor/reference-type payloads remain data and fail before repository identifier selection;
- missing/partial future dependency providers return explicit unavailable/indeterminate state rather than optimistic eligibility;
- forced failure of Customer-reference generation trigger rolls back Customer/identifier/revision/receipt/audit changes atomically.

This pass also verifies query statement counts remain bounded independently of page row count and that exact matching/keyset navigation uses declared indexes on representative synthetic populations.

<a id="chk01-ui-reference"></a>
## CHK01.UI.REFERENCE

Using synthetic/reference data, exercise list->workbench return context, archived state, candidate review, Account Code conflict review/staleness, Contact channel ambiguity, affiliation history, Dispatch address-source presentation and lifecycle blocker preview. Shared Foundation selection/scroll/dialog/working-copy semantics remain unchanged.

<a id="chk01-ui-settings"></a>
## CHK01.UI.SETTINGS

Verify Profile display-name editing remains visibly separate from password/login, no username control appears, Settings distinguish DEFAULT/PERSISTED, secret values are absent, and stale revisions preserve safe working intent.
