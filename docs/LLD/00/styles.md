<!-- soma-meta
{
  "version": 1,
  "id": "LLD-00-STYLES",
  "scope": "00",
  "items": [
    {
      "id": "UI.STYLE_LIBRARY",
      "anchor": "ui-style-library",
      "depends_on": ["UI.TOKENS", "UI.VISUAL_GRAMMAR"],
      "code_paths": ["src/main/styles/", "src/main/shared/components/"]
    },
    {
      "id": "UI.SCROLLBAR",
      "anchor": "ui-scrollbar",
      "depends_on": ["UI.STYLE_LIBRARY", "UI.SCROLL"],
      "code_paths": ["src/main/styles/primitives/scrollbars.css"]
    }
  ],
  "tags": ["foundation", "frontend", "css", "style-system"]
}
-->

# Foundation style library

Scope 00 owns one internal SOMA CSS library. Future feature scopes compose it; they do not redefine the shell, interaction chrome, base controls, pane focus, scrollbars, spacing, typography, or semantic state from scratch.

<a id="ui-style-library"></a>
## UI.STYLE_LIBRARY

**Trigger/input:** Main or any future feature renders shared SOMA UI.

**Visible result:** Shared presentation is produced by one predictable token/cascade/component system rather than append-only page CSS.

### Source layout

`src/main/styles/soma.css` is the stable entry/aggregator, not the place where every feature appends another override block.

Initial target layout:

```text
src/main/styles/
  soma.css
  reset.css
  tokens.css
  base.css
  components.css
  utilities.css
  primitives/
    actions.css
    panes.css
    collections.css
    forms.css
    feedback.css
    scrollbars.css
    status.css
    shell.css
```

Feature-local CSS may exist beside a feature only for genuinely feature-specific composition. It consumes library tokens/primitives and must not override shared component internals by selector accident.

### Cascade contract

The shared library declares one stable layer order:

`reset -> tokens -> base -> primitives -> components -> utilities -> features`

Rules:

- Shared selectors are class/data-attribute based with deliberately low specificity; avoid ID selectors and deep descendant chains for styling.
- New shared rules do not rely on source-order “last override wins” against older blocks. A behavior belongs in its owning layer/file.
- `!important` is forbidden in ordinary component/feature styling; narrowly-scoped accessibility/reduced-motion/forced-color resets may use it when required.
- Shared component variation uses explicit modifier class/data attribute/custom property rather than feature selectors reaching inside another component.
- Feature CSS never changes global `button`, `input`, `body`, shell, pane or scrollbar behavior.
- The current monolithic `soma.css` override stack is migration input only; IMP-00-07 restructures it before scope-01/02 UI work starts.

### Token contract

Primitive palette values and semantic meaning remain separate. New public shared tokens use the `--soma-` prefix; temporary aliases may bridge current names during IMP-00-07 and are removed once all current Foundation components migrate.

Required semantic token families include:

- canvas/surface/raised/border;
- primary/muted/disabled text;
- brand/current/focus/selection;
- command/current/info/success/warning/destructive/unknown without color-only meaning;
- compact spacing/control heights/radii;
- typography families/sizes/line heights;
- pane/status/navigation dimensions;
- scrollbar track/thumb/hover/size.

The initial Core Dark terminal-accent set is deliberately richer than the brand board while remaining semantic and restrained:

- `command/current`: Electric-derived violet/lavender;
- `info/section`: cool cyan/ice;
- `success/ready`: muted green, never neon;
- `warning`: subdued amber/gold;
- `destructive/error`: muted coral/red.

Strict complementary hue is **not** used for ordinary active-pane state when it would collide with warning/success semantics. Current-pane treatment uses a restrained Electric-derived rail/wash plus a friendlier highlighted title color; warning amber remains reserved for warnings.

### Shared primitives

The library owns at least these reusable visual primitives before future feature UI begins:

- shell/header/navigation/status strip;
- operational pane + active-pane treatment with fixed header / scrollable body;
- compact text action/button;
- key/value list;
- metric grid;
- bounded table/list/selectable row;
- form field/input;
- modal/confirmation;
- warning/error/empty state;
- runtime/event list;
- console cue hierarchy (`$` page command, `--` pane/section, `>` nested subsection where useful);
- scrollbar.

A feature may compose these into its own workbench without copying their CSS.

### Navigation, content and command composition

Section navigation uses semantic links/current-page state, unboxed resting text and a vivid current underline/weight. Secondary navigation is smaller; keyboard focus has its own visible treatment. Tabs are not ordinary outlined command buttons.

Large pane chrome belongs to independent operational regions (Diagnostics and explicitly opened inspection workbenches). Forms, empty collections, browse and create surfaces are ordinary content; they reserve no viewport-sized bordered panel or active-pane rail merely to obtain headings/spacing. Thin separators, typography and spacing replace nested cards. Every border identifies an actual input, data, pane, dialog, shell, selection or focus boundary. Split collection tracks and compact key/value evidence reserve readable text widths; opened/selected markers do not squeeze names into vertical letter columns. Bounded lists/tables own any necessary horizontal scrolling.

