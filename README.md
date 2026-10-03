# SOMA

**Service Operations Management Application**

SOMA is a local-first operational workspace for managing service work, technical infrastructure, inventory, objectives, tasks, communications, and the evidence connecting them.

## Architecture

SOMA is divided into two primary planes:

- `src/core` — the system plane: runtime, persistence, security, domain logic, application operations, adapters, and transport.
- `src/main` — the user plane: application shell, feature views and state, shared interactions, presentation, and API bindings.

Behavior is specified under `docs/LLD`. Active implementation outcomes and their exercised state are recorded under `docs/implementation`.

## Development

SOMA is developed iteratively. The development database is disposable, schema and implementation may be revised as live use exposes better designs, and focused checks accompany each runnable increment. Formal whole-application certification is deferred until the required application functionality is complete and exercised.

Alpha and Beta are reference implementations and design sources. Their useful behavior is reused by ownership and capability; their historical structure is not authoritative for this repository.
