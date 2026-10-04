<!-- soma-meta
{
  "version": 1,
  "id": "LLD-01-MIGRATIONS",
  "scope": "01",
  "items": [
    {
      "id": "M01.001",
      "anchor": "m01-001",
      "depends_on": ["CUSTOMER.ORGANIZATION", "CUSTOMER.ACCOUNT_CODE", "PROFILE.LOCAL_USER", "MIGRATION.MANIFEST", "M00.006"],
      "code_paths": ["src/core/soma/db/migrations/01/001_customer_profile.sql"]
    },
    {
      "id": "M01.002",
      "anchor": "m01-002",
      "depends_on": ["CONTACT.MASTER", "CONTACT.CHANNEL", "CONTACT.AFFILIATION", "M01.001"],
      "code_paths": ["src/core/soma/db/migrations/01/002_contacts.sql"]
    },
    {
      "id": "M01.003",
      "anchor": "m01-003",
      "depends_on": ["DISPATCH.LOCATION", "REF.LIFECYCLE", "M01.002"],
      "code_paths": ["src/core/soma/db/migrations/01/003_dispatch_lifecycle.sql"]
    },
    {
      "id": "M01.004",
      "anchor": "m01-004",
      "depends_on": ["SETTING.VALUE", "M01.003"],
      "code_paths": ["src/core/soma/db/migrations/01/004_settings.sql"]
    }
  ],
  "tags": ["identity", "reference", "settings", "migration"]
}
-->

# Identity / Reference schema

All scope-01 tables are SQLite STRICT. Technical/entity/event IDs are canonical Foundation UUIDv4 text; business/descriptive values are never relational keys.

The Foundation schema verifier must include these tables, indexes and protection/generation triggers after the corresponding migration is accepted.

<a id="m01-001"></a>
## M01.001 — Customer reference and Local User Profile

Creates the matching-profile singleton, Local User Profile metadata, Customer masters and Account Code claim history.

### `reference_metadata`

```text
singleton_guard               INTEGER PRIMARY KEY CHECK(singleton_guard = 1)
matching_profile_id           TEXT NOT NULL CHECK(length(matching_profile_id) > 0)
customer_reference_generation INTEGER NOT NULL DEFAULT 0 CHECK(customer_reference_generation >= 0)
```

Migration inserts exactly `(1, 'UNICODE_MATCH_V1', 0)`. This technical singleton has no wall-clock chronology column; migration SQL must not invent domain chronology through SQLite `now`/`strftime`. Runtime does not change the profile ID. A future profile change requires a governed forward migration/reindex.

### `local_user_profiles`

```text
local_user_profile_id TEXT PRIMARY KEY
                      REFERENCES local_admin_credentials(actor_id)
                      ON UPDATE RESTRICT ON DELETE RESTRICT
singleton_guard       INTEGER NOT NULL UNIQUE CHECK(singleton_guard = 1)
display_name          TEXT NOT NULL CHECK(length(display_name) > 0)
revision              INTEGER NOT NULL DEFAULT 1 CHECK(revision > 0)
created_at_utc        INTEGER NOT NULL CHECK(created_at_utc >= 0)
updated_at_utc        INTEGER NOT NULL CHECK(updated_at_utc >= created_at_utc)
```

No password, verifier, username/login-name, session, auto-login or encryption material exists here. The FK enforces the approved singleton-model equality with Foundation Local Administrator `actor_id`; scope 01 still does not own credential state.

A protection trigger rejects changes to `local_user_profile_id`, `singleton_guard` or `created_at_utc`; accepted profile updates may change only `display_name`, `revision`, and `updated_at_utc` through the owner command.

### `customer_organizations`

```text
customer_org_id   TEXT PRIMARY KEY
name              TEXT NOT NULL CHECK(length(name) > 0)
name_match_key    TEXT NOT NULL CHECK(length(name_match_key) > 0)
lifecycle_state   TEXT NOT NULL CHECK(lifecycle_state IN ('active','archived'))
revision          INTEGER NOT NULL DEFAULT 1 CHECK(revision > 0)
created_at_utc    INTEGER NOT NULL CHECK(created_at_utc >= 0)
updated_at_utc    INTEGER NOT NULL CHECK(updated_at_utc >= created_at_utc)
```

