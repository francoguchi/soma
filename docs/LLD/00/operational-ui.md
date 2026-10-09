<!-- soma-meta
{
 "version":1,"id":"LLD-00-OPERATIONAL-UI","scope":"00",
 "items":[
  {"id":"UI.OPERATIONAL_LAYOUT","anchor":"ui-operational-layout","depends_on":["UI.COLLECTIONS","UI.SELECTION","UI.PANE_FOCUS","UI.RESPONSIVE"],"code_paths":["src/main/shared/components/","src/main/shared/interactions/","src/main/styles/"]},
  {"id":"UI.RECORD_INSPECTOR","anchor":"ui-record-inspector","depends_on":["UI.OPERATIONAL_LAYOUT","UI.WORKING_COPY","UI.CONFIRMATION"],"code_paths":["src/main/shared/components/","src/main/shared/interactions/"]},
  {"id":"UI.CONTEXT_REGION","anchor":"ui-context-region","depends_on":["UI.RECORD_INSPECTOR","UI.COLLECTIONS","TIME.DISPLAY"],"code_paths":["src/main/shared/components/"]},
  {"id":"UI.PANEL_RESIZE","anchor":"ui-panel-resize","depends_on":["UI.OPERATIONAL_LAYOUT","UI.RESPONSIVE","UI.SCROLL","UI.ACCESSIBILITY"],"code_paths":["src/main/shared/interactions/","src/main/styles/"]},
  {"id":"UI.ADAPTIVE_OVERLAY","anchor":"ui-adaptive-overlay","depends_on":["UI.ROUTING","UI.DIALOG_FOCUS","UI.WORKING_COPY","UI.WORKSPACE_REGISTRY"],"code_paths":["src/main/app/","src/main/shared/components/"]},
  {"id":"UI.PROGRESS_SEGMENTED","anchor":"ui-progress-segmented","depends_on":["UI.TOKENS","UI.ACCESSIBILITY"],"code_paths":["src/main/shared/components/","src/main/styles/"]},
  {"id":"UI.COMMAND_RESERVATION","anchor":"ui-command-reservation","depends_on":["UI.OPERATOR_STATUS_STRIP","UI.ROUTING","UI.SEARCH"],"code_paths":["src/main/app/","src/main/styles/"]}
 ],
 "tags":["foundation","interface","operational-layout","inspector","overlay"]
}
-->

# SOMA operational interface — SOMA-UI-ARCH-V1

**Normative approved design, 2026-10-09. NOT implemented or certified by this document.** Foundation owns shared presentation/interactions, Scope 01 is first consuming implementation. Existing domain/query/auth/replay/UoW/audit/recovery authority is untouched. These UI items supersede the old permanent three-column Reference Open geometry, not historical tested behavior, deep links or owner contracts. MUST and MUST NOT are binding; SHOULD is a preference requiring reason to deviate.

## Core invariant and visual map

One consistent SOMA desktop instrument: compact top chrome, FIVE workspace icon dock (Overview, Tickets, Objectives, Inventory, Infrastructure), second contextual navigator, main surface with ONE upper collection, optional lower Details/Context, persistent bottom operator strip. Global Settings gear is NOT a sixth dock icon; invokes UI.ADAPTIVE_OVERLAY. Diagnostics remains an explicitly separate Foundation/System destination. Noncollection screens (Overview, Diagnostics, login, basic forms) are allowed different justified composition.

```text
[SOMA TOP BAR                                    SETTINGS]
[DOCK][CONTEXT][COLLECTION HEADER  New Refresh Search Advanced]
[    ][       ][ONE UPPER COLLECTION                ]
[    ][       ][=========== HORIZONTAL HANDLE =====]  <- selected only
[    ][       ][DETAILS / EDITOR | CONTEXT          ]  <- selected only
[STATUS + reserved future command area: run / READY]
```

