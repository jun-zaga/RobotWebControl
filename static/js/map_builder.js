import { $, debugLog, getJSON, postJSON } from "./api.js";

let mapTimer = null;

function setText(id, value) {
  const el = $(id);
  if (el) el.textContent = value == null ? "---" : String(value);
}

function renderSnapshot(snapshot) {
  if (!snapshot) return;

  const zones = snapshot.greeter_zones || {};
  const scan = snapshot.scan_8 || {};

  setText("mapFrontMm", zones.front_mm);
  setText("mapLeftMm", zones.left_mm);
  setText("mapRightMm", zones.right_mm);

  const scanBox = $("mapScan8");
  if (scanBox) {
    scanBox.textContent = JSON.stringify(scan, null, 2);
  }
}

function renderPoints(points) {
  const list = $("mapPointsList");
  if (!list) return;

  if (!points || points.length === 0) {
    list.innerHTML = "<li>No points saved yet.</li>";
    return;
  }

  list.innerHTML = "";

  for (const point of points) {
    const zones = point.snapshot?.greeter_zones || {};

    const li = document.createElement("li");
    li.className = "map-point-item";

    li.innerHTML = `
      <strong>${point.index}. ${point.label}</strong><br>
      <span>${point.notes || ""}</span><br>
      <span>step_index=${point.step_index ?? "---"}</span><br>
      <span>
        front=${zones.front_mm ?? "---"},
        left=${zones.left_mm ?? "---"},
        right=${zones.right_mm ?? "---"}
      </span>
    `;

    list.appendChild(li);
  }
}

function renderSteps(steps) {
  const box = $("mapStepsList");
  if (!box) return;

  if (!steps || steps.length === 0) {
    box.innerHTML = "<li>No movement steps recorded yet.</li>";
    return;
  }

  box.innerHTML = "";

  for (const step of steps) {
    const zones = step.snapshot?.greeter_zones || {};

    const li = document.createElement("li");
    li.className = "map-step-item";

    li.innerHTML = `
      <strong>${step.index}. ${step.label}</strong>
      <span> type=${step.type}</span><br>
      <span>left=${step.left}, right=${step.right}</span><br>
      <span>
        front=${zones.front_mm ?? "---"},
        left_mm=${zones.left_mm ?? "---"},
        right_mm=${zones.right_mm ?? "---"}
      </span>
    `;

    box.appendChild(li);
  }
}

function showMapStatus(data) {
  if (!data) return;

  renderSnapshot(data.snapshot);
  renderPoints(data.points);
  renderSteps(data.steps);

  setText("mapPointCount", data.point_count ?? 0);
  setText("mapStepCount", data.step_count ?? 0);

  const raw = $("mapRawStatus");
  if (raw) {
    raw.textContent = JSON.stringify(data, null, 2);
  }

  debugLog("[MAP]", data);
}

async function refreshMapStatus() {
  const data = await getJSON("/api/map/status");
  showMapStatus(data);
}

async function mapDrive(left, right, label) {
  const data = await postJSON("/api/map/drive", { left, right, label });
  debugLog("[MAP DRIVE]", data);
  await refreshMapStatus();
}

async function mapStop(label = "manual_stop") {
  const data = await postJSON("/api/map/stop", { label });
  debugLog("[MAP STOP]", data);
  await refreshMapStatus();
}

async function markMapPoint() {
  await mapStop("stop_before_mark");

  const labelBox = $("mapPointLabel");
  const notesBox = $("mapPointNotes");

  const label = labelBox ? labelBox.value.trim() : "";
  const notes = notesBox ? notesBox.value.trim() : "";

  if (!label) {
    debugLog("[MAP]", "label required");
    alert("Add a label first.");
    return;
  }

  const data = await postJSON("/api/map/mark", { label, notes });
  showMapStatus(data);

  if (data.ok && labelBox) labelBox.value = "";
  if (data.ok && notesBox) notesBox.value = "";
}

async function saveMap() {
  await mapStop("stop_before_save");

  const data = await postJSON("/api/map/save", {});
  debugLog("[MAP SAVE]", data);

  const raw = $("mapRawStatus");
  if (raw) {
    raw.textContent = JSON.stringify(data, null, 2);
  }

  if (data.ok) {
    alert(`Map saved to ${data.saved_to}`);
  }
}

async function clearMap() {
  const ok = confirm("Clear all saved map points and movement steps?");
  if (!ok) return;

  const data = await postJSON("/api/map/clear", {});
  showMapStatus(data);
}

export function initMapBuilder() {
  debugLog("[MAP]", "initMapBuilder called");

  const speedBox = $("mapDriveSpeed");

  function speed() {
    const value = Number(speedBox?.value || 0.80);
    return Math.max(0.1, Math.min(1.0, value));
  }

  const forwardBtn = $("mapForwardBtn");
  const backBtn = $("mapBackBtn");
  const leftBtn = $("mapLeftBtn");
  const rightBtn = $("mapRightBtn");
  const stopBtn = $("mapStopBtn");

  const markBtn = $("mapMarkBtn");
  const saveBtn = $("mapSaveBtn");
  const clearBtn = $("mapClearBtn");
  const refreshBtn = $("mapRefreshBtn");

  debugLog("[MAP]", {
    forwardFound: !!forwardBtn,
    backFound: !!backBtn,
    leftFound: !!leftBtn,
    rightFound: !!rightBtn,
    stopFound: !!stopBtn,
    markFound: !!markBtn,
    saveFound: !!saveBtn,
    clearFound: !!clearBtn,
    refreshFound: !!refreshBtn,
  });

  if (forwardBtn) {
    forwardBtn.addEventListener("click", () => {
      mapDrive(-speed(), -speed(), "forward");
    });
  }

  if (backBtn) {
    backBtn.addEventListener("click", () => {
      mapDrive(speed(), speed(), "backward");
    });
  }

  if (leftBtn) {
    leftBtn.addEventListener("click", () => {
      mapDrive(-speed(), speed(), "turn_left");
    });
  }

  if (rightBtn) {
    rightBtn.addEventListener("click", () => {
      mapDrive(speed(), -speed(), "turn_right");
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", () => {
      mapStop("manual_stop");
    });
  }

  if (markBtn) markBtn.addEventListener("click", markMapPoint);
  if (saveBtn) saveBtn.addEventListener("click", saveMap);
  if (clearBtn) clearBtn.addEventListener("click", clearMap);
  if (refreshBtn) refreshBtn.addEventListener("click", refreshMapStatus);

  refreshMapStatus().catch((err) => {
    debugLog("[MAP]", `initial status failed: ${err}`);
  });

  if (!mapTimer) {
    mapTimer = setInterval(() => {
      refreshMapStatus().catch(() => {});
    }, 2000);
  }

  debugLog("[MAP]", "map builder UI initialized");
}