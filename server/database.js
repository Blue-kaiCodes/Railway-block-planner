import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATA_DIR = path.join(path.dirname(__dirname), "data");
const DATA_FILE = path.join(DATA_DIR, "datastore.json");
const SNAPSHOT_FILE = path.join(DATA_DIR, "snapshot.json");

function formatHour(h) {
  if (h === undefined || h === null) return "--:--";
  const totalMins = Math.round(h * 60);
  const hrs = Math.floor(totalMins / 60);
  const mins = totalMins % 60;
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}

function getDefaultDataset() {
  return {
    sections: [
      { id: "A12-B14", name: "Howrah - Bardhaman Line", length_km: 95, tracks: 2, max_speed_kmh: 130 },
      { id: "B14-C02", name: "Bardhaman - Asansol Line", length_km: 106, tracks: 2, max_speed_kmh: 130 },
      { id: "C02-C08", name: "Asansol - Dhanbad Line", length_km: 60, tracks: 2, max_speed_kmh: 110 },
      { id: "C08-D15", name: "Dhanbad - Gaya Line", length_km: 201, tracks: 2, max_speed_kmh: 130 },
      { id: "D15-E20", name: "Gaya - Pt. Deen Dayal Upadhyaya Line", length_km: 204, tracks: 2, max_speed_kmh: 130 }
    ],
    assets: [
      { id: "AST-101", type: "Track Rail Joint", section: "A12-B14", age_years: 8.5, criticality: "HIGH", last_maintenance: "2026-03-12", health_score: 62.0 },
      { id: "AST-102", type: "Point Switch #14B", section: "A12-B14", age_years: 12.0, criticality: "CRITICAL", last_maintenance: "2025-11-05", health_score: 45.0 },
      { id: "AST-201", type: "Automatic Interlocking Signal", section: "B14-C02", age_years: 4.2, criticality: "MEDIUM", last_maintenance: "2026-06-01", health_score: 78.0 },
      { id: "AST-202", type: "OHE Overhead Line Support #88", section: "B14-C02", age_years: 9.1, criticality: "HIGH", last_maintenance: "2026-02-18", health_score: 58.0 },
      { id: "AST-301", type: "Track Bed Ballast", section: "C02-C08", age_years: 15.0, criticality: "CRITICAL", last_maintenance: "2025-08-20", health_score: 38.0 },
      { id: "AST-302", type: "Axle Counter Sensor Unit", section: "C02-C08", age_years: 2.5, criticality: "MEDIUM", last_maintenance: "2026-07-10", health_score: 88.0 },
      { id: "AST-401", type: "Traction Transformer Substation", section: "C08-D15", age_years: 11.2, criticality: "HIGH", last_maintenance: "2026-01-14", health_score: 52.0 },
      { id: "AST-501", type: "Girder Railway Bridge #42", section: "D15-E20", age_years: 24.0, criticality: "CRITICAL", last_maintenance: "2025-09-30", health_score: 41.0 }
    ],
    tasks: [],
    trains: [
      { train_id: "12301", train_name: "Howrah Rajdhani Express", origin: "Howrah Jn (HWH)", destination: "New Delhi (NDLS)", section: "A12-B14", arrival_hour: 0.5, departure_hour: 1.75, service_priority: 1 },
      { train_id: "12301", train_name: "Howrah Rajdhani Express", origin: "Howrah Jn (HWH)", destination: "New Delhi (NDLS)", section: "B14-C02", arrival_hour: 1.8, departure_hour: 3.0, service_priority: 1 },
      { train_id: "12301", train_name: "Howrah Rajdhani Express", origin: "Howrah Jn (HWH)", destination: "New Delhi (NDLS)", section: "C02-C08", arrival_hour: 3.1, departure_hour: 4.0, service_priority: 1 },
      { train_id: "12259", train_name: "Sealdah Duronto Express", origin: "Sealdah (SDAH)", destination: "Bikaner Jn (BKN)", section: "A12-B14", arrival_hour: 6.0, departure_hour: 7.2, service_priority: 1 },
      { train_id: "12259", train_name: "Sealdah Duronto Express", origin: "Sealdah (SDAH)", destination: "Bikaner Jn (BKN)", section: "B14-C02", arrival_hour: 7.3, departure_hour: 8.5, service_priority: 1 },
      { train_id: "12305", train_name: "Kolkata Rajdhani Express", origin: "Howrah Jn (HWH)", destination: "New Delhi (NDLS)", section: "C08-D15", arrival_hour: 10.0, departure_hour: 11.5, service_priority: 1 },
      { train_id: "12305", train_name: "Kolkata Rajdhani Express", origin: "Howrah Jn (HWH)", destination: "New Delhi (NDLS)", section: "D15-E20", arrival_hour: 11.6, departure_hour: 13.0, service_priority: 1 },
      { train_id: "12313", train_name: "Sealdah Rajdhani Express", origin: "Sealdah (SDAH)", destination: "New Delhi (NDLS)", section: "A12-B14", arrival_hour: 16.5, departure_hour: 17.8, service_priority: 1 },
      { train_id: "12313", train_name: "Sealdah Rajdhani Express", origin: "Sealdah (SDAH)", destination: "New Delhi (NDLS)", section: "B14-C02", arrival_hour: 17.9, departure_hour: 19.1, service_priority: 1 },

      { train_id: "13005", train_name: "Amritsar Mail", origin: "Howrah Jn (HWH)", destination: "Amritsar Jn (ASR)", section: "A12-B14", arrival_hour: 8.0, departure_hour: 9.5, service_priority: 2 },
      { train_id: "13005", train_name: "Amritsar Mail", origin: "Howrah Jn (HWH)", destination: "Amritsar Jn (ASR)", section: "B14-C02", arrival_hour: 9.6, departure_hour: 11.0, service_priority: 2 },
      { train_id: "13005", train_name: "Amritsar Mail", origin: "Howrah Jn (HWH)", destination: "Amritsar Jn (ASR)", section: "C02-C08", arrival_hour: 11.1, departure_hour: 12.2, service_priority: 2 },
      { train_id: "12381", train_name: "Poorva Express", origin: "Howrah Jn (HWH)", destination: "New Delhi (NDLS)", section: "C08-D15", arrival_hour: 13.5, departure_hour: 15.2, service_priority: 2 },
      { train_id: "12381", train_name: "Poorva Express", origin: "Howrah Jn (HWH)", destination: "New Delhi (NDLS)", section: "D15-E20", arrival_hour: 15.3, departure_hour: 17.0, service_priority: 2 },

      { train_id: "N-BOST", train_name: "Coal Rake Freight Special", origin: "Dhanbad Goods Yard", destination: "Kolaghat Thermal Plant", section: "C02-C08", arrival_hour: 5.0, departure_hour: 6.8, service_priority: 3 },
      { train_id: "N-BOXN", train_name: "Container Freight Express", origin: "Kolkata Port Terminal", destination: "Dadri ICD", section: "C08-D15", arrival_hour: 7.0, departure_hour: 9.0, service_priority: 3 },
      { train_id: "N-BCN", train_name: "Foodgrain Special Freight", origin: "FCI Godown Mughalsarai", destination: "FCI Godown Dankuni", section: "D15-E20", arrival_hour: 18.0, departure_hour: 20.0, service_priority: 3 }
    ],
    block_windows: [
      { id: "BLK-101", section: "A12-B14", start_hour: 2.0, end_hour: 5.5, permitted_departments: ["Engineering", "Signal & Telecom", "Traction / OHE"], max_duration_mins: 210, status: "AVAILABLE" },
      { id: "BLK-102", section: "A12-B14", start_hour: 10.0, end_hour: 16.0, permitted_departments: ["Engineering", "Signal & Telecom"], max_duration_mins: 360, status: "AVAILABLE" },
      
      { id: "BLK-201", section: "B14-C02", start_hour: 3.2, end_hour: 7.0, permitted_departments: ["Engineering", "Traction / OHE"], max_duration_mins: 228, status: "AVAILABLE" },
      { id: "BLK-202", section: "B14-C02", start_hour: 11.5, end_hour: 17.0, permitted_departments: ["Signal & Telecom", "Traction / OHE"], max_duration_mins: 330, status: "AVAILABLE" },

      { id: "BLK-301", section: "C02-C08", start_hour: 0.5, end_hour: 3.0, permitted_departments: ["Engineering", "Signal & Telecom"], max_duration_mins: 150, status: "AVAILABLE" },
      { id: "BLK-302", section: "C02-C08", start_hour: 12.5, end_hour: 16.0, permitted_departments: ["Engineering", "Traction / OHE", "Signal & Telecom"], max_duration_mins: 210, status: "AVAILABLE" },

      { id: "BLK-401", section: "C08-D15", start_hour: 1.0, end_hour: 6.5, permitted_departments: ["Traction / OHE", "Engineering"], max_duration_mins: 330, status: "AVAILABLE" },
      { id: "BLK-402", section: "C08-D15", start_hour: 15.5, end_hour: 20.0, permitted_departments: ["Signal & Telecom", "Traction / OHE"], max_duration_mins: 270, status: "AVAILABLE" },

      { id: "BLK-501", section: "D15-E20", start_hour: 2.0, end_hour: 7.0, permitted_departments: ["Engineering", "Signal & Telecom"], max_duration_mins: 300, status: "AVAILABLE" },
      { id: "BLK-502", section: "D15-E20", start_hour: 13.5, end_hour: 15.0, permitted_departments: ["Engineering", "Traction / OHE"], max_duration_mins: 90, status: "AVAILABLE" }
    ],
    resources: [
      { id: "RES-ENG-1", department: "Engineering", skill: "Track Heavy Maintenance Gang", team_name: "Howrah Track Unit 1", available_start_hour: 0.0, available_end_hour: 24.0 },
      { id: "RES-ENG-2", department: "Engineering", skill: "Bridge & Structural Team", team_name: "Dhanbad Bridge Unit", available_start_hour: 0.0, available_end_hour: 24.0 },
      { id: "RES-ST-1", department: "Signal & Telecom", skill: "Automatic Interlocking Crew", team_name: "Bardhaman Signal Gang", available_start_hour: 0.0, available_end_hour: 24.0 },
      { id: "RES-ST-2", department: "Signal & Telecom", skill: "Axle & Sensor Diagnostics", team_name: "Asansol Telecom Unit", available_start_hour: 0.0, available_end_hour: 24.0 },
      { id: "RES-OHE-1", department: "Traction / OHE", skill: "Tower Wagon Electrical Crew", team_name: "Howrah Traction Wing", available_start_hour: 0.0, available_end_hour: 24.0 },
      { id: "RES-OHE-2", department: "Traction / OHE", skill: "Substation High-Voltage Team", team_name: "Gaya Electrical Substation Crew", available_start_hour: 0.0, available_end_hour: 24.0 }
    ],
    incidents: [],
    current_schedule: [],
    plan_history: [],
    baseline_comparison: null,
    latest_summary: "Clean scenario active. Add maintenance tasks or load sample tasks to run CP-SAT optimizer.",
    data_source: "REPRESENTATIVE_WTT",
    scenario_name: "Howrah – Pt. Deen Dayal Upadhyaya Corridor (Zone 4)",
    data_source_label: "Representative Train Timetable",
    last_optimized_at: null,
    last_solver_status: "NOT RUN",
    latest_diff: null
  };
}

