import { initDrive } from "./drive.js";
import { initHead } from "./head.js";
import { initArms } from "./arms.js";
import { initPoses } from "./poses.js";
import { initDialog } from "./dialog.js";
import { initWallFollow } from "./wall_follow.js";

initDrive();
initWallFollow();
initHead();
initArms();
initPoses();
initDialog();
