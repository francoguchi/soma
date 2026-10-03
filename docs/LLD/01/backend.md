<!-- soma-meta
{
  "version": 1,
  "id": "LLD-01-BACKEND",
  "scope": "01",
  "items": [
    {
      "id": "REF.IDENTITY",
      "anchor": "ref-identity",
      "depends_on": ["IDENTITY.UUID"],
      "code_paths": ["src/core/soma/modules/reference/domain/"]
    },
    {
      "id": "REF.UNICODE_MATCH",
      "anchor": "ref-unicode-match",
      "depends_on": ["PLATFORM.BASELINE"],
      "code_paths": ["src/core/soma/modules/reference/domain/matching.py", "src/core/soma/modules/reference/assets/"]
    },
    {
      "id": "REF.BOUNDS",
      "anchor": "ref-bounds",
      "depends_on": ["QUERY.PAGE"],
      "code_paths": ["src/core/soma/modules/reference/domain/validation.py", "src/core/soma/modules/reference/transport/"]
    },
    {
      "id": "REF.COMMAND_ORDER",
      "anchor": "ref-command-order",
      "depends_on": ["TX.UOW", "COMMAND.REPLAY", "AUDIT.APPEND_ONLY", "TIME.UTC", "IDENTITY.UUID"],
      "code_paths": ["src/core/soma/modules/reference/application/"]
    },
    {
      "id": "REF.ERRORS",
      "anchor": "ref-errors",
      "depends_on": ["ERROR.CONTRACT"],
      "code_paths": ["src/core/soma/modules/reference/transport/errors.py"]
    },
    {
      "id": "PROFILE.LOCAL_USER",
      "anchor": "profile-local-user",
      "depends_on": ["AUTH.LOCAL_ADMIN", "TX.UOW", "COMMAND.REPLAY", "AUDIT.APPEND_ONLY"],
      "code_paths": ["src/core/soma/modules/reference/application/profile.py", "src/core/soma/modules/reference/adapters/"]
    },
    {
      "id": "CUSTOMER.ORGANIZATION",
      "anchor": "customer-organization",
      "depends_on": ["REF.IDENTITY", "REF.UNICODE_MATCH", "TX.UOW", "COMMAND.REPLAY", "AUDIT.APPEND_ONLY"],
      "code_paths": ["src/core/soma/modules/reference/domain/customer.py", "src/core/soma/modules/reference/application/customer.py"]
    },
    {
      "id": "CUSTOMER.ACCOUNT_CODE",
      "anchor": "customer-account-code",
      "depends_on": ["CUSTOMER.ORGANIZATION", "REF.UNICODE_MATCH", "PERSISTENCE.READ_SNAPSHOT", "SERIALIZATION.STRICT_JSON"],
      "code_paths": ["src/core/soma/modules/reference/domain/account_code.py", "src/core/soma/modules/reference/application/customer.py"]
    },
    {
      "id": "CONTACT.MASTER",
      "anchor": "contact-master",
      "depends_on": ["REF.IDENTITY", "REF.UNICODE_MATCH", "TX.UOW", "COMMAND.REPLAY", "AUDIT.APPEND_ONLY"],
      "code_paths": ["src/core/soma/modules/reference/domain/contact.py", "src/core/soma/modules/reference/application/contact.py"]
    },
    {
      "id": "CONTACT.CHANNEL",
      "anchor": "contact-channel",
      "depends_on": ["CONTACT.MASTER", "REF.UNICODE_MATCH"],
      "code_paths": ["src/core/soma/modules/reference/domain/channels.py", "src/core/soma/modules/reference/application/contact.py"]
    },
    {
      "id": "CONTACT.AFFILIATION",
      "anchor": "contact-affiliation",
      "depends_on": ["CONTACT.MASTER", "CUSTOMER.ORGANIZATION"],
      "code_paths": ["src/core/soma/modules/reference/domain/contact.py", "src/core/soma/modules/reference/application/contact.py"]
    },
    {
      "id": "DISPATCH.LOCATION",
      "anchor": "dispatch-location",
      "depends_on": ["REF.IDENTITY", "REF.UNICODE_MATCH"],
      "code_paths": ["src/core/soma/modules/reference/domain/dispatch.py", "src/core/soma/modules/reference/application/dispatch.py"]
    },
    {
      "id": "REF.MATCHING",
      "anchor": "ref-matching",
      "depends_on": ["REF.UNICODE_MATCH", "CUSTOMER.ACCOUNT_CODE", "CONTACT.CHANNEL", "CONTACT.AFFILIATION", "QUERY.PAGE"],
      "code_paths": ["src/core/soma/modules/reference/application/queries/matching.py", "src/core/soma/modules/reference/adapters/persistence/reference_reader.py"]
    },
    {
      "id": "REF.DEPENDENCY_GUARD",
      "anchor": "ref-dependency-guard",
      "depends_on": ["TX.UOW", "QUERY.PAGE"],
      "code_paths": ["src/core/soma/modules/reference/domain/dependencies.py", "src/core/soma/modules/reference/composition.py"]
    },
    {
      "id": "REF.LIFECYCLE",
      "anchor": "ref-lifecycle",
      "depends_on": ["REF.DEPENDENCY_GUARD", "TX.UOW", "COMMAND.REPLAY", "AUDIT.APPEND_ONLY"],
      "code_paths": ["src/core/soma/modules/reference/application/lifecycle.py"]
    },
    {
      "id": "SETTING.REGISTRY",
      "anchor": "setting-registry",
      "depends_on": ["SERIALIZATION.STRICT_JSON"],
      "code_paths": ["src/core/soma/modules/reference/domain/settings.py"]
    },
    {
      "id": "SETTING.VALUE",
      "anchor": "setting-value",
      "depends_on": ["SETTING.REGISTRY", "TX.UOW", "COMMAND.REPLAY", "AUDIT.APPEND_ONLY"],
      "code_paths": ["src/core/soma/modules/reference/application/settings.py", "src/core/soma/modules/reference/adapters/"]
    },
    {
      "id": "REF.NO_CHANGE",
      "anchor": "ref-no-change",
      "depends_on": ["COMMAND.REPLAY"],
      "code_paths": ["src/core/soma/modules/reference/application/"]
    },
    {
      "id": "REF.AUDIT",
      "anchor": "ref-audit",
      "depends_on": ["AUDIT.APPEND_ONLY"],
      "code_paths": ["src/core/soma/modules/reference/audit.py"]
    },
    {
      "id": "REF.QUERY",
      "anchor": "ref-query",
      "depends_on": ["QUERY.PAGE", "PERSISTENCE.READ_SNAPSHOT"],
      "code_paths": ["src/core/soma/modules/reference/application/queries/", "src/core/soma/modules/reference/adapters/persistence/reference_reader.py"]
    }
  ],
  "tags": ["identity", "reference", "settings"]
}
-->