export function getSampleDemoTasks() {
  return [
    {
      id: "TSK-001",
      asset_id: "AST-102",
      section: "A12-B14",
      department: "Engineering",
      task_type: "Switch & Crossover Deep Overhaul",
      duration_mins: 120,
      priority: "CRITICAL",
      deadline_hour: 10.0,
      status: "PENDING",
      risk_score: 92.0,
      description: "Urgent rail switch realignment required on Down Line to prevent speed restrictions."
    },
    {
      id: "TSK-002",
      asset_id: "AST-202",
      section: "B14-C02",
      department: "Traction / OHE",
      task_type: "OHE Catenary Wire Cantilever Adjustment",
      duration_mins: 90,
      priority: "HIGH",
      deadline_hour: 14.0,
      status: "PENDING",
      risk_score: 75.0,
      description: "Overhead contact wire height deviation detected during high-speed pantograph test."
    },
    {
      id: "TSK-003",
      asset_id: "AST-201",
      section: "B14-C02",
      department: "Signal & Telecom",
      task_type: "Relay Interlocking Calibration",
      duration_mins: 60,
      priority: "MEDIUM",
      deadline_hour: 18.0,
      status: "PENDING",
      risk_score: 55.0,
      description: "Periodic calibration of automatic block signaling relays."
    },
    {
      id: "TSK-004",
      asset_id: "AST-301",
      section: "C02-C08",
      department: "Engineering",
      task_type: "Ballast Cleaning Machine (BCM) Deep Tamping",
      duration_mins: 150,
      priority: "CRITICAL",
      deadline_hour: 8.0,
      status: "PENDING",
      risk_score: 88.0,
      description: "Heavy track bed settlement; required before monsoon speed clearance."
    },
    {
      id: "TSK-005",
      asset_id: "AST-401",
      section: "C08-D15",
      department: "Traction / OHE",
      task_type: "Substation Circuit Breaker Replacement",
      duration_mins: 105,
      priority: "HIGH",
      deadline_hour: 16.0,
      status: "PENDING",
      risk_score: 72.0,
      description: "Preventive replacement of thermal damaged vacuum circuit breaker."
    },
    {
      id: "TSK-006",
      asset_id: "AST-501",
      section: "D15-E20",
      department: "Engineering",
      task_type: "Bridge Pier Expansion Joint Inspection",
      duration_mins: 90,
      priority: "HIGH",
      deadline_hour: 20.0,
      status: "PENDING",
      risk_score: 68.0,
      description: "Structural vibration check and bolt tightening on main girder bridge."
    },
    {
      id: "TSK-007",
      asset_id: "AST-302",
      section: "C02-C08",
      department: "Signal & Telecom",
      task_type: "Track Circuit Sensor Calibration",
      duration_mins: 45,
      priority: "LOW",
      deadline_hour: 22.0,
      status: "PENDING",
      risk_score: 35.0,
      description: "Routine diagnostic test of digital axle counters."
    }
  ];
}

