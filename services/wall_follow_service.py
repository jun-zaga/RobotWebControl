import threading
import time

from config import (
    WALL_FOLLOW_DEFAULT_SIDE,
    WALL_FOLLOW_TARGET_MM,
    WALL_FOLLOW_TOLERANCE_MM,
    WALL_FOLLOW_FRONT_STOP_MM,
    WALL_FOLLOW_BASE_SPEED,
    WALL_FOLLOW_TURN_GAIN,
    WALL_FOLLOW_MAX_TURN,
    WALL_FOLLOW_SEARCH_TURN,
    WALL_FOLLOW_LOOP_HZ,
    WALL_FOLLOW_WALL_LOST_MM,
    WALL_FOLLOW_LIDAR_LEFT_OFFSET_MM,
    WALL_FOLLOW_FRONT_CENTER_DEG,
    WALL_FOLLOW_FRONT_HALF_ANGLE_DEG,
    WALL_FOLLOW_RIGHT_CENTER_DEG,
    WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG,
    WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG,
    WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG,
    WALL_FOLLOW_BACK_RIGHT_CENTER_DEG,
    WALL_FOLLOW_BACK_RIGHT_HALF_ANGLE_DEG,
    WALL_FOLLOW_LEFT_CENTER_DEG,
    WALL_FOLLOW_LEFT_HALF_ANGLE_DEG,
    WALL_FOLLOW_FRONT_LEFT_CENTER_DEG,
    WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG,
    WALL_FOLLOW_BACK_LEFT_CENTER_DEG,
    WALL_FOLLOW_BACK_LEFT_HALF_ANGLE_DEG,
)


