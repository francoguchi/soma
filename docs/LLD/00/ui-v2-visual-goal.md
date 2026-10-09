<!-- soma-meta
{
  "version": 1,
  "id": "LLD-00-UI-V2-VISUAL",
  "scope": "00",
  "items": [
    {
      "id": "UI.V2.VISUAL_GOAL",
      "anchor": "ui-v2-visual-goal",
      "depends_on": ["UI.VISUAL_GRAMMAR", "UI.STYLE_LIBRARY", "UI.OPERATIONAL_LAYOUT", "UI.ADAPTIVE_OVERLAY", "UI.BRAND", "UI.ACCESSIBILITY"],
      "code_paths": ["src/main/app/", "src/main/shared/components/", "src/main/styles/"]
    }
  ],
  "tags": ["foundation", "frontend", "visual-design", "design-gate"]
}
-->

# SOMA UI V2 — visual design goal

<a id="ui-v2-visual-goal"></a>
## UI.V2.VISUAL_GOAL

**State: DRAFT VISUAL DESIGN — operator approval pending; this document authorizes NO React, frontend deletion, backend/schema or runtime change.** On 2026-10-09 the operator examined the technically passing V1 Phase-B fixture and rejected its look. The existing UI is still present in source. This file supersedes V1's purple/cyan visual direction while retaining independently accepted interaction/domain requirements. Work happens on isolated `feat/ui-v2-reconstruction`.

### Source hierarchy and design boundaries

- PRIMARY operational reference: operator-supplied **SOMA Alpha / Zeus** screenshots (Service Requests, Spare Requests, work fields, emails, dated operations, controls, dialogues). Preserve their real information hierarchy and compact functionality rather than copying their source code or brand.
- PRIMARY framing reference: **btop**, specifically sober terminal pane geometry, neutral gray one-pixel delimiters, simple near-black surfaces, square corners and legible disciplined mono text. Do not render a literal terminal or copy btop branding.
- PRIMARY interaction reference: the operator's SOMA UI drawing and explicit decisions: icon-only workspace dock; contextual navigation beside it; ONE collection above; no lower regions when unselected; when selected lower-left read-only Details / explicit pencil edit and lower-right actual owner-provided Notes, emails, relations or history; lower panels resizable; compact Settings expands to SAME wide Reference Manager dialog above preserved workspace.
- Historical AI-generated inventory/AWS/cyberpunk mockups and V1 synthetic fixture were **not visually approved**. They are not implementation designs. Do not treat their fictional resource lists, rounded styling or neon color as product semantics.
- **Settled direction** is binding; numeric colors/sizes/font stack below are PROPOSED only until an editable visual frame and design tokens receive explicit human visual approval.

### No-go visual language

MUST NOT use purple/lavender for navigation, selection, command or focus; cyan/teal/green neon wash or glow; bright multicolor section themes; gradient backgrounds, glass overlays, large soft shadows, card-within-card decorative chrome; pill-like buttons; overly rounded panes; giant empty bordered regions; illegibly tiny monochrome text; or title-bar imitations of macOS controls in the Windows/browser application.

True success/READY may use muted green, true warning amber and destructive/error red. Blue is restrained and denotes active navigation/selection/focus, not general decoration. The canonical old SOMA brand Electric `#5A33FF` is historical asset provenance, **not a mandate to show purple in V2 UI**; retaining originals does not require reusing the purple mark in new chrome. Any logo replacement is a separate design decision.

### Suggested design tokens — candidate study, not accepted release CSS

| Role | Candidate | Meaning |
|---|---|---|
| App background | `#0B0D10` | Nearly black, neutral |
| Panel | `#111417` | Flat charcoal surface |
| Header/raised | `#171B20` | One step lighter, no gradient |
| 1px divider | `#384049` | Neutral gray, uniform |
| Primary text | `#E4E8ED` | Crisp white-gray |
| Secondary text | `#A8B1BC` | Readable subdued copy |
| Tertiary | `#818B97` | Use cautiously for true secondary text |
| Selected row | `#1D304B` | Quiet slate blue |
| Current/action | `#6299D9` | Focused blue only |
| Keyboard focus | `#9BC5EF` | Distinct outline from selection |
| Success | `#73B68A` | Actual owner state only |
| Warning | `#D7B359` | Actual caution only |
| Destructive | `#DB7980` | Actual danger only |

**Comparison required:** monochrome variant versus sparse-blue variant, same exact screen. Check contrast and readable appearance at 100%, forced colors and 200% zoom before final tokens.

**Typography candidates:** local Cascadia Mono/Consolas for IDs, tables, labels, metrics; 13–14px primary dense text, 12–13px supporting, 14–16px section title, 17–19px workspace heading. Long notes and email bodies MAY use a readable proportional stack. Core UI may not depend on online font downloads. Dense is not the same as tiny.

**Geometry candidates:** pane/control radius 0–2px; 1px neutral-gray borders; record rows 27–32px; tabs/actions ~28–34px tall; icon glyphs ~16–18px in 40px+ reachable targets; status ~24–30px. These are FIRST FRAME targets only. No developer guesses beyond approved design dimensions.

### Shell and command-area placement

```text
┌───────────────────────────────────────────────────────────────────────┐
│ SOMA                                               global controls   │
├─────┬─────────────────┬───────────────────────────────────────────────┤
│icon │ CONTEXTUAL      │ owner tabs / list toolbar                      │
│only │ NAVIGATION      ├───────────────────────────────────────────────┤
│dock │                 │ ONE PRIMARY UPPER RECORD COLLECTION            │
│     │                 │                                               │
│     │                 ├──────────────────────┬────────────────────────┤
│     │                 │ DETAILS / EDITOR     │ CONTEXT / ACTIVITY     │
│     │                 │ explicit pencil      │ real provider only     │
│     ├─────────────────┤                      │                        │
│     │ COMMAND RESERVED│                      │                        │
├─────┴─────────────────┴──────────────────────┴────────────────────────┤
│ factual status: run / READY / schema / build / local protection       │
└───────────────────────────────────────────────────────────────────────┘
```

