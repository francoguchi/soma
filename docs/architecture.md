<!-- soma-meta
{
  "version": 1,
  "id": "SOMA.ARCHITECTURE",
  "scope": "00",
  "tags": ["architecture", "coding"]
}
-->

# SOMA coding guide

This document defines the current repository layout, documentation model, coding boundaries, and iterative development workflow.

## Development mode

- SOMA is in development and testing with one current user.
- Start with a fresh SOMA development database. Carryover of Alpha/Beta records is outside the current implementation scope.
- The current development database is disposable. Schema changes may rewrite, replace, or reorder development migrations, followed by database recreation.
- Write code, exercise it, fix observed behavior, and repeat. Every design item and implementation goal may be revised.
- Run checks relevant to changed behavior. Formal certification occurs after required application functionality is complete and has been tested in use.
- A certificate, design freeze, or per-module formal review is never a prerequisite for continuing development.

Database recreation is an implementation action when schema changes require it. Resolve the configured SOMA development instance, stop its runtime, recreate its database and migration ledger from the current manifest, then apply the declared development seed. Reset only that resolved instance. Routine startup does not clear records. The reset entry point and seed are foundation responsibilities and are not assumed to exist before implementation.

## Scope and authority

Use the current user request to select work. For that work, read:

1. The implementation goal selected by the request. If none exists, create it from the requested outcome before substantial implementation.
2. Its referenced LLD items.
3. The interfaces it directly consumes.
4. The affected source and relevant tests.

Read additional dependents only when the change affects them. Do not reread the entire repository before each task.

The user can revise any design decision. Current LLD items define intended behavior; implementation goals define the increment being built. A goal that changes behavior updates the owning LLD item in the same iteration. README files state purpose. Alpha/Beta documents and code are reuse references, not current authority.

Do not recursively inspect Alpha/Beta. Follow provenance or reuse references named by the current LLD/goal, and broaden inspection only when required behavior is missing, contradictory, or insufficient.

If two current items conflict, identify the exact items and resolve the conflict in their owning document. Provider contracts own their exported interface. Consumers cannot override that interface. A material product decision lacking a specified answer requires user clarification; independent coding continues. An internal implementation choice that preserves specified behavior can be made by the agent.

Before returning, make the current goal, its owning LLD items, and resulting code agree. Record unfinished behavior as remaining work. Do not make a working stub appear to be a completed user operation.

## Repository layout

Use `docs/` with exact capitalization: `docs/LLD` and `docs/implementation`.

Scope `00` is foundation. Allocate other two-digit scopes to named capabilities when their goals are defined. Scope numbers are permanent; delivery order may change. Record scope names in `docs/LLD/README.md`. Source module names describe capabilities rather than historical LLD numbers.

Goal `IMP-NN-KK` lives at `docs/implementation/NN/NN.KK.md`. `NN` is its owner scope and `KK` its stable goal number. A later revision edits the same goal file.

~~~text
soma/
  AGENTS.md
  README.md
  pyproject.toml
  soma_setup.bat
  soma_run.bat
  soma_run_console.bat
  soma_stop.bat
  docs/
    architecture.md
    LLD/
      README.md
      00/
        README.md
        backend.md
        frontend.md
        checks.md
        contracts/
        migrations/
          README.md
      01/
      02/
    implementation/
      README.md
      00/
        00.01.md
      01/
    decisions/
    reference/
  src/
    core/
      soma/
        foundation/
          audit/
          build/
          config/
          context/
          diagnostics/
          errors/
          filesystem/
          identity/
          persistence/
          query/
          security/
          testing/
          time/
          transactions/
          jobs/
          development/
        modules/
          tickets/
            domain/
            application/
            ports/
            adapters/
            transport/
          inventory/
          communications/
        db/
          migrations/
            manifest.json
            00/
              001_bootstrap.sql
        runtime/
          control.py
          health.py
          host.py
          lifecycle.py
          static_assets.py
          tray.py
          trust.py
          workers.py
        composition/
          capabilities.py
    main/
      package.json
      app/
        bootstrap/
        capabilities/
        routing/
      shared/
        api/
        build/
        collections/
        components/
        interactions/
        navigation/
        time/
      features/
        system/
        tickets/
          views/
          state/
          api/
      styles/
      assets/
        brand/
      tests/
      browser-tests/
  tests/
    core/
    integration/
  tools/
    source_launcher.py
~~~

The tree defines placement, not a requirement to create empty wrappers or folders. Add a file when it has real behavior. One feature may begin with a small number of files and split when responsibilities require it.

The root `pyproject.toml`, when introduced, packages the `soma` Python package from `src/core`. Frontend dependency/build configuration lives in `src/main/package.json`. Frontend unit and browser tests belong in `src/main/tests` and `src/main/browser-tests`; cross-plane integration tests belong in `tests/integration`.

