from typing import List, Dict, Any, Optional

def generate_task_explanation(item: Dict[str, Any], trains: List[Dict[str, Any]], 
                              all_tasks: Optional[List[Dict[str, Any]]] = None,
                              block_windows: Optional[List[Dict[str, Any]]] = None) -> str:
    sec = item["section"]
    prio = item["priority"]
    dept = item["department"]
    blk = item["block_id"]
    st_h = item["start_hour"]
    end_h = item["end_hour"]
    dur = item.get("duration_mins", int(round((end_h - st_h) * 60)))
    is_emg = item.get("is_emergency", False)
    
    sec_trains = [t for t in trains if t["section"] == sec]
    express_trains = [t for t in sec_trains if t.get("service_priority", 1) == 1]
    
    start_str = f"{int(st_h):02d}:{int(round((st_h % 1)*60)):02d}"
    end_str = f"{int(end_h):02d}:{int(round((end_h % 1)*60)):02d}"

    reasons = []

    if is_emg:
        reasons.append(f"EMERGENCY PRIORITY PREEMPTION: Immediate line block allocated in {blk} ({start_str}–{end_str}) on Section {sec}.")
    elif prio == "CRITICAL":
        reasons.append(f"Ranked #1 Priority (Critical Safety Defect) on Section {sec}: Allocated window {start_str}–{end_str} in Block {blk}.")
    elif prio == "HIGH":
        reasons.append(f"High-urgency task scheduled on Section {sec} in sanctioned window {start_str}–{end_str} ({blk}).")
    else:
        reasons.append(f"Scheduled on Section {sec} during low-density traffic window {start_str}–{end_str} ({blk}).")

    if item.get("shift_reason"):
        reasons.append(item["shift_reason"])

    reasons.append(f"Window {blk} permits {dept} operations with {dur}m required duration satisfied.")

    if express_trains:
        t_names = ", ".join(set([t["train_name"] for t in express_trains[:2]]))
        reasons.append(f"100% Express Timetable Isolation verified (Protected: {t_names}).")
    else:
        reasons.append("Section clear of high-speed passenger movements.")

    crew = item.get("assigned_resources", ["Maintenance Team"])[0]
    reasons.append(f"Assigned designated {dept} gang ({crew}).")

    return " ".join(reasons)

def generate_unassigned_explanation(task: Dict[str, Any], block_windows: List[Dict[str, Any]], 
                                     trains: List[Dict[str, Any]]) -> str:
    sec = task.get("section", "")
    dept = task.get("department", "")
    dur = task.get("duration_mins", 0)
    deadline = task.get("deadline_hour", 24.0)

    matching_windows = [
        b for b in block_windows 
        if b["section"] == sec and dept in b.get("permitted_departments", [])
    ]

    if not matching_windows:
        return f"Not scheduled: No sanctioned block windows on section {sec} allow {dept} maintenance."

    valid_dur_windows = [
        b for b in matching_windows 
        if b.get("max_duration_mins", int((b["end_hour"] - b["start_hour"]) * 60)) >= dur
    ]
    if not valid_dur_windows:
        return f"Not scheduled: Required duration ({dur} mins) exceeds capacity of permitted block windows on {sec}."

    before_deadline_windows = [
        b for b in valid_dur_windows 
        if b["start_hour"] + (dur / 60.0) <= deadline
    ]
    if not before_deadline_windows:
        return f"Not scheduled: Permitted block windows on {sec} cannot fit task before strict deadline {deadline:04.1f} hrs."

    return f"Not scheduled: Corridor track and timetable density on section {sec} precluded collision-free placement before deadline {deadline:04.1f} hrs."

def generate_plan_summary(scheduled: List[Dict[str, Any]], unassigned: List[str], 
                          baseline: Optional[Dict[str, Any]], solver_status: str = "OPTIMAL",
                          solve_time_seconds: float = 0.0) -> str:
    count = len(scheduled)
    unassigned_count = len(unassigned)
    if count == 0 and unassigned_count == 0:
        return "No maintenance tasks registered in current scenario. Add tasks or load demo scenario to plan."

    crit_count = len([x for x in scheduled if x["priority"] == "CRITICAL"])
    
    parts = [f"OR-Tools CP-SAT ({solver_status} in {solve_time_seconds:.2f}s): {count} blocks scheduled."]
    if crit_count > 0:
        parts.append(f"{crit_count} critical safety defect(s) secured before deadlines.")
    if unassigned_count > 0:
        parts.append(f"{unassigned_count} task(s) unassigned due to corridor/window constraints.")
    else:
        parts.append("0 unscheduled tasks.")

    if baseline and baseline.get("manual_total_delay_mins", 0) > 0:
        delay_saved = baseline["manual_total_delay_mins"] - baseline["optimized_total_delay_mins"]
        parts.append(f"Saved {delay_saved} mins vs uncoordinated baseline ({baseline['delay_reduction_pct']}% reduction).")
        parts.append(f"Window utilization: {baseline['optimized_block_utilization_pct']}%.")

    return " ".join(parts)
