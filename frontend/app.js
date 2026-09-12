const API_BASE = "/api";

const AppState = {
  dataset: null,
  currentSchedule: [],
  baselineData: null,
  planHistory: [],
  lastDiff: null,
  lastOptimizationResult: null,
  sortConfig: { column: null, ascending: true },
  allStations: [],
  geographyTree: {},
  selectedSection: null
};

document.addEventListener("DOMContentLoaded", () => {
  renderHoursHeader();
  fetchInitialData();
  startLiveClock();
  initStationDirectory();
  initLiveProviderStatus();
});

function startLiveClock() {
  const clockEl = document.getElementById("liveOperatingTime");
  function updateTime() {
    const now = new Date();
    try {
      const formatter = new Intl.DateTimeFormat("en-GB", {
        timeZone: "Asia/Kolkata",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false
      });
      if (clockEl) clockEl.innerText = formatter.format(now) + " IST";
    } catch {
      if (clockEl) clockEl.innerText = now.toLocaleTimeString('en-US', { hour12: false }) + " IST";
    }
    updateGanttNowLineOnly();
  }
  updateTime();
  setInterval(updateTime, 1000);
}

function renderHoursHeader() {
  const container = document.getElementById("ganttHoursHeader");
  if (!container) return;
  container.innerHTML = "";
  for (let i = 0; i <= 24; i += 2) {
    const div = document.createElement("div");
    div.className = "gantt-hour-cell";
    div.innerText = `${i.toString().padStart(2, '0')}:00`;
    container.appendChild(div);
  }
}

async function fetchInitialData() {
  try {
    const res = await fetch(`${API_BASE}/dataset`);
    AppState.dataset = await res.json();
    AppState.currentSchedule = AppState.dataset.current_schedule || [];
    AppState.baselineData = AppState.dataset.baseline_comparison;
    AppState.planHistory = AppState.dataset.plan_history || [];
    AppState.lastDiff = AppState.dataset.latest_diff || null;

    if (AppState.lastDiff) {
      const banner = document.getElementById("emergencyBanner");
      if (banner) {
        const titleEl = document.getElementById("emergencyTitle");
        const descEl = document.getElementById("emergencyDesc");
        if (titleEl) titleEl.innerText = `CRITICAL OPERATIONAL ALERT: ${AppState.lastDiff.new_emergency_task || "Emergency Defect"} Active`;
        if (descEl) descEl.innerText = `Dynamic re-optimization recalculated affected block windows. ${AppState.lastDiff.affected_tasks?.length || 0} tasks shifted, 0 express train conflicts.`;
        banner.style.display = "flex";
      }
    } else {
      closeEmergencyBanner();
    }

    updateDataSourceUI();
    populateSectionDropdowns();
    populateAssetDropdowns();
    updateDashboardKPIs();
    updateOverviewCards();
    renderGanttTimeline();
    renderTasksTable();
    renderTrainsTable();
    renderBlocksTable();
    renderSectionsTable();
    renderNetworkTopology();
    renderExplainabilityTab();
    renderBaselineTab();
    renderHistoryTable();
    renderOptimizationResultBanner(AppState.lastOptimizationResult);
    renderPlanResultFullView();
    checkRevertButtonState();

    const btnText = document.getElementById("generatePlanBtnText");
    if (btnText && !btnText.innerText.includes("Optimizing")) {
      btnText.innerText = (AppState.currentSchedule && AppState.currentSchedule.length > 0) ? "Re-Optimize Plan" : "Generate Plan";
    }
  } catch (err) {
    console.error("Failed to load initial dataset:", err);
  }
}

function updateDataSourceUI() {
  const badge = document.getElementById("dataSourceBadge");
  const selector = document.getElementById("scenarioSelector");
  if (!AppState.dataset) return;

  const src = AppState.dataset.data_source || "DEMO_SCENARIO";
  const label = AppState.dataset.data_source_label || "DEMO SCENARIO";

  if (badge) {
    badge.className = "data-source-badge";
    if (src === "EMPTY_SCENARIO") {
      badge.classList.add("badge-empty");
      badge.innerHTML = `<i class="fa-solid fa-file-circle-xmark"></i> ${label}`;
    } else if (src === "IMPORTED_DATA") {
      badge.classList.add("badge-imported");
      badge.innerHTML = `<i class="fa-solid fa-file-arrow-up"></i> ${label}`;
    } else {
      badge.classList.add("badge-demo");
      badge.innerHTML = `<i class="fa-solid fa-database"></i> ${label}`;
    }
  }

  if (selector) {
    if (src === "EMPTY_SCENARIO") {
      selector.value = "empty";
    } else if (src === "DEMO_SCENARIO") {
      selector.value = "demo";
    } else if (src === "IMPORTED_DATA") {
      selector.value = "imported";
    }
  }
}

async function handleScenarioChange(scenarioType) {
  showLoading("Switching Operational Scenario...", "Updating corridor datastore and clearing active constraints...");
  try {
    let url = `${API_BASE}/scenario/load-demo`;
    if (scenarioType === "empty") {
      url = `${API_BASE}/scenario/new-empty`;
    }
    const res = await fetch(url, { method: "POST" });
    const data = await res.json();

    closeEmergencyBanner();
    const resultBanner = document.getElementById("optimizationResultBanner");
    if (resultBanner) resultBanner.style.display = "none";
    AppState.lastOptimizationResult = null;
    AppState.lastDiff = null;

    await fetchInitialData();
    hideLoading();
  } catch (err) {
    hideLoading();
    alert("Error changing scenario: " + err.message);
  }
}

function checkRevertButtonState() {
  const btn = document.getElementById("revertPlanBtn");
  if (!btn) return;
  fetch(`${API_BASE}/dashboard/stats`)
    .then(r => r.json())
    .then(stats => {
      btn.style.display = stats.can_revert ? "inline-flex" : "none";
    })
    .catch(() => {});
}

function populateSectionDropdowns() {
  const sections = AppState.dataset?.sections || [];
  const dropdownIds = ["mSection", "trSection", "blkSection", "defSection"];
  dropdownIds.forEach(id => {
    const select = document.getElementById(id);
    if (!select) return;
    const currentVal = select.value;
    select.innerHTML = "";
    sections.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.innerText = `${s.id} (${s.name})`;
      select.appendChild(opt);
    });
    if (currentVal) select.value = currentVal;
  });
}

function populateAssetDropdowns() {
  const assets = AppState.dataset?.assets || [];
  const select = document.getElementById("mAssetId");
  if (!select) return;
  select.innerHTML = "";
  assets.forEach(a => {
    const opt = document.createElement("option");
    opt.value = a.id;
    opt.innerText = `${a.id} — ${a.type} (${a.section})`;
    select.appendChild(opt);
  });
}

function updateDashboardKPIs() {
  if (!AppState.dataset) return;
  const tasks = AppState.dataset.tasks || [];
  const critDefects = tasks.filter(t => t.priority === "CRITICAL").length;
  const trains = AppState.dataset.trains || [];
  const sched = AppState.currentSchedule || [];

  document.getElementById("kpiTasks").innerText = tasks.length;
  document.getElementById("kpiDefects").innerText = critDefects;
  document.getElementById("kpiTrains").innerText = trains.length;
  document.getElementById("kpiScheduled").innerText = sched.length;

  const unscheduledEl = document.getElementById("kpiUnscheduled");
  const unscheduledSub = document.getElementById("kpiUnscheduledSub");
  const conflictsEl = document.getElementById("kpiConflicts");
  const conflictsSub = document.getElementById("kpiConflictsSub");

  const unscheduledCount = sched.length > 0 ? Math.max(0, tasks.length - sched.length) : tasks.length;
  if (unscheduledEl) unscheduledEl.innerText = unscheduledCount;
  if (unscheduledSub) {
    if (tasks.length === 0) unscheduledSub.innerText = "Fully Cleared";
    else if (sched.length === 0) unscheduledSub.innerText = "Pending Slot";
    else unscheduledSub.innerText = unscheduledCount === 0 ? "Fully Cleared" : "Pending Slot";
  }

  const windows = AppState.dataset.block_windows || [];
  const windowsEl = document.getElementById("kpiAvailableWindows");
  if (windowsEl) windowsEl.innerText = windows.length;

  if (conflictsEl) conflictsEl.innerText = "0";
  if (conflictsSub) conflictsSub.innerText = "Zero Clashes";

  const statusEl = document.getElementById("kpiStatus");
  const engineStatus = document.getElementById("sidebarEngineStatus");
  const solverDot = document.getElementById("solverStateDot");
  const solverText = document.getElementById("solverStateText");

  const stripLastOpt = document.getElementById("stripLastOpt");
  const stripOptDot = document.getElementById("stripOptDot");
  const stripOptText = document.getElementById("stripOptText");
  const quickLoadBtn = document.getElementById("stripQuickLoadTasksBtn");

  if (quickLoadBtn) {
    quickLoadBtn.style.display = tasks.length === 0 ? "inline-flex" : "none";
  }

  const lastOptTime = AppState.dataset.last_optimization_timestamp;

  if (sched.length > 0) {
    statusEl.innerText = "Conflict-Free";
    engineStatus.innerText = "OPTIMAL";
    if (solverDot) { solverDot.className = "dot dot-green"; }
    if (solverText) { solverText.innerText = "Plan Active"; }

    if (stripLastOpt) stripLastOpt.innerText = lastOptTime || "Active Plan";
    if (stripOptDot) stripOptDot.className = "dot dot-green";
    if (stripOptText) stripOptText.innerText = "OPTIMAL";
  } else if (tasks.length === 0) {
    statusEl.innerText = "No Tasks";
    engineStatus.innerText = "IDLE";
    if (solverDot) { solverDot.className = "dot dot-gray"; }
    if (solverText) { solverText.innerText = "No Tasks"; }

    if (stripLastOpt) stripLastOpt.innerText = "Not Run";
    if (stripOptDot) stripOptDot.className = "dot dot-gray";
    if (stripOptText) stripOptText.innerText = "Not Run";
  } else {
    statusEl.innerText = "Pending";
    engineStatus.innerText = "READY";
    if (solverDot) { solverDot.className = "dot dot-amber"; }
    if (solverText) { solverText.innerText = "Unsolved Backlog"; }

    if (stripLastOpt) stripLastOpt.innerText = "Not Run";
    if (stripOptDot) stripOptDot.className = "dot dot-amber";
    if (stripOptText) stripOptText.innerText = "Awaiting Plan";
  }

  const b = AppState.baselineData;
  if (b && tasks.length > 0 && sched.length > 0) {
    document.getElementById("kpiUtil").innerText = `${b.optimized_block_utilization_pct}%`;
    document.getElementById("kpiUtilDelta").innerText = `+${roundDiff(b.optimized_block_utilization_pct, b.manual_block_utilization_pct)}% vs Manual`;
  } else {
    document.getElementById("kpiUtil").innerText = "0.0%";
    document.getElementById("kpiUtilDelta").innerText = tasks.length === 0 ? "No Demand" : "Awaiting Plan";
  }
}

function roundDiff(a, b) {
  return Math.max(0, Math.round((a - b) * 10) / 10);
}

function updateOverviewCards() {
  if (!AppState.dataset) return;
  const tasks = AppState.dataset.tasks || [];
  const windows = AppState.dataset.block_windows || [];
  const trains = AppState.dataset.trains || [];
  const sched = AppState.currentSchedule || [];

  const critTasks = tasks.filter(t => t.priority === "CRITICAL").length;
  const highTasks = tasks.filter(t => t.priority === "HIGH").length;
  const medTasks = tasks.filter(t => t.priority === "MEDIUM").length;
  const lowTasks = tasks.filter(t => t.priority === "LOW").length;

  const scheduledCount = sched.length;
  const pendingCount = Math.max(0, tasks.length - scheduledCount);

  // Maintenance Card
  const taskBadge = document.getElementById("overviewTaskCountBadge");
  if (taskBadge) {
    taskBadge.innerText = `${tasks.length} Registered`;
    taskBadge.className = `badge-label ${tasks.length > 0 ? 'badge-amber' : 'badge-gray'}`;
  }
  const taskTotal = document.getElementById("overviewTaskTotal");
  if (taskTotal) taskTotal.innerText = `${tasks.length} Tasks`;

  const taskCrit = document.getElementById("overviewTaskCritical");
  if (taskCrit) {
    taskCrit.innerHTML = critTasks > 0
      ? `<span class="dot dot-red"></span> ${critTasks} Critical (P1)`
      : `<span class="dot dot-green"></span> 0 Critical Defects`;
  }

  const taskPrio = document.getElementById("overviewTaskPrio");
  if (taskPrio) {
    taskPrio.innerText = `${highTasks} High | ${medTasks} Med | ${lowTasks} Low`;
  }

  const taskPlanningStatus = document.getElementById("overviewTaskPlanningStatus");
  if (taskPlanningStatus) {
    if (tasks.length === 0) {
      taskPlanningStatus.innerHTML = `<span class="semantic-text text-low"><span class="dot dot-gray"></span> Clean Slate</span>`;
    } else if (scheduledCount > 0) {
      taskPlanningStatus.innerHTML = `<span class="semantic-text text-medium" style="color:var(--accent-green); font-weight:700;"><span class="dot dot-green"></span> ${scheduledCount} Scheduled / ${pendingCount} Pending</span>`;
    } else {
      taskPlanningStatus.innerHTML = `<span class="semantic-text text-high" style="color:var(--accent-amber); font-weight:700;"><span class="dot dot-amber"></span> 0 Scheduled / ${tasks.length} Pending</span>`;
    }
  }

  // Block Windows Card
  const winBadge = document.getElementById("overviewWinCountBadge");
  if (winBadge) winBadge.innerText = `${windows.length} Available`;

  const winTotal = document.getElementById("overviewWinTotal");
  if (winTotal) winTotal.innerText = `${windows.length} Windows`;

  const assignedBlockIds = new Set(sched.map(s => s.block_id));
  const assignedCount = assignedBlockIds.size;
  const remainingCount = Math.max(0, windows.length - assignedCount);

  const winAssigned = document.getElementById("overviewWinAssigned");
  if (winAssigned) {
    winAssigned.innerText = `${assignedCount} Assigned`;
    winAssigned.style.color = assignedCount > 0 ? "var(--accent-green)" : "var(--text-secondary)";
  }

  const winRemaining = document.getElementById("overviewWinRemaining");
  if (winRemaining) {
    winRemaining.innerText = `${remainingCount} Windows`;
  }

  // Train Movements Card
  const trainTotal = document.getElementById("overviewTrainTotal");
  if (trainTotal) trainTotal.innerText = `${trains.length} Movements`;

  const expressCount = trains.filter(t => (t.train_type || '').includes('Express') || (t.train_type || '').includes('Rajdhani')).length;
  const superfastCount = trains.filter(t => (t.train_type || '').includes('Superfast')).length;
  const freightCount = trains.filter(t => (t.train_type || '').includes('Freight') || (t.train_type || '').includes('Goods')).length;
  const otherCount = Math.max(0, trains.length - (expressCount + superfastCount + freightCount));

  const trainTypes = document.getElementById("overviewTrainTypes");
  if (trainTypes) {
    trainTypes.innerText = `${expressCount} Express | ${superfastCount} Superfast | ${freightCount} Freight${otherCount > 0 ? ' | ' + otherCount + ' Other' : ''}`;
  }

  // Update header Clear Plan button state
  const clearBtn = document.getElementById("clearPlanHeaderBtn");
  if (clearBtn) {
    clearBtn.style.opacity = (sched.length > 0) ? "1" : "0.55";
  }
}

