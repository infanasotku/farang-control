# Engine Heartbeat

Heartbeat refreshes liveness and updates the current runtime snapshot.

It provides:

- liveness tracking
- ownership validation
- monotonic `seq_no` processing
- idempotent retries

# API

```
POST /engines/{engine_id}/heartbeat
```

Request:

```json
{
  "instance_id": "00000000-0000-0000-0000-000000000001",
  "epoch": 3,
  "seq_no": 12,
  "phase": "starting",
  "generation": 7
}
```

Response:

```http
200 OK
```

The endpoint returns no body.

# Data Used

- `engine_runtime_state`: current runtime snapshot, loaded `FOR UPDATE`
- `engine_instances`: instance history used to validate the sender

Raw heartbeat events are not persisted.

# Algorithm

Heartbeat runs in a single transaction.

1. Check that the engine exists, otherwise raise `EngineNotFoundError`.
2. Load the current runtime snapshot for update.
3. Load `engine_instances[instance_id]`.
4. If either the snapshot or instance is missing, raise `InstanceNotRegisteredError`.
5. If `instance_id != current_instance_id` or `epoch != current_epoch`, ignore the heartbeat.
6. If `seq_no <= last_seq_no`, ignore the heartbeat.
7. Otherwise update:
   - `reported_phase = phase`
   - `observed_generation = generation`
   - `last_seen_at = now`
   - `last_seq_no = seq_no`

# Guarantees

- Only the current runtime owner can update the snapshot.
- Duplicate, late, and stale-owner heartbeats are harmless.
- `last_seq_no` is monotonic.
- Liveness is refreshed only by accepted heartbeats.

# Example

```text
current_instance = A
current_epoch = 3
last_seq_no = 0

heartbeat(A, epoch=3, seq_no=1) -> accepted
heartbeat(A, epoch=3, seq_no=1) -> ignored
heartbeat(A, epoch=3, seq_no=2) -> accepted

heartbeat(old_instance, old_epoch, seq_no=9) -> ignored
```