- No selected record: lower Details and Context and both split handles are ABSENT; upper list expands. Do not render empty placeholder panels.
- Selected: upper collection retained at proposed initial ~40% height; lower region ~60%, two columns initially ~50/50. Ratios are adjustable, not hard dimensions.
- New record: retained upper collection; lower-left CREATING editor only, no fake accepted ID, right side absent unless real owner creation context exists.
- Selection, logical focus, opened item, editing, current pane and multi-selection remain separate. One click selects and REVEALS read-only inspector; it NEVER silently mutates, links, merges, edits or accepts candidate.
- Search, default listing, expert exact matching and historical query modes share ONE primary visible list. Query semantics/candidates remain distinct; no second search-result grid or duplicated count. No UI-local page-filter pretending to search full authoritative population.

<a id="ui-operational-layout"></a>
## UI.OPERATIONAL_LAYOUT

**Trigger:** operator opens an owner-backed collection, selects a row, creates or reviews.

**Visible result:** Upper list is the navigation anchor; lower-left read-only Details and lower-right contextual evidence appear only for selected accepted identity. Header Search/New/Refresh/Advanced positions stay fixed across owner collections. Scroll owners are collection, Details and Context separately, with headers fixed and no horizontal/document overflow behind the persistent bottom strip.

**Shell:** Five tiny consistent local SVG icons with one active subtle background/non-color cue, accessible labels, hover and separate keyboard focus. Adjacent contextual navigation derives from registered workspace owner, never guessed from module names. Settings is a global overlay action. No per-workspace palette required.

**State contract:**

| State | Upper collection | Lower-left | Lower-right |
|---|---|---|---|
| BROWSE | full available height | absent | absent |
| SELECTED | retained/resizable | accepted read-only Details | real owner Context |
| EDITING | retained | working-copy editor | context retained |
| CREATING | retained | creation form, no accepted ID | absent unless owner-specific |
| REVIEWING | retained | explicit proposal/preview | authoritative owner evidence as needed |

**Transitions:**
1. Single click eligible row selects; reveal lower regions with fetched accepted truth, no edit, mutation or relationship acceptance. Selecting another row refreshes both, supersedes stale responses, retains query, page/cursor, selection context and scroll where valid.
2. Enter/double-click retain ONE registered Open/focus action; on this layout focus/reveal inspector or justified owner deep destination, not a competing duplicate full-record view, automatic Edit or implicit merge. Foundation arrow/multi-select/nested control behavior remains.
3. Clear selection collapses lower regions and expands upper list; preserves ratios. Dirty edit/draft must pass UI.WORKING_COPY guard first. New opens lower-left CREATING; accepted creation selects returned owner identity. Cancel never writes.
4. Query and advanced matching use same visual collection, one count/ambiguity summary. Unique candidate remains evidence only until explicit owner acceptance; stale review fingerprints/preview/confirmation remain binding.
5. Fixed collection command zone owns New and Refresh; search bar just above list and advanced disclosure collapsed. Record-local commands belong in Details; Notes/channel commands belong to owner Context. No wandering Back button inside child pane for whole-surface transition.
6. Owners define semantics and allowed operations; Foundation only owns view/layout/query cancellation/routing/focus. A missing provider cannot be fabricated as a UI convenience.

**Responsive:** test at 1440, 1040, 1039, 390 CSS px, constrained height, 200% zoom, forced colors and reduced motion. When insufficient room for lower columns, switch collection/details/context deliberately, preserve selection/query/draft and accessible navigation; never squeeze text to vertical letters. Noncollection views and Diagnostics keep their distinct, tested layout.

<a id="ui-record-inspector"></a>
## UI.RECORD_INSPECTOR

**Trigger:** selected accepted record, explicit pencil Edit, New or owner review.

**Visible result:** lower-left shows concise read-only key/value facts with fixed-header pencil when eligible. Pencil initiates EDITING and only then exposes inputs, Save and Cancel in fixed action area. Ordinary accepted values must NOT appear as disabled form inputs. A selected row does not automatically edit or persist anything.

