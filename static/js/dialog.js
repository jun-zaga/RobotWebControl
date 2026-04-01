import { $, postJSON } from "./api.js";

export function initDialog() {
  const dialogInput = $("dialogInput");
  const dialogSendBtn = $("dialogSendBtn");
  const dialogOut = $("dialogOut");
  const runScriptBtn = $("runScriptBtn");

  async function send() {
    const text = (dialogInput?.value ?? "").trim();
    if (!text) return;
    if (dialogInput) dialogInput.value = "";

    try {
      const res = await postJSON("/api/dialog", { text });
      if (res && dialogOut) {
        const line = `[${res.state}] ${res.speak || ""}`.trim();
        dialogOut.textContent = (dialogOut.textContent + "\n" + line).trim();
      }
    } catch (err) {
      if (dialogOut) {
        dialogOut.textContent = (dialogOut.textContent + "\n[dialog] failed to call /api/dialog").trim();
      }
      console.error(err);
    }
  }

  if (dialogSendBtn) {
    dialogSendBtn.addEventListener("click", send);
  }

  if (dialogInput) {
    dialogInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        send();
      }
    });
  }

  if (runScriptBtn) {
    runScriptBtn.onclick = async () => {
      try {
        const res = await fetch("/api/run_script", { method: "POST" });
        const data = await res.json();

        if (dialogOut) {
          const line = `[script ${data.state || ""}] ${data.speak || data.message || data.error || ""}`.trim();
          dialogOut.textContent = (dialogOut.textContent + "\n" + line).trim();
        }
      } catch (err) {
        if (dialogOut) {
          dialogOut.textContent = (dialogOut.textContent + "\n[script] failed to call /api/run_script").trim();
        }
        console.error(err);
      }
    };
  }
}