Name/match key is not unique. A protection trigger rejects changes to immutable `customer_org_id`/`created_at_utc`; ordinary DELETE is rejected.

### `customer_org_identifiers`

```text
customer_org_identifier_id TEXT PRIMARY KEY
customer_org_id            TEXT NOT NULL REFERENCES customer_organizations(customer_org_id)
                           ON UPDATE RESTRICT ON DELETE RESTRICT
identifier_type            TEXT NOT NULL CHECK(identifier_type = 'customer_account_code')
value_text                 TEXT NOT NULL CHECK(length(value_text) > 0)
match_key                  TEXT NOT NULL CHECK(length(match_key) > 0)
lifecycle_state            TEXT NOT NULL CHECK(lifecycle_state IN ('active','superseded'))
created_at_utc             INTEGER NOT NULL CHECK(created_at_utc >= 0)
superseded_at_utc          INTEGER NULL
created_command_id         TEXT NOT NULL REFERENCES command_receipts(command_id)
                           ON UPDATE RESTRICT ON DELETE RESTRICT
superseded_command_id      TEXT NULL REFERENCES command_receipts(command_id)
                           ON UPDATE RESTRICT ON DELETE RESTRICT
CHECK(
  (lifecycle_state='active' AND superseded_at_utc IS NULL AND superseded_command_id IS NULL)
  OR
  (lifecycle_state='superseded' AND superseded_at_utc IS NOT NULL AND superseded_command_id IS NOT NULL)
)
```

Required indexes:

- `idx_customer_org_active_name_match(lifecycle_state,name_match_key,customer_org_id)`;
- partial unique `uq_customer_org_active_identifier_type(customer_org_id,identifier_type) WHERE lifecycle_state='active'`;
- `idx_customer_active_identifier_value(identifier_type,match_key,customer_org_id) WHERE lifecycle_state='active'`;
- `idx_customer_identifier_history(customer_org_id,identifier_type,created_at_utc,customer_org_identifier_id)`;
- `idx_customer_identifier_created_command(created_command_id)`;
- `idx_customer_identifier_superseded_command(superseded_command_id) WHERE superseded_command_id IS NOT NULL`.

Identifier UPDATE is restricted to the one `active -> superseded` transition setting supersession UTC/command while preserving identity/owner/type/value/key/opening provenance; superseded rows reject further UPDATE and every DELETE is rejected.

Protected generation triggers increment `reference_metadata.customer_reference_generation` after Customer INSERT/accepted UPDATE and Account Code INSERT/accepted UPDATE. Trigger failure rolls back the owning UnitOfWork.

<a id="m01-002"></a>
## M01.002 — Contacts

### `contacts`

```text
contact_id       TEXT PRIMARY KEY
name             TEXT NOT NULL CHECK(length(name) > 0)
name_match_key   TEXT NOT NULL CHECK(length(name_match_key) > 0)
lifecycle_state  TEXT NOT NULL CHECK(lifecycle_state IN ('active','archived'))
revision         INTEGER NOT NULL DEFAULT 1 CHECK(revision > 0)
created_at_utc   INTEGER NOT NULL CHECK(created_at_utc >= 0)
updated_at_utc   INTEGER NOT NULL CHECK(updated_at_utc >= created_at_utc)
```

Equal names are allowed. A protection trigger preserves immutable `contact_id`/`created_at_utc`; ordinary DELETE is rejected.

### `contact_channels`

```text
contact_channel_id TEXT PRIMARY KEY
contact_id         TEXT NOT NULL REFERENCES contacts(contact_id)
                   ON UPDATE RESTRICT ON DELETE RESTRICT
channel_kind       TEXT NOT NULL CHECK(channel_kind = 'email')
value_text         TEXT NOT NULL CHECK(length(value_text) > 0)
match_key          TEXT NOT NULL CHECK(length(match_key) > 0)
lifecycle_state    TEXT NOT NULL CHECK(lifecycle_state IN ('active','archived'))
revision           INTEGER NOT NULL DEFAULT 1 CHECK(revision > 0)
created_at_utc     INTEGER NOT NULL CHECK(created_at_utc >= 0)
updated_at_utc     INTEGER NOT NULL CHECK(updated_at_utc >= created_at_utc)
```

