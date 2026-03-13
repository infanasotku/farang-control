# Engine Instance Registration

This document describes the **engine instance registration protocol** used by the control‑plane.

The protocol provides:

- idempotent registration
- a single active instance per engine
- monotonic epoch assignment
- protection against race conditions

---

# Overview

Each running engine process must register itself in the control‑plane.

Registration assigns the process an **epoch** that identifies the current runtime generation of the engine.

Registration also updates the **runtime snapshot** maintained by the control‑plane.

---

# Key Concepts

## Engine

Logical proxy engine managed by the control‑plane.

```
engines
-------
id
...
```

The `engine` row is used for **row‑level locking** to serialize registrations.

---

## Engine Instance (history)

Every successful registration creates an instance record.

```
engine_instances
----------------
id (UUID)          -- instance_id
engine_id
epoch
created_at
```

Properties:

- `instance_id` is globally unique (UUID)
- `(engine_id, epoch)` is unique
- used for **idempotency**

---

## Engine Runtime State (snapshot)

Current runtime state of the engine.

```
engine_runtime_state
--------------------
engine_id
current_instance_id
current_epoch
reported_phase
observed_generation
last_seen_at
last_seq_no
```

This table represents the **current runtime owner** of the engine.

---

# Registration API

```
POST /engines/{engine_id}/register-instance
```

## Request

```query
?instance_id=UUID
```

## Response

```json
{
  "epoch": 3
}
```

---

# Registration Algorithm

Registration runs inside a **single database transaction**.

## Step 1 — Lock the engine

```
SELECT * FROM engines
WHERE id = :engine_id
FOR UPDATE
```

This serializes registrations for the same engine and prevents races when the runtime state does not yet exist.

---

## Step 2 — Load runtime snapshot

```
state = engine_runtime_state
```

`state` may be `NULL` if this is the **first registration**.

---

## Step 3 — Check instance history

```
instance = engine_instances.get(instance_id)
```

### Case A — Instance already registered

If the instance exists:

1. If it is the current instance

   ```
   instance_id == state.current_instance_id
   ```

   Return the existing epoch.

   This handles **idempotent retries**.

2. If it is not the current instance

   The instance is **retired**.

   Return:

   ```
   InstanceDeprecatedError
   ```

---

### Case B — Instance not found

Proceed with normal registration.

---

## Step 4 — Check active instance

If a runtime state exists and the current instance is alive:

```
state.get_liveness() == ALIVE
```

The liveness status is derived from the runtime snapshot
(e.g. using heartbeat timeouts).

Reject registration:

```
CurrentInstanceAliveError
```

This guarantees **a single active instance per engine**.

---

## Step 5 — Compute new epoch

```
new_epoch = 1 if state is None else state.current_epoch + 1
```

Epoch values are **monotonic per engine**.

---

## Step 6 — Insert instance history

```
INSERT INTO engine_instances
(id, engine_id, epoch)
VALUES (...)
```

This records the registration in history.

---

## Step 7 — Update runtime snapshot

```
engine_runtime_state.upsert(
    engine_id=engine_id,
    current_instance_id=instance_id,
    current_epoch=new_epoch,
    reported_phase=STARTING,
    observed_generation=0,
    last_seen_at=now,
    last_seq_no=0
)
```

This makes the instance the **current active runtime owner**.

---

# Runtime State Initialization

When a new instance becomes active, runtime fields are initialized as follows:

| Field               | Value           | Reason                           |
| ------------------- | --------------- | -------------------------------- |
| current_instance_id | new instance id | new owner                        |
| current_epoch       | new epoch       | ownership generation             |
| reported_phase      | `STARTING`      | instance just registered         |
| observed_generation | `0`             | no config applied yet            |
| last_seq_no         | `0`             | no heartbeat received            |
| last_seen_at        | `now`           | instance contacted control plane |

---

# Idempotency Guarantees

## Retry of the same instance

If the same `instance_id` calls registration again:

```
return existing epoch
```

No state changes occur.

---

## Retry after network failure

Because `instance_id` is globally unique, registration can safely be retried.

---

# Race Condition Handling

Registration is safe because:

1. the `engine` row is locked (`FOR UPDATE`)
2. registrations for the same engine are serialized by locking the engine row
3. epoch calculation occurs inside the transaction

This prevents races such as multiple instances registering simultaneously.

---

# Example Timeline

## First registration

```
state = NULL
instance A registers

epoch = 1
current_instance = A
```

---

## Retry of the same instance

```
instance A registers again

return epoch 1
```

---

## New instance after failure

```
instance A died
instance B registers

epoch = 2
current_instance = B
```

---

## Old instance retry

```
instance A registers again

InstanceDeprecatedError
```

---

# Guarantees

The system guarantees:

- exactly one active runtime owner
- monotonic epoch sequence
- idempotent registration
- safe concurrent registration attempts

---

# Summary

Registration relies on:

- engine row locking
- instance history
- runtime snapshot
- monotonic epoch
