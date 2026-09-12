# Railway Block Planner

## SIH 2026 — Problem Statement 26027
**AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations on Indian Railways**

---

## Overview

### The Problem
Indian Railways operates thousands of passenger and freight trains daily over heavily congested trunk corridors. To keep railway infrastructure safe and functional, maintenance departments—primarily **Civil Engineering (Track/Bridges)**, **Signal & Telecom (S&T)**, and **Electrical Traction (OHE)**—must take track sections offline ("maintenance blocks"). 

Historically, these departments have submitted block requests independently through departmental channels. Without automated synchronization across departments or against the live train operating timetable, railway controllers face severe operational friction:
- Uncoordinated maintenance requests conflict with express train paths.
- Multiple departments demand blocks on the same track section at different times instead of coordinating integrated possessions.
- Manual planning results in train detentions, compromised safety margins, and maintenance backlogs.

### What the Application Does
The **Railway Block Planner** is a deterministic decision-support application built for railway corridor operations. It automates the allocation of maintenance blocks across corridor sections by:
1. Reconciling departmental maintenance demands with train timetable schedules.
2. Formulating the scheduling problem as an exact mathematical constraint satisfaction problem.
3. Guaranteeing zero collisions between train movements and scheduled track blocks.
4. Dynamically re-optimizing schedules upon emergency defect injection with minimal disruption to unaffected work.
5. Providing plain-English audit justifications for every allocation decision.

---

## Features

- **Corridor Timeline & Gantt View**: 24-hour visual schedule displaying train paths (Express/Freight) alongside scheduled departmental maintenance blocks across five corridor sections (`A12-B14` through `D15-E20`).
- **Interactive Detail Inspection**: Click any train path or maintenance block on the Gantt chart to inspect timetable protections, asset health, crew allocation, and audit reasoning.
- **Full Maintenance Task Management (CRUD)**: Create, edit, delete, duplicate, search, filter, and sort maintenance tasks across Engineering, S&T, and Traction departments.
- **Master Train Timetable Management**: Add, update, and delete scheduled train services with arrival/departure windows and priority classifications.
- **Block Windows Management**: Configure corridor maintenance windows and allowable departmental work types.
- **Google OR-Tools CP-SAT Optimizer**: Deterministic solver enforcing zero train collisions, single-track occupancy, and departmental crew capacity limits.
- **Live Emergency Defect Re-Optimization**: Simulate emergency track defects (e.g. ultrasonic rail fracture detection) with minimal-disruption rescheduling.
- **Interactive Plan Diff & Rollback**: Compare schedule changes before and after re-optimization, with one-click rollback to previous plan snapshots.
- **Algorithmic Baseline Comparison**: Compare optimized schedules against an uncoordinated First-Come, First-Served (FCFS) manual baseline to quantify conflict and delay reductions.
- **Plain-English Explainability Engine**: Human-readable audit trails detailing why each task was assigned to its specific time window.
- **CSV Plan Export**: Download scheduled block orders formatted for field maintenance gangs.

---

## Architecture

```
Frontend (HTML5 / Vanilla ES6+ / CSS Grid)
    │
    ▼  REST JSON APIs
Backend API (FastAPI / Pydantic)
    │
    ├────────► Constraint Optimization Engine (Google OR-Tools CP-SAT)
    │
    ├────────► Baseline Simulator (FCFS Uncoordinated Benchmark)
    │
    ├────────► Explainability Engine (Natural Language Audit Log)
    │
    └────────► Data Layer (Thread-Safe File-Backed JSON Store)
```

For detailed architectural diagrams and data flows, see [docs/architecture.md](docs/architecture.md).

---

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, Pydantic, Uvicorn
- **Optimization Solver**: Google OR-Tools (CP-SAT Constraint Programming Solver)
- **Frontend**: Vanilla HTML5, CSS3 (Inter typography, responsive grid), Modern JavaScript (ES6+), FontAwesome 6 (CDN)
- **Data Layer**: File-backed JSON repository (`data/datastore.json`)

---

## Project Structure

