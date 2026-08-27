# Planned Engine Replacement

A replacement permit allows an operator to deliberately restart an edge and register its new instance immediately,
without waiting for the current owner to cross the five-minute dead threshold.

The permit does not change the current owner's liveness. The old instance remains valid until the replacement registers,
at which point the normal epoch fencing mechanism makes the old instance stale.

# Configuration

Set a dedicated operator API key in the control service:

```text
AUTH__OPERATOR_API_KEY=SECRET
```

If this setting is absent, management endpoints return `503 Service Unavailable`. The operator key must not be shared
with edge instances.

# Issue a Permit

```http
POST /api/v1/management/engines/{engine_id}/replacement-permit
X-Operator-Key: SECRET
```

Successful response (`201 Created`):

```json
{
  "engine_id": "5ef71e0d-bf65-45e2-9637-4ebd3e92db71",
  "current_instance_id": "ea85a007-e3e9-40ae-8406-c4934c7c3a90",
  "permit": "ONE_TIME_SECRET",
  "expires_at": "2026-08-27T09:10:00Z"
}
```

The permit expires after ten minutes. Issuing another permit replaces the previous one. Control stores only a SHA-256
digest of the returned value and never logs the secret.

# Register the Replacement

Start the replacement edge with a fresh `instance_id` and include the permit in its registration request:

```http
POST /api/v1/engines/{engine_id}/register-instance?instance_id={new_instance_id}
X-API-Key: EDGE_SECRET
X-Replacement-Permit: ONE_TIME_SECRET
```

Registration validates and consumes the permit in the same transaction that creates the new instance and increments the
epoch. Only one concurrent registration can consume it.

Missing, invalid, or expired permits do not reveal permit details; registration returns the existing `409 Conflict`
response while the current owner is alive. Historical instance IDs remain deprecated and return `410 Gone`.

# Revoke a Permit

If the restart is cancelled, revoke the outstanding permit:

```http
DELETE /api/v1/management/engines/{engine_id}/replacement-permit
X-Operator-Key: SECRET
```

Revocation is idempotent and returns `204 No Content`.