class WallFollowService:
    def __init__(self, robot_service, lidar_service):
        self.robot = robot_service
        self.lidar = lidar_service

        self._lock = threading.Lock()
        self._started = False
        self._enabled = False
        self._thread = None

        self._side = WALL_FOLLOW_DEFAULT_SIDE
        self._target_mm = float(WALL_FOLLOW_TARGET_MM)
        self._tolerance_mm = float(WALL_FOLLOW_TOLERANCE_MM)
        self._front_stop_mm = float(WALL_FOLLOW_FRONT_STOP_MM)
        self._base_speed = float(WALL_FOLLOW_BASE_SPEED)
        self._turn_gain = float(WALL_FOLLOW_TURN_GAIN)
        self._max_turn = float(WALL_FOLLOW_MAX_TURN)
        self._search_turn = float(WALL_FOLLOW_SEARCH_TURN)
        self._wall_lost_mm = float(WALL_FOLLOW_WALL_LOST_MM)
        self._loop_hz = float(WALL_FOLLOW_LOOP_HZ)
        self._lidar_left_offset_mm = float(WALL_FOLLOW_LIDAR_LEFT_OFFSET_MM)

        self._last_cmd = {"left": 0.0, "right": 0.0}
        self._last_state = "idle"
        self._last_error_mm = None
        self._last_reason = "idle"
        self._last_zone_snapshot = {}
        self._last_update_ts = 0.0

    @staticmethod
    def clamp(x, lo, hi):
        return max(lo, min(hi, x))

    @staticmethod
    def _is_number(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    def start(self):
        if self._started:
            return
        self._started = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def enable(self, side=None, target_mm=None, tolerance_mm=None):
        with self._lock:
            if side is not None:
                side = str(side).strip().lower()
                if side not in ("left", "right"):
                    raise ValueError("side must be 'left' or 'right'")
                self._side = side

            if target_mm is not None:
                if not self._is_number(target_mm):
                    raise ValueError("target_mm must be a number")
                self._target_mm = max(50.0, float(target_mm))

            if tolerance_mm is not None:
                if not self._is_number(tolerance_mm):
                    raise ValueError("tolerance_mm must be a number")
                self._tolerance_mm = max(0.0, float(tolerance_mm))

            self._enabled = True
            self._last_state = "starting"
            self._last_reason = "enabled"

        return self.get_status()

    def disable(self, stop_robot=True, reason="disabled"):
        with self._lock:
            was_enabled = self._enabled
            self._enabled = False
            self._last_state = "idle"
            self._last_reason = reason
            self._last_cmd = {"left": 0.0, "right": 0.0}
            self._last_update_ts = time.time()

        if was_enabled and stop_robot:
            self.robot.stop()

        return self.get_status()

    def is_enabled(self):
        with self._lock:
            return self._enabled

    def set_params(self, data):
        with self._lock:
            if "side" in data and data["side"] is not None:
                side = str(data["side"]).strip().lower()
                if side not in ("left", "right"):
                    raise ValueError("side must be 'left' or 'right'")
                self._side = side

            for key in (
                "target_mm",
                "tolerance_mm",
                "front_stop_mm",
                "base_speed",
                "turn_gain",
                "max_turn",
                "search_turn",
                "wall_lost_mm",
                "loop_hz",
                "lidar_left_offset_mm",
            ):
                if key not in data or data[key] is None:
                    continue
                if not self._is_number(data[key]):
                    raise ValueError(f"{key} must be a number")
                value = float(data[key])
                if key == "tolerance_mm":
                    value = max(0.0, value)
                setattr(self, f"_{key}", value)

        return self.get_status()

    def get_status(self):
        with self._lock:
            z = dict(self._last_zone_snapshot)
            return {
                "ok": True,
                "enabled": self._enabled,
                "side": self._side,
                "target_mm": self._target_mm,
                "tolerance_mm": self._tolerance_mm,
                "front_stop_mm": self._front_stop_mm,
                "base_speed": self._base_speed,
                "turn_gain": self._turn_gain,
                "max_turn": self._max_turn,
                "search_turn": self._search_turn,
                "wall_lost_mm": self._wall_lost_mm,
                "loop_hz": self._loop_hz,
                "lidar_left_offset_mm": self._lidar_left_offset_mm,
                "state": self._last_state,
                "reason": self._last_reason,
                "last_error_mm": self._last_error_mm,
                "last_cmd": dict(self._last_cmd),
                "last_zone_snapshot": z,
                "front_mm": z.get("front_mm"),
                "side_mm": z.get("side_mm"),
                "front_side_mm": z.get("front_side_mm"),
                "back_side_mm": z.get("back_side_mm"),
                "scan_age_sec": z.get("scan_age_sec"),
                "config": {
                    "side": self._side,
                    "target_mm": self._target_mm,
                    "tolerance_mm": self._tolerance_mm,
                    "front_stop_mm": self._front_stop_mm,
                    "base_speed": self._base_speed,
                    "turn_gain": self._turn_gain,
                    "max_turn": self._max_turn,
                    "search_turn": self._search_turn,
                    "wall_lost_mm": self._wall_lost_mm,
                    "loop_hz": self._loop_hz,
                    "lidar_left_offset_mm": self._lidar_left_offset_mm,
                    "front_arc_center_deg": WALL_FOLLOW_FRONT_CENTER_DEG,
                },
                "last_update_ts": self._last_update_ts,
            }

    def _loop(self):
        while True:
            with self._lock:
                enabled = self._enabled
                loop_hz = max(1.0, self._loop_hz)

            if enabled:
                try:
                    self._step()
                except Exception as e:
                    print(f"[WALL] step error: {e}", flush=True)
                    self.disable(stop_robot=True, reason=f"error: {e}")

            time.sleep(1.0 / loop_hz)

    def _apply_side_offset(self, raw_mm, side):
        if raw_mm is None:
            return None

        d = max(0.0, float(self._lidar_left_offset_mm))
        if side == "left":
            return raw_mm + d
        return max(0.0, raw_mm - d)

    def _get_zone_snapshot(self, side):
        front = self.lidar.get_zone_min(WALL_FOLLOW_FRONT_CENTER_DEG, WALL_FOLLOW_FRONT_HALF_ANGLE_DEG)

        if side == "right":
            side_raw = self.lidar.get_zone_min(WALL_FOLLOW_RIGHT_CENTER_DEG, WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG)
            front_side_raw = self.lidar.get_zone_min(
                WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG,
                WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG,
            )
            back_side_raw = self.lidar.get_zone_min(
                WALL_FOLLOW_BACK_RIGHT_CENTER_DEG,
                WALL_FOLLOW_BACK_RIGHT_HALF_ANGLE_DEG,
            )
        else:
            side_raw = self.lidar.get_zone_min(WALL_FOLLOW_LEFT_CENTER_DEG, WALL_FOLLOW_LEFT_HALF_ANGLE_DEG)
            front_side_raw = self.lidar.get_zone_min(
                WALL_FOLLOW_FRONT_LEFT_CENTER_DEG,
                WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG,
            )
            back_side_raw = self.lidar.get_zone_min(
                WALL_FOLLOW_BACK_LEFT_CENTER_DEG,
                WALL_FOLLOW_BACK_LEFT_HALF_ANGLE_DEG,
            )

        side_mm = self._apply_side_offset(side_raw, side)
        front_side_mm = self._apply_side_offset(front_side_raw, side)
        back_side_mm = self._apply_side_offset(back_side_raw, side)

        return {
            "front_mm": front,
            "side_raw_mm": side_raw,
            "front_side_raw_mm": front_side_raw,
            "back_side_raw_mm": back_side_raw,
            "side_mm": side_mm,
            "front_side_mm": front_side_mm,
            "back_side_mm": back_side_mm,
            "scan_age_sec": self.lidar.get_status().get("last_scan_age_sec"),
            "lidar_left_offset_mm": self._lidar_left_offset_mm,
        }

    def _step(self):
        with self._lock:
            side = self._side
            target_mm = self._target_mm
            tolerance_mm = self._tolerance_mm
            front_stop_mm = self._front_stop_mm
            base_speed = self._base_speed
            turn_gain = self._turn_gain
            max_turn = self._max_turn
            search_turn = self._search_turn
            wall_lost_mm = self._wall_lost_mm

        z = self._get_zone_snapshot(side)
        front_mm = z["front_mm"]
        side_mm = z["side_mm"]
        front_side_mm = z["front_side_mm"]
        back_side_mm = z["back_side_mm"]
        scan_age_sec = z["scan_age_sec"]

        state = "follow"
        reason = "tracking wall"
        error_mm = None

        if scan_age_sec is None or scan_age_sec > 1.0:
            state = "stale"
            reason = "lidar stale"
            left, right = 0.0, 0.0
        elif front_mm is not None and front_mm <= front_stop_mm:
            state = "avoid_front"
            reason = f"front blocked at {front_mm:.1f} mm"
            if side == "right":
                left, right = self._tank_from_forward_turn(0.0, +max_turn)
            else:
                left, right = self._tank_from_forward_turn(0.0, -max_turn)
        else:
            wall_reference_mm = side_mm
            if front_side_mm is not None and back_side_mm is not None:
                wall_reference_mm = min(front_side_mm, back_side_mm)
            elif front_side_mm is not None:
                wall_reference_mm = front_side_mm
            elif back_side_mm is not None:
                wall_reference_mm = back_side_mm

            if wall_reference_mm is None or wall_reference_mm >= wall_lost_mm:
                state = "search"
                reason = "wall lost"
                turn = -search_turn if side == "right" else +search_turn
                left, right = self._tank_from_forward_turn(-base_speed * 0.5, turn)
            else:
                error_mm = target_mm - wall_reference_mm
                if abs(error_mm) <= tolerance_mm:
                    state = "follow"
                    reason = "within band"
                    left, right = self._tank_from_forward_turn(-base_speed, 0.0)
                else:
                    norm_error = error_mm / max(1.0, target_mm)
                    turn_mag = self.clamp(abs(norm_error) * turn_gain, 0.0, max_turn)

                    if side == "right":
                        turn = +turn_mag if error_mm > 0 else -turn_mag
                    else:
                        turn = -turn_mag if error_mm > 0 else +turn_mag

                    state = "correct"
                    reason = f"wall error {error_mm:.1f} mm"
                    left, right = self._tank_from_forward_turn(-base_speed, turn)

        resp = self.robot.drive(left, right)
        actual_l = resp.get("l", 0.0)
        actual_r = resp.get("r", 0.0)
        safety_mode = (resp.get("safety") or {}).get("mode")

        with self._lock:
            self._last_state = state
            self._last_reason = f"{reason}; safety={safety_mode}"
            self._last_error_mm = error_mm
            self._last_cmd = {"left": actual_l, "right": actual_r}
            self._last_zone_snapshot = z
            self._last_update_ts = time.time()

        print(
            f"[WALL] state={state} side={side} front={front_mm} side_raw={z['side_raw_mm']} "
            f"side_adj={side_mm} front_side_adj={front_side_mm} back_side_adj={back_side_mm} "
            f"err={error_mm} cmd=({actual_l:.2f},{actual_r:.2f}) safety={safety_mode}",
            flush=True,
        )

    def _tank_from_forward_turn(self, forward, turn):
        left = self.clamp(float(forward) + float(turn), -1.0, 1.0)
        right = self.clamp(float(forward) - float(turn), -1.0, 1.0)
        return left, right