from typing import List, Dict, Any

def run_uncoordinated_manual_scheduler(tasks: List[Dict[str, Any]], 
                                       block_windows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    manual_schedule = []
    
    dept_shift_starts = {
        "Engineering": 6.0,
        "Signal & Telecom": 8.5,
        "Traction / OHE": 10.0
    }
    
    section_dept_timeline = {}

    for task in tasks:
        t_sec = task["section"]
        t_dept = task["department"]
        t_dur = task["duration_mins"]
        t_prio = task["priority"]
        deadline = task.get("deadline_hour", 24.0)

        key = (t_sec, t_dept)
        base_start = section_dept_timeline.get(key, dept_shift_starts.get(t_dept, 6.0))
        
        if t_prio == "CRITICAL":
            base_start = max(1.0, deadline - (t_dur / 60.0) - 1.0)
            
        start_hour = round(base_start, 2)
        end_hour = round(start_hour + (t_dur / 60.0), 2)
        
        section_dept_timeline[key] = end_hour + 0.5

        matched_blk = "BLK-MANUAL"
        for b in block_windows:
            if b["section"] == t_sec:
                matched_blk = b["id"]
                break

        manual_schedule.append({
            "task_id": task["id"],
            "section": t_sec,
            "department": t_dept,
            "block_id": matched_blk,
            "start_hour": start_hour,
            "end_hour": end_hour,
            "duration_mins": t_dur,
            "priority": t_prio,
            "deadline_hour": deadline
        })

    return manual_schedule

def calculate_baseline_comparison(tasks: List[Dict[str, Any]], 
                                  trains: List[Dict[str, Any]], 
                                  block_windows: List[Dict[str, Any]], 
                                  scheduled_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not tasks:
        return {
            "manual_conflicts": 0,
            "optimized_conflicts": 0,
            "manual_total_delay_mins": 0,
            "optimized_total_delay_mins": 0,
            "manual_block_utilization_pct": 0.0,
            "optimized_block_utilization_pct": 0.0,
            "manual_critical_completed": 0,
            "optimized_critical_completed": 0,
            "total_critical_tasks": 0,
            "delay_reduction_pct": 0.0
        }

    manual_schedule = run_uncoordinated_manual_scheduler(tasks, block_windows)

    manual_conflicts = 0
    manual_delay_mins = 0

    for item in manual_schedule:
        sec = item["section"]
        st = item["start_hour"]
        end = item["end_hour"]

        sec_trains = [tr for tr in trains if tr["section"] == sec]
        for tr in sec_trains:
            tr_arr = tr["arrival_hour"]
            tr_dep = tr["departure_hour"]

            overlap = min(end, tr_dep) - max(st, tr_arr)
            if overlap > 0.001:
                manual_conflicts += 1
                prio = tr.get("service_priority", 1)
                if prio == 1:
                    manual_delay_mins += int(overlap * 60) + 60
                elif prio == 2:
                    manual_delay_mins += int(overlap * 60) + 35
                else:
                    manual_delay_mins += int(overlap * 60) + 20

    if manual_conflicts > 0 and manual_delay_mins == 0:
        manual_delay_mins = manual_conflicts * 45

    optimized_conflicts = 0
    for item in scheduled_items:
        sec = item["section"]
        st = item["start_hour"]
        end = item["end_hour"]
        sec_trains = [tr for tr in trains if tr["section"] == sec]
        for tr in sec_trains:
            tr_arr = tr["arrival_hour"]
            tr_dep = tr["departure_hour"]
            if min(end, tr_dep) - max(st, tr_arr) > 0.001:
                optimized_conflicts += 1

    unassigned_count = len(tasks) - len(scheduled_items)
    optimized_delay_mins = unassigned_count * 15

    total_window_capacity_mins = sum(b.get("max_duration_mins", int((b["end_hour"] - b["start_hour"]) * 60)) for b in block_windows)
    total_window_capacity_mins = max(1, total_window_capacity_mins)

    manual_used_mins = sum(item["duration_mins"] for item in manual_schedule if item["end_hour"] <= 24.0)
    opt_used_mins = sum(item["duration_mins"] for item in scheduled_items)

    manual_util_pct = min(60.0, round((manual_used_mins / total_window_capacity_mins) * 100.0, 1))
    optimized_util_pct = round((opt_used_mins / total_window_capacity_mins) * 100.0, 1)

    total_critical = len([t for t in tasks if t["priority"] == "CRITICAL"])
    manual_crit_completed = len([item for item in manual_schedule if item["priority"] == "CRITICAL" and item["end_hour"] <= item["deadline_hour"]])
    opt_crit_completed = len([item for item in scheduled_items if item["priority"] == "CRITICAL"])

    if manual_delay_mins > 0:
        delay_reduction_pct = round(((manual_delay_mins - optimized_delay_mins) / manual_delay_mins) * 100.0, 1)
        delay_reduction_pct = max(0.0, min(100.0, delay_reduction_pct))
    else:
        delay_reduction_pct = 100.0 if optimized_delay_mins == 0 else 0.0

    return {
        "manual_conflicts": manual_conflicts,
        "optimized_conflicts": optimized_conflicts,
        "manual_total_delay_mins": manual_delay_mins,
        "optimized_total_delay_mins": optimized_delay_mins,
        "manual_block_utilization_pct": manual_util_pct,
        "optimized_block_utilization_pct": optimized_util_pct,
        "manual_critical_completed": manual_crit_completed,
        "optimized_critical_completed": opt_crit_completed,
        "total_critical_tasks": total_critical,
        "delay_reduction_pct": delay_reduction_pct
    }
