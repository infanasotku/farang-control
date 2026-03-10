# Control plane spec

## Phase 1 — Control-plane: Core Domain Models

### 1.1 Engine

Logical proxy engine (not a running process).

Fields:

- `id` (UUID)
- `name`

---

### 1.2 EngineSpec (desired state)

Fields:

- `engine_id`
- `config`
- `enabled`
- `generation`
- `config_hash` (derived property from `config`, SHA-256 over canonical JSON)

Invariants:

- `generation` is monotonic
- `config_hash` matches `config`
- any config change → increment `generation`

---

### 1.3 EngineRuntimeState (observed runtime snapshot)

State reported by data‑plane.

Fields:

- `engine_id`
- `reported_phase`
- `observed_generation`
- `last_seen_at`

Epoch/sequence fields are added later.

---

### 1.4 Derived Status

Computed control‑plane interpretation.

Derived fields:

- `liveness`: `alive | stale | dead`
- `sync`: `in_sync | outdated`

Current rule set:

- `liveness` by `last_seen_at` age (`alive` <= 30s, `stale` > 30s, `dead` > 5m)
- `sync` by `runtime.observed_generation == spec.generation`

---