Executable SQL exists only under `src/core/soma/db/migrations`. Foundation persistence provides database connections and the migration runner. Documentation under `docs/LLD/NN/migrations` explains and links to SQL; it never contains a second executable copy.

Local design references and scratch material may live under ignored `.tmp/`. Nothing under `.tmp/` may become an application dependency or source of truth. Accepted permanent assets move to owned repository paths such as `src/main/assets/brand/`.

## Source runtime controls

The repository-root `soma_setup.bat`, `soma_run.bat`, `soma_run_console.bat`, and `soma_stop.bat` are stable development/operator buttons. They remain thin adapters over `tools/source_launcher.py` and shared core runtime/security providers; BAT files never duplicate trust or lifecycle logic.

`soma_run` and `soma_run_console` start the same authoritative application composition. Detached and console modes differ only in operator presentation/logging and process attachment, not in domain/runtime behavior. Both expose the same system tray control surface when available.

Source launchers are development infrastructure. They may later inform installer shortcuts, but packaging/release mechanics do not own the authoritative runtime lifecycle. Host control always passes through the same verified local-instance protocol, and system tray actions never become alternate kill/business authority.

The source-development instance defaults beneath Windows LocalAppData at `SOMA/Development/instance-v1`. This intentionally separates disposable development data from a future packaged release instance.

## Foundation boundary

Scope 00 owns mechanisms required before domain capabilities can safely exist: configuration/paths, build identity, UTC and monotonic clocks, technical IDs/correlation, errors, safe filesystem/temp, protected persistence/migrations/snapshots, transactions/replay/audit, jobs, trusted runtime/control, browser-session/CSRF substrate, static serving, API/query mechanics, diagnostics, capability discovery, testing seams, and shared user-plane interactions.

Foundation never owns ticket, customer, Objective, Task, SLA, inventory, infrastructure, communication, import, or other business meaning. A generic mechanism may validate/transport an owner contract, but it may not infer owner lifecycle, eligibility, ranking, relationship, or audit semantics.

A later module registers only the minimum data needed by a foundation registry (for example a job contract, audit payload contract, capability descriptor, route, seed contributor, or query DTO). Registration does not transfer business ownership to Foundation.

## System plane: core

| Layer or role | Owns | Allowed dependency direction |
|---|---|---|
| Transport | External request shape, security-context validation, response/error mapping. | Calls application operations and declared request/session providers. |
| Application | Commands, queries, workflows, transaction boundaries, replay, revisions, job coordination. | Uses domain behavior, its ports, and shared foundation interfaces. |
| Domain | Entities, identities, policies, and valid business transitions. | Uses pure domain types/utilities. Imports no HTTP, SQL, UI, filesystem, or OS implementation. |
| Ports/contracts | Typed operations provided or required by a module. | Describe a boundary without importing its concrete provider. |
| Adapters | Persistence, source readers, exports, and native mechanisms. | Implement ports and use foundation infrastructure or external libraries. |
| Runtime | Process lifecycle, readiness, trusted local control, source-launch integration, native tray lifecycle, scheduling, and workers. | Runs application operations; owns no independent business mutation rules. |
| Composition | Construction and wiring of concrete providers. | Imports implementations required to assemble the application. |

Transport does not execute SQL or decide business transitions. The application operation owns the transaction; participating adapters use its context and do not commit independently. A query may use a dedicated read adapter without constructing entities.

A background worker invokes an application operation. Cross-module calls use an exported provider interface; consumers do not query another module's private tables. Cross-module orchestration belongs to one named application coordinator. Do not add reciprocal module imports; resolve a cycle through a provider interface and composition.

Every externally visible operation carries stable safe error semantics and an opaque correlation context. Correlation supports tracing only; it never grants identity, authorization, replay, transaction, or domain authority.

Wall-clock chronology and elapsed timing are separate mechanisms: UTC records facts; monotonic clocks govern durations/timeouts. Feature code does not call wall-clock/local-time APIs directly when an owned clock/provider exists.

Shared foundation provides mechanisms. Domain-specific customer, ticket, SLA, inventory, and communication policies belong to their modules. Foundation must not become a domain catch-all.

## User plane: main

| Layer | Owns |
|---|---|
| App shell | Routing, startup/authentication presentation, navigation, workspace and pane composition. |
| Feature views | Tables, forms, record inspectors, and actions. |
| Feature state | Selection, working copies, local validation, request identity, loading/error/conflict behavior, and API orchestration. |
| Shared presentation/API | Reusable interactions, semantic styles, time formatting, typed requests, and generated/validated API bindings. |

The system plane owns durable business rules and resulting facts. The user plane presents those facts and manages interaction state.

