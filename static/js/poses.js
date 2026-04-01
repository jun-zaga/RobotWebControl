import { $, postJSON } from "./api.js";
import { setArmSliders, sendArms, sendLeftArm, sendRightArm } from "./arms.js";

export function initPoses() {
  const neutralBtn = $("armsNeutralBtn");
  if (neutralBtn) {
    neutralBtn.addEventListener("click", async () => {
      const res = await postJSON("/api/pose", { name: "arms_neutral" });
      if (res?.ok) {
        if (Array.isArray(res.left_joints)) setArmSliders("l", res.left_joints);
        if (Array.isArray(res.right_joints)) setArmSliders("r", res.right_joints);
        await sendArms(false);
      }
    });
  }

  const raiseLeft = $("raiseLeftBtn");
  if (raiseLeft) {
    raiseLeft.addEventListener("click", async () => {
      const res = await postJSON("/api/pose", { name: "raise_left" });
      if (res?.ok && Array.isArray(res.left_joints)) {
        setArmSliders("l", res.left_joints);
        await sendLeftArm();
      }
    });
  }

  const raiseRight = $("raiseRightBtn");
  if (raiseRight) {
    raiseRight.addEventListener("click", async () => {
      const res = await postJSON("/api/pose", { name: "raise_right" });
      if (res?.ok && Array.isArray(res.right_joints)) {
        setArmSliders("r", res.right_joints);
        await sendRightArm();
      }
    });
  }

  // Hands Open = only joint 6
  const handsOpen = $("handsOpenBtn");
  if (handsOpen) {
    handsOpen.addEventListener("click", async () => {
      $("lJ6").value = "0.05";
      $("rJ6").value = "0.05";
      $("lJ6Val").textContent = "0.05";
      $("rJ6Val").textContent = "0.05";

      await postJSON("/api/arms", {
        left_joints:  [null, null, null, null, null, 0.05],
        right_joints: [null, null, null, null, null, 0.05],
      });
    });
  }

  // Hands Close = only joint 6
  const handsClose = $("handsCloseBtn");
  if (handsClose) {
    handsClose.addEventListener("click", async () => {
      $("lJ6").value = "0.95";
      $("rJ6").value = "0.95";
      $("lJ6Val").textContent = "0.95";
      $("rJ6Val").textContent = "0.95";

      await postJSON("/api/arms", {
        left_joints:  [null, null, null, null, null, 0.95],
        right_joints: [null, null, null, null, null, 0.95],
      });
    });
  }
}