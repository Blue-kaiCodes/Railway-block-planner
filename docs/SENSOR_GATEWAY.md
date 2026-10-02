# Trackside Sensor & IoT Gateway Specification

The **Sensor & IoT Gateway** (`backend/sensor_gateway.py`) provides an authenticated, high-throughput edge telemetry pipeline for railway monitoring instruments along the corridor.

---

## 1. Authentication & Security

All telemetry ingestion requests require token authentication:
- **Header**: `X-Sensor-Token: <token>` (or `Authorization: Bearer <token>`).
- **Configuration**: Set via `SENSOR_INGESTION_TOKEN` environment variable.
- **Unauthorized Request**: Returns HTTP `401 Unauthorized`:
  ```json
  {
    "detail": "Invalid or missing X-Sensor-Token header."
  }
  ```

---

## 2. Sensor Types & Operating Thresholds

### 2.1 Axle Counters (`AXLE_COUNTER`)
- **Purpose**: Fail-safe section occupancy determination and train integrity verification.
- **Operating Logic**:
  - `ENTRY` / `direction: "IN"`: Increments `axle_count_balance` by incoming axles; sets block state to `OCCUPIED`.
  - `EXIT` / `direction: "OUT"`: Decrements `axle_count_balance`.
  - When balance reaches zero, marks block `CLEAR`.
  - **Negative Balance Anomaly**: If exit count exceeds entry count, emits a `CRITICAL` severity `TRACK_ANOMALY` event (`Axle Counter Mismatch: Possible axle miscount or train split!`) and flags the sensor status as `ERROR`.

### 2.2 Continuous Rail Temperature Sensors (`RAIL_TEMPERATURE`)
- **Purpose**: Prevention of rail buckling during intense summer heat and rail fractures during winter cold.
- **Threshold Rules**:
  | Temperature | Severity | Action Imposed |
  | :--- | :--- | :--- |
  | $< 55^\circ\text{C}$ | Normal | Normal corridor speeds. |
  | $\ge 55^\circ\text{C}$ | `WARNING` | Rail temperature alert emitted; engineering foot patrol mobilized. |
  | $\ge 65^\circ\text{C}$ | `CRITICAL` | Block status set to `RESTRICTED`; mandatory **30 km/h** thermal caution order imposed. |
  | $\le 50^\circ\text{C}$ | Normal | Caution order automatically lifted; normal speeds restored (hysteresis). |

### 2.3 Bridge Pier Water Level Sensors (`BRIDGE_WATER_LEVEL`)
- **Purpose**: Real-time river flood monitoring on major bridge substructures.
- **Threshold Rules**:
  | Water Level | Severity | Action Imposed |
  | :--- | :--- | :--- |
  | $< 3.5\text{ m}$ | Normal | Normal bridge transit. |
  | $\ge 3.5\text{ m}$ | `WARNING` | Warning Level exceeded; speed restricted to **20 km/h**. |
  | $\ge 4.5\text{ m}$ | `EMERGENCY` | **Danger Level exceeded**; block status set to `RESTRICTED`; **0 km/h speed limit (TRAFFIC SUSPENDED)**. |

### 2.4 Track Geometry & Vibration Sensors (`TRACK_GEOMETRY`, `VIBRATION`)
- **Purpose**: Detection of rail surface corrugation, track twist, and foundation subsidence using trackside tri-axial accelerometers.
- **Threshold Rules**:
  - Dynamic vertical/lateral acceleration $\ge 0.8\text{ g}$: Emits a `CRITICAL` `TRACK_GEOMETRY_DEFECT` event and triggers engineering inspection.

---

## 3. Ingestion API Schema & Example Payloads

**Endpoint**: `POST /api/v1/events/sensor`  
**Headers**:
```http
Content-Type: application/json
X-Sensor-Token: test_sensor_gateway_token_2026
```

### Example A: Axle Counter Train Entry
```json
{
  "sensor_id": "AXL-DDU-01",
  "sensor_type": "AXLE_COUNTER",
  "section_id": "SEC-01",
  "event_type": "SECTION_ENTRY",
  "axle_count": 88,
  "timestamp": "2026-10-01T15:30:00Z",
  "payload": {
    "direction": "IN",
    "train_id": "12301",
    "block_id": "BLK-01",
    "speed_kmph": 110.0
  }
}
```

### Example B: Rail Temperature Buckling Warning
```json
{
  "sensor_id": "TEMP-HWH-02",
  "sensor_type": "RAIL_TEMPERATURE",
  "section_id": "SEC-02",
  "event_type": "RAIL_TEMPERATURE_ALERT",
  "temperature_celsius": 67.5,
  "timestamp": "2026-10-01T15:31:00Z",
  "payload": {
    "block_id": "BLK-03"
  }
}
```

### Success Response (`200 OK`)
```json
{
  "status": "SUCCESS",
  "sensor_id": "TEMP-HWH-02",
  "events_count": 1,
  "block_id": "BLK-03",
  "block_occupancy": "CLEAR",
  "restriction_status": "RESTRICTED",
  "timestamp": "2026-10-01T15:31:00.123456+00:00"
}
```