```
railway-block-planner/
│
├── README.md               # Project documentation
├── LICENSE                 # MIT License
├── .gitignore              # Git ignore configuration
├── .env.example            # Environment configuration template
├── requirements.txt        # Python dependencies
├── run_app.py              # Application launcher script
├── start.bat               # Windows batch launcher
│
├── backend/
│   ├── main.py             # FastAPI server, REST API endpoints, static file mounting
│   ├── optimizer.py        # Google OR-Tools CP-SAT scheduling model
│   ├── baseline_solver.py  # Algorithmic FCFS baseline comparison model
│   ├── explainability.py   # Decision explanation and audit generator
│   ├── database.py         # Thread-safe JSON data store and snapshot management
│   ├── schemas.py          # Pydantic data schemas and validation models
│   ├── synthetic_data.py   # Default corridor topology, assets, and seed data
│   └── test_optimizer.py   # Automated test suite
│
├── data/
│   └── datastore.json      # Persistent JSON database
│
├── docs/
│   ├── architecture.md     # System architecture and layer specifications
│   └── optimization.md     # Mathematical formulation and solver constraints
│
└── frontend/
    ├── index.html          # Single-page interface markup
    ├── styles.css          # Design system, layout, and component styles
    └── app.js              # Application state, UI interactions, API client
```

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Git (optional, for cloning)

### Setup Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/railway-block-planner.git
   cd railway-block-planner
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running Locally

### Option 1: One-Click Launcher (Windows)
Double-click `start.bat`, or execute:
```bash
python run_app.py
```
This starts the Uvicorn server and automatically opens `http://127.0.0.1:8000` in your default web browser.

### Option 2: Direct Uvicorn Command
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Then navigate to `http://127.0.0.1:8000` in any modern web browser.

---

## Environment Variables

Copy `.env.example` to `.env` if custom server settings are needed:
```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `HOST` | `127.0.0.1` | Network interface for FastAPI/Uvicorn |
| `PORT` | `8000` | Port number for FastAPI/Uvicorn |
| `ENVIRONMENT` | `development` | Runtime environment flag |

---

## Demo Walkthrough

1. **Generate Optimized Plan**: Click **"Generate Plan"** in the top header. The CP-SAT solver assigns maintenance tasks into valid corridor block windows while enforcing zero train collisions.
2. **Inspect Schedule Details**: Click any train block or maintenance slot on the Gantt chart to open the item drawer with full timetable and audit details.
3. **Inject Operational Defect**: Click **"Inject Defect"**, choose a corridor section, defect classification, duration, and deadline. The solver recalculates the schedule, prioritizing the defect with minimal disruption to unaffected tasks.
4. **View Plan Diff**: After defect injection, review the Plan Diff dialog detailing newly scheduled, rescheduled, and unchanged blocks.
5. **Revert Plan**: Click **"Revert Plan"** to restore the schedule state prior to defect injection.
6. **Compare Baseline**: Navigate to the **"Baseline Benchmark"** tab to see side-by-side performance metrics between the uncoordinated manual baseline and the CP-SAT optimized schedule.
7. **Export Schedule**: Click **"Export Plan"** to download a CSV file of the active maintenance block schedule.

---

## Running Automated Tests

To execute the verification test suite:
```bash
python -m unittest backend/test_optimizer.py
```
The test suite validates:
- Thread-safe CRUD operations in the database layer.
- Mathematical zero-collision guarantees of the CP-SAT optimizer.
- Baseline benchmark calculations.
- Emergency defect injection and snapshot rollback integrity.

---

## Dataset

The corridor topology, asset inventory, maintenance requests, and train timetables provided in this application are **representative synthetic datasets** based on the **Howrah – Pt. Deen Dayal Upadhyaya Trunk Corridor** (Eastern Railway / East Central Railway). They reflect realistic operational speeds, asset aging characteristics, and timetable density patterns for demonstration purposes.

---

## Limitations

- **Prototype Scope**: This software is an engineering decision-support prototype developed for Smart India Hackathon 2026. It does not directly interface with live railway interlocking systems or Centralised Traffic Control (CTC) signalling hardware.
- **Corridor Abstraction**: Station interlocking yards, passing loops, and bidirectional signalling nuances are modeled as unified corridor track sections with capacity constraints.

---

## Future Scope

- **Live TMS/COA Integration**: Direct API connectors to Indian Railways' Control Office Application (COA) and Track Management System (TMS).
- **Stochastic Delay Modeling**: Real-time GPS train delay feed integration for rolling-horizon re-optimization.
- **Machine Learning Failure Predictors**: Integration with acoustic/ultrasonic flaw detection feeds for automated condition-based maintenance task generation.

---

## Team

- **Smart India Hackathon 2026**
- **Problem Statement PS 26027**