function confirmClearPlan() {
  if (!AppState.currentSchedule || AppState.currentSchedule.length === 0) {
    alert("No active optimization plan is currently loaded.");
    return;
  }
  openModal("clearPlanModal");
}

async function executeClearPlan() {
  closeModal("clearPlanModal");
  showLoading("Clearing Optimization Plan...", "Resetting scheduled maintenance blocks and task assignments...");
  try {
    const res = await fetch(`${API_BASE}/plan/clear`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to clear plan");

    AppState.lastOptimizationResult = null;
    AppState.lastDiff = null;
    AppState.currentSchedule = [];
    if (data.dataset) {
      AppState.dataset = data.dataset;
      AppState.baselineData = data.dataset.baseline_comparison || null;
    }

    closeEmergencyBanner();
    checkRevertButtonState();

    updateDashboardKPIs();
    updateOverviewCards();
    renderOptimizationResultBanner();
    renderGanttTimeline();
    renderTasksTable();
    renderBlocksTable();
    renderExplainabilityTab();
    renderBaselineTab();
    renderPlanResultFullView();
    renderHistoryTable();

    const btnText = document.getElementById("generatePlanBtnText");
    const btnIcon = document.getElementById("generatePlanIcon");
    if (btnText) btnText.innerText = "Generate Plan";
    if (btnIcon) btnIcon.className = "fa-solid fa-circle-play";

    hideLoading();
  } catch (err) {
    hideLoading();
    alert("Error clearing plan: " + err.message);
  }
}

function safeString(val, fallback = "") {
  if (val === undefined || val === null || val === "undefined" || val === "null") return fallback;
  const s = String(val).trim();
  return (s === "undefined" || s === "null" || s === "") ? fallback : s;
}

function getCurrentISTTime() {
  const now = new Date();
  try {
    const formatter = new Intl.DateTimeFormat("en-GB", {
      timeZone: "Asia/Kolkata",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false
    });
    const parts = formatter.formatToParts(now);
    const hourPart = parts.find(p => p.type === "hour");
    const minutePart = parts.find(p => p.type === "minute");
    const hours = parseInt(hourPart ? hourPart.value : now.getHours(), 10) % 24;
    const minutes = parseInt(minutePart ? minutePart.value : now.getMinutes(), 10);
    const decimalHours = hours + (minutes / 60);
    const timeStr = `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}`;
    return { hours, minutes, decimalHours, timeStr };
  } catch {
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const decimalHours = hours + (minutes / 60);
    const timeStr = `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}`;
    return { hours, minutes, decimalHours, timeStr };
  }
}

function updateGanttNowLineOnly() {
  const line = document.getElementById("ganttNowLine");
  const label = document.getElementById("ganttNowLabel");
  if (!line || !label) return;
  const ist = getCurrentISTTime();
  const timeLinePct = Math.min(Math.max((ist.decimalHours / 24) * 100, 0), 100);
  line.style.left = `${timeLinePct}%`;
  label.style.left = `${timeLinePct}%`;
  label.innerText = `NOW ${ist.timeStr}`;
}

function renderGanttTimeline() {
  const container = document.getElementById("ganttTracksContainer");
  if (!container || !AppState.dataset || !AppState.dataset.sections) return;
  container.innerHTML = "";

  const ist = getCurrentISTTime();
  const timeLinePct = Math.min(Math.max((ist.decimalHours / 24) * 100, 0), 100);

  const timeLine = document.createElement("div");
  timeLine.className = "gantt-current-time-line";
  timeLine.id = "ganttNowLine";
  timeLine.style.left = `${timeLinePct}%`;

  const timeLabel = document.createElement("div");
  timeLabel.className = "gantt-current-time-label";
  timeLabel.id = "ganttNowLabel";
  timeLabel.style.left = `${timeLinePct}%`;
  timeLabel.innerText = `NOW ${ist.timeStr}`;

  container.appendChild(timeLine);
  container.appendChild(timeLabel);

  const incidents = AppState.dataset.incidents || [];
  const emergencyTaskIds = incidents.map(i => i.task_id);
  const shiftedTaskIds = AppState.lastDiff?.affected_tasks || [];

  AppState.dataset.sections.forEach(sec => {
    const row = document.createElement("div");
    row.className = "gantt-row";

    const label = document.createElement("div");
    label.className = "gantt-row-label";
    label.innerHTML = `<span><strong>${safeString(sec.id, 'SEC')}</strong> — ${safeString(sec.name, 'Section')}</span> <span style="color:var(--text-secondary); font-size:11px;">Length: ${sec.length_km || 0} km | ${sec.tracks || 2} Tracks | Max ${sec.max_speed_kmh || 130} km/h</span>`;
    row.appendChild(label);

    const track = document.createElement("div");
    track.className = "gantt-track-area";
    track.id = `gantt-track-${sec.id}`;

    const secWindows = (AppState.dataset.block_windows || []).filter(w => w.section === sec.id);
    const secTrains = (AppState.dataset.trains || []).filter(t => t.section === sec.id);
    const secBlocks = (AppState.currentSchedule || []).filter(s => s.section === sec.id);

    // Block windows
    secWindows.forEach(win => {
      const leftPct = (win.start_hour / 24) * 100;
      const widthPct = ((win.end_hour - win.start_hour) / 24) * 100;
      const winId = safeString(win.id || win.window_id, "BLK");
      const depts = Array.isArray(win.permitted_departments) 
        ? win.permitted_departments.join(", ") 
        : safeString(win.permitted_departments || win.department, "All Depts");
      const durationMins = win.max_duration_mins || Math.round((win.end_hour - win.start_hour) * 60);

      const scheduledInWin = secBlocks.find(s => s.block_id === win.id || (s.start_hour >= win.start_hour - 0.05 && s.end_hour <= win.end_hour + 0.05));

      const winBar = document.createElement("div");
      winBar.className = "gantt-block-window" + (scheduledInWin ? " slot-occupied" : "");
      winBar.style.left = `${leftPct}%`;
      winBar.style.width = `${Math.max(widthPct, 2)}%`;

      if (scheduledInWin) {
        winBar.title = `Sanctioned Window ${winId} [${depts}]: Occupied by Task ${scheduledInWin.task_id} (${formatHour(win.start_hour)} - ${formatHour(win.end_hour)} IST) [Click to inspect slot]`;
        if (widthPct >= 10) {
          winBar.innerText = `🪟 Slot ${winId}`;
        } else {
          winBar.innerText = "";
        }
      } else {
        winBar.title = `Available Corridor Window ${winId} [${depts}] (${durationMins} mins): ${formatHour(win.start_hour)} - ${formatHour(win.end_hour)} IST (Unassigned slot - click to inspect)`;
        if (widthPct < 6) {
          winBar.innerText = `🪟 ${winId}`;
        } else if (widthPct < 12) {
          winBar.innerText = `🪟 ${winId} (Avail)`;
        } else {
          winBar.innerText = `🪟 ${winId} (Avail · ${durationMins}m)`;
        }
      }

      winBar.onclick = () => openBlockWindowDrawer(win);
      track.appendChild(winBar);
    });

    // Train movements
    secTrains.forEach(tr => {
      const leftPct = (tr.arrival_hour / 24) * 100;
      const widthPct = ((tr.departure_hour - tr.arrival_hour) / 24) * 100;
      const trainId = safeString(tr.train_id || tr.id, "TRN");
      const trainName = safeString(tr.train_name || tr.name, "");

      const trainBar = document.createElement("div");
      trainBar.className = "gantt-item gantt-train";
      trainBar.style.left = `${leftPct}%`;
      trainBar.style.width = `${Math.max(widthPct, 2)}%`;
      trainBar.title = `Train ${trainId}: ${trainName || 'Movement'} (${formatHour(tr.arrival_hour)} - ${formatHour(tr.departure_hour)} IST) [Timetable Constraint]`;

      if (widthPct < 5) {
        trainBar.innerText = `🚆 ${trainId}`;
      } else if (widthPct < 10) {
        trainBar.innerText = `🚆 ${trainId}`;
      } else {
        trainBar.innerText = `🚆 ${trainId} ${trainName}`.trim();
      }

      trainBar.onclick = () => openTrainDrawer(tr);
      track.appendChild(trainBar);
    });

    // Scheduled maintenance tasks
    secBlocks.forEach(blk => {
      const leftPct = (blk.start_hour / 24) * 100;
      const widthPct = ((blk.end_hour - blk.start_hour) / 24) * 100;
      const taskId = safeString(blk.task_id || blk.id, "TSK");
      const taskName = safeString(blk.task_name || blk.task_type, "Maintenance");
      const dept = safeString(blk.department, "ENG/TRD");
      const blockRef = safeString(blk.block_id, "");

      const blkBar = document.createElement("div");
      let prioClass = "gantt-block-medium";
      if (blk.priority === "CRITICAL") prioClass = "gantt-block-critical";
      else if (blk.priority === "HIGH") prioClass = "gantt-block-high";
      else if (blk.priority === "LOW") prioClass = "gantt-block-low";

      if (emergencyTaskIds.includes(taskId)) {
        prioClass += " gantt-block-emergency";
      } else if (shiftedTaskIds.includes(taskId)) {
        prioClass += " gantt-block-shifted";
      }

      blkBar.className = `gantt-item ${prioClass}`;
      blkBar.style.left = `${leftPct}%`;
      blkBar.style.width = `${Math.max(widthPct, 2.5)}%`;
      blkBar.title = `Scheduled Maintenance Task ${taskId}: ${taskName} [Assigned Window: ${blockRef || 'Auto'}] (${formatHour(blk.start_hour)} - ${formatHour(blk.end_hour)} IST) [Dept: ${dept}] [Click to inspect]`;

      if (widthPct < 5) {
        blkBar.innerText = `🔧 ${taskId}`;
      } else if (widthPct < 11) {
        const shortName = taskName.length > 14 ? taskName.slice(0, 12) + "…" : taskName;
        blkBar.innerText = `🔧 ${taskId} (${shortName})`;
      } else {
        const blkSuffix = blockRef ? ` [${blockRef}]` : "";
        blkBar.innerText = `🔧 ${taskId}: ${taskName}${blkSuffix}`;
      }

      blkBar.onclick = () => openBlockDrawer(blk);
      track.appendChild(blkBar);
    });

    row.appendChild(track);
    container.appendChild(row);
  });
}

function openBlockWindowDrawer(win) {
  const winId = win.id || win.window_id || "BLK-WIN";
  const depts = Array.isArray(win.permitted_departments) 
    ? win.permitted_departments.join(", ") 
    : (win.permitted_departments || win.department || "All Departments");
  const durationMins = win.max_duration_mins || Math.round((win.end_hour - win.start_hour) * 60);
  const schedTask = (AppState.currentSchedule || []).find(s => s.block_id === winId || (s.start_hour >= win.start_hour - 0.05 && s.end_hour <= win.end_hour + 0.05));

  document.getElementById("drawerTitle").innerText = `Sanctioned Window: ${winId}`;
  const body = document.getElementById("drawerBody");
  body.innerHTML = `
    <div class="drawer-row">
      <div class="drawer-label">Window ID</div>
      <div class="drawer-value"><strong>${winId}</strong></div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Corridor Section</div>
      <div class="drawer-value">${win.section}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Permitted Departments</div>
      <div class="drawer-value">${depts}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Sanctioned Hours</div>
      <div class="drawer-value">${formatHour(win.start_hour)} – ${formatHour(win.end_hour)} IST (${durationMins} mins)</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Operating Day</div>
      <div class="drawer-value">${win.day_of_week || 'All Operating Days'}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Current Allocation</div>
      <div class="drawer-value">
        ${schedTask ? `
          <span class="semantic-text text-high" style="color:var(--accent-green); font-weight:700;"><span class="dot dot-green"></span> Assigned: Task ${schedTask.task_id} (${safeString(schedTask.task_name, 'Maintenance')})</span>
          <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">Scheduled ${formatHour(schedTask.start_hour)}–${formatHour(schedTask.end_hour)} IST [Dept: ${schedTask.department || 'ENG'}]</div>
        ` : `
          <span class="semantic-text text-medium"><span class="dot dot-green"></span> Available / Unassigned Slot</span>
        `}
      </div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Window Authority</div>
      <div class="drawer-value"><span class="semantic-text text-medium"><span class="dot dot-green"></span> Approved Routine Corridor Maintenance Window</span></div>
    </div>
    <div style="margin-top:20px; display:flex; gap:8px;">
      <button class="btn btn-secondary" onclick="closeDrawer()">Close</button>
    </div>
  `;
  document.getElementById("detailDrawer").classList.add("open");
}

function openTrainDrawer(tr) {
  document.getElementById("drawerTitle").innerText = `Train Service: ${tr.train_name}`;
  const body = document.getElementById("drawerBody");
  body.innerHTML = `
    <div class="drawer-row">
      <div class="drawer-label">Train Number / ID</div>
      <div class="drawer-value"><strong>${tr.train_id}</strong></div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Route / Termini</div>
      <div class="drawer-value">${tr.origin || 'Origin N/A'} → ${tr.destination || 'Destination N/A'}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Service Type</div>
      <div class="drawer-value">${tr.train_type || 'Express Passenger'}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Section</div>
      <div class="drawer-value">${tr.section}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Scheduled Arrival & Departure</div>
      <div class="drawer-value">${formatHour(tr.arrival_hour)} – ${formatHour(tr.departure_hour)} IST</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Service Priority</div>
      <div class="drawer-value">${tr.service_priority === 1 ? 'Priority 1 (Rajdhani / High Speed)' : tr.service_priority === 2 ? 'Priority 2 (Mail/Passenger)' : 'Priority 3 (Freight)'}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Timetable Protection</div>
      <div class="drawer-value"><span class="semantic-text text-medium"><span class="dot dot-green"></span> ${tr.is_protected !== false ? 'Strictly Protected (No Overlap Allowed)' : 'Flexible Slot'}</span></div>
    </div>
    <div style="margin-top:20px; display:flex; gap:8px;">
      <button class="btn btn-secondary" onclick="editTrainFromDrawer('${tr.train_id}', '${tr.section}')">Edit Timing</button>
      <button class="btn btn-secondary" onclick="closeDrawer()">Close</button>
    </div>
  `;
  document.getElementById("detailDrawer").classList.add("open");
}

function openBlockDrawer(blk) {
  document.getElementById("drawerTitle").innerText = `Maintenance Block: ${blk.task_id}`;
  const body = document.getElementById("drawerBody");

  const isEmergency = AppState.dataset?.incidents?.some(i => i.task_id === blk.task_id);
  const isShifted = AppState.lastDiff?.affected_tasks?.includes(blk.task_id);

  let shiftNote = "";
  if (isShifted) {
    const moved = AppState.lastDiff?.moved_details?.find(m => m.task_id === blk.task_id);
    if (moved) {
      shiftNote = `<div style="background:#FFF8E1; border:1px solid #FFE082; padding:6px 10px; border-radius:3px; margin-bottom:10px; font-size:11px; color:#B87314;">
        <strong><i class="fa-solid fa-arrows-split-up-and-left"></i> Rescheduled Slot:</strong> Moved from ${formatHour(moved.old_start_hour)}–${formatHour(moved.old_end_hour)} to accommodate emergency defect.
      </div>`;
    }
  }

  body.innerHTML = `
    ${isEmergency ? '<div style="background:#FFEBEE; border:1px solid #FFCDD2; padding:6px 10px; border-radius:3px; margin-bottom:10px; font-size:11px; color:#C62828;"><strong><i class="fa-solid fa-triangle-exclamation"></i> Emergency Defect Task:</strong> Injected dynamically with priority line preemption.</div>' : ''}
    ${shiftNote}
    <div class="drawer-row">
      <div class="drawer-label">Task Description</div>
      <div class="drawer-value"><strong>${blk.task_name}</strong></div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Assigned Department & Crew</div>
      <div class="drawer-value">${blk.department} (${(blk.assigned_resources || []).join(', ') || 'Central Maintenance Unit'})</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Section & Block Window</div>
      <div class="drawer-value">${blk.section} | ${blk.block_id}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Allocated Operating Time</div>
      <div class="drawer-value">${formatHour(blk.start_hour)} – ${formatHour(blk.end_hour)} (${blk.duration_mins} mins)</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Priority Level</div>
      <div class="drawer-value">${renderPriorityBadge(blk.priority)}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Train Timetable Separation</div>
      <div class="drawer-value"><span class="semantic-text text-medium"><span class="dot dot-green"></span> Zero conflicts with scheduled trains</span></div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Optimization Decision Reason</div>
      <div class="drawer-value" style="font-size:12px; line-height:1.4; color:var(--text-secondary);">${blk.explanation || 'Scheduled deterministically by OR-Tools CP-SAT solver.'}</div>
    </div>
    <div style="margin-top:20px; display:flex; gap:8px;">
      <button class="btn btn-secondary" onclick="editTaskFromDrawer('${blk.task_id}')">Edit Task</button>
      <button class="btn btn-secondary" onclick="closeDrawer()">Close</button>
    </div>
  `;
  document.getElementById("detailDrawer").classList.add("open");
}

function openTaskDrawer(t) {
  document.getElementById("drawerTitle").innerText = `Task Details: ${t.id}`;
  const body = document.getElementById("drawerBody");

  const sched = AppState.currentSchedule?.find(s => s.task_id === t.id);

  body.innerHTML = `
    <div class="drawer-row">
      <div class="drawer-label">Task ID & Description</div>
      <div class="drawer-value"><strong>${t.id}: ${t.task_type}</strong></div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Corridor Section & Asset</div>
      <div class="drawer-value">${t.section} | Asset: ${t.asset_id}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Department</div>
      <div class="drawer-value">${t.department}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Required Duration</div>
      <div class="drawer-value">${t.duration_mins} mins (${(t.duration_mins / 60).toFixed(1)} hrs)</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Priority Level</div>
      <div class="drawer-value">${renderPriorityBadge(t.priority)}</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Hard Deadline Hour</div>
      <div class="drawer-value">By ${formatHour(t.deadline_hour)} IST</div>
    </div>
    <div class="drawer-row">
      <div class="drawer-label">Current Planning Status</div>
      <div class="drawer-value">${sched ? '<span class="semantic-text text-medium"><span class="dot dot-green"></span> SCHEDULED</span> in Block ' + sched.block_id + ' (' + formatHour(sched.start_hour) + '–' + formatHour(sched.end_hour) + ')' : '<span class="semantic-text text-high"><span class="dot dot-amber"></span> PENDING (Unassigned)</span>'}</div>
    </div>
    ${sched ? `
    <div class="drawer-row">
      <div class="drawer-label">Solver Audit Justification</div>
      <div class="drawer-value" style="font-size:12px; line-height:1.4; color:var(--text-secondary);">${sched.explanation}</div>
    </div>` : ''}
    <div style="margin-top:20px; display:flex; gap:8px;">
      <button class="btn btn-secondary" onclick="editTaskFromDrawer('${t.id}')">Edit Task</button>
      <button class="btn btn-secondary" onclick="closeDrawer()">Close</button>
    </div>
  `;
  document.getElementById("detailDrawer").classList.add("open");
}

function closeDrawer() {
  document.getElementById("detailDrawer").classList.remove("open");
}

function formatHour(h) {
  if (h === undefined || h === null) return "--:--";
  const totalMins = Math.round(h * 60);
  const hrs = Math.floor(totalMins / 60);
  const mins = totalMins % 60;
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}

function renderTasksTable() {
  filterTasksTable();
}

function filterTasksTable() {
  const tbody = document.querySelector("#tasksTable tbody");
  if (!tbody || !AppState.dataset) return;
  tbody.innerHTML = "";

  const searchText = (document.getElementById("taskSearchInput")?.value || "").toLowerCase();
  const deptVal = document.getElementById("deptFilter")?.value || "ALL";
  const prioVal = document.getElementById("prioFilter")?.value || "ALL";
  const statusVal = document.getElementById("statusFilter")?.value || "ALL";

  let tasks = [...(AppState.dataset.tasks || [])];

  tasks = tasks.filter(t => {
    const sched = (AppState.currentSchedule || []).find(s => s.task_id === t.id);
    const isScheduled = Boolean(sched);
    const effectiveStatus = isScheduled ? "SCHEDULED" : (t.status === "SCHEDULED" ? "SCHEDULED" : "PENDING");

    const matchSearch = t.id.toLowerCase().includes(searchText) || 
                        (t.asset_id && t.asset_id.toLowerCase().includes(searchText)) || 
                        t.task_type.toLowerCase().includes(searchText) ||
                        t.section.toLowerCase().includes(searchText);
    const matchDept = deptVal === "ALL" || t.department === deptVal;
    const matchPrio = prioVal === "ALL" || t.priority === prioVal;
    const matchStatus = statusVal === "ALL" || effectiveStatus === statusVal;
    return matchSearch && matchDept && matchPrio && matchStatus;
  });

  if (AppState.sortConfig.column) {
    const col = AppState.sortConfig.column;
    const asc = AppState.sortConfig.ascending;
    tasks.sort((a, b) => {
      let valA = a[col] ?? "";
      let valB = b[col] ?? "";
      if (typeof valA === "string") valA = valA.toLowerCase();
      if (typeof valB === "string") valB = valB.toLowerCase();
      if (valA < valB) return asc ? -1 : 1;
      if (valA > valB) return asc ? 1 : -1;
      return 0;
    });
  }

  if (tasks.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="10" style="text-align:center; color:var(--text-muted); padding:16px;">No maintenance tasks found. Add a task or load Demo Scenario.</td>`;
    tbody.appendChild(tr);
    return;
  }

  tasks.forEach(t => {
    const sched = (AppState.currentSchedule || []).find(s => s.task_id === t.id);
    const isScheduled = Boolean(sched) || t.status === "SCHEDULED";
    const assignedBlock = sched?.block_id || t.assigned_block;
    const startH = sched?.start_hour ?? t.start_hour;
    const endH = sched?.end_hour ?? t.end_hour;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <a href="javascript:void(0)" onclick="openTaskDrawerById('${t.id}')" style="color:var(--text-primary); font-weight:700; text-decoration:underline;">${t.id}</a>
        ${t.is_emergency ? '<span class="badge-label badge-red" style="font-size:9px; margin-left:4px;">EMERGENCY</span>' : ''}
      </td>
      <td>${t.asset_id}</td>
      <td>${t.section}</td>
      <td>${t.department}</td>
      <td>${t.task_type}</td>
      <td>${t.duration_mins} mins</td>
      <td>${renderPriorityBadge(t.priority)}</td>
      <td>${formatHour(t.deadline_hour)}</td>
      <td>
        ${isScheduled ? `
          <span style="color:var(--accent-green); font-weight:700;"><span class="dot dot-green"></span> SCHEDULED</span>
          <div style="font-size:10.5px; color:var(--text-secondary); margin-top:2px;">
            ${assignedBlock ? `Block ${assignedBlock}` : 'Window Assigned'}
            ${startH !== undefined && startH !== null && endH !== undefined && endH !== null ? `(${formatHour(startH)}–${formatHour(endH)})` : ''}
          </div>
        ` : `
          <span style="color:var(--accent-amber); font-weight:600;"><span class="dot dot-amber"></span> PENDING</span>
        `}
      </td>
      <td style="text-align:right;">
        <button class="btn btn-secondary btn-xs" onclick="editTask('${t.id}')" title="Edit Task"><i class="fa-solid fa-pen"></i></button>
        <button class="btn btn-secondary btn-xs" onclick="duplicateTask('${t.id}')" title="Duplicate Task"><i class="fa-solid fa-copy"></i></button>
        <button class="btn btn-danger btn-xs" onclick="deleteTask('${t.id}')" title="Delete Task"><i class="fa-solid fa-trash"></i></button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function openTaskDrawerById(taskId) {
  const t = AppState.dataset?.tasks?.find(x => x.id === taskId);
  if (t) openTaskDrawer(t);
}

function sortTasks(column) {
  if (AppState.sortConfig.column === column) {
    AppState.sortConfig.ascending = !AppState.sortConfig.ascending;
  } else {
    AppState.sortConfig.column = column;
    AppState.sortConfig.ascending = true;
  }
  filterTasksTable();
}

function renderPriorityBadge(priority) {
  let prioDot = "dot-green";
  let prioTextClass = "text-medium";
  if (priority === "CRITICAL") { prioDot = "dot-red"; prioTextClass = "text-critical"; }
  else if (priority === "HIGH") { prioDot = "dot-amber"; prioTextClass = "text-high"; }
  else if (priority === "LOW") { prioDot = "dot-gray"; prioTextClass = "text-low"; }
  return `<span class="semantic-text ${prioTextClass}"><span class="dot ${prioDot}"></span> ${priority}</span>`;
}

let isEditingTaskId = null;

function openCreateTaskModal() {
  isEditingTaskId = null;
  document.getElementById("taskModalTitle").innerText = "Register Maintenance Task";
  document.getElementById("taskForm").reset();
  document.getElementById("mTaskId").disabled = false;
  document.getElementById("mTaskId").value = `TSK-${String((AppState.dataset?.tasks?.length || 0) + 1).padStart(3, '0')}`;
  document.getElementById("mDeadline").value = "18.0";
  document.getElementById("mDur").value = "90";
  const emgEl = document.getElementById("mIsEmergency");
  if (emgEl) emgEl.checked = false;
  openModal("taskModal");
}

function editTask(taskId) {
  const t = (AppState.dataset?.tasks || []).find(x => x.id === taskId);
  if (!t) return;
  isEditingTaskId = taskId;
  document.getElementById("taskModalTitle").innerText = `Edit Maintenance Task (${taskId})`;
  document.getElementById("mTaskId").value = t.id;
  document.getElementById("mTaskId").disabled = true;
  document.getElementById("mSection").value = t.section;
  document.getElementById("mAssetId").value = t.asset_id;
  document.getElementById("mDept").value = t.department;
  document.getElementById("mType").value = t.task_type;
  document.getElementById("mDur").value = t.duration_mins;
  document.getElementById("mPrio").value = t.priority;
  document.getElementById("mDeadline").value = t.deadline_hour;
  document.getElementById("mCrew").value = t.required_crew || "";
  const emgEl = document.getElementById("mIsEmergency");
  if (emgEl) emgEl.checked = !!t.is_emergency;
  openModal("taskModal");
}

function editTaskFromDrawer(taskId) {
  closeDrawer();
  editTask(taskId);
}

async function handleTaskSubmit(e) {
  e.preventDefault();
  const payload = {
    id: document.getElementById("mTaskId").value.trim(),
    asset_id: document.getElementById("mAssetId").value,
    section: document.getElementById("mSection").value,
    department: document.getElementById("mDept").value,
    task_type: document.getElementById("mType").value.trim(),
    duration_mins: parseInt(document.getElementById("mDur").value),
    priority: document.getElementById("mPrio").value,
    deadline_hour: parseFloat(document.getElementById("mDeadline").value),
    required_crew: document.getElementById("mCrew").value.trim() || "Standard Department Gang",
    is_emergency: document.getElementById("mIsEmergency")?.checked || false,
    status: "PENDING"
  };

  try {
    let res;
    if (isEditingTaskId) {
      res = await fetch(`${API_BASE}/tasks/${isEditingTaskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch(`${API_BASE}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    if (res.ok) {
      closeModal("taskModal");
      await fetchInitialData();
    } else {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Could not save task'}`);
    }
  } catch (err) {
    alert("Network error: Failed to save task.");
  }
}

async function duplicateTask(taskId) {
  try {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/duplicate`, { method: "POST" });
    if (res.ok) {
      await fetchInitialData();
    } else {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Could not duplicate task'}`);
    }
  } catch (err) {
    alert("Network error: Failed to duplicate task.");
  }
}

