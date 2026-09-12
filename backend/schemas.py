from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any

class MaintenanceTask(BaseModel):
    id: str = Field(..., min_length=2, description="Unique Task Identifier, e.g. TSK-001")
    asset_id: str = Field(..., description="Target railway asset, e.g. AST-101")
    section: str = Field(..., description="Corridor section, e.g. A12-B14")
    department: str = Field(..., description="Department: Engineering, Signal & Telecom, Traction / OHE")
    task_type: str = Field(..., min_length=3, description="Operational task description")
    duration_mins: int = Field(..., gt=0, le=720, description="Task duration in minutes (max 12h)")
    priority: str = Field(..., description="Priority: CRITICAL, HIGH, MEDIUM, LOW")
    deadline_hour: float = Field(..., ge=0.0, le=24.0, description="Operational deadline hour (0.0 to 24.0)")
    status: str = Field(default="PENDING", description="PENDING, SCHEDULED, IN_PROGRESS, COMPLETED")
    is_emergency: bool = Field(default=False, description="Whether task is an emergency defect")
    required_crew: str = Field(default="Standard Department Gang", description="Designated maintenance gang")
    required_equipment: str = Field(default="Standard Tooling", description="Heavy machinery or inspection kit")
    risk_score: float = Field(default=50.0, ge=0.0, le=100.0)
    description: str = Field(default="")

    @field_validator("priority")
    def validate_priority(cls, v):
        v_upper = v.upper()
        if v_upper not in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            raise ValueError("Priority must be one of: CRITICAL, HIGH, MEDIUM, LOW")
        return v_upper

    @field_validator("department")
    def validate_department(cls, v):
        allowed = ["Engineering", "Signal & Telecom", "Traction / OHE"]
        if v not in allowed:
            raise ValueError(f"Department must be one of: {', '.join(allowed)}")
        return v

class MaintenanceTaskUpdate(BaseModel):
    asset_id: Optional[str] = None
    section: Optional[str] = None
    department: Optional[str] = None
    task_type: Optional[str] = None
    duration_mins: Optional[int] = None
    priority: Optional[str] = None
    deadline_hour: Optional[float] = None
    status: Optional[str] = None
    is_emergency: Optional[bool] = None
    required_crew: Optional[str] = None
    required_equipment: Optional[str] = None
    description: Optional[str] = None

class TrainMovement(BaseModel):
    train_id: str = Field(..., min_length=2, description="Train number or ID, e.g. 12301")
    train_name: str = Field(..., description="Name of the service")
    origin: str = Field(default="Howrah Jn (HWH)", description="Origin station")
    destination: str = Field(default="New Delhi (NDLS)", description="Destination station")
    train_type: str = Field(default="Express", description="Express, Superfast, Freight, Passenger")
    section: str = Field(..., description="Section identifier, e.g. A12-B14")
    arrival_hour: float = Field(..., ge=0.0, le=24.0)
    departure_hour: float = Field(..., ge=0.0, le=24.0)
    service_priority: int = Field(default=1, ge=1, le=3, description="1=Express, 2=Passenger, 3=Freight")
    direction: str = Field(default="DOWN", description="UP or DOWN")
    is_protected: bool = Field(default=True, description="Strict timetable protection (no overlap allowed)")
    pass_frequency: str = Field(default="Daily")

    @field_validator("departure_hour")
    def validate_times(cls, v, info):
        arr = info.data.get("arrival_hour")
        if arr is not None and v <= arr:
            raise ValueError("Departure hour must be strictly greater than arrival hour.")
        return v

class TrainMovementUpdate(BaseModel):
    train_name: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    train_type: Optional[str] = None
    arrival_hour: Optional[float] = None
    departure_hour: Optional[float] = None
    service_priority: Optional[int] = None
    direction: Optional[str] = None
    is_protected: Optional[bool] = None

class BlockWindow(BaseModel):
    id: str = Field(..., min_length=2, description="Block window ID, e.g. BLK-101")
    section: str = Field(..., description="Section identifier, e.g. A12-B14")
    start_hour: float = Field(..., ge=0.0, le=24.0)
    end_hour: float = Field(..., ge=0.0, le=24.0)
    permitted_departments: List[str] = Field(default_factory=list)
    max_duration_mins: int = Field(default=180, gt=0)
    status: str = Field(default="AVAILABLE", description="AVAILABLE, OCCUPIED, CLOSED")

    @field_validator("end_hour")
    def validate_block_times(cls, v, info):
        st = info.data.get("start_hour")
        if st is not None and v <= st:
            raise ValueError("Block window end hour must be strictly greater than start hour.")
        return v

class BlockWindowUpdate(BaseModel):
    section: Optional[str] = None
    start_hour: Optional[float] = None
    end_hour: Optional[float] = None
    permitted_departments: Optional[List[str]] = None
    max_duration_mins: Optional[int] = None
    status: Optional[str] = None

class EmergencyDefectRequest(BaseModel):
    defect_id: Optional[str] = None
    section: str = Field(default="A12-B14")
    asset_id: str = Field(default="AST-102")
    defect_type: str = Field(default="EMERGENCY Rail Fracture Repair")
    severity: str = Field(default="CRITICAL")
    deadline_hour: float = Field(default=6.0, ge=0.0, le=24.0)
    duration_mins: int = Field(default=90, gt=0, le=360)
    description: str = Field(default="Immediate ultrasonic rail fracture risk identified.")

class ScheduleItem(BaseModel):
    task_id: str
    task_name: str
    department: str
    section: str
    block_id: str
    start_hour: float
    end_hour: float
    duration_mins: int
    assigned_resources: List[str]
    priority: str
    explanation: str
    train_conflicts_avoided: int = 0

class BaselineComparison(BaseModel):
    manual_conflicts: int
    optimized_conflicts: int
    manual_total_delay_mins: int
    optimized_total_delay_mins: int
    manual_block_utilization_pct: float
    optimized_block_utilization_pct: float
    manual_critical_completed: int
    optimized_critical_completed: int
    delay_reduction_pct: float

class PlanDiff(BaseModel):
    new_emergency_task: str
    affected_tasks: List[str]
    unchanged_tasks: List[str]
    total_moved: int

class OptimizationResult(BaseModel):
    status: str
    total_tasks_scheduled: int
    schedule: List[ScheduleItem]
    unassigned_tasks: List[str]
    baseline_comparison: BaselineComparison
    summary_explanation: str
    plan_id: str
    diff: Optional[PlanDiff] = None