Mutation flow:

~~~text
feature view
  -> feature state
  -> API client
  -> transport
  -> application operation
  -> domain / ports
  -> adapters
  -> committed result
  -> frontend state / view
~~~

This is control flow; source imports still follow the layer rules above.

## Contract seam

Core and main must not independently invent the same transport contract. Runtime request/response schemas live in one authoritative contract source and are validated or used to generate bindings for both planes.

The shared seam also standardizes the safe error envelope, correlation identity, build/protocol bootstrap, capability registry, keyset-page/cursor mechanics, authenticated browser context, and current-run identity. Domain payloads remain owned by their scope.

A contract change updates its owner LLD item, provider implementation, generated/validated consumer binding, and affected goal in the same iteration.

## Documentation roles

Each scope has a README plus `backend.md`, `frontend.md`, and `checks.md` as needed. `contracts/` holds schemas used for runtime validation or type generation. `migrations/` documents current schema construction.

Scope `00` owns shared runtime, persistence, security mechanisms, time, interaction, API-contract, and tooling foundations.

`backend.md` specifies owned operations and behavior. `frontend.md` specifies presentation and interactions. `checks.md` lists observable scenarios for development testing. A feature with no work in one plane says `none` in the relevant goal; it does not create dummy code or a migration.

An actionable behavior item states the trigger/input, output or visible result, constraints, failure behavior, and side effects. Include units, timezone, defaults, null meaning, identity, and transaction ownership when they matter. Specify exact fields/enums where consumers need them. Link shared rules by ID instead of copying their text.

A goal file contains only:

- Metadata: ID, status, scope, relationships, affected paths, and `reset_db`.
- Outcome: one sentence describing the user/system result.
- Work: backend, frontend, and migration changes; use `none` where applicable.
- Run: relevant automated or live-use scenarios and actual results.
- Remaining: concrete unfinished behavior or blocker; use `none` when working.

Record what was actually run and its result. Note the commit when exercising a committed build, or `working tree` for uncommitted code. Additional prose is used only for a material decision or defect.

Goal statuses:

- `queued`: selected work has not started.
- `in_progress`: implementation or correction is underway.
- `working`: the stated outcome has been exercised successfully and required remaining work is none.
- `revisit`: a previously working outcome requires another iteration.
- `blocked`: a named dependency or required user decision prevents remaining work.

`working` makes no claim about whole-application completion or certification. Optional future enhancements become separate goals.

## README rule

Each README contains a general purpose in one or two sentences, at most 40 words, followed only by necessary navigation links. Status, steps, history, and detailed rules belong in adjacent documents.

Example for `00`:

> Provide the runtime, persistence, security, time, API-contract, and interaction foundations shared by all SOMA modules. Define shared contracts and dependency boundaries.

Use direct responsibility statements. Each paragraph must help locate work, decide behavior, implement it, or exercise it; remove other prose from active coding documents.

## Stable IDs and relationship format

Tags support discovery. Explicit relationships support impact analysis.

Use uppercase IDs matching `[A-Z][A-Z0-9_.-]*`. Document IDs, goal IDs, and section-item IDs share one globally unique namespace. Examples: `LLD-00-BACKEND`, `IMP-00-03`, `TIME.UTC`, `TIME.DISPLAY`, and `M00.001`.

Preserve an ID through wording edits and file moves. To replace a concept, keep its old ID as a retired entry and link the new item through `supersedes`. Renumbering scopes or reusing retired IDs is prohibited.

Metadata is strict JSON in one HTML comment before the title of a referenced LLD or goal Markdown file. UTF-8 BOM and leading blank lines are permitted. Examples inside fenced code blocks are ignored by the scanner.

~~~text
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
    }
  ],
  "tags": ["time", "user-plane"]
}
-->
~~~

Place the matching explicit anchor immediately before its section:

~~~html
<a id="time-display"></a>
~~~

A goal file uses the same metadata shape:

~~~text
<!-- soma-meta
{
  "version": 1,
  "id": "IMP-00-03",
  "scope": "00",
  "status": "queued",
  "implements": ["TIME.DISPLAY"],
  "depends_on": ["TIME.UTC"],
  "code_paths": ["src/main/shared/time/"],
  "reset_db": false,
  "tags": ["time", "user-plane"]
}
-->
~~~

These examples define the format; they do not declare that the referenced implementation exists.

Parser rules:

