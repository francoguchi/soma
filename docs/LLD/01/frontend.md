<!-- soma-meta
{
  "version": 1,
  "id": "LLD-01-FRONTEND",
  "scope": "01",
  "items": [
    {
      "id": "UI.REF.WORKSPACE",
      "anchor": "ui-ref-workspace",
      "depends_on": ["UI.SHELL", "UI.WORKSPACE_REGISTRY", "UI.COLLECTIONS", "UI.SEARCH", "UI.OPERATIONAL_LAYOUT", "UI.RECORD_INSPECTOR", "UI.CONTEXT_REGION", "UI.ADAPTIVE_OVERLAY", "REF.QUERY"],
      "code_paths": ["src/main/features/reference/"]
    },
    {
      "id": "UI.REF.CANDIDATES",
      "anchor": "ui-ref-candidates",
      "depends_on": ["REF.MATCHING", "UI.COLLECTIONS", "UI.SEARCH", "UI.SELECTION"],
      "code_paths": ["src/main/features/reference/components/"]
    },
    {
      "id": "UI.REF.ACCOUNT_CODE_REVIEW",
      "anchor": "ui-ref-account-code-review",
      "depends_on": ["CUSTOMER.ACCOUNT_CODE", "UI.CONFIRMATION", "UI.DIALOG_FOCUS"],
      "code_paths": ["src/main/features/reference/customer/"]
    },
    {
      "id": "UI.REF.CONTACT",
      "anchor": "ui-ref-contact",
      "depends_on": ["CONTACT.MASTER", "CONTACT.CHANNEL", "CONTACT.AFFILIATION", "UI.WORKING_COPY"],
      "code_paths": ["src/main/features/reference/contact/"]
    },
    {
      "id": "UI.REF.DISPATCH",
      "anchor": "ui-ref-dispatch",
      "depends_on": ["DISPATCH.LOCATION", "UI.WORKING_COPY"],
      "code_paths": ["src/main/features/reference/dispatch/"]
    },
    {
      "id": "UI.REF.LIFECYCLE",
      "anchor": "ui-ref-lifecycle",
      "depends_on": ["REF.LIFECYCLE", "REF.DEPENDENCY_GUARD", "UI.CONFIRMATION"],
      "code_paths": ["src/main/features/reference/components/"]
    },
    {
      "id": "UI.PROFILE.METADATA",
      "anchor": "ui-profile-metadata",
      "depends_on": ["PROFILE.LOCAL_USER", "UI.WORKING_COPY", "UI.ADAPTIVE_OVERLAY"],
      "code_paths": ["src/main/features/settings/profile/"]
    },
    {
      "id": "UI.SETTINGS.REGISTRY",
      "anchor": "ui-settings-registry",
      "depends_on": ["SETTING.REGISTRY", "SETTING.VALUE", "UI.WORKING_COPY", "UI.ADAPTIVE_OVERLAY"],
      "code_paths": ["src/main/features/settings/"]
    }
  ],
  "tags": ["identity", "reference", "settings", "user-plane"]
}
-->

# Identity / Reference frontend

<a id="ui-ref-workspace"></a>
## UI.REF.WORKSPACE

Approved presentation authority is Foundation `../00/operational-ui.md`. The old unconditional three-column Reference Open layout is SUPERSEDED, not existing owner query/review/replay/working-copy semantics.

Customers (`CustomerOrganization`), Contacts and Dispatch Locations are type subviews of the EXPANDED SAME Settings overlay, also reachable from owner-contextual invocation. No separate top-level Customers workspace. Existing /settings/profile, /settings/preferences, /settings/reference-data/{customer_organization|contact|dispatch_location}[/{id|new}] remain authenticated closed overlay-entry routes with safe origin fallback.

Each reference type uses ONE upper collection with fixed New/Refresh/Search/Advanced controls. Without selection, upper list expands and lower regions are ABSENT. Clicking a record selects and reveals lower-left read-only Details plus lower-right real owner Context; fixed pencil explicitly enables editing. New opens lower-left creation only, no accepted ID or empty right panel. Successful creation selects accepted identity. Both lower splits are resizable when their adjacent regions exist. Record focus, selected/open state, archived eligibility, query/page/cursor/scroll and working-copy intent retain Foundation semantics.

Contact lower-left owns name/lifecycle edit; right Context may show actual channels, Customer affiliation/history, identity/lifecycle chronology; email channel is NOT an inbox, Notes need real provider. Customer preserves reviewed Account Code conflict/shared/reassignment evidence. Dispatch preserves standalone vs Site-derived address ownership; no editing Infrastructure Site data here.

### Browse/search composition

UI.SEARCH uses one shared visible primary collection for ordinary list/exact-match modes, not a duplicate candidate grid. Advanced matching/historical tools start collapsed and retain exact UNRESOLVED/UNIQUE/AMBIGUOUS semantics; selection never accepts an identity/relationship implicitly. One bounded count/ambiguity summary; no repeated engine zero counts. Up to eight existing bounded query/page contexts may be retained, only one rendered.

Existing Customer default term uses bounded exact name/Account Code (512-byte common ceiling), not fuzzy matching. Contact arbitrary-term name/email with explicit affiliation scope and Dispatch ordinary human-name search are UNAPPROVED owner-contract gaps (R01.06-E); Contact raw_email requires real email syntax, Dispatch no default query route. No UI-only page filtering or malformed input submission. Show truthful source capability and preserve expert matching until owner contract approved.

<a id="ui-ref-candidates"></a>
## UI.REF.CANDIDATES

Candidate matching displays `UNRESOLVED`, `UNIQUE_CANDIDATE`, and `AMBIGUOUS` explicitly. A unique candidate is never silently accepted as a link/merge.

