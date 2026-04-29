import threading
import time

from config import (
    WALL_FOLLOW_DEFAULT_SIDE,
    WALL_FOLLOW_TARGET_MM,
    WALL_FOLLOW_TOLERANCE_MM,
    WALL_FOLLOW_WALL_LOST_MM,
    WALL_FOLLOW_BASE_SPEED,
    WALL_FOLLOW_TURN_GAIN,
    WALL_FOLLOW_MAX_TURN,
    WALL_FOLLOW_SEARCH_TURN,
    WALL_FOLLOW_FRONT_STOP_MM,
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
    WALL_FOLLOW_CORNER_TURN,
)


class WallFollowService:
    """
    Simple autonomous wall follower.

    Behavior:
    1. If front obstacle is close: pivot left.
    2. If wall is too close: steer away.
    3. If wall is too far: steer toward it.
    4. If wall is lost: gently search toward chosen wall side.
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
        self._tolerance_mm = float(WALL_FOLLOW_TOLERANCE_MM)
        self._wall_lost_mm = float(WALL_FOLLOW_WALL_LOST_MM)
        self._base_speed = float(WALL_FOLLOW_BASE_SPEED)
        self._turn_gain = float(WALL_FOLLOW_TURN_GAIN)
        self._max_turn = float(WALL_FOLLOW_MAX_TURN)
        self._search_turn = float(WALL_FOLLOW_SEARCH_TURN)
        self._front_stop_mm = float(WALL_FOLLOW_FRONT_STOP_MM)
        self._loop_hz = float(WALL_FOLLOW_LOOP_HZ)
        self._forward_sign = float(WALL_FOLLOW_FORWARD_SIGN)

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
            return {
                "ok": True,
                "enabled": self._enabled,
                "side": self._side,
                "state": self._last_state,
                "reason": self._last_reason,
                "target_mm": self._target_mm,
                "tolerance_mm": self._tolerance_mm,
                "wall_lost_mm": self._wall_lost_mm,
                "front_stop_mm": self._front_stop_mm,
                "base_speed": self._base_speed,
                "turn_gain": self._turn_gain,
                "max_turn": self._max_turn,
                "search_turn": self._search_turn,
                "last_error_mm": self._last_error_mm,
                "last_cmd": dict(self._last_cmd),
                "last_zone_snapshot": dict(self._last_zones),
                "front_mm": self._last_zones.get("front_mm"),
                "side_mm": self._last_zones.get("side_mm"),
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

        scan_age = None
        try:
            scan_age = self.lidar.get_status().get("last_scan_age_sec")
        except Exception:
            pass

        return {
            "front_mm": front_mm,
            "side_mm": side_mm,
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

        response = self.robot.drive(left, right, bypass_safety=True)

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
            f"error={error_mm} "
            f"reason={reason}",
            flush=True,
        )

    def _pivot_left(self, power):
        # Your robot uses negative wheel command as forward.
        # Left reverse + right forward = pivot left.
        return power, -power

    def _pivot_right(self, power):
        return -power, power

    def _step(self):
        with self._lock:
            side = self._side
            target_mm = self._target_mm
            tolerance_mm = self._tolerance_mm
            wall_lost_mm = self._wall_lost_mm
            front_stop_mm = self._front_stop_mm
            base_speed = abs(self._base_speed)
            turn_gain = self._turn_gain
            max_turn = abs(self._max_turn)
            search_turn = abs(self._search_turn)
            forward_sign = self._forward_sign

        zones = self._get_zones()
        front_mm = zones.get("front_mm")
        side_mm = zones.get("side_mm")

        # Case 1: obstacle in front.
        if front_mm is not None and front_mm <= front_stop_mm:
            left, right = self._pivot_left(max(search_turn, 0.35))
            self._drive_and_record(
                left,
                right,
                "front_blocked",
                "front obstacle close; pivoting left",
                None,
                zones,
            )
            return

        # Case 4: wall lost.
        if side_mm is None or side_mm > wall_lost_mm:
            if side == "left":
                left, right = self._pivot_left(search_turn)
                reason = "left wall lost; searching left"
            else:
                left, right = self._pivot_right(search_turn)
                reason = "right wall lost; searching right"

            self._drive_and_record(
                left,
                right,
                "searching",
                reason,
                None,
                zones,
            )
            return

        error_mm = side_mm - target_mm

        front_side_mm = zones.get("front_side_mm")

        # Strong corner assist:
        # When the front-side opens up, pivot instead of arc-turning.
        if front_side_mm is not None:
            if side == "left":
                if front_side_mm > WALL_FOLLOW_CORNER_OPEN_MM:
                    left, right = self._pivot_left(WALL_FOLLOW_CORNER_TURN)
                    self._drive_and_record(
                        left,
                        right,
                        "corner_left",
                        "front-left opened; pivoting left with corner",
                        error_mm,
                        zones,
                    )
                    return

                if front_side_mm < WALL_FOLLOW_CORNER_CLOSE_MM:
                    left, right = self._pivot_right(WALL_FOLLOW_CORNER_TURN)
                    self._drive_and_record(
                        left,
                        right,
                        "corner_right",
                        "front-left close; pivoting right away from corner",
                        error_mm,
                        zones,
                    )
                    return

            else:
                if front_side_mm > WALL_FOLLOW_CORNER_OPEN_MM:
                    left, right = self._pivot_right(WALL_FOLLOW_CORNER_TURN)
                    self._drive_and_record(
                        left,
                        right,
                        "corner_right",
                        "front-right opened; pivoting right with corner",
                        error_mm,
                        zones,
                    )
                    return

                if front_side_mm < WALL_FOLLOW_CORNER_CLOSE_MM:
                    left, right = self._pivot_left(WALL_FOLLOW_CORNER_TURN)
                    self._drive_and_record(
                        left,
                        right,
                        "corner_left",
                        "front-right close; pivoting left away from corner",
                        error_mm,
                        zones,
                    )
                    return
        corner_turn = abs(WALL_FOLLOW_CORNER_TURN)

        # Corner assist:
        # For left wall:
        # - front-left opens up = wall is turning left, so turn left
        # - front-left gets close = inside corner/obstacle, so turn right
        #
        # For right wall:
        # - front-right opens up = wall is turning right, so turn right
        # - front-right gets close = inside corner/obstacle, so turn left

        if front_side_mm is not None:
            if side == "left":
                if front_side_mm > WALL_FOLLOW_CORNER_OPEN_MM:
                    self._drive_and_record(
                        forward_sign * (base_speed - corner_turn),
                        forward_sign * (base_speed + corner_turn),
                        "corner_left",
                        "front-left opened; turning left with corner",
                        error_mm,
                        zones,
                    )
                    return

                if front_side_mm < WALL_FOLLOW_CORNER_CLOSE_MM:
                    self._drive_and_record(
                        forward_sign * (base_speed + corner_turn),
                        forward_sign * (base_speed - corner_turn),
                        "corner_right",
                        "front-left close; steering right away from corner",
                        error_mm,
                        zones,
                    )
                    return

            else:
                if front_side_mm > WALL_FOLLOW_CORNER_OPEN_MM:
                    self._drive_and_record(
                        forward_sign * (base_speed + corner_turn),
                        forward_sign * (base_speed - corner_turn),
                        "corner_right",
                        "front-right opened; turning right with corner",
                        error_mm,
                        zones,
                    )
                    return

                if front_side_mm < WALL_FOLLOW_CORNER_CLOSE_MM:
                    self._drive_and_record(
                        forward_sign * (base_speed - corner_turn),
                        forward_sign * (base_speed + corner_turn),
                        "corner_left",
                        "front-right close; steering left away from corner",
                        error_mm,
                        zones,
                    )
                    return

        # Straight if inside tolerance.
        if abs(error_mm) <= tolerance_mm:
            left_power = base_speed
            right_power = base_speed
            reason = "wall centered"
        else:
            turn = min(abs(error_mm) * turn_gain / 1000.0, max_turn)

            if side == "left":
                if error_mm > 0:
                    # Too far from left wall: steer left.
                    left_power = base_speed - turn
                    right_power = base_speed + turn
                    reason = "too far from left wall; steering left"
                else:
                    # Too close to left wall: steer right.
                    left_power = base_speed + turn
                    right_power = base_speed - turn
                    reason = "too close to left wall; steering right"
            else:
                if error_mm > 0:
                    # Too far from right wall: steer right.
                    left_power = base_speed + turn
                    right_power = base_speed - turn
                    reason = "too far from right wall; steering right"
                else:
                    # Too close to right wall: steer left.
                    left_power = base_speed - turn
                    right_power = base_speed + turn
                    reason = "too close to right wall; steering left"

        self._drive_and_record(
            forward_sign * left_power,
            forward_sign * right_power,
            "following",
            reason,
            error_mm,
            zones,
        )