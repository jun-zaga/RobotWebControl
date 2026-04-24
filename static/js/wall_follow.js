import { $, setText, postJSON, getJSON, debugLog } from "./api.js";

let wfStatusTimer = null;

function num(id) {
  const el = $(id);
  return el ? Number(el.value) : 0;
}

function stopStatusPolling() {
  if (wfStatusTimer) {
    window.clearInterval(wfStatusTimer);
    wfStatusTimer = null;
    debugLog("[wall_follow]", "status polling stopped");
  }
}

function startStatusPolling() {
  stopStatusPolling();
  wfStatusTimer = window.setInterval(fetchStatus, 1000);
}

function setStatus(running, detail = "") {
  const badge = $("wfStatus");
  if (!badge) return;

  if (running) {
    badge.textContent = "RUNNING";
    badge.className = "statusBadge running";
    return;
  }

  if (detail && String(detail).toLowerCase().includes("error")) {
    badge.textContent = "ERROR";
    badge.className = "statusBadge error";
    return;
  }

  badge.textContent = "IDLE";
  badge.className = "statusBadge idle";
}

function currentPayload() {
  return {
    side: $("wfSide")?.value || "right",
    target_mm: num("wfTarget"),
    tolerance_mm: num("wfTolerance"),
    base_speed: num("wfBaseSpeed"),
    max_turn: num("wfMaxTurn"),
    front_stop_mm: num("wfFrontStop"),
    search_turn: num("wfSearchTurn"),
    front_arc_center_deg: num("wfFrontArcCenter"),
  };
}

function wireValue(id, outId, digits = 0) {
  const s = $(id);
  const out = $(outId);
  if (!s) return;

  const render = () => {
    const v = Number(s.value);
    setText(out, digits > 0 ? v.toFixed(digits) : Math.round(v));
  };

  s.addEventListener("input", render);
  render();
}

function renderStatus(data) {
  if (!data) return;

  const running = Boolean(data.running ?? data.enabled ?? false);
  setStatus(running, data.status || "");

  if (data.config) {
    const c = data.config;
    if ($("wfSide") && c.side) $("wfSide").value = c.side;
    if ($("wfTarget") && c.target_mm != null) $("wfTarget").value = c.target_mm;
    if ($("wfTolerance") && c.tolerance_mm != null) $("wfTolerance").value = c.tolerance_mm;
    if ($("wfBaseSpeed") && c.base_speed != null) $("wfBaseSpeed").value = c.base_speed;
    if ($("wfMaxTurn") && c.max_turn != null) $("wfMaxTurn").value = c.max_turn;
    if ($("wfFrontStop") && c.front_stop_mm != null) $("wfFrontStop").value = c.front_stop_mm;
    if ($("wfSearchTurn") && c.search_turn != null) $("wfSearchTurn").value = c.search_turn;
    if ($("wfFrontArcCenter") && c.front_arc_center_deg != null) $("wfFrontArcCenter").value = c.front_arc_center_deg;
  }

  setText($("wfTargetVal"), num("wfTarget"));
  setText($("wfToleranceVal"), num("wfTolerance"));
  setText($("wfBaseSpeedVal"), num("wfBaseSpeed").toFixed(2));
  setText($("wfMaxTurnVal"), num("wfMaxTurn").toFixed(2));
  setText($("wfFrontStopVal"), num("wfFrontStop"));
  setText($("wfSearchTurnVal"), num("wfSearchTurn").toFixed(2));
  setText($("wfFrontArcVal"), num("wfFrontArcCenter"));

  const telem = $("wfTelemetry");
  if (telem) {
    const state = data.state || data.mode || "--";
    const side = data.side_distance_mm ?? data.side_mm ?? "--";
    const front = data.front_distance_mm ?? data.front_mm ?? "--";
    telem.textContent = `side=${side} front=${front} state=${state}`;
  }
}

async function fetchStatus() {
  try {
    const data = await getJSON("/api/wall_follow");
    if (!data) throw new Error("no response data");
    renderStatus(data);
    return data;
  } catch (err) {
    stopStatusPolling();
    setStatus(false, "error");
    const telem = $("wfTelemetry");
    if (telem) telem.textContent = "wall follow status unavailable";
    debugLog("[wall_follow]", `status fetch failed: ${err}`);
    console.error(err);
    return null;
  }
}

export async function stopWallFollowSilent() {
  try {
    await postJSON("/api/wall_follow/stop", {});
    await fetchStatus();
  } catch (err) {
    console.error(err);
  }
}

export function initWallFollow() {
  wireValue("wfTarget", "wfTargetVal", 0);
  wireValue("wfTolerance", "wfToleranceVal", 0);
  wireValue("wfBaseSpeed", "wfBaseSpeedVal", 2);
  wireValue("wfMaxTurn", "wfMaxTurnVal", 2);
  wireValue("wfFrontStop", "wfFrontStopVal", 0);
  wireValue("wfSearchTurn", "wfSearchTurnVal", 2);
  wireValue("wfFrontArcCenter", "wfFrontArcVal", 0);

  const startBtn = $("wfStartBtn");
  const stopBtn = $("wfStopBtn");
  const applyBtn = $("wfApplyBtn");
  const refreshBtn = $("wfRefreshBtn");

  if (startBtn) {
    startBtn.addEventListener("click", async () => {
      const payload = currentPayload();
      debugLog("[wall_follow]", { action: "start_click", payload });
      const data = await postJSON("/api/wall_follow/start", payload);
      renderStatus(data);
      startStatusPolling();
    });
  }

  if (applyBtn) {
    applyBtn.addEventListener("click", async () => {
      const payload = currentPayload();
      debugLog("[wall_follow]", { action: "apply_click", payload });
      const data = await postJSON("/api/wall_follow/config", payload);
      renderStatus(data);
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", async () => {
      debugLog("[wall_follow]", { action: "stop_click" });
      stopStatusPolling();
      const data = await postJSON("/api/wall_follow/stop", {});
      renderStatus(data);
    });
  }

  if (refreshBtn) {
    refreshBtn.addEventListener("click", fetchStatus);
  }

  fetchStatus();
  startStatusPolling();
}