- Owner-approved editable fields only. Save executes original owner command, treats accepted server response as authority, updates revision and history; Cancel never creates a new accepted version. Lost replies, stale revision/review and retry are protected by existing recovery/replay/UI.WORKING_COPY.
- New creates lower-left unaccepted form; successful creation selects the accepted identity and returns to read-only. Cancel restores prior collection safely, without allocating a fake identity.
- Lifecycle/archive/reactivate and Account Code review remain owner commands with preview/confirmation/guards; no generic unguarded Delete or last-write-wins.
- Edit marker has proper accessible meaning; if not supported, never show a fake clickable pencil.
- List identifies item; Details edits it; Context supplies distinct facts. Repeating identical prominent record identity cards in multiple regions is prohibited.

<a id="ui-context-region"></a>
## UI.CONTEXT_REGION

**Trigger:** selected accepted owner identity and registered contextual capabilities.

**Visible result:** lower-right shows only applicable contextual tabs: dated Notes, communication channels, actual emails/messages, relationships/affiliation, source/import evidence and/or immutable chronology.

- A Contact email address/channel is NOT message history; a Notes tab/composer requires an actual owner Notes provider. No invented notes, message bodies or dates.
- Tab actions belong to that tab; Add channel is not a global collection command. Context is not a second generic Details form.
- Times follow TIME.DISPLAY without rewriting canonical chronology. Historical evidence is read-only unless owner explicitly offers correction. Channels/history retain bounded owner paging.
- Empty capability-specific collection: concise “No channels yet”, not repeated generic engine zero counts.
- Context remains inspectable during Details edit without silently altering working copy. Preserve tab/scroll when returning safely.

<a id="ui-panel-resize"></a>
## UI.PANEL_RESIZE

**Trigger:** selected layout includes adjacent regions and operator operates horizontal or vertical divider.

**Visible result:** horizontal divider changes upper/lower ratio, vertical lower divider changes Details/Context ratio. Handles only exist with actual adjacent regions. Creation-only layout may have a horizontal divider but no vertical handle without right region.

- Pointer/touch drag affects presentation only: never selects row, scrolls siblings or sends owner command.
- Keyboard focusable separator has orientation/min/max/current value; arrows adjust small step, Shift+arrow larger step, labelled Reset layout returns to defaults; visible focus/forced colors/200% zoom.
- Clamp to empirically tested readable minimums; if width/height insufficient, recompose rather than crop action controls or overlap footer.
- Session remember ratios independently PER workspace/collection. Cross-restart persistence is approved target but BLOCKED pending explicit Foundation storage owner. No unilateral localStorage, SQLite table or audit record.
- Viewport change/reselection retains compatible ratios. Business truth never changes as result of resize.

<a id="ui-adaptive-overlay"></a>
## UI.ADAPTIVE_OVERLAY

**Trigger:** global Settings control or contextual Reference Manager invocation.

**Visible result:** ONE modal, two sizes/states. Compact Settings contains Profile/Appearance/registered typed preferences as simple bounded forms; choosing Reference data EXPANDS SAME modal to a wide Reference Manager with the upper collection/lower Details+Context pattern. Expansion is NOT stacking two independent dialogs and does NOT replace active background workspace.

- Settings remains in closed UI.WORKSPACE_REGISTRY for compatibility but as registered global overlay entry; only the five operational workspaces belong in product dock.
- Existing `/settings/profile`, `/settings/preferences`, `/settings/reference-data/{customer_organization|contact|dispatch_location}[/{id|new}]` remain closed authenticated capability-checked overlay deep routes. Cold reload/bookmark resolves deterministic safe background origin.
- Background remains mounted/equivalently preserved: selected ticket/workspace, active subtab, query/cursor/page, scroll, focus, unsaved draft and pane ratios; it is inert and unscrollable under overlay.
- From Settings, Return to Settings collapses; Close dismisses whole overlay and returns origin. Contextual invocation from Tickets/other owner may close to invoker. “Manage reference” and “choose reference for workflow” modes are different; clicking/selection in Manager does NOT silently link identity to origin workflow.
- Dialog focus trap, Escape, dirty-close safeguards, return focus and consequential nested confirmations follow UI.DIALOG_FOCUS/UI.WORKING_COPY. Failed/unavailable owner does not discard origin.
- Proposed initial compact width ~440–580px, expanded width up to ~90–95% viewport with sensible bound; test in real browser. On narrow screens near-fullscreen modal with explicit Collection/Details/Context switcher. Do not force simple Profile/Appearance into operational collection grid.

