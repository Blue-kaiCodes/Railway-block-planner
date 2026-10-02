# System Architecture & Technical Specifications

> The comprehensive enterprise technical specifications and architecture diagrams are documented in **[docs/ARCHITECTURE.md](ARCHITECTURE.md)**.
>
> Complementary architectural guides:
> - **[docs/LIVE_DATA.md](LIVE_DATA.md)**: CRIS/ISRO RTIS and NTES Integration Specifications.
> - **[docs/SENSOR_GATEWAY.md](SENSOR_GATEWAY.md)**: Trackside IoT Telemetry & Threshold Definitions.
> - **[docs/API.md](API.md)**: REST API V1 OpenAPI Reference.
> - **[docs/DEPLOYMENT.md](DEPLOYMENT.md)**: Production Deployment & Systemd Operations Guide.

---

## High-Level Operational Architecture

The **Railway Block Planner** operates on a modular, multi-tier architecture designed for continuous real-time decision support on dense Indian Railways corridors:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Web Browser Interface                        │
│   (Vanilla ES6+ JavaScript, Responsive Grid CSS, FontAwesome)    │
│   - Provider Health & Authenticity Status Pill                  │
│   - Live Fleet Grid & IoT Sensor Tile Matrix                    │
│   - Candidate Plan Review Drawer & Shift Diff Visualizer        │
│   - Corridor Timeline Gantt Chart & Conflict Alerts             │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP REST JSON APIs (v1)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application Server                   │
│   - Static File Serving (/)                                     │
│   - Provider Health (/api/v1/providers/health)                  │
│   - Sensor Telemetry Ingest (/api/v1/events/sensor)             │
│   - Live Fleet & Blocks (/api/v1/trains, /api/v1/blocks)       │
│   - Conflict Management (/api/v1/conflicts)                     │
│   - Re-Optimization & Plan Approval (/api/v1/plans)            │
└───────┬───────────────────────┬─────────────────────────┬───────┘
        │                       │                         │
        ▼                       ▼                         ▼
┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│  State Store     │  │  Google OR-Tools │  │  Conflict Detection │
│  (SQLite WAL     │  │  CP-SAT Solver   │  │  Engine             │
│   Mode DB)       │  │  (Constraint     │  │  (Headway, Speed,   │
│  railway_state.db│  │   Optimization)  │  │   Drift, Occupancy) │
└──────────────────┘  └──────────────────┘  └─────────────────────┘
        ▲                       │                         ▲
        │                       ▼                         │
┌───────┴──────────┐  ┌──────────────────┐  ┌─────────────┴───────┐
│  Sensor Gateway  │  │  Candidate Plan  │  │ External Providers  │
│  (X-Sensor-Token │  │  Engine          │  │ (RTIS, NTES, OGD,   │
│   Auth & Limits) │  │  (PLAN-00X Diffs │  │  Simulation Engine) │
│                  │  │   & Approvals)   │  │                     │
└──────────────────┘  └──────────────────┘  └─────────────────────┘
```

For complete technical specifications, see [docs/ARCHITECTURE.md](ARCHITECTURE.md).
