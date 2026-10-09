<!-- soma-meta
{
  "version": 1,
  "id": "LLD-00-FRONTEND",
  "scope": "00",
  "items": [
    {
      "id": "TIME.DISPLAY",
      "anchor": "time-display",
      "depends_on": ["TIME.UTC"],
      "code_paths": ["src/main/shared/time/"]
    },
    {
      "id": "API.CLIENT",
      "anchor": "api-client",
      "depends_on": ["CONTRACT.SOURCE", "SECURITY.BROWSER_SESSION", "ERROR.CONTRACT", "TRACE.CORRELATION"],
      "code_paths": ["src/main/shared/api/"]
    },
    {
      "id": "UI.BOOTSTRAP",
      "anchor": "ui-bootstrap",
      "depends_on": ["STATIC.ASSETS", "BUILD.IDENTITY", "API.CLIENT", "CAPABILITY.REGISTRY"],
      "code_paths": ["src/main/app/bootstrap/", "src/main/shared/build/"]
    },
    {
      "id": "UI.AUTH_GATE",
      "anchor": "ui-auth-gate",
      "depends_on": ["AUTH.LOCAL_ADMIN", "SECURITY.BROWSER_SESSION", "UI.BOOTSTRAP"],
      "code_paths": ["src/main/app/auth/", "src/main/shared/api/"]
    },
    {
      "id": "BRAND.ASSETS",
      "anchor": "brand-assets",
      "code_paths": ["src/main/assets/brand/"]
    },
    {
      "id": "UI.BRAND",
      "anchor": "ui-brand",
      "depends_on": ["BRAND.ASSETS"],
      "code_paths": ["src/main/styles/"]
    },
    {
      "id": "UI.APPEARANCE",
      "anchor": "ui-appearance",
      "depends_on": ["UI.TOKENS"],
      "code_paths": ["src/main/styles/", "src/main/shared/appearance/", "src/core/soma/foundation/appearance.py"]
    },
    {
      "id": "UI.TOKENS",
      "anchor": "ui-tokens",
      "depends_on": ["UI.BRAND"],
      "code_paths": ["src/main/styles/"]
    },
    {
      "id": "UI.WORKSPACE_REGISTRY",
      "anchor": "ui-workspace-registry",
      "depends_on": ["CAPABILITY.REGISTRY"],
      "code_paths": ["src/main/app/workspaces/"]
    },
    {
      "id": "UI.VISUAL_GRAMMAR",
      "anchor": "ui-visual-grammar",
      "depends_on": ["UI.BRAND", "UI.TOKENS"],
      "code_paths": ["src/main/styles/", "src/main/shared/components/"]
    },
    {
      "id": "UI.TEXT_INTEGRITY",
      "anchor": "ui-text-integrity",
      "depends_on": ["BUILD.IDENTITY"],
      "code_paths": ["src/main/shared/text/", "src/main/app/bootstrap/"]
    },
    {
      "id": "UI.PANE_FOCUS",
      "anchor": "ui-pane-focus",
      "depends_on": ["UI.SELECTION", "UI.SCROLL", "UI.TOKENS"],
      "code_paths": ["src/main/shared/interactions/", "src/main/shared/components/"]
    },
    {
      "id": "UI.OPERATOR_STATUS_STRIP",
      "anchor": "ui-operator-status-strip",
      "depends_on": ["RUNTIME.HEALTH", "BUILD.IDENTITY", "UI.TOKENS", "UI.TEXT_INTEGRITY"],
      "code_paths": ["src/main/app/status/", "src/main/shared/components/"]
    },
    {
      "id": "UI.SHELL",
      "anchor": "ui-shell",
      "depends_on": ["UI.TOKENS", "UI.VISUAL_GRAMMAR", "UI.STYLE_LIBRARY", "UI.WORKSPACE_REGISTRY", "UI.TEXT_INTEGRITY", "UI.PANE_FOCUS", "UI.OPERATOR_STATUS_STRIP", "API.CLIENT", "UI.BOOTSTRAP", "UI.AUTH_GATE"],
      "code_paths": ["src/main/app/", "src/main/shared/components/"]
    },
    {
      "id": "UI.ROUTING",
      "anchor": "ui-routing",
      "depends_on": ["UI.SHELL"],
      "code_paths": ["src/main/app/routing/", "src/main/shared/navigation/"]
    },
    {
      "id": "UI.CAPABILITY_STATE",
      "anchor": "ui-capability-state",
      "depends_on": ["CAPABILITY.REGISTRY", "UI.SHELL"],
      "code_paths": ["src/main/app/capabilities/", "src/main/shared/components/"]
    },
    {
      "id": "UI.SYSTEM_TRAY",
      "anchor": "ui-system-tray",
      "depends_on": ["RUNTIME.TRUSTED_CONTROL", "DIAGNOSTICS.OPERATOR_LOGS", "BRAND.ASSETS"],
      "code_paths": ["src/core/soma/runtime/tray.py", "src/main/assets/brand/"]
    },
    {
      "id": "UI.SELECTION",
      "anchor": "ui-selection",
      "depends_on": [],
      "code_paths": ["src/main/shared/interactions/"]
    },
    {
      "id": "UI.SCROLL",
      "anchor": "ui-scroll",
      "depends_on": [],
      "code_paths": ["src/main/shared/interactions/"]
    },
    {
      "id": "UI.COLLECTIONS",
      "anchor": "ui-collections",
      "depends_on": ["QUERY.PAGE", "API.CLIENT", "UI.SELECTION", "UI.SCROLL"],
      "code_paths": ["src/main/shared/collections/", "src/main/shared/components/"]
    },
    {
      "id": "UI.SEARCH",
      "anchor": "ui-search",
      "depends_on": ["UI.COLLECTIONS", "UI.ROUTING", "UI.ACCESSIBILITY"],
      "code_paths": ["src/main/shared/search/", "src/main/shared/components/", "src/main/shared/interactions/"]
    },
    {
      "id": "UI.AUTOCOMPLETE",
      "anchor": "ui-autocomplete",
      "depends_on": ["UI.COLLECTIONS", "UI.SELECTION", "UI.SCROLL"],
      "code_paths": ["src/main/shared/components/autocomplete/", "src/main/shared/interactions/"]
    },
    {
      "id": "UI.DIALOG_FOCUS",
      "anchor": "ui-dialog-focus",
      "depends_on": ["UI.SHELL", "UI.SCROLL"],
      "code_paths": ["src/main/shared/components/dialog/", "src/main/shared/interactions/"]
    },
    {
      "id": "UI.RESPONSIVE",
      "anchor": "ui-responsive",
      "depends_on": ["UI.SHELL", "UI.SELECTION", "UI.SCROLL"],
      "code_paths": ["src/main/shared/components/", "src/main/styles/"]
    },
    {
      "id": "UI.WORKING_COPY",
      "anchor": "ui-working-copy",
      "depends_on": ["API.CLIENT", "WORKING_COPY.STORE"],
      "code_paths": ["src/main/shared/interactions/"]
    },
    {
      "id": "UI.CONFIRMATION",
      "anchor": "ui-confirmation",
      "depends_on": ["UI.SHELL", "SECURITY.DELIBERATE_PROOF"],
      "code_paths": ["src/main/shared/interactions/", "src/main/shared/components/"]
    },
    {
      "id": "UI.SAFE_UNDO",
      "anchor": "ui-safe-undo",
      "depends_on": ["API.CLIENT", "UI.CONFIRMATION"],
      "code_paths": ["src/main/shared/interactions/undo/", "src/main/shared/components/"]
    },
    {
      "id": "UI.DIAGNOSTICS_STATE",
      "anchor": "ui-diagnostics-state",
      "depends_on": ["RUNTIME.HEALTH", "DIAGNOSTICS.OPERATOR_LOGS", "UI.CAPABILITY_STATE", "UI.SHELL"],
      "code_paths": ["src/main/features/system/", "src/main/shared/components/"]
    },
    {
      "id": "UI.ACCESSIBILITY",
      "anchor": "ui-accessibility",
      "depends_on": ["UI.TOKENS", "UI.SELECTION", "UI.DIALOG_FOCUS", "UI.CONFIRMATION"],
      "code_paths": ["src/main/shared/interactions/", "src/main/styles/"]
    },
    {
      "id": "UI.ERROR_STATE",
      "anchor": "ui-error-state",
      "depends_on": ["API.CLIENT", "UI.TOKENS", "ERROR.CONTRACT"],
      "code_paths": ["src/main/shared/components/", "src/main/shared/api/"]
    }
  ],
  "tags": ["foundation", "user-plane", "ui"]
}
-->

