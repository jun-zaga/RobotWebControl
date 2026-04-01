import { $, setText, postJSON } from "./api.js";

export function initHead() {
  function wire(sliderId, outId, axis) {
    const s = $(sliderId);
    const out = $(outId);
    if (!s) return;

    const send = () => postJSON("/api/servo", { axis, value: Number(s.value) });

    s.addEventListener("input", () => {
      setText(out, s.value);
      send();
    });

    setText(out, s.value);
  }

  wire("pan", "panVal", "pan");
  wire("tilt", "tiltVal", "tilt");
  wire("waist", "waistVal", "waist");
}