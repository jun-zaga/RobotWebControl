import threading
import time

from config import (
    WALL_FOLLOW_DEFAULT_SIDE,
    WALL_FOLLOW_TARGET_MM,
    WALL_FOLLOW_TARGET_LEFT_MM,
    WALL_FOLLOW_TARGET_RIGHT_MM,
    WALL_FOLLOW_TOLERANCE_MM,
    WALL_FOLLOW_WALL_LOST_MM,
    WALL_FOLLOW_BASE_SPEED,
    WALL_FOLLOW_TURN_GAIN,
    WALL_FOLLOW_MAX_TURN,
    WALL_FOLLOW_SEARCH_TURN,
    WALL_FOLLOW_FRONT_STOP_MM,
    WALL_FOLLOW_FRONT_SIDE_DANGER_MM,
    WALL_FOLLOW_LOOP_HZ,
    WALL_FOLLOW_FORWARD_SIGN,
    WALL_FOLLOW_FRONT_CENTER_DEG,
    WALL_FOLLOW_FRONT_HALF_ANGLE_DEG,
    WALL_FOLLOW_LEFT_CENTER_DEG,
    WALL_FOLLOW_LEFT_HALF_ANGLE_DEG,
    WALL_FOLLOW_RIGHT_CENTER_DEG,
    WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG,
    WALL_FOLLOW_FRONT_LEFT_CENTER_DEG,
    WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG,
    WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG,
    WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG,
    WALL_FOLLOW_CORNER_OPEN_MM,
    WALL_FOLLOW_CORNER_CLOSE_MM,
    WALL_FOLLOW_LEFT_BODY_OFFSET_MM,
    WALL_FOLLOW_RIGHT_BODY_OFFSET_MM,
)


