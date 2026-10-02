import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class EventSource(str, Enum):
    RTIS = 'RTIS'
    NTES = 'NTES'
    OGD_PORTAL = 'OGD_PORTAL'
    OPEN_DATA_GOV = 'OGD_PORTAL'
    AXLE_COUNTER = 'AXLE_COUNTER'
    TRACK_SENSOR = 'TRACK_SENSOR'
    IoT_GATEWAY = 'IoT_GATEWAY'
    OPERATOR = 'OPERATOR'
    SIMULATION = 'SIMULATION'

class EventType(str, Enum):
    TRAIN_POSITION_UPDATE = 'TRAIN_POSITION_UPDATE'
    TRAIN_SPEED_UPDATE = 'TRAIN_SPEED_UPDATE'
    TRAIN_DELAY_UPDATE = 'TRAIN_DELAY_UPDATE'
    TRAIN_STALLED = 'TRAIN_STALLED'
    UNEXPECTED_STOP = 'UNEXPECTED_STOP'
    SECTION_ENTRY = 'SECTION_ENTRY'
    SECTION_EXIT = 'SECTION_EXIT'
    SECTION_OCCUPIED = 'SECTION_OCCUPIED'
    SECTION_CLEAR = 'SECTION_CLEAR'
    AXLE_COUNT_UPDATE = 'AXLE_COUNT_UPDATE'
    TRACK_ANOMALY = 'TRACK_ANOMALY'
    RAIL_TEMPERATURE_ALERT = 'RAIL_TEMPERATURE_ALERT'
    BRIDGE_WATER_ALERT = 'BRIDGE_WATER_ALERT'
    TRACK_GEOMETRY_DEFECT = 'TRACK_GEOMETRY_DEFECT'
    SENSOR_HEARTBEAT = 'SENSOR_HEARTBEAT'
    SENSOR_FAULT = 'SENSOR_FAULT'
    SENSOR_OFFLINE = 'SENSOR_OFFLINE'
    SENSOR_RECOVERED = 'SENSOR_RECOVERED'
    SPEED_RESTRICTION_APPLIED = 'SPEED_RESTRICTION_APPLIED'
    SPEED_RESTRICTION_REMOVED = 'SPEED_RESTRICTION_REMOVED'
    PLAN_CONFLICT_DETECTED = 'PLAN_CONFLICT_DETECTED'
    REPLAN_TRIGGERED = 'REPLAN_TRIGGERED'
    CANDIDATE_PLAN_GENERATED = 'CANDIDATE_PLAN_GENERATED'
    PLAN_APPROVED = 'PLAN_APPROVED'
    PLAN_REJECTED = 'PLAN_REJECTED'
    TRAIN_GPS_UPDATE = 'TRAIN_POSITION_UPDATE'
    SCHEDULE_DRIFT = 'TRAIN_DELAY_UPDATE'
    TRAIN_STATION_ARRIVAL = 'SECTION_ENTRY'
    TRAIN_STATION_DEPARTURE = 'SECTION_EXIT'
    AXLE_COUNTER_ENTRY = 'SECTION_ENTRY'
    AXLE_COUNTER_EXIT = 'SECTION_EXIT'
    BLOCK_OCCUPIED = 'SECTION_OCCUPIED'
    BLOCK_CLEARED = 'SECTION_CLEAR'
    SPEED_RESTRICTION_IMPOSED = 'SPEED_RESTRICTION_APPLIED'
    SPEED_RESTRICTION_LIFTED = 'SPEED_RESTRICTION_REMOVED'

class EventSeverity(str, Enum):
    INFO = 'INFO'
    WARNING = 'WARNING'
    CRITICAL = 'CRITICAL'
    EMERGENCY = 'EMERGENCY'

