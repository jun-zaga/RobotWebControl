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
  const box = $("debugLog");
  if (!box) return;

  const text = box.textContent || "";
  if (!text.trim()) {
    debugLog("[ui]", "copy skipped: empty debug log");
    return;
  }

  let ta = null;

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      debugLog("[ui]", "console copied");
      return;
    }

    ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    ta.style.top = "0";
    ta.style.opacity = "0";
    document.body.appendChild(ta);

    ta.focus();
    ta.select();
    ta.setSelectionRange(0, ta.value.length);

    const ok = document.execCommand("copy");
    if (ok) {
      debugLog("[ui]", "console copied (fallback)");
      return;
    }

    throw new Error("execCommand copy failed");
  } catch (err) {
    debugLog("[ui]", `copy failed: ${err}`);

    try {
      const range = document.createRange();
      range.selectNodeContents(box);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
      debugLog("[ui]", "manual selection highlighted; press Ctrl+C");
    } catch (selectErr) {
      debugLog("[ui]", `manual select failed: ${selectErr}`);
      console.error(selectErr);
    }

    console.error(err);
  } finally {
    if (ta && ta.parentNode) {
      ta.parentNode.removeChild(ta);
    }
  }
}

export function initDebugUI() {
  const copyBtn = $("copyDebugBtn");
  const clearBtn = $("clearDebugBtn");

  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      await copyDebugLog();
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

