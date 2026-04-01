export const $ = (id) => document.getElementById(id);

export function setText(el, txt) {
  if (el) el.textContent = String(txt);
}

export function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

export async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  let data = null;
  try { data = await res.json(); } catch {}

  if (!res.ok) console.warn("POST failed", url, res.status, data);
  return data;
}