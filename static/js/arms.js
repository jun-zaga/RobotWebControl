import { $, setText, postJSON } from "./api.js";

const ARMS_SEND_PERIOD = 60;
let lastArmsSent = 0;

function getArmVals(prefix) {
  const vals = [];
  for (let i = 1; i <= 6; i++) {
    const s = $(`${prefix}J${i}`);
    vals.push(Number(s?.value ?? 0.5));
  }
  return vals;
}

// 🔹 Send BOTH (used for manual slider movement)
export async function sendArms(throttle = true) {
  const now = Date.now();
  if (throttle && now - lastArmsSent < ARMS_SEND_PERIOD) return;
  lastArmsSent = now;

  return postJSON("/api/arms", {
    left_joints: getArmVals("l"),
    right_joints: getArmVals("r"),
  });
}

// 🔹 NEW: send only LEFT
export async function sendLeftArm() {
  return postJSON("/api/arms", {
    left_joints: getArmVals("l")
  });
}

// 🔹 NEW: send only RIGHT
export async function sendRightArm() {
  return postJSON("/api/arms", {
    right_joints: getArmVals("r")
  });
}

export function setArmSliders(prefix, vals) {
  for (let i = 1; i <= 6; i++) {
    const s = $(`${prefix}J${i}`);
    const v = $(`${prefix}J${i}Val`);
    if (!s) continue;
    s.value = Number(vals[i - 1]).toFixed(2);
    if (v) v.textContent = s.value;
  }
}

export function initArms() {
  function wire(prefix, i) {
    const s = $(`${prefix}J${i}`);
    const v = $(`${prefix}J${i}Val`);
    if (!s) return;

    s.addEventListener("input", () => {
      setText(v, s.value);

      // 🔹 Send only the side being changed
      if (prefix === "l") sendLeftArm();
      if (prefix === "r") sendRightArm();
    });

    setText(v, s.value);
  }

  for (let i = 1; i <= 6; i++) {
    wire("l", i);
    wire("r", i);
  }
}