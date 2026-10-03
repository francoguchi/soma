# Beta foundation migration map

This file records provenance only. Current behavior is owned by `docs/LLD/00/`.

| Beta source | New scope-00 authority |
|---|---|
| LLD-01 LocalHostLifecycle | `RUNTIME.INSTANCE`, `RUNTIME.LIFECYCLE`, `RUNTIME.HEALTH`, `RUNTIME.SHUTDOWN` |
| LLD-01 ConnectionFactoryAndUnitOfWork | `PERSISTENCE.CONNECTION`, `PERSISTENCE.READ_SNAPSHOT`, `TX.UOW`, `PERSISTENCE.SNAPSHOT` |
| LLD-01 migration runner/status/schema verification | `MIGRATION.MANIFEST`, `MIGRATION.STATUS`, `PERSISTENCE.SCHEMA_VERIFY`, `DEV.DB_RESET`, `M00.001` |
| LLD-01 StrictVersionedJson | `SERIALIZATION.STRICT_JSON`, `CONTRACT.SOURCE` |
| LLD-01 exact command receipts/results | `COMMAND.REPLAY`, `M00.002` |
| LLD-01 AuditWriter | `AUDIT.APPEND_ONLY`, `M00.003` |
| LLD-01 DurableJobCoordinator/recovery | `JOBS.COORDINATOR`, `JOBS.EXECUTION`, `M00.004` |
| LLD-01 stable error catalogue | `ERROR.CONTRACT`, `TRACE.CORRELATION` |
| LLD-01 technical IDs/time | `IDENTITY.UUID`, `TIME.UTC`, `TIME.MONOTONIC` |
| LLD-12 live key/DPAPI/SQLCipher handoff | `SECURITY.LIVE_DATA_KEY`, `PERSISTENCE.CONNECTION` |
| LLD-12 RuntimeRegistryV2/TrustedLocalInstance | `RUNTIME.TRUSTED_CONTROL` |
| Beta launcher implementation `fbe3821...` | `DEV.SOURCE_LAUNCHERS`, `DIAGNOSTICS.OPERATOR_LOGS` |
| LLD-12 Shell_NotifyIconW design | `UI.SYSTEM_TRAY` |
| LLD-12 PasswordAuthenticationV1 | `AUTH.LOCAL_ADMIN`, `UI.AUTH_GATE`, `M00.006` |
| LLD-12 BrowserSessionAndCsrfV1 | `SECURITY.BROWSER_SESSION` |
| LLD-12 DeliberateActionProofV1 | `SECURITY.DELIBERATE_PROOF` |
| LLD-12 diagnostic sanitization | `DIAGNOSTICS.SAFE`, `UI.DIAGNOSTICS_STATE` |
| LLD-10 technology/static SPA | `PLATFORM.BASELINE`, `STATIC.ASSETS`, `UI.BOOTSTRAP` |
| LLD-10 semantic tokens/typography | `UI.BRAND`, `UI.TOKENS`, `UI.ACCESSIBILITY` |
| LLD-10 selection/open | `UI.SELECTION`, `UI.ROUTING` |
| LLD-10 scroll ownership | `UI.SCROLL`, `UI.DIALOG_FOCUS` |
| LLD-10 bounded collection/autocomplete rules | `QUERY.PAGE`, `UI.COLLECTIONS`, `UI.AUTOCOMPLETE` |
| LLD-10 responsive workbench | `UI.SHELL`, `UI.RESPONSIVE` |
| LLD-10 working copies | `WORKING_COPY.STORE`, `UI.WORKING_COPY`, `M00.005` |
| LLD-10 confirmation tiers | `UI.CONFIRMATION` |
| LLD-10 Safe Undo | `UI.SAFE_UNDO` |
| LLD-10 error/loading/conflict presentation | `UI.ERROR_STATE` |

New scope-00 mechanisms not copied as Beta packet ownership include `CONFIG.RUNTIME`, `BUILD.IDENTITY`, `FS.SAFE`, `FS.TEMP`, `DEV.SEED`, `CAPABILITY.REGISTRY`, and `TEST.SEAMS`. They formalize repeated needs exposed during Alpha/Beta development.

Excluded from scope 00 even when Beta LLD-12 grouped them nearby: Local Administrator profile/display-name/contact settings, password change/reset/recovery product UX beyond minimal setup/login/logout, portable-backup envelope/recovery UX, release installer/signing, and domain authorization. Their later owner scopes consume the foundation mechanisms instead.
