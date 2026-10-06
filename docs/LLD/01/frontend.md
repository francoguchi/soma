<!-- soma-meta
{
  "version": 1,
  "id": "LLD-01-FRONTEND",
  "scope": "01",
  "items": [
    {
      "id": "UI.REF.WORKSPACE",
      "anchor": "ui-ref-workspace",
      "depends_on": ["UI.SHELL", "UI.WORKSPACE_REGISTRY", "UI.COLLECTIONS", "UI.SEARCH", "REF.QUERY"],
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
      "depends_on": ["PROFILE.LOCAL_USER", "UI.WORKING_COPY"],
      "code_paths": ["src/main/features/settings/profile/"]
    },
    {
      "id": "UI.SETTINGS.REGISTRY",
      "anchor": "ui-settings-registry",
      "depends_on": ["SETTING.REGISTRY", "SETTING.VALUE", "UI.WORKING_COPY"],
      "code_paths": ["src/main/features/settings/"]
    }
  ],
  "tags": ["identity", "reference", "settings", "user-plane"]
}
-->

# Identity / Reference frontend

<a id="ui-ref-workspace"></a>
## UI.REF.WORKSPACE

Provide dense Reference-data surfaces for **Customers** (domain `CustomerOrganization`), Contacts, and Dispatch Locations using Foundation shell/collection/selection/working-copy primitives. Their primary navigation entry is **Settings → Reference data** under Foundation `UI.WORKSPACE_REGISTRY`; scope 01 does not create a top-level Customers workspace. Contextual deep links from owning workflows may open the same surfaces directly. Lists are bounded and preserve filters, active/selected identity, scroll and open-workbench context.

Active references are available for new work; archived references remain history-visible and visually ineligible until explicit reactivation.

Reference workspaces expose immutable identity and lifecycle/revision evidence without turning raw UUIDs into primary operator labels.


### Browse/search composition

Reference Browse consumes Foundation `UI.SEARCH` wherever the current owner exposes bounded search or exact-evidence lookup. Search placement is stable across Customer, Contact and Dispatch browse surfaces even when owner-specific fields differ.

The search affordance reflects the authoritative owner/search source:

- known searchable source with eligible records -> enabled;
- authoritative searchable source known empty -> remains recognisable but disabled with a concise accessible reason;
- source/capability unavailable -> disabled/unavailable with a concise reason;
- empty current bounded page alone -> does not disable broader valid owner search.

Reference never filters only the currently loaded bounded page while presenting that subset as complete search truth.

Browse empty state shows one primary explanation and one useful next action. Generic page/count machinery stays hidden when it adds no operator value.

Collection rows present record identity separately from selection/open/focus evidence. `Selected`, `Opened`, lifecycle state and revision never concatenate into the human-readable record name.

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

The Settings routes are `/settings/profile`, `/settings/preferences`, and `/settings/reference-data/{customer_organization|contact|dispatch_location}[/{id|new}]`; contextual routes never add primary workspace labels. Core supplies the same closed route grammar to Foundation static serving. Settings capability availability comes from the actual composed Reference/Settings owner.

Settings uses Foundation section/tab grammar: one `$ Settings` page title, Profile/Preferences/Reference data sub-navigation and specific content headings. Profile is a bounded ordinary section with current display-name evidence, editable field, compact Save and sign-in comment. Preferences renders the sole registered Appearance definition directly; multiple definitions use compact registry-generated sub-navigation, never arbitrary key/value editing.

Reference type navigation is secondary to Settings navigation. Browse is ordinary content, with entity heading and New <type>/quiet Refresh actions, structured Name/Revision/Open rows and one pristine empty message. Exact matching and historical identity tools are collapsed utilities. Create is a bounded non-pane form with secondary back/cancel and compact primary creation command; it has no collection/work/evidence chrome before an accepted identity.

Only Open uses the retained three-pane collection / Details / Evidence & history workbench. Section labels identify entity details, Account Code, Lifecycle, Identity, Channels, Affiliation, Address source and History as applicable. Narrow mode switches the same three panes. Collection models and DOM are retained independently of presentation containers across Browse/Open/Create and Settings visits, preserving filters, selection, cursor/page, matching inputs, scroll and open/return context. Back/Cancel consumes Foundation unsaved-navigation/recovery protections. Refresh does not reset collection pagination.


Whole-Reference navigation such as `Back to list` belongs to the Reference surface context, not inside the Details pane. Create cancellation and surface navigation do not present duplicate controls for the same transition; if their semantics differ because of unsaved working intent, that distinction is explicit and tested.

Open-mode owner subsections use concise owner-language empty states such as `No channels yet.` or `No affiliation history.` rather than generic zero-page text when pagination evidence is not useful.

Reference registers closed Foundation recovery contracts for metadata, Account Code intent, channel correction, affiliation intent, and lifecycle reason; Profile and ordinary settings use their respective owner contracts. New-reference draft identities identify recovery only and never allocate accepted domain identity. Review fingerprints are not restored as authority. A changed base revision retains input but requires explicit review before submission; successful partial operations acknowledge only their declared fields. Unknown-response retries retain the exact captured command/body, while local request-validation failure permits correction without a network send.

Profile and registered definition read contracts supply descriptive/semantic presentation metadata only. The Foundation appearance panel owns its enum and current rendering availability; Settings never supplies an arbitrary JSON/key editor. Candidate/history labels use one bounded identity batch per page. Channel values remain text; more than one usable channel still requires explicit row choice and fresh server validation.