- The comment starts with the exact line `<!-- soma-meta` and ends with `-->` on its own line. Parse contents as JSON and reject duplicate object keys.
- `version` is integer `1`, not a boolean. `id` and `scope` are required strings. `scope` matches `[0-9]{2}` and agrees with the enclosing numbered directory; shared `docs/architecture.md` belongs to `00`.
- `items` is optional. Each entry requires `id` and `anchor`. Item scope and document tags are inherited. Relationships are not inherited; declare them on the node that uses them.
- Document nodes point to the file. Section nodes point to the declared anchor, which must occur exactly once.
- Relationship and `code_paths` fields are arrays of unique nonempty strings. Arrays may be empty. Each tag matches `[a-z][a-z0-9_-]*` and tags are unique.
- `status`, `reset_db`, `implements`, and `code_paths` are required for implementation goal documents. `status` is one of the five statuses above and `reset_db` is boolean. `status`/`reset_db` are allowed only on goal documents.
- `retired` is optional boolean, default `false`, on document/section nodes.
- Absent relationship fields mean empty arrays. Unknown metadata fields fail validation.
- README and AGENTS files need no metadata. Current LLD/goal files containing referenced behavior need metadata. Schema and manifest files reference behavior IDs without creating duplicate graph nodes.
- ID references resolve to nodes, never tags or path substrings.
- `code_paths` are case-correct repository-relative paths with forward slashes and no globs. A trailing slash matches that directory and descendants; otherwise it matches exactly one file.
- Future code paths may be listed before files exist. Report them as planned paths for non-working goals/design items. For working goals, every mapped path must exist.
- The generated index maps each ID to its current location; do not maintain a second manual registry.

Allowed document fields: `version`, `id`, `scope`, `items`, `tags`, `depends_on`, `implements`, `covers`, `relates_to`, `supersedes`, `code_paths`, `status`, `reset_db`, `retired`.

Allowed section fields: `id`, `anchor`, `depends_on`, `implements`, `covers`, `relates_to`, `supersedes`, `code_paths`, `retired`.

| Relationship | Direction and meaning |
|---|---|
| `depends_on` | Consumer -> provider item whose behavior/interface it requires. |
| `implements` | Goal/implementation mapping -> design item it delivers. |
| `covers` | Test or scenario item -> behavior item it exercises. |
| `relates_to` | Contextual association; does not trigger impact propagation. |
| `supersedes` | Replacement -> retained retired item. |

Tags are browsing labels and never establish a dependency. Paths map affected code to documented items; multiple owners are reported explicitly.

## Impact analysis

Generate the index from current source metadata. The first checker should:

1. Validate IDs, references, metadata types, and anchors.
2. Compare tracked files with the task's declared Git baseline, default `HEAD`, including staged/unstaged edits. Enumerate untracked files separately. For an unborn branch, use an empty baseline. Generated/ignored build outputs are excluded.
3. Attribute edits between explicit item anchors to those items. Edits to document-level text, metadata, or deletion mark all document nodes/items as changed.
4. Resolve code changes through `code_paths`; moves consider both old and new paths.
5. Traverse incoming `depends_on`, `implements`, and `covers` edges with a visited set. Use the union of baseline/current edges so removing a reference does not hide impact.
6. Report direct impacts, indirect impacts, and the path explaining each. Include unmapped changed code as a mapping gap. Sort results by stable ID.

For deleted/retired items, retain the baseline graph while locating affected consumers. `supersedes` points to the replacement through its reverse relation; then traverse the replacement's consumers. Unresolved references must be repaired or redirected before the iteration is finished.

The agent reviews affected items and updates those whose behavior changed. A declared dependency does not itself prove a consumer is broken. Compatible consumers require no rewritten document. Put deferred required work in a goal with a named dependency and current state.

The checker is planned foundation tooling. Until implemented, use ID search to locate incoming references and affected paths, follow the same relationships, and record mapping gaps. Add tooling only for repeated coding needs.

## Development migrations

Use owner IDs such as `M03.001` and owner paths such as `src/core/soma/db/migrations/03/001_import_staging.sql`. One manifest defines current application order, dependencies, and SQL hashes. Execution follows that manifest, not directory sorting.

DDL ownership follows schema ownership. If one change touches schema owned by multiple scopes, prefer owner-local migrations linked by manifest dependencies instead of one cross-owner migration.

During development:

- Edit current schema/migrations when an iteration requires it.
- Update the manifest and related LLD items together.
- Set `reset_db` to `true` on the active goal when the existing development database must be recreated.
- Rebuild the designated development database and exercise the changed workflow.
- Keep one executable SQL copy.
- Do not add dummy migrations to mirror LLD numbers.

No upgrade-compatibility work or historical migration preservation is required for the disposable development database. A future release baseline is a later whole-application task.

## Coding loop

Select outcome -> read linked items -> edit code -> run focused checks/live scenario -> resolve relevant impact -> update current goal/design -> continue.

Keep documents sufficient to execute that loop. Reuse existing Alpha/Beta code where it fits, revise it when this design requires, and preserve useful regression cases. Formal certification remains a final whole-application activity.