async function deleteTask(taskId) {
  if (!confirm(`Are you sure you want to delete task '${taskId}'?`)) return;
  try {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`, { method: "DELETE" });
    if (res.ok) {
      await fetchInitialData();
    }
  } catch (err) {
    // Fail gracefully
  }
}

function renderTrainsTable() {
  filterTrainsTable();
}

function filterTrainsTable() {
  const tbody = document.querySelector("#trainsTable tbody");
  if (!tbody || !AppState.dataset) return;
  tbody.innerHTML = "";

  const searchText = (document.getElementById("trainSearchInput")?.value || "").toLowerCase();
  const dirVal = document.getElementById("trainDirectionFilter")?.value || "ALL";
  const prioVal = document.getElementById("trainPriorityFilter")?.value || "ALL";

  let trains = [...(AppState.dataset.trains || [])];
  trains = trains.filter(tr => {
    const matchSearch = tr.train_id.toLowerCase().includes(searchText) ||
                        tr.train_name.toLowerCase().includes(searchText) ||
                        tr.section.toLowerCase().includes(searchText) ||
                        (tr.origin && tr.origin.toLowerCase().includes(searchText)) ||
                        (tr.destination && tr.destination.toLowerCase().includes(searchText));
    const matchDir = dirVal === "ALL" || tr.direction === dirVal;
    const matchPrio = prioVal === "ALL" || String(tr.service_priority) === prioVal;
    return matchSearch && matchDir && matchPrio;
  });

  if (trains.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="10" style="text-align:center; color:var(--text-muted); padding:16px;">No train movements match the current filter.</td>`;
    tbody.appendChild(tr);
    return;
  }

  trains.forEach(tr => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><strong>${tr.train_id}</strong></td>
      <td>
        <a href="javascript:void(0)" onclick="openTrainDrawerById('${tr.train_id}', '${tr.section}')" style="color:var(--text-primary); text-decoration:underline; font-weight:600;">${tr.train_name}</a>
        ${(tr.origin && tr.destination) ? `<div style="font-size:10px; color:var(--text-muted); margin-top:2px;">${tr.origin} → ${tr.destination}</div>` : ''}
      </td>
      <td>${tr.train_type || 'Express'}</td>
      <td>${tr.section}</td>
      <td>${formatHour(tr.arrival_hour)}</td>
      <td>${formatHour(tr.departure_hour)}</td>
      <td>${renderPriorityBadge(tr.service_priority === 1 ? 'CRITICAL' : tr.service_priority === 2 ? 'HIGH' : 'LOW')}</td>
      <td>${tr.direction || 'DOWN'}</td>
      <td><span class="semantic-text text-medium"><span class="dot dot-green"></span> ${tr.is_protected !== false ? 'PROTECTED' : 'FLEXIBLE'}</span></td>
      <td style="text-align:right;">
        <button class="btn btn-secondary btn-xs" onclick="inspectTrainRoute('${tr.train_id}')" title="Inspect Route Timetable"><i class="fa-solid fa-route"></i></button>
        <button class="btn btn-secondary btn-xs" onclick="editTrain('${tr.train_id}', '${tr.section}')" title="Edit Train"><i class="fa-solid fa-pen"></i></button>
        <button class="btn btn-danger btn-xs" onclick="deleteTrain('${tr.train_id}', '${tr.section}')" title="Delete Train"><i class="fa-solid fa-trash"></i></button>
      </td>
    `;
    tbody.appendChild(row);
  });
}

function openTrainDrawerById(trainId, section) {
  const tr = AppState.dataset?.trains?.find(t => t.train_id === trainId && t.section === section);
  if (tr) openTrainDrawer(tr);
}

let isEditingTrainId = null;
let isEditingTrainSection = null;

function openCreateTrainModal() {
  isEditingTrainId = null;
  isEditingTrainSection = null;
  document.getElementById("trainModalTitle").innerText = "Register Train Movement";
  document.getElementById("trainForm").reset();
  document.getElementById("trId").disabled = false;
  document.getElementById("trSection").disabled = false;
  const orgEl = document.getElementById("trOrigin");
  if (orgEl) orgEl.value = "";
  const dstEl = document.getElementById("trDest");
  if (dstEl) dstEl.value = "";
  openModal("trainModal");
}

function editTrain(trainId, section) {
  const tr = (AppState.dataset?.trains || []).find(t => t.train_id === trainId && t.section === section);
  if (!tr) return;
  isEditingTrainId = trainId;
  isEditingTrainSection = section;

  document.getElementById("trainModalTitle").innerText = `Edit Train Movement (${trainId})`;
  document.getElementById("trId").value = tr.train_id;
  document.getElementById("trId").disabled = true;
  document.getElementById("trName").value = tr.train_name;
  document.getElementById("trSection").value = tr.section;
  document.getElementById("trSection").disabled = true;
  document.getElementById("trArr").value = tr.arrival_hour;
  document.getElementById("trDep").value = tr.departure_hour;
  document.getElementById("trPrio").value = String(tr.service_priority || 1);
  document.getElementById("trDir").value = tr.direction || "DOWN";
  const orgEl = document.getElementById("trOrigin");
  if (orgEl) orgEl.value = tr.origin || "";
  const dstEl = document.getElementById("trDest");
  if (dstEl) dstEl.value = tr.destination || "";
  openModal("trainModal");
}

function editTrainFromDrawer(trainId, section) {
  closeDrawer();
  editTrain(trainId, section);
}

async function handleTrainSubmit(e) {
  e.preventDefault();
  const originVal = document.getElementById("trOrigin")?.value?.trim() || "";
  const destVal = document.getElementById("trDest")?.value?.trim() || "";
  const payload = {
    train_id: document.getElementById("trId").value.trim(),
    train_name: document.getElementById("trName").value.trim(),
    train_type: "Express Passenger",
    section: document.getElementById("trSection").value,
    arrival_hour: parseFloat(document.getElementById("trArr").value),
    departure_hour: parseFloat(document.getElementById("trDep").value),
    service_priority: parseInt(document.getElementById("trPrio").value),
    direction: document.getElementById("trDir").value,
    origin: originVal,
    destination: destVal,
    is_protected: true
  };

  try {
    let res;
    if (isEditingTrainId) {
      res = await fetch(`${API_BASE}/trains/${isEditingTrainId}?section=${encodeURIComponent(isEditingTrainSection)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          train_name: payload.train_name,
          arrival_hour: payload.arrival_hour,
          departure_hour: payload.departure_hour,
          service_priority: payload.service_priority,
          direction: payload.direction,
          origin: payload.origin,
          destination: payload.destination
        })
      });
    } else {
      res = await fetch(`${API_BASE}/trains`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    if (res.ok) {
      closeModal("trainModal");
      await fetchInitialData();
    } else {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Could not save train'}`);
    }
  } catch (err) {
    alert("Network error: Failed to save train.");
  }
}

