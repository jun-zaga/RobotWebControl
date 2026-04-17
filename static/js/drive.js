import { $, setText, clamp, postJSON } from "./api.js";
import { stopWallFollowSilent } from "./wall_follow.js";

export function initDrive() {
  const joy = $("joystick");
  const knob = $("joystick-knob");
  const readout = $("driveReadout");
  const stopBtn = $("stopBtn");

  if (!joy || !knob) return;

  let dragging = false;
  let activePointerId = null;
  let wallFollowCancelledForThisDrag = false;

  const DEADZONE = 0.05;

  async function sendDrive(l, r) {
    await postJSON("/api/drive", { left: l, right: r });
    setText(readout, `L=${l.toFixed(2)} R=${r.toFixed(2)}`);
  }

  function setKnob(nx, ny) {
    const maxX = (joy.clientWidth - knob.clientWidth) / 2;
    const maxY = (joy.clientHeight - knob.clientHeight) / 2;
    knob.style.transform = `translate(calc(-50% + ${nx * maxX}px), calc(-50% + ${ny * maxY}px))`;
  }

  async function endDrag() {
    dragging = false;
    activePointerId = null;
    wallFollowCancelledForThisDrag = false;
    setKnob(0, 0);
    await sendDrive(0, 0);
  }

  function computeLR(nx, ny) {
    let fwd = ny;
    let turn = nx;

    if (Math.abs(fwd) < DEADZONE) fwd = 0;
    if (Math.abs(turn) < DEADZONE) turn = 0;

    const l = clamp(fwd + turn, -1, 1);
    const r = clamp(fwd - turn, -1, 1);
    return [l, r];
  }

  function onPointerDown(e) {
    e.preventDefault();
    dragging = true;
    activePointerId = e.pointerId;
    try { joy.setPointerCapture(activePointerId); } catch {}
    onPointerMove(e);
  }

  async function onPointerMove(e) {
    if (!dragging) return;
    if (activePointerId !== null && e.pointerId !== activePointerId) return;

    const rect = joy.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const cx = rect.width / 2;
    const cy = rect.height / 2;

    let nx = clamp((x - cx) / cx, -1, 1);
    let ny = clamp((y - cy) / cy, -1, 1);

    setKnob(nx, ny);

    if (!wallFollowCancelledForThisDrag && (Math.abs(nx) > DEADZONE || Math.abs(ny) > DEADZONE)) {
      wallFollowCancelledForThisDrag = true;
      await stopWallFollowSilent();
    }

    const [l, r] = computeLR(nx, ny);
    await sendDrive(l, r);
  }

  function onPointerUp(e) {
    if (activePointerId !== null && e.pointerId !== activePointerId) return;
    endDrag();
  }

  joy.addEventListener("pointerdown", onPointerDown);
  joy.addEventListener("pointermove", onPointerMove);
  joy.addEventListener("pointerup", onPointerUp);
  joy.addEventListener("pointercancel", endDrag);

  window.addEventListener("pointerup", onPointerUp);
  window.addEventListener("pointercancel", endDrag);
  window.addEventListener("blur", endDrag);

  if (stopBtn) {
    stopBtn.addEventListener("click", async () => {
      await endDrag();
      await stopWallFollowSilent();
      await postJSON("/api/stop", {});
    });
  }
}