This diagram describes ownership; final geometry is approved through actual design frames.

- Top title displays **SOMA only**; remove the rejected “LOCAL OPERATIONS” caption from V2 visual chrome. Use actual browser/Windows host controls rather than decorative traffic lights.
- First dock is ICON-ONLY: Overview, Tickets, Objectives, Inventory, Infrastructure. Each has consistent outline glyph, accessible name, tooltip, current-state cue and keyboard focus; Diagnostics remains a separate System destination. No permanent labels inside icon cells.
- Adjacent navigation shows the actual workspace owner's subsections; no invented “All Items/Favourites/Tags” categories unless the owner genuinely provides them.
- The **reserved command region belongs at the BOTTOM of the contextual navigation column, to the LEFT of the workbench and ABOVE the separate full-width status bar**. Not a fake input. Do not move it into the status strip; future CLI behavior remains deferred until approved owner command grammar exists.
- Status bar is an independent full-width factual strip showing real Foundation state; no fictional “TLS” badge or mock run/schema values.
- One upper collection contains compact rows and stable owner toolbar. With no selected item, lower Details/Context and their resize handles do not exist. Selecting reveals two lower independent-scroll regions; left starts read-only and pencil enters editing; right shows only actual supported contextual tabs. New opens a left-only creation form; resizing changes presentation only.
- Selected rows have subtle blue fill/current marker. Gray separators convey panel structure. Tabs are squared and use underline/edge current-state instead of card-like buttons. Avoid giant whitespace and repeated record names.
- Settings opens a compact modal above the preserved application. Reference Data widens that SAME modal rather than stacking a second. Modal frame is square/near-square, gray border, no purple header, with true dirty edit protection.

### Real SOMA screens to design first

The PRIMARY design-density test is **Tickets / Service Requests**, using the user-provided actual SR and Zeus illustrations as exemplars, not implementing Scope-02 functionality yet. Upper table demonstrates SR, Customer, site/cloud context, short summary, actual status, relevant dates, sorting and filtering. Lower-left uses the accepted SR-centric tabs where supported by owner design (Overview, Work fields, Spare Parts, Emails, MOPs, History). Lower-right illustrates *real* dated related activity and notes/emails only if a provider exists; long subjects/body have readable scroll/inspect path. Do not invent arbitrary backend features to match a picture.

A SECOND frame demonstrates **Contacts/Reference Manager** — Customers, Contacts, Dispatch Locations; one upper list; Contact detail/editor; real email CHANNELS and affiliation/history, not a fabricated mailbox or Notes provider. Third frame demonstrates compact Settings -> expanded same overlay. No fictional AWS, Kubernetes or inventory product catalogs as universal fixtures.

### Deliverables and acceptance — before any frontend work

Prepare EDITABLE (Figma/Penpot/equivalent) designs, not generated pictures alone:

1. Desktop shell, one empty/unselected list and one selected SR/record (1440×900 initial reference).
2. Selected operational Details/Context at real readable density, plus explicit Edit, Create and dirty state.
3. Settings compact and expanded Reference Manager, both preserving background.
4. Notes/emails/activity with long data and a truthful missing-provider state.
5. Compact component sheet: icon dock, tabs, table row, input, button, selection/focus, status, dividers, resizer, scrollbars, segmented progress with accurate units.
6. Width/reflow examples at 1040px and 390px, constrained height, plus 200% zoom, high contrast and keyboard focus.

Each frame must have versioned editable source, exported render, sample-data provenance, proposed pixel metrics and a side-by-side reference comparison. A durable approved `docs/LLD/00/design/` artifact is added ONLY AFTER the operator explicitly accepts it; ignored `.tmp/` screenshots and prior AI mockups are not design authority.

**Human visual gate**: operator explicitly approves component system, desktop shell, selected state, Settings overlay and responsive variants. Document approval and EXACT accepted palette/font/layout values in Foundation before React implementation begins. Machine tests, typecheck, screenshot creation and synthetic fixture “pass” cannot substitute for this sign-off.

**Automatic visual failure**: purple/lavender UI identity, cyan/green cyberpunk glow, bright rails, heavy round panels, illegible small text, fake functional actions, empty giant panes, duplicate ordinary collection/results, screenshot that cannot be opened by operator, modal replacing workspace or unapproved recorded Notes/email content.

### Safe rollback boundary and pending decisions

The reconstruction worktree exists. **NO code rollback is performed in this documentation checkpoint.** When the operator explicitly authorizes the selective rollback, inspect the historical pre-Reference/Settings UI commit `d89e616f...` as a frontend comparison ONLY; do not reset whole repository to it because newer commits include genuine backend/API work. Preserve current Core, SQLCipher, migrations, owner APIs, TypeScript generated contracts/clients, working-copy and recovery logic, auth/Diagnostics and existing worktrees. Do not wipe the development database. Any removal must be targeted and verified.

Still open for human review: final color/font palette and logo treatment, exact control/pane geometry, icon stroke, toolbar ordering, Tabs and contextual pane contents consistent with owners, approved design artifact/source location, narrowed reflow behavior. Scope-01 arbitrary-term Contact/Dispatch search and cross-restart splitter persistence remain separate blocked owner decisions.

**STOP:** no Codex; no new React/layout implementation; no Contacts pilot or Scope-02 implementation; no visual rollback code changes until separately requested. Next task is visual design and human review.