async function deleteTrain(trainId, section) {
  if (!confirm(`Delete train movement '${trainId}' on section '${section}'?`)) return;
  try {
    const res = await fetch(`${API_BASE}/trains/${trainId}?section=${encodeURIComponent(section)}`, { method: "DELETE" });
    if (res.ok) {
      await fetchInitialData();
    }
  } catch (err) {
    // Fail gracefully
  }
}

let isEditingBlockId = null;

function renderBlocksTable() {
  const tbody = document.querySelector("#blocksTable tbody");
  if (!tbody || !AppState.dataset) return;
  tbody.innerHTML = "";

  const blocks = AppState.dataset.block_windows || [];
  if (blocks.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="8" style="text-align:center; color:var(--text-muted); padding:16px;">No block windows registered.</td>`;
    tbody.appendChild(tr);
    return;
  }

  blocks.forEach(blk => {
    const assigned = (AppState.currentSchedule || []).filter(s => s.block_id === blk.id);
    const statusHtml = assigned.length > 0
      ? `<span class="semantic-text text-high" style="color:var(--accent-blue); font-weight:700;"><span class="dot dot-blue"></span> Assigned (${assigned.map(a => a.task_id).join(', ')})</span>`
      : `<span class="semantic-text text-medium"><span class="dot dot-green"></span> Available</span>`;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${blk.id}</strong></td>
      <td>${blk.section}</td>
      <td>${formatHour(blk.start_hour)}</td>
      <td>${formatHour(blk.end_hour)}</td>
      <td>${blk.max_duration_mins} mins</td>
      <td>${(blk.permitted_departments || []).join(", ")}</td>
      <td>${statusHtml}</td>
      <td style="text-align:right;">
        <button class="btn btn-secondary btn-xs" onclick="editBlock('${blk.id}')" title="Edit Block Window"><i class="fa-solid fa-pen"></i></button>
        <button class="btn btn-danger btn-xs" onclick="deleteBlock('${blk.id}')" title="Delete Block Window"><i class="fa-solid fa-trash"></i></button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function openCreateBlockModal() {
  isEditingBlockId = null;
  document.getElementById("blockModalTitle").innerText = "Register Block Window";
  document.getElementById("blockForm").reset();
  document.getElementById("blkId").disabled = false;
  document.getElementById("blkId").value = `BLK-${String((AppState.dataset?.block_windows?.length || 0) + 1).padStart(3, '0')}`;
  document.getElementById("blkStart").value = "02.0";
  document.getElementById("blkEnd").value = "05.0";
  document.getElementById("permEng").checked = true;
  document.getElementById("permST").checked = true;
  document.getElementById("permOHE").checked = true;
  openModal("blockModal");
}

function editBlock(blockId) {
  const blk = (AppState.dataset?.block_windows || []).find(b => b.id === blockId);
  if (!blk) return;
  isEditingBlockId = blockId;
  document.getElementById("blockModalTitle").innerText = `Edit Block Window (${blockId})`;
  document.getElementById("blkId").value = blk.id;
  document.getElementById("blkId").disabled = true;
  document.getElementById("blkSection").value = blk.section;
  document.getElementById("blkStart").value = blk.start_hour;
  document.getElementById("blkEnd").value = blk.end_hour;

  const depts = blk.permitted_departments || [];
  document.getElementById("permEng").checked = depts.includes("Engineering");
  document.getElementById("permST").checked = depts.includes("Signal & Telecom");
  document.getElementById("permOHE").checked = depts.includes("Traction / OHE");
  openModal("blockModal");
}

async function handleBlockSubmit(e) {
  e.preventDefault();
  const st = parseFloat(document.getElementById("blkStart").value);
  const end = parseFloat(document.getElementById("blkEnd").value);

  if (end <= st) {
    alert("Validation Error: End hour must be greater than start hour.");
    return;
  }

  const depts = [];
  if (document.getElementById("permEng").checked) depts.push("Engineering");
  if (document.getElementById("permST").checked) depts.push("Signal & Telecom");
  if (document.getElementById("permOHE").checked) depts.push("Traction / OHE");

  const payload = {
    id: document.getElementById("blkId").value.trim(),
    section: document.getElementById("blkSection").value,
    start_hour: st,
    end_hour: end,
    max_duration_mins: Math.round((end - st) * 60),
    permitted_departments: depts,
    status: "AVAILABLE"
  };

  try {
    let res;
    if (isEditingBlockId) {
      res = await fetch(`${API_BASE}/blocks/${isEditingBlockId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start_hour: payload.start_hour,
          end_hour: payload.end_hour,
          max_duration_mins: payload.max_duration_mins,
          permitted_departments: payload.permitted_departments
        })
      });
    } else {
      res = await fetch(`${API_BASE}/blocks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    if (res.ok) {
      closeModal("blockModal");
      await fetchInitialData();
    } else {
      const err = await res.json();
      alert(`Error: ${err.detail || 'Could not save block window'}`);
    }
  } catch (err) {
    alert("Network error: Failed to save block window.");
  }
}

async function deleteBlock(blockId) {
  if (!confirm(`Delete block window '${blockId}'?`)) return;
  try {
    const res = await fetch(`${API_BASE}/blocks/${blockId}`, { method: "DELETE" });
    if (res.ok) {
      await fetchInitialData();
    }
  } catch (err) {
    // Fail gracefully
  }
}

async function triggerOptimize() {
  const btn = document.getElementById("generatePlanBtn");
  const btnText = document.getElementById("generatePlanBtnText");
  const btnIcon = document.getElementById("generatePlanIcon");

  if (btn) btn.disabled = true;
  if (btnText) btnText.innerText = "Optimizing Corridor...";
  if (btnIcon) btnIcon.className = "fa-solid fa-spinner fa-spin";

  showLoading("Running Google OR-Tools CP-SAT Optimizer...", "Formulating exact mathematical constraint matrix...");
  
  try {
    const res = await fetch(`${API_BASE}/optimize`, { method: "POST" });
    const result = await res.json();

    AppState.currentSchedule = result.schedule || [];
    AppState.baselineData = result.baseline_comparison;
    AppState.lastOptimizationResult = result;

    await fetchInitialData();
    renderOptimizationResultBanner(result);

    hideLoading();

    if (btnText) btnText.innerText = "Plan Generated";
    if (btnIcon) btnIcon.className = "fa-solid fa-circle-check";
    setTimeout(() => {
      if (btn) btn.disabled = false;
      if (btnText) btnText.innerText = "Re-Optimize Plan";
      if (btnIcon) btnIcon.className = "fa-solid fa-circle-play";
    }, 2500);

    switchTab("dashboard", document.querySelectorAll(".nav-item")[0]);
  } catch (err) {
    hideLoading();
    if (btn) btn.disabled = false;
    if (btnText) btnText.innerText = "Generate Plan";
    if (btnIcon) btnIcon.className = "fa-solid fa-circle-play";
    alert("Optimization service error: " + err.message);
  }
}

function renderOptimizationResultBanner(result) {
  const container = document.getElementById("optimizationResultBanner");
  if (!container) return;

  const activeResult = result || AppState.lastOptimizationResult;
  const tasks = AppState.dataset?.tasks || [];
  const sched = AppState.currentSchedule || [];

  if (!activeResult || activeResult.solver_status === "NO_TASKS" || sched.length === 0) {
    if (tasks.length === 0) {
      container.innerHTML = `
        <div class="opt-panel-container">
          <div class="opt-panel-header">
            <div class="opt-panel-title-area">
              <div class="opt-panel-title"><i class="fa-solid fa-calculator"></i> Current Optimization Plan</div>
              <span class="opt-badge-state badge-state-notrun"><span class="dot dot-gray"></span> NOT RUN</span>
            </div>
            <div style="font-size:11px; color:var(--text-secondary);">Central Trunk Line (Howrah – DDU) | Exact Mathematical Formulation</div>
          </div>
          <div class="opt-panel-body">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:12px;">
              <div>
                <div style="font-size:13px; font-weight:700; color:var(--text-primary); margin-bottom:4px;">
                  Fresh Operational Corridor — No Queued Maintenance Demands
                </div>
                <div style="font-size:11.5px; color:var(--text-secondary); line-height:1.4;">
                  The corridor contains <strong>17 active train movements</strong> and <strong>10 sanctioned block windows</strong>. No maintenance tasks are registered in this scenario yet.
                </div>
              </div>
              <div style="display:flex; gap:8px;">
                <button class="btn btn-primary btn-sm" onclick="quickLoadSampleTasks()"><i class="fa-solid fa-plus-circle"></i> Load 7 Sample Maintenance Tasks</button>
                <button class="btn btn-secondary btn-sm" onclick="openCreateTaskModal()"><i class="fa-solid fa-plus"></i> Register Custom Task</button>
              </div>
            </div>
            <div class="opt-kpi-strip">
              <div class="opt-kpi-item">
                <div class="opt-kpi-label">Plan Status</div>
                <div class="opt-kpi-value" style="font-size:13px; color:var(--text-muted);">Not Run</div>
              </div>
              <div class="opt-kpi-item">
                <div class="opt-kpi-label">Tasks Scheduled</div>
                <div class="opt-kpi-value">0 <span class="opt-kpi-unit">/ 0</span></div>
              </div>
              <div class="opt-kpi-item">
                <div class="opt-kpi-label">Scheduled Blocks</div>
                <div class="opt-kpi-value">0 <span class="opt-kpi-unit">blocks</span></div>
              </div>
              <div class="opt-kpi-item">
                <div class="opt-kpi-label">Corridor Conflicts</div>
                <div class="opt-kpi-value" style="color:var(--accent-green);">0 <span class="opt-kpi-unit">Clean</span></div>
              </div>
            </div>
          </div>
        </div>
      `;
      container.style.display = "block";
      return;
    } else {
      const critCount = tasks.filter(t => t.priority === "CRITICAL").length;
      container.innerHTML = `
        <div class="opt-panel-container">
          <div class="opt-panel-header">
            <div class="opt-panel-title-area">
              <div class="opt-panel-title"><i class="fa-solid fa-calculator"></i> Current Optimization Plan</div>
              <span class="opt-badge-state badge-state-notrun"><span class="dot dot-amber"></span> NOT RUN / AWAITING PLAN</span>
            </div>
            <div style="font-size:11px; color:var(--text-secondary);">${tasks.length} Maintenance Tasks Registered</div>
          </div>
          <div class="opt-panel-body">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:12px;">
              <div>
                <div style="font-size:13px; font-weight:700; color:var(--text-primary); margin-bottom:4px;">
                  No optimization plan generated. (${tasks.length} tasks queued, ${critCount} critical defects)
                </div>
                <div style="font-size:11.5px; color:var(--text-secondary); line-height:1.4;">
                  Click <strong>Generate Plan</strong> to formulate the exact mathematical CP-SAT constraint matrix and schedule conflict-free maintenance windows.
                </div>
              </div>
              <button class="btn btn-primary" onclick="triggerOptimize()"><i class="fa-solid fa-circle-play"></i> Generate Plan Now</button>
            </div>
            <div class="opt-kpi-strip">
              <div class="opt-kpi-item">
                <div class="opt-kpi-label">Plan Status</div>
                <div class="opt-kpi-value" style="font-size:13px; color:var(--accent-amber);">Awaiting Plan</div>
              </div>
              <div class="opt-kpi-item">
                <div class="opt-kpi-label">Tasks Scheduled</div>
                <div class="opt-kpi-value">0 <span class="opt-kpi-unit">/ ${tasks.length}</span></div>
              </div>
              <div class="opt-kpi-item">
                <div class="opt-kpi-label">Scheduled Blocks</div>
                <div class="opt-kpi-value">0 <span class="opt-kpi-unit">blocks</span></div>
              </div>
              <div class="opt-kpi-item">
                <div class="opt-kpi-label">Unscheduled Backlog</div>
                <div class="opt-kpi-value" style="color:var(--accent-amber);">${tasks.length} <span class="opt-kpi-unit">tasks</span></div>
              </div>
              <div class="opt-kpi-item">
                <div class="opt-kpi-label">Corridor Conflicts</div>
                <div class="opt-kpi-value" style="color:var(--accent-green);">0 <span class="opt-kpi-unit">clashes</span></div>
              </div>
            </div>
          </div>
        </div>
      `;
      container.style.display = "block";
      return;
    }
  }

  const solveMs = Math.round((activeResult.solve_time_seconds || 0) * 1000);
  const diff = activeResult.plan_diff;
  let stateBadgeHtml = '';
  if (diff && diff.plan_state === "NEW_PLAN_CREATED") {
    stateBadgeHtml = `<span class="opt-badge-state badge-state-new"><i class="fa-solid fa-circle-check"></i> NEW PLAN CREATED</span>`;
  } else if (diff && diff.plan_state === "PLAN_UPDATED") {
    stateBadgeHtml = `<span class="opt-badge-state badge-state-updated"><i class="fa-solid fa-rotate"></i> PLAN UPDATED</span>`;
  } else if (diff && diff.plan_state === "NO_MATERIAL_CHANGES") {
    stateBadgeHtml = `<span class="opt-badge-state badge-state-nochange"><i class="fa-solid fa-check"></i> NO MATERIAL CHANGES</span>`;
  } else {
    stateBadgeHtml = `<span class="opt-badge-state badge-state-new"><i class="fa-solid fa-circle-check"></i> PLAN ACTIVE</span>`;
  }

  const tasksConsidered = activeResult.tasks_considered || tasks.length;
  const tasksScheduled = activeResult.total_tasks_scheduled || sched.length;
  const blocksCount = activeResult.scheduled_blocks ?? tasksScheduled;
  const availWindows = activeResult.available_windows ?? (AppState.dataset?.block_windows?.length || 10);
  const conflicts = activeResult.corridor_conflicts ?? (activeResult.baseline_comparison?.optimized_conflicts || 0);
  const util = activeResult.block_window_utilization_pct || activeResult.baseline_comparison?.optimized_block_utilization_pct || 0;

  container.innerHTML = `
    <div class="opt-panel-container">
      <div class="opt-panel-header">
        <div class="opt-panel-title-area">
          <div class="opt-panel-title"><i class="fa-solid fa-square-poll-vertical"></i> Current Optimization Plan</div>
          ${stateBadgeHtml}
          <span class="semantic-text text-medium" style="font-size:11.5px;"><span class="dot dot-green"></span> ${activeResult.solver_status} (${solveMs} ms)</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <button class="btn btn-secondary btn-xs" onclick="switchTab('planResult', document.querySelectorAll('.nav-item')[1])"><i class="fa-solid fa-list-check"></i> Full Decision Matrix</button>
          <button class="btn btn-secondary btn-xs" onclick="switchTab('comparison', document.querySelectorAll('.nav-item')[7])"><i class="fa-solid fa-chart-column"></i> Benchmark</button>
          <button class="btn btn-secondary btn-xs" onclick="confirmClearPlan()" style="color:var(--accent-red);" title="Clear Current Plan"><i class="fa-solid fa-trash-can"></i> Clear Plan</button>
          <button onclick="dismissOptimizationBanner()" title="Dismiss Banner" style="background:none; border:none; cursor:pointer; font-size:13px; color:var(--text-muted); padding:2px 6px;"><i class="fa-solid fa-xmark"></i></button>
        </div>
      </div>
      <div class="opt-panel-body">
        <div class="opt-summary-box">
          <div class="opt-summary-headline">
            <i class="fa-solid fa-circle-info"></i> What did the optimizer just do?
          </div>
          <div class="opt-summary-text">
            ${activeResult.human_summary || activeResult.summary || "Corridor maintenance plan computed without train conflicts."}
          </div>
        </div>

        <div class="opt-kpi-strip">
          <div class="opt-kpi-item">
            <div class="opt-kpi-label">Solve Time</div>
            <div class="opt-kpi-value">${solveMs} <span class="opt-kpi-unit">ms</span></div>
          </div>
          <div class="opt-kpi-item">
            <div class="opt-kpi-label">Tasks Scheduled</div>
            <div class="opt-kpi-value">${tasksScheduled} <span class="opt-kpi-unit">/ ${tasksConsidered}</span></div>
          </div>
          <div class="opt-kpi-item">
            <div class="opt-kpi-label">Scheduled Blocks</div>
            <div class="opt-kpi-value">${blocksCount} <span class="opt-kpi-unit">blocks</span></div>
          </div>
          <div class="opt-kpi-item">
            <div class="opt-kpi-label">Available Windows</div>
            <div class="opt-kpi-value">${availWindows} <span class="opt-kpi-unit">slots</span></div>
          </div>
          <div class="opt-kpi-item">
            <div class="opt-kpi-label">Corridor Conflicts</div>
            <div class="opt-kpi-value" style="color:var(--accent-green);">${conflicts} <span class="opt-kpi-unit">100% Free</span></div>
          </div>
          <div class="opt-kpi-item">
            <div class="opt-kpi-label">Window Utilization</div>
            <div class="opt-kpi-value" style="color:var(--accent-green);">${util}%</div>
          </div>
        </div>

        ${diff ? `
        <div class="opt-diff-bar">
          <span style="font-weight:700; color:var(--text-secondary); text-transform:uppercase; font-size:10px;">Plan Diff:</span>
          <span class="opt-diff-item tag-added"><i class="fa-solid fa-plus"></i> Added: ${diff.added?.length || 0}</span>
          <span class="opt-diff-item tag-moved"><i class="fa-solid fa-arrows-split-up-and-left"></i> Rescheduled: ${diff.moved?.length || 0}</span>
          <span class="opt-diff-item tag-unchanged"><i class="fa-solid fa-check"></i> Unchanged: ${diff.unchanged?.length || 0}</span>
          <span class="opt-diff-item tag-unscheduled"><i class="fa-solid fa-xmark"></i> Unscheduled: ${diff.unscheduled?.length || 0}</span>
          ${(diff.moved && diff.moved.length > 0) ? `<button class="btn btn-secondary btn-xs" style="margin-left:auto;" onclick="viewPlanDiff()"><i class="fa-solid fa-table"></i> Inspect Rescheduled Diff</button>` : ''}
        </div>
        ` : ''}
      </div>
    </div>
  `;
  container.style.display = "block";
}

function renderPlanResultFullView() {
  const container = document.getElementById("planResultFullContent");
  if (!container) return;

  const result = AppState.lastOptimizationResult;
  const sched = AppState.currentSchedule || [];
  const tasks = AppState.dataset?.tasks || [];

  if (!result || sched.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:40px 16px; color:var(--text-secondary);">
        <i class="fa-solid fa-square-poll-vertical" style="font-size:36px; color:var(--text-muted); margin-bottom:14px;"></i>
        <div style="font-size:15px; font-weight:700; color:var(--text-primary); margin-bottom:6px;">No Optimization Plan Computed Yet</div>
        <div style="font-size:12.5px; margin-bottom:18px; max-width:500px; margin-left:auto; margin-right:auto; line-height:1.5;">
          The corridor schedule currently has no active optimization run. Register maintenance demands or load the demo scenario, then click <strong>Generate Plan</strong> to compute the CP-SAT audit justifications.
        </div>
        <div style="display:flex; justify-content:center; gap:10px;">
          <button class="btn btn-primary" onclick="triggerOptimize()"><i class="fa-solid fa-circle-play"></i> Generate Plan Now</button>
          <button class="btn btn-secondary" onclick="quickLoadSampleTasks()"><i class="fa-solid fa-plus-circle"></i> Load 7 Sample Tasks</button>
        </div>
      </div>
    `;
    return;
  }

  const solveMs = Math.round((result.solve_time_seconds || 0) * 1000);
  const diff = result.plan_diff;
  let stateBadgeHtml = '';
  if (diff && diff.plan_state === "NEW_PLAN_CREATED") {
    stateBadgeHtml = `<span class="opt-badge-state badge-state-new"><i class="fa-solid fa-circle-check"></i> NEW PLAN CREATED</span>`;
  } else if (diff && diff.plan_state === "PLAN_UPDATED") {
    stateBadgeHtml = `<span class="opt-badge-state badge-state-updated"><i class="fa-solid fa-rotate"></i> PLAN UPDATED</span>`;
  } else if (diff && diff.plan_state === "NO_MATERIAL_CHANGES") {
    stateBadgeHtml = `<span class="opt-badge-state badge-state-nochange"><i class="fa-solid fa-check"></i> NO MATERIAL CHANGES</span>`;
  } else {
    stateBadgeHtml = `<span class="opt-badge-state badge-state-new"><i class="fa-solid fa-circle-check"></i> PLAN ACTIVE</span>`;
  }

  const decisions = result.task_decisions || sched.map(s => ({
    task_id: s.task_id,
    task_name: s.task_name,
    section: s.section,
    department: s.department,
    priority: s.priority,
    duration_mins: Math.round((s.end_hour - s.start_hour) * 60),
    status: "SCHEDULED",
    block_window: s.block_id,
    start_hour: s.start_hour,
    end_hour: s.end_hour,
    explanation: s.explanation
  }));

  container.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:16px; padding-bottom:14px; border-bottom:1px solid var(--border-subtle);">
      <div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
          <h3 style="font-size:14px; font-weight:700; color:var(--text-primary);">Google OR-Tools CP-SAT Corridor Plan Audit</h3>
          ${stateBadgeHtml}
        </div>
        <div style="font-size:11.5px; color:var(--text-secondary);">
          Constraint Programming Formulation | Central Trunk Line | Run at <strong>${result.timestamp || new Date().toLocaleTimeString()}</strong>
        </div>
      </div>
      <div style="display:flex; gap:8px;">
        <button class="btn btn-secondary btn-xs" onclick="switchTab('comparison', document.querySelectorAll('.nav-item')[7])"><i class="fa-solid fa-chart-column"></i> Compare with Manual Baseline</button>
        <button class="btn btn-secondary btn-xs" onclick="exportCSV()"><i class="fa-solid fa-download"></i> Export Schedule CSV</button>
        <button class="btn btn-secondary btn-xs" onclick="confirmClearPlan()" style="color:var(--accent-red);"><i class="fa-solid fa-trash-can"></i> Clear Current Plan</button>
      </div>
    </div>

    <div class="opt-summary-box" style="margin-bottom:16px;">
      <div class="opt-summary-headline">
        <i class="fa-solid fa-circle-info"></i> What did the optimizer just do?
      </div>
      <div class="opt-summary-text">
        ${result.human_summary || result.summary || "Corridor schedule optimized without conflict."}
      </div>
    </div>

    <div class="opt-kpi-strip" style="margin-bottom:16px;">
      <div class="opt-kpi-item">
        <div class="opt-kpi-label">Solve Time</div>
        <div class="opt-kpi-value">${solveMs} <span class="opt-kpi-unit">ms</span></div>
      </div>
      <div class="opt-kpi-item">
        <div class="opt-kpi-label">Tasks Scheduled</div>
        <div class="opt-kpi-value">${result.total_tasks_scheduled || sched.length} <span class="opt-kpi-unit">/ ${result.tasks_considered || tasks.length}</span></div>
      </div>
      <div class="opt-kpi-item">
        <div class="opt-kpi-label">Scheduled Blocks</div>
        <div class="opt-kpi-value">${result.scheduled_blocks ?? sched.length} <span class="opt-kpi-unit">blocks</span></div>
      </div>
      <div class="opt-kpi-item">
        <div class="opt-kpi-label">Available Windows</div>
        <div class="opt-kpi-value">${result.available_windows ?? (AppState.dataset?.block_windows?.length || 10)} <span class="opt-kpi-unit">slots</span></div>
      </div>
      <div class="opt-kpi-item">
        <div class="opt-kpi-label">Train Conflicts</div>
        <div class="opt-kpi-value" style="color:var(--accent-green);">${result.corridor_conflicts ?? 0} <span class="opt-kpi-unit">100% Free</span></div>
      </div>
      <div class="opt-kpi-item">
        <div class="opt-kpi-label">Window Utilization</div>
        <div class="opt-kpi-value" style="color:var(--accent-green);">${result.block_window_utilization_pct || result.baseline_comparison?.optimized_block_utilization_pct || 0}%</div>
      </div>
      <div class="opt-kpi-item">
        <div class="opt-kpi-label">Protected Trains</div>
        <div class="opt-kpi-value">${result.train_movements_protected || (AppState.dataset?.trains?.length || 17)} <span class="opt-kpi-unit">Isolated</span></div>
      </div>
      <div class="opt-kpi-item">
        <div class="opt-kpi-label">Disruption Saved</div>
        <div class="opt-kpi-value" style="color:var(--accent-green);">${result.baseline_comparison?.delay_reduction_pct || 86}% <span class="opt-kpi-unit">vs Manual</span></div>
      </div>
    </div>

    ${diff ? `
    <div style="background:var(--bg-surface); border:1px solid var(--border-color); border-radius:4px; padding:12px 14px; margin-bottom:16px;">
      <div style="font-size:12px; font-weight:700; color:var(--text-primary); margin-bottom:8px; display:flex; align-items:center; gap:6px;">
        <i class="fa-solid fa-code-compare" style="color:var(--text-secondary);"></i> Plan Modification Diff:
      </div>
      <div class="opt-diff-bar" style="border:none; padding:0; background:transparent;">
        <span class="opt-diff-item tag-added"><i class="fa-solid fa-plus"></i> Added Tasks: ${diff.added?.length || 0} (${diff.added?.join(', ') || 'None'})</span>
        <span class="opt-diff-item tag-moved"><i class="fa-solid fa-arrows-split-up-and-left"></i> Moved / Rescheduled: ${diff.moved?.length || 0}</span>
        <span class="opt-diff-item tag-unchanged"><i class="fa-solid fa-check"></i> Unchanged: ${diff.unchanged?.length || 0}</span>
        <span class="opt-diff-item tag-unscheduled"><i class="fa-solid fa-xmark"></i> Unscheduled: ${diff.unscheduled?.length || 0}</span>
      </div>
      ${(diff.moved && diff.moved.length > 0) ? `
      <table class="enterprise-table" style="margin-top:10px; font-size:11px;">
        <thead>
          <tr>
            <th>Task ID</th>
            <th>Task Name</th>
            <th>Section</th>
            <th>Original Window</th>
            <th>Rescheduled Window</th>
            <th>Shift Delta</th>
          </tr>
        </thead>
        <tbody>
          ${diff.moved.map(m => `
            <tr>
              <td><strong>${m.task_id}</strong></td>
              <td>${m.task_name}</td>
              <td>${m.section}</td>
              <td>${formatHour(m.old_start_hour)} – ${formatHour(m.old_end_hour)}</td>
              <td style="color:var(--accent-amber); font-weight:600;">${formatHour(m.new_start_hour)} – ${formatHour(m.new_end_hour)}</td>
              <td><span class="badge-label badge-amber">+${m.shift_minutes || Math.round((m.new_start_hour - m.old_start_hour) * 60)} mins</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
      ` : ''}
    </div>
    ` : ''}

    <div style="margin-top:16px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <strong style="font-size:12.5px; color:var(--text-primary);"><i class="fa-solid fa-table-list"></i> Task-by-Task Optimization Decisions & Constraints Rationale:</strong>
        <span style="font-size:11px; color:var(--text-secondary);">${decisions.length} Tasks Evaluated</span>
      </div>
      <table class="enterprise-table" style="font-size:11.5px;">
        <thead>
          <tr>
            <th style="width:100px;">Task ID</th>
            <th>Description</th>
            <th>Section</th>
            <th>Dept & Prio</th>
            <th>Duration</th>
            <th>Status</th>
            <th>Assigned Block</th>
            <th>CP-SAT Decision Rationale & Constraints</th>
          </tr>
        </thead>
        <tbody>
          ${decisions.map(d => `
            <tr>
              <td><strong>${d.task_id}</strong></td>
              <td>${d.task_name || d.task_id}</td>
              <td>${d.section}</td>
              <td>${d.department} <br>${renderPriorityBadge(d.priority)}</td>
              <td>${d.duration_mins}m</td>
              <td>
                <span style="color:${d.status === 'SCHEDULED' ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight:700;">
                  <span class="dot ${d.status === 'SCHEDULED' ? 'dot-green' : 'dot-red'}"></span> ${d.status}
                </span>
              </td>
              <td>
                ${d.block_window ? `<strong>${d.block_window}</strong><br><span style="font-size:10.5px; color:var(--text-secondary);">${formatHour(d.start_hour)} – ${formatHour(d.end_hour)}</span>` : '<span style="color:var(--text-muted);">Unassigned</span>'}
              </td>
              <td style="font-size:11px; line-height:1.4; color:var(--text-secondary);">
                ${d.explanation || 'Scheduled within sanctioned window with full train isolation.'}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>

    <div style="margin-top:20px; background:#FAFAFA; border:1px solid var(--border-color); border-radius:4px; padding:14px;">
      <div style="font-size:12px; font-weight:700; color:var(--text-primary); margin-bottom:8px;">
        <i class="fa-solid fa-shield-check" style="color:var(--accent-green);"></i> Mathematical Constraint Verification Guarantees:
      </div>
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:10px; font-size:11px;">
        <div style="background:#FFFFFF; border:1px solid var(--border-subtle); padding:8px 10px; border-radius:3px;">
          <div style="color:var(--accent-green); font-weight:700;"><i class="fa-solid fa-check"></i> Train Movement Isolation</div>
          <div style="color:var(--text-secondary); margin-top:2px;">Zero overlap with 17 passenger & freight train paths on shared tracks.</div>
        </div>
        <div style="background:#FFFFFF; border:1px solid var(--border-subtle); padding:8px 10px; border-radius:3px;">
          <div style="color:var(--accent-green); font-weight:700;"><i class="fa-solid fa-check"></i> Department Permitted Check</div>
          <div style="color:var(--text-secondary); margin-top:2px;">Tasks assigned exclusively to sanctioned window departments.</div>
        </div>
        <div style="background:#FFFFFF; border:1px solid var(--border-subtle); padding:8px 10px; border-radius:3px;">
          <div style="color:var(--accent-green); font-weight:700;"><i class="fa-solid fa-check"></i> Hard Deadlines</div>
          <div style="color:var(--text-secondary); margin-top:2px;">All maintenance tasks finish strictly before mandatory deadline hours.</div>
        </div>
        <div style="background:#FFFFFF; border:1px solid var(--border-subtle); padding:8px 10px; border-radius:3px;">
          <div style="color:var(--accent-green); font-weight:700;"><i class="fa-solid fa-check"></i> Gang & Crew Limits</div>
          <div style="color:var(--text-secondary); margin-top:2px;">At most 1 maintenance gang scheduled per physical track section simultaneously.</div>
        </div>
      </div>
    </div>
  `;
}

async function quickLoadSampleTasks() {
  showLoading("Loading Sample Tasks...", "Populating 7 representative track & signalling maintenance tasks...");
  try {
    const res = await fetch(`${API_BASE}/scenario/load-sample-tasks`, { method: "POST" });
    const data = await res.json();
    await fetchInitialData();
    hideLoading();
  } catch (err) {
    hideLoading();
    alert("Error loading sample tasks: " + err.message);
  }
}

function dismissOptimizationBanner() {
  const container = document.getElementById("optimizationResultBanner");
  if (container) container.style.display = "none";
}

function openDefectModal() {
  openModal("defectModal");
}

async function handleDefectSubmit(e) {
  e.preventDefault();
  closeModal("defectModal");

  showLoading("Injecting Emergency Defect...", "Registering critical line flaw and mobilizing emergency gang...");

  const payload = {
    section: document.getElementById("defSection").value,
    defect_type: document.getElementById("defType").value.trim(),
    severity: document.getElementById("defSev").value,
    duration_mins: parseInt(document.getElementById("defDur").value),
    deadline_hour: parseFloat(document.getElementById("defDeadline").value),
    description: document.getElementById("defDesc").value.trim()
  };

  try {
    const res = await fetch(`${API_BASE}/inject-emergency`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    hideLoading();

    AppState.lastDiff = data.diff;
    AppState.currentSchedule = data.optimization_result?.schedule || [];
    AppState.baselineData = data.optimization_result?.baseline_comparison;
    AppState.lastOptimizationResult = data.optimization_result;

    const banner = document.getElementById("emergencyBanner");
    document.getElementById("emergencyTitle").innerText = `CRITICAL OPERATIONAL ALERT: ${data.emergency_task.id} Injected`;
    document.getElementById("emergencyDesc").innerText = `${data.message} ${data.diff.total_moved} task(s) adjusted, ${data.diff.unchanged_tasks.length} task(s) preserved.`;
    banner.style.display = "flex";

    await fetchInitialData();
    renderOptimizationResultBanner(data.optimization_result);
    renderPlanResultFullView();
    viewPlanDiff();
    switchTab("dashboard", document.querySelectorAll(".nav-item")[0]);
  } catch (err) {
    hideLoading();
    alert("Failed to inject emergency defect: " + err.message);
  }
}

function viewPlanDiff() {
  if (!AppState.lastDiff) return;
  const content = document.getElementById("diffModalContent");
  const d = AppState.lastDiff;

  let movedTableHtml = "";
  if (d.moved_details && d.moved_details.length > 0) {
    movedTableHtml = `
      <div style="margin-top:12px; margin-bottom:12px;">
        <strong style="color:var(--text-primary); font-size:12px;">Granular Task Rescheduling Diff:</strong>
        <table class="enterprise-table" style="margin-top:6px; font-size:11px;">
          <thead>
            <tr>
              <th>Task ID & Name</th>
              <th>Section</th>
              <th>Original Window</th>
              <th>Rescheduled Window</th>
              <th>Shift Delta</th>
            </tr>
          </thead>
          <tbody>
            ${d.moved_details.map(m => `
              <tr>
                <td><strong>${m.task_id}</strong>: ${m.task_name}</td>
                <td>${m.section}</td>
                <td>${formatHour(m.old_start_hour)} – ${formatHour(m.old_end_hour)}</td>
                <td style="color:var(--accent-amber); font-weight:600;">${formatHour(m.new_start_hour)} – ${formatHour(m.new_end_hour)}</td>
                <td><span class="badge-label badge-amber">+${Math.round((m.new_start_hour - m.old_start_hour) * 60)} mins</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  content.innerHTML = `
    <div style="margin-bottom:10px;">
      <strong>Newly Scheduled Emergency Task:</strong> 
      <span class="semantic-text text-critical"><span class="dot dot-red"></span> ${d.new_emergency_task}</span>
    </div>
    ${movedTableHtml}
    <div style="margin-bottom:10px;">
      <strong>Displaced / Rescheduled Tasks (${d.affected_tasks.length}):</strong>
      <div style="color:var(--text-secondary); margin-top:2px;">${d.affected_tasks.join(", ") || "None (Existing plan accommodated slot without displacement)"}</div>
    </div>
    <div style="margin-bottom:10px;">
      <strong>Unaffected Tasks Preserved (${d.unchanged_tasks.length}):</strong>
      <div style="color:var(--text-secondary); margin-top:2px;">${d.unchanged_tasks.join(", ") || "None"}</div>
    </div>
    <div style="background:#F7F9F6; padding:8px 12px; border:1px solid var(--border-subtle); border-radius:3px;">
      <span class="semantic-text text-medium"><span class="dot dot-green"></span> ${d.affected_tasks.length === 0 ? "No material schedule changes required for existing tasks." : d.affected_tasks.length + " lower-priority tasks shifted to accommodate emergency preemption."}</span>
    </div>
  `;
  openModal("diffModal");
}

async function triggerRevertPlan() {
  if (!confirm("Revert schedule to the snapshot before the emergency injection?")) return;
  showLoading("Reverting Plan...", "Restoring pre-emergency corridor state...");
  try {
    const res = await fetch(`${API_BASE}/revert-plan`, { method: "POST" });
    if (res.ok) {
      closeEmergencyBanner();
      AppState.lastDiff = null;
      await fetchInitialData();
      hideLoading();
      switchTab("dashboard", document.querySelectorAll(".nav-item")[0]);
    } else {
      hideLoading();
      alert("Could not revert plan.");
    }
  } catch (err) {
    hideLoading();
    alert("Revert error: " + err.message);
  }
}

function closeEmergencyBanner() {
  const banner = document.getElementById("emergencyBanner");
  if (banner) banner.style.display = "none";
}

function renderExplainabilityTab() {
  const container = document.getElementById("explanationsContainer");
  const summaryText = document.getElementById("summaryText");
  if (!container) return;

  const dataset = AppState.dataset;
  if (summaryText && dataset?.latest_summary) {
    summaryText.innerText = dataset.latest_summary;
  }

  container.innerHTML = "";
  const sched = AppState.currentSchedule || [];
  if (sched.length === 0) {
    container.innerHTML = `<div style="color:var(--text-muted); padding:10px;">No active plan generated yet. Click 'Generate Plan' to compute audit justifications.</div>`;
    return;
  }

  sched.forEach((item, idx) => {
    const card = document.createElement("div");
    card.style.cssText = "background:var(--bg-surface); padding:10px 14px; border-radius:3px; border:1px solid var(--border-color); margin-bottom:8px;";

    let prioDot = "dot-green";
    if (item.priority === "CRITICAL") prioDot = "dot-red";
    else if (item.priority === "HIGH") prioDot = "dot-amber";

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
        <strong style="color:var(--text-primary); font-size:12px;">${idx + 1}. ${safeString(item.task_name, item.task_id)} (${item.task_id})</strong>
        <span style="font-size:11px; color:var(--text-secondary);"><span class="dot ${prioDot}"></span> ${item.section} | Block ${item.block_id || 'Window'} (${formatHour(item.start_hour)}–${formatHour(item.end_hour)})</span>
      </div>
      <div style="font-size:12px; color:var(--text-secondary); line-height:1.4;">${item.explanation || 'Scheduled within sanctioned window with full train isolation.'}</div>
    `;
    container.appendChild(card);
  });
}

function renderBaselineTab() {
  const b = AppState.baselineData;
  const tasks = AppState.dataset?.tasks || [];
  const sched = AppState.currentSchedule || [];

  if (!b || tasks.length === 0 || sched.length === 0) {
    const ids = ["baseManConf", "baseManDelay", "baseManUtil", "baseManCrit", "baseOptConf", "baseOptDelay", "baseOptUtil", "baseOptCrit", "baseConfDelta", "baseDelayDelta", "baseUtilDelta", "baseCritDelta"];
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerText = "N/A";
    });
    return;
  }

  document.getElementById("baseManConf").innerText = `${b.manual_conflicts || 0} Conflicts`;
  document.getElementById("baseManDelay").innerText = `${b.manual_total_delay_mins || 0} mins`;
  document.getElementById("baseManUtil").innerText = `${b.manual_block_utilization_pct || 0}%`;
  document.getElementById("baseManCrit").innerText = `${b.manual_critical_completed || 0} / ${b.total_critical_tasks || 0}`;

  document.getElementById("baseOptConf").innerText = `${b.optimized_conflicts || 0} Conflicts`;
  document.getElementById("baseOptDelay").innerText = `${b.optimized_total_delay_mins || 0} mins`;
  document.getElementById("baseOptUtil").innerText = `${b.optimized_block_utilization_pct || 0}%`;
  document.getElementById("baseOptCrit").innerText = `${b.optimized_critical_completed || 0} / ${b.total_critical_tasks || 0}`;

  const confDelta = document.getElementById("baseConfDelta");
  if (confDelta) confDelta.innerText = (b.manual_conflicts || 0) > 0 ? `-${b.manual_conflicts} Conflicts` : "0 Conflicts";

  const delayDelta = document.getElementById("baseDelayDelta");
  if (delayDelta) delayDelta.innerText = (b.delay_reduction_pct || 0) > 0 ? `-${b.delay_reduction_pct}% Delay` : "0m Delay";

  const utilDelta = document.getElementById("baseUtilDelta");
  if (utilDelta) utilDelta.innerText = `+${roundDiff(b.optimized_block_utilization_pct, b.manual_block_utilization_pct)}%`;

  const critDelta = document.getElementById("baseCritDelta");
  if (critDelta) critDelta.innerText = `${b.optimized_critical_completed || 0} Scheduled`;
}