A protection trigger preserves channel ID/contact/kind/created UTC, rejects any UPDATE once archived, and permits only active value/key/revision correction or the governed `active -> archived` transition. DELETE is rejected.

### `contact_affiliations`

```text
contact_affiliation_id TEXT PRIMARY KEY
contact_id             TEXT NOT NULL REFERENCES contacts(contact_id)
                       ON UPDATE RESTRICT ON DELETE RESTRICT
customer_org_id        TEXT NOT NULL REFERENCES customer_organizations(customer_org_id)
                       ON UPDATE RESTRICT ON DELETE RESTRICT
is_current             INTEGER NOT NULL CHECK(is_current IN (0,1))
opened_at_utc          INTEGER NOT NULL CHECK(opened_at_utc >= 0)
closed_at_utc          INTEGER NULL CHECK(closed_at_utc IS NULL OR closed_at_utc >= opened_at_utc)
opened_command_id      TEXT NOT NULL REFERENCES command_receipts(command_id)
                       ON UPDATE RESTRICT ON DELETE RESTRICT
closed_command_id      TEXT NULL REFERENCES command_receipts(command_id)
                       ON UPDATE RESTRICT ON DELETE RESTRICT
CHECK(
  (is_current=1 AND closed_at_utc IS NULL AND closed_command_id IS NULL)
  OR
  (is_current=0 AND closed_at_utc IS NOT NULL AND closed_command_id IS NOT NULL)
)
```

Required indexes:

- `idx_contacts_active_name_match(lifecycle_state,name_match_key,contact_id)`;
- `idx_contact_channels_contact(contact_id,lifecycle_state,channel_kind,created_at_utc,contact_channel_id)`;
- `idx_contact_channels_match(channel_kind,lifecycle_state,match_key,contact_id)`;
- partial unique `uq_contact_current_affiliation(contact_id) WHERE is_current=1`;
- `idx_contact_affiliation_customer_current(customer_org_id,is_current,contact_id)`;
- `idx_contact_affiliation_history(contact_id,opened_at_utc,contact_affiliation_id)`;
- `idx_contact_affiliation_opened_command(opened_command_id)`;
- `idx_contact_affiliation_closed_command(closed_command_id) WHERE closed_command_id IS NOT NULL`.

Affiliation UPDATE is restricted to the single current->historical closure that preserves immutable relationship/opening fields and sets closing UTC/command. Historical rows reject further UPDATE and every DELETE is rejected.

<a id="m01-003"></a>
## M01.003 — Dispatch Locations and lifecycle evidence

### `dispatch_locations`

```text
dispatch_location_id    TEXT PRIMARY KEY
name                    TEXT NOT NULL CHECK(length(name) > 0)
name_match_key          TEXT NOT NULL CHECK(length(name_match_key) > 0)
address_mode            TEXT NOT NULL CHECK(address_mode IN ('standalone','site_derived'))
standalone_address_text TEXT NULL
lifecycle_state         TEXT NOT NULL CHECK(lifecycle_state IN ('active','archived'))
revision                INTEGER NOT NULL DEFAULT 1 CHECK(revision > 0)
created_at_utc          INTEGER NOT NULL CHECK(created_at_utc >= 0)
updated_at_utc          INTEGER NOT NULL CHECK(updated_at_utc >= created_at_utc)
CHECK(
  (address_mode='standalone' AND standalone_address_text IS NOT NULL AND length(standalone_address_text) > 0)
  OR
  (address_mode='site_derived' AND standalone_address_text IS NULL)
)
```

There is no Customer ownership/preference, Site-ID shortcut or logistics-role column. A protection trigger preserves immutable location ID/address mode/created UTC; a `site_derived` row can never receive standalone address text through an update. Ordinary DELETE is rejected.

### `reference_lifecycle_events`

