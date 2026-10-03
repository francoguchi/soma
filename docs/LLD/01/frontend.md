<!-- soma-meta
{
  "version": 1,
  "id": "LLD-01-FRONTEND",
  "scope": "01",
  "items": [
    {
      "id": "UI.REF.WORKSPACE",
      "anchor": "ui-ref-workspace",
      "depends_on": ["UI.SHELL", "UI.COLLECTIONS", "REF.QUERY"],
      "code_paths": ["src/main/features/reference/"]
    },
    {
      "id": "UI.REF.CANDIDATES",
      "anchor": "ui-ref-candidates",
      "depends_on": ["REF.MATCHING", "UI.COLLECTIONS", "UI.SELECTION"],
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

Provide dense Reference workspaces for **Customers** (domain `CustomerOrganization`), Contacts, and Dispatch Locations using Foundation shell/collection/selection/working-copy primitives. Lists are bounded and preserve filters, active/selected identity, scroll and open-workbench context.

Active references are available for new work; archived references remain history-visible and visually ineligible until explicit reactivation.

Reference workspaces expose immutable identity and lifecycle/revision evidence without turning raw UUIDs into primary operator labels.

<a id="ui-ref-candidates"></a>
## UI.REF.CANDIDATES

Candidate matching displays `UNRESOLVED`, `UNIQUE_CANDIDATE`, and `AMBIGUOUS` explicitly. A unique candidate is never silently accepted as a link/merge.

Ambiguous state shows exact candidate count plus bounded/paginated candidate evidence; page size does not change ambiguity. Customer Account Code evidence is visually distinguishable from descriptive-name evidence. Ordinary operator labels say **Customer**; transport/domain identifiers may retain `CustomerOrganization` where precision is required.

Creating a new reference or choosing an existing candidate is always an explicit owner action.

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

<a id="ui-settings-registry"></a>
## UI.SETTINGS.REGISTRY

Settings UI is generated/composed from registered semantic definitions rather than arbitrary key/value editing. It distinguishes `DEFAULT` from `PERSISTED` without creating rows merely by viewing defaults.

Validation/errors remain setting-owner specific. Secret-classified definitions never expose raw values through the ordinary Settings surface.

Scope 01 provides the registry/store presentation substrate; later domain scopes contribute their own registered definitions and may supply feature-specific Settings panels when generic rendering would be misleading.
