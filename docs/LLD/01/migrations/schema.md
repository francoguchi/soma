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

Creates:

### `reference_metadata`

Singleton row describing the supported matching profile and conservative Customer-reference generation.

- `singleton_guard INTEGER PRIMARY KEY CHECK(singleton_guard=1)`
- `matching_profile_id TEXT NOT NULL`
- `customer_reference_generation INTEGER NOT NULL DEFAULT 0 CHECK(customer_reference_generation>=0)`

Initial row declares `UNICODE_MATCH_V1` with generation 0. This technical singleton carries no wall-clock chronology column; migration SQL must not invent domain chronology through SQLite `now`/`strftime`. Ordinary runtime never changes `matching_profile_id`; a new profile requires a forward migration/reindex.

Protected triggers increment `customer_reference_generation` for accepted Customer Organization insert/update and Customer Account Code insert/active->superseded changes. This intentionally over-invalidates conflict-review snapshots rather than accepting against changed reference state.

### `local_user_profiles`

Singleton descriptive metadata only:

- `local_user_profile_id TEXT PRIMARY KEY REFERENCES local_admin_credentials(actor_id) ON UPDATE RESTRICT ON DELETE RESTRICT`
- `singleton_guard INTEGER NOT NULL UNIQUE CHECK(singleton_guard=1)`
- `display_name TEXT NOT NULL`
- `revision INTEGER NOT NULL DEFAULT 1`
- `created_at_utc INTEGER NOT NULL`
- `updated_at_utc INTEGER NOT NULL`

No password, verifier, username/login-name, session, auto-login or encryption material exists here. The foreign key enforces the approved singleton-model identity equality with Foundation Local Administrator `actor_id`; scope 01 still does not own credential state.

### `customer_organizations`

- immutable `customer_org_id`
- bounded `name` + governed `name_match_key`
- `lifecycle_state active|archived`
- positive revision
- created/updated UTC

Name/match key is not unique. Ordinary DELETE is rejected.

### `customer_org_identifiers`

History-preserving external identifier claims. Initial supported `identifier_type` is `customer_account_code`.

Rows store immutable identifier/customer/type/value/match-key/opening provenance plus `active|superseded`, supersession UTC/command when terminal. One Customer may have at most one active Account Code claim, but one normalized code may have multiple active Customers after reviewed shared-claim acceptance.

Required indexes include active Customer-name matching, one-active-code-per-Customer, active code claimant lookup, history order and all command-FK leading-prefix coverage. UPDATE is restricted to the single active->superseded transition; DELETE is rejected.

<a id="m01-002"></a>
## M01.002 — Contacts

Creates:

### `contacts`

Immutable `contact_id`, bounded name/match key, active/archive lifecycle, revision and chronology. Equal names are allowed; ordinary DELETE is rejected.

### `contact_channels`

Initial channel kind is only `email`. Rows carry immutable channel/contact/kind identity, accepted text, governed match key, active/archive lifecycle, revision and chronology. Equal values are allowed. Ordinary DELETE is rejected.

### `contact_affiliations`

Append-protected affiliation history: immutable relationship ID, Contact, Customer, current/historical state, opening UTC/command, optional closing UTC/command. A partial unique index permits at most one current affiliation per Contact. UPDATE is restricted to current->historical closure; DELETE is rejected.

Indexes cover active Contact matching, channel lookup/matching, current Customer affiliation, affiliation history and command-FK child paths.

<a id="m01-003"></a>
## M01.003 — Dispatch Locations and lifecycle evidence

Creates:

### `dispatch_locations`

Immutable `dispatch_location_id`, name/match key, `address_mode standalone|site_derived`, standalone address only when applicable, active/archive lifecycle, revision and chronology.

There is no Customer ownership/preference, Site ID shortcut or logistics-role column. Site relationship is owned by Infrastructure. Ordinary DELETE is rejected.

### `reference_lifecycle_events`

Append-only occurrence evidence for Customer Organization, Contact and Dispatch Location.

Stores immutable event ID, target type/ID, event type `created|archived|reactivated|descriptive_corrected`, occurrence UTC, command receipt and optional bounded reason category. UPDATE/DELETE is rejected.

Indexes cover active Dispatch matching, target event history and command-FK child path.

<a id="m01-004"></a>
## M01.004 — Typed setting values

Creates `setting_values` for explicit writes only:

- `setting_key TEXT PRIMARY KEY`
- `contract_name TEXT NOT NULL`
- `contract_version INTEGER NOT NULL CHECK(contract_version>0)`
- `value_json TEXT NOT NULL CHECK(json_valid(value_json))`
- `revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0)`
- `updated_at_utc INTEGER NOT NULL`
- `command_id TEXT NOT NULL REFERENCES command_receipts(command_id)`

Rows exist only for explicit writes. Defaults stay code-defined and absent until changed. Unknown/secret-classified settings cannot use this store. SQL REPLACE is forbidden; upgrades are explicit validated UPDATE operations. A leading-prefix index covers `command_id`.
