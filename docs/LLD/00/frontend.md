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
      "depends_on": ["CONTRACT.SOURCE"],
      "code_paths": ["src/main/shared/api/"]
    },
    {
      "id": "UI.BRAND",
      "anchor": "ui-brand",
      "code_paths": ["src/main/assets/brand/", "src/main/styles/"]
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
      "depends_on": ["UI.TOKENS", "API.CLIENT"],
      "code_paths": ["src/main/app/", "src/main/shared/components/"]
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
      "id": "UI.RESPONSIVE",
      "anchor": "ui-responsive",
      "depends_on": ["UI.SHELL", "UI.SELECTION", "UI.SCROLL"],
      "code_paths": ["src/main/shared/components/", "src/main/styles/"]
    },
    {
      "id": "UI.WORKING_COPY",
      "anchor": "ui-working-copy",
      "depends_on": ["API.CLIENT"],
      "code_paths": ["src/main/shared/interactions/"]
    },
    {
      "id": "UI.CONFIRMATION",
      "anchor": "ui-confirmation",
      "depends_on": ["UI.SHELL"],
      "code_paths": ["src/main/shared/interactions/", "src/main/shared/components/"]
    },
    {
      "id": "UI.ERROR_STATE",
      "anchor": "ui-error-state",
      "depends_on": ["API.CLIENT", "UI.TOKENS"],
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

**Failure:** stale/invalid/unsupported restoration remains a working-copy conflict/unavailable state and never becomes accepted truth.

**Side effects:** local/recoverable draft state only; accepted mutation only through owner commands.

Reuse provenance: Beta LLD-10 working-copy semantics.

<a id="ui-confirmation"></a>
## UI.CONFIRMATION

**Trigger/input:** Operator activates an action whose owner declares a confirmation tier.

**Visible result:** Shared UI applies the declared friction without changing the owner's eligibility or business meaning.

**Rules:**
- Tiers: ordinary activation, deliberate hold, impact preview, impact preview plus hold, or domain-specific authority.
- Confirmation tier is owner-declared/registered; UI does not invent consequences.
- Deliberate hold lasts one continuous `3000 ms` measured by a monotonic source.
- Release/cancel/route or target change, lost activation, stale dependency, or scroll-classified movement resets the hold and submits nothing.
- Completion triggers at most one command and owner state is revalidated before commit.
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
