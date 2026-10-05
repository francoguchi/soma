<!-- soma-meta
{
  "version": 1,
  "id": "LLD-01-API",
  "scope": "01",
  "items": [
    {
      "id": "REF.API",
      "anchor": "ref-api",
      "depends_on": ["CONTRACT.SOURCE", "SECURITY.BROWSER_SESSION", "REF.ERRORS", "REF.BOUNDS", "REF.QUERY", "REF.COMMAND_ORDER"],
      "code_paths": ["src/core/soma/modules/reference/transport/", "src/main/features/reference/api/", "src/main/features/settings/api/"]
    }
  ],
  "tags": ["identity", "reference", "api", "contract"]
}
-->

# Identity / Reference API

<a id="ref-api"></a>
## REF.API

Scope 01 exposes authenticated local API contracts beneath `/api/v1`. Machine-readable schemas ultimately live in Foundation `CONTRACT.SOURCE`; this document owns the scope-01 operation/route semantics those schemas must encode.

### Route policy

- Queries use the authenticated browser-query boundary; mutations use the authenticated browser-mutation + CSRF/origin boundary.
- Every mutation carries a Foundation command envelope with canonical `command_id` plus the exact base revision/review fingerprint required by the owner command.
- POST may represent a pure query only when structured bounded request bodies are useful (matching/review/channel validation/archive preview). Method alone never grants mutation authority.
- Generic `reference_type` is a closed enum: `customer_organization | contact | dispatch_location`; it never becomes a SQL/table identifier.
- There is no ordinary DELETE route for Customer, Contact, Dispatch Location, Contact channel, Account Code history, affiliation history, lifecycle evidence or settings history.
- Internal `PROFILE.AUTH_PARTICIPANT` and `DISPATCH.SITE_PARTICIPANT` have no public HTTP route.
- List/candidate/history/blocker/channel routes use scope-01 default 50 and maximum 200, never Beta's stale 500 transport annotation.
- Unknown fields are rejected. Request values are validated/bound data, never SQL fragments.
- Route body ceilings remain bounded: ordinary path/query requests <=4096 bytes, structured query/ordinary mutation bodies <=8192 bytes, setting write <=16384 bytes, subject to stricter field/JSON limits.

### Customer operations

- `GET /reference/customer-organizations` — active Customer page.
- `POST /reference/customer-organizations` — explicit Customer create.
- `GET /reference/customer-organizations/{id}` — current/historical detail.
- `PATCH /reference/customer-organizations/{id}` — descriptive update.
- `PUT /reference/customer-organizations/{id}/customer-account-code` — ordinary code set/replace.
- `POST /reference/customer-account-code/review-preview` — pure conflict-review query.
- `POST /reference/customer-organizations/{id}/customer-account-code/confirm-shared-claim` — reviewed shared claim.
- `POST /reference/customer-account-code/reassign` — reviewed reassignment.
- `GET /reference/customer-organizations/{id}/customer-account-code/history` — paginated preserved claim history.
- `POST /reference/identities` - pure bounded identity labels/revisions for one closed reference type, at most 200 distinct UUIDs, using one owner query per page.
- `POST /reference/match/customer-organization` — pure candidate query.

UI labels these records **Customer** while route/domain naming remains explicit.

### Contact operations

- `GET|POST /reference/contacts` — active page / explicit create.
- `GET|PATCH /reference/contacts/{id}` — detail / descriptive update.
- `GET|POST /reference/contacts/{id}/channels` — bounded channels / add channel.
- `PATCH /reference/contacts/{id}/channels/{channel_id}` — update accepted value.
- `POST /reference/contacts/{id}/channels/{channel_id}/archive` — archive channel.
- `POST /reference/contacts/{id}/channels/validate-for-use` — pure current-use validation.
- `POST /reference/contacts/{id}/affiliation` — affiliation change.
- `GET /reference/contacts/{id}/affiliation-history` — preserved bounded history.
- `POST /reference/match/contact` — pure scoped candidate query.

### Dispatch and lifecycle operations

- `GET|POST /reference/dispatch-locations` — active page / standalone create.
- `GET|PATCH /reference/dispatch-locations/{id}` — detail / descriptive or standalone-address update.
- `POST /reference/{reference_type}/{id}/archive-preview` — pure dependency preview.
- `POST /reference/{reference_type}/{id}/archive` — governed archive.
- `POST /reference/{reference_type}/{id}/reactivate` — governed reactivation.

Site-derived address edits are not accepted by the Dispatch PATCH and must route to the future Infrastructure owner.

### Profile and settings operations

- `GET /local-user-profile` - current descriptive singleton metadata only.
- `GET /settings/registry/definitions` - at most 200 closed registered ordinary-nonsecret definition descriptors; no arbitrary key enumeration or secret values.
- `PATCH /local-user-profile/display-name` — descriptive metadata only; no credential operation.
- `GET /settings/{setting_key}` — effective DEFAULT/PERSISTED typed value.
- `PUT /settings/{setting_key}` — explicit typed setting write.

The ordinary settings API cannot enumerate arbitrary unknown keys or store secrets.

### Response/error contracts

Mutation results distinguish `APPLIED|NO_CHANGE` with immutable target identity/revision and bounded typed result references. Candidate, blocker, history and channel outputs retain exact semantic count/state plus continuation where omission could otherwise change meaning.

All failures use `REF.ERRORS` through Foundation `ERROR.CONTRACT`; raw internal/provider/database text never crosses transport.

### Shared wire bindings

The closed `*.schema.json` files in this directory generate both Core validators and Main types through Foundation's contract generator. Reference queries return signed Foundation continuations; active/history pages include `as_of_utc_s` and optional exact counts. Mutation `result_refs` contain bounded `{type, id}` identities derived from the accepted result, including historical replay.

Generic setting requests/responses carry the owner-typed JSON value as bounded `value_json`. Core strictly parses it and applies the registered owner's contract before writing; reads serialize the effective typed value without materializing defaults. This preserves closed shared transport schemas without assigning arbitrary setting semantics to Reference.
