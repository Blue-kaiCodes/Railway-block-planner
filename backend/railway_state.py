import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from threading import RLock
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from backend.canonical_schemas import (
    NormalizedTrainState, BlockState, SensorEntity, RailwayEvent,
    CorridorConflict, PlanVersion, PlanApprovalStatus, EventSource,
    EventType, EventSeverity, SensorType, SensorStatus, DataQuality
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "railway_state.db")

class RailwayStateStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = RLock()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._lock, self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS train_states (
                    train_id TEXT PRIMARY KEY,
                    train_name TEXT,
                    source TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    speed_kmph REAL DEFAULT 0,
                    direction TEXT DEFAULT 'DOWN',
                    current_section TEXT NOT NULL,
                    next_section TEXT,
                    status TEXT DEFAULT 'RUNNING',
                    delay_seconds INTEGER DEFAULT 0,
                    timestamp TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    source_event_id TEXT,
                    data_quality TEXT DEFAULT 'LIVE'
                );
                CREATE INDEX IF NOT EXISTS idx_trains_sec ON train_states(current_section);
                CREATE INDEX IF NOT EXISTS idx_trains_time ON train_states(timestamp);

                CREATE TABLE IF NOT EXISTS block_states (
                    block_id TEXT PRIMARY KEY,
                    section_id TEXT NOT NULL,
                    occupancy_state TEXT DEFAULT 'CLEAR',
                    restriction_status TEXT DEFAULT 'NORMAL',
                    active_speed_limit_kmph REAL,
                    occupied_by TEXT,
                    axle_count_balance INTEGER DEFAULT 0,
                    last_entry_time TEXT,
                    last_exit_time TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_blocks_sec ON block_states(section_id);

                CREATE TABLE IF NOT EXISTS sensors (
                    sensor_id TEXT PRIMARY KEY,
                    sensor_type TEXT NOT NULL,
                    section_id TEXT NOT NULL,
                    status TEXT DEFAULT 'ONLINE',
                    last_seen TEXT NOT NULL,
                    source TEXT DEFAULT 'TRACK_SENSOR',
                    telemetry_json TEXT DEFAULT '{}',
                    battery_pct REAL,
                    data_quality TEXT DEFAULT 'LIVE',
                    metadata_json TEXT DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_sensors_sec ON sensors(section_id);
                CREATE INDEX IF NOT EXISTS idx_sensors_type ON sensors(sensor_type);

                CREATE TABLE IF NOT EXISTS telemetry_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    raw_payload TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry_history(sensor_id, timestamp);

                CREATE TABLE IF NOT EXISTS events_log (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    section_id TEXT,
                    timestamp TEXT NOT NULL,
                    severity TEXT DEFAULT 'INFO',
                    title TEXT,
                    description TEXT,
                    payload_json TEXT DEFAULT '{}',
                    acknowledged INTEGER DEFAULT 0,
                    processed INTEGER DEFAULT 0,
                    processed_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_events_time ON events_log(timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_type ON events_log(event_type);
                CREATE INDEX IF NOT EXISTS idx_events_sev ON events_log(severity);

                CREATE TABLE IF NOT EXISTS plan_versions (
                    plan_id TEXT PRIMARY KEY,
                    version_number INTEGER NOT NULL,
                    status TEXT DEFAULT 'PENDING_APPROVAL',
                    trigger_event_id TEXT,
                    trigger_reason TEXT,
                    solver_status TEXT DEFAULT 'OPTIMAL',
                    solve_time_seconds REAL DEFAULT 0,
                    objective_value REAL DEFAULT 0,
                    tasks_scheduled INTEGER DEFAULT 0,
                    tasks_unscheduled INTEGER DEFAULT 0,
                    scheduled_items_json TEXT DEFAULT '[]',
                    unassigned_tasks_json TEXT DEFAULT '[]',
                    diff_json TEXT DEFAULT '[]',
                    summary TEXT,
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    reviewed_by TEXT,
                    rejection_reason TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_plans_time ON plan_versions(created_at);
                CREATE INDEX IF NOT EXISTS idx_plans_status ON plan_versions(status);

                CREATE TABLE IF NOT EXISTS conflicts (
                    conflict_id TEXT PRIMARY KEY,
                    section_id TEXT NOT NULL,
                    conflict_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'CRITICAL',
                    affected_trains_json TEXT DEFAULT '[]',
                    affected_tasks_json TEXT DEFAULT '[]',
                    affected_blocks_json TEXT DEFAULT '[]',
                    description TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    requires_reoptimization INTEGER DEFAULT 1,
                    resolved INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_conflicts_res ON conflicts(resolved);
            """)

    # --- Train State Methods ---

    def upsert_train_state(self, state: NormalizedTrainState):
        with self._lock, self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO train_states (
                    train_id, train_name, source, latitude, longitude, speed_kmph,
                    direction, current_section, next_section, status, delay_seconds,
                    timestamp, received_at, source_event_id, data_quality
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                state.train_id, state.train_name, state.source.value, state.latitude,
                state.longitude, state.speed_kmph, state.direction, state.current_section,
                state.next_section, state.status, state.delay_seconds, state.timestamp,
                state.received_at, state.source_event_id, state.data_quality.value
            ))

    def get_train_state(self, train_id: str) -> Optional[NormalizedTrainState]:
        with self._lock, self._get_connection() as conn:
            row = conn.execute("SELECT * FROM train_states WHERE train_id = ?", (train_id,)).fetchone()
            if not row:
                return None
            return NormalizedTrainState(
                train_id=row["train_id"],
                train_name=row["train_name"],
                source=EventSource(row["source"]),
                latitude=row["latitude"],
                longitude=row["longitude"],
                speed_kmph=row["speed_kmph"],
                direction=row["direction"],
                current_section=row["current_section"],
                next_section=row["next_section"],
                status=row["status"],
                delay_seconds=row["delay_seconds"],
                timestamp=row["timestamp"],
                received_at=row["received_at"],
                source_event_id=row["source_event_id"],
                data_quality=DataQuality(row["data_quality"])
            )

    def get_all_train_states(self) -> List[NormalizedTrainState]:
        with self._lock, self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM train_states ORDER BY train_id").fetchall()
            return [
                NormalizedTrainState(
                    train_id=r["train_id"],
                    train_name=r["train_name"],
                    source=EventSource(r["source"]),
                    latitude=r["latitude"],
                    longitude=r["longitude"],
                    speed_kmph=r["speed_kmph"],
                    direction=r["direction"],
                    current_section=r["current_section"],
                    next_section=r["next_section"],
                    status=r["status"],
                    delay_seconds=r["delay_seconds"],
                    timestamp=r["timestamp"],
                    received_at=r["received_at"],
                    source_event_id=r["source_event_id"],
                    data_quality=DataQuality(r["data_quality"])
                ) for r in rows
            ]

    # --- Block State Methods ---

    def upsert_block_state(self, block: BlockState):
        with self._lock, self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO block_states (
                    block_id, section_id, occupancy_state, restriction_status,
                    active_speed_limit_kmph, occupied_by, axle_count_balance,
                    last_entry_time, last_exit_time, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                block.block_id, block.section_id, block.occupancy_state, block.restriction_status,
                block.active_speed_limit_kmph, block.occupied_by, block.axle_count_balance,
                block.last_entry_time, block.last_exit_time, block.updated_at
            ))

    def get_block_state(self, block_id: str) -> Optional[BlockState]:
        with self._lock, self._get_connection() as conn:
            row = conn.execute("SELECT * FROM block_states WHERE block_id = ?", (block_id,)).fetchone()
            if not row:
                return None
            return BlockState(
                block_id=row["block_id"],
                section_id=row["section_id"],
                occupancy_state=row["occupancy_state"],
                restriction_status=row["restriction_status"],
                active_speed_limit_kmph=row["active_speed_limit_kmph"],
                occupied_by=row["occupied_by"],
                axle_count_balance=row["axle_count_balance"],
                last_entry_time=row["last_entry_time"],
                last_exit_time=row["last_exit_time"],
                updated_at=row["updated_at"]
            )

    def get_all_block_states(self) -> List[BlockState]:
        with self._lock, self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM block_states ORDER BY block_id").fetchall()
            return [
                BlockState(
                    block_id=r["block_id"],
                    section_id=r["section_id"],
                    occupancy_state=r["occupancy_state"],
                    restriction_status=r["restriction_status"],
                    active_speed_limit_kmph=r["active_speed_limit_kmph"],
                    occupied_by=r["occupied_by"],
                    axle_count_balance=r["axle_count_balance"],
                    last_entry_time=r["last_entry_time"],
                    last_exit_time=r["last_exit_time"],
                    updated_at=r["updated_at"]
                ) for r in rows
            ]

    # --- Sensor Methods ---

    def upsert_sensor(self, sensor: SensorEntity):
        with self._lock, self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sensors (
                    sensor_id, sensor_type, section_id, status, last_seen,
                    source, telemetry_json, battery_pct, data_quality, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sensor.sensor_id, sensor.sensor_type.value, sensor.section_id,
                sensor.status.value, sensor.last_seen, sensor.source.value,
                json.dumps(sensor.telemetry), sensor.battery_pct,
                sensor.data_quality.value, json.dumps(sensor.metadata)
            ))

    def get_sensor(self, sensor_id: str) -> Optional[SensorEntity]:
        with self._lock, self._get_connection() as conn:
            row = conn.execute("SELECT * FROM sensors WHERE sensor_id = ?", (sensor_id,)).fetchone()
            if not row:
                return None
            return SensorEntity(
                sensor_id=row["sensor_id"],
                sensor_type=SensorType(row["sensor_type"]),
                section_id=row["section_id"],
                status=SensorStatus(row["status"]),
                last_seen=row["last_seen"],
                source=EventSource(row["source"]),
                telemetry=json.loads(row["telemetry_json"] or "{}"),
                battery_pct=row["battery_pct"],
                data_quality=DataQuality(row["data_quality"]),
                metadata=json.loads(row["metadata_json"] or "{}")
            )

    def get_all_sensors(self) -> List[SensorEntity]:
        with self._lock, self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM sensors ORDER BY sensor_id").fetchall()
            return [
                SensorEntity(
                    sensor_id=r["sensor_id"],
                    sensor_type=SensorType(r["sensor_type"]),
                    section_id=r["section_id"],
                    status=SensorStatus(r["status"]),
                    last_seen=r["last_seen"],
                    source=EventSource(r["source"]),
                    telemetry=json.loads(r["telemetry_json"] or "{}"),
                    battery_pct=r["battery_pct"],
                    data_quality=DataQuality(r["data_quality"]),
                    metadata=json.loads(r["metadata_json"] or "{}")
                ) for r in rows
            ]

    def record_telemetry(self, sensor_id: str, timestamp: str, metric_name: str, metric_value: float, raw_payload: Dict[str, Any]):
        with self._lock, self._get_connection() as conn:
            conn.execute("""
                INSERT INTO telemetry_history (sensor_id, timestamp, metric_name, metric_value, raw_payload)
                VALUES (?, ?, ?, ?, ?)
            """, (sensor_id, timestamp, metric_name, metric_value, json.dumps(raw_payload)))

    # --- Event Methods ---

    def record_event(self, event: RailwayEvent) -> RailwayEvent:
        with self._lock, self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO events_log (
                    event_id, event_type, source, entity_id, section_id,
                    timestamp, severity, title, description, payload_json,
                    acknowledged, processed, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id, event.event_type.value, event.source.value,
                event.entity_id, event.section_id, event.timestamp,
                event.severity.value, event.title, event.description,
                json.dumps(event.payload), 1 if event.acknowledged else 0,
                1 if event.processed else 0, event.processed_at
            ))
            return event

    def get_recent_events(self, limit: int = 50, event_type: Optional[str] = None, severity: Optional[str] = None) -> List[RailwayEvent]:
        query = "SELECT * FROM events_log WHERE 1=1"
        params = []
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._lock, self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                RailwayEvent(
                    event_id=r["event_id"],
                    event_type=EventType(r["event_type"]),
                    source=EventSource(r["source"]),
                    entity_id=r["entity_id"],
                    section_id=r["section_id"],
                    timestamp=r["timestamp"],
                    severity=EventSeverity(r["severity"]),
                    title=r["title"] or "",
                    description=r["description"] or "",
                    payload=json.loads(r["payload_json"] or "{}"),
                    acknowledged=bool(r["acknowledged"]),
                    processed=bool(r["processed"]),
                    processed_at=r["processed_at"]
                ) for r in rows
            ]

    # --- Conflict Methods ---

    def record_conflict(self, conflict: CorridorConflict):
        with self._lock, self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO conflicts (
                    conflict_id, section_id, conflict_type, severity,
                    affected_trains_json, affected_tasks_json, affected_blocks_json,
                    description, detected_at, requires_reoptimization, resolved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conflict.conflict_id, conflict.section_id, conflict.conflict_type,
                conflict.severity.value, json.dumps(conflict.affected_train_ids),
                json.dumps(conflict.affected_task_ids), json.dumps(conflict.affected_block_ids),
                conflict.description, conflict.detected_at,
                1 if conflict.requires_reoptimization else 0,
                1 if conflict.resolved else 0
            ))

    def get_active_conflicts(self) -> List[CorridorConflict]:
        with self._lock, self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM conflicts WHERE resolved = 0 ORDER BY detected_at DESC").fetchall()
            return [
                CorridorConflict(
                    conflict_id=r["conflict_id"],
                    section_id=r["section_id"],
                    conflict_type=r["conflict_type"],
                    severity=EventSeverity(r["severity"]),
                    affected_train_ids=json.loads(r["affected_trains_json"] or "[]"),
                    affected_task_ids=json.loads(r["affected_tasks_json"] or "[]"),
                    affected_block_ids=json.loads(r["affected_blocks_json"] or "[]"),
                    description=r["description"],
                    detected_at=r["detected_at"],
                    requires_reoptimization=bool(r["requires_reoptimization"]),
                    resolved=bool(r["resolved"])
                ) for r in rows
            ]

    def resolve_conflicts_for_section(self, section_id: str):
        with self._lock, self._get_connection() as conn:
            conn.execute("UPDATE conflicts SET resolved = 1 WHERE section_id = ? AND resolved = 0", (section_id,))

    def get_unresolved_conflicts(self) -> List[CorridorConflict]:
        return self.get_active_conflicts()

    def resolve_conflict(self, conflict_id: str):
        with self._lock, self._get_connection() as conn:
            conn.execute("UPDATE conflicts SET resolved = 1 WHERE conflict_id = ?", (conflict_id,))

    # --- Plan Versioning Methods ---

    def save_plan_version(self, plan: PlanVersion):
        with self._lock, self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO plan_versions (
                    plan_id, version_number, status, trigger_event_id, trigger_reason,
                    solver_status, solve_time_seconds, objective_value, tasks_scheduled,
                    tasks_unscheduled, scheduled_items_json, unassigned_tasks_json,
                    diff_json, summary, created_at, reviewed_at, reviewed_by, rejection_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan.plan_id, plan.version_number, plan.status.value, plan.trigger_event_id,
                plan.trigger_reason, plan.solver_status, plan.solve_time_seconds,
                plan.objective_value, plan.tasks_scheduled, plan.tasks_unscheduled,
                json.dumps(plan.scheduled_items), json.dumps(plan.unassigned_tasks),
                json.dumps([d.model_dump() for d in (plan.diff or [])]),
                plan.summary, plan.created_at, plan.reviewed_at, plan.reviewed_by, plan.rejection_reason
            ))

    def get_plan_version(self, plan_id: str) -> Optional[PlanVersion]:
        with self._lock, self._get_connection() as conn:
            row = conn.execute("SELECT * FROM plan_versions WHERE plan_id = ?", (plan_id,)).fetchone()
            if not row:
                return None
            diff_raw = json.loads(row["diff_json"] or "[]")
            return PlanVersion(
                plan_id=row["plan_id"],
                version_number=row["version_number"],
                status=PlanApprovalStatus(row["status"]),
                trigger_event_id=row["trigger_event_id"],
                trigger_reason=row["trigger_reason"] or "",
                solver_status=row["solver_status"] or "OPTIMAL",
                solve_time_seconds=row["solve_time_seconds"] or 0.0,
                objective_value=row["objective_value"] or 0.0,
                tasks_scheduled=row["tasks_scheduled"] or 0,
                tasks_unscheduled=row["tasks_unscheduled"] or 0,
                scheduled_items=json.loads(row["scheduled_items_json"] or "[]"),
                unassigned_tasks=json.loads(row["unassigned_tasks_json"] or "[]"),
                diff=diff_raw,
                summary=row["summary"] or "",
                created_at=row["created_at"],
                reviewed_at=row["reviewed_at"],
                reviewed_by=row["reviewed_by"],
                rejection_reason=row["rejection_reason"]
            )

    def get_active_plan(self) -> Optional[PlanVersion]:
        with self._lock, self._get_connection() as conn:
            row = conn.execute("""
                SELECT plan_id FROM plan_versions 
                WHERE status = 'ACTIVE' OR status = 'APPROVED'
                ORDER BY version_number DESC LIMIT 1
            """).fetchone()
            if not row:
                return None
            return self.get_plan_version(row["plan_id"])

    def get_pending_candidate_plan(self) -> Optional[PlanVersion]:
        with self._lock, self._get_connection() as conn:
            row = conn.execute("""
                SELECT plan_id FROM plan_versions 
                WHERE status = 'PENDING_APPROVAL' 
                ORDER BY version_number DESC LIMIT 1
            """).fetchone()
            if not row:
                return None
            return self.get_plan_version(row["plan_id"])

    def get_all_plan_versions(self) -> List[PlanVersion]:
        with self._lock, self._get_connection() as conn:
            rows = conn.execute("SELECT plan_id FROM plan_versions ORDER BY version_number DESC").fetchall()
            return [self.get_plan_version(r["plan_id"]) for r in rows if r]

    # --- Retention & Maintenance ---

    def prune_stale_telemetry(self, retention_hours: int = 24):
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=retention_hours)).isoformat()
        with self._lock, self._get_connection() as conn:
            conn.execute("DELETE FROM telemetry_history WHERE timestamp < ?", (cutoff,))

state_store = RailwayStateStore()

def get_state_store() -> RailwayStateStore:
    return state_store