# Identity / Reference backend

<a id="ref-identity"></a>
## REF.IDENTITY

Scope 01 owns durable reusable reference identities for Customer Organization, Contact, Dispatch Location, Local User Profile metadata, relationship/history rows, and reference events. IDs are immutable lowercase canonical UUIDv4 values allocated through Foundation `IDENTITY.UUID`; descriptive/business values never become relational identity.

Equal names, addresses, emails, account codes, or normalized keys never authorize implicit merge/reuse. Cross-domain consumers store/reference immutable IDs and preserve their own at-use snapshots when history requires them.

<a id="ref-unicode-match"></a>
## REF.UNICODE_MATCH

Reference matching uses one versioned deterministic normalization profile. Initial profile is `UNICODE_MATCH_V1`: Unicode 17.0.0 NFKC + repository-versioned full CaseFolding and White_Space data, with `unicodedata2==17.0.1` providing the pinned normalization database.

Normalization rejects non-strings, enforces pre/post UTF-8 bounds, collapses governed whitespace runs to one ASCII space, applies full case-folding, preserves diacritics and punctuation, and rejects empty output. Built-in Python Unicode tables are not authority when they differ across supported runtimes.

Persisted match-key columns are interpreted only when the stored matching-profile ID is supported. A profile change requires an explicit forward migration/reindex; it is never an in-place reinterpretation.