class SensorType(str, Enum):
    AXLE_COUNTER = 'AXLE_COUNTER'
    TRACK_OCCUPANCY = 'TRACK_OCCUPANCY'
    TRAIN_DETECTION = 'TRAIN_DETECTION'
    RAIL_TEMPERATURE = 'RAIL_TEMPERATURE'
    TRACK_GEOMETRY = 'TRACK_GEOMETRY'
    BRIDGE_WATER_LEVEL = 'BRIDGE_WATER_LEVEL'
    VIBRATION = 'VIBRATION'
    EQUIPMENT_HEALTH = 'EQUIPMENT_HEALTH'
    OTHER = 'OTHER'

class SensorStatus(str, Enum):
    ONLINE = 'ONLINE'
    WARNING = 'WARNING'
    ALERT = 'ALERT'
    OFFLINE = 'OFFLINE'
    FAULT = 'FAULT'

class DataQuality(str, Enum):
    LIVE = 'LIVE'
    STALE = 'STALE'
    INVALID = 'INVALID'
    SIMULATED = 'SIMULATED'
    SIMULATION = 'SIMULATION'

class ProviderState(str, Enum):
    CONNECTED = 'CONNECTED'
    DISCONNECTED = 'DISCONNECTED'
    DEGRADED = 'DEGRADED'
    AUTHENTICATION_REQUIRED = 'AUTHENTICATION_REQUIRED'
    UNAVAILABLE = 'UNAVAILABLE'
    ERROR = 'ERROR'
    SIMULATION = 'SIMULATION'

class PlanApprovalStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    SUPERSEDED = 'SUPERSEDED'

class NormalizedTrainState(BaseModel):
    train_id: str = Field(..., description='Unique train identifier, e.g. 12301')
    train_name: Optional[str] = Field(default='', description='Name of the service')
    source: EventSource = Field(..., description='Ingestion data source')
    latitude: Optional[float] = Field(default=None, description='GPS Latitude')
    longitude: Optional[float] = Field(default=None, description='GPS Longitude')
    speed_kmph: float = Field(default=0.0, ge=0.0, le=250.0, description='Current speed in km/h')
    direction: str = Field(default='DOWN', description='UP or DOWN')
    current_section: str = Field(..., description='Corridor section ID')
    next_section: Optional[str] = Field(default=None)
    status: str = Field(default='RUNNING', description='RUNNING, STOPPED, DELAYED, STALLED')
    delay_seconds: int = Field(default=0, description='Delay relative to timetable in seconds')
    timestamp: str = Field(..., description='ISO 8601 timestamp')
    received_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_event_id: Optional[str] = Field(default=None)
    data_quality: DataQuality = Field(default=DataQuality.LIVE)

class SensorEntity(BaseModel):
    sensor_id: str = Field(..., min_length=2)
    sensor_type: SensorType = Field(...)
    section_id: str = Field(...)
    status: SensorStatus = Field(default=SensorStatus.ONLINE)
    last_seen: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: EventSource = Field(default=EventSource.TRACK_SENSOR)
    telemetry: Dict[str, Any] = Field(default_factory=dict)
    battery_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    data_quality: DataQuality = Field(default=DataQuality.LIVE)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SensorIngestPayload(BaseModel):
    event_id: str = Field(default_factory=lambda: f'EVT-{uuid.uuid4().hex[:12].upper()}')
    sensor_id: str = Field(..., min_length=2)
    sensor_type: SensorType = Field(...)
    section_id: str = Field(..., min_length=2)
    event_type: EventType = Field(...)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: EventSource = Field(default=EventSource.TRACK_SENSOR)
    severity: EventSeverity = Field(default=EventSeverity.INFO)
    axle_count: Optional[int] = Field(default=None, ge=0)
    temperature_celsius: Optional[float] = Field(default=None)
    water_level_meters: Optional[float] = Field(default=None)
    vibration_g: Optional[float] = Field(default=None)
    details: Optional[str] = Field(default='')
    payload: Dict[str, Any] = Field(default_factory=dict)

class RailwayEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f'EVT-{uuid.uuid4().hex[:12].upper()}')
    event_type: EventType = Field(...)
    source: EventSource = Field(...)
    entity_id: str = Field(default='')
    train_id: Optional[str] = Field(default=None)
    block_id: Optional[str] = Field(default=None)
    sensor_id: Optional[str] = Field(default=None)
    section_id: Optional[str] = Field(default=None)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    severity: EventSeverity = Field(default=EventSeverity.INFO)
    title: str = Field(default='')
    description: str = Field(default='')
    payload: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    acknowledged: bool = Field(default=False)
    processed: bool = Field(default=False)
    processed_at: Optional[str] = Field(default=None)

class BlockState(BaseModel):
    block_id: str = Field(...)
    section_id: str = Field(...)
    occupancy_state: str = Field(default='CLEAR')
    restriction_status: str = Field(default='NORMAL')
    active_speed_limit_kmph: Optional[float] = Field(default=None)
    occupied_by: Optional[str] = Field(default=None)
    axle_count_balance: int = Field(default=0)
    last_entry_time: Optional[str] = Field(default=None)
    last_exit_time: Optional[str] = Field(default=None)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CorridorConflict(BaseModel):
    conflict_id: str = Field(default_factory=lambda: f'CONF-{uuid.uuid4().hex[:8].upper()}')
    section_id: str = Field(...)
    conflict_type: str = Field(...)
    severity: EventSeverity = Field(default=EventSeverity.CRITICAL)
    affected_train_ids: List[str] = Field(default_factory=list)
    affected_task_ids: List[str] = Field(default_factory=list)
    affected_block_ids: List[str] = Field(default_factory=list)
    affected_trains: List[str] = Field(default_factory=list)
    affected_tasks: List[str] = Field(default_factory=list)
    affected_blocks: List[str] = Field(default_factory=list)
    description: str = Field(...)
    detected_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    requires_reoptimization: bool = Field(default=True)
    resolved: bool = Field(default=False)

class PlanDiffItem(BaseModel):
    task_id: str
    task_name: str
    section: str = ''
    section_id: Optional[str] = None
    action: str = 'SHIFTED'
    old_block_id: Optional[str] = None
    new_block_id: Optional[str] = None
    old_start_hour: Optional[float] = None
    new_start_hour: Optional[float] = None
    old_end_hour: Optional[float] = None
    new_end_hour: Optional[float] = None
    time_shift_mins: int = 0
    shift_minutes: int = 0
    reason: str = ''
    impact_reason: str = ''

class PlanVersion(BaseModel):
    plan_id: str = Field(...)
    version_number: int = Field(default=1)
    status: PlanApprovalStatus = Field(default=PlanApprovalStatus.PENDING_APPROVAL)
    trigger_event_id: Optional[str] = Field(default=None)
    trigger_reason: str = Field(default='Routine Corridor Optimization')
    solver_status: str = Field(default='OPTIMAL')
    solve_time_seconds: float = Field(default=0.0)
    objective_value: float = Field(default=0.0)
    tasks_scheduled: int = Field(default=0)
    tasks_unscheduled: int = Field(default=0)
    scheduled_items: List[Dict[str, Any]] = Field(default_factory=list)
    unassigned_tasks: List[str] = Field(default_factory=list)
    diff: Optional[List[PlanDiffItem]] = Field(default_factory=list)
    summary: str = Field(default='')
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewed_at: Optional[str] = Field(default=None)
    reviewed_by: Optional[str] = Field(default=None)
    rejection_reason: Optional[str] = Field(default=None)

class OperatorDecisionRequest(BaseModel):
    operator_id: str = Field(default='CORRIDOR_CONTROLLER_01')
    operator_name: str = Field(default='Chief Traffic Controller')
    decision: str = Field(default='APPROVE')
    comments: Optional[str] = Field(default='')
    notes: Optional[str] = Field(default='')
    rejection_reason: Optional[str] = Field(default=None)
