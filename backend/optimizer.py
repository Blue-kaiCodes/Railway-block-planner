import time
from typing import List, Dict, Any, Optional
from ortools.sat.python import cp_model

def minutes(hours: float) -> int:
    return int(round(hours * 60))

def hours(mins: int) -> float:
    return round(mins / 60.0, 2)

def run_optimization(tasks: List[Dict[str, Any]], 
                     trains: List[Dict[str, Any]], 
                     block_windows: List[Dict[str, Any]], 
                     resources: List[Dict[str, Any]],
                     previous_schedule: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    start_perf = time.perf_counter()

    if not tasks:
        return {
            "status": "NO_TASKS",
            "solver_status": "NO_TASKS",
            "solve_time_seconds": 0.0,
            "tasks_considered": 0,
            "total_tasks_scheduled": 0,
            "scheduled_items": [],
            "unassigned_tasks": [],
            "objective_value": 0.0
        }

    model = cp_model.CpModel()
    
    priority_weights = {
        "CRITICAL": 20000,
        "HIGH": 6000,
        "MEDIUM": 2000,
        "LOW": 600
    }
    
    prev_starts = {}
    if previous_schedule:
        for ps in previous_schedule:
            prev_starts[ps["task_id"]] = minutes(ps["start_hour"])

    task_vars = {}
    
    for task in tasks:
        t_id = task["id"]
        dur = task["duration_mins"]
        deadline_min = minutes(task.get("deadline_hour", 24.0))
        
        is_sched = model.NewBoolVar(f"sched_{t_id}")
        start_var = model.NewIntVar(0, 1440, f"start_{t_id}")
        end_var = model.NewIntVar(0, 1440, f"end_{t_id}")
        interval_var = model.NewOptionalIntervalVar(start_var, dur, end_var, is_sched, f"interval_{t_id}")
        
        task_vars[t_id] = {
            "task": task,
            "is_scheduled": is_sched,
            "start": start_var,
            "end": end_var,
            "interval": interval_var
        }
        
        model.Add(end_var <= deadline_min).OnlyEnforceIf(is_sched)

    for t_id, tv in task_vars.items():
        task = tv["task"]
        t_section = task["section"]
        t_dept = task["department"]
        t_dur = task["duration_mins"]
        
        candidate_blocks = [
            b for b in block_windows 
            if b["section"] == t_section and 
               t_dept in b.get("permitted_departments", []) and 
               b.get("max_duration_mins", int((b["end_hour"] - b["start_hour"]) * 60)) >= t_dur
        ]
        
        if not candidate_blocks:
            model.Add(tv["is_scheduled"] == 0)
            continue
            
        block_bools = []
        for b in candidate_blocks:
            b_id = b["id"]
            b_start = minutes(b["start_hour"])
            b_end = minutes(b["end_hour"])
            
            in_b = model.NewBoolVar(f"task_{t_id}_in_block_{b_id}")
            block_bools.append((in_b, b))
            
            model.Add(tv["start"] >= b_start).OnlyEnforceIf(in_b)
            model.Add(tv["end"] <= b_end).OnlyEnforceIf(in_b)
            
        model.Add(sum(b_bool for b_bool, _ in block_bools) == tv["is_scheduled"])
        tv["candidate_block_bools"] = block_bools

    for t_id, tv in task_vars.items():
        task = tv["task"]
        t_section = task["section"]
        section_trains = [tr for tr in trains if tr["section"] == t_section and tr.get("is_protected", True)]
        
        for tr in section_trains:
            tr_start = minutes(tr["arrival_hour"])
            tr_end = minutes(tr["departure_hour"])
            
            before_train = model.NewBoolVar(f"{t_id}_before_{tr['train_id']}")
            after_train = model.NewBoolVar(f"{t_id}_after_{tr['train_id']}")
            
            model.Add(tv["end"] <= tr_start).OnlyEnforceIf(before_train)
            model.Add(tv["start"] >= tr_end).OnlyEnforceIf(after_train)
            model.AddBoolOr([before_train, after_train]).OnlyEnforceIf(tv["is_scheduled"])

    tasks_by_section = {}
    tasks_by_dept = {}
    
    for t_id, tv in task_vars.items():
        sec = tv["task"]["section"]
        dept = tv["task"]["department"]
        tasks_by_section.setdefault(sec, []).append(tv["interval"])
        tasks_by_dept.setdefault(dept, []).append(tv["interval"])

    for sec, intervals in tasks_by_section.items():
        if len(intervals) > 1:
            model.AddNoOverlap(intervals)
            
    for dept, intervals in tasks_by_dept.items():
        if len(intervals) > 1:
            model.AddNoOverlap(intervals)

    objective_terms = []
    for t_id, tv in task_vars.items():
        prio = tv["task"]["priority"]
        is_emg = tv["task"].get("is_emergency", False) or t_id.startswith("EMG-")
        w = 60000 if is_emg else priority_weights.get(prio, 2000)
        
        objective_terms.append(tv["is_scheduled"] * w)
        objective_terms.append(-tv["start"])

        if t_id in prev_starts:
            target_start = prev_starts[t_id]
            diff_var = model.NewIntVar(0, 1440, f"diff_{t_id}")
            model.Add(diff_var >= tv["start"] - target_start)
            model.Add(diff_var >= target_start - tv["start"])
            objective_terms.append(-diff_var * 2)

    model.Maximize(sum(objective_terms))
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status_code = solver.Solve(model)
    status_str = solver.StatusName(status_code)
    
    scheduled_items = []
    unassigned = []
    
    dept_resources = {}
    for r in resources:
        dept_resources.setdefault(r["department"], []).append(r.get("team_name", "Central Maintenance Crew"))

    if status_code in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for t_id, tv in task_vars.items():
            task = tv["task"]
            if solver.Value(tv["is_scheduled"]) == 1:
                start_m = solver.Value(tv["start"])
                end_m = solver.Value(tv["end"])
                
                assigned_blk = "BLK-CUSTOM"
                for b_bool, b_obj in tv.get("candidate_block_bools", []):
                    if solver.Value(b_bool) == 1:
                        assigned_blk = b_obj["id"]
                        break
                        
                assigned_res = dept_resources.get(task["department"], [task.get("required_crew", "Central Crew")])
                sec_trains = [tr for tr in trains if tr["section"] == task["section"]]
                is_task_emg = task.get("is_emergency", False) or task["id"].startswith("EMG-")
                
                scheduled_items.append({
                    "task_id": task["id"],
                    "task_name": task["task_type"],
                    "department": task["department"],
                    "section": task["section"],
                    "block_id": assigned_blk,
                    "start_hour": hours(start_m),
                    "end_hour": hours(end_m),
                    "duration_mins": task["duration_mins"],
                    "assigned_resources": assigned_res,
                    "priority": task["priority"],
                    "is_emergency": is_task_emg,
                    "explanation": "",
                    "train_conflicts_avoided": len(sec_trains)
                })
            else:
                unassigned.append(task["id"])

        scheduled_items.sort(key=lambda x: x["start_hour"])
    else:
        unassigned = [t["id"] for t in tasks]

    elapsed = time.perf_counter() - start_perf
    return {
        "status": status_str,
        "solver_status": status_str,
        "solve_time_seconds": round(elapsed, 3),
        "tasks_considered": len(tasks),
        "total_tasks_scheduled": len(scheduled_items),
        "scheduled_items": scheduled_items,
        "unassigned_tasks": unassigned,
        "objective_value": solver.ObjectiveValue() if status_code in [cp_model.OPTIMAL, cp_model.FEASIBLE] else 0.0
    }
