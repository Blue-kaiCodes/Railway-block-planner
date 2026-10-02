# Railway Block Planner — REST API V1 Reference

The Railway Block Planner provides OpenAPI 3.1 compliant endpoints served via FastAPI. Interactive Swagger UI documentation is available at `http://127.0.0.1:8000/docs`.

---

## 1. External Providers & System Health

### `GET /api/v1/providers/health`
Returns aggregated real-time health across all connected railway data providers.

**Response (`200 OK`)**:
```json
{
  "status": "HEALTHY",
  "primary_source": "RTIS",
  "data_quality": "LIVE",
  "is_live_data": true,
  "disclaimer": null,
  "providers": {
    "rtis": {
      "name": "CRIS/ISRO RTIS",
      "source": "RTIS",
      "state": "CONNECTED",
      "poll_interval_sec": 15.0,
      "last_heartbeat": "2026-10-01T15:30:00Z",
      "circuit_breaker_open": false
    },
    "ntes": {
      "name": "Indian Railways NTES",
      "source": "NTES",
      "state": "CONNECTED",
      "poll_interval_sec": 30.0,
      "last_heartbeat": "2026-10-01T15:30:00Z",
      "circuit_breaker_open": false
    }
  },
  "timestamp": "2026-10-01T15:30:05Z"
}
```

---

## 2. Trackside Sensor & Telemetry Endpoints

### `POST /api/v1/events/sensor`
Ingests a trackside IoT telemetry event. Requires `X-Sensor-Token` header.

**Headers**:
- `X-Sensor-Token`: Bearer authorization token.

**Request Body**:
```json
{
  "sensor_id": "TEMP-001",
  "sensor_type": "RAIL_TEMPERATURE",
  "section_id": "SEC-01",
  "event_type": "RAIL_TEMPERATURE_ALERT",
  "temperature_celsius": 68.0,
  "timestamp": "2026-10-01T15:30:00Z",
  "payload": {
    "block_id": "BLK-01"
  }
}
```

**Response (`200 OK`)**:
```json
{
  "status": "SUCCESS",
  "sensor_id": "TEMP-001",
  "events_count": 1,
  "block_id": "BLK-01",
  "block_occupancy": "CLEAR",
  "restriction_status": "RESTRICTED",
  "timestamp": "2026-10-01T15:30:00.123456+00:00"
}
```

### `GET /api/v1/sensors`
Lists all registered corridor sensors and their current status (`ONLINE`, `WARNING`, `ALERT`, `FAULT`).

### `GET /api/v1/sensors/{sensor_id}/telemetry`
Retrieves time-series telemetry history for a specific sensor.
- **Query Parameter**: `limit` (default: 50).

---

## 3. Real-Time Fleet & Corridor Tracking

### `GET /api/v1/trains/live`
Returns normalized locomotive positions, speeds, directions, timetable delay, and data quality tags.

**Response (`200 OK`)**:
```json
[
  {
    "train_id": "12301",
    "train_name": "Howrah Rajdhani Express",
    "source": "RTIS",
    "latitude": 22.585,
    "longitude": 88.351,
    "speed_kmph": 110.0,
    "direction": "UP",
    "current_section": "SEC-01",
    "next_section": "SEC-02",
    "status": "RUNNING",
    "delay_seconds": 120,
    "timestamp": "2026-10-01T15:30:00Z",
    "data_quality": "LIVE"
  }
]
```

### `GET /api/v1/trains/{train_id}`
Returns live state for a single train. Returns `404 Not Found` if not tracked.

### `GET /api/v1/blocks/state`
Returns the operational status of all corridor track blocks (`CLEAR`, `OCCUPIED`, `RESTRICTED`, axle count balance, active speed limits).

### `GET /api/v1/blocks/{block_id}`
Returns state for a specific block.

---

## 4. Corridor Conflict Detection

### `GET /api/v1/conflicts`
Returns active corridor conflicts identified by the conflict engine (`HEADWAY_VIOLATION`, `SPEED_RESTRICTION_EXCEEDED`, `UNEXPLAINED_BLOCK_OCCUPANCY`, `SCHEDULE_DRIFT_CASCADE`).

### `POST /api/v1/conflicts/{conflict_id}/resolve`
Manually acknowledges and resolves a corridor conflict.

---

## 5. Candidate Plan Generation & Operator Approval

### `GET /api/v1/plans/active`
Returns the currently approved, active operational maintenance schedule.

### `GET /api/v1/plans/candidate`
Returns the pending candidate plan awaiting Chief Traffic Controller sign-off (or `null` if none pending).

### `GET /api/v1/plans/history`
Returns all historical plan versions with approval audits.

### `POST /api/v1/plans/reoptimize`
Triggers Google OR-Tools CP-SAT re-optimization based on live fleet delays and track restrictions. Creates a new candidate plan in `PENDING_APPROVAL` status.

- **Query Parameters**:
  - `triggered_by` (default: `'OPERATOR'`)
  - `reason` (default: `'Manual re-optimization request'`)

### `POST /api/v1/plans/{plan_id}/approve`
Chief Controller approval gate. Activates candidate plan, supersedes prior plan, and auto-resolves active corridor conflicts.

**Request Body**:
```json
{
  "decision": "APPROVE",
  "operator_name": "Chief Traffic Controller S. Mukherjee",
  "comments": "Approved after reviewing timetable shift diffs."
}
```

### `POST /api/v1/plans/{plan_id}/reject`
Rejects a candidate plan. Leaves active operational plan intact.

**Request Body**:
```json
{
  "decision": "REJECT",
  "operator_name": "Chief Traffic Controller S. Mukherjee",
  "rejection_reason": "Excessive delay to freight corridor; reschedule to night window."
}
```

---

## 6. Operational Events & Simulation Control

### `GET /api/v1/events`
Returns immutable audit log of railway events.
- **Query Parameters**: `limit` (int, default 50), `event_type` (str), `severity` (str).

### `POST /api/v1/simulation/inject-disturbance`
Injects an intentional test disturbance into the simulation kinematics engine.

**Request Body**:
```json
{
  "disturbance_type": "TRAIN_DELAY",
  "target_id": "12301",
  "value": 600
}
```
