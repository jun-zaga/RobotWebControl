export const $ = (id) => document.getElementById(id);

const MAX_DEBUG_LINES = 250;
const debugState = {
  lines: [],
};

function nowStamp() {
  const d = new Date();
  return d.toLocaleTimeString();
}

function safeStringify(value) {
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function renderDebug() {
  const box = $("debugLog");
  if (box) box.textContent = debugState.lines.join("\n");
}

export function debugLog(tag, payload = "") {
  const suffix = payload === "" ? "" : ` ${typeof payload === "string" ? payload : safeStringify(payload)}`;
  debugState.lines.push(`[${nowStamp()}] ${tag}${suffix}`);
  if (debugState.lines.length > MAX_DEBUG_LINES) {
    debugState.lines = debugState.lines.slice(-MAX_DEBUG_LINES);
  }
  renderDebug();
}

export function clearDebugLog() {
  debugState.lines = [];
  renderDebug();
}

export async function copyDebugLog() {
  const text = debugState.lines.join("\n");
  try {
    await navigator.clipboard.writeText(text);
    debugLog("[ui]", "copied debug log to clipboard");
    return true;
  } catch (err) {
    debugLog("[ui]", `copy failed: ${err}`);
    return false;
  }
}

export function initDebugUI() {
  const copyBtn = $("copyDebugBtn");
  const clearBtn = $("clearDebugBtn");

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      copyDebugLog();
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      clearDebugLog();
      debugLog("[ui]", "cleared debug log");
    });
  }

  debugLog("[ui]", "debug console ready");
}

export function setText(el, txt) {
  if (el) el.textContent = String(txt);
}

export function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

export async function getJSON(url) {
  debugLog("[GET]", url);
  const res = await fetch(url);

  let data = null;
  try {
    data = await res.json();
  } catch {}

  debugLog(`[GET ${res.status}]`, { url, data });
  if (!res.ok) console.warn("GET failed", url, res.status, data);
  return data;
}

export async function postJSON(url, payload) {
  debugLog("[POST]", { url, payload });

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  let data = null;
  try {
    data = await res.json();
  } catch {}

  debugLog(`[POST ${res.status}]`, { url, data });
  if (!res.ok) console.warn("POST failed", url, res.status, data);
  return data;
}