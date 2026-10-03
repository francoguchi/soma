# Foundation contracts

Hold JSON Schema Draft 2020-12 runtime/API contracts owned by scope 00. Behavioral authority remains in backend/frontend LLD items; generated bindings are outputs.

Rules: `*.schema.json`, closed objects, explicit bounds/nullability/units, local references only, no remote refs. Validate/generate through `tools/contracts.py`; TypeScript output goes to `src/main/shared/api/generated/`.