<a id="ref-bounds"></a>
## REF.BOUNDS

Scope 01 owns semantic bounds for its reference fields; Foundation owns absolute parser/transport safety ceilings. Values are rejected, never truncated.

Initial accepted field bounds:

| Field | Accepted bound |
|---|---|
| Local User Profile `display_name` | 1..512 UTF-8 bytes, one line, reject NUL/CR/LF |
| Customer name | 1..1024 UTF-8 bytes, one line, reject NUL/CR/LF |
| Customer Account Code | 1..512 UTF-8 bytes, one line, reject NUL/CR/LF |
| Contact name | 1..1024 UTF-8 bytes, one line, reject NUL/CR/LF |
| Email channel | 1..2048 UTF-8 bytes before governed trim; one line; reject NUL/CR/LF/C0/C1 controls |
| Dispatch Location name | 1..1024 UTF-8 bytes, one line, reject NUL/CR/LF |
| Standalone Dispatch address | 1..8192 UTF-8 bytes, maximum 32 lines, reject NUL; normalize accepted CRLF/CR to LF before validation/persistence |
| Governed normalized match key | 1..2048 UTF-8 bytes, one line, reject NUL/CR/LF |
| Lifecycle `reason_category` | maximum 128 UTF-8 bytes, one closed category/code rather than free narrative |
| `review_context_id` | 1..256 UTF-8 bytes, one line, opaque provenance only |

The Beta packet's stale `local_user_profiles.username` bound is interpreted only as the intended 512-byte descriptive display-name limit; no username/login field is migrated.

Scope-01 collection default is 50 items with hard maximum 200. This is intentionally stricter than Foundation's shared default while respecting Foundation's maximum. Candidate/history/channel/blocker pages never use the stale Beta transport annotation of 500.

Each SettingDefinition declares its own UTF-8/depth/collection bounds under Foundation strict-JSON absolute safety ceilings.

<a id="ref-command-order"></a>
## REF.COMMAND_ORDER

Every ordinary accepted scope-01 command follows one ordering. Accepted chronology comes only from Foundation `TIME.UTC`; newly allocated owner/event identities come only from Foundation `IDENTITY.UUID`:

1. exact replay/idempotency lookup;
2. pure bounded preflight outside the writer transaction (field bounds, Unicode normalization, email syntax, state-independent setting validation);
3. open one Foundation outer UnitOfWork;
4. load/revalidate current identity, lifecycle, revision, uniqueness, dependency and review-freshness state;
5. detect semantic `NO_CHANGE` where the command permits it;
6. allocate new immutable IDs needed by the accepted change;
7. insert the Foundation command receipt;
8. perform owner domain/history/lifecycle writes;
9. append required typed privacy-minimized audit/result evidence;
10. commit once.

No DNS/network/external I/O, operator wait, unbounded claimant/blocker enumeration, or other long work occurs while the write transaction is held. Cross-scope participants receive the existing UoW/parent receipt and never commit or create competing receipts.

Any failure after opening the UnitOfWork rolls back the receipt and every attempted scope-01 write.

<a id="ref-errors"></a>
## REF.ERRORS

Scope 01 uses Foundation `ERROR.CONTRACT` and adds stable domain codes. HTTP status is transport mapping only; clients act on the machine code/recoverability.

Current domain catalogue includes:

