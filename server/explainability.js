export function generateTaskExplanation(item, trains, allTasks = [], blockWindows = []) {
  const taskId = item.task_id || item.id || "Task";
  const sec = item.section;
  const prio = item.priority;
  const dept = item.department;
  const blk = item.block_id;
  const stH = item.start_hour;
  const endH = item.end_hour;
  const dur = item.duration_mins || Math.round((endH - stH) * 60);
  const isEmg = Boolean(item.is_emergency);

  const startStr = `${Math.floor(stH).toString().padStart(2, "0")}:${Math.round((stH % 1) * 60).toString().padStart(2, "0")}`;
  const endStr = `${Math.floor(endH).toString().padStart(2, "0")}:${Math.round((endH % 1) * 60).toString().padStart(2, "0")}`;

  const parts = [];

  if (isEmg) {
    parts.push(`Emergency defect ${taskId} was allocated priority track possession in ${blk} (${startStr}–${endStr}) on section ${sec}.`);
  } else if (prio === "CRITICAL") {
    parts.push(`${taskId} was assigned to ${blk} from ${startStr}–${endStr} on section ${sec} to resolve critical safety defect before deadline.`);
  } else {
    parts.push(`${taskId} was assigned to ${blk} from ${startStr}–${endStr} on section ${sec}.`);
  }

  parts.push(`Window ${blk} permits ${dept} operations, accommodates the required ${dur}-minute duration, and does not overlap scheduled train movements.`);

  if (item.shift_reason) {
    parts.push(item.shift_reason);
  }

  return parts.join(" ");
}

export function generateUnassignedExplanation(task, blockWindows, trains) {
  const sec = task.section || "";
  const dept = task.department || "";
  const dur = task.duration_mins || 0;
  const deadline = task.deadline_hour ?? 24.0;

  const matchingWindows = blockWindows.filter(
    b => b.section === sec && (b.permitted_departments || []).includes(dept)
  );

  if (matchingWindows.length === 0) {
    return `Not scheduled: No sanctioned block windows on section ${sec} allow ${dept} maintenance.`;
  }

  const validDurWindows = matchingWindows.filter(
    b => (b.max_duration_mins ?? Math.round((b.end_hour - b.start_hour) * 60)) >= dur
  );
  if (validDurWindows.length === 0) {
    return `Not scheduled: Required duration (${dur} mins) exceeds capacity of permitted block windows on ${sec}.`;
  }

  const beforeDeadlineWindows = validDurWindows.filter(
    b => b.start_hour + dur / 60.0 <= deadline
  );
  if (beforeDeadlineWindows.length === 0) {
    return `Not scheduled: Permitted block windows on ${sec} cannot fit task before strict deadline ${deadline.toFixed(1)} hrs.`;
  }

  return `Not scheduled: Corridor track and timetable density on section ${sec} precluded collision-free placement before deadline ${deadline.toFixed(1)} hrs.`;
}

export function generatePlanSummary(scheduled, unassigned, baseline, solverStatus = "OPTIMAL", solveTimeSeconds = 0.0) {
  const count = scheduled.length;
  const unassignedCount = unassigned.length;
  if (count === 0 && unassignedCount === 0) {
    return "No maintenance tasks registered in current scenario. Add tasks or load demo scenario to plan.";
  }

  const critCount = scheduled.filter(x => x.priority === "CRITICAL").length;

  const parts = [`OR-Tools CP-SAT (${solverStatus} in ${solveTimeSeconds.toFixed(2)}s): ${count} blocks scheduled.`];
  if (critCount > 0) {
    parts.push(`${critCount} critical safety defect(s) secured before deadlines.`);
  }
  if (unassignedCount > 0) {
    parts.push(`${unassignedCount} task(s) unassigned due to corridor/window constraints.`);
  } else {
    parts.push("0 unscheduled tasks.");
  }

  if (baseline && (baseline.manual_total_delay_mins || 0) > 0) {
    const delaySaved = baseline.manual_total_delay_mins - baseline.optimized_total_delay_mins;
    parts.push(`Saved ${delaySaved} mins vs uncoordinated baseline (${baseline.delay_reduction_pct}% reduction).`);
    parts.push(`Window utilization: ${baseline.optimized_block_utilization_pct}%.`);
  }

  return parts.join(" ");
}
