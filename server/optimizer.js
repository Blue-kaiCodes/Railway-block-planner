function minutes(hours) {
  return Math.round(hours * 60);
}

function hours(mins) {
  return Math.round((mins / 60.0) * 100) / 100;
}

export function runOptimization(tasks = [], trains = [], blockWindows = [], resources = [], previousSchedule = null) {
  const startPerf = performance.now();

  if (!tasks || tasks.length === 0) {
    return {
      status: "NO_TASKS",
      solver_status: "NO_TASKS",
      solve_time_seconds: 0.0,
      tasks_considered: 0,
      total_tasks_scheduled: 0,
      scheduled_items: [],
      unassigned_tasks: [],
      objective_value: 0.0
    };
  }

  const priorityWeights = {
    "CRITICAL": 20000,
    "HIGH": 6000,
    "MEDIUM": 2000,
    "LOW": 600
  };

  const prevStarts = {};
  if (previousSchedule && Array.isArray(previousSchedule)) {
    for (const ps of previousSchedule) {
      if (ps.task_id && ps.start_hour !== undefined) {
        prevStarts[ps.task_id] = minutes(ps.start_hour);
      }
    }
  }

  const deptResources = {};
  for (const r of resources) {
    const d = r.department;
    if (!deptResources[d]) deptResources[d] = [];
    deptResources[d].push(r.team_name || "Central Maintenance Crew");
  }

  // Sort tasks by priority: Emergency > Critical > High > Medium > Low
  const sortedTasks = [...tasks].sort((a, b) => {
    const isEmgA = Boolean(a.is_emergency || a.id.startsWith("EMG-"));
    const isEmgB = Boolean(b.is_emergency || b.id.startsWith("EMG-"));
    if (isEmgA !== isEmgB) return isEmgA ? -1 : 1;

    const wA = priorityWeights[a.priority] || 1000;
    const wB = priorityWeights[b.priority] || 1000;
    if (wA !== wB) return wB - wA;

    const deadA = a.deadline_hour ?? 24.0;
    const deadB = b.deadline_hour ?? 24.0;
    if (deadA !== deadB) return deadA - deadB;

    return (b.duration_mins || 0) - (a.duration_mins || 0);
  });

  const scheduledItems = [];
  const unassigned = [];
  let objectiveValue = 0;

  // Track intervals per section and per department: { startM, endM, taskId }
  const sectionOccupancies = {};
  const deptOccupancies = {};

  for (const task of sortedTasks) {
    const tId = task.id;
    const tSection = task.section;
    const tDept = task.department;
    const tDur = task.duration_mins;
    const tDeadlineM = minutes(task.deadline_hour ?? 24.0);
    const isEmg = Boolean(task.is_emergency || tId.startsWith("EMG-"));
    const pWeight = isEmg ? 60000 : (priorityWeights[task.priority] || 2000);

    const candidateBlocks = blockWindows.filter(b => {
      if (b.section !== tSection) return false;
      const perms = b.permitted_departments || [];
      if (!perms.includes(tDept)) return false;
      const maxD = b.max_duration_mins ?? Math.round((b.end_hour - b.start_hour) * 60);
      return maxD >= tDur;
    });

    if (candidateBlocks.length === 0) {
      unassigned.push(tId);
      continue;
    }

    const sectionTrains = trains.filter(tr => tr.section === tSection && tr.is_protected !== false);

    let bestSlot = null;
    let bestSlotScore = -Infinity;

    for (const b of candidateBlocks) {
      const bStartM = minutes(b.start_hour);
      const bEndM = minutes(b.end_hour);
      const maxStartM = Math.min(bEndM, tDeadlineM) - tDur;

      if (bStartM > maxStartM) continue;

      // Collect candidate start minutes
      const candidateStarts = new Set();
      candidateStarts.add(bStartM);

      for (const tr of sectionTrains) {
        const trEndM = minutes(tr.departure_hour);
        if (trEndM >= bStartM && trEndM <= maxStartM) {
          candidateStarts.add(trEndM);
        }
      }

      const existingSecOccupancies = sectionOccupancies[tSection] || [];
      for (const occ of existingSecOccupancies) {
        if (occ.endM >= bStartM && occ.endM <= maxStartM) {
          candidateStarts.add(occ.endM);
        }
      }

      const existingDeptOccupancies = deptOccupancies[tDept] || [];
      for (const occ of existingDeptOccupancies) {
        if (occ.endM >= bStartM && occ.endM <= maxStartM) {
          candidateStarts.add(occ.endM);
        }
      }

      // Also sample every 10 minutes within the block window
      for (let m = bStartM; m <= maxStartM; m += 10) {
        candidateStarts.add(m);
      }

      const sortedStarts = Array.from(candidateStarts).sort((x, y) => x - y);

      for (const startM of sortedStarts) {
        const endM = startM + tDur;
        if (endM > bEndM || endM > tDeadlineM) continue;

        // Check collision with trains
        let collidesWithTrain = false;
        for (const tr of sectionTrains) {
          const trArrM = minutes(tr.arrival_hour);
          const trDepM = minutes(tr.departure_hour);
          // Overlap check
          if (Math.min(endM, trDepM) > Math.max(startM, trArrM)) {
            collidesWithTrain = true;
            break;
          }
        }
        if (collidesWithTrain) continue;

        // Check collision with already scheduled tasks on same section
        let collidesWithSection = false;
        for (const occ of existingSecOccupancies) {
          if (Math.min(endM, occ.endM) > Math.max(startM, occ.startM)) {
            collidesWithSection = true;
            break;
          }
        }
        if (collidesWithSection) continue;

        // Check collision with already scheduled tasks of same department
        let collidesWithDept = false;
        for (const occ of existingDeptOccupancies) {
          if (Math.min(endM, occ.endM) > Math.max(startM, occ.startM)) {
            collidesWithDept = true;
            break;
          }
        }
        if (collidesWithDept) continue;

        // Calculate score: prefer earlier start, minimize deviation from prev start
        let score = pWeight - (startM * 0.1);
        if (prevStarts[tId] !== undefined) {
          score -= Math.abs(startM - prevStarts[tId]) * 2;
        }

        if (score > bestSlotScore) {
          bestSlotScore = score;
          bestSlot = {
            blockId: b.id,
            startM,
            endM
          };
        }
      }
    }

    if (bestSlot) {
      if (!sectionOccupancies[tSection]) sectionOccupancies[tSection] = [];
      sectionOccupancies[tSection].push({
        startM: bestSlot.startM,
        endM: bestSlot.endM,
        taskId: tId
      });

      if (!deptOccupancies[tDept]) deptOccupancies[tDept] = [];
      deptOccupancies[tDept].push({
        startM: bestSlot.startM,
        endM: bestSlot.endM,
        taskId: tId
      });

      const assignedRes = deptResources[tDept] || [task.required_crew || "Central Crew"];
      const secTrains = trains.filter(tr => tr.section === tSection);

      scheduledItems.push({
        task_id: task.id,
        task_name: task.task_type,
        department: task.department,
        section: task.section,
        block_id: bestSlot.blockId,
        start_hour: hours(bestSlot.startM),
        end_hour: hours(bestSlot.endM),
        duration_mins: task.duration_mins,
        assigned_resources: assignedRes,
        priority: task.priority,
        is_emergency: isEmg,
        explanation: "",
        train_conflicts_avoided: secTrains.length
      });

      objectiveValue += bestSlotScore;
    } else {
      unassigned.push(tId);
    }
  }

  scheduledItems.sort((a, b) => a.start_hour - b.start_hour);

  const elapsed = (performance.now() - startPerf) / 1000;
  let statusStr = "OPTIMAL";
  if (scheduledItems.length === 0 && unassigned.length > 0) {
    statusStr = "INFEASIBLE";
  } else if (unassigned.length > 0) {
    statusStr = "FEASIBLE";
  } else if (tasks.length === 0) {
    statusStr = "NO_TASKS";
  }

  return {
    status: statusStr,
    solver_status: statusStr,
    solve_time_seconds: Math.round(elapsed * 1000) / 1000,
    tasks_considered: tasks.length,
    total_tasks_scheduled: scheduledItems.length,
    scheduled_items: scheduledItems,
    unassigned_tasks: unassigned,
    objective_value: Math.round(objectiveValue)
  };
}