- lifecycle/dependency: `REFERENCE_ARCHIVED`, `ARCHIVE_BLOCKED`, `REACTIVATION_BLOCKED`, `DEPENDENCY_VALIDATION_FAILED`;
- Customer/reference conflict: `CUSTOMER_ORG_INACTIVE`, `ACCOUNT_CODE_CONFLICT_REVIEW`, `ACCOUNT_CODE_SOURCE_NOT_OWNER`, `ACCOUNT_CODE_SHARED_CONTEXT_REQUIRED`, `REVIEW_CONTEXT_STALE`;
- matching: `MATCH_PROFILE_UNSUPPORTED`, `MATCH_INPUT_INVALID`;
- channels: `CHANNEL_INVALID`, `CHANNEL_NOT_USABLE`, `CHANNEL_SELECTION_REQUIRED`, `CHANNEL_NOT_OWNED`;
- settings: `SETTING_UNKNOWN`, `SETTING_CONTRACT_MISMATCH`, `SETTING_SECRET_FORBIDDEN`;
- profile/bounds: `SINGLETON_PROFILE_EXISTS`, `FIELD_BOUND_EXCEEDED`.

Foundation supplies generic not-found, stale-revision, validation, replay/idempotency, persistence and internal categories. Candidate states `UNRESOLVED|UNIQUE_CANDIDATE|AMBIGUOUS`, channel prerequisite states, affiliation mismatch warnings and `NO_CHANGE` are not errors.

Scope-01 codes map only to Foundation's closed recoverability enum:

- `correct_input`: `MATCH_INPUT_INVALID`, `CHANNEL_INVALID`, `SETTING_UNKNOWN`, `SETTING_SECRET_FORBIDDEN`, `FIELD_BOUND_EXCEEDED`, malformed reviewed-command input;
- `refresh`: lifecycle/reference staleness/blockers, Account Code review/source changes, Customer inactive, channel ownership/usability/selection changes, singleton-profile already present;
- `retry`: `DEPENDENCY_VALIDATION_FAILED` only when the safe next action is a bounded retry after the dependency owner recovers;
- `none`: unsupported matching profile or setting contract/version requiring a compatible build/governed upgrader rather than blind retry.

No scope-01 error invents additional recoverability strings. More specific operator guidance belongs in bounded `safe_next_action`.

Raw names, addresses, emails, setting values, SQL/provider exceptions or unrestricted source evidence never enter safe error summaries merely to explain a failure.

<a id="profile-local-user"></a>
## PROFILE.LOCAL_USER

Scope 01 owns the singleton Local User Profile's descriptive identity metadata only: immutable `local_user_profile_id`, editable nonblank `display_name`, revision, and chronology.

Foundation `AUTH.LOCAL_ADMIN` owns password setup/login/logout and browser-session authority. First-run authentication coordinates creation of the profile in the same outer UnitOfWork, defaulting `display_name` server-side to **Local Administrator** when no explicit accepted name exists.

Updating `display_name` revalidates the exact metadata revision, changes no credential/session/DEK/security authority, and records only bounded identifiers/revisions/changed-field audit evidence—not raw prior/new display-name text.

There is no username/login-name field.

<a id="customer-organization"></a>
## CUSTOMER.ORGANIZATION

Customer Organization is an immutable reference identity with bounded descriptive name, governed name match key, lifecycle `active|archived`, revision, and chronology.

Create is explicit even when an equal normalized name already exists. Descriptive updates preserve identity and lifecycle, use revision preconditions, and produce lifecycle/audit evidence only when accepted state actually changes.

Customer references are history-bearing and do not expose ordinary hard delete.

<a id="customer-account-code"></a>
## CUSTOMER.ACCOUNT_CODE

Customer Account Code is external matching evidence, never `customer_org_id`. One Customer has at most one active code claim; prior claims are superseded, not overwritten/deleted.

The same normalized code may have more than one active Customer claimant only through explicit reviewed acceptance. Ordinary set/create detects another claimant and returns conflict-review state rather than stealing, merging, or silently sharing.

Conflict preview binds the reviewed action to current matching-profile ID, conservative Customer-reference generation, normalized code key, target/source revisions/current claims, proposed action, and exact claimant count. Commit recomputes that bounded snapshot inside the existing UnitOfWork and constant-time compares its SHA-256. Changed context returns stale-review failure before receipt/mutation.

Reviewed actions are:
- confirm a shared claim while preserving future matching ambiguity;
- reassign one source claim to a different Customer without touching unrelated third-party claimants.