# Foundation frontend

<a id="time-display"></a>
## TIME.DISPLAY

**Trigger/input:** Main receives an authoritative UTC chronology value plus optional provenance fields.

**Visible result:** Ordinary UI shows the instant in the operator's effective local timezone and readable locale format; evidence/debug surfaces may additionally expose canonical UTC/source detail.

**Rules:**
- One shared formatter owns ordinary SOMA date/time presentation.
- Main never rewrites the underlying authoritative instant.
- The effective display timezone is explicit and testable; it defaults to the operator/system setting defined by current product settings.
- Raw epoch/unit values are not primary operator-facing text.
- Relative age/duration is derived against the same captured reference instant for a projection/page where consistency matters.
- Unknown/absent time is shown as an explicit unknown/none state, never epoch zero.

**Failure:** Invalid/unsupported time shows a visible unavailable state and preserves raw evidence in inspector/debug context when safe.

**Side effects:** none.

Reuse provenance: Beta LLD-10 presentation lessons and LLD-09 chronology refinement.

<a id="api-client"></a>
## API.CLIENT

**Trigger/input:** Feature state issues a query/command through the typed local API boundary.

**Visible result:** One shared client applies generated/validated contracts, request identity, cancellation/supersession, security context, and normalized transport errors.

**Rules:**
- Contract fields come from CONTRACT.SOURCE.
- Stale superseded query responses cannot replace newer request state.
- Feature views do not call transport directly.
- Errors preserve stable machine identity plus operator-readable presentation context.
- Authentication/session/CSRF headers or equivalent context are attached centrally when those providers exist.
- No runtime network dependency/download is introduced by the client.

**Failure:** Contract mismatch, unavailable host/session, network failure, or invalid response returns typed failure to feature state; no fabricated success.

**Side effects:** local request state only, except commands explicitly sent to core.

<a id="ui-bootstrap"></a>
## UI.BOOTSTRAP

**Trigger/input:** Browser loads the verified Main bundle for the current SOMA origin.

**Visible result:** Establish one current-run UI bootstrap state before feature routes/actions become active.

**Rules:**
- Bootstrap verifies compatible frontend/build/protocol identity, current session/authentication state when available, capability registry, and required foundation API availability.
- A stale browser tab from a prior run cannot silently operate against a new `run_id`; it must refresh/rebootstrap before mutations.
- Bootstrap failure renders a bounded recovery screen rather than partially enabling domain actions.
- Main assets are local STATIC.ASSETS only; no remote scripts/fonts/styles/runtime package downloads.
- Bootstrap does not manufacture unavailable capabilities or domain records.

**Failure:** Build/protocol mismatch, unavailable host, session failure, or invalid bootstrap contract produces explicit reload/restart/login/remediation as applicable.

**Side effects:** client bootstrap/session presentation state only.

<a id="ui-auth-gate"></a>
## UI.AUTH_GATE

**Trigger/input:** UI.BOOTSTRAP receives the current AUTH.LOCAL_ADMIN state for the current run.

**Visible result:** Gate ordinary SOMA workspaces behind one minimal Local Administrator first-run setup/login flow.

**Rules:**
- Bootstrap states are at least `setup_required`, `login_required`, and `authenticated`.
- `setup_required` presents password + confirmation only; there is no username field or profile editor.
- `login_required` presents password only plus concise recovery guidance appropriate to the current development phase.
- Password fields use secure input semantics, never persist to local/session storage, never populate URLs, and are never copied into diagnostic/error context.
- First-run setup and login use exact current-origin authentication contracts; stale prior-run pages must rebootstrap before submitting credentials.
- Successful setup/login transitions through SECURITY.BROWSER_SESSION and reboots the authenticated shell state rather than manually marking the UI authenticated.
- Logout destroys the current browser session and returns to `login_required`.
- Generic credential failure text is uniform and does not disclose whether verifier/schema/internal security state differs.
- Password change/reset and profile/display-name controls are intentionally absent from this foundation surface.

**Failure:** Invalid credentials/setup input, stale run, unavailable authentication service, or session issuance failure remains on the auth gate with safe actionable error state; no ordinary domain route/action becomes available.

**Side effects:** authentication request/session presentation state only.

<a id="ui-routing"></a>
## UI.ROUTING

**Trigger/input:** Operator opens a SOMA route, follows a record action, or uses browser history.

