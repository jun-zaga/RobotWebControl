import { $, getJSON, postJSON, debugLog } from "./api.js";

let greeterStatusTimer = null;

export function initGreeter() {
  const stopBtn = $("greeterStopBtn");
  const statusBtn = $("greeterStatusBtn");
  const bathroomBtn = $("greeterBathroomBtn");
  const labBtn = $("greeterLabBtn");
    const startBtn = $("greeterStartBtn");
    debugLog("[GREETER]", {
    startBtnFound: !!startBtn,
    stopBtnFound: !!stopBtn,
    statusBtnFound: !!statusBtn,
    bathroomBtnFound: !!bathroomBtn,
    labBtnFound: !!labBtn,
    });
    

    if (startBtn) {
    startBtn.addEventListener("click", startGreeter);
    }
  if (stopBtn) stopBtn.addEventListener("click", stopGreeter);
  if (statusBtn) statusBtn.addEventListener("click", refreshGreeterStatus);
  if (bathroomBtn) bathroomBtn.addEventListener("click", testBathroom);
  if (labBtn) labBtn.addEventListener("click", testRobotLab);

  refreshGreeterStatus().catch((err) => {
    debugLog("[GREETER]", `initial status failed: ${err}`);
  });

  if (!greeterStatusTimer) {
    greeterStatusTimer = setInterval(() => {
      refreshGreeterStatus().catch(() => {});
    }, 1500);
  }

  debugLog("[GREETER]", "UI initialized");
}

function showGreeterStatus(data) {
  const box = $("greeterStatus");

  if (box) {
    box.textContent = JSON.stringify(data, null, 2);
  }

  debugLog("[GREETER]", data);
}

async function startGreeter() {
  const data = await postJSON("/api/greeter/start", {});
  showGreeterStatus(data);
}

async function stopGreeter() {
  const data = await postJSON("/api/greeter/stop", {});
  showGreeterStatus(data);
}

async function refreshGreeterStatus() {
  const data = await getJSON("/api/greeter/status");
  showGreeterStatus(data);
}

async function testBathroom() {
  const data = await postJSON("/api/greeter/test_destination", {
    destination: "bathroom",
  });

  showGreeterStatus(data);
}

async function testRobotLab() {
  const data = await postJSON("/api/greeter/test_destination", {
    destination: "robot lab",
  });

  showGreeterStatus(data);
}