```text
reference_lifecycle_event_id TEXT PRIMARY KEY
target_type                  TEXT NOT NULL CHECK(target_type IN ('customer_organization','contact','dispatch_location'))
target_id                    TEXT NOT NULL
event_type                   TEXT NOT NULL CHECK(event_type IN ('created','archived','reactivated','descriptive_corrected'))
occurred_at_utc              INTEGER NOT NULL CHECK(occurred_at_utc >= 0)
command_id                   TEXT NOT NULL REFERENCES command_receipts(command_id)
                             ON UPDATE RESTRICT ON DELETE RESTRICT
reason_category              TEXT NULL
```

The polymorphic target is immutable evidence identity, not a destructive FK. UPDATE/DELETE is rejected.

Required indexes:

- `idx_dispatch_active_name_match(lifecycle_state,name_match_key,dispatch_location_id)`;
- `idx_reference_lifecycle_target(target_type,target_id,occurred_at_utc,reference_lifecycle_event_id)`;
- `idx_reference_lifecycle_command(command_id)`.

<a id="m01-004"></a>
## M01.004 — Typed setting values

Creates `setting_values` for explicit writes only:

```text
setting_key      TEXT PRIMARY KEY
contract_name    TEXT NOT NULL
contract_version INTEGER NOT NULL CHECK(contract_version > 0)
value_json       TEXT NOT NULL CHECK(json_valid(value_json))
revision         INTEGER NOT NULL DEFAULT 1 CHECK(revision > 0)
updated_at_utc   INTEGER NOT NULL CHECK(updated_at_utc >= 0)
command_id       TEXT NOT NULL REFERENCES command_receipts(command_id)
                 ON UPDATE RESTRICT ON DELETE RESTRICT
```

Rows exist only for explicit writes. Defaults remain code-defined and absent until changed. Unknown/secret-classified settings cannot use this store. SQL `REPLACE` is forbidden; upgrades are explicit validated UPDATE operations. `idx_setting_values_command(command_id)` provides required FK child coverage.

A settings UPDATE may change only registered contract/value/revision/updated UTC/command fields after owner validation. Setting keys are immutable; changing semantic identity means a new registered key plus an explicit owner migration, not an UPDATE of `setting_key`.


## Required protection and generation triggers

The current schema verifier treats the following trigger identities/behaviors as authoritative once scope 01 is implemented:

- `reference_metadata_delete_forbidden` — singleton metadata cannot be deleted during ordinary runtime.
- `local_user_profile_update_guard` / `local_user_profile_delete_forbidden` — preserve profile identity/singleton/opening chronology and forbid ordinary deletion.
- `reference_customer_organizations_update_guard` / `reference_customer_organizations_delete_forbidden` — preserve Customer immutable ID/opening chronology and forbid ordinary deletion.
- `customer_identifier_history_update_guard` / `customer_identifier_history_delete_forbidden` — permit only active->superseded closure while preserving identifier history.
- `reference_contacts_update_guard` / `reference_contacts_delete_forbidden` — preserve Contact immutable ID/opening chronology and forbid ordinary deletion.
- `contact_channels_update_guard` / `contact_channels_delete_forbidden` — preserve channel identity/owner/kind/opening chronology, reject updates after archive, and forbid deletion.
- `contact_affiliation_history_update_guard` / `contact_affiliation_history_delete_forbidden` — permit only current->historical closure and preserve relationship history.
- `reference_dispatch_locations_update_guard` / `reference_dispatch_locations_delete_forbidden` — preserve location identity/address mode/opening chronology, prevent address ownership crossing, and forbid ordinary deletion.
- `reference_lifecycle_events_update_forbidden` / `reference_lifecycle_events_delete_forbidden` — lifecycle occurrence evidence is append-only.
- `customer_reference_generation_after_customer_insert`, `customer_reference_generation_after_customer_update`, `customer_reference_generation_after_identifier_insert`, `customer_reference_generation_after_identifier_update` — conservatively advance reviewed Customer-reference freshness generation inside the same transaction.
- `setting_key_update_guard` — `setting_key` cannot be renamed in place; owner upgrades preserve the registered semantic key.

Trigger messages are stable internal integrity identities and are mapped through `REF.ERRORS`; raw SQLite text never crosses transport.

