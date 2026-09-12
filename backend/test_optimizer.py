import unittest
from backend.database import db
from backend.optimizer import run_optimization
from backend.baseline_solver import calculate_baseline_comparison
from backend.schemas import MaintenanceTask, EmergencyDefectRequest
from backend.main import solve_schedule, inject_emergency_defect, revert_to_previous_plan

class TestRailwayBlockPlannerEndToEnd(unittest.TestCase):

    def setUp(self):
        # Reset to clean initial state
        db.reset_to_default()

    def test_database_crud(self):
        # 1. Add task
        new_task = {
            "id": "TSK-TEST-99",
            "asset_id": "AST-101",
            "section": "A12-B14",
            "department": "Engineering",
            "task_type": "Ultrasonic Rail Joint Testing",
            "duration_mins": 60,
            "priority": "HIGH",
            "deadline_hour": 15.0,
            "status": "PENDING"
        }
        added = db.add_task(new_task)
        self.assertEqual(added["id"], "TSK-TEST-99")

        # 2. Update task
        updated = db.update_task("TSK-TEST-99", {"priority": "CRITICAL"})
        self.assertEqual(updated["priority"], "CRITICAL")

        # 3. Delete task
        deleted = db.delete_task("TSK-TEST-99")
        self.assertTrue(deleted)
        self.assertIsNone(db.get_task("TSK-TEST-99"))

    def test_optimization_solver_zero_conflicts(self):
        data = db.get_all()
        tasks = data["tasks"]
        trains = data["trains"]
        blocks = data["block_windows"]
        resources = data["resources"]

        res = run_optimization(tasks, trains, blocks, resources)
        self.assertIn(res["status"], ["OPTIMAL", "FEASIBLE"])
        self.assertGreater(len(res["scheduled_items"]), 0)

        # Verify strict train timetable deconfliction
        for item in res["scheduled_items"]:
            sec = item["section"]
            st = item["start_hour"]
            end = item["end_hour"]

            sec_trains = [t for t in trains if t["section"] == sec]
            for tr in sec_trains:
                tr_arr = tr["arrival_hour"]
                tr_dep = tr["departure_hour"]
                overlap = min(end, tr_dep) - max(st, tr_arr)
                self.assertLessEqual(overlap, 0.001, f"Conflict detected on section {sec} between task {item['task_id']} and train {tr['train_id']}")

    def test_baseline_real_mathematical_metrics(self):
        data = db.get_all()
        tasks = data["tasks"]
        trains = data["trains"]
        blocks = data["block_windows"]

        res = run_optimization(tasks, trains, blocks, data["resources"])
        baseline = calculate_baseline_comparison(tasks, trains, blocks, res["scheduled_items"])

        # Naive uncoordinated planning MUST produce train collisions on dense corridor
        self.assertGreater(baseline["manual_conflicts"], 0)
        # OR-Tools plan MUST produce 0 conflicts
        self.assertEqual(baseline["optimized_conflicts"], 0)
        # Delay saved must be calculated mathematically
        self.assertGreater(baseline["delay_reduction_pct"], 50.0)

    def test_emergency_injection_and_revert(self):
        # 1. Initial optimization
        initial_plan = solve_schedule()
        initial_count = initial_plan["total_tasks_scheduled"]

        # 2. Inject emergency defect
        req = EmergencyDefectRequest(
            defect_id="EMG-TEST-001",
            section="A12-B14",
            defect_type="EMERGENCY Track Rail Fracture",
            severity="CRITICAL",
            duration_mins=90,
            deadline_hour=5.0
        )
        emg_res = inject_emergency_defect(req)
        self.assertEqual(emg_res["status"], "SUCCESS")
        self.assertIn("diff", emg_res)

        # Verify emergency task is scheduled
        sched_tasks = [s["task_id"] for s in emg_res["optimization_result"]["schedule"]]
        self.assertIn("EMG-TEST-001", sched_tasks)

        # 3. Test revert
        rev_res = revert_to_previous_plan()
        self.assertEqual(rev_res["status"], "SUCCESS")
        
        # Verify emergency task is gone after revert
        self.assertIsNone(db.get_task("EMG-TEST-001"))

    def test_empty_scenario_state(self):
        empty_data = db.load_empty_scenario()
        self.assertEqual(len(empty_data["tasks"]), 0)
        self.assertEqual(len(empty_data["trains"]), 0)
        self.assertEqual(len(empty_data["block_windows"]), 0)
        self.assertEqual(empty_data["data_source"], "EMPTY_SCENARIO")

        # Running optimizer on empty dataset should return NO_TASKS cleanly
        opt_res = solve_schedule()
        self.assertEqual(opt_res["total_tasks_scheduled"], 0)
        self.assertEqual(opt_res["status"], "NO_TASKS")

    def test_pan_india_station_search(self):
        from backend.station_data import search_stations, get_station_by_code, get_all_states
        
        # Search by code
        hwh = get_station_by_code("HWH")
        self.assertIsNotNone(hwh)
        self.assertEqual(hwh["name"], "Howrah Junction")

        # Search by city / name
        results = search_stations("New Delhi")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["code"], "NDLS")

        # Check states list
        states = get_all_states()
        self.assertIn("West Bengal", states)
        self.assertIn("Delhi", states)
        self.assertIn("Maharashtra", states)

    def test_live_provider_fallback(self):
        from backend.train_provider import train_provider
        status = train_provider.get_live_train_status("12301")
        self.assertIn(status["label"], ["SIMULATED TIMETABLE", "LIVE STATUS UNAVAILABLE"])
        self.assertFalse(status["configured"])

    def test_data_import(self):
        new_tasks = [
            {
                "id": "TSK-IMP-01",
                "asset_id": "AST-101",
                "section": "A12-B14",
                "department": "Engineering",
                "task_type": "Imported Ultrasonic Track Scan",
                "duration_mins": 90,
                "priority": "HIGH",
                "deadline_hour": 18.0,
                "status": "PENDING"
            }
        ]
        count = db.import_tasks(new_tasks)
        self.assertEqual(count, 1)
        self.assertIsNotNone(db.get_task("TSK-IMP-01"))
        self.assertEqual(db.get_all()["data_source"], "IMPORTED_DATA")

if __name__ == "__main__":
    unittest.main()
