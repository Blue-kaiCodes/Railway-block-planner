import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";

import { db, getSampleDemoTasks } from "./server/database.js";
import { runOptimization } from "./server/optimizer.js";
import { calculateBaselineComparison } from "./server/baseline_solver.js";
import { generateTaskExplanation, generateUnassignedExplanation, generatePlanSummary } from "./server/explainability.js";
import { searchStations, getStationByCode, getAllStates, getDistrictsByState, getStationsByDistrict, getGeographicalTree } from "./server/station_data.js";
import { trainProvider } from "./server/train_provider.js";

function formatHour(h) {
  if (h === undefined || h === null) return "--:--";
  const totalMins = Math.round(h * 60);
  const hrs = Math.floor(totalMins / 60);
  const mins = totalMins % 60;
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;
const HOST = "0.0.0.0";

app.use(cors());
app.use(express.json({ limit: "50mb" }));

// Static frontend serving
const frontendPath = path.join(__dirname, "frontend");
app.use(express.static(frontendPath));

// --- Core Dataset & Scenario Routes ---

app.get("/api/dataset", (req, res) => {
  const data = db.getAll();
  data.can_revert = db.canRevert();
  res.json(data);
});

app.post("/api/scenario/load-demo", (req, res) => {
  const data = db.loadDemoScenario();
  res.json({
    status: "SUCCESS",
    message: "Demo Scenario successfully loaded.",
    scenario_name: data.scenario_name,
    task_count: (data.tasks || []).length,
    train_count: (data.trains || []).length,
    block_count: (data.block_windows || []).length
  });
});

app.post("/api/scenario/new-empty", (req, res) => {
  const data = db.loadEmptyScenario();
  res.json({
    status: "SUCCESS",
    message: "Empty scenario created. Ready for user task inputs and file imports.",
    scenario_name: data.scenario_name,
    task_count: 0
  });
});

app.post("/api/scenario/load-sample-tasks", (req, res) => {
  const sampleTasks = getSampleDemoTasks();
  for (const t of sampleTasks) {
    try {
      db.addTask(t);
    } catch {}
  }
  res.json({
    status: "SUCCESS",
    message: `Loaded ${sampleTasks.length} sample maintenance tasks into scenario.`,
    task_count: db.getTasks().length
  });
});

app.post("/api/scenario", (req, res) => {
  const payload = req.body || {};
  if (payload.action === "LOAD_DEMO") {
    const data = db.loadDemoScenario();
    return res.json({ status: "SUCCESS", message: "Demo Scenario loaded.", dataset: data });
  } else if (payload.action === "NEW_EMPTY") {
    const data = db.loadEmptyScenario();
    return res.json({ status: "SUCCESS", message: "New empty scenario initialized.", dataset: data });
  } else if (payload.action === "LOAD_SAMPLE_TASKS") {
    const sampleTasks = getSampleDemoTasks();
    for (const t of sampleTasks) {
      try { db.addTask(t); } catch {}
    }
    return res.json({ status: "SUCCESS", message: "Sample tasks loaded.", dataset: db.getAll() });
  }
  return res.status(400).json({ error: "Invalid action. Use 'LOAD_DEMO', 'NEW_EMPTY', or 'LOAD_SAMPLE_TASKS'." });
});

app.get("/api/dashboard/stats", (req, res) => {
  const data = db.getAll();
  const tasks = data.tasks || [];
  const trains = data.trains || [];
  const blocks = data.block_windows || [];
  const schedule = data.current_schedule || [];
  const baseline = data.baseline_comparison || {};

  const criticalTasks = tasks.filter(t => t.priority === "CRITICAL").length;
  const criticalScheduled = schedule.filter(s => s.priority === "CRITICAL").length;
  const hasPlan = schedule.length > 0;

  res.json({
    total_tasks: tasks.length,
    scheduled_tasks: schedule.length,
    unscheduled_tasks: Math.max(0, tasks.length - schedule.length),
    total_trains: trains.length,
    total_blocks: blocks.length,
    critical_safety_tasks: criticalTasks,
    critical_safety_scheduled: criticalScheduled,
    conflicts_count: hasPlan ? (baseline.optimized_conflicts ?? 0) : 0,
    block_utilization_pct: hasPlan ? (baseline.optimized_block_utilization_pct ?? 0.0) : 0.0,
    delay_saved_mins: hasPlan ? ((baseline.manual_total_delay_mins || 0) - (baseline.optimized_total_delay_mins || 0)) : 0,
    delay_reduction_pct: hasPlan ? (baseline.delay_reduction_pct ?? 0.0) : 0.0,
    optimization_status: data.last_solver_status || (hasPlan ? "OPTIMAL" : "NOT RUN"),
    data_source: data.data_source || "REPRESENTATIVE_WTT",
    data_source_label: data.data_source_label || "Representative Train Timetable",
    scenario_name: data.scenario_name || "Operational Scenario",
    last_optimized_at: data.last_optimized_at,
    can_revert: db.canRevert()
  });
});

// --- Tasks CRUD ---

app.get("/api/tasks", (req, res) => {
  res.json(db.getTasks());
});

app.post("/api/tasks", (req, res) => {
  try {
    const task = req.body;
    if (!task.id || !task.section || !task.department || !task.duration_mins) {
      return res.status(400).json({ error: "Missing required fields for maintenance task." });
    }
    const created = db.addTask(task);
    res.json({ status: "SUCCESS", task: created });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.get("/api/tasks/:task_id", (req, res) => {
  const task = db.getTask(req.params.task_id);
  if (!task) return res.status(404).json({ error: "Task not found" });
  res.json(task);
});

app.put("/api/tasks/:task_id", (req, res) => {
  try {
    const updated = db.updateTask(req.params.task_id, req.body);
    res.json({ status: "SUCCESS", task: updated });
  } catch (err) {
    res.status(404).json({ error: err.message });
  }
});

app.delete("/api/tasks/:task_id", (req, res) => {
  const ok = db.deleteTask(req.params.task_id);
  if (!ok) return res.status(404).json({ error: "Task not found" });
  res.json({ status: "SUCCESS", message: `Task '${req.params.task_id}' removed.` });
});

app.post("/api/tasks/:task_id/duplicate", (req, res) => {
  const orig = db.getTask(req.params.task_id);
  if (!orig) return res.status(404).json({ error: "Task not found" });

  const tasks = db.getTasks();
  let newId = `${orig.id}-COPY`;
  let c = 1;
  while (tasks.some(t => t.id === newId)) {
    c++;
    newId = `${orig.id}-COPY-${c}`;
  }

  const dup = { ...orig, id: newId, status: "PENDING" };
  try {
    const created = db.addTask(dup);
    res.json({ status: "SUCCESS", task: created });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// --- Trains CRUD ---

app.get("/api/trains", (req, res) => {
  res.json(db.getTrains());
});

app.post("/api/trains", (req, res) => {
  try {
    const train = req.body;
    if (!train.train_id || !train.section) {
      return res.status(400).json({ error: "train_id and section are required." });
    }
    const created = db.addTrain(train);
    res.json({ status: "SUCCESS", train: created });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.put("/api/trains/:train_id", (req, res) => {
  try {
    const section = req.query.section || req.body.section;
    if (!section) return res.status(400).json({ error: "section query parameter or body field required." });
    const updated = db.updateTrain(req.params.train_id, section, req.body);
    res.json({ status: "SUCCESS", train: updated });
  } catch (err) {
    res.status(404).json({ error: err.message });
  }
});

app.delete("/api/trains/:train_id", (req, res) => {
  const section = req.query.section || req.body.section;
  if (!section) return res.status(400).json({ error: "section query parameter required." });
  const ok = db.deleteTrain(req.params.train_id, section);
  if (!ok) return res.status(404).json({ error: "Train not found on section" });
  res.json({ status: "SUCCESS", message: `Train '${req.params.train_id}' removed from section '${section}'.` });
});

// --- Blocks CRUD ---

app.get("/api/blocks", (req, res) => {
  res.json(db.getBlocks());
});

app.post("/api/blocks", (req, res) => {
  try {
    const block = req.body;
    if (!block.id || !block.section) {
      return res.status(400).json({ error: "id and section are required." });
    }
    const created = db.addBlock(block);
    res.json({ status: "SUCCESS", block: created });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.put("/api/blocks/:block_id", (req, res) => {
  try {
    const updated = db.updateBlock(req.params.block_id, req.body);
    res.json({ status: "SUCCESS", block: updated });
  } catch (err) {
    res.status(404).json({ error: err.message });
  }
});

app.delete("/api/blocks/:block_id", (req, res) => {
  const ok = db.deleteBlock(req.params.block_id);
  if (!ok) return res.status(404).json({ error: "Block not found" });
  res.json({ status: "SUCCESS", message: `Block '${req.params.block_id}' removed.` });
});

// --- Reference Sections & Assets ---

app.get("/api/sections", (req, res) => {
  const data = db.getAll();
  res.json(data.sections || []);
});

app.get("/api/assets", (req, res) => {
  const data = db.getAll();
  res.json(data.assets || []);
});

// --- Optimization Engine Route ---

app.post("/api/optimize", (req, res) => {
  const data = db.getAll();
  const tasks = data.tasks || [];
  const trains = data.trains || [];
  const blocks = data.block_windows || [];
  const resources = data.resources || [];
  const prevSchedule = data.current_schedule || [];

  if (tasks.length === 0) {
    return res.json({
      status: "NO_TASKS",
      solver_status: "NO_TASKS",
      solve_time_seconds: 0.0,
      solve_time_ms: 0,
      tasks_considered: 0,
      tasks_scheduled: 0,
      tasks_unscheduled: 0,
      scheduled_maintenance_blocks: 0,
      train_conflicts: 0,
      window_utilization: 0.0,
      critical_tasks_scheduled: 0,
      total_critical_tasks: 0,
      plan_state: "NO_TASKS",
      human_summary: "No maintenance tasks registered in scenario. Add tasks via 'Maintenance Tasks' tab to run CP-SAT optimizer.",
      summary: "No maintenance tasks registered in scenario. Add tasks via 'Maintenance Tasks' tab to run CP-SAT optimizer.",
      schedule: [],
      task_decisions: [],
      plan_diff: null,
      baseline_comparison: calculateBaselineComparison([], trains, blocks, []),
      history_record: null,
      can_revert: db.canRevert()
    });
  }

  // Create snapshot before optimization to allow reverting if desired
  db.createSnapshot();

  const optRes = runOptimization(tasks, trains, blocks, resources, prevSchedule);

  for (const item of optRes.scheduled_items) {
    item.explanation = generateTaskExplanation(item, trains, tasks, blocks);
  }

  const unassignedExplanations = {};
  for (const uId of optRes.unassigned_tasks) {
    const t = tasks.find(x => x.id === uId);
    if (t) {
      unassignedExplanations[uId] = generateUnassignedExplanation(t, blocks, trains);
    }
  }

  const baseline = calculateBaselineComparison(tasks, trains, blocks, optRes.scheduled_items);

  // Compute plan state and diff relative to prevSchedule
  const isNewPlan = prevSchedule.length === 0;
  const oldScheduleMap = {};
  for (const ps of prevSchedule) {
    oldScheduleMap[ps.task_id] = ps;
  }

  const addedTasks = [];
  const movedTasks = [];
  const unchangedTasks = [];
  const unscheduledTasks = [];

  for (const s of optRes.scheduled_items) {
    const old = oldScheduleMap[s.task_id];
    if (!old) {
      addedTasks.push(s.task_id);
    } else if (old.block_id !== s.block_id || Math.abs(old.start_hour - s.start_hour) > 0.01) {
      const shiftMins = Math.round((s.start_hour - old.start_hour) * 60);
      movedTasks.push({
        task_id: s.task_id,
        task_name: s.task_name,
        section: s.section,
        old_window: `${old.block_id} (${formatHour(old.start_hour)}–${formatHour(old.end_hour)})`,
        new_window: `${s.block_id} (${formatHour(s.start_hour)}–${formatHour(s.end_hour)})`,
        shift_mins: shiftMins
      });
    } else {
      unchangedTasks.push(s.task_id);
    }
  }

  for (const ps of prevSchedule) {
    if (!optRes.scheduled_items.some(s => s.task_id === ps.task_id)) {
      unscheduledTasks.push(ps.task_id);
    }
  }

  const isMaterialChange = isNewPlan || addedTasks.length > 0 || movedTasks.length > 0 || unscheduledTasks.length > 0;
  const planState = isNewPlan ? "NEW_PLAN_CREATED" : (isMaterialChange ? "PLAN_UPDATED" : "NO_MATERIAL_CHANGES");

  // Dynamic concise natural summary
  const uniqueWindowsUsed = new Set(optRes.scheduled_items.map(s => s.block_id)).size;
  const scheduledSections = new Set(optRes.scheduled_items.map(s => s.section));
  const protectedTrainsAvoided = trains.filter(tr => scheduledSections.has(tr.section) && tr.service_priority <= 2).length;

  let humanSummary = "";
  if (optRes.scheduled_items.length > 0) {
    humanSummary = `CP-SAT scheduled ${optRes.scheduled_items.length} maintenance ${optRes.scheduled_items.length === 1 ? 'task' : 'tasks'} across ${uniqueWindowsUsed} available block ${uniqueWindowsUsed === 1 ? 'window' : 'windows'} while avoiding ${protectedTrainsAvoided} protected train movements.`;
  } else {
    humanSummary = "CP-SAT found no feasible block assignments for the registered tasks without violating safety constraints.";
  }

  const taskDecisions = tasks.map(t => {
    const scheduledItem = optRes.scheduled_items.find(s => s.task_id === t.id);
    const isScheduled = Boolean(scheduledItem);
    const expl = isScheduled ? scheduledItem.explanation : (unassignedExplanations[t.id] || "No available block window met duration/deadline constraints.");
    return {
      task_id: t.id,
      task_name: t.task_type,
      section: t.section,
      department: t.department,
      priority: t.priority,
      duration_mins: t.duration_mins,
      status: isScheduled ? "SCHEDULED" : "UNASSIGNED",
      block_id: isScheduled ? scheduledItem.block_id : null,
      block_window: isScheduled ? scheduledItem.block_id : null,
      assigned_window: isScheduled ? `${scheduledItem.block_id} (${formatHour(scheduledItem.start_hour)}–${formatHour(scheduledItem.end_hour)})` : "None",
      start_hour: isScheduled ? scheduledItem.start_hour : null,
      end_hour: isScheduled ? scheduledItem.end_hour : null,
      start_time: isScheduled ? formatHour(scheduledItem.start_hour) : null,
      end_time: isScheduled ? formatHour(scheduledItem.end_hour) : null,
      explanation: expl,
      reason: expl
    };
  });

  const planDiff = {
    plan_state: planState,
    is_material_change: isMaterialChange,
    change_message: isMaterialChange
      ? (isNewPlan ? "New baseline plan generated from pending task backlog." : "Corridor schedule updated with adjusted task assignments.")
      : "No material schedule changes were required.",
    added: addedTasks,
    moved: movedTasks,
    unchanged: unchangedTasks,
    unscheduled: unscheduledTasks
  };

  const criticalTasks = tasks.filter(t => t.priority === "CRITICAL").length;
  const criticalScheduled = optRes.scheduled_items.filter(s => s.priority === "CRITICAL").length;
  const trigger = req.body?.triggered_by || "MANUAL_TRIGGER";

  const historyRecord = db.setOptimizationResult(
    optRes.scheduled_items,
    baseline,
    humanSummary,
    trigger,
    optRes.solver_status,
    optRes.solve_time_seconds,
    tasks.length
  );

  res.json({
    status: optRes.status,
    solver_status: optRes.solver_status,
    solve_time_seconds: optRes.solve_time_seconds,
    solve_time_ms: Math.round(optRes.solve_time_seconds * 1000 * 10) / 10,
    tasks_considered: tasks.length,
    tasks_scheduled: optRes.scheduled_items.length,
    total_tasks_scheduled: optRes.scheduled_items.length,
    scheduled_blocks: optRes.scheduled_items.length,
    tasks_unscheduled: optRes.unassigned_tasks.length,
    scheduled_maintenance_blocks: optRes.scheduled_items.length,
    train_conflicts: baseline.optimized_conflicts ?? 0,
    window_utilization: baseline.optimized_block_utilization_pct ?? 0.0,
    critical_tasks_scheduled: criticalScheduled,
    total_critical_tasks: criticalTasks,
    plan_state: planState,
    human_summary: humanSummary,
    summary: humanSummary,
    schedule: optRes.scheduled_items,
    task_decisions: taskDecisions,
    unassigned_tasks: optRes.unassigned_tasks,
    unassigned_explanations: unassignedExplanations,
    baseline_comparison: baseline,
    plan_diff: planDiff,
    history_record: historyRecord,
    can_revert: db.canRevert()
  });
});

// --- Emergency Defect Injection ---

app.post("/api/inject-emergency", (req, res) => {
  db.createSnapshot();

  const dataBefore = db.getAll();
  const oldSchedule = dataBefore.current_schedule || [];
  const oldScheduleMap = {};
  for (const s of oldSchedule) {
    oldScheduleMap[s.task_id] = {
      block_id: s.block_id,
      start_hour: s.start_hour,
      end_hour: s.end_hour,
      task_name: s.task_name,
      section: s.section
    };
  }

  const sec = req.body?.section || "A12-B14";
  const dur = parseInt(req.body?.duration_mins, 10) || 90;
  const desc = req.body?.description || "Critical rail fracture detected via track ultrasonic sensor.";

  const emgId = `EMG-${Date.now().toString().slice(-4)}`;

  const emgTask = {
    id: emgId,
    asset_id: "AST-EMG",
    section: sec,
    department: "Engineering",
    task_type: "EMERGENCY: Ultrasonic Rail Fracture Repair",
    duration_mins: dur,
    priority: "CRITICAL",
    is_emergency: true,
    deadline_hour: 4.0,
    status: "PENDING",
    risk_score: 99.0,
    description: desc
  };

  db.addTask(emgTask);
  db.addIncident({
    id: `INC-${emgId}`,
    task_id: emgId,
    severity: "CRITICAL",
    detected_at: new Date().toISOString().slice(0, 19).replace("T", " "),
    section: sec,
    description: desc,
    status: "DISPATCHED"
  });

  const updatedData = db.getAll();
  const optRes = runOptimization(
    updatedData.tasks,
    updatedData.trains,
    updatedData.block_windows,
    updatedData.resources,
    oldSchedule
  );

  for (const item of optRes.scheduled_items) {
    item.explanation = generateTaskExplanation(item, updatedData.trains, updatedData.tasks, updatedData.block_windows);
  }

  const baseline = calculateBaselineComparison(
    updatedData.tasks,
    updatedData.trains,
    updatedData.block_windows,
    optRes.scheduled_items
  );

  const humanSummary = `EMERGENCY PREEMPTION ACTIVE: Emergency repair ${emgId} allocated priority track possession on ${sec}. ` +
    `CP-SAT scheduled ${optRes.scheduled_items.length} maintenance tasks with 0 express train conflicts.`;

  // Calculate detailed before/after diff
  const affectedTasks = [];
  const unchangedTasks = [];
  const movedDetails = [];

  for (const s of optRes.scheduled_items) {
    const tId = s.task_id;
    if (tId === emgId) continue;
    const oldItem = oldScheduleMap[tId];
    if (oldItem && oldItem.block_id === s.block_id && Math.abs(oldItem.start_hour - s.start_hour) < 0.01) {
      unchangedTasks.push(tId);
    } else if (oldItem) {
      affectedTasks.push(tId);
      const shiftMins = Math.round((s.start_hour - oldItem.start_hour) * 60);
      movedDetails.push({
        task_id: tId,
        task_name: s.task_name,
        section: s.section,
        old_start_hour: oldItem.start_hour,
        old_end_hour: oldItem.end_hour,
        new_start_hour: s.start_hour,
        new_end_hour: s.end_hour,
        old_block_id: oldItem.block_id,
        new_block_id: s.block_id,
        time_shift_mins: shiftMins,
        reason: `Preempted by emergency defect ${emgId} on corridor section ${sec}`
      });
    } else {
      affectedTasks.push(tId);
    }
  }

  const diff = {
    new_emergency_task: emgId,
    affected_tasks: affectedTasks,
    unchanged_tasks: unchangedTasks,
    total_moved: affectedTasks.length,
    moved_details: movedDetails
  };

  db.saveDiff(diff);

  const taskDecisions = updatedData.tasks.map(t => {
    const scheduledItem = optRes.scheduled_items.find(s => s.task_id === t.id);
    const isScheduled = Boolean(scheduledItem);
    const expl = isScheduled ? scheduledItem.explanation : "Window capacity allocated to higher priority safety emergency.";
    return {
      task_id: t.id,
      task_name: t.task_type,
      section: t.section,
      department: t.department,
      priority: t.priority,
      duration_mins: t.duration_mins,
      status: isScheduled ? "SCHEDULED" : "UNASSIGNED",
      block_id: isScheduled ? scheduledItem.block_id : null,
      block_window: isScheduled ? scheduledItem.block_id : null,
      assigned_window: isScheduled ? `${scheduledItem.block_id} (${formatHour(scheduledItem.start_hour)}–${formatHour(scheduledItem.end_hour)})` : "None",
      start_hour: isScheduled ? scheduledItem.start_hour : null,
      end_hour: isScheduled ? scheduledItem.end_hour : null,
      start_time: isScheduled ? formatHour(scheduledItem.start_hour) : null,
      end_time: isScheduled ? formatHour(scheduledItem.end_hour) : null,
      explanation: expl,
      reason: expl
    };
  });

  const criticalTasks = updatedData.tasks.filter(t => t.priority === "CRITICAL").length;
  const criticalScheduled = optRes.scheduled_items.filter(s => s.priority === "CRITICAL").length;

  const historyRecord = db.setOptimizationResult(
    optRes.scheduled_items,
    baseline,
    humanSummary,
    "EMERGENCY_INJECTION",
    optRes.solver_status,
    optRes.solve_time_seconds,
    updatedData.tasks.length
  );

  const planDiff = {
    plan_state: "PLAN_UPDATED",
    is_material_change: true,
    change_message: `Emergency defect ${emgId} preempted ${affectedTasks.length} task(s); preserved ${unchangedTasks.length} task(s).`,
    added: [emgId],
    moved: movedDetails.map(m => ({
      task_id: m.task_id,
      task_name: m.task_name,
      section: m.section,
      old_window: `${m.old_block_id} (${formatHour(m.old_start_hour)}–${formatHour(m.old_end_hour)})`,
      new_window: `${m.new_block_id} (${formatHour(m.new_start_hour)}–${formatHour(m.new_end_hour)})`,
      shift_mins: m.time_shift_mins
    })),
    unchanged: unchangedTasks,
    unscheduled: optRes.unassigned_tasks
  };

  res.json({
    status: "SUCCESS",
    solver_status: optRes.solver_status,
    solve_time_seconds: optRes.solve_time_seconds,
    solve_time_ms: Math.round(optRes.solve_time_seconds * 1000 * 10) / 10,
    tasks_considered: updatedData.tasks.length,
    tasks_scheduled: optRes.scheduled_items.length,
    total_tasks_scheduled: optRes.scheduled_items.length,
    scheduled_blocks: optRes.scheduled_items.length,
    tasks_unscheduled: optRes.unassigned_tasks.length,
    scheduled_maintenance_blocks: optRes.scheduled_items.length,
    train_conflicts: baseline.optimized_conflicts ?? 0,
    window_utilization: baseline.optimized_block_utilization_pct ?? 0.0,
    critical_tasks_scheduled: criticalScheduled,
    total_critical_tasks: criticalTasks,
    plan_state: "PLAN_UPDATED",
    human_summary: humanSummary,
    summary: humanSummary,
    message: `Emergency defect '${emgId}' registered on ${sec}. Corridor schedule re-optimized.`,
    emergency_task: emgTask,
    optimization_result: {
      ...optRes,
      schedule: optRes.scheduled_items,
      baseline_comparison: baseline
    },
    schedule: optRes.scheduled_items,
    task_decisions: taskDecisions,
    diff: diff,
    plan_diff: planDiff,
    baseline_comparison: baseline,
    history_record: historyRecord,
    can_revert: true
  });
});

// --- Revert Plan ---

app.post("/api/revert-plan", (req, res) => {
  const ok = db.revertSnapshot();
  if (ok) {
    res.json({ status: "SUCCESS", message: "Reverted to prior stable plan state successfully." });
  } else {
    res.status(400).json({ error: "No snapshot available to revert." });
  }
});

// --- Clear Current Plan ---

app.post(["/api/plan/clear", "/api/clear-plan"], (req, res) => {
  db.clearPlan();
  res.json({
    status: "SUCCESS",
    message: "Current optimization plan cleared successfully. Scenario inputs, tasks, block windows, and train timetable remain intact.",
    dataset: db.getAll()
  });
});

// --- Plan History ---

app.get("/api/history", (req, res) => {
  const data = db.getAll();
  res.json(data.plan_history || []);
});

// --- Export Routes ---

app.get("/api/export", (req, res) => {
  const data = db.getAll();
  res.setHeader("Content-Disposition", "attachment; filename=maintenance_schedule.json");
  res.json({
    export_timestamp: new Date().toISOString(),
    scenario_name: data.scenario_name,
    data_source: data.data_source,
    schedule: data.current_schedule || [],
    baseline_comparison: data.baseline_comparison,
    summary: data.latest_summary
  });
});

app.get("/api/export/dataset", (req, res) => {
  const data = db.getAll();
  res.setHeader("Content-Disposition", "attachment; filename=railway_dataset_export.json");
  res.json(data);
});

// --- Import Routes ---

app.post("/api/import/blocks", (req, res) => {
  const blocks = req.body;
  if (!Array.isArray(blocks)) {
    return res.status(400).json({ error: "Expected an array of block window objects." });
  }
  const count = db.importBlocks(blocks);
  res.json({ status: "SUCCESS", imported_count: count, message: `Successfully imported ${count} block windows.` });
});

app.post("/api/import/tasks", (req, res) => {
  const tasks = req.body;
  if (!Array.isArray(tasks)) {
    return res.status(400).json({ error: "Expected an array of task objects." });
  }
  const count = db.importTasks(tasks);
  res.json({ status: "SUCCESS", imported_count: count, message: `Successfully imported ${count} tasks.` });
});

app.post("/api/import/trains", (req, res) => {
  const trains = req.body;
  if (!Array.isArray(trains)) {
    return res.status(400).json({ error: "Expected an array of train timetable objects." });
  }
  const count = db.importTrains(trains);
  res.json({ status: "SUCCESS", imported_count: count, message: `Successfully imported ${count} train movements.` });
});

app.post("/api/import/scenario", (req, res) => {
  try {
    const payload = req.body;
    db.importScenario(payload, payload.source_label || "Imported Full Scenario");
    res.json({ status: "SUCCESS", message: "Scenario successfully imported." });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.post("/api/reset", (req, res) => {
  const defaultData = db.resetToDefault();
  res.json({ status: "SUCCESS", message: "Reset to default synthetic demo dataset.", data: defaultData });
});

// --- Geography & Station Directory Routes ---

app.get("/api/stations", (req, res) => {
  const q = req.query.query || "";
  const state = req.query.state || null;
  const district = req.query.district || null;
  const limit = parseInt(req.query.limit, 10) || 20;
  res.json(searchStations(q, state, district, limit));
});

app.get("/api/stations/:code", (req, res) => {
  const s = getStationByCode(req.params.code);
  if (!s) return res.status(404).json({ error: "Station not found" });
  res.json(s);
});

app.get("/api/geography/states", (req, res) => {
  res.json(getAllStates());
});

app.get("/api/geography/districts", (req, res) => {
  const state = req.query.state;
  if (!state) return res.status(400).json({ error: "State parameter is required" });
  res.json(getDistrictsByState(state));
});

app.get("/api/geography/stations", (req, res) => {
  const state = req.query.state;
  const district = req.query.district;
  if (!state || !district) {
    return res.status(400).json({ error: "Both state and district parameters are required" });
  }
  res.json(getStationsByDistrict(state, district));
});

app.get("/api/geography/tree", (req, res) => {
  res.json(getGeographicalTree());
});

// --- Live Train Provider Routes ---

app.get("/api/live/provider-status", (req, res) => {
  res.json(trainProvider.getProviderStatus());
});

app.get("/api/live/search-trains", async (req, res) => {
  const q = req.query.query || req.query.q || "";
  const results = await trainProvider.searchTrains(q);
  res.json(results);
});

app.get("/api/live/train-timetable/:train_number", async (req, res) => {
  const data = await trainProvider.getTrainTimetable(req.params.train_number);
  if (!data) return res.status(404).json({ error: "Train timetable not found" });
  res.json(data);
});

app.get("/api/live/station-board/:station_code", async (req, res) => {
  const data = await trainProvider.getStationBoard(req.params.station_code);
  res.json(data);
});

app.get("/api/live/trains-between-stations", async (req, res) => {
  const from = req.query.from || "";
  const to = req.query.to || "";
  const data = await trainProvider.getTrainsBetweenStations(from, to);
  res.json(data);
});

app.get("/api/live/train-status/:train_number", async (req, res) => {
  const data = await trainProvider.getLiveTrainStatus(req.params.train_number);
  res.json(data);
});

// Fallback route for SPA / frontend index
app.get("*", (req, res) => {
  res.sendFile(path.join(frontendPath, "index.html"));
});

app.listen(PORT, HOST, () => {
  console.log(`Railway Block Planner running at http://localhost:${PORT}`);
});