<a id="ui-progress-segmented"></a>
## UI.PROGRESS_SEGMENTED

**Trigger:** owner-provided measurable quantity/completion/capacity.

**Visible result:** compact segmented-block meter plus truthful numeric units/numerator/denominator and accessible label. Use consistent Foundation token/colors; directional reference inspires grammar, not cloned brand/font/assets.

- Stock count, Task completion, readiness and percentage are distinct owner meanings. No fabricated denominators, made-up progress or green “ready” for unknown.
- Rendered segment count is bounded visual representation, not redefinition of value. Forced colors, 200% zoom and reduced motion retain textual truth.

<a id="ui-command-reservation"></a>
## UI.COMMAND_RESERVATION

**Trigger:** authenticated shell and runtime status updates.

**Visible result:** compact factual bottom strip showing run, READY, schema/trust etc; small space reserved for future shell-like command interface.

- Not an editable fake `user@soma:~$` prompt. No current shell, arbitrary process, SQL, filesystem or network execution. Do not remove existing runtime truth.
- Future closed `cd settings/profile` resolves only via UI.ROUTING; `find <term>` only via real UI.SEARCH owner; separate approved parser goal required. Mutations would still use accepted auth/command/confirmation/replay/audit.
- Narrow preserves readiness/run and labelled secondary fact access.

## Architecture reconciliation and implementation gates

**A — DOCUMENTATION FIRST:** UI.SHELL/REGISTRY/ROUTING/SELECTION/RESPONSIVE/SEARCH/STYLE_LIBRARY and Scope-01 frontend/checks/goal/ledger MUST refer to this authority. Old permanent three-column Open layout is superseded only as geometry; prior passing run history is preserved, not proof of this design.

**B — FOUNDATION SYNTHETIC FIXTURE:** build fixture showing dock+second navigation, one upper list, selection-gated read-only/editor/context, horizontal/vertical resize, Settings compact->expanded SAME dialog, bottom reserved strip. Test keyboard, mouse, responsive, 200% zoom, focus, forced colors and inspect actual screenshots BEFORE consuming Contact complexity.

**C — CONTACTS FIRST:** bind existing authoritative Contact list, selection, explicit pencil/new, actual channels/affiliation/history, lifecycle and exact matching. Do not fabricate Notes/mailbox. STOP for human visual acceptance after real authenticated Contact workflows before adapting Customer and Dispatch.

**D — CUSTOMER/DISPATCH REUSE:** same shared mechanics, Customer Account Code review/claimants/stale fingerprint, Dispatch standalone/Site-source restrictions and owner lifecycle. No feature-local clone layout engines.

**E — FINAL:** require focused Core/Main/browser/build/typecheck/contracts/impact and real screenshot review at 1440/1040/1039/390, constrained height, keyboard, forced colors, zoom, resize, overlay and dirty draft scenarios. Close rows only after actual evidence. No Scope-02 implementation.

**Hard blocked owner-search gate R01.06-E:** Customer default term uses existing bounded exact name/Account Code, not fuzzy. Contact arbitrary-term name/email within explicit affiliation scope requires approved owner query (raw_email presently email-only). Dispatch has no ordinary human-name search route. Never invent current-page-only filtering, accept candidate silently or expand backend contract for appearance. Approval requires bounds, indexing, cursor, count, stable order and scope.

**Hard blocked storage gate:** cross-restart per-workspace ratio persistence needs accepted Foundation owner. Session ratios interim. No migration/reset or silent storage.

**Downstream:** Tickets, Objectives, Inventory, Infrastructure reuse the shared collection grammar where appropriate while preserving their domain tab/ownership contracts. Scope-02 design is separate and not edited by this branch.
