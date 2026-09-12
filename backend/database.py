import os
import json
import copy
from typing import Dict, Any, List, Optional
from threading import Lock
from backend.synthetic_data import get_initial_dataset

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "datastore.json")
SNAPSHOT_FILE = os.path.join(DATA_DIR, "snapshot.json")

class Database:
    def __init__(self):
        self._lock = Lock()
        self._data: Dict[str, Any] = {}
        self._snapshot_before_emergency: Optional[Dict[str, Any]] = None
        self._ensure_storage()

    def _ensure_storage(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(DATA_FILE):
            self.reset_to_default()
        else:
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self.reset_to_default()

    def _save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def reset_to_default(self) -> Dict[str, Any]:
        return self.load_demo_scenario()

    def load_demo_scenario(self) -> Dict[str, Any]:
        with self._lock:
            default_data = get_initial_dataset()
            default_data["current_schedule"] = []
            default_data["plan_history"] = []
            default_data["baseline_comparison"] = None
            default_data["latest_summary"] = "Demo scenario loaded. Click 'Generate Plan' to run Google OR-Tools optimizer."
            default_data["data_source"] = "DEMO_SCENARIO"
            default_data["scenario_name"] = "Demo Scenario (Howrah – Pt. DDU Trunk Line)"
            default_data["data_source_label"] = "Synthetic Demo Dataset"
            default_data["last_optimized_at"] = None
            default_data["latest_diff"] = None
            self._data = default_data
            self._snapshot_before_emergency = None
            if os.path.exists(SNAPSHOT_FILE):
                try:
                    os.remove(SNAPSHOT_FILE)
                except Exception:
                    pass
            self._save()
            return copy.deepcopy(self._data)

    def load_empty_scenario(self) -> Dict[str, Any]:
        with self._lock:
            base_data = get_initial_dataset()
            empty_data = {
                "sections": copy.deepcopy(base_data["sections"]),
                "assets": copy.deepcopy(base_data["assets"]),
                "tasks": [],
                "trains": [],
                "block_windows": [],
                "resources": copy.deepcopy(base_data["resources"]),
                "current_schedule": [],
                "plan_history": [],
                "baseline_comparison": None,
                "latest_diff": None,
                "latest_summary": "Empty scenario initialized. Add maintenance tasks or import operational data to begin.",
                "data_source": "EMPTY_SCENARIO",
                "scenario_name": "New Empty Scenario",
                "data_source_label": "User-Entered Data (Blank Slate)",
                "last_optimized_at": None,
                "last_solver_status": "NOT RUN"
            }
            self._data = empty_data
            self._snapshot_before_emergency = None
            if os.path.exists(SNAPSHOT_FILE):
                try:
                    os.remove(SNAPSHOT_FILE)
                except Exception:
                    pass
            self._save()
            return copy.deepcopy(self._data)

    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._data)

    def get_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(self._data.get("tasks", []))

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for t in self._data.get("tasks", []):
                if t["id"] == task_id:
                    return copy.deepcopy(t)
            return None

    def add_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            tasks = self._data.setdefault("tasks", [])
            for t in tasks:
                if t["id"] == task["id"]:
                    raise ValueError(f"Task ID '{task['id']}' already exists.")
            tasks.append(task)
            self._save()
            return copy.deepcopy(task)

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            tasks = self._data.get("tasks", [])
            for i, t in enumerate(tasks):
                if t["id"] == task_id:
                    tasks[i].update(updates)
                    self._save()
                    return copy.deepcopy(tasks[i])
            raise KeyError(f"Task '{task_id}' not found.")

    def delete_task(self, task_id: str) -> bool:
        with self._lock:
            tasks = self._data.get("tasks", [])
            initial_len = len(tasks)
            self._data["tasks"] = [t for t in tasks if t["id"] != task_id]
            if len(self._data["tasks"]) < initial_len:
                sched = self._data.get("current_schedule", [])
                self._data["current_schedule"] = [s for s in sched if s.get("task_id") != task_id]
                self._save()
                return True
            return False

    def get_trains(self) -> List[Dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(self._data.get("trains", []))

    def add_train(self, train: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            trains = self._data.setdefault("trains", [])
            for tr in trains:
                if tr["train_id"] == train["train_id"] and tr["section"] == train["section"]:
                    raise ValueError(f"Train '{train['train_id']}' movement on section '{train['section']}' already exists.")
            trains.append(train)
            self._save()
            return copy.deepcopy(train)

    def update_train(self, train_id: str, section: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            trains = self._data.get("trains", [])
            for i, tr in enumerate(trains):
                if tr["train_id"] == train_id and tr["section"] == section:
                    trains[i].update(updates)
                    self._save()
                    return copy.deepcopy(trains[i])
            raise KeyError(f"Train '{train_id}' on section '{section}' not found.")

    def delete_train(self, train_id: str, section: str) -> bool:
        with self._lock:
            trains = self._data.get("trains", [])
            initial_len = len(trains)
            self._data["trains"] = [tr for tr in trains if not (tr["train_id"] == train_id and tr["section"] == section)]
            if len(self._data["trains"]) < initial_len:
                self._save()
                return True
            return False

    def get_blocks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(self._data.get("block_windows", []))

    def add_block(self, block: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            blocks = self._data.setdefault("block_windows", [])
            for b in blocks:
                if b["id"] == block["id"]:
                    raise ValueError(f"Block ID '{block['id']}' already exists.")
            blocks.append(block)
            self._save()
            return copy.deepcopy(block)

    def update_block(self, block_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            blocks = self._data.get("block_windows", [])
            for i, b in enumerate(blocks):
                if b["id"] == block_id:
                    blocks[i].update(updates)
                    self._save()
                    return copy.deepcopy(blocks[i])
            raise KeyError(f"Block '{block_id}' not found.")

    def delete_block(self, block_id: str) -> bool:
        with self._lock:
            blocks = self._data.get("block_windows", [])
            initial_len = len(blocks)
            self._data["block_windows"] = [b for b in blocks if b["id"] != block_id]
            if len(self._data["block_windows"]) < initial_len:
                self._save()
                return True
            return False

    def set_optimization_result(self, schedule: List[Dict[str, Any]], baseline: Optional[Dict[str, Any]], 
                                summary: str, triggered_by: str = "MANUAL_TRIGGER",
                                solver_status: str = "OPTIMAL", solve_time_seconds: float = 0.0,
                                tasks_considered: int = 0) -> Dict[str, Any]:
        with self._lock:
            self._data["current_schedule"] = schedule
            self._data["baseline_comparison"] = baseline
            self._data["latest_summary"] = summary
            self._data["last_optimized_at"] = self._get_iso_time()
            self._data["last_solver_status"] = solver_status

            scheduled_ids = set(s["task_id"] for s in schedule)
            for t in self._data.get("tasks", []):
                t["status"] = "SCHEDULED" if t["id"] in scheduled_ids else "UNASSIGNED"

            history = self._data.setdefault("plan_history", [])
            conflicts = baseline.get("optimized_conflicts", 0) if baseline else 0
            utilization = baseline.get("optimized_block_utilization_pct", 0.0) if baseline else 0.0
            delay_saved = baseline.get("delay_reduction_pct", 0.0) if baseline else 0.0

            history_record = {
                "plan_id": f"PLAN-{len(history) + 1:04d}",
                "timestamp": self._get_iso_time(),
                "triggered_by": triggered_by,
                "status": solver_status,
                "solve_time_seconds": round(solve_time_seconds, 3),
                "tasks_considered": tasks_considered,
                "tasks_scheduled": len(schedule),
                "tasks_unscheduled": max(0, tasks_considered - len(schedule)),
                "conflicts": conflicts,
                "utilization_pct": utilization,
                "delay_saved_pct": delay_saved,
                "summary": summary
            }
            history.insert(0, history_record)
            if len(history) > 50:
                self._data["plan_history"] = history[:50]

            self._save()
            return history_record

    def create_snapshot(self):
        with self._lock:
            self._snapshot_before_emergency = copy.deepcopy(self._data)
            try:
                with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
                    json.dump(self._snapshot_before_emergency, f, indent=2)
            except Exception:
                pass

    def can_revert(self) -> bool:
        with self._lock:
            return self._snapshot_before_emergency is not None or os.path.exists(SNAPSHOT_FILE)

    def revert_snapshot(self) -> bool:
        with self._lock:
            snap = self._snapshot_before_emergency
            if not snap and os.path.exists(SNAPSHOT_FILE):
                try:
                    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
                        snap = json.load(f)
                except Exception:
                    snap = None

            if snap:
                self._data = copy.deepcopy(snap)
                self._data["latest_diff"] = None
                self._snapshot_before_emergency = None
                if os.path.exists(SNAPSHOT_FILE):
                    try:
                        os.remove(SNAPSHOT_FILE)
                    except Exception:
                        pass
                self._save()
                return True
            return False

    def save_diff(self, diff: Dict[str, Any]):
        with self._lock:
            self._data["latest_diff"] = diff
            self._save()

    def clear_diff(self):
        with self._lock:
            self._data["latest_diff"] = None
            self._save()

    def add_incident(self, incident: Dict[str, Any]):
        with self._lock:
            incidents = self._data.setdefault("incidents", [])
            incidents.append(incident)
            self._save()

    def import_blocks(self, blocks: List[Dict[str, Any]]) -> int:
        with self._lock:
            existing = {b["id"]: i for i, b in enumerate(self._data.get("block_windows", []))}
            added_count = 0
            for b in blocks:
                if b.get("id") in existing:
                    self._data["block_windows"][existing[b["id"]]].update(b)
                else:
                    self._data.setdefault("block_windows", []).append(b)
                added_count += 1
            self._data["data_source"] = "IMPORTED_DATA"
            self._data["data_source_label"] = f"Imported Data ({added_count} block windows)"
            self._save()
            return added_count

    def import_tasks(self, tasks: List[Dict[str, Any]]) -> int:
        with self._lock:
            existing = {t["id"]: i for i, t in enumerate(self._data.get("tasks", []))}
            added_count = 0
            for t in tasks:
                if t.get("id") in existing:
                    self._data["tasks"][existing[t["id"]]].update(t)
                else:
                    self._data.setdefault("tasks", []).append(t)
                added_count += 1
            self._data["data_source"] = "IMPORTED_DATA"
            self._data["data_source_label"] = f"Imported Data ({added_count} tasks)"
            self._save()
            return added_count

    def import_trains(self, trains: List[Dict[str, Any]]) -> int:
        with self._lock:
            existing = {(tr.get("train_id"), tr.get("section")): i for i, tr in enumerate(self._data.get("trains", []))}
            added_count = 0
            for tr in trains:
                key = (tr.get("train_id"), tr.get("section"))
                if key in existing:
                    self._data["trains"][existing[key]].update(tr)
                else:
                    self._data.setdefault("trains", []).append(tr)
                added_count += 1
            self._data["data_source"] = "IMPORTED_DATA"
            self._data["data_source_label"] = f"Imported Data ({added_count} trains)"
            self._save()
            return added_count

    def import_scenario(self, scenario_data: Dict[str, Any], source_label: str = "Imported Scenario") -> bool:
        with self._lock:
            for key in ["sections", "tasks", "trains", "block_windows"]:
                if key not in scenario_data:
                    raise ValueError(f"Missing required key '{key}' in scenario dataset.")
            scenario_data["current_schedule"] = []
            scenario_data["plan_history"] = []
            scenario_data["baseline_comparison"] = None
            scenario_data["latest_summary"] = "Imported scenario loaded. Ready for optimization."
            scenario_data["data_source"] = "IMPORTED_DATA"
            scenario_data["data_source_label"] = source_label
            scenario_data["scenario_name"] = scenario_data.get("scenario_name", "Imported Operational Scenario")
            scenario_data["last_optimized_at"] = None
            scenario_data["last_solver_status"] = "NOT RUN"
            self._data = scenario_data
            self._snapshot_before_emergency = None
            self._save()
            return True

    def _get_iso_time(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

db = Database()