**Visible result:** Resolve through one closed route registry over the browser History API while retaining eligible navigation context.

**Rules:**
- Route IDs/patterns are statically registered by the owning feature; arbitrary strings do not become executable feature routes.
- Legacy /settings/* URLs are authenticated closed overlay-entry states using UI.ADAPTIVE_OVERLAY, never a replacement background workspace; cold reload uses safe origin fallback.
- A route records enough restoration context to preserve filters, active/selected IDs, pane/tab, scroll anchor, and focus token where applicable.
- Back/forward navigation replays navigation state, not accepted business mutation.
- Unknown/unavailable capability routes show explicit unavailable/not-found state and safe return navigation.
- No routing library/runtime download is required by the baseline.

**Failure:** Malformed route or unavailable owner does not dispatch owner API calls until route/capability validation succeeds.

**Side effects:** browser history/navigation state only.


### Future interaction concept — SOMA command surface (deferred)

This is a design placeholder, not an accepted current implementation item.

A future SOMA command surface may expose shell-like local interaction such as:

`operator@soma:~$ cd settings/profile`

`operator@soma:~$ find <term>`

The presentation may borrow shell syntax, but it is **not** an operating-system shell and never grants arbitrary process, filesystem, SQL, network or code execution.

Any eventual parser maps a closed command vocabulary onto existing SOMA authorities:

- navigation verbs resolve only through `UI.ROUTING` / `UI.WORKSPACE_REGISTRY`;
- search/find verbs dispatch only to registered owner search contracts governed by `UI.SEARCH`;
- mutation verbs, if ever accepted, use the same owner commands, authentication, validation, confirmation, replay and audit rules as graphical actions;
- capability/unavailable state remains authoritative;
- command completion/help enumerates only registered safe commands/routes;
- user-entered text never becomes raw SQL, filesystem path, OS shell or subprocess input.

The command surface is another interface to the same application semantics, never a second authority. No visible fake prompt or disabled command bar is required until a dedicated design/implementation goal accepts its grammar.

<a id="ui-capability-state"></a>
## UI.CAPABILITY_STATE

**Trigger/input:** UI bootstrap or runtime capability update provides CAPABILITY.REGISTRY.

**Visible result:** Navigation/actions truthfully reflect what this assembled build can perform.

**Rules:**
- Only workspaces declared by UI.WORKSPACE_REGISTRY participate in primary navigation. Declared future workspaces remain visible while unavailable; they render disabled/unavailable state rather than disappearing or invoking stubs/500s.
- `available` capability surfaces may be entered; `unavailable` surfaces stay visibly disabled with concise “Not available in this build” meaning.
- Repeated unavailable navigation rows may use a compact non-color marker such as `—`/`unavailable` treatment instead of repeating the full phrase on every row, provided the accessible name/tooltip/detail exposes the full meaning.
- `development` may be shown with a concise non-authoritative development indicator.
- Capability state controls exposure/availability only; it is never business authorization or a replacement for owner action blockers.
- A route/bookmark to an unavailable feature remains understandable and provides safe navigation back.
- Unknown capability is treated as unavailable.

**Failure:** Missing/invalid registry yields conservative unavailable behavior except for foundation recovery/diagnostics surfaces.

**Side effects:** presentation/navigation availability only.

<a id="ui-collections"></a>
## UI.COLLECTIONS

**Trigger/input:** A feature presents a bounded server-owned collection/list/table/tree result.

**Visible result:** Render deterministic bounded pages with explicit loading/partial/continuation state while preserving selection and evidence context.

**Rules:**
- Default requested page size is 100 and no shared collection requests more than QUERY.PAGE's maximum 200.
- Main never decodes or edits opaque server cursor internals.
- At most 200 rows/items from one collection surface are retained in the ordinary DOM at once unless an owning item explicitly defines a stricter/specialized presentation.
- New filter/order input supersedes prior request identity; stale responses are discarded. A shared collection may retain at most eight bounded query-page/cursor/scroll contexts for accepted return/Clear behavior while rendering only one page. Revisited evidence is stale until the owner query refreshes.
- Reaching a bound exposes partial/additional-results state and never silently drops selected IDs, warnings, dirty fields, or accepted rows.
- Server/owner owns total/filter/order semantics; UI does not resort a partial page as though it were the complete dataset.

**Failure:** Cursor/transport/stale error preserves current safe context and exposes refresh/retry rather than mixing result generations.

**Side effects:** client collection/request state only.


<a id="ui-search"></a>
## UI.SEARCH

**Trigger/input:** An owner exposes a bounded searchable collection, exact-evidence lookup, or search-capable chooser.

**Visible result:** SOMA presents one recognisable search grammar with predictable placement, availability, loading, no-result and error state while preserving owner authority over what is actually searchable.

**Rules:**
- Shared search owns presentation and interaction mechanics; domain owners own query semantics, scope, ordering, bounds and result truth.
- Search never silently filters only the currently loaded bounded page when the authoritative searchable set may be larger.
- Search controls remain compact in a predictable collection-associated command zone across browsing and an opened inspection workbench. Supported default search uses one entry field; expert evidence fields remain in a collapsed Advanced search disclosure.
- Search replaces the query represented by the owner's primary collection instead of adding a competing result list. Ordinary collection and exact-candidate modes remain semantically distinguishable; owner evidence/count/ambiguity is presented once and opening a result is never implicit acceptance.
- Owner-specific search may use one field, multiple exact-evidence fields or a bounded chooser; those variations retain common search iconography/state/action grammar.
- Search state distinguishes idle, disabled-empty-source, unavailable, loading, results, no-results, partial/additional-results and error.
- A known-empty authoritative searchable source leaves the affordance recognisable but disabled with a concise accessible explanation.
- An empty current page does not by itself imply that the searchable source is empty.
- Enter submits/accepts only where the owner contract defines that behavior; clear/Escape never performs business mutation.
- Search does not create entities, relationships or ownership implicitly.
- Search/filter state participates in `UI.ROUTING` restoration where the owner promises return-state preservation.
- Accessible name and disabled/unavailable meaning do not rely on the search icon or placeholder text alone.

**Failure:** Missing/unavailable owner search remains visibly unavailable and never falls back to local fuzzy filtering or unbounded enumeration.

**Side effects:** local query/presentation state plus bounded owner read/query calls only.

<a id="ui-autocomplete"></a>
## UI.AUTOCOMPLETE

**Trigger/input:** Operator enters text into a bounded searchable chooser.

**Visible result:** Present a bounded, keyboard/pointer/touch-equivalent suggestion list without enumerating an unbounded population or creating entities implicitly.

**Rules:**
- Initial shared defaults: minimum 2 entered characters, page size 25, maximum 50 loaded options, 150 ms debounce; an owning feature may select a documented minimum in the range 1–4.
- Focus alone never enumerates an unbounded population; an owner may expose an explicit bounded disclosure.
- Each query has identity; new input cancels/supersedes stale work.
- Arrow keys change active option without accepting; Enter accepts one eligible active option; Escape closes without change; Tab never commits ambiguity.
- Typed/highlighted text never creates an entity or relationship. Missing-entity creation is a separate owner command.
- Popup is its own scroll owner and remains viewport-safe.

**Failure:** Loading, minimum-input, no-match, partial, stale, source-warning, and error are distinct states.

**Side effects:** local chooser state only.

Reuse provenance: Beta LLD-10 bounded chooser/autocomplete contract.

<a id="ui-dialog-focus"></a>
## UI.DIALOG_FOCUS

**Trigger/input:** A modal/dialog/impact preview is opened or closed.

**Visible result:** Provide safe accessible focus, scroll isolation, dismissal, and return behavior.

**Rules:**
- Dialog exposes accessible title/purpose, target/material consequence where applicable, validation/warnings, primary action, and cancellation/safe exit.
- Initial focus is safe/context-appropriate and never automatically destructive.
- Focus is contained within the active modal; background is inert/non-interactive and cannot scroll.
- Escape closes a dismissible modal without acceptance; blocking dismissal requires a genuine atomic/domain reason and visible explanation.
- Close restores the invoker when it survives, otherwise a deterministic safe fallback.
- Long dialog content scrolls inside its owned surface.

**Failure:** If focus isolation cannot be established, consequential dialog action remains unavailable rather than leaking interaction into the background.

**Side effects:** presentation/focus state only.

<a id="ui-safe-undo"></a>
## UI.SAFE_UNDO

**Trigger/input:** An owning domain exposes an explicitly registered currently valid inverse/correction preview for an accepted reversible action.

**Visible result:** Offer bounded action-scoped Undo only while that exact inverse remains safe.

**Rules:**
- There is no global rollback writer and no generic database undo.
- Owner supplies inverse/correction command contract, current preview/fingerprint, eligibility, blockers, and consequence text.
- UI revalidates owner preview immediately before dispatching the inverse.
- Independent reversible actions may retain independent bounded opportunities; one action does not replace unrelated undo state.
- Stale/unsafe/unregistered inverse becomes unavailable with reason.
- Accepted evidence/lifecycle that requires correction/cancellation/supersession uses the owner's named command rather than rewriting history.

**Failure:** Missing/indeterminate/stale inverse registration fails closed; original accepted action remains unchanged.

**Side effects:** inverse owner command only after successful fresh validation.

Reuse provenance: Beta LLD-10 safe-undo principle, moved into shared user-plane foundation.

<a id="ui-diagnostics-state"></a>
## UI.DIAGNOSTICS_STATE

**Trigger/input:** Operator opens the foundation System/Diagnostics surface.

**Visible result:** Show concise live-test state without requiring log-file hunting.

**Minimum content:** host/build identity, run state/uptime, instance/schema/migration state, capability availability, technical job counts, safe executor/connection/transaction counts when available, current log identity/path action, recent runtime chronology/events, and separately identified sanitized Foundation warning/error codes when present.

**Rules:**
- This surface is observational; it does not mutate jobs, migrations, database, capabilities, or runtime except through separately labelled trusted controls.
- Secrets, customer/domain bodies, raw exceptions, raw SQL, reusable credentials, and unrestricted filesystem paths are never displayed.
- Time uses TIME.DISPLAY while an evidence/detail affordance may expose canonical UTC.
- Open-log/log-folder actions use declared diagnostics/trusted local mechanisms.
- Failed diagnostic subpanels remain visibly partial rather than making the whole application unavailable.
- Normal host lifecycle transitions are presented as compact runtime/event evidence, not as recent warning/error codes.
- Capability diagnostics report registered descriptors only. Missing future workspace owners appear through the workspace unavailable state rather than synthetic diagnostic entries.
- Compact metric groups such as Durable jobs use the shared balanced metric-grid primitive. Equal columns stay aligned and an odd final metric is centered/spans intentionally rather than being stranded at the left edge.

**Failure:** Diagnostic provider failure shows unavailable/partial state and never changes authoritative readiness/domain results.

**Side effects:** presentation only except separately labelled local open-file/folder actions.

<a id="ui-accessibility"></a>
## UI.ACCESSIBILITY

**Trigger/input:** Any shared SOMA interaction renders or receives keyboard/pointer/touch input, zoom/text enlargement, reduced-motion, high-contrast, or forced-color preferences.

**Visible result:** Equivalent operability and meaning across supported input/presentation modes.

**Rules:**
- Every operable element has visible unclipped focus distinct from hover/selection.
- State/consequence never depends only on hue, blinking, motion, position, or one sensory channel.
- Initial support target includes 200% text zoom and a shared minimum pointer target of 32 CSS px where density permits; compact table cells may use equivalent enlarged labelled action affordances.
- Reduced motion preserves final state, chronology, progress, warning, and operability.
- Forced colors/high contrast preserve selection/focus/warning/destructive distinctions.
- Pointer, keyboard, and touch paths converge on the same owner command result.
- Icon-only actions require accessible name and a labelled alternative/tooltip; tooltip is never the only label.

**Failure:** A shared component that cannot meet its required accessible interaction must not be used for a consequential operation.

**Side effects:** presentation/interaction only.

<a id="ui-appearance"></a>
## UI.APPEARANCE

**Trigger/input:** Main initializes its shared presentation theme or a later settings owner supplies an accepted appearance preference.

**Visible result:** SOMA starts in **SOMA Core Dark** when no accepted preference exists and all components consume theme-independent semantic tokens.

**Rules:**
- `core_dark` is the initial development and product default.
- Scope 00 owns appearance semantics. The accepted current/future mode enum is `core_dark | system | light`; `core_dark` is the default. When a typed settings store is available, Foundation may register/persist this preference through that generic store without transferring appearance meaning to the settings module.
- Beta terminal-green/amber/violet decorative skins are not part of the current Foundation contract; adding skins later requires a new accepted appearance decision rather than inheriting old Beta values.
- Components never branch on raw palette values to infer business meaning.
- Theme changes, when later exposed, preserve selection/focus/warning/destructive distinctions and accessibility requirements.
- Brand assets and semantic state remain legible in Core Dark; small text/focus colors may use accessible derived blues rather than forcing raw brand blue.

**Failure:** Missing/invalid appearance preference falls back deterministically to `core_dark`.

**Side effects:** presentation theme state only.

<a id="brand-assets"></a>
## BRAND.ASSETS

**Trigger/input:** Runtime tray or Main needs a permanent SOMA-owned logo/icon asset.

**Visible result:** Resolve only canonical repository-owned SOMA brand masters/derived runtime variants.

**Rules:**
- Accepted permanent SVG/PNG/ICO assets live under `src/main/assets/brand/`; `.tmp/` references never become runtime dependencies.
- One canonical source asset may have deterministic derived sizes/formats for tray/favicon/application use.
- Runtime never downloads, regenerates from screenshots, or substitutes third-party branding.
- This item owns asset identity/files only. UI.BRAND owns how Main visually applies the brand.

**Failure:** Missing required runtime icon falls back only where the consuming contract explicitly permits text/default shell presentation; it never loads an untracked/remote asset.

**Side effects:** none.

<a id="ui-brand"></a>
## UI.BRAND

**Trigger/input:** Main renders SOMA-owned application chrome or permanent branded assets.

**Visible result:** SOMA uses the approved stellated symbol/wordmark and a restrained technical visual identity derived from the supplied brand set.

**Rules:**
- Canonical permanent assets live under `src/main/assets/brand/`; `.tmp/` screenshots/design candidates are never runtime dependencies.
- Historical canonical brand palette includes Electric `#5A33FF`, Slate `#0F1115`, Mist `#ECEEF2`, and Pure `#FFFFFF`. **UI V2 does NOT require or permit violet/lavender visual chrome**. The old brand assets are retained until a separately approved asset replacement. See `ui-v2-visual-goal.md`; semantic state still uses owner truth.
- The brand blue may be used freely for the logo, large graphic accents, and sufficiently contrasted surfaces.
- Small dark-mode text/focus/status use a derived semantic accent that meets current accessibility contrast targets rather than forcing the raw brand-blue value.
- Do not copy third-party product branding/trade dress from directional references.

**Failure:** Missing canonical asset falls back to a SOMA text identity rather than loading from remote/untracked files.

**Side effects:** none.

<a id="ui-tokens"></a>
## UI.TOKENS

**Trigger/input:** Any main component requests visual primitives or semantic state styling.

**Visible result:** One versioned token system separates primitive palette/type/spacing/radius/elevation/motion values from semantic meaning.

**Rules:**
- Components consume semantic tokens, not ad-hoc status colors.
- Selection, focus, hover, checked membership, disabled, provisional, destructive, warning, stale, historical, and unknown remain visually distinguishable.
- State never depends only on color, motion, or position.
- Monospace is favored for identifiers, timestamps, metrics, command cues, and dense technical evidence; readable proportional text is used for long-form notes/messages/help.
- Light, dark, high-contrast/forced-color, zoom, and enlarged-text modes preserve meaning.
- The NEW UI V2 visual direction is SOMA Alpha/Zeus operational density plus sober btop framing: neutral near-black, 1px gray delimiters, square frames and restrained blue selected/focus. V1 purple/cyan synthetic fixture appearance was REJECTED. See draft human visual acceptance gate `ui-v2-visual-goal.md`.

**Failure:** Missing semantic token is a development error; components do not silently invent a replacement palette.

**Side effects:** none.

<a id="ui-workspace-registry"></a>
## UI.WORKSPACE_REGISTRY

**Trigger/input:** Main constructs primary navigation for the assembled build.

**Visible result:** SOMA exposes one closed, deterministic set of top-level product workspaces in this order:

1. **Overview**
2. **Tickets**
3. **Objectives**
4. **Inventory**
5. **Infrastructure**
6. **Settings** — registered global overlay entry, not sixth product icon

**System surface:** **Diagnostics** is a Foundation/System destination and is visually separated from product workspaces. It is not inserted into the product workspace sequence merely because it is available.

**Rules:**
- Five operational workspaces occupy the icon dock; the registered Settings entry opens UI.ADAPTIVE_OVERLAY over the preserved active workspace. Diagnostics remains separate.
- Workspace names/order are product contract, not inferred from capability IDs, module names, database tables, Beta packet names, or agent guesses.
- Capability availability controls whether a declared workspace is active/development/unavailable; it never creates a new top-level workspace.
- Declared-but-unavailable product workspaces remain visible with concise unavailable state.
- Unknown capabilities remain absent from primary navigation unless this registry is deliberately revised.
- **Finance**, **Products**, **Service levels**, **Workflows**, and **Customers** are not current top-level SOMA workspaces. Domain concepts with those meanings may appear inside their owning workspace/context, but Main must not invent primary navigation entries for them.
- Scope-01 reusable reference administration is reached through the Settings/reference-data surface or owning contextual links; Customer identity does not automatically create a primary **Customers** workspace.
- Deep links may enter a feature route without adding that route to top-level navigation.
- Future top-level workspace changes require an explicit LLD revision and corresponding navigation/check update.

**Failure:** Missing/invalid workspace registry blocks ordinary shell navigation rather than falling back to module/capability enumeration.

**Side effects:** presentation/navigation registration only.

<a id="ui-visual-grammar"></a>
## UI.VISUAL_GRAMMAR

**Trigger/input:** SOMA shell/shared components render authenticated operational UI.

**Visible result:** The interface uses a restrained terminal-inspired operational grammar: dense information, thin structural separation, compact controls, strong textual hierarchy, and multi-pane inspectability without becoming a literal terminal emulator.

**Rules:**
- Discoverability takes precedence over decorative terminal resemblance: operators should understand where to navigate, search, edit and act without interpreting internal architecture.
- Navigation, search, command actions, selection and evidence use visibly distinct presentation roles; a surface must not render every interaction as the same bordered control.
- Search presentation follows `UI.SEARCH` and remains spatially consistent across owner collections.
- Empty-state copy is owner-facing and concise. Generic pagination/query-engine text does not replace simple domain statements such as `No Contacts yet.`.
- Technical implementation detail such as byte encoding, persistence revision or semantic-owner identity remains secondary unless required for conflict/evidence handling.
- Repeated information is removed unless the repetition communicates distinct state.
- Whole-surface navigation is positioned at the scope it controls; a transition affecting the entire workbench does not appear to belong to one child pane.
- Terminal comment syntax such as `//` may provide short secondary guidance, but ordinary usability never depends on understanding shell conventions.
- Primary structure comes from alignment, whitespace rhythm, 1px separators/borders, typography, and pane boundaries. Large floating rounded cards are exceptional rather than the default container.
- Initial surface radii are restrained: square/near-square operational panes and rows; controls may use a small radius. Large soft SaaS-style card radii/shadows are not the default visual hierarchy.
- Operational chrome, navigation labels, status bands, identifiers, timestamps, metrics, command cues, table/list rows, evidence keys and compact section labels favor the approved local monospace stack. Long notes, explanations and form help may use the readable proportional stack.
- Typical dense list/status rows target approximately 28–36 CSS px height at default zoom when content permits. Empty padding must not dominate information-bearing space.
- Pane/content padding is compact and consistent; use nested card-within-card presentation only when the nested boundary has real interaction/authority meaning.
- The operational canvas fills the available application viewport after fixed shell chrome. Panes may stretch to own remaining space while their facts stay top-aligned; do not leave a large dead field below a small dashboard grid when the same pane system can own that space.
- Pane tracks need not be visually equal. Intentional asymmetry is preferred when one pane carries denser/current operational work and another carries secondary evidence; equal quarters are not a default.
- Buttons/actions are compact and textual with restrained borders/backgrounds. Large full-width call-to-action styling is reserved for genuine gates such as first-run authentication or narrow layouts where width is necessary.
- Status/evidence presentation uses the shared console-cue hierarchy (`$` page/command, `--` pane/major section, `>` nested subsection where useful), compact brackets, monospace labels and restrained semantic accents. Cues are generated by shared presentation primitives rather than hand-authored into every title.
- UI V2 must use a human-approved sparse blue selected/focus treatment on NEUTRAL backgrounds. Electric-derived violet navigation/current and decorative cyan structural rails are superseded and prohibited in V2. True READY/success, warning and danger retain muted distinct semantic colors.
- Typography has at least three clear operational levels: page/workspace title, pane/section heading, and compact label/value/evidence text. The entire screen must not speak at one typographic volume.
- Operator-supplied SOMA Alpha/Zeus screenshots and sober btop framing replace Init.Habits and AI-generated cyberpunk mockups as the primary V2 visual reference. Keep SOMA information architecture; do not invent example vendor features.
- Diagnostics is the Foundation exemplar: current-run/runtime/capability/log facts should read as one operational console composed of panes/rows, not four marketing/dashboard cards. Pane headers remain fixed while only pane bodies scroll.
- Wide business workspaces should support navigation/context rail, primary operational list/work area, contextual/evidence pane, plus bounded lower activity surface where the owner needs it.
- Semantic state remains visible without relying on color alone. Focus/selection/warning/destructive/unavailable states remain distinct under forced colors/high contrast.
- Visual density never permits clipping/truncating authoritative identifiers/evidence without an explicit inspect/copy path.

**Failure:** Shared component or feature styling that reintroduces an unregistered visual hierarchy/ad-hoc palette is a development conformance failure, not a new implicit design convention.

**Side effects:** presentation only.

<a id="ui-text-integrity"></a>
## UI.TEXT_INTEGRITY

**Trigger/input:** Static Main assets or runtime strings are rendered.

**Visible result:** Operator-facing text is valid Unicode and displays intended separators/symbols without mojibake.

**Rules:**
- Repository source/static text is UTF-8; transport JSON follows the contract encoding.
- Do not render accidental mojibake sequences such as `Â·`, `Ã—`, replacement-character `�`, or mis-decoded UTF-8.
- Prefer ordinary Unicode glyphs only when available in the local font stack and understandable in accessible text; otherwise use ASCII text.
- Decorative separators are presentation characters, never protocol/domain delimiters.
- Build/test fixtures include representative SOMA symbols/separators and fail when bytes are decoded through the wrong code page.

**Failure:** Invalid/mis-decoded visible text falls back to safe plain text and is reported as a development defect; it never silently ships as the canonical label.

**Side effects:** none.

<a id="ui-pane-focus"></a>
## UI.PANE_FOCUS

**Trigger/input:** Pointer, keyboard, touch, route restore, or narrow-pane switching moves the operator's current interaction locus among shell/workbench panes.

**Visible result:** Exactly one pane is the active interaction owner when pane-specific keyboard/scroll commands are meaningful, and that state is visually distinguishable from row selection, opened record, hover, and DOM focus.

**Rules:**
- Active pane is a presentation/interaction concept; it never changes business truth.
- Pointer interaction inside a pane makes it active unless a modal/overlay owns focus.
- Keyboard traversal into a pane makes it active without selecting/opening a record merely to advertise activity.
- Pane-local shortcuts, arrows, page navigation and scroll commands target the active pane only; no hidden/background pane consumes them.
- Active pane uses one restrained current-locus rail/header wash plus a readable current-title tint and non-color structure where accessibility requires it. It does not show a persistent visible `ACTIVE` badge/word in ordinary desktop presentation.
- Focusing the pane container itself must not produce a full-pane rectangular outline. Keyboard-visible pane focus is localized to the same rail/header/current-locus treatment; nested buttons/inputs/links keep their ordinary visible focus ring.
- Active pane survives responsive recomposition when the same logical pane still exists. If it cannot survive, the owner chooses a deterministic adjacent/default pane and preserves record/filter/working-copy state.
- Narrow mode exposes an explicit pane switcher/label so the operator always knows which logical pane is active.
- Modal/dialog focus temporarily supersedes pane focus and restores the surviving invoker pane on close.
- Pane activation and row selection remain independent: selecting a record may occur inside the active pane, but activating a pane never fabricates a selection.

**Failure:** If the previously active pane disappears or becomes unavailable, focus moves to a deterministic safe shell/pane target and no keyboard command is delivered to stale hidden content.

**Side effects:** local interaction/focus state only.

<a id="ui-operator-status-strip"></a>
## UI.OPERATOR_STATUS_STRIP

**Trigger/input:** Authenticated shell renders and runtime/build health changes.

**Visible result:** A persistent compact bottom status strip gives the operator one-glance instrument state without opening Diagnostics.

**Minimum content:** short current run identity, host readiness/observation summary when available, current schema/migration identity, development/build mode, and local trust/data-protection summary.

**Rules:**
- Example wide presentation: `run 1cf8147f · READY · schema M00.005 · development · loopback/encrypted`.
- The strip is factual status, not a warning/event log and not a second navigation bar. UI.COMMAND_RESERVATION is future design, not a fake editable shell.
- Normal READY/startup state uses neutral/brand-current emphasis; warning/error emphasis appears only for actual degraded/failed conditions.
- Run/build/schema/trust facts come from current Foundation providers and never from feature-local guesses.
- Values are compact and bounded; exact/canonical detail remains available through Diagnostics when needed.
- `READY` in the persistent strip uses the muted success/ready token, not plain white and not a neon green. Pre-ready/checking stays neutral/current; degraded/failed uses governed warning/destructive treatment.
- On narrow width, preserve at least run identity + readiness and provide a labelled overflow/detail affordance for secondary facts rather than wrapping into a tall footer.
- The strip does not display secrets, full reusable tokens, unrestricted filesystem paths, or customer/domain data.

**Failure:** Missing one optional provider renders a concise unavailable marker for that fact while preserving the rest of the strip; the shell does not disappear.

**Side effects:** presentation only.

<a id="ui-shell"></a>
## UI.SHELL

**Trigger/input:** Application starts or operator navigates between SOMA workspaces/records.

**Visible result:** Stable global shell composes workspace navigation, scoped context, selected-entity/workbench regions, and bounded activity/evidence surfaces without discarding relevant interaction state.

**Rules:**
- Shell navigation does not own business truth.
- For collection-oriented owners retain UI.OPERATIONAL_LAYOUT **interaction intent**, but the V1 fixture is NOT accepted visually. New rendering must first pass UI.V2.VISUAL_GOAL editable-frame gate: ICON-ONLY dock, sober gray framing, contextual-left reserved command region above independent full-width factual status, one upper collection and selected-only lower Details/Context, same Settings overlay.
- Domain features own their workbench content/actions; shared shell owns placement and navigation mechanics.
- Primary product navigation comes only from UI.WORKSPACE_REGISTRY; the shell never enumerates CAPABILITY.REGISTRY into guessed workspace labels.
- Returning from a record preserves applicable filter/query, selected/active records, scroll context, and focus where the referenced result survives.
- Deep operational surfaces favor dense inspectable information over decorative dashboard space. UI.OPERATIONAL_LAYOUT (operational-ui.md) supersedes old always-on three-column Reference geometry.
- Between top chrome and UI.OPERATOR_STATUS_STRIP, the shell provides a bounded working viewport. Actual multi-region inspection surfaces fill it with owner panes and pane-local scrolling; ordinary content-sized settings, browse and creation surfaces remain top-aligned without reserving viewport-sized bordered chrome. Shared tabs, section/icon/comment hierarchy and explicit command variants follow UI.STYLE_LIBRARY.
- Jobs, warnings, imports, reviews, and recent processing may use a shared activity surface, but their facts remain owner-produced.

**Failure:** Missing feature route shows explicit unavailable/not-found state and preserves safe navigation back to the prior context.

**Side effects:** navigation/presentation state only.

<a id="ui-system-tray"></a>
## UI.SYSTEM_TRAY

**Trigger/input:** A Windows SOMA host starts through either detached or console development launch.

**Visible result:** Exactly one SOMA system-tray icon represents the current verified host and exposes tidy local runtime controls.

**Rules:**
- Use the approved SOMA application/tray icon from canonical brand assets and native Win32 `Shell_NotifyIconW` with a hidden message window; no separate tray framework is required.
- Tooltip/status reflects at least `Starting`, `Ready`, `Stopping`, and `Failed` when the host can still present that state.
- The context menu contains, in this order:
  1. a disabled status line (`SOMA — <state>`);
  2. `Open SOMA`;
  3. `Open Current Log`;
  4. `Open Logs Folder`;
  5. separator;
  6. `Stop SOMA`.
- `Open SOMA` performs a fresh RUNTIME.TRUSTED_CONTROL verification before opening the browser origin.
- `Open Current Log` opens the exact current run log recorded by DIAGNOSTICS.OPERATOR_LOGS; `Open Logs Folder` opens the canonical diagnostics directory.
- `Stop SOMA` invokes the same authenticated graceful shutdown path as `soma_stop.bat`; tray UI is never independent kill authority.
- Console and detached modes use the same tray behavior. Ctrl+C in console mode and tray Stop both converge on the same graceful host shutdown.
- There is no separate `Exit Tray` action while the host is running: the icon represents host lifecycle and disappears after exact-owned runtime cleanup.
- Only one icon is shown for the authoritative run; launcher races do not create duplicate tray owners.
- Tray failure does not make the host untrusted or unavailable; launcher/console controls remain usable and the failure is logged safely.

**Failure:** If native tray creation fails, SOMA continues with console/BAT runtime controls and records a sanitized warning. A tray action that cannot freshly verify the current run is disabled/fails closed and performs no control action.

**Side effects:** Native shell notification icon/menu state and verified runtime-control requests only.

Reuse provenance: Beta LLD-12 package lifecycle/technology design (`Shell_NotifyIconW`) promoted into scope 00 because live-test runtime control is foundational in the new SOMA.

<a id="ui-selection"></a>
## UI.SELECTION

**Trigger/input:** Pointer, keyboard, or touch interaction with a record list/table/tree/grid.

**Visible result:** Focus, active row, single selection, multi-selection membership, expansion, opened record, and nested-control activation remain distinct states.

**Rules:**
- Primary single click selects/activates; it does not dispatch deep Open. On UI.OPERATIONAL_LAYOUT it reveals read-only lower Details/actual Context, never edits or mutates.
- `Enter` on the active eligible row and double-click on the row body invoke the same registered Open/focus action; for this layout focus the inspector or explicitly justified owner view, never implicit edit, merge, duplicate list or mutation.
- Arrow keys move active focus without opening.
- On multi-select surfaces, `Space` controls membership; arrows never silently change membership.
- Nested buttons, links, checkboxes, menus, expanders, and actions perform only their own behavior.
- Touch provides an explicit labelled Open action; double-tap is not required.
- Blank/header/disabled/non-record regions never open a record.
- Return navigation restores surviving IDs or a deterministic nearby/container fallback and explains a lost target when material.

**Failure:** stale/ineligible target does not open and produces the owning surface's explicit stale/unavailable state.

**Side effects:** local interaction/navigation state only.

Reuse provenance: Beta LLD-10 `SELECTION_OPEN_V1`.

<a id="ui-scroll"></a>
## UI.SCROLL

**Trigger/input:** Wheel/trackpad, keyboard, or touch scrolling within nested SOMA panes.

**Visible result:** Scrolling belongs to the nearest legitimate scroll surface for the interaction origin and does not unexpectedly chain into sibling/background panes at boundaries.

**Rules:**
- Pointer wheel/trackpad: nearest applicable scroll owner beneath the pointer.
- Keyboard: focused scroll surface, otherwise the workbench's declared primary surface.
- Touch: gesture-origin scroll surface after movement disambiguation; ownership does not transfer mid-gesture.
- Horizontal delta is offered only to horizontal-capable owners.
- Dialog/modal prevents background scrolling.
- Autocomplete/listbox owns its scroll while applicable.
- Scrolling never changes selection, multi-select membership, accepts an option, opens a record, completes a hold, or submits a command.

**Failure:** if no applicable owner exists, input is ignored or handled by the next legitimate containing surface; never redirected to an unrelated sibling.

**Side effects:** scroll position only.

Reuse provenance: Beta LLD-10 `SCROLL_OWNERSHIP_V1`.

<a id="ui-responsive"></a>
## UI.RESPONSIVE

**Trigger/input:** Available container/viewport width changes.

**Visible result:** SOMA reflows without losing capability, material facts, warnings, actions, selection, drafts, or pane context.

**Rules:**
- Old 1040 CSS px workbench threshold is a regression probe, not fixed breakpoint for new upper/lower UI; recompose according to measured panel minima, test 1440/1040/1039/390 and 200% zoom.
- Wide collection-oriented operational views use upper list and conditional lower Details/Context split with accessible resizers; unselected list expands. Overview/Diagnostics retain justified special views.
- Narrow layouts must **recompose**, not merely stack every wide-layout panel vertically. Primary workspace navigation becomes a compact labelled tab/command strip with bounded horizontal scrolling or an explicit overflow control; owner workbench panes switch one-at-a-time/drawer/stack as appropriate.
- Diagnostics narrow mode presents one operational panel at a time in deliberate order and preserves access to all facts/actions without forcing a page-length copy of the desktop grid.
- Tables remain tabular inside bounded horizontal scroll rather than causing page overflow.
- Layout changes preserve active pane, filters, selection, scroll context, working copies, unsaved protection, and applicable focus.
- Responsive behavior is capability-based, not named-device-specific.

**Failure:** unsupported layout constraints produce bounded overflow/explicit alternative, never hidden authoritative actions/facts.

**Side effects:** presentation layout only.

Reuse provenance: Beta LLD-10 shared workbench shell and responsive composition.

<a id="ui-working-copy"></a>
## UI.WORKING_COPY

**Trigger/input:** Operator changes editable UI state before an owner command accepts it.

**Visible result:** Unsaved working intent is explicit, recoverable where supported, and distinct from accepted domain state including an accepted domain lifecycle state named Draft.

**Rules:**
- Dirty scope/fields are identifiable.
- Save/discard/selective operations disclose exact scope.
- Partial save is permitted only when it forms a complete valid owner transaction.
- Validation/permission/stale/transport failure preserves safe input and never shows false success.
- Material edits do not silently autosave into accepted truth without an owner contract.
- A copy based on an older accepted revision never overwrites newer truth; conflict review distinguishes current truth from proposed edits.
- Last-write-wins is prohibited for identity/evidence/lifecycle facts.
- Navigation within the same flow preserves working intent; abandoning it warns when loss would occur.
- Recoverable checkpointing uses WORKING_COPY.STORE; shared initial bounds are 262144 canonical draft bytes, 256 nonexpired copies, 7-day expiry, checkpoint after 5 seconds idle, and at least 30 seconds between successful checkpoints for the same copy.
- Restoring a recoverable copy never accepts it; current owner revision/freshness is shown and stale copies enter conflict review.

**Failure:** stale/invalid/unsupported restoration, generation conflict, capacity, or checkpoint failure preserves safe in-memory input and never becomes accepted truth.

**Side effects:** local/recoverable draft state only; accepted mutation only through owner commands.

Reuse provenance: Beta LLD-10 working-copy semantics.

Recovery restore returns the server-verified `draft_sha256` alongside generation/freshness evidence. Main passes that exact checksum to the shared working-copy client; it does not manufacture a replacement checkpoint identity. Closed owner draft schemas and freshness callbacks remain supplied through composition.

<a id="ui-confirmation"></a>
## UI.CONFIRMATION

**Trigger/input:** Operator activates an action whose owner declares a confirmation tier.

**Visible result:** Shared UI applies the declared friction without changing the owner's eligibility or business meaning.

**Rules:**
- Tiers: ordinary activation, deliberate hold, impact preview, impact preview plus hold, or domain-specific authority.
- Confirmation tier is owner-declared/registered; UI does not invent consequences.
- Deliberate hold lasts one continuous `3000 ms` measured by browser TIME.MONOTONIC semantics (`performance.now()`) and is paired with SECURITY.DELIBERATE_PROOF server challenge/proof for tiers that require a hold.
- Release/cancel/route or target/revision/preview change, lost activation, visibility suspension that invalidates continuity, stale dependency, challenge expiry, or scroll-classified movement resets/abandons the hold and submits nothing.
- Completion obtains at most one proof and triggers at most one owning command; owner state is revalidated and proof consumed at the owner-declared boundary before mutation.
- Impact preview shows material targets/effects/blockers; hold never substitutes for required preview.
- Pointer, keyboard, and touch provide equivalent consequence/label semantics.

**Failure:** indeterminate owner/target/proof/eligibility fails closed and no mutation is dispatched.

**Side effects:** local confirmation state; command dispatch only after successful completion.

Reuse provenance: Beta LLD-10 confirmation tiers and deliberate-hold algorithm.

<a id="ui-error-state"></a>
## UI.ERROR_STATE

**Trigger/input:** Shared client/feature reports loading, empty, partial, stale, validation, conflict, warning, or failure state.

**Visible result:** Operator can distinguish the state and see an actionable next step when one exists.

**Rules:**
- Loading, no match, empty data, partial page, stale response, source warning, validation error, conflict, unavailable, and command failure are distinct.
- A failed command never renders the optimistic state as accepted.
- Machine error identity may be inspectable; primary text is concise and operational.
- Warning/error meaning is not color-only.
- Owner-projected blockers/remediation are shown rather than recomputed by UI.

**Failure:** unknown error falls back to a generic explicit failure while preserving request/diagnostic correlation that is safe to expose.

**Side effects:** presentation state only.