Shared SectionHeading, ConsoleComment, explicit command/quiet/destructive actions and flex FormActions establish hierarchy without changing default Foundation controls. Save/Create commands stay compact rather than inheriting grid stretch. Local functional icons are sparse inline SVG, roughly 16px with consistent stroke/currentColor, decorative aria-hidden markup and visible command text; icon-only actions require an accessible name. No remote assets, emoji or icon runtime dependency.

Core Dark keeps controlled violet/lavender navigation/command identity and cyan/blue structural/secondary interaction accents. Dedicated presentation tokens `--soma-accent-navigation` and `--soma-accent-structure` never assert business state. Green/amber/red remain success/warning/destructive semantics; no large painted backgrounds or color-only state. Icons, selected rows and key section labels carry small deliberate accent moments. Concise muted `//` comments provide supporting context without prefixing every paragraph or emulating a shell.

### Focus / selection / active distinction

- DOM keyboard focus, logical active pane, row selection, opened record, hover and disabled state remain visually distinct.
- A pane receiving keyboard focus must **not** draw a giant rectangular focus ring around the entire pane. The pane uses a localized rail/header/current-locus treatment; nested controls keep the ordinary visible focus ring.
- The active pane title receives a readable semantic current/title accent in addition to the structural cue; the rail alone is not the entire active-state language.
- Pointer/keyboard activation may change logical pane activity without adding visible text such as `ACTIVE` inside every pane heading. Screen-reader status may announce the logical active pane.
- Current-pane treatment uses one small geometric/non-color cue (for example a rail) plus a restrained current accent/wash.

### Diagnostics metric rhythm

Reusable metric grids keep equal column geometry and deliberate owner order. Metric **content** is vertically centered inside each metric box (`align-items:center` or equivalent) while label/value retain left/right alignment. An odd final item stays in its natural next grid cell unless the owner explicitly requests a different layout; Foundation does **not** auto-center the orphan box.

### Console cue hierarchy

The CLI-inspired hierarchy is presentation-generated, not literal punctuation copied into every feature string.

- page/command title: `$ Diagnostics`;
- pane/major section: `-- Current run`, `-- Runtime activity`;
- nested subsection when useful: `> Durable jobs`, `> Runtime chronology`.

Shared heading components/classes/data attributes own the cue through CSS pseudo-elements or equivalent decorative markup so feature authors provide semantic text only. Cue glyphs are decorative and excluded from accessible names. Command/current cues use the Electric-derived family; major section cues may use the cool info/cyan family; warnings/errors keep their semantic colors.

### Scrollable pane structure

A reusable operational pane has two structural regions: a non-scrolling pane header and a scroll-owning body.

- pane title/header remains visible while body content scrolls;
- only the body receives the governed scrollbar/scroll-owner behavior;
- header background/border remains visually continuous with the pane;
- sticky-header CSS is acceptable only if it cannot obscure focus targets; the preferred shared primitive is explicit header + body structure;
- narrow pane switching preserves the same header/body contract.

**Failure:** A new feature that requires copying shared CSS, adding global overrides, inventing raw colors/spacing, or relying on selector-order accidents is not style-library conformant and must first extend the owning shared primitive/token.

**Side effects:** presentation architecture only.

<a id="ui-scrollbar"></a>
## UI.SCROLLBAR

**Trigger/input:** Any governed shell/pane/list/modal/navigation surface becomes scrollable.

**Visible result:** Scrollbars visually belong to the current SOMA appearance while remaining obvious, usable and OS-accessible.

**Rules:**
- All governed scroll owners consume shared scrollbar tokens; feature scopes do not style scrollbars independently.
- Core Dark uses a dark/low-noise track and a clearly visible neutral/current-compatible thumb. Hover/active thumb increases contrast without becoming a warning/success color.
- Chromium/WebKit uses the shared `::-webkit-scrollbar*` rules; standards-capable engines also receive `scrollbar-color` / `scrollbar-width` behavior.
- Horizontal and vertical scrollbars use the same family and remain usable at 200% zoom.
- Scrollbar styling never removes the thumb, makes it fully transparent, or shrinks it below a practical pointer target merely for aesthetics.
- In forced-colors/high-contrast mode, prefer/re-enable system scrollbar colors rather than forcing branded colors.
- The scrollbar primitive follows `UI.APPEARANCE`; later light/system modes swap semantic scrollbar tokens, not feature CSS.
- Nested scroll ownership remains governed by `UI.SCROLL`; visual scrollbar theming does not change which surface owns wheel/trackpad/touch scrolling.

**Failure:** If custom scrollbar styling is unsupported, the browser/OS native scrollbar remains usable. Unsupported theming is acceptable; invisible/low-contrast or feature-inconsistent scrolling is not.

**Side effects:** presentation only.

The implemented library also exposes `operational-surface`, `operational-form`, `form-field`, `action-strip`, and bounded evidence-list composition. `ConsolePanes` accepts an explicit `workbench` track variation, switcher label and owner focus request; the Diagnostics default remains unchanged. These shared variations retain fixed pane headers, governed body scrolling and narrow recomposition. Feature surfaces consume them without global control/pane CSS overrides.
