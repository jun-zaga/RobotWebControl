const joy = document.getElementById("joystick");
const knob = document.getElementById("joystick-knob");
const readout = document.getElementById("driveReadout");
const stopBtn = document.getElementById("stopBtn");

const pan = document.getElementById("pan");
const tilt = document.getElementById("tilt");
const waist = document.getElementById("waist");

let dragging = false;
let pointerId = null;

let lastSent = 0;
const SEND_HZ = 20;
const SEND_PERIOD = 1000 / SEND_HZ;

// current joystick normalized state in [-1,1]
let joyX = 0;
let joyY = 0;

function clamp(x, lo, hi) { return Math.max(lo, Math.min(hi, x)); }

async function postJSON(url, body) {
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

function setKnobFromNorm(nx, ny) {
  // nx, ny in [-1,1] (ny up positive)
  const rect = joy.getBoundingClientRect();
  const radius = rect.width / 2;
  const knobRadius = 28; // half of knob size (~56)
  const max = radius - knobRadius;

  const px = radius + nx * max;
  const py = radius - ny * max; // invert for screen coords

  knob.style.left = `${px}px`;
  knob.style.top = `${py}px`;
  knob.style.transform = "translate(-50%, -50%)";
}

function arcadeToLR(x, y) {
  // x=turn, y=forward, both in [-1,1]
  let l = y + x;
  let r = y - x;

  // normalize if needed
  const m = Math.max(1, Math.abs(l), Math.abs(r));
  l /= m; r /= m;

  return [l, r];
}

async function sendDrive(x, y) {
  const now = Date.now();
  if (now - lastSent < SEND_PERIOD) return;
  lastSent = now;

  const [l, r] = arcadeToLR(x, y);
  readout.textContent =
    `x=${x.toFixed(2)} y=${y.toFixed(2)} | l=${l.toFixed(2)} r=${r.toFixed(2)}`;

  await postJSON("/api/drive", { l, r });
}

function computeNormFromPointer(e) {
  const rect = joy.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;

  const dx = e.clientX - cx;
  const dy = e.clientY - cy;

  const radius = rect.width / 2;
  const knobRadius = 28;
  const max = radius - knobRadius;

  let nx = clamp(dx / max, -1, 1);
  let ny = clamp(-dy / max, -1, 1); // up positive

  // circular clamp
  const mag = Math.hypot(nx, ny);
  if (mag > 1) { nx /= mag; ny /= mag; }

  return [nx, ny];
}

function startDrag(e) {
  dragging = true;
  pointerId = e.pointerId;
  joy.setPointerCapture(pointerId);

  const [nx, ny] = computeNormFromPointer(e);
  joyX = nx; joyY = ny;
  setKnobFromNorm(joyX, joyY);
  sendDrive(joyX, joyY);
}

function moveDrag(e) {
  if (!dragging || e.pointerId !== pointerId) return;

  const [nx, ny] = computeNormFromPointer(e);
  joyX = nx; joyY = ny;

  setKnobFromNorm(joyX, joyY);
  sendDrive(joyX, joyY);
}

async function endDrag() {
  dragging = false;
  pointerId = null;
  joyX = 0; joyY = 0;
  setKnobFromNorm(0, 0);
  readout.textContent = "x=0.00 y=0.00 | l=0.00 r=0.00";
  await postJSON("/api/stop", {});
}

joy.addEventListener("pointerdown", (e) => startDrag(e));
joy.addEventListener("pointermove", (e) => moveDrag(e));
joy.addEventListener("pointerup", () => endDrag());
joy.addEventListener("pointercancel", () => endDrag());
joy.addEventListener("lostpointercapture", () => endDrag());

stopBtn.addEventListener("click", () => endDrag());

// Head sliders (debounced)
function debounce(fn, ms) {
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

const sendHead = debounce(() => {
  postJSON("/api/head", { pan: Number(pan.value), tilt: Number(tilt.value) });
}, 60);

pan.addEventListener("input", sendHead);
tilt.addEventListener("input", sendHead);

waist.addEventListener("input", debounce(() => {
  postJSON("/api/waist", { pos: Number(waist.value) });
}, 60));

// Voice buttons
document.querySelectorAll(".say").forEach(btn => {
  btn.addEventListener("click", () => {
    const id = Number(btn.dataset.id);
    postJSON("/api/say", { phraseId: id });
  });
});

// Safety: try to stop on refresh/close
window.addEventListener("beforeunload", () => {
  navigator.sendBeacon("/api/stop", "{}");
});

// init knob center
setKnobFromNorm(0, 0);