Ambiguous state shows exact candidate count plus bounded/paginated candidate evidence; page size does not change ambiguity. Customer Account Code evidence is visually distinguishable from descriptive-name evidence. Ordinary operator labels say **Customer**; transport/domain identifiers may retain `CustomerOrganization` where precision is required.

Creating a new reference or choosing an existing candidate is always an explicit owner action.


Exact-evidence matching consumes Foundation `UI.SEARCH` presentation/state grammar while retaining its current owner-specific fields, exact ambiguity semantics and server-owned candidate truth. It does not invent fuzzy or current-page-only filtering.

<a id="ui-ref-account-code-review"></a>
## UI.REF.ACCOUNT_CODE_REVIEW

Account Code conflicts open a bounded review showing proposed action, target/source identities and current revisions, exact claimant count, bounded claimant page, and server-issued review snapshot fingerprint.

There is no default winner. Confirm shared claim and reassign are distinct actions. Submission carries the exact reviewed fingerprint; stale review forces reload/review and must never silently substitute a freshly generated fingerprint under an old confirmation.

Shared-claim state is labelled as ambiguous reviewed external evidence rather than unique Customer ownership.

<a id="ui-ref-contact"></a>
## UI.REF.CONTACT

Contact editing permits zero channels and no current Customer affiliation.

Channels show active/archive state explicitly. Recipient-dependent UI asks the server to validate current channel usability; multiple usable channels require explicit choice unless the consuming workflow owns an accepted deterministic rule.

Affiliation shows current Customer or Unbound plus a separate paginated history. A mismatch between current affiliation and another workflow's preserved Customer context is a warning/review condition, never automatic reassignment or Contact duplication.

Channel values render strictly as text.

<a id="ui-ref-dispatch"></a>
## UI.REF.DISPATCH

Dispatch Location editing never exposes Customer ownership/preference or logistics role as master fields.

Standalone addresses are edited here. Site-derived addresses are labelled as Site-derived and are not editable through the Dispatch Location master; address editing/navigation belongs to the future Infrastructure owner.

<a id="ui-ref-lifecycle"></a>
## UI.REF.LIFECYCLE

Archive preview shows exact blocker count with bounded deterministic blocker pages and safe next actions. Archive/reactivate remains an explicit operation and may still fail after fresh transactional revalidation.

Blocked or indeterminate dependency validation never appears as eligible. The UI does not expect unbounded blocker detail from the write transaction.

<a id="ui-profile-metadata"></a>
## UI.PROFILE.METADATA

Settings/Profile presents descriptive Local User Profile `display_name` separately from authentication. The default visible name is Local Administrator unless changed.

There is no username/login-name field. Display-name editing never requests or changes password, verifier, actor ID, session, auto-login, live-data key or backup/recovery authority.

A stale metadata revision reloads current descriptive state while preserving recoverable working intent according to Foundation rules.


Profile avoids duplicating the same accepted display-name fact immediately beside its editable field unless the duplicate communicates a distinct accepted/current/proposed state. Technical revision or byte-storage detail stays secondary to ordinary operator meaning.

<a id="ui-settings-registry"></a>
## UI.SETTINGS.REGISTRY

Operator wording distinguishes the default preference from a saved choice without exposing storage state enums, persistence revisions or semantic-owner IDs in ordinary Preferences labels.

Settings UI is generated/composed from registered semantic definitions rather than arbitrary key/value editing. It distinguishes `DEFAULT` from `PERSISTED` without creating rows merely by viewing defaults.

Validation/errors remain setting-owner specific. Secret-classified definitions never expose raw values through the ordinary Settings surface.

Scope 01 provides the registry/store presentation substrate; later domain scopes contribute their own registered definitions and may supply feature-specific Settings panels when generic rendering would be misleading.


When only one registered preference is currently renderable, Settings presents it directly rather than forcing a redundant preference chooser. Common preference operations use concise operator copy and shared navigation/action grammar; persistence source/revision/semantic-owner evidence appears only where it materially helps conflict or diagnostic review.

## Composition boundaries

Compact Settings uses UI.ADAPTIVE_OVERLAY and shows Profile/registered Appearance as simple bounded forms. Reference Data expands SAME dialog into Reference Manager; origin workspace stays preserved. Manager selection only inspects, never silently links an identity to a Ticket/other workflow; distinguish Manage from Choose invocation.

The old left-list / middle work / right evidence three-column layout is superseded by one UPPER list and conditional lower Details+Context. Whole-modal close/collapse actions live at modal scope, pencil/lifecycle commands in lower-left, channels/affiliation/history operations in their actual lower-right contextual tabs. New pre-identity form uses lower-left only. Dirty selection/close guarded; ratio changes only UI presentation. Deep links resolve overlay state, not new background Settings workspace.

Reference registers closed Foundation recovery contracts for metadata, Account Code intent, channel correction, affiliation intent, and lifecycle reason; Profile and ordinary settings use their respective owner contracts. New-reference draft identities identify recovery only and never allocate accepted domain identity. Review fingerprints are not restored as authority. A changed base revision retains input but requires explicit review before submission; successful partial operations acknowledge only their declared fields. Unknown-response retries retain the exact captured command/body, while local request-validation failure permits correction without a network send.

Profile and registered definition read contracts supply descriptive/semantic presentation metadata only. The Foundation appearance panel owns its enum and current rendering availability; Settings never supplies an arbitrary JSON/key editor. Candidate/history labels use one bounded identity batch per page. Channel values remain text; more than one usable channel still requires explicit row choice and fresh server validation.