export class Database {
  constructor() {
    this._data = {};
    this._snapshot = null;
    this._ensureStorage();
  }

  _ensureStorage() {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (fs.existsSync(DATA_FILE)) {
      try {
        const raw = fs.readFileSync(DATA_FILE, "utf-8");
        this._data = JSON.parse(raw);
      } catch {
        this.resetToDefault();
      }
    } else {
      this.resetToDefault();
    }
  }

  _save() {
    try {
      fs.writeFileSync(DATA_FILE, JSON.stringify(this._data, null, 2), "utf-8");
    } catch (e) {
      console.error("Error saving data file:", e);
    }
  }

  _getIsoTime() {
    const d = new Date();
    const pad = (n) => n.toString().padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  resetToDefault() {
    const defaultData = getDefaultDataset();
    this._data = defaultData;
    this._snapshot = null;
    if (fs.existsSync(SNAPSHOT_FILE)) {
      try { fs.unlinkSync(SNAPSHOT_FILE); } catch {}
    }
    this._save();
    return JSON.parse(JSON.stringify(this._data));
  }

  loadDemoScenario() {
    const baseData = getDefaultDataset();
    baseData.tasks = getSampleDemoTasks();
    baseData.tasks.forEach(t => {
      t.status = "PENDING";
      t.assigned_block = null;
      t.assigned_section = null;
      t.start_hour = null;
      t.end_hour = null;
      t.start_time = null;
      t.end_time = null;
    });
    baseData.block_windows.forEach(b => {
      b.status = "AVAILABLE";
      b.assigned_task_id = null;
    });
    baseData.current_schedule = [];
    baseData.plan_history = [];
    baseData.baseline_comparison = null;
    baseData.latest_summary = "Demo scenario loaded with 7 sample maintenance tasks. Click 'Generate Plan' to run Google OR-Tools CP-SAT.";
    baseData.data_source = "DEMO_SCENARIO";
    baseData.scenario_name = "Howrah – Pt. DDU Trunk Line (Demo Tasks)";
    baseData.data_source_label = "Demo Scenario (7 Sample Tasks)";
    baseData.last_optimized_at = null;
    baseData.last_solver_status = "NOT RUN";
    baseData.latest_diff = null;

    this._data = baseData;
    this._snapshot = null;
    if (fs.existsSync(SNAPSHOT_FILE)) {
      try { fs.unlinkSync(SNAPSHOT_FILE); } catch {}
    }
    this._save();
    return JSON.parse(JSON.stringify(this._data));
  }

  loadEmptyScenario() {
    const baseData = getDefaultDataset();
    this._data = {
      sections: JSON.parse(JSON.stringify(baseData.sections)),
      assets: JSON.parse(JSON.stringify(baseData.assets)),
      tasks: [],
      trains: JSON.parse(JSON.stringify(baseData.trains)),
      block_windows: JSON.parse(JSON.stringify(baseData.block_windows)),
      resources: JSON.parse(JSON.stringify(baseData.resources)),
      incidents: [],
      current_schedule: [],
      plan_history: [],
      baseline_comparison: null,
      latest_diff: null,
      latest_summary: "Clean scenario active. Add maintenance tasks to begin corridor planning.",
      data_source: "EMPTY_SCENARIO",
      scenario_name: "Howrah – Pt. DDU Trunk Line (Clean Slate)",
      data_source_label: "Blank Scenario (0 Tasks)",
      last_optimized_at: null,
      last_solver_status: "NOT RUN"
    };
    this._snapshot = null;
    if (fs.existsSync(SNAPSHOT_FILE)) {
      try { fs.unlinkSync(SNAPSHOT_FILE); } catch {}
    }
    this._save();
    return JSON.parse(JSON.stringify(this._data));
  }

  getAll() {
    return JSON.parse(JSON.stringify(this._data));
  }

  getTasks() {
    return JSON.parse(JSON.stringify(this._data.tasks || []));
  }

  getTask(taskId) {
    const t = (this._data.tasks || []).find(x => x.id === taskId);
    return t ? JSON.parse(JSON.stringify(t)) : null;
  }

  addTask(task) {
    if (!this._data.tasks) this._data.tasks = [];
    if (this._data.tasks.some(t => t.id === task.id)) {
      throw new Error(`Task ID '${task.id}' already exists.`);
    }
    this._data.tasks.push(task);
    this._save();
    return JSON.parse(JSON.stringify(task));
  }

  updateTask(taskId, updates) {
    const idx = (this._data.tasks || []).findIndex(t => t.id === taskId);
    if (idx === -1) {
      throw new Error(`Task '${taskId}' not found.`);
    }
    Object.assign(this._data.tasks[idx], updates);
    this._save();
    return JSON.parse(JSON.stringify(this._data.tasks[idx]));
  }

  deleteTask(taskId) {
    const initialLen = (this._data.tasks || []).length;
    this._data.tasks = (this._data.tasks || []).filter(t => t.id !== taskId);
    if (this._data.tasks.length < initialLen) {
      this._data.current_schedule = (this._data.current_schedule || []).filter(s => s.task_id !== taskId);
      this._save();
      return true;
    }
    return false;
  }

  getTrains() {
    return JSON.parse(JSON.stringify(this._data.trains || []));
  }

  addTrain(train) {
    if (!this._data.trains) this._data.trains = [];
    if (this._data.trains.some(tr => tr.train_id === train.train_id && tr.section === train.section)) {
      throw new Error(`Train '${train.train_id}' movement on section '${train.section}' already exists.`);
    }
    this._data.trains.push(train);
    this._save();
    return JSON.parse(JSON.stringify(train));
  }

  updateTrain(trainId, section, updates) {
    const idx = (this._data.trains || []).findIndex(tr => tr.train_id === trainId && tr.section === section);
    if (idx === -1) {
      throw new Error(`Train '${trainId}' on section '${section}' not found.`);
    }
    Object.assign(this._data.trains[idx], updates);
    this._save();
    return JSON.parse(JSON.stringify(this._data.trains[idx]));
  }

  deleteTrain(trainId, section) {
    const initialLen = (this._data.trains || []).length;
    this._data.trains = (this._data.trains || []).filter(tr => !(tr.train_id === trainId && tr.section === section));
    if (this._data.trains.length < initialLen) {
      this._save();
      return true;
    }
    return false;
  }

  getBlocks() {
    return JSON.parse(JSON.stringify(this._data.block_windows || []));
  }

  addBlock(block) {
    if (!this._data.block_windows) this._data.block_windows = [];
    if (this._data.block_windows.some(b => b.id === block.id)) {
      throw new Error(`Block ID '${block.id}' already exists.`);
    }
    this._data.block_windows.push(block);
    this._save();
    return JSON.parse(JSON.stringify(block));
  }

  updateBlock(blockId, updates) {
    const idx = (this._data.block_windows || []).findIndex(b => b.id === blockId);
    if (idx === -1) {
      throw new Error(`Block '${blockId}' not found.`);
    }
    Object.assign(this._data.block_windows[idx], updates);
    this._save();
    return JSON.parse(JSON.stringify(this._data.block_windows[idx]));
  }

  deleteBlock(blockId) {
    const initialLen = (this._data.block_windows || []).length;
    this._data.block_windows = (this._data.block_windows || []).filter(b => b.id !== blockId);
    if (this._data.block_windows.length < initialLen) {
      this._save();
      return true;
    }
    return false;
  }

  setOptimizationResult(schedule, baseline, summary, triggeredBy = "MANUAL_TRIGGER", solverStatus = "OPTIMAL", solveTimeSeconds = 0.0, tasksConsidered = 0) {
    this._data.current_schedule = schedule;
    this._data.baseline_comparison = baseline;
    this._data.latest_summary = summary;
    this._data.last_optimized_at = this._getIsoTime();
    this._data.last_solver_status = solverStatus;

    const scheduledByTaskId = {};
    for (const s of schedule) {
      scheduledByTaskId[s.task_id] = s;
    }
    for (const t of (this._data.tasks || [])) {
      const s = scheduledByTaskId[t.id];
      if (s) {
        t.status = "SCHEDULED";
        t.assigned_block = s.block_id;
        t.assigned_section = s.section;
        t.start_hour = s.start_hour;
        t.end_hour = s.end_hour;
        t.start_time = formatHour(s.start_hour);
        t.end_time = formatHour(s.end_hour);
      } else {
        t.status = "PENDING";
        t.assigned_block = null;
        t.assigned_section = null;
        t.start_hour = null;
        t.end_hour = null;
        t.start_time = null;
        t.end_time = null;
      }
    }

    const assignedBlockIds = new Set(schedule.map(s => s.block_id));
    for (const b of (this._data.block_windows || [])) {
      b.status = assignedBlockIds.has(b.id) ? "ASSIGNED" : "AVAILABLE";
      const s = schedule.find(x => x.block_id === b.id);
      b.assigned_task_id = s ? s.task_id : null;
    }

    if (!this._data.plan_history) this._data.plan_history = [];
    const history = this._data.plan_history;
    const conflicts = baseline?.optimized_conflicts ?? 0;
    const utilization = baseline?.optimized_block_utilization_pct ?? 0.0;
    const delaySaved = baseline?.delay_reduction_pct ?? 0.0;

    const historyRecord = {
      plan_id: `PLAN-${(history.length + 1).toString().padStart(4, "0")}`,
      timestamp: this._getIsoTime(),
      triggered_by: triggeredBy,
      status: solverStatus,
      solve_time_seconds: Math.round(solveTimeSeconds * 1000) / 1000,
      tasks_considered: tasksConsidered,
      tasks_scheduled: schedule.length,
      tasks_unscheduled: Math.max(0, tasksConsidered - schedule.length),
      conflicts,
      utilization_pct: utilization,
      delay_saved_pct: delaySaved,
      summary
    };

    history.unshift(historyRecord);
    if (history.length > 50) {
      this._data.plan_history = history.slice(0, 50);
    }

    this._save();
    return historyRecord;
  }

  clearPlan() {
    this._data.current_schedule = [];
    this._data.baseline_comparison = null;
    this._data.latest_summary = "No optimization plan generated. Click 'Generate Plan' to solve.";
    this._data.last_solver_status = "NOT RUN";
    this._data.last_optimized_at = null;
    this._data.latest_diff = null;

    if (Array.isArray(this._data.tasks)) {
      for (const t of this._data.tasks) {
        t.status = "PENDING";
        t.assigned_block = null;
        t.assigned_section = null;
        t.start_hour = null;
        t.end_hour = null;
        t.start_time = null;
        t.end_time = null;
      }
    }
    if (Array.isArray(this._data.block_windows)) {
      for (const b of this._data.block_windows) {
        b.status = "AVAILABLE";
        b.assigned_task_id = null;
      }
    }
    this._save();
    return true;
  }

  createSnapshot() {
    this._snapshot = JSON.parse(JSON.stringify(this._data));
    try {
      fs.writeFileSync(SNAPSHOT_FILE, JSON.stringify(this._snapshot, null, 2), "utf-8");
    } catch {}
  }

  canRevert() {
    return this._snapshot !== null || fs.existsSync(SNAPSHOT_FILE);
  }

  revertSnapshot() {
    let snap = this._snapshot;
    if (!snap && fs.existsSync(SNAPSHOT_FILE)) {
      try {
        snap = JSON.parse(fs.readFileSync(SNAPSHOT_FILE, "utf-8"));
      } catch {
        snap = null;
      }
    }

    if (snap) {
      this._data = JSON.parse(JSON.stringify(snap));
      this._data.latest_diff = null;
      this._snapshot = null;
      if (fs.existsSync(SNAPSHOT_FILE)) {
        try { fs.unlinkSync(SNAPSHOT_FILE); } catch {}
      }
      this._save();
      return true;
    }
    return false;
  }

  saveDiff(diff) {
    this._data.latest_diff = diff;
    this._save();
  }

  clearDiff() {
    this._data.latest_diff = null;
    this._save();
  }

  addIncident(incident) {
    if (!this._data.incidents) this._data.incidents = [];
    this._data.incidents.push(incident);
    this._save();
  }

  importBlocks(blocks) {
    if (!this._data.block_windows) this._data.block_windows = [];
    const existing = {};
    this._data.block_windows.forEach((b, i) => { existing[b.id] = i; });
    let addedCount = 0;
    for (const b of blocks) {
      if (b.id in existing) {
        Object.assign(this._data.block_windows[existing[b.id]], b);
      } else {
        this._data.block_windows.push(b);
      }
      addedCount++;
    }
    this._data.data_source = "IMPORTED_DATA";
    this._data.data_source_label = `Imported Data (${addedCount} block windows)`;
    this._save();
    return addedCount;
  }

  importTasks(tasks) {
    if (!this._data.tasks) this._data.tasks = [];
    const existing = {};
    this._data.tasks.forEach((t, i) => { existing[t.id] = i; });
    let addedCount = 0;
    for (const t of tasks) {
      if (t.id in existing) {
        Object.assign(this._data.tasks[existing[t.id]], t);
      } else {
        this._data.tasks.push(t);
      }
      addedCount++;
    }
    this._data.data_source = "IMPORTED_DATA";
    this._data.data_source_label = `Imported Data (${addedCount} tasks)`;
    this._save();
    return addedCount;
  }

  importTrains(trains) {
    if (!this._data.trains) this._data.trains = [];
    const existing = {};
    this._data.trains.forEach((tr, i) => {
      existing[`${tr.train_id}__${tr.section}`] = i;
    });
    let addedCount = 0;
    for (const tr of trains) {
      const key = `${tr.train_id}__${tr.section}`;
      if (key in existing) {
        Object.assign(this._data.trains[existing[key]], tr);
      } else {
        this._data.trains.push(tr);
      }
      addedCount++;
    }
    this._data.data_source = "IMPORTED_DATA";
    this._data.data_source_label = `Imported Data (${addedCount} trains)`;
    this._save();
    return addedCount;
  }

  importScenario(scenarioData, sourceLabel = "Imported Scenario") {
    for (const key of ["sections", "tasks", "trains", "block_windows"]) {
      if (!scenarioData[key]) {
        throw new Error(`Missing required key '${key}' in scenario dataset.`);
      }
    }
    scenarioData.current_schedule = [];
    scenarioData.plan_history = [];
    scenarioData.baseline_comparison = null;
    scenarioData.latest_summary = "Imported scenario loaded. Ready for optimization.";
    scenarioData.data_source = "IMPORTED_DATA";
    scenarioData.data_source_label = sourceLabel;
    scenarioData.scenario_name = scenarioData.scenario_name || "Imported Operational Scenario";
    scenarioData.last_optimized_at = null;
    scenarioData.last_solver_status = "NOT RUN";
    this._data = scenarioData;
    this._snapshot = null;
    this._save();
    return true;
  }
}

export const db = new Database();
