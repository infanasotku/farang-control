# Engine Instance Registration

Registration makes an engine instance the current runtime owner in the control-plane.

It provides:

- idempotent registration by `instance_id`
- a single active instance per engine
- monotonic `epoch` assignment

# API

```
POST /engines/{engine_id}/register-instance?instance_id=UUID
```

Response:

```json
{
  "epoch": 3
}
```

# Data Used

- `engines`: locked to serialize concurrent registrations
- `engine_instances`: stores registration history
- `engine_runtime_state`: stores the current runtime owner

# Algorithm

Registration runs in a single transaction.

1. Lock the `engine` row with `FOR UPDATE`.
2. Load the current runtime snapshot for the engine.
3. Load `engine_instances[instance_id]`.
4. If the instance already exists:
   - if it is the current owner, return the existing `epoch`
   - otherwise raise `InstanceDeprecatedError`
5. If a runtime snapshot exists and the current owner is not `DEAD`, raise `CurrentInstanceAliveError`.
6. Compute `epoch = 1` for the first registration, otherwise `current_epoch + 1`.
7. Insert a new row into `engine_instances`.
8. Upsert `engine_runtime_state` with:
   - `current_instance_id = instance_id`
   - `current_epoch = epoch`
   - `reported_phase = STARTING`
   - `observed_generation = 0`
   - `last_seen_at = now`
   - `last_seq_no = 0`

# Guarantees

- The same instance can safely retry registration.
- Only one runtime owner is accepted at a time.
- `epoch` is monotonic per engine.
- Concurrent registrations are serialized by engine row locking.

# Example

```text
state = NULL
instance A registers -> epoch 1

instance A retries -> epoch 1

instance B registers after A is dead -> epoch 2

instance A retries again -> InstanceDeprecatedError
```