class WallFollowService:
    """
    Wall follower using tank-style left/right commands.

    Movement idea:
      - Normal follow uses gentle steering.
      - If followed wall disappears/falls far away:
          right wall -> right wheel anchors, left wheel drives
          left wall  -> left wheel anchors, right wheel drives
      - Safety is NOT bypassed.
    """

    def __init__(self, robot_service, lidar_service):
        self.robot = robot_service
        self.lidar = lidar_service

        self._lock = threading.RLock()
        self._started = False
        self._enabled = False
        self._thread = None

        self._side = WALL_FOLLOW_DEFAULT_SIDE

        self._target_mm = float(WALL_FOLLOW_TARGET_MM)
        self._target_left_mm = float(WALL_FOLLOW_TARGET_LEFT_MM)
        self._target_right_mm = float(WALL_FOLLOW_TARGET_RIGHT_MM)

        self._tolerance_mm = float(WALL_FOLLOW_TOLERANCE_MM)
        self._wall_lost_mm = float(WALL_FOLLOW_WALL_LOST_MM)
        self._base_speed = float(WALL_FOLLOW_BASE_SPEED)
        self._turn_gain = float(WALL_FOLLOW_TURN_GAIN)
        self._max_turn = float(WALL_FOLLOW_MAX_TURN)
        self._search_turn = float(WALL_FOLLOW_SEARCH_TURN)
        self._front_stop_mm = float(WALL_FOLLOW_FRONT_STOP_MM)
        self._front_side_danger_mm = float(WALL_FOLLOW_FRONT_SIDE_DANGER_MM)
        self._loop_hz = float(WALL_FOLLOW_LOOP_HZ)
        self._forward_sign = float(WALL_FOLLOW_FORWARD_SIGN)

        self._left_body_offset_mm = float(WALL_FOLLOW_LEFT_BODY_OFFSET_MM)
        self._right_body_offset_mm = float(WALL_FOLLOW_RIGHT_BODY_OFFSET_MM)

        self._last_state = "idle"
        self._last_reason = "idle"
        self._last_error_mm = None
        self._last_cmd = {"left": 0.0, "right": 0.0}
        self._last_zones = {}
        self._last_update_ts = 0.0

    def start(self):
        with self._lock:
            if self._started:
                return

            self._started = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def enable(self, side=None):
        with self._lock:
            if side in ("left", "right"):
                self._side = side

            self._enabled = True
            self._last_state = "enabled"
            self._last_reason = "enabled"
            self._last_update_ts = time.time()

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
            side = data.get("side")
            if side in ("left", "right"):
                self._side = side

        return self.get_status()

    def get_status(self):
        with self._lock:
            active_target = (
                self._target_left_mm
                if self._side == "left"
                else self._target_right_mm
            )

            return {
                "ok": True,
                "enabled": self._enabled,
                "side": self._side,
                "state": self._last_state,
                "reason": self._last_reason,

                "target_mm": active_target,
                "target_fallback_mm": self._target_mm,
                "target_left_mm": self._target_left_mm,
                "target_right_mm": self._target_right_mm,

                "tolerance_mm": self._tolerance_mm,
                "wall_lost_mm": self._wall_lost_mm,
                "front_stop_mm": self._front_stop_mm,
                "front_side_danger_mm": self._front_side_danger_mm,

                "base_speed": self._base_speed,
                "turn_gain": self._turn_gain,
                "max_turn": self._max_turn,
                "search_turn": self._search_turn,

                "left_body_offset_mm": self._left_body_offset_mm,
                "right_body_offset_mm": self._right_body_offset_mm,

                "last_error_mm": self._last_error_mm,
                "last_cmd": dict(self._last_cmd),
                "last_zone_snapshot": dict(self._last_zones),

                "front_mm": self._last_zones.get("front_mm"),
                "side_mm": self._last_zones.get("side_mm"),
                "corrected_side_mm": self._last_zones.get("corrected_side_mm"),
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
                    print(f"[WALL] error: {e}", flush=True)
                    self.disable(stop_robot=True, reason=f"error: {e}")

            time.sleep(1.0 / loop_hz)

    def _zone_min(self, center_deg, half_angle_deg):
        try:
            value = self.lidar.get_zone_min(center_deg, half_angle_deg)
        except Exception:
            return None

        if value is None:
            return None

        value = float(value)

        if value < 40 or value > 4000:
            return None

        return value

    def _correct_side_distance(self, side, side_mm):
        if side_mm is None:
            return None

        if side == "left":
            return side_mm - self._left_body_offset_mm

        return side_mm - self._right_body_offset_mm

    def _get_zones(self):
        with self._lock:
            side = self._side

        front_mm = self._zone_min(
            WALL_FOLLOW_FRONT_CENTER_DEG,
            WALL_FOLLOW_FRONT_HALF_ANGLE_DEG,
        )

        left_mm = self._zone_min(
            WALL_FOLLOW_LEFT_CENTER_DEG,
            WALL_FOLLOW_LEFT_HALF_ANGLE_DEG,
        )

        right_mm = self._zone_min(
            WALL_FOLLOW_RIGHT_CENTER_DEG,
            WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG,
        )

        front_left_mm = self._zone_min(
            WALL_FOLLOW_FRONT_LEFT_CENTER_DEG,
            WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG,
        )

        front_right_mm = self._zone_min(
            WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG,
            WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG,
        )

        if side == "left":
            side_mm = left_mm
            front_side_mm = front_left_mm
        else:
            side_mm = right_mm
            front_side_mm = front_right_mm

        corrected_side_mm = self._correct_side_distance(side, side_mm)

        scan_age = None
        try:
            scan_age = self.lidar.get_status().get("last_scan_age_sec")
        except Exception:
            pass

        return {
            "front_mm": front_mm,
            "side_mm": side_mm,
            "corrected_side_mm": corrected_side_mm,
            "left_mm": left_mm,
            "right_mm": right_mm,
            "front_left_mm": front_left_mm,
            "front_right_mm": front_right_mm,
            "front_side_mm": front_side_mm,
            "scan_age_sec": scan_age,
        }

    @staticmethod
    def _clamp(value, lo, hi):
        return max(lo, min(hi, float(value)))

    def _drive_and_record(self, left, right, state, reason, error_mm, zones):
        left = self._clamp(left, -1.0, 1.0)
        right = self._clamp(right, -1.0, 1.0)

        # Safety is NOT bypassed.
        response = self.robot.drive(left, right, bypass_safety=False)

        actual_left = response.get("l", left)
        actual_right = response.get("r", right)
        safety = response.get("safety") or {}

        with self._lock:
            self._last_state = state
            self._last_reason = f"{reason}; safety={safety.get('mode')}"
            self._last_error_mm = error_mm
            self._last_cmd = {
                "left": actual_left,
                "right": actual_right,
            }
            self._last_zones = dict(zones)
            self._last_update_ts = time.time()

        print(
            f"[WALL] {state} "
            f"cmd=({left:.2f},{right:.2f}) "
            f"front={zones.get('front_mm')} "
            f"side={zones.get('side_mm')} "
            f"corrected_side={zones.get('corrected_side_mm')} "
            f"error={error_mm} "
            f"reason={reason} "
            f"safety={safety.get('mode')}",
            flush=True,
        )

    def _pivot_left(self, power):
        # left backward, right forward
        return power, -power

    def _pivot_right(self, power):
        # left forward, right backward
        return -power, power

    def _anchor_right_turn(self):
        # Right wall missing/opening:
        # right wheel anchors/slows, left wheel drives forward.
        return -1.0, -0.10

    def _anchor_left_turn(self):
        # Left wall missing/opening:
        # left wheel anchors/slows, right wheel drives forward.
        return -0.10, -1.0

    def _step(self):
        with self._lock:
            side = self._side

            if side == "left":
                target_mm = self._target_left_mm
            elif side == "right":
                target_mm = self._target_right_mm
            else:
                target_mm = self._target_mm

            tolerance_mm = self._tolerance_mm
            wall_lost_mm = self._wall_lost_mm
            front_stop_mm = self._front_stop_mm
            front_side_danger_mm = self._front_side_danger_mm

            base_speed = abs(self._base_speed)
            turn_gain = self._turn_gain
            max_turn = abs(self._max_turn)

        zones = self._get_zones()
        front_mm = zones.get("front_mm")
        side_mm = zones.get("side_mm")
        corrected_side_mm = zones.get("corrected_side_mm")
        front_side_mm = zones.get("front_side_mm")

        # True front obstacle: hard pivot away.
        if front_mm is not None and front_mm <= front_stop_mm:
            pivot_power = 1.0

            if side == "right":
                left, right = self._pivot_left(pivot_power)
            else:
                left, right = self._pivot_right(pivot_power)

            self._drive_and_record(
                left,
                right,
                "front_blocked",
                "front obstacle close; hard pivoting away",
                None,
                zones,
            )
            return

        # Front-side danger: soft steer unless extremely close.
        if front_side_mm is not None and front_side_mm <= front_side_danger_mm:
            if front_side_mm <= 320:
                pivot_power = 1.0

                if side == "right":
                    left, right = self._pivot_left(pivot_power)
                    reason = "front-right very close; hard pivoting left"
                else:
                    left, right = self._pivot_right(pivot_power)
                    reason = "front-left very close; hard pivoting right"
            else:
                if side == "right":
                    left = -0.65
                    right = -0.85
                    reason = "front-right close; soft steering left"
                else:
                    left = -0.85
                    right = -0.65
                    reason = "front-left close; soft steering right"

            self._drive_and_record(
                left,
                right,
                "front_side_close",
                reason,
                None,
                zones,
            )
            return

        # Too close to followed wall: gentle recovery away.
        if side == "right" and side_mm is not None and side_mm < target_mm - tolerance_mm:
            left = -0.78
            right = -0.85
            self._drive_and_record(
                left,
                right,
                "recovering_right",
                "soft recovering away from right wall",
                side_mm - target_mm,
                zones,
            )
            return

        if side == "left" and side_mm is not None and side_mm < target_mm - tolerance_mm:
            left = -0.85
            right = -0.78
            self._drive_and_record(
                left,
                right,
                "recovering_left",
                "soft recovering away from left wall",
                side_mm - target_mm,
                zones,
            )
            return

        # Wall completely invisible: stop instead of driving blind.
        # Wall side cone missing:
        # If the front-side cone still sees the wall/corner, keep anchor-turning.
        # If both are missing, stop instead of driving blind.
        if side_mm is None:
            if front_side_mm is not None and front_side_mm < wall_lost_mm:
                if side == "right":
                    left, right = self._anchor_right_turn()
                    reason = "right side missing but front-right visible; continuing anchor-right turn"
                else:
                    left, right = self._anchor_left_turn()
                    reason = "left side missing but front-left visible; continuing anchor-left turn"

                self._drive_and_record(
                    left,
                    right,
                    "searching",
                    reason,
                    None,
                    zones,
                )
                return

            self._drive_and_record(
                0.0,
                0.0,
                "wall_lost_stop",
                f"{side} wall not visible; stopping instead of driving blind",
                None,
                zones,
            )
            return

        # Wall far: pivot toward missing wall using that side as anchor.
        if side_mm > wall_lost_mm:
            if side == "right":
                left, right = self._anchor_right_turn()
                reason = "right wall far; anchor-right pivot to re-detect"
            else:
                left, right = self._anchor_left_turn()
                reason = "left wall far; anchor-left pivot to re-detect"

            self._drive_and_record(
                left,
                right,
                "searching",
                reason,
                None,
                zones,
            )
            return

        if corrected_side_mm is None:
            self._drive_and_record(
                0.0,
                0.0,
                "no_side_distance",
                "side distance unavailable; stopping",
                None,
                zones,
            )
            return

        error_mm = corrected_side_mm - target_mm

        # Corner assist:
        # If the wall opens up ahead and we are safely far from the wall,
        # anchor that side wheel and pivot toward the missing wall.
        if front_side_mm is not None:
            if side == "left":
                if (
                    front_side_mm > WALL_FOLLOW_CORNER_OPEN_MM
                    and corrected_side_mm > target_mm + 250.0
                ):
                    left, right = self._anchor_left_turn()
                    self._drive_and_record(
                        left,
                        right,
                        "corner_left",
                        "front-left opened; anchor-left pivot to re-detect",
                        error_mm,
                        zones,
                    )
                    return

                if front_side_mm < WALL_FOLLOW_CORNER_CLOSE_MM:
                    left, right = -1.0, -0.50
                    self._drive_and_record(
                        left,
                        right,
                        "corner_right",
                        "front-left close; soft right correction",
                        error_mm,
                        zones,
                    )
                    return

            else:
                if (
                    front_side_mm > WALL_FOLLOW_CORNER_OPEN_MM
                    and corrected_side_mm > target_mm + 250.0
                ):
                    left, right = self._anchor_right_turn()
                    self._drive_and_record(
                        left,
                        right,
                        "corner_right",
                        "front-right opened; anchor-right pivot to re-detect",
                        error_mm,
                        zones,
                    )
                    return

                if front_side_mm < WALL_FOLLOW_CORNER_CLOSE_MM:
                    left, right = -0.50, -1.0
                    self._drive_and_record(
                        left,
                        right,
                        "corner_left",
                        "front-right close; soft left correction",
                        error_mm,
                        zones,
                    )
                    return

        
        
        if abs(error_mm) <= tolerance_mm:
            left_power = base_speed
            right_power = base_speed
            reason = "wall centered; stabilizing forward"
        else:
            turn = min(abs(error_mm) * turn_gain / 1000.0, max_turn)

            if side == "left":
                if error_mm > 0:
                    left_power = base_speed - turn
                    right_power = base_speed + turn
                    reason = "too far from left wall; steering left"
                else:
                    left_power = base_speed + turn
                    right_power = base_speed - turn
                    reason = "too close to left wall; steering right"
            else:
                if error_mm > 0:
                    left_power = base_speed + turn
                    right_power = base_speed - turn
                    reason = "too far from right wall; steering right"
                else:
                    left_power = base_speed - turn
                    right_power = base_speed + turn
                    reason = "too close to right wall; steering left"

        self._drive_and_record(
            WALL_FOLLOW_FORWARD_SIGN * left_power,
            WALL_FOLLOW_FORWARD_SIGN * right_power,
            "following",
            reason,
            error_mm,
            zones,
        )