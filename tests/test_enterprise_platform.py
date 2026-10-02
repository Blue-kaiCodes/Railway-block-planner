import os
import asyncio
import tempfile
import unittest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.canonical_schemas import (
    SensorIngestPayload, SensorType, SensorStatus, DataQuality,
    EventSource, EventType, EventSeverity, PlanApprovalStatus,
    NormalizedTrainState, BlockState, SensorEntity, OperatorDecisionRequest
)
from backend.railway_state import RailwayStateStore
from backend.providers.rtis_provider import RTISDataProvider
from backend.providers.ntes_provider import NTESDataProvider
from backend.providers.open_data_provider import OpenDataProvider
from backend.providers.simulation_provider import SimulationDataProvider
from backend.providers.manager import ProviderManager
from backend.sensor_gateway import SensorGateway
from backend.conflict_engine import ConflictDetectionEngine
from backend.plan_engine import PlanEngine
from backend.main import app

class TestEnterprisePlatform(unittest.TestCase):

    def setUp(self):
        # Create an isolated temporary SQLite database for state tests
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.state_store = RailwayStateStore(db_path=self.temp_db_path)
        self.sensor_gateway = SensorGateway(state_store=self.state_store)
        self.conflict_engine = ConflictDetectionEngine(state_store=self.state_store)
        self.plan_engine = PlanEngine(state_store=self.state_store)
        self.client = TestClient(app)

    def tearDown(self):
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
            wal = self.temp_db_path + "-wal"
            shm = self.temp_db_path + "-shm"
            if os.path.exists(wal):
                os.remove(wal)
            if os.path.exists(shm):
                os.remove(shm)
        except Exception:
            pass

    # =========================================================================
    # 1. PROVIDER FRAMEWORK & AUTHENTICITY TESTS
    # =========================================================================

    def test_unconfigured_rtis_provider(self):
        # RTIS without valid credentials must not fabricate fake live trains
        provider = RTISDataProvider()
        health = provider.get_health()
        self.assertIn(health["state"], ["UNCONFIGURED", "DISCONNECTED", "AUTHENTICATION_REQUIRED"])
        self.assertFalse(provider.is_configured())

    def test_unconfigured_ntes_provider(self):
        # NTES without API key must report unconfigured
        provider = NTESDataProvider()
        health = provider.get_health()
        self.assertIn(health["state"], ["UNCONFIGURED", "DISCONNECTED", "AUTHENTICATION_REQUIRED"])
        self.assertFalse(provider.is_configured())

    def test_unconfigured_ogd_provider(self):
        # OGD without API key must report unconfigured
        provider = OpenDataProvider()
        health = provider.get_health()
        self.assertIn(health["state"], ["UNCONFIGURED", "DISCONNECTED", "AUTHENTICATION_REQUIRED"])
        self.assertFalse(provider.is_configured())

    def test_simulation_provider_explicit_labeling(self):
        # Simulation provider MUST explicitly flag data as SIMULATED
        provider = SimulationDataProvider()
        self.assertTrue(provider.is_configured())
        health = provider.get_health()
        self.assertEqual(health["source"], "SIMULATION")

        # Poll simulation events
        events = asyncio.run(provider.poll())
        self.assertGreater(len(events), 0)
        for ev in events:
            self.assertEqual(ev.source.value, "SIMULATION")
            self.assertIn("DATA SOURCE: SIMULATION", ev.provenance.get("disclaimer", "").upper())

    def test_provider_manager_health_aggregation(self):
        manager = ProviderManager(state_store=self.state_store)
        summary = manager.get_health_summary()
        self.assertIn("status", summary)
        self.assertIn("primary_source", summary)
        self.assertIn("data_quality", summary)
        self.assertIn("providers", summary)
        self.assertIn("rtis", summary["providers"])
        self.assertIn("ntes", summary["providers"])
        self.assertIn("ogd", summary["providers"])
        self.assertIn("simulation", summary["providers"])

    # =========================================================================
    # 2. SENSOR GATEWAY & IOT TELEMETRY TESTS
    # =========================================================================

    def test_sensor_gateway_token_authorization(self):
        token = self.sensor_gateway.auth_token
        self.assertTrue(self.sensor_gateway.validate_token(token))
        self.assertTrue(self.sensor_gateway.validate_token(f"Bearer {token}"))
        self.assertFalse(self.sensor_gateway.validate_token("invalid_token_9999"))
        self.assertFalse(self.sensor_gateway.validate_token(None))

    def test_axle_counter_occupancy_cycle(self):
        sensor_id = "AXL-TEST-01"
        section_id = "A12-B14"

        # 1. Train Entry (48 axles)
        entry_payload = SensorIngestPayload(
            sensor_id=sensor_id,
            sensor_type=SensorType.AXLE_COUNTER,
            section_id=section_id,
            event_type=EventType.SECTION_ENTRY,
            axle_count=48,
            payload={"direction": "IN", "train_id": "12301", "block_id": "BLK-14"}
        )
        res1 = self.sensor_gateway.ingest_payload(entry_payload)
        self.assertEqual(res1["status"], "SUCCESS")

        block = self.state_store.get_block_state("BLK-14")
        self.assertIsNotNone(block)
        self.assertEqual(block.occupancy_state, "OCCUPIED")
        self.assertEqual(block.axle_count_balance, 48)

        # 2. Train Exit (matching 48 axles)
        exit_payload = SensorIngestPayload(
            sensor_id=sensor_id,
            sensor_type=SensorType.AXLE_COUNTER,
            section_id=section_id,
            event_type=EventType.SECTION_EXIT,
            axle_count=48,
            payload={"direction": "OUT", "block_id": "BLK-14"}
        )
        res2 = self.sensor_gateway.ingest_payload(exit_payload)
        self.assertEqual(res2["status"], "SUCCESS")

        block_cleared = self.state_store.get_block_state("BLK-14")
        self.assertEqual(block_cleared.occupancy_state, "CLEAR")
        self.assertEqual(block_cleared.axle_count_balance, 0)

        # 3. Anomaly / Negative balance mismatch test
        mismatch_payload = SensorIngestPayload(
            sensor_id=sensor_id,
            sensor_type=SensorType.AXLE_COUNTER,
            section_id=section_id,
            event_type=EventType.SECTION_EXIT,
            axle_count=24,
            payload={"direction": "OUT", "block_id": "BLK-14"}
        )
        self.sensor_gateway.ingest_payload(mismatch_payload)
        events = self.state_store.get_recent_events(limit=5)
        anomaly_events = [e for e in events if e.event_type.value == "TRACK_ANOMALY"]
        self.assertGreater(len(anomaly_events), 0)

    def test_rail_temperature_threshold_triggers(self):
        sensor_id = "TEMP-TEST-01"
        section_id = "B14-C16"

        # Case A: Normal temperature (42 C)
        normal_p = SensorIngestPayload(
            sensor_id=sensor_id,
            sensor_type=SensorType.RAIL_TEMPERATURE,
            section_id=section_id,
            event_type=EventType.RAIL_TEMPERATURE_ALERT,
            temperature_celsius=42.0,
            payload={"block_id": "BLK-16"}
        )
        self.sensor_gateway.ingest_payload(normal_p)
        block = self.state_store.get_block_state("BLK-16")
        self.assertIn(block.restriction_status, ["NORMAL", "CLEAR"])

        # Case B: Extreme temperature (67 C, exceeds 65 C limit) -> 30 km/h critical restriction
        critical_p = SensorIngestPayload(
            sensor_id=sensor_id,
            sensor_type=SensorType.RAIL_TEMPERATURE,
            section_id=section_id,
            event_type=EventType.RAIL_TEMPERATURE_ALERT,
            temperature_celsius=67.0,
            payload={"block_id": "BLK-16"}
        )
        self.sensor_gateway.ingest_payload(critical_p)
        block = self.state_store.get_block_state("BLK-16")
        self.assertEqual(block.restriction_status, "RESTRICTED")
        self.assertEqual(block.active_speed_limit_kmph, 30.0)

    def test_bridge_water_level_threshold_triggers(self):
        sensor_id = "WL-TEST-01"
        section_id = "BR-TEST"

        # Normal water level (3.2m, below 3.5m caution / 4.5m danger mark)
        normal_p = SensorIngestPayload(
            sensor_id=sensor_id,
            sensor_type=SensorType.BRIDGE_WATER_LEVEL,
            section_id=section_id,
            event_type=EventType.BRIDGE_WATER_ALERT,
            water_level_meters=3.2,
            payload={"block_id": "BLK-BR-01"}
        )
        self.sensor_gateway.ingest_payload(normal_p)
        block = self.state_store.get_block_state("BLK-BR-01")
        self.assertEqual(block.restriction_status, "NORMAL")

        # Danger water level (4.8m, above 4.5m danger mark) -> Emergency closure / 0 km/h
        danger_p = SensorIngestPayload(
            sensor_id=sensor_id,
            sensor_type=SensorType.BRIDGE_WATER_LEVEL,
            section_id=section_id,
            event_type=EventType.BRIDGE_WATER_ALERT,
            water_level_meters=4.8,
            payload={"block_id": "BLK-BR-01"}
        )
        self.sensor_gateway.ingest_payload(danger_p)
        block = self.state_store.get_block_state("BLK-BR-01")
        self.assertEqual(block.restriction_status, "RESTRICTED")
        self.assertEqual(block.active_speed_limit_kmph, 0.0)

    def test_geometry_vibration_alert(self):
        sensor_id = "VIB-TEST-01"
        section_id = "SEC-VIB"

        high_vib_payload = SensorIngestPayload(
            sensor_id=sensor_id,
            sensor_type=SensorType.TRACK_GEOMETRY,
            section_id=section_id,
            event_type=EventType.TRACK_GEOMETRY_DEFECT,
            vibration_g=0.95, # Exceeds 0.8g critical threshold
            payload={"block_id": "BLK-VIB"}
        )
        self.sensor_gateway.ingest_payload(high_vib_payload)
        events = self.state_store.get_recent_events(limit=5)
        geom_events = [e for e in events if "TRACK_GEOMETRY_DEFECT" in e.event_type.value or "VIBRATION" in e.title.upper()]
        self.assertGreater(len(geom_events), 0)

    # =========================================================================
    # 3. CONFLICT ENGINE DETECTION TESTS
    # =========================================================================

    def test_headway_violation_detection(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        t1 = NormalizedTrainState(
            train_id="TR-101",
            train_name="Rajdhani Exp",
            source=EventSource.SIMULATION,
            latitude=28.61,
            longitude=77.20,
            speed_kmph=110.0,
            direction="DOWN",
            current_section="A12-B14",
            status="RUNNING",
            delay_seconds=0,
            timestamp=now_iso,
            received_at=now_iso,
            data_quality=DataQuality.SIMULATED
        )
        t2 = NormalizedTrainState(
            train_id="TR-102",
            train_name="Shatabdi Exp",
            source=EventSource.SIMULATION,
            latitude=28.62,
            longitude=77.21,
            speed_kmph=105.0,
            direction="DOWN",
            current_section="A12-B14",
            status="RUNNING",
            delay_seconds=60,
            timestamp=now_iso,
            received_at=now_iso,
            data_quality=DataQuality.SIMULATED
        )
        self.state_store.upsert_train_state(t1)
        self.state_store.upsert_train_state(t2)

        conflicts = self.conflict_engine.evaluate_corridor()
        headway_conflicts = [c for c in conflicts if c.conflict_type == "HEADWAY_VIOLATION"]
        self.assertGreater(len(headway_conflicts), 0)
        self.assertIn("TR-101", headway_conflicts[0].affected_trains)
        self.assertIn("TR-102", headway_conflicts[0].affected_trains)

    def test_speed_restriction_exceeded(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        section_id = "SPEED-CHECK-SEC"

        blk = BlockState(
            block_id=section_id,
            section_id=section_id,
            occupancy_state="CLEAR",
            restriction_status="RESTRICTED",
            active_speed_limit_kmph=40.0,
            updated_at=now_iso
        )
        self.state_store.upsert_block_state(blk)

        t = NormalizedTrainState(
            train_id="TR-SPEEDING",
            train_name="Fast Goods",
            source=EventSource.SIMULATION,
            speed_kmph=95.0,
            current_section=section_id,
            timestamp=now_iso,
            received_at=now_iso
        )
        self.state_store.upsert_train_state(t)

        conflicts = self.conflict_engine.evaluate_corridor()
        speed_conflicts = [c for c in conflicts if c.conflict_type == "SPEED_RESTRICTION_EXCEEDED"]
        self.assertGreater(len(speed_conflicts), 0)
        self.assertEqual(speed_conflicts[0].affected_trains, ["TR-SPEEDING"])

    def test_unexplained_occupancy_detection(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        section_id = "GHOST-BLOCK"

        blk = BlockState(
            block_id=section_id,
            section_id=section_id,
            occupancy_state="OCCUPIED",
            axle_count_balance=32,
            updated_at=now_iso
        )
        self.state_store.upsert_block_state(blk)

        conflicts = self.conflict_engine.evaluate_corridor()
        unexplained = [c for c in conflicts if "UNEXPLAINED" in c.conflict_type]
        self.assertGreater(len(unexplained), 0)
        self.assertIn(section_id, unexplained[0].affected_blocks)

    def test_schedule_drift_detection(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        t = NormalizedTrainState(
            train_id="TR-DRIFT-01",
            train_name="Express",
            source=EventSource.SIMULATION,
            current_section="C16-D18",
            speed_kmph=50.0,
            delay_seconds=3300, # 55 minutes (> 10 min threshold)
            timestamp=now_iso,
            received_at=now_iso
        )
        self.state_store.upsert_train_state(t)

        conflicts = self.conflict_engine.evaluate_corridor()
        drift_conflicts = [c for c in conflicts if "SCHEDULE_DRIFT" in c.conflict_type]
        self.assertGreater(len(drift_conflicts), 0)
        self.assertIn("TR-DRIFT-01", drift_conflicts[0].affected_trains)

    # =========================================================================
    # 4. PLAN ENGINE & OPERATOR APPROVAL WORKFLOW TESTS
    # =========================================================================

    def test_candidate_plan_lifecycle_and_approval(self):
        # 1. Generate candidate plan via re-optimization
        candidate = self.plan_engine.generate_candidate_plan(
            triggered_by="TEST_SUITE",
            reason="Automated verification test"
        )
        self.assertIsNotNone(candidate)
        self.assertTrue(candidate.plan_id.startswith("PLAN-"))
        self.assertEqual(candidate.status, PlanApprovalStatus.PENDING_APPROVAL)
        self.assertIn(candidate.solver_status, ["OPTIMAL", "FEASIBLE"])

        # Active plan should still be None or unchanged (NOT automatically activated)
        active_before = self.state_store.get_active_plan()
        self.assertTrue(active_before is None or active_before.plan_id != candidate.plan_id)

        # 2. Operator reviews and APPROVES the candidate plan
        approved = self.plan_engine.approve_candidate_plan(
            plan_id=candidate.plan_id,
            reviewer="Chief Traffic Controller test_runner",
            comments="Approved for corridor implementation"
        )
        self.assertEqual(approved.status, PlanApprovalStatus.APPROVED)
        self.assertEqual(approved.reviewed_by, "Chief Traffic Controller test_runner")

        # Now active plan MUST be the newly approved plan
        active_after = self.state_store.get_active_plan()
        self.assertIsNotNone(active_after)
        self.assertEqual(active_after.plan_id, candidate.plan_id)

    def test_candidate_plan_rejection_workflow(self):
        candidate = self.plan_engine.generate_candidate_plan(
            triggered_by="TEST_SUITE",
            reason="Test for rejection"
        )
        self.assertEqual(candidate.status, PlanApprovalStatus.PENDING_APPROVAL)

        rejected = self.plan_engine.reject_candidate_plan(
            plan_id=candidate.plan_id,
            reviewer="Section Controller",
            reason="Corridor traffic density too high; request rescheduled window."
        )
        self.assertEqual(rejected.status, PlanApprovalStatus.REJECTED)

        retrieved = self.state_store.get_plan_version(candidate.plan_id)
        self.assertEqual(retrieved.status, PlanApprovalStatus.REJECTED)

        with self.assertRaises(ValueError):
            self.plan_engine.approve_candidate_plan(candidate.plan_id)

    # =========================================================================
    # 5. REST API ENDPOINTS VIA FASTAPI TESTCLIENT
    # =========================================================================

    def test_api_providers_health(self):
        res = self.client.get("/api/v1/providers/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("providers", data)
        self.assertIn("status", data)

    def test_api_sensor_token_authentication(self):
        payload = {
            "sensor_id": "AXL-API-01",
            "sensor_type": "AXLE_COUNTER",
            "section_id": "A12-B14",
            "event_type": "SECTION_ENTRY",
            "axle_count": 24,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"direction": "IN", "block_id": "BLK-14"}
        }
        # POST without token should return 401
        res_no_token = self.client.post("/api/v1/events/sensor", json=payload)
        self.assertEqual(res_no_token.status_code, 401)

        # POST with valid token should return 200
        valid_token = self.sensor_gateway.auth_token
        res_with_token = self.client.post(
            "/api/v1/events/sensor",
            json=payload,
            headers={"X-Sensor-Token": valid_token}
        )
        self.assertEqual(res_with_token.status_code, 200)
        data = res_with_token.json()
        self.assertEqual(data["status"], "SUCCESS")

    def test_api_sensors_and_telemetry(self):
        res = self.client.get("/api/v1/sensors")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_api_live_trains(self):
        res = self.client.get("/api/v1/trains/live")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_api_blocks_state(self):
        res = self.client.get("/api/v1/blocks/state")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_api_conflicts(self):
        res = self.client.get("/api/v1/conflicts")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_api_plans_reoptimization_and_approval_flow(self):
        res_opt = self.client.post(
            "/api/v1/plans/reoptimize",
            params={"reason": "Integration Test Reoptimization"}
        )
        self.assertEqual(res_opt.status_code, 200)
        plan_data = res_opt.json()
        plan_id = plan_data["plan_id"]
        self.assertEqual(plan_data["status"], "PENDING_APPROVAL")

        res_cand = self.client.get("/api/v1/plans/candidate")
        self.assertEqual(res_cand.status_code, 200)
        cand_data = res_cand.json()
        self.assertIsNotNone(cand_data)
        self.assertEqual(cand_data["plan_id"], plan_id)

        approval_body = {
            "decision": "APPROVE",
            "operator_name": "Chief Controller Integration Test",
            "comments": "Approved via REST API test"
        }
        res_appr = self.client.post(f"/api/v1/plans/{plan_id}/approve", json=approval_body)
        self.assertEqual(res_appr.status_code, 200)
        self.assertEqual(res_appr.json()["status"], "APPROVED")

        res_active = self.client.get("/api/v1/plans/active")
        self.assertEqual(res_active.status_code, 200)
        self.assertEqual(res_active.json()["plan_id"], plan_id)

    def test_api_simulation_disturbance_injection(self):
        dist_body = {
            "disturbance_type": "TRAIN_DELAY",
            "target_id": "12301",
            "value": 300
        }
        res = self.client.post("/api/v1/simulation/inject-disturbance", json=dist_body)
        self.assertEqual(res.status_code, 200)
        res_data = res.json()
        self.assertEqual(res_data["status"], "SUCCESS")
        self.assertIn("event", res_data)

if __name__ == "__main__":
    unittest.main()
