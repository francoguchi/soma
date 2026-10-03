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
      "id": "UI.BRAND",
      "anchor": "ui-brand",
      "code_paths": ["src/main/assets/brand/", "src/main/styles/"]
    },
    {
      "id": "UI.APPEARANCE",
      "anchor": "ui-appearance",
      "depends_on": ["UI.BRAND", "UI.APPEARANCE"],
      "code_paths": ["src/main/styles/", "src/main/shared/appearance/"]
    },
    {
      "id": "UI.TOKENS",
      "anchor": "ui-tokens",
      "depends_on": ["UI.BRAND"],
      "code_paths": ["src/main/styles/"]
    },
    {
      "id": "UI.SHELL",
      "anchor": "ui-shell",
      "depends_on": ["UI.TOKENS", "API.CLIENT", "UI.BOOTSTRAP", "UI.AUTH_GATE"],
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
      "depends_on": ["RUNTIME.TRUSTED_CONTROL", "DIAGNOSTICS.OPERATOR_LOGS", "UI.BRAND"],
      "code_paths": ["src/core/soma/runtime/tray.py", "src/main/assets/brand/"]
    },
    {
      "id": "UI.SELECTION",
      "anchor": "ui-selection",
      "depends_on": ["UI.SHELL"],
      "code_paths": ["src/main/shared/interactions/"]
    },
    {
      "id": "UI.SCROLL",
      "anchor": "ui-scroll",
      "depends_on": ["UI.SHELL"],
      "code_paths": ["src/main/shared/interactions/"]
    },
    {
      "id": "UI.COLLECTIONS",
      "anchor": "ui-collections",
      "depends_on": ["QUERY.PAGE", "API.CLIENT", "UI.SELECTION", "UI.SCROLL"],
      "code_paths": ["src/main/shared/collections/", "src/main/shared/components/"]
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

<a id="ui-routing"></a>
## UI.ROUTING

**Trigger/input:** Operator opens a SOMA route, follows a record action, or uses browser history.

**Visible result:** Resolve through one closed route registry over the browser History API while retaining eligible navigation context.

**Rules:**
- Route IDs/patterns are statically registered by the owning feature; arbitrary strings do not become executable feature routes.
- A route records enough restoration context to preserve filters, active/selected IDs, pane/tab, scroll anchor, and focus token where applicable.
- Back/forward navigation replays navigation state, not accepted business mutation.
- Unknown/unavailable capability routes show explicit unavailable/not-found state and safe return navigation.
- No routing library/runtime download is required by the baseline.

**Failure:** Malformed route or unavailable owner does not dispatch owner API calls until route/capability validation succeeds.

**Side effects:** browser history/navigation state only.

<a id="ui-capability-state"></a>
## UI.CAPABILITY_STATE

**Trigger/input:** UI bootstrap or runtime capability update provides CAPABILITY.REGISTRY.

**Visible result:** Navigation/actions truthfully reflect what this assembled build can perform.

**Rules:**
- Declared future workspaces remain visible in primary navigation while unavailable; they render disabled/unavailable state rather than disappearing or invoking stubs/500s.
- `available` capability surfaces may be entered; `unavailable` surfaces stay visibly disabled with concise “Not available in this build” meaning.
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
- New filter/order input supersedes prior request identity; stale responses are discarded.
- Reaching a bound exposes partial/additional-results state and never silently drops selected IDs, warnings, dirty fields, or accepted rows.
- Server/owner owns total/filter/order semantics; UI does not resort a partial page as though it were the complete dataset.

**Failure:** Cursor/transport/stale error preserves current safe context and exposes refresh/retry rather than mixing result generations.

**Side effects:** client collection/request state only.

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

**Minimum content:** host/build identity, run state/uptime, instance/schema/migration state, capability availability, technical job counts, safe executor/connection/transaction counts when available, current log identity/path action, and recent sanitized foundation error codes.

**Rules:**
- This surface is observational; it does not mutate jobs, migrations, database, capabilities, or runtime except through separately labelled trusted controls.
- Secrets, customer/domain bodies, raw exceptions, raw SQL, reusable credentials, and unrestricted filesystem paths are never displayed.
- Time uses TIME.DISPLAY while an evidence/detail affordance may expose canonical UTC.
- Open-log/log-folder actions use declared diagnostics/trusted local mechanisms.
- Failed diagnostic subpanels remain visibly partial rather than making the whole application unavailable.

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

<a id="ui-brand"></a>
## UI.BRAND

**Trigger/input:** Main renders SOMA-owned application chrome or permanent branded assets.

**Visible result:** SOMA uses the approved stellated symbol/wordmark and a restrained technical visual identity derived from the supplied brand set.

**Rules:**
- Canonical permanent assets live under `src/main/assets/brand/`; `.tmp/` screenshots/design candidates are never runtime dependencies.
- Primary brand blue: `#0A33FF`. Primary dark slate: `#0F1115`.
- The brand blue may be used freely for the logo, large graphic accents, and sufficiently contrasted surfaces.
- Small dark-mode text/focus/status use a derived semantic accent that meets current accessibility contrast targets rather than forcing `#0A33FF`.
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
- The visual direction is terminal-inspired operational density plus contextual exploration and Wireshark-style list/detail/evidence inspection; it is not a literal terminal emulator.

**Failure:** Missing semantic token is a development error; components do not silently invent a replacement palette.

**Side effects:** none.

<a id="ui-shell"></a>
## UI.SHELL

**Trigger/input:** Application starts or operator navigates between SOMA workspaces/records.

**Visible result:** Stable global shell composes workspace navigation, scoped context, selected-entity/workbench regions, and bounded activity/evidence surfaces without discarding relevant interaction state.

**Rules:**
- Shell navigation does not own business truth.
- Domain features own their workbench content/actions; shared shell owns placement and navigation mechanics.
- Returning from a record preserves applicable filter/query, selected/active records, scroll context, and focus where the referenced result survives.
- Deep operational surfaces favor dense inspectable information over decorative dashboard space.
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
- Primary single click selects/activates; it does not open.
- `Enter` on the active eligible row and double-click on the row body open the same default destination.
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
- Initial workbench prototype uses `1040 CSS px` as the wide split baseline; live testing may revise this value by updating this item.
- Wide layouts may show operational list/work pane beside context/communications/evidence.
- Narrow layouts use labelled pane switching/drawers/stacks rather than deleting either side.
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