Claim history preserves creation/supersession command provenance.

<a id="contact-master"></a>
## CONTACT.MASTER

Contact is one immutable identity with bounded descriptive name/match key, lifecycle, revision, and chronology. Zero channels and zero Customer affiliation are valid.

Creating or editing a Contact never silently reuses another Contact because names/emails compare equal. Archived Contacts remain historically queryable but are excluded from new-work selectors until explicit reactivation.

<a id="contact-channel"></a>
## CONTACT.CHANNEL

Contact channels are reusable communication/matching attributes, not Contact identity and never authentication identity. Initial supported kind is `email`.

Storage validation trims only governed leading/trailing whitespace, rejects empty/NUL/CR/LF/C0/C1 controls, parses the complete value as exactly one address via Python `email.headerregistry.Address(addr_spec=value)`, performs no DNS/SMTP/deliverability lookup, persists accepted text, and derives a separate governed match key.

Equal channel values are allowed and may remain ambiguous. Channel kind is immutable for one channel ID; changing kind requires archive + add. Archived channels remain history and are not eligible for matching/recipient use.

Use validation is just-in-time. A specific selected channel must still belong to the active Contact, be active, and pass current syntax policy. Auto-select may return `USABLE|MISSING|ARCHIVED|INVALID|MULTIPLE_USABLE`; multiple usable values never choose a row-order winner unless the consuming workflow separately owns a deterministic selection rule.

<a id="contact-affiliation"></a>
## CONTACT.AFFILIATION

A Contact may be unbound or have one current Customer Organization affiliation. Changing affiliation preserves the Contact identity, closes the prior current relationship with command/UTC provenance, and inserts the replacement current relationship in the same UnitOfWork.

Historical affiliations are append-protected and never rewritten to current labels. A non-null new affiliation requires an active Customer Organization.

Operational domains preserve their own organization-at-use context instead of depending on future affiliation changes.

<a id="dispatch-location"></a>
## DISPATCH.LOCATION

Dispatch Location is a Customer-neutral reusable reference identity with name/match key, lifecycle, revision and one address mode:

- `standalone`: scope 01 owns bounded multiline address text;
- `site_derived`: address text is resolved from the future Infrastructure owner through an explicit provider.

Scope 01 never stores Customer ownership/preference, Site ID shortcut, or logistics role on the Dispatch Location master.

A standalone location is created through scope 01. A dedicated Site-derived location is an internal participant in the Infrastructure owner's existing outer UnitOfWork and never creates its own receipt/commit.

<a id="ref-matching"></a>
## REF.MATCHING

Matching is deterministic read-only candidate evidence and returns exactly `UNRESOLVED|UNIQUE_CANDIDATE|AMBIGUOUS` plus bounded candidate IDs/count/continuation, normalized-key evidence, scope, and explanation code.

Customer matching prefers exact Account Code evidence but never hides conflict: multiple code claimants remain ambiguous; supplied name evidence identifying another Customer makes the union ambiguous.

Contact matching is scoped to one current Customer affiliation or explicit `UNBOUND`; name/email evidence is exact governed matching only. Equal email in different Customer scopes is not a global identity collision.

`UNIQUE_CANDIDATE` is proposal evidence, not authorization to merge/link/mutate.

<a id="ref-dependency-guard"></a>
## REF.DEPENDENCY_GUARD

Scope 01 owns a deterministic registry of cross-domain lifecycle validators. Each consuming/owning domain implements bounded indexed guards for the reference types it depends on.

Authoritative archive/reactivation guards run inside the caller's existing UnitOfWork and return only eligibility/blocker/indeterminate facts without loading unbounded bodies or mutating. Indeterminate fails closed.

Detailed blocker previews run in read snapshots outside the writer transaction and return exact count plus bounded deterministic pages. Scope 01 never queries another module's private tables directly.

<a id="ref-lifecycle"></a>
## REF.LIFECYCLE

Customer Organization, Contact, and Dispatch Location use `active|archived` lifecycle with explicit archive/reactivate commands. Archive/reactivate revalidate base revision and every registered dependency guard inside one outer UnitOfWork.

