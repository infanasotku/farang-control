# Engine Spec Polling

Spec polling lets the engine instance read the desired state from the control-plane.

It provides:

- access to the latest desired config
- monotonic `generation` for change detection
- stable `config_hash` for config comparison

# API

```
GET /engines/{engine_id}/spec
```

Response:

```json
{
  "engine_id": "00000000-0000-0000-0000-000000000001",
  "config": {
    "mode": "proxy"
  },
  "enabled": true,
  "generation": 12,
  "config_hash": "sha256..."
}
```

If the spec does not exist, the endpoint returns:

```http
404 Not Found
```

# Data Used

- `engine_specs`: desired engine state stored by the control-plane

The endpoint is read-only and does not modify runtime ownership or runtime state.

# Polling Flow

1. The engine calls `GET /engines/{engine_id}/spec`.
2. The control-plane returns the current desired spec.
3. The engine compares the returned `generation` with the generation it already applied.
4. If the generation is newer, the engine reloads config and applies the new desired state.
5. The engine later reports its applied generation through heartbeat.

# Meaning of Fields

- `config`: desired runtime configuration
- `enabled`: whether the engine should be enabled
- `generation`: monotonic desired-state version
- `config_hash`: hash of canonical JSON config, useful for debugging and consistency checks

# Guarantees

- The engine always reads the latest stored desired spec.
- `generation` is the primary change detector for polling.
- `config_hash` is derived from `config` and represents the same desired state.
- Polling is safe to repeat at any interval.

# Example

```text
engine has applied generation 11

GET /engines/{id}/spec -> generation 12

engine detects a newer desired state
engine applies the new config
engine later reports observed_generation = 12 in heartbeat
```
