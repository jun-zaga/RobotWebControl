// robot-ui.js (clean joystick rework)

const joy = document.getElementById("joystick");
const knob = document.getElementById("joystick-knob");
const readout = document.getElementById("driveReadout");
const stopBtn = document.getElementById("stopBtn");

const pan = document.getElementById("pan");
const tilt = document.getElementById("tilt");
const waist = document.getElementById("waist");

const panVal = document.getElementById("panVal");
const tiltVal = document.getElementById("tiltVal");
const waistVal = document.getElementById("waistVal");

const face = document.getElementById("robotFace");

// ======= ONLY CHANGE THESE IF THE ROBOT IS WIRED “BACKWARDS” =======
const INVERT_TURN = true;   // if pushing left makes it turn right -> true
const INVERT_FWD  = true;   // if pushing up makes it go backward -> true
// ===================================================================

// Network mock: add ?mock=1 to URL
const MOCK = new URLSearchParams(location.search).get("mock") === "1";

// Throttle drive sends
let lastSent = 0;
const SEND_HZ = 20;
const SEND_PERIOD = 1000 / SEND_HZ;

let dragging = false;
let pointerId = null;

function clamp(x, lo, hi) { return Math.max(lo, Math.min(hi, x)); }

async function postJSON(url, body) {
  if (MOCK) {
    console.log("FAKE POST:", url, body);
    return { ok: true, mock: true };
  }
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await res.json();
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}

function setFace(mode) {
  if (!face) return;
  face.classList.remove("idle", "drive", "stop");
  face.classList.add(mode);
}

function blink() {
  if (!face) return;
  face.classList.add("blink");
  setTimeout(() => face.classList.remove("blink"), 120);
}

function updateSliderVals() {
  if (panVal && pan) panVal.textContent = Number(pan.value).toFixed(2);
  if (tiltVal && tilt) tiltVal.textContent = Number(tilt.value).toFixed(2);
  if (waistVal && waist) waistVal.textContent = Number(waist.value).toFixed(2);
}

function setKnobFromNorm(nx, ny) {
  // nx, ny in [-1,1], ny up positive
  const rect = joy.getBoundingClientRect();
  const radius = rect.width / 2;
  const knobRadius = 33; // knob ~66px
  const max = radius - knobRadius;

  const px = radius + nx * max;
  const py = radius - ny * max; // screen y down -> invert
  knob.style.left = `${px}px`;
  knob.style.top = `${py}px`;
  knob.style.transform = "translate(-50%, -50%)";
}

// Convert arcade (turn, forward) into left/right wheel power
function arcadeToLR(turn, fwd) {
  let l = fwd + turn;
  let r = fwd - turn;

  const m = Math.max(1, Math.abs(l), Math.abs(r));
  return [l / m, r / m];
}

// UI vector -> robot command (DO NOT swap these)
function displayToCommand(nx, ny) {
  let turn = nx;  // 0°=right, 180°=left
  let fwd  = ny;  // 90°=forward, 270°=back

  // optional wiring fixes:
  // turn = -turn;
  // fwd  = -fwd;

  return [turn, fwd];
}


// Pointer -> DISPLAY norm (this defines the angle behavior you described)
function pointerToDisplayNorm(e) {
  const rect = joy.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;

  const dx = e.clientX - cx;     // right positive
  const dy = e.clientY - cy;     // down positive

  const radius = rect.width / 2;
  const knobRadius = 33;
  const max = radius - knobRadius;

  // DISPLAY vector: right=+x, up=+y
  let nx = clamp(dx / max, -1, 1);
  let ny = clamp(-dy / max, -1, 1);

  // circle clamp
  const mag = Math.hypot(nx, ny);
  if (mag > 1) { nx /= mag; ny /= mag; }

  return [nx, ny];
}

async function sendDriveFromCommand(turn, fwd, dbg = null) {
  const now = Date.now();
  if (now - lastSent < SEND_PERIOD) return;
  lastSent = now;

  const [l, r] = arcadeToLR(turn, fwd);

  if (readout) {
    const extra = dbg
      ? ` | disp=(${dbg.nx.toFixed(2)},${dbg.ny.toFixed(2)}) cmd=(${turn.toFixed(2)},${fwd.toFixed(2)})`
      : "";
    readout.textContent =
      `l=${l.toFixed(2)} r=${r.toFixed(2)}${extra}${MOCK ? " [MOCK]" : ""}`;
  }

  setFace((Math.abs(turn) > 0.05 || Math.abs(fwd) > 0.05) ? "drive" : "idle");
  await postJSON("/api/drive", { l, r });
}

function startDrag(e) {
  dragging = true;
  pointerId = e.pointerId;
  joy.setPointerCapture(pointerId);

  const [nx, ny] = pointerToDisplayNorm(e);
  setKnobFromNorm(nx, ny); // UI always matches finger

  const [turn, fwd] = displayToCommand(nx, ny);
  sendDriveFromCommand(turn, fwd, { nx, ny });
}

function moveDrag(e) {
  if (!dragging || e.pointerId !== pointerId) return;

  const [nx, ny] = pointerToDisplayNorm(e);
  setKnobFromNorm(nx, ny);

  const [turn, fwd] = displayToCommand(nx, ny);
  sendDriveFromCommand(turn, fwd, { nx, ny });
}

async function endDrag() {
  dragging = false;
  pointerId = null;

  setKnobFromNorm(0, 0);
  setFace("stop");

  if (readout) readout.textContent = `l=0.00 r=0.00${MOCK ? " [MOCK]" : ""}`;
  await postJSON("/api/stop", {});
}

// Pointer events
if (joy) {
  joy.addEventListener("pointerdown", startDrag);
  joy.addEventListener("pointermove", moveDrag);
  joy.addEventListener("pointerup", endDrag);
  joy.addEventListener("pointercancel", endDrag);
  joy.addEventListener("lostpointercapture", endDrag);
}
if (stopBtn) stopBtn.addEventListener("click", endDrag);

// Sliders (debounced)
function debounce(fn, ms) {
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

const sendHead = debounce(() => {
  updateSliderVals();
  if (pan && tilt) postJSON("/api/head", { pan: Number(pan.value), tilt: Number(tilt.value) });
}, 60);

if (pan) pan.addEventListener("input", sendHead);
if (tilt) tilt.addEventListener("input", sendHead);

if (waist) {
  waist.addEventListener("input", debounce(() => {
    updateSliderVals();
    postJSON("/api/waist", { pos: Number(waist.value) });
  }, 60));
}

// Voice buttons
document.querySelectorAll(".say").forEach(btn => {
  btn.addEventListener("click", () => {
    const id = Number(btn.dataset.id);
    postJSON("/api/say", { phraseId: id });
  });
});

// Stop on refresh
window.addEventListener("beforeunload", () => {
  navigator.sendBeacon("/api/stop", "{}");
});

// Init
if (joy && knob) setKnobFromNorm(0, 0);
updateSliderVals();
setFace("idle");

setInterval(() => { if (Math.random() < 0.22) blink(); }, 900);

if (MOCK) {
  console.log("[MOCK MODE] Network calls disabled. Remove ?mock=1 to use real API.");
}
console.log("Joystick mapping:", { INVERT_TURN, INVERT_FWD });
