from typing import List, Dict, Any

def get_initial_dataset() -> Dict[str, Any]:
    sections = [
        {"id": "A12-B14", "name": "Howrah - Bardhaman Line", "length_km": 95, "tracks": 2, "max_speed_kmh": 130},
        {"id": "B14-C02", "name": "Bardhaman - Asansol Line", "length_km": 106, "tracks": 2, "max_speed_kmh": 130},
        {"id": "C02-C08", "name": "Asansol - Dhanbad Line", "length_km": 60, "tracks": 2, "max_speed_kmh": 110},
        {"id": "C08-D15", "name": "Dhanbad - Gaya Line", "length_km": 201, "tracks": 2, "max_speed_kmh": 130},
        {"id": "D15-E20", "name": "Gaya - Pt. Deen Dayal Upadhyaya Line", "length_km": 204, "tracks": 2, "max_speed_kmh": 130},
    ]

    assets = [
        {"id": "AST-101", "type": "Track Rail Joint", "section": "A12-B14", "age_years": 8.5, "criticality": "HIGH", "last_maintenance": "2026-03-12", "health_score": 62.0},
        {"id": "AST-102", "type": "Point Switch #14B", "section": "A12-B14", "age_years": 12.0, "criticality": "CRITICAL", "last_maintenance": "2025-11-05", "health_score": 45.0},
        {"id": "AST-201", "type": "Automatic Interlocking Signal", "section": "B14-C02", "age_years": 4.2, "criticality": "MEDIUM", "last_maintenance": "2026-06-01", "health_score": 78.0},
        {"id": "AST-202", "type": "OHE Overhead Line Support #88", "section": "B14-C02", "age_years": 9.1, "criticality": "HIGH", "last_maintenance": "2026-02-18", "health_score": 58.0},
        {"id": "AST-301", "type": "Track Bed Ballast", "section": "C02-C08", "age_years": 15.0, "criticality": "CRITICAL", "last_maintenance": "2025-08-20", "health_score": 38.0},
        {"id": "AST-302", "type": "Axle Counter Sensor Unit", "section": "C02-C08", "age_years": 2.5, "criticality": "MEDIUM", "last_maintenance": "2026-07-10", "health_score": 88.0},
        {"id": "AST-401", "type": "Traction Transformer Substation", "section": "C08-D15", "age_years": 11.2, "criticality": "HIGH", "last_maintenance": "2026-01-14", "health_score": 52.0},
        {"id": "AST-501", "type": "Girder Railway Bridge #42", "section": "D15-E20", "age_years": 24.0, "criticality": "CRITICAL", "last_maintenance": "2025-09-30", "health_score": 41.0},
    ]

    tasks = [
        {
            "id": "TSK-001",
            "asset_id": "AST-102",
            "section": "A12-B14",
            "department": "Engineering",
            "task_type": "Switch & Crossover Deep Overhaul",
            "duration_mins": 120,
            "priority": "CRITICAL",
            "deadline_hour": 10.0,
            "status": "PENDING",
            "risk_score": 92.0,
            "description": "Urgent rail switch realignment required on Down Line to prevent speed restrictions."
        },
        {
            "id": "TSK-002",
            "asset_id": "AST-202",
            "section": "B14-C02",
            "department": "Traction / OHE",
            "task_type": "OHE Catenary Wire Cantilever Adjustment",
            "duration_mins": 90,
            "priority": "HIGH",
            "deadline_hour": 14.0,
            "status": "PENDING",
            "risk_score": 75.0,
            "description": "Overhead contact wire height deviation detected during high-speed pantograph test."
        },
        {
            "id": "TSK-003",
            "asset_id": "AST-201",
            "section": "B14-C02",
            "department": "Signal & Telecom",
            "task_type": "Relay Interlocking Calibration",
            "duration_mins": 60,
            "priority": "MEDIUM",
            "deadline_hour": 18.0,
            "status": "PENDING",
            "risk_score": 55.0,
            "description": "Periodic calibration of automatic block signaling relays."
        },
        {
            "id": "TSK-004",
            "asset_id": "AST-301",
            "section": "C02-C08",
            "department": "Engineering",
            "task_type": "Ballast Cleaning Machine (BCM) Deep Tamping",
            "duration_mins": 150,
            "priority": "CRITICAL",
            "deadline_hour": 8.0,
            "status": "PENDING",
            "risk_score": 88.0,
            "description": "Heavy track bed settlement; required before monsoon speed clearance."
        },
        {
            "id": "TSK-005",
            "asset_id": "AST-401",
            "section": "C08-D15",
            "department": "Traction / OHE",
            "task_type": "Substation Circuit Breaker Replacement",
            "duration_mins": 105,
            "priority": "HIGH",
            "deadline_hour": 16.0,
            "status": "PENDING",
            "risk_score": 72.0,
            "description": "Preventive replacement of thermal damaged vacuum circuit breaker."
        },
        {
            "id": "TSK-006",
            "asset_id": "AST-501",
            "section": "D15-E20",
            "department": "Engineering",
            "task_type": "Bridge Pier Expansion Joint Inspection",
            "duration_mins": 90,
            "priority": "HIGH",
            "deadline_hour": 20.0,
            "status": "PENDING",
            "risk_score": 68.0,
            "description": "Structural vibration check and bolt tightening on main girder bridge."
        },
        {
            "id": "TSK-007",
            "asset_id": "AST-302",
            "section": "C02-C08",
            "department": "Signal & Telecom",
            "task_type": "Track Circuit Sensor Calibration",
            "duration_mins": 45,
            "priority": "LOW",
            "deadline_hour": 22.0,
            "status": "PENDING",
            "risk_score": 35.0,
            "description": "Routine diagnostic test of digital axle counters."
        }
    ]

    trains = [
        {"train_id": "12301", "train_name": "Howrah Rajdhani Express", "origin": "Howrah Jn (HWH)", "destination": "New Delhi (NDLS)", "section": "A12-B14", "arrival_hour": 0.5, "departure_hour": 1.75, "service_priority": 1},
        {"train_id": "12301", "train_name": "Howrah Rajdhani Express", "origin": "Howrah Jn (HWH)", "destination": "New Delhi (NDLS)", "section": "B14-C02", "arrival_hour": 1.8, "departure_hour": 3.0, "service_priority": 1},
        {"train_id": "12301", "train_name": "Howrah Rajdhani Express", "origin": "Howrah Jn (HWH)", "destination": "New Delhi (NDLS)", "section": "C02-C08", "arrival_hour": 3.1, "departure_hour": 4.0, "service_priority": 1},
        {"train_id": "12259", "train_name": "Sealdah Duronto Express", "origin": "Sealdah (SDAH)", "destination": "Bikaner Jn (BKN)", "section": "A12-B14", "arrival_hour": 6.0, "departure_hour": 7.2, "service_priority": 1},
        {"train_id": "12259", "train_name": "Sealdah Duronto Express", "origin": "Sealdah (SDAH)", "destination": "Bikaner Jn (BKN)", "section": "B14-C02", "arrival_hour": 7.3, "departure_hour": 8.5, "service_priority": 1},
        {"train_id": "12305", "train_name": "Kolkata Rajdhani Express", "origin": "Howrah Jn (HWH)", "destination": "New Delhi (NDLS)", "section": "C08-D15", "arrival_hour": 10.0, "departure_hour": 11.5, "service_priority": 1},
        {"train_id": "12305", "train_name": "Kolkata Rajdhani Express", "origin": "Howrah Jn (HWH)", "destination": "New Delhi (NDLS)", "section": "D15-E20", "arrival_hour": 11.6, "departure_hour": 13.0, "service_priority": 1},
        {"train_id": "12313", "train_name": "Sealdah Rajdhani Express", "origin": "Sealdah (SDAH)", "destination": "New Delhi (NDLS)", "section": "A12-B14", "arrival_hour": 16.5, "departure_hour": 17.8, "service_priority": 1},
        {"train_id": "12313", "train_name": "Sealdah Rajdhani Express", "origin": "Sealdah (SDAH)", "destination": "New Delhi (NDLS)", "section": "B14-C02", "arrival_hour": 17.9, "departure_hour": 19.1, "service_priority": 1},

        {"train_id": "13005", "train_name": "Amritsar Mail", "origin": "Howrah Jn (HWH)", "destination": "Amritsar Jn (ASR)", "section": "A12-B14", "arrival_hour": 8.0, "departure_hour": 9.5, "service_priority": 2},
        {"train_id": "13005", "train_name": "Amritsar Mail", "origin": "Howrah Jn (HWH)", "destination": "Amritsar Jn (ASR)", "section": "B14-C02", "arrival_hour": 9.6, "departure_hour": 11.0, "service_priority": 2},
        {"train_id": "13005", "train_name": "Amritsar Mail", "origin": "Howrah Jn (HWH)", "destination": "Amritsar Jn (ASR)", "section": "C02-C08", "arrival_hour": 11.1, "departure_hour": 12.2, "service_priority": 2},
        {"train_id": "12381", "train_name": "Poorva Express", "origin": "Howrah Jn (HWH)", "destination": "New Delhi (NDLS)", "section": "C08-D15", "arrival_hour": 13.5, "departure_hour": 15.2, "service_priority": 2},
        {"train_id": "12381", "train_name": "Poorva Express", "origin": "Howrah Jn (HWH)", "destination": "New Delhi (NDLS)", "section": "D15-E20", "arrival_hour": 15.3, "departure_hour": 17.0, "service_priority": 2},

        {"train_id": "N-BOST", "train_name": "Coal Rake Freight Special", "origin": "Dhanbad Goods Yard", "destination": "Kolaghat Thermal Plant", "section": "C02-C08", "arrival_hour": 5.0, "departure_hour": 6.8, "service_priority": 3},
        {"train_id": "N-BOXN", "train_name": "Container Freight Express", "origin": "Kolkata Port Terminal", "destination": "Dadri ICD", "section": "C08-D15", "arrival_hour": 7.0, "departure_hour": 9.0, "service_priority": 3},
        {"train_id": "N-BCN", "train_name": "Foodgrain Special Freight", "origin": "FCI Godown Mughalsarai", "destination": "FCI Godown Dankuni", "section": "D15-E20", "arrival_hour": 18.0, "departure_hour": 20.0, "service_priority": 3},
    ]

    block_windows = [
        {"id": "BLK-101", "section": "A12-B14", "start_hour": 2.0, "end_hour": 5.5, "permitted_departments": ["Engineering", "Signal & Telecom", "Traction / OHE"], "max_duration_mins": 210, "status": "AVAILABLE"},
        {"id": "BLK-102", "section": "A12-B14", "start_hour": 10.0, "end_hour": 16.0, "permitted_departments": ["Engineering", "Signal & Telecom"], "max_duration_mins": 360, "status": "AVAILABLE"},
        
        {"id": "BLK-201", "section": "B14-C02", "start_hour": 3.2, "end_hour": 7.0, "permitted_departments": ["Engineering", "Traction / OHE"], "max_duration_mins": 228, "status": "AVAILABLE"},
        {"id": "BLK-202", "section": "B14-C02", "start_hour": 11.5, "end_hour": 17.0, "permitted_departments": ["Signal & Telecom", "Traction / OHE"], "max_duration_mins": 330, "status": "AVAILABLE"},

        {"id": "BLK-301", "section": "C02-C08", "start_hour": 0.5, "end_hour": 3.0, "permitted_departments": ["Engineering", "Signal & Telecom"], "max_duration_mins": 150, "status": "AVAILABLE"},
        {"id": "BLK-302", "section": "C02-C08", "start_hour": 12.5, "end_hour": 16.0, "permitted_departments": ["Engineering", "Traction / OHE", "Signal & Telecom"], "max_duration_mins": 210, "status": "AVAILABLE"},

        {"id": "BLK-401", "section": "C08-D15", "start_hour": 1.0, "end_hour": 6.5, "permitted_departments": ["Traction / OHE", "Engineering"], "max_duration_mins": 330, "status": "AVAILABLE"},
        {"id": "BLK-402", "section": "C08-D15", "start_hour": 15.5, "end_hour": 20.0, "permitted_departments": ["Signal & Telecom", "Traction / OHE"], "max_duration_mins": 270, "status": "AVAILABLE"},

        {"id": "BLK-501", "section": "D15-E20", "start_hour": 2.0, "end_hour": 7.0, "permitted_departments": ["Engineering", "Signal & Telecom"], "max_duration_mins": 300, "status": "AVAILABLE"},
        {"id": "BLK-502", "section": "D15-E20", "start_hour": 13.5, "end_hour": 15.0, "permitted_departments": ["Engineering", "Traction / OHE"], "max_duration_mins": 90, "status": "AVAILABLE"},
    ]

    resources = [
        {"id": "RES-ENG-1", "department": "Engineering", "skill": "Track Heavy Maintenance Gang", "team_name": "Howrah Track Unit 1", "available_start_hour": 0.0, "available_end_hour": 24.0},
        {"id": "RES-ENG-2", "department": "Engineering", "skill": "Bridge & Structural Team", "team_name": "Dhanbad Bridge Unit", "available_start_hour": 0.0, "available_end_hour": 24.0},
        {"id": "RES-ST-1", "department": "Signal & Telecom", "skill": "Automatic Interlocking Crew", "team_name": "Bardhaman Signal Gang", "available_start_hour": 0.0, "available_end_hour": 24.0},
        {"id": "RES-ST-2", "department": "Signal & Telecom", "skill": "Axle & Sensor Diagnostics", "team_name": "Asansol Telecom Unit", "available_start_hour": 0.0, "available_end_hour": 24.0},
        {"id": "RES-OHE-1", "department": "Traction / OHE", "skill": "Tower Wagon Electrical Crew", "team_name": "Howrah Traction Wing", "available_start_hour": 0.0, "available_end_hour": 24.0},
        {"id": "RES-OHE-2", "department": "Traction / OHE", "skill": "Substation High-Voltage Team", "team_name": "Gaya Electrical Substation Crew", "available_start_hour": 0.0, "available_end_hour": 24.0},
    ]

    incidents = [
        {"id": "INC-801", "severity": "HIGH", "detected_at": "2026-09-10 05:45", "section": "A12-B14", "description": "Minor track gauge widening observed near switch 14B.", "status": "UNSCHEDULED"}
    ]

    return {
        "sections": sections,
        "assets": assets,
        "tasks": tasks,
        "trains": trains,
        "block_windows": block_windows,
        "resources": resources,
        "incidents": incidents
    }