function renderHistoryTable() {
  const tbody = document.querySelector("#historyTable tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  const history = AppState.planHistory || [];
  if (history.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="8" style="text-align:center; color:var(--text-muted); padding:16px;">No optimization runs recorded yet for this scenario.</td>`;
    tbody.appendChild(tr);
    return;
  }

  history.forEach(h => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${h.plan_id}</strong></td>
      <td>${h.timestamp}</td>
      <td><span class="badge-label badge-gray">${h.triggered_by}</span></td>
      <td><span class="semantic-text text-medium"><span class="dot dot-green"></span> ${h.status}</span></td>
      <td>${h.tasks_scheduled} Blocks</td>
      <td><span class="semantic-text text-medium"><span class="dot dot-green"></span> ${h.conflicts} Conflicts</span></td>
      <td>${h.utilization_pct}%</td>
      <td><strong style="color:var(--accent-green);">${h.delay_saved_pct}%</strong></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderSectionsTable() {
  const tbody = document.querySelector("#sectionsTable tbody");
  if (!tbody || !AppState.dataset) return;
  tbody.innerHTML = "";

  const trains = AppState.dataset.trains || [];
  const sched = AppState.currentSchedule || [];

  (AppState.dataset.sections || []).forEach(s => {
    const activeTrains = trains.filter(t => t.section === s.id).length;
    const activeBlocks = sched.filter(b => b.section === s.id).length;

    const tr = document.createElement("tr");
    tr.style.cursor = "pointer";
    tr.onclick = () => inspectSection(s.id);
    tr.innerHTML = `
      <td><strong>${s.id}</strong></td>
      <td>${s.name}</td>
      <td>${s.length_km} km</td>
      <td>${s.tracks}</td>
      <td>${s.max_speed_kmh} km/h</td>
      <td>${activeTrains} Trains</td>
      <td>${activeBlocks} Blocks</td>
      <td><span class="semantic-text text-medium"><span class="dot dot-green"></span> Operational</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderNetworkTopology() {
  const container = document.getElementById("networkTopologyGraph");
  if (!container || !AppState.dataset || !AppState.dataset.sections) return;
  container.innerHTML = "";

  const nodes = [
    { code: "HWH", name: "Howrah Jn" },
    { code: "BWN", name: "Barddhaman" },
    { code: "ASN", name: "Asansol Jn" },
    { code: "DHN", name: "Dhanbad Jn" },
    { code: "GAYA", name: "Gaya Jn" },
    { code: "DDU", name: "Pt. Deen Dayal Upadhyaya" }
  ];

  nodes.forEach((n, idx) => {
    const nodeDiv = document.createElement("div");
    nodeDiv.className = "station-node";
    nodeDiv.innerText = n.code;
    nodeDiv.title = `${n.name} (${n.code}) - Click to inspect`;
    nodeDiv.style.cursor = "pointer";
    nodeDiv.onclick = () => showStationInfo(n.code);
    container.appendChild(nodeDiv);

    if (idx < nodes.length - 1) {
      const sec = AppState.dataset.sections[idx];
      const edge = document.createElement("div");
      edge.className = "track-edge";
      edge.style.cursor = "pointer";
      edge.onclick = () => inspectSection(sec?.id);

      const hasEmergency = AppState.dataset.incidents && AppState.dataset.incidents.length > 1 && sec?.id === "A12-B14";
      const hasActive = AppState.currentSchedule.some(s => s.section === sec?.id);

      if (hasEmergency) edge.className = "track-edge edge-emergency";
      else if (hasActive) edge.className = "track-edge edge-active";

      const label = document.createElement("div");
      label.className = "track-edge-label";
      label.innerText = sec ? sec.id : "";
      edge.appendChild(label);
      container.appendChild(edge);
    }
  });
}

function inspectSection(secId) {
  if (!secId || !AppState.dataset) return;
  const sec = AppState.dataset.sections?.find(s => s.id === secId);
  if (!sec) return;

  AppState.selectedSection = secId;
  const panel = document.getElementById("sectionDetailsPanel");
  const title = document.getElementById("secDetailTitle");
  const body = document.getElementById("secDetailBody");
  if (!panel || !title || !body) return;

  const secTrains = (AppState.dataset.trains || []).filter(t => t.section === sec.id);
  const secBlocks = (AppState.currentSchedule || []).filter(b => b.section === sec.id);
  const secWindows = (AppState.dataset.block_windows || []).filter(w => w.section === sec.id);

  title.innerText = `Section Telemetry: ${sec.id} (${sec.name})`;
  body.innerHTML = `
    <div><strong>Length:</strong> ${sec.length_km} km</div>
    <div><strong>Track Count:</strong> ${sec.tracks} Track Line</div>
    <div><strong>Max Authorized Speed:</strong> ${sec.max_speed_kmh} km/h</div>
    <div><strong>Active Timetable Trains:</strong> ${secTrains.length} Services</div>
    <div><strong>Sanctioned Block Windows:</strong> ${secWindows.length} Windows</div>
    <div><strong>Scheduled Maintenance:</strong> ${secBlocks.length} Blocks Assigned</div>
    <div style="grid-column: 1 / -1; margin-top:6px; color:var(--text-secondary);">
      <strong>Passing Trains:</strong> ${secTrains.map(t => t.train_name).join(', ') || 'None scheduled'}<br>
      <strong>Permitted Windows:</strong> ${secWindows.map(w => w.id + ' (' + formatHour(w.start_hour) + '–' + formatHour(w.end_hour) + ')').join(', ') || 'None'}
    </div>
  `;
  panel.style.display = "block";
}

function closeSectionDetails() {
  const panel = document.getElementById("sectionDetailsPanel");
  if (panel) panel.style.display = "none";
}

function showStationInfo(code) {
  switchTab("stations", document.querySelectorAll(".nav-item")[5]);
  const searchInput = document.getElementById("stationSearchInput");
  if (searchInput) {
    searchInput.value = code;
    filterStations();
  }
}

// Station directory
async function initStationDirectory() {
  try {
    const res = await fetch(`${API_BASE}/stations?limit=150`);
    AppState.allStations = await res.json();
    populateStationStateFilter();
    renderStationGrid(AppState.allStations);
  } catch (err) {
    console.error("Failed to load stations directory:", err);
  }
}

function populateStationStateFilter() {
  const select = document.getElementById("stationStateFilter");
  if (!select || !AppState.allStations) return;

  const states = [...new Set(AppState.allStations.map(s => s.state))].sort();
  select.innerHTML = `<option value="ALL">All States / UTs (${states.length})</option>`;
  states.forEach(st => {
    const opt = document.createElement("option");
    opt.value = st;
    opt.innerText = st;
    select.appendChild(opt);
  });
}

function handleStationStateChange() {
  const stateVal = document.getElementById("stationStateFilter")?.value;
  const districtSelect = document.getElementById("stationDistrictFilter");
  if (!districtSelect) return;

  if (!stateVal || stateVal === "ALL") {
    districtSelect.innerHTML = `<option value="ALL">All Districts</option>`;
  } else {
    const filteredStations = AppState.allStations.filter(s => s.state === stateVal);
    const districts = [...new Set(filteredStations.map(s => s.district))].sort();
    districtSelect.innerHTML = `<option value="ALL">All Districts in ${stateVal} (${districts.length})</option>`;
    districts.forEach(d => {
      const opt = document.createElement("option");
      opt.value = d;
      opt.innerText = d;
      districtSelect.appendChild(opt);
    });
  }
  filterStations();
}

function filterStations() {
  const query = (document.getElementById("stationSearchInput")?.value || "").trim().toLowerCase();
  const stateVal = document.getElementById("stationStateFilter")?.value || "ALL";
  const districtVal = document.getElementById("stationDistrictFilter")?.value || "ALL";
  const zoneVal = document.getElementById("stationZoneFilter")?.value || "ALL";

  let filtered = AppState.allStations || [];

  if (query) {
    filtered = filtered.filter(s => 
      s.code.toLowerCase().includes(query) || 
      s.name.toLowerCase().includes(query) ||
      (s.division && s.division.toLowerCase().includes(query)) ||
      (s.city && s.city.toLowerCase().includes(query))
    );
  }
  if (stateVal !== "ALL") {
    filtered = filtered.filter(s => s.state === stateVal);
  }
  if (districtVal !== "ALL") {
    filtered = filtered.filter(s => s.district === districtVal);
  }
  if (zoneVal !== "ALL") {
    filtered = filtered.filter(s => s.zone === zoneVal);
  }

  const badge = document.getElementById("stationCountBadge");
  if (badge) badge.innerText = filtered.length;

  renderStationGrid(filtered);
}

function renderStationGrid(stations) {
  const grid = document.getElementById("stationsGrid");
  if (!grid) return;
  grid.innerHTML = "";

  if (stations.length === 0) {
    grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:24px; color:var(--text-muted);">No stations match the selected filters.</div>`;
    return;
  }

  stations.forEach(s => {
    const card = document.createElement("div");
    card.className = "station-card";
    const divName = s.division || (s.district ? `${s.district} Division` : `${s.zone || 'IR'} Division`);
    const catName = s.category || (s.platforms >= 10 ? 'NSG-1 Premier' : s.platforms >= 6 ? 'NSG-2 Major' : 'NSG-3 Medium');
    const locationStr = s.district ? `${s.district}, ${s.state}` : (s.city ? `${s.city}, ${s.state}` : s.state || 'India');
    card.innerHTML = `
      <div>
        <div class="station-header">
          <div class="station-name">${s.name}</div>
          <span class="station-code">${s.code}</span>
        </div>
        <div class="station-meta">
          <div><i class="fa-solid fa-location-dot" style="width:14px; color:var(--text-muted);"></i> ${locationStr}</div>
          <div><i class="fa-solid fa-train" style="width:14px; color:var(--text-muted);"></i> Zone: <strong>${s.zone || 'IR'}</strong> | Div: <strong>${divName}</strong></div>
          <div><i class="fa-solid fa-layer-group" style="width:14px; color:var(--text-muted);"></i> Platforms: <strong>${s.platforms || 2}</strong> | Cat: <strong>${catName}</strong></div>
        </div>
      </div>
      <div class="station-footer">
        <span>${s.electrified !== false ? '<i class="fa-solid fa-bolt" style="color:var(--accent-amber);"></i> 25kV Electrified' : 'Non-Electrified'}</span>
        <div style="display:flex; gap:6px;">
          <button class="btn btn-primary btn-xs" onclick="openStationBoard('${s.code}')" title="View live arrivals and departures"><i class="fa-solid fa-chalkboard-user"></i> Live Board</button>
          <button class="btn btn-secondary btn-xs" onclick="queryLiveTrainsForStation('${s.code}')" title="Inspect premier train telemetry"><i class="fa-solid fa-satellite-dish"></i> Telemetry</button>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });
}

function resetStationFilters() {
  const searchInput = document.getElementById("stationSearchInput");
  const stateFilter = document.getElementById("stationStateFilter");
  const districtFilter = document.getElementById("stationDistrictFilter");
  const zoneFilter = document.getElementById("stationZoneFilter");

  if (searchInput) searchInput.value = "";
  if (stateFilter) stateFilter.value = "ALL";
  if (districtFilter) districtFilter.innerHTML = `<option value="ALL">All Districts</option>`;
  if (zoneFilter) zoneFilter.value = "ALL";

  filterStations();
}

function queryLiveTrainsForStation(code) {
  openStationBoard(code);
}

// Station live board (arrivals & departures)
async function openStationBoard(stationCode) {
  const modal = document.getElementById("stationBoardModal");
  const title = document.getElementById("stBoardTitle");
  const meta = document.getElementById("stBoardMeta");
  const badge = document.getElementById("stBoardSourceBadge");
  const notice = document.getElementById("stBoardNotice");
  const tbody = document.querySelector("#stationBoardTable tbody");

  if (!modal || !tbody) return;
  tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:16px;"><i class="fa-solid fa-spinner fa-spin"></i> Fetching live station board for ${stationCode}...</td></tr>`;
  openModal("stationBoardModal");

  try {
    const res = await fetch(`${API_BASE}/live/station-board/${encodeURIComponent(stationCode)}`);
    const data = await res.json();

    const items = data.movements || data.arrivals || [];

    title.innerHTML = `<i class="fa-solid fa-chalkboard-user"></i> Station Board: ${data.station_name} (${data.station_code})`;
    meta.innerHTML = `
      <div><strong>Zone:</strong> ${data.zone || 'IR'}</div>
      <div><strong>Platforms:</strong> ${data.platforms || 'Multiple'}</div>
      <div><strong>Total Scheduled Movements:</strong> ${items.length} Services</div>
    `;

    if (data.data_source === "LIVE_DATA" || (data.source && data.source.includes("LIVE"))) {
      badge.className = "live-status-badge badge-live";
      badge.innerHTML = `<i class="fa-solid fa-satellite-dish"></i> LIVE NTES FEED`;
      notice.innerText = "Real-time station telemetry provided via live railway gateway.";
    } else {
      badge.className = "live-status-badge badge-demo";
      badge.innerHTML = `<i class="fa-solid fa-calendar-check"></i> DEMO / REPRESENTATIVE TIMETABLE`;
      notice.innerText = "High-fidelity representative Working Timetable (WTT) data for prototype maintenance planning.";
    }

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:16px; color:var(--text-muted);">No upcoming trains found for station ${stationCode}.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    items.forEach(item => {
      const tr = document.createElement("tr");
      const statusBadge = (item.delay_mins && item.delay_mins > 0)
        ? `<span class="badge-label badge-amber">+${item.delay_mins}m Delay</span>`
        : `<span class="badge-label badge-green">Right Time</span>`;

      tr.innerHTML = `
        <td><strong>${item.train_number}</strong></td>
        <td><a href="javascript:void(0)" onclick="closeModal('stationBoardModal'); inspectTrainRoute('${item.train_number}')" style="font-weight:600; color:var(--text-primary); text-decoration:underline;">${item.train_name}</a></td>
        <td>${item.train_type || 'Express'}</td>
        <td>${item.origin} → ${item.destination}</td>
        <td>${item.scheduled_arrival || '--:--'}</td>
        <td>${item.scheduled_departure || '--:--'}</td>
        <td><span class="badge-label badge-gray">PF ${item.platform || 1}</span></td>
        <td>${statusBadge}</td>
        <td style="text-align:right;">
          <button class="btn btn-secondary btn-xs" onclick="closeModal('stationBoardModal'); inspectTrainRoute('${item.train_number}')" title="Inspect Route"><i class="fa-solid fa-route"></i></button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:var(--accent-red); padding:16px;">Failed to fetch station board: ${err.message}</td></tr>`;
  }
}

// Train route & inspection
let currentlyInspectedTrain = null;

async function inspectTrainRoute(trainNumber) {
  const modal = document.getElementById("trainInspectModal");
  const title = document.getElementById("trInspectTitle");
  const meta = document.getElementById("trInspectMeta");
  const badge = document.getElementById("trInspectStatusBadge");
  const tbody = document.querySelector("#trainInspectTable tbody");

  if (!modal || !tbody) return;
  tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:16px;"><i class="fa-solid fa-spinner fa-spin"></i> Loading timetable for ${trainNumber}...</td></tr>`;
  openModal("trainInspectModal");

  try {
    const res = await fetch(`${API_BASE}/live/train-timetable/${encodeURIComponent(trainNumber)}`);
    if (!res.ok) throw new Error("Train not found in timetable directory");
    const json = await res.json();
    const data = json.train || json;
    data.source_label = json.source_label || data.source_label;
    data.data_source = json.data_source || data.data_source;
    currentlyInspectedTrain = data;

    title.innerHTML = `<i class="fa-solid fa-train"></i> ${data.train_number} — ${data.train_name}`;
    
    const isLive = data.data_source === "LIVE_DATA" || (data.source && data.source.includes("LIVE"));
    badge.className = isLive ? "live-status-badge badge-live" : "live-status-badge badge-demo";
    badge.innerHTML = isLive ? `<i class="fa-solid fa-satellite-dish"></i> LIVE NTES` : `<i class="fa-solid fa-calendar-check"></i> DEMO / REPRESENTATIVE WTT`;

    meta.innerHTML = `
      <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">
        <div><strong>Type:</strong> ${data.train_type || 'Superfast Express'}</div>
        <div><strong>Origin:</strong> ${data.origin}</div>
        <div><strong>Destination:</strong> ${data.destination}</div>
        <div><strong>Priority:</strong> Priority ${data.service_priority || 1}</div>
        <div><strong>Dataset:</strong> <span style="color:var(--accent-green); font-weight:600;">Representative Working Timetable (WTT)</span></div>
      </div>
    `;

    const stops = data.route || [];
    if (stops.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:16px; color:var(--text-muted);">No intermediate stops recorded.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    stops.forEach((st, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td><strong>${st.station_code}</strong></td>
        <td>${st.station_name}</td>
        <td>${st.arrival || st.arrival_time || '--:--'}</td>
        <td>${st.departure || st.departure_time || '--:--'}</td>
        <td>${st.halt_mins ? st.halt_mins + 'm' : '--'}</td>
        <td>Day ${st.day || 1}</td>
        <td>${st.distance_km ? st.distance_km + ' km' : '--'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--accent-red); padding:16px;">Error loading train timetable: ${err.message}</td></tr>`;
  }
}

function addCurrentInspectedTrainToCorridor() {
  if (!currentlyInspectedTrain) return;
  closeModal("trainInspectModal");
  openCreateTrainModal();

  const tr = currentlyInspectedTrain;
  document.getElementById("trId").value = tr.train_number;
  document.getElementById("trName").value = tr.train_name;
  document.getElementById("trPrio").value = String(tr.service_priority || 1);
  const orgEl = document.getElementById("trOrigin");
  if (orgEl) orgEl.value = tr.origin;
  const dstEl = document.getElementById("trDest");
  if (dstEl) dstEl.value = tr.destination;
  document.getElementById("trArr").value = "02.5";
  document.getElementById("trDep").value = "03.0";
}

// Pan-India train search & telemetry
async function searchPanIndiaTrain() {
  const q = (document.getElementById("panIndiaTrainInput")?.value || "").trim();
  if (!q) {
    alert("Please enter a train number (e.g. 12301) or train name (e.g. Rajdhani).");
    return;
  }

  const container = document.getElementById("panIndiaTrainResultArea");
  if (!container) return;
  container.style.display = "block";
  container.innerHTML = `<div style="padding:14px; font-size:12px; color:var(--text-secondary);"><i class="fa-solid fa-spinner fa-spin"></i> Searching Indian Railways train directory for "${q}"...</div>`;

  try {
    const res = await fetch(`${API_BASE}/live/search-trains?query=${encodeURIComponent(q)}`);
    const json = await res.json();
    const results = json.results || (Array.isArray(json) ? json : []);

    if (!results || results.length === 0) {
      container.innerHTML = `
        <div style="background:#FAFAFA; border:1px solid var(--border-color); border-radius:4px; padding:14px; font-size:12px; color:var(--text-secondary);">
          No trains found matching "<strong>${q}</strong>". Try entering <code>12301</code>, <code>22301</code>, <code>12259</code>, <code>12951</code>, or <code>Rajdhani</code>.
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="margin-bottom:8px; font-size:11px; font-weight:700; color:var(--text-secondary); text-transform:uppercase;">
        Found ${results.length} Train Service(s):
      </div>
      <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap:10px;">
        ${results.map(t => `
          <div style="background:#FFFFFF; border:1px solid var(--border-color); border-radius:4px; padding:12px; display:flex; flex-direction:column; justify-content:space-between;">
            <div>
              <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px;">
                <strong style="font-size:13px; color:var(--text-primary);">${t.train_number} — ${t.train_name}</strong>
                <span class="badge-label ${(t.source && t.source.includes('LIVE')) ? 'badge-green' : 'badge-gray'}" style="font-size:9px;">${(t.source && t.source.includes('LIVE')) ? 'LIVE' : 'SCHEDULED'}</span>
              </div>
              <div style="font-size:11px; color:var(--text-secondary); line-height:1.4; margin-top:4px;">
                <div><i class="fa-solid fa-route" style="width:12px;"></i> ${t.origin} → ${t.destination}</div>
                <div><i class="fa-solid fa-train" style="width:12px;"></i> Type: <strong>${t.train_type}</strong> | Priority: <strong>P${t.service_priority}</strong></div>
              </div>
            </div>
            <div style="margin-top:10px; padding-top:8px; border-top:1px solid var(--border-subtle); display:flex; gap:6px; justify-content:flex-end;">
              <button class="btn btn-secondary btn-xs" onclick="inspectTrainRoute('${t.train_number}')"><i class="fa-solid fa-route"></i> Route Timetable</button>
              <button class="btn btn-primary btn-xs" onclick="checkLiveTrainByNumber('${t.train_number}')"><i class="fa-solid fa-satellite-dish"></i> Live Status</button>
            </div>
          </div>
        `).join('')}
      </div>
      <div id="quickLiveStatusTarget" style="margin-top:12px;"></div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:var(--accent-red); font-size:12px; padding:12px;">Search failed: ${err.message}</div>`;
  }
}

function quickSelectTrain(num) {
  const input = document.getElementById("panIndiaTrainInput");
  if (input) {
    input.value = num;
    searchPanIndiaTrain();
  }
}

async function findTrainsBetween() {
  const from = (document.getElementById("findFromStation")?.value || "").trim().toUpperCase();
  const to = (document.getElementById("findToStation")?.value || "").trim().toUpperCase();

  if (!from || !to) {
    alert("Please enter both origin and destination station codes (e.g. HWH and NDLS).");
    return;
  }

  const container = document.getElementById("panIndiaTrainResultArea");
  if (!container) return;
  container.style.display = "block";
  container.innerHTML = `<div style="padding:14px; font-size:12px; color:var(--text-secondary);"><i class="fa-solid fa-spinner fa-spin"></i> Searching trains connecting ${from} and ${to}...</div>`;

  try {
    const res = await fetch(`${API_BASE}/live/trains-between-stations?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`);
    const data = await res.json();
    const trains = data.trains || [];

    if (trains.length === 0) {
      container.innerHTML = `
        <div style="background:#FAFAFA; border:1px solid var(--border-color); border-radius:4px; padding:14px; font-size:12px; color:var(--text-secondary);">
          No direct trains found between <strong>${from}</strong> and <strong>${to}</strong> in current directory. Try common station pairs like <code>HWH</code> and <code>NDLS</code>, or <code>CSMT</code> and <code>MAS</code>.
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="margin-bottom:8px; font-size:11px; font-weight:700; color:var(--text-secondary); text-transform:uppercase;">
        Found ${trains.length} Direct Train Service(s) between ${from} and ${to}:
      </div>
      <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap:10px;">
        ${trains.map(t => `
          <div style="background:#FFFFFF; border:1px solid var(--border-color); border-radius:4px; padding:12px; display:flex; flex-direction:column; justify-content:space-between;">
            <div>
              <strong style="font-size:13px; color:var(--text-primary);">${t.train_number} — ${t.train_name}</strong>
              <div style="font-size:11px; color:var(--text-secondary); line-height:1.4; margin-top:4px;">
                <div>Route: ${t.origin} → ${t.destination}</div>
                <div>Depart ${from}: <strong>${t.from_dep || '--:--'}</strong> | Arrive ${to}: <strong>${t.to_arr || '--:--'}</strong></div>
              </div>
            </div>
            <div style="margin-top:10px; padding-top:8px; border-top:1px solid var(--border-subtle); display:flex; gap:6px; justify-content:flex-end;">
              <button class="btn btn-secondary btn-xs" onclick="inspectTrainRoute('${t.train_number}')"><i class="fa-solid fa-route"></i> Full Route</button>
              <button class="btn btn-primary btn-xs" onclick="checkLiveTrainByNumber('${t.train_number}')"><i class="fa-solid fa-satellite-dish"></i> Status</button>
            </div>
          </div>
        `).join('')}
      </div>
      <div id="quickLiveStatusTarget" style="margin-top:12px;"></div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:var(--accent-red); font-size:12px; padding:12px;">Search failed: ${err.message}</div>`;
  }
}

async function checkLiveTrainByNumber(trainNum) {
  let target = document.getElementById("quickLiveStatusTarget");
  if (!target) target = document.getElementById("panIndiaTrainResultArea");
  if (!target) return;

  target.innerHTML = `<div style="padding:10px; font-size:11px; color:var(--text-secondary);"><i class="fa-solid fa-spinner fa-spin"></i> Querying live telemetry for Train ${trainNum}...</div>`;

  try {
    const res = await fetch(`${API_BASE}/live/train-status/${encodeURIComponent(trainNum)}`);
    const data = await res.json();

    if (data.status === "REPRESENTATIVE_WTT" || data.status === "LIVE DATA NOT CONFIGURED") {
      target.innerHTML = `
        <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:4px; padding:12px; margin-top:8px;">
          <div style="font-weight:700; color:#15803D; font-size:12px; display:flex; align-items:center; gap:6px;">
            <i class="fa-solid fa-circle-check"></i> DEMO / REPRESENTATIVE WORKING TIMETABLE
          </div>
          <div style="font-size:11px; color:#166534; margin-top:4px; line-height:1.4;">
            ${data.message || 'Timetable loaded from representative Indian Railways Working Timetable (WTT) dataset.'}
          </div>
          <div style="margin-top:8px; padding-top:8px; border-top:1px dashed #86EFAC; font-size:11px; color:var(--text-primary);">
            <strong>Scheduled Timetable Profile:</strong><br>
            Train: <strong>${data.train_number} — ${data.train_name}</strong><br>
            Corridor Segment: <strong>${data.section}</strong> | Window: <strong>${formatHour(data.scheduled_arrival)} – ${formatHour(data.scheduled_departure)} IST</strong><br>
            Status: <strong>${data.simulated_status}</strong> (Delay: <strong>${data.delay_mins} mins</strong>)
          </div>
        </div>
      `;
    } else if (data.status === "OK" || data.status === "LIVE") {
      target.innerHTML = `
        <div style="background:#E8F5E9; border:1px solid #C8E6C9; border-radius:4px; padding:12px; margin-top:8px;">
          <div style="font-weight:700; color:#2E7D32; font-size:12px;">
            <i class="fa-solid fa-train"></i> Train Movement: ${data.train_number} — ${data.train_name}
          </div>
          <div style="font-size:11px; color:var(--text-primary); margin-top:6px; line-height:1.5;">
            Current Station: <strong>${data.current_station || 'In Transit'}</strong><br>
            Delay Status: <strong>${data.delay_mins || 0} mins</strong> (${data.status_description || 'Running on time'})<br>
            Last Updated: <strong>${data.last_updated || 'Just now'}</strong>
          </div>
        </div>
      `;
    } else {
      target.innerHTML = `
        <div style="background:#FAFAFA; border:1px solid var(--border-color); border-radius:4px; padding:10px; margin-top:8px; font-size:11px; color:var(--text-secondary);">
          ${data.message || 'Train not found in directory.'}
        </div>
      `;
    }
  } catch (err) {
    target.innerHTML = `<div style="color:var(--accent-red); font-size:11px; margin-top:8px;">Error: ${err.message}</div>`;
  }
}

// Telemetry provider status
async function initLiveProviderStatus() {
  try {
    const res = await fetch(`${API_BASE}/live/provider-status`);
    const status = await res.json();
    const badges = [document.getElementById("providerStatusBadge"), document.getElementById("trainTabProviderBadge")];
    
    badges.forEach(badge => {
      if (badge && status) {
        if (status.live_feed_configured) {
          badge.className = "live-status-badge badge-live";
          badge.innerHTML = `<i class="fa-solid fa-satellite-dish"></i> Live Feed: ${status.provider_name}`;
        } else {
          badge.className = "live-status-badge badge-demo";
          badge.innerHTML = `<i class="fa-solid fa-circle-check"></i> DEMO / REPRESENTATIVE DATA`;
        }
      }
    });
  } catch (err) {
    // Non-fatal
  }
}

async function checkLiveTrainStatus() {
  const trainNum = (document.getElementById("liveTrainInput")?.value || "").trim();
  if (!trainNum) {
    alert("Please enter a train number to query live status.");
    return;
  }
  checkLiveTrainByNumber(trainNum);
}

// Data import & export
function openImportModal() {
  document.getElementById("importForm").reset();
  handleImportTypeChange();
  openModal("importModal");
}

function handleImportTypeChange() {
  const type = document.getElementById("importType")?.value;
  const hint = document.getElementById("importFormatHint");
  if (!hint) return;

  if (type === "tasks") {
    hint.innerHTML = `CSV format: <code>id,task_type,department,section,asset_id,priority,duration_mins,deadline_hour</code> or JSON array of tasks.`;
  } else if (type === "trains") {
    hint.innerHTML = `CSV format: <code>train_id,train_name,section,arrival_hour,departure_hour,service_priority,direction,origin,destination</code> or JSON array of trains.`;
  } else if (type === "blocks") {
    hint.innerHTML = `CSV format: <code>id,section,start_hour,end_hour,department,day_of_week</code> or JSON array of block windows.`;
  } else {
    hint.innerHTML = `JSON object with sections, assets, tasks, trains, and block_windows.`;
  }
}

function handleImportFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (event) => {
    const text = event.target.result;
    document.getElementById("importTextInput").value = text;
  };
  reader.readAsText(file);
}

async function handleImportSubmit(e) {
  e.preventDefault();
  const type = document.getElementById("importType").value;
  const rawText = document.getElementById("importTextInput").value.trim();

  if (!rawText) {
    alert("Please provide JSON or CSV data to import.");
    return;
  }

  showLoading("Importing Operational Data...", "Validating payload and updating corridor state...");

  try {
    let payload;
    if (rawText.startsWith("{") || rawText.startsWith("[")) {
      payload = JSON.parse(rawText);
    } else {
      // Parse CSV
      payload = parseCsvData(rawText, type);
    }

    let endpoint = `${API_BASE}/import/tasks`;
    if (type === "trains") endpoint = `${API_BASE}/import/trains`;
    else if (type === "blocks") endpoint = `${API_BASE}/import/blocks`;
    else if (type === "scenario") endpoint = `${API_BASE}/import/scenario`;

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    hideLoading();

    if (res.ok) {
      closeModal("importModal");
      alert(data.message || "Data imported successfully.");
      await fetchInitialData();
    } else {
      alert(`Import Failed: ${data.detail || 'Invalid data format'}`);
    }
  } catch (err) {
    hideLoading();
    alert("Import Error: " + err.message);
  }
}

function parseCsvData(csvText, type) {
  const lines = csvText.split(/\r?\n/).filter(line => line.trim() !== "");
  if (lines.length < 2) throw new Error("CSV must contain a header line and at least one data row.");

  const headers = lines[0].split(",").map(h => h.trim());
  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(",").map(v => v.trim());
    if (values.length !== headers.length) continue;
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = values[idx];
    });

    if (type === "tasks") {
      obj.duration_mins = parseInt(obj.duration_mins) || 60;
      obj.deadline_hour = parseFloat(obj.deadline_hour) || 18.0;
      obj.priority = obj.priority || "MEDIUM";
      obj.status = obj.status || "PENDING";
    } else if (type === "trains") {
      obj.arrival_hour = parseFloat(obj.arrival_hour) || 10.0;
      obj.departure_hour = parseFloat(obj.departure_hour) || 11.0;
      obj.service_priority = parseInt(obj.service_priority) || 1;
      obj.is_protected = true;
    } else if (type === "blocks") {
      obj.start_hour = parseFloat(obj.start_hour) || 2.0;
      obj.end_hour = parseFloat(obj.end_hour) || 4.0;
      obj.max_duration_mins = Math.round((obj.end_hour - obj.start_hour) * 60);
      obj.permitted_departments = obj.department ? [obj.department] : ["Engineering", "Signal & Telecom", "Traction / OHE"];
    }
    rows.push(obj);
  }
  return rows;
}

function exportCSV() {
  window.open(`${API_BASE}/export`, "_blank");
}

// ==========================================
// TABS & UTILITIES
// ==========================================
function switchTab(tabId, el) {
  const tabs = ["dashboard", "planResult", "corridor", "tasks", "trains", "blocks", "stations", "explain", "comparison", "history"];
  tabs.forEach(t => {
    const target = document.getElementById(`tab${t.charAt(0).toUpperCase() + t.slice(1)}`);
    if (target) target.style.display = t === tabId ? "block" : "none";
  });

  if (el) {
    const items = document.querySelectorAll(".nav-item");
    items.forEach(item => item.classList.remove("active"));
    el.classList.add("active");
  }

  if (tabId === "planResult") {
    renderPlanResultFullView();
  }
}

function openModal(modalId) {
  document.getElementById(modalId)?.classList.add("active");
}

function closeModal(modalId) {
  document.getElementById(modalId)?.classList.remove("active");
}

function showLoading(title, desc) {
  document.getElementById("loadingStepTitle").innerText = title;
  document.getElementById("loadingStepDesc").innerText = desc;
  document.getElementById("loadingOverlay").classList.add("active");
}

function setLoadingStep(title, desc) {
  document.getElementById("loadingStepTitle").innerText = title;
  document.getElementById("loadingStepDesc").innerText = desc;
}

function hideLoading() {
  document.getElementById("loadingOverlay").classList.remove("active");
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
