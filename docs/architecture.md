# System Architecture

## Overview
The **Railway Block Planner** is designed as a lightweight, deterministic decision-support system for railway corridor operations. It synchronizes departmental maintenance requests across Engineering, Signal & Telecom (S&T), and Traction (OHE) with master passenger and freight train timetables.

## Component Breakdown

\\\
┌─────────────────────────────────────────────────────────────────┐
│                    Web Browser Interface                        │
│   (Vanilla ES6+ JavaScript, Responsive Grid CSS, FontAwesome)    │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP REST JSON APIs
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application Server                   │
│   - Static File Serving (/)                                   │
│   - Dataset & Stats Endpoints (/api/dataset, /api/stats)    │
│   - Task, Train, and Block CRUD (/api/tasks, /api/trains)  │
│   - Dynamic Optimization Handlers (/api/optimize)             │
│   - Emergency Defect Injection & Rollback                       │
└───────┬───────────────────────┬─────────────────────────┬───────┘
        │                       │                         │
        ▼                       ▼                         ▼
┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│  Data Repository │  │  Google OR-Tools │  │ Baseline Benchmark  │
│  (JSON File-     │  │  CP-SAT Solver   │  │ Simulator (FCFS     │
│  Backed Store)   │  │  (Constraint     │  │ Uncoordinated       │
│  datastore.json│  │   Optimization)  │  │ Departmental Model) │
└──────────────────┘  └──────────────────┘  └─────────────────────┘
                                │
                                ▼
                      ┌──────────────────┐
                      │  Explainability  │
                      │  Audit Engine    │
                      │  (Plain-English  │
                      │   Decision Log)  │
                      └──────────────────┘
\\\

### 1. Presentation Layer (rontend/)
- Single-page application built with clean HTML5, custom CSS (Inter typography, responsive data density, zero bloated external JS frameworks), and modern JavaScript.
- Interactive components:
  - Corridor timeline Gantt chart with interactive inspection drawers.
  - CRUD modals for maintenance tasks, train timetables, block windows, and emergency defect injection.
  - Multi-criteria task filtering, text search, and column sorting.
  - Tab views for operations overview, corridor topology, audit logs, benchmark comparisons, and plan history.

### 2. API & Routing Layer (ackend/main.py)
- Powered by FastAPI, exposing type-safe REST endpoints validated with Pydantic schemas (ackend/schemas.py).
- Manages CORS, asynchronous request handling, CSV export streaming, and atomic plan rollback states.

### 3. Constraint Optimization Engine (ackend/optimizer.py)
- Implemented using Google OR-Tools CP-SAT (Constraint Programming - Satisfiability).
- Formulates maintenance block scheduling as an integer programming problem with strict hard constraints (zero train collisions, single track occupancy, department-window compatibility, daily crew gang limits) and multi-term objective functions.

### 4. Baseline Simulation Engine (ackend/baseline_solver.py)
- Simulates real-world legacy operations where individual departments request and receive blocks on a first-come, first-served basis during shift mobilization hours without automated timetable conflict checking.
- Computes empirical conflict counts, train delay minutes, and corridor window utilization to provide a mathematically grounded benchmark against the CP-SAT optimizer.

### 5. Data Persistence (ackend/database.py)
- Thread-safe, file-backed repository (data/datastore.json) providing instant state persistence across sessions and browser reloads.
- Includes pre-optimization snapshotting to support one-click rollback following emergency rescheduling.
