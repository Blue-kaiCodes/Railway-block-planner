# Railway Block Planner — Enterprise Real-Time Platform

## SIH 2026 — Problem Statement 26027
**AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations on Indian Railways**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Google OR-Tools](https://img.shields.io/badge/Google%20OR--Tools-CP--SAT-orange.svg)](https://developers.google.com/optimization)
[![Tests Passing](https://img.shields.io/badge/tests-32%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Overview

Indian Railways operates thousands of passenger and freight services daily over congested trunk corridors (e.g. Howrah – Pt. Deen Dayal Upadhyaya on the Grand Chord). To maintain permanent way infrastructure, signaling interlockings, and overhead traction (OHE), engineering gangs must take track sections offline ("maintenance blocks").

The **Railway Block Planner** has evolved from an initial timetable deconfliction tool into an **enterprise-grade, real-time decision-support platform**. It integrates authenticated external railway feeds (CRIS/ISRO RTIS, NTES), trackside IoT sensor telemetry (Axle Counters, Continuous Rail Temperature, Bridge Pier Water Level Gauges, Track Accelerometers), an atomic SQLite WAL state store, continuous corridor conflict detection, Google OR-Tools CP-SAT re-optimization, and an explicit **Chief Traffic Controller Approval Workflow**.

> [!IMPORTANT]
> **Strict Operational Authenticity**:
> The system enforces zero fabricated live data. When external CRIS or NTES credentials are unconfigured, feeds enter `AUTHENTICATION REQUIRED` or `UNAVAILABLE` state without generating synthetic live trains. An optional development simulation provider is provided for offline testing, strictly labeled with `data_quality: SIMULATED` and prominent disclaimer banners.

---

## 2. Key Capabilities & Architecture

```
                          ┌────────────────────────┐
                          │   CRIS / ISRO RTIS     │ (Locomotive GPS Telemetry via mTLS/OAuth2)
                          └───────────┬────────────┘
                          ┌───────────▼────────────┐
                          │  IR NTES / API Setu    │ (Timetables & Station Delay Tracking)
                          └───────────┬────────────┘
                          ┌───────────▼────────────┐
                          │ Trackside IoT Sensors  │ (Axle Counters, Temp, Water Level, Vibration)
                          └───────────┬────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │       CANONICAL RAILWAY STATE STORE (SQLite WAL) │
             │  Microsecond ACID telemetry storage & history    │
             └────────────────────────┬─────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │         CORRIDOR CONFLICT DETECTION ENGINE       │
             │  Headway, Speed Violations, Ghost Occupancies    │
             └────────────────────────┬─────────────────────────┘
                                      │ Triggers Re-Optimization
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │      GOOGLE OR-TOOLS CP-SAT RE-OPTIMIZER         │
             │  Deterministic integer programming solver        │
             └────────────────────────┬─────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │       CANDIDATE PLAN GATEWAY & OPERATOR APPROVAL │
             │  PLAN-00X versioning, Plan Diffs, Sign-off Gate  │
             └────────────────────────┬─────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │    CHIEF CONTROLLER CONSOLE & REST API V1        │
             │  Dark console UI, Live Fleet Grid, IoT Matrix    │
             └──────────────────────────────────────────────────┘
```

- **Live Fleet Tracking**: Ingests high-frequency locomotive coordinates, velocity, direction, and delay seconds.
- **Trackside IoT Gateway**: Authenticated (`X-Sensor-Token`) endpoint evaluating axle counts, track buckling risks ($>55^\circ\text{C}$ / $>65^\circ\text{C}$), bridge flooding ($>3.5\text{m}$ / $>4.5\text{m}$ Danger Level), and track geometry acceleration ($>0.8\text{g}$).
- **Continuous Conflict Detection**: Real-time evaluation of headway infractions, speed restriction exceedances, unexplained occupancies, and schedule drift cascades.
- **Dynamic Re-Optimization**: Google OR-Tools CP-SAT re-allocates maintenance possessions dynamically when corridor conditions change.
- **Versioned Candidate Plans & Sign-Off**: Generates candidate plans (`PLAN-001`, `PLAN-002`) in `PENDING_APPROVAL` status with shift diffs. The Chief Traffic Controller reviews and executes digital sign-off (`APPROVED` or `REJECTED`) before any schedule becomes active.
- **Decision Support Independence**: Operates strictly as a decision-support advisory system without replacing physical safety interlocking.

---

## 3. Technology Stack

- **Backend Runtime**: Python 3.11+ / 3.14
- **API Framework**: FastAPI, Pydantic v2, Starlette, Uvicorn, HTTPX
- **Optimization Engine**: Google OR-Tools (Constraint Programming - Satisfiability CP-SAT)
- **Data Persistence**: SQLite 3 with Write-Ahead Logging (WAL) mode & thread-safe re-entrant locks
- **Frontend Console**: Vanilla ES6+ JavaScript, CSS3 Grid (Indian Railways dark console theme, Inter font), FontAwesome 6
- **Testing**: Python Standard Library `unittest` with FastAPI `TestClient` (32 passing automated tests)

---

## 4. Quick Start

### 4.1 Prerequisites & Installation

Clone repository and set up virtual environment:
```bash
git clone https://github.com/Blue-kaiCodes/Railway-block-planner.git
cd Railway-block-planner

python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 4.2 Configuration

Copy the production configuration template:
```bash
cp .env.example .env
```
Configure your credentials in `.env` (or leave defaults for local simulation mode).

### 4.3 Launch Application

Start the backend server:
```bash
python run_app.py
```
Open your browser and navigate to:
- **Operator Console Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 5. Automated Verification & Test Suite

Run the full automated test suite (32 tests covering optimizer mathematics, provider circuit breakers, sensor gateway thresholds, conflict detection, plan versioning, and REST endpoints):

```bash
# Run Core CP-SAT Solver and Database Tests
python -m backend.test_optimizer

# Run Enterprise Real-Time Platform Tests
python -m tests.test_enterprise_platform
```

Both test suites execute in $< 3.0$ seconds with $100\%$ pass rate.

---

## 6. Comprehensive Documentation Directory

| Document | Description |
| :--- | :--- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Enterprise system architecture, data flows, and component breakdown. |
| [docs/LIVE_DATA.md](docs/LIVE_DATA.md) | Integration specifications for CRIS/ISRO RTIS, NTES, and data.gov.in. |
| [docs/SENSOR_GATEWAY.md](docs/SENSOR_GATEWAY.md) | IoT sensor specs, authentication, and threshold definitions. |
| [docs/API.md](docs/API.md) | OpenAPI v1 endpoint reference with request/response payloads. |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production Linux systemd, Nginx reverse proxy, and hot backup guide. |

---

## 7. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
