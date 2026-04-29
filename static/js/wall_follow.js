import { $, postJSON, getJSON, debugLog } from "./api.js";

let wfStatusTimer = null;

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
  };
}

function renderStatus(data) {
  if (!data) return;

  const running = Boolean(data.running ?? data.enabled ?? false);
  setStatus(running, data.status || data.reason || "");

  if ($("wfSide") && data.side) {
    $("wfSide").value = data.side;
  } else if ($("wfSide") && data.config?.side) {
    $("wfSide").value = data.config.side;
  }

  const telem = $("wfTelemetry");
  if (telem) {
    const state = data.state || data.mode || "--";
    const side = data.side_distance_mm ?? data.side_mm ?? "--";
    const front = data.front_distance_mm ?? data.front_mm ?? "--";
    const reason = data.reason ? ` ${data.reason}` : "";

    telem.textContent = `side=${side} front=${front} state=${state}${reason}`;
  }
}

async function fetchStatus() {
  try {
    const data = await getJSON("/api/wall_follow");

    if (!data) {
      throw new Error("no response data");
    }

    renderStatus(data);
    return data;
  } catch (err) {
    stopStatusPolling();
    setStatus(false, "error");

    const telem = $("wfTelemetry");
    if (telem) {
      telem.textContent = "wall follow status unavailable";
    }

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
  const startBtn = $("wfStartBtn");
  const stopBtn = $("wfStopBtn");
  const refreshBtn = $("wfRefreshBtn");

  if (startBtn) {
    startBtn.addEventListener("click", async () => {
      const payload = currentPayload();

      debugLog("[wall_follow]", {
        action: "start_click",
        payload,
      });

      const data = await postJSON("/api/wall_follow/start", payload);
      renderStatus(data);
      startStatusPolling();
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", async () => {
      debugLog("[wall_follow]", {
        action: "stop_click",
      });

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