import csv
import io
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import db
from backend.schemas import (
    MaintenanceTask, MaintenanceTaskUpdate,
    TrainMovement, TrainMovementUpdate,
    BlockWindow, BlockWindowUpdate,
    EmergencyDefectRequest
)
from backend.optimizer import run_optimization
from backend.baseline_solver import calculate_baseline_comparison
from backend.explainability import generate_task_explanation, generate_plan_summary, generate_unassigned_explanation
from backend.station_data import (
    search_stations, get_station_by_code, get_all_states,
    get_districts_by_state, get_stations_by_district, get_geographical_tree
)
from backend.train_provider import train_provider

app = FastAPI(
    title="Railway Maintenance Block Planning & Optimization System (PS 26027)",
    description="Enterprise Decision-Support Platform for Indian Railways Corridor Operations",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/dataset")
def get_full_dataset() -> Dict[str, Any]:
    return db.get_all()

@app.post("/api/scenario/load-demo")
def load_demo_scenario() -> Dict[str, Any]:
    dataset = db.load_demo_scenario()
    return {
        "status": "SUCCESS",
        "message": "Standard demonstration scenario loaded.",
        "data_source": dataset.get("data_source", "DEMO_SCENARIO"),
        "dataset": dataset
    }

@app.post("/api/scenario/new-empty")
def load_empty_scenario() -> Dict[str, Any]:
    dataset = db.load_empty_scenario()
    return {
        "status": "SUCCESS",
        "message": "New Empty Scenario initialized.",
        "data_source": dataset.get("data_source", "EMPTY_SCENARIO"),
        "dataset": dataset
    }

@app.get("/api/scenario")
def get_scenario() -> Dict[str, Any]:
    data = db.get_all()
    return {
        "scenario_name": data.get("scenario_name", "Demo Scenario"),
        "data_source": data.get("data_source", "DEMO_SCENARIO"),
        "data_source_label": data.get("data_source_label", "Synthetic Demo Dataset"),
        "last_optimized_at": data.get("last_optimized_at"),
        "last_solver_status": data.get("last_solver_status", "NOT RUN"),
        "latest_summary": data.get("latest_summary", "")
    }

@app.get("/api/dashboard/stats")
def get_dashboard_stats() -> Dict[str, Any]:
    data = db.get_all()
    tasks = data.get("tasks", [])
    trains = data.get("trains", [])
    blocks = data.get("block_windows", [])
    current_schedule = data.get("current_schedule", [])
    baseline = data.get("baseline_comparison")
    history = data.get("plan_history", [])

    crit_tasks = [t for t in tasks if t.get("priority") == "CRITICAL"]
    pending_tasks = [t for t in tasks if t.get("status") in ["PENDING", "UNASSIGNED"]]
    
    total_window_capacity_mins = sum(b.get("max_duration_mins", int((b["end_hour"] - b["start_hour"]) * 60)) for b in blocks)
    opt_used_mins = sum(item.get("duration_mins", 0) for item in current_schedule)
    utilization_pct = round((opt_used_mins / max(1, total_window_capacity_mins)) * 100.0, 1) if blocks and current_schedule else 0.0

    delay_saved_pct = baseline.get("delay_reduction_pct", 0.0) if baseline else 0.0
    conflicts_count = baseline.get("optimized_conflicts", 0) if baseline else 0
    solver_status = data.get("last_solver_status", "NOT RUN")

    return {
        "total_tasks": len(tasks),
        "pending_tasks": len(pending_tasks),
        "critical_defects": len(crit_tasks),
        "scheduled_blocks": len(current_schedule),
        "active_trains": len(trains),
        "available_blocks": len(blocks),
        "block_utilization_pct": utilization_pct,
        "delay_reduction_pct": delay_saved_pct,
        "conflicts_count": conflicts_count,
        "optimization_status": solver_status,
        "latest_plan_id": history[0]["plan_id"] if history else "NONE",
        "last_optimized_at": data.get("last_optimized_at"),
        "data_source": data.get("data_source", "DEMO_SCENARIO"),
        "data_source_label": data.get("data_source_label", "Synthetic Demo Dataset"),
        "scenario_name": data.get("scenario_name", "Demo Scenario"),
        "can_revert": db.can_revert(),
        "latest_diff": data.get("latest_diff")
    }

@app.get("/api/tasks")
def list_tasks(
    search: Optional[str] = None,
    department: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    tasks = db.get_tasks()
    if search:
        s_lower = search.lower()
        tasks = [t for t in tasks if s_lower in t["id"].lower() or s_lower in t["task_type"].lower() or s_lower in t["section"].lower()]
    if department and department != "ALL":
        tasks = [t for t in tasks if t["department"] == department]
    if priority and priority != "ALL":
        tasks = [t for t in tasks if t["priority"] == priority]
    if status and status != "ALL":
        tasks = [t for t in tasks if t.get("status") == status]
    return tasks

@app.post("/api/tasks")
def create_task(task: MaintenanceTask) -> Dict[str, Any]:
    try:
        created = db.add_task(task.model_dump())
        return {"status": "SUCCESS", "message": f"Task {task.id} created successfully", "task": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tasks/{task_id}")
def get_task(task_id: str) -> Dict[str, Any]:
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

@app.put("/api/tasks/{task_id}")
def update_task(task_id: str, updates: MaintenanceTaskUpdate) -> Dict[str, Any]:
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    try:
        updated = db.update_task(task_id, update_data)
        return {"status": "SUCCESS", "message": f"Task {task_id} updated", "task": updated}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str) -> Dict[str, Any]:
    success = db.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"status": "SUCCESS", "message": f"Task {task_id} deleted successfully"}

@app.post("/api/tasks/{task_id}/duplicate")
def duplicate_task(task_id: str) -> Dict[str, Any]:
    original = db.get_task(task_id)
    if not original:
        raise HTTPException(status_code=404, detail="Original task not found")
    
    new_task = dict(original)
    new_task["id"] = f"{original['id']}-COPY"
    new_task["status"] = "PENDING"
    try:
        created = db.add_task(new_task)
        return {"status": "SUCCESS", "message": f"Task duplicated as {created['id']}", "task": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/trains")
def list_trains() -> List[Dict[str, Any]]:
    return db.get_trains()

@app.post("/api/trains")
def create_train(train: TrainMovement) -> Dict[str, Any]:
    try:
        created = db.add_train(train.model_dump())
        return {"status": "SUCCESS", "message": f"Train {train.train_id} on section {train.section} registered", "train": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/trains/{train_id}")
def update_train(train_id: str, section: str, updates: TrainMovementUpdate) -> Dict[str, Any]:
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    try:
        updated = db.update_train(train_id, section, update_data)
        return {"status": "SUCCESS", "message": f"Train {train_id} updated", "train": updated}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/api/trains/{train_id}")
def delete_train(train_id: str, section: str) -> Dict[str, Any]:
    success = db.delete_train(train_id, section)
    if not success:
        raise HTTPException(status_code=404, detail=f"Train {train_id} on section {section} not found")
    return {"status": "SUCCESS", "message": f"Train {train_id} deleted successfully"}

@app.get("/api/blocks")
def list_blocks() -> List[Dict[str, Any]]:
    return db.get_blocks()

@app.post("/api/blocks")
def create_block(block: BlockWindow) -> Dict[str, Any]:
    try:
        created = db.add_block(block.model_dump())
        return {"status": "SUCCESS", "message": f"Block window {block.id} registered", "block": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/blocks/{block_id}")
def update_block(block_id: str, updates: BlockWindowUpdate) -> Dict[str, Any]:
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    try:
        updated = db.update_block(block_id, update_data)
        return {"status": "SUCCESS", "message": f"Block {block_id} updated", "block": updated}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/api/blocks/{block_id}")
def delete_block(block_id: str) -> Dict[str, Any]:
    success = db.delete_block(block_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Block {block_id} not found")
    return {"status": "SUCCESS", "message": f"Block {block_id} deleted successfully"}

@app.get("/api/sections")
def list_sections() -> List[Dict[str, Any]]:
    return db.get_all().get("sections", [])

@app.get("/api/assets")
def list_assets() -> List[Dict[str, Any]]:
    return db.get_all().get("assets", [])

@app.post("/api/optimize")
def solve_schedule(triggered_by: str = "MANUAL_TRIGGER") -> Dict[str, Any]:
    data = db.get_all()
    tasks = data.get("tasks", [])
    trains = data.get("trains", [])
    blocks = data.get("block_windows", [])
    resources = data.get("resources", [])
    prev_schedule = data.get("current_schedule", [])

    res = run_optimization(tasks, trains, blocks, resources, previous_schedule=prev_schedule)
    scheduled = res["scheduled_items"]
    unassigned = res["unassigned_tasks"]

    for item in scheduled:
        item["explanation"] = generate_task_explanation(item, trains, tasks, blocks)

    unassigned_explanations = {}
    task_map = {t["id"]: t for t in tasks}
    for u_id in unassigned:
        if u_id in task_map:
            unassigned_explanations[u_id] = generate_unassigned_explanation(task_map[u_id], blocks, trains)

    baseline = calculate_baseline_comparison(tasks, trains, blocks, scheduled) if tasks else None
    summary_exp = generate_plan_summary(
        scheduled, unassigned, baseline, 
        solver_status=res["solver_status"], 
        solve_time_seconds=res["solve_time_seconds"]
    )

    history_record = db.set_optimization_result(
        scheduled, baseline, summary_exp, 
        triggered_by=triggered_by,
        solver_status=res["solver_status"],
        solve_time_seconds=res["solve_time_seconds"],
        tasks_considered=res["tasks_considered"]
    )

    return {
        "status": res["status"],
        "solver_status": res["solver_status"],
        "solve_time_seconds": res["solve_time_seconds"],
        "tasks_considered": res["tasks_considered"],
        "tasks_scheduled": len(scheduled),
        "tasks_unscheduled": len(unassigned),
        "conflicts_count": baseline.get("optimized_conflicts", 0) if baseline else 0,
        "plan_id": history_record["plan_id"],
        "timestamp": history_record["timestamp"],
        "total_tasks_scheduled": len(scheduled),
        "schedule": scheduled,
        "unassigned_tasks": unassigned,
        "unassigned_explanations": unassigned_explanations,
        "baseline_comparison": baseline,
        "summary_explanation": summary_exp
    }

@app.post("/api/inject-emergency")
def inject_emergency_defect(request: EmergencyDefectRequest) -> Dict[str, Any]:
    db.create_snapshot()
    data_before = db.get_all()
    old_schedule_map = {s["task_id"]: (s["block_id"], s["start_hour"]) for s in data_before.get("current_schedule", [])}

    tasks = data_before.get("tasks", [])
    emg_id = request.defect_id or f"EMG-{len(tasks) + 1:03d}"
    
    emergency_task = {
        "id": emg_id,
        "asset_id": request.asset_id or "AST-102",
        "section": request.section,
        "department": "Engineering",
        "task_type": request.defect_type,
        "duration_mins": request.duration_mins,
        "priority": request.severity,
        "deadline_hour": request.deadline_hour,
        "status": "PENDING",
        "is_emergency": True,
        "required_crew": "Emergency Track Gang 911",
        "required_equipment": "Rail Weld Kit & Ultrasonic Detector",
        "risk_score": 99.5,
        "description": request.description
    }
    db.add_task(emergency_task)
    db.add_incident({
        "incident_id": f"INC-{len(tasks) + 1:03d}",
        "task_id": emg_id,
        "section": request.section,
        "defect_type": request.defect_type,
        "severity": request.severity,
        "timestamp": db._get_iso_time()
    })

    opt_res = solve_schedule(triggered_by=f"EMERGENCY_DEFECT_{emg_id}")

    new_schedule = opt_res["schedule"]
    affected_tasks = []
    unchanged_tasks = []

    for s in new_schedule:
        t_id = s["task_id"]
        if t_id == emg_id:
            continue
        old_loc = old_schedule_map.get(t_id)
        if old_loc and old_loc == (s["block_id"], s["start_hour"]):
            unchanged_tasks.append(t_id)
        else:
            affected_tasks.append(t_id)

    moved_details = []
    old_task_details = {s["task_id"]: s for s in data_before.get("current_schedule", [])}
    for s in new_schedule:
        t_id = s["task_id"]
        if t_id in affected_tasks and t_id in old_task_details:
            old_item = old_task_details[t_id]
            shift_mins = int(round((s["start_hour"] - old_item["start_hour"]) * 60))
            moved_details.append({
                "task_id": t_id,
                "task_name": s["task_name"],
                "section": s["section"],
                "old_start_hour": old_item["start_hour"],
                "old_end_hour": old_item["end_hour"],
                "new_start_hour": s["start_hour"],
                "new_end_hour": s["end_hour"],
                "old_block_id": old_item["block_id"],
                "new_block_id": s["block_id"],
                "time_shift_mins": shift_mins,
                "reason": f"Displaced by {emg_id} (preempted corridor line block on {request.section})"
            })

    diff = {
        "new_emergency_task": emg_id,
        "affected_tasks": affected_tasks,
        "unchanged_tasks": unchanged_tasks,
        "total_moved": len(affected_tasks),
        "moved_details": moved_details
    }
    db.save_diff(diff)
    opt_res["diff"] = diff

    return {
        "status": "SUCCESS",
        "message": f"Emergency defect '{emg_id}' registered on {request.section}. Schedule re-optimized.",
        "emergency_task": emergency_task,
        "optimization_result": opt_res,
        "diff": diff
    }

@app.post("/api/revert-plan")
def revert_to_previous_plan() -> Dict[str, Any]:
    success = db.revert_snapshot()
    if not success:
        raise HTTPException(status_code=400, detail="No previous plan snapshot available to revert to.")
    return {"status": "SUCCESS", "message": "Plan successfully reverted to previous state.", "dataset": db.get_all()}

@app.get("/api/history")
def get_plan_history() -> List[Dict[str, Any]]:
    return db.get_history()

@app.get("/api/export")
def export_csv(entity: str = "schedule"):
    data = db.get_all()
    output = io.StringIO()
    writer = csv.writer(output)

    if entity == "tasks":
        tasks = data.get("tasks", [])
        writer.writerow(["Task ID", "Asset ID", "Section", "Department", "Task Type", "Duration Mins", "Priority", "Deadline Hour", "Status", "Crew", "Is Emergency"])
        for t in tasks:
            writer.writerow([t.get("id"), t.get("asset_id"), t.get("section"), t.get("department"), t.get("task_type"), t.get("duration_mins"), t.get("priority"), t.get("deadline_hour"), t.get("status"), t.get("required_crew"), t.get("is_emergency", False)])
        filename = "maintenance_tasks.csv"
    elif entity == "trains":
        trains = data.get("trains", [])
        writer.writerow(["Train ID", "Train Name", "Origin", "Destination", "Type", "Section", "Arrival Hour", "Departure Hour", "Service Priority", "Direction", "Protected"])
        for tr in trains:
            writer.writerow([tr.get("train_id"), tr.get("train_name"), tr.get("origin"), tr.get("destination"), tr.get("train_type"), tr.get("section"), tr.get("arrival_hour"), tr.get("departure_hour"), tr.get("service_priority"), tr.get("direction"), tr.get("is_protected")])
        filename = "train_timetable.csv"
    elif entity == "blocks":
        blocks = data.get("block_windows", [])
        writer.writerow(["Block ID", "Section", "Start Hour", "End Hour", "Max Duration Mins", "Permitted Departments", "Status"])
        for b in blocks:
            writer.writerow([b.get("id"), b.get("section"), b.get("start_hour"), b.get("end_hour"), b.get("max_duration_mins"), "; ".join(b.get("permitted_departments", [])), b.get("status")])
        filename = "block_windows.csv"
    else:
        schedule = data.get("current_schedule", [])
        writer.writerow([
            "Task ID", "Task Name", "Department", "Section", "Block ID",
            "Start Time (Hrs)", "End Time (Hrs)", "Duration (Mins)",
            "Priority", "Is Emergency", "Assigned Crew", "Protected Train Movements", "Reasoning / Audit Notes"
        ])
        for s in schedule:
            writer.writerow([
                s["task_id"],
                s["task_name"],
                s["department"],
                s["section"],
                s["block_id"],
                f"{s['start_hour']:05.2f}",
                f"{s['end_hour']:05.2f}",
                s["duration_mins"],
                s["priority"],
                s.get("is_emergency", False),
                "; ".join(s.get("assigned_resources", [])),
                f"{s.get('train_conflicts_avoided', 0)} Trains Protected",
                s.get("explanation", "")
            ])
        filename = "railway_maintenance_block_plan.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/api/import/blocks")
def import_blocks_endpoint(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        count = db.import_blocks(blocks)
        return {"status": "SUCCESS", "message": f"Successfully imported {count} block windows.", "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/reset")
def reset_system() -> Dict[str, Any]:
    db.reset_to_default()
    return {"status": "SUCCESS", "message": "System datastore reset to representative demonstration state."}

# Pan-India Station Search & Geographical Navigation
@app.get("/api/stations")
def get_stations(
    search: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    return search_stations(search or "", state=state, district=district, limit=limit)

@app.get("/api/stations/{code}")
def get_station_details(code: str) -> Dict[str, Any]:
    station = get_station_by_code(code)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station code '{code}' not found.")
    return station

@app.get("/api/geography/states")
def list_states() -> List[str]:
    return get_all_states()

@app.get("/api/geography/districts")
def list_districts(state: str) -> List[str]:
    return get_districts_by_state(state)

@app.get("/api/geography/stations")
def list_stations_in_district(state: str, district: str) -> List[Dict[str, Any]]:
    return get_stations_by_district(state, district)

@app.get("/api/geography/tree")
def get_geography_tree() -> Dict[str, Any]:
    return get_geographical_tree()

# Provider-based Live Train Running Status (Decoupled & Graceful)
@app.get("/api/live/provider-status")
def get_live_provider_status() -> Dict[str, Any]:
    return train_provider.get_provider_status()

@app.get("/api/live/train-status/{train_number}")
def get_live_train_status(train_number: str) -> Dict[str, Any]:
    return train_provider.get_live_train_status(train_number)

# Data Import & Export
@app.post("/api/import/tasks")
def import_tasks_endpoint(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        count = db.import_tasks(tasks)
        return {"status": "SUCCESS", "message": f"Successfully imported {count} maintenance tasks.", "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/import/trains")
def import_trains_endpoint(trains: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        count = db.import_trains(trains)
        return {"status": "SUCCESS", "message": f"Successfully imported {count} train movements.", "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/import/scenario")
def import_scenario_endpoint(scenario: Dict[str, Any]) -> Dict[str, Any]:
    try:
        db.import_scenario(scenario)
        return {"status": "SUCCESS", "message": "Custom scenario imported successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/export/dataset")
def export_dataset_json():
    return db.get_all()

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