Archive never cascades deletion/unlinking to manufacture eligibility. Reactivation preserves prior archived history.

Accepted create/archive/reactivate/descriptive-correction facts append reference lifecycle evidence linked to the command receipt and privacy-minimized Foundation audit evidence.

<a id="setting-registry"></a>
## SETTING.REGISTRY

Settings use a closed code-defined registry. Each definition owns: stable key, semantic owner, contract name/version, default provider, strict validator, semantic equality, ordinary-nonsecret storage class, and field/depth/collection byte bounds. The first scope-01 implementation accepts only `unknown_field_policy=reject`; there is no generic preserve/quarantine fallback.

Scope 01 owns registry/store mechanics; each semantic owner owns the meaning and state-dependent validation of its settings. Unknown keys are rejected and do not create generic storage.

Secret material is forbidden from this store and remains with its security owner.

<a id="setting-value"></a>
## SETTING.VALUE

Reading an absent setting returns the registered default with source `DEFAULT` and performs zero persistence.

Explicit writes validate through the registered contract, revalidate expected revision/absence and owner checks inside one UnitOfWork, then INSERT or explicit UPDATE with next revision and command/audit evidence. SQL REPLACE is forbidden.

Persisted contract mismatch fails unless an explicit registered upgrader handles that exact origin/version. A registered upgrade parses/validates old bytes, produces/validates new bytes, and updates atomically. Unsupported/unknown fields or versions are never moved into a generic quarantine store and never become loosely typed authority.

<a id="ref-no-change"></a>
## REF.NO_CHANGE

After identity/lifecycle/revision/security preconditions pass, commands compare the requested accepted state using exact stored semantics. If already current, commit only the Foundation command receipt with result type `NO_CHANGE`.

NO_CHANGE does not increment revision, create/supersede relationship/identifier state, append lifecycle evidence, or fabricate application audit history. Exact replay of that command returns the original NO_CHANGE result even if later unrelated changes occur.

Create operations, lifecycle precondition failures, channel archive, and reviewed ownership reassignment are not NO_CHANGE merely because the resulting visible text could appear similar.

<a id="ref-audit"></a>
## REF.AUDIT

Scope 01 registers typed audit actions on Foundation `AUDIT.APPEND_ONLY`; it does not create a competing audit store.

Action families cover Customer create/descriptive update/Account Code set-reviewed-share-reassign, Contact create/descriptive/channel/affiliation changes, Dispatch create/descriptive changes, reference archive/reactivate, setting writes, and Local User Profile create/display-name update.

Audit payloads carry only bounded immutable IDs, revisions, closed change classifications/reason categories, review fingerprints and bounded result references required to explain the accepted mutation.

Privacy exclusions are explicit:

- no Customer/Contact/Dispatch descriptive names;
- no raw Customer Account Code unless a future accepted authority specifically requires a bounded representation;
- no email/channel value;
- no physical address text;
- no setting value;
- no Local User Profile display-name text;
- no credentials/verifiers/session/token/key material;
- no unrestricted import/source row or unbounded claimant/blocker detail.

Accepted `NO_CHANGE` writes no scope-01 application audit event because no authoritative domain fact changed; the Foundation command receipt remains technical idempotency evidence.

<a id="ref-query"></a>
## REF.QUERY

Reference collections use deterministic keyset pagination and Foundation `QUERY.PAGE`; scope 01 uses default 50 and hard maximum 200. The conflicting Beta transport annotations of default 100 / maximum 500 are rejected as stale because they contradict both the Beta semantic bounds packet and the current Foundation hard maximum.

Primary query families include current detail, active lists, Account Code history/review, Contact channels/affiliation history/use validation, matching, lifecycle blocker preview, and setting lookup/list-by-owner.

Large nested collections are dedicated bounded queries rather than unbounded detail expansion. Exact counts are on-demand except where ambiguity/review/eligibility semantics require them. Read-only queries never persist defaults or repair state.
