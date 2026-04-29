import threading
import time

from config import *


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
        self._left_body_offset_mm = float(WALL_FOLLOW_LEFT_BODY_OFFSET_MM)
        self._right_body_offset_mm = float(WALL_FOLLOW_RIGHT_BODY_OFFSET_MM)
        self._forward_sign = float(WALL_FOLLOW_FORWARD_SIGN)
        self._turn_sign = float(WALL_FOLLOW_TURN_SIGN)
        self._min_motor_power = float(WALL_FOLLOW_MIN_MOTOR_POWER)

        self._last_cmd = {"left": 0.0, "right": 0.0}
        self._last_state = "idle"
        self._last_error_mm = None
        self._last_reason = "idle"
        self._last_zone_snapshot = {}
        self._last_update_ts = 0.0

    def start(self):
        if self._started:
            return
        self._started = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def enable(self, side=None):
        with self._lock:
            if side is not None:
                side = str(side).strip().lower()
                if side in ("left", "right"):
                    self._side = side

            self._enabled = True
            self._last_state = "enabled"
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
            side = data.get("side")
            if side is not None:
                side = str(side).strip().lower()
                if side in ("left", "right"):
                    self._side = side

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
                "left_body_offset_mm": self._left_body_offset_mm,
                "right_body_offset_mm": self._right_body_offset_mm,
                "forward_sign": self._forward_sign,
                "turn_sign": self._turn_sign,
                "min_motor_power": self._min_motor_power,
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
                    "left_body_offset_mm": self._left_body_offset_mm,
                    "right_body_offset_mm": self._right_body_offset_mm,
                    "forward_sign": self._forward_sign,
                    "turn_sign": self._turn_sign,
                    "min_motor_power": self._min_motor_power,
                    "front_center_deg": WALL_FOLLOW_FRONT_CENTER_DEG,
                    "left_center_deg": WALL_FOLLOW_LEFT_CENTER_DEG,
                    "right_center_deg": WALL_FOLLOW_RIGHT_CENTER_DEG,
                    "front_left_center_deg": WALL_FOLLOW_FRONT_LEFT_CENTER_DEG,
                    "front_right_center_deg": WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG,
                    "back_left_center_deg": WALL_FOLLOW_BACK_LEFT_CENTER_DEG,
                    "back_right_center_deg": WALL_FOLLOW_BACK_RIGHT_CENTER_DEG,
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


    def _zone_min_safe(self, center_deg, half_angle_deg):
        try:
            return self.lidar.get_zone_min(center_deg, half_angle_deg)
        except Exception:
            return None
        
    def _valid_mm(value, lo=50, hi=2500):
        if value is None:
            return None

        value = float(value)

        if lo <= value <= hi:
            return value

        return None
        
        
    def _get_zones(self):
        def _valid_mm(value, lo=50, hi=2500):
            if value is None:
                return None

            try:
                value = float(value)
            except Exception:
                return None

            if lo <= value <= hi:
                return value

            return None

        scan_age = None
        try:
            scan_age = self.lidar.get_status().get("last_scan_age_sec")
        except Exception:
            pass

        front_mm = self._zone_min_safe(
            WALL_FOLLOW_FRONT_CENTER_DEG,
            WALL_FOLLOW_FRONT_HALF_ANGLE_DEG,
        )

        if self._side == "left":
            side_center = WALL_FOLLOW_LEFT_CENTER_DEG
            side_half_angle = WALL_FOLLOW_LEFT_HALF_ANGLE_DEG

            front_side_center = WALL_FOLLOW_FRONT_LEFT_CENTER_DEG
            front_side_half_angle = WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG

            back_side_center = WALL_FOLLOW_BACK_LEFT_CENTER_DEG
            back_side_half_angle = WALL_FOLLOW_BACK_LEFT_HALF_ANGLE_DEG

            body_offset = self._left_body_offset_mm

        else:
            side_center = WALL_FOLLOW_RIGHT_CENTER_DEG
            side_half_angle = WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG

            front_side_center = WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG
            front_side_half_angle = WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG

            back_side_center = WALL_FOLLOW_BACK_RIGHT_CENTER_DEG
            back_side_half_angle = WALL_FOLLOW_BACK_RIGHT_HALF_ANGLE_DEG

            body_offset = self._right_body_offset_mm

        raw_side_mm = self._zone_min_safe(side_center, side_half_angle)
        front_side_mm = self._zone_min_safe(front_side_center, front_side_half_angle)
        back_side_mm = self._zone_min_safe(back_side_center, back_side_half_angle)

        raw = _valid_mm(raw_side_mm)
        front_side = _valid_mm(front_side_mm)
        back_side = _valid_mm(back_side_mm)

        side_mm = None
        side_source = "none"

        AGREE_MM = 120
        SELF_ECHO_MAX_MM = 240

        raw_agrees = False

        for other in (front_side, back_side):
            if raw is not None and other is not None:
                if 50 <= other <= 700 and abs(raw - other) <= AGREE_MM:
                    raw_agrees = True

        # Trust raw side only if it agrees with a nearby side slice,
        # or if it is clearly far away. A lonely ~170mm reading is likely
        # the robot seeing itself/bracket/body instead of the wall.
        if raw is not None:
            if raw_agrees:
                side_mm = raw
                side_source = "raw_confirmed"
            elif raw > SELF_ECHO_MAX_MM:
                side_mm = raw
                side_source = "raw_far"
            else:
                side_mm = None
                side_source = "raw_rejected_self_echo"

        # Fallback: use front/back side only if they agree with each other.
        if side_mm is None and front_side is not None and back_side is not None:
            if abs(front_side - back_side) <= AGREE_MM:
                side_mm = (front_side + back_side) / 2.0
                side_source = "front_back_average"

        if side_mm is not None:
            side_mm = max(0.0, side_mm - float(body_offset))

        return {
            "front_mm": front_mm,
            "side_mm": side_mm,
            "raw_side_mm": raw_side_mm,
            "front_side_mm": front_side_mm,
            "back_side_mm": back_side_mm,
            "scan_age_sec": scan_age,
            "side_center_deg": side_center,
            "front_side_center_deg": front_side_center,
            "back_side_center_deg": back_side_center,
            "side_source": side_source,
        }

    def _clamp_motor(self, value):
        value = max(-1.0, min(1.0, float(value)))

        if abs(value) < 0.001:
            return 0.0

        min_power = max(0.0, min(1.0, self._min_motor_power))
        if abs(value) < min_power:
            return min_power if value > 0 else -min_power

        return value

    def _drive_and_record(self, left, right, state, reason, error_mm, zones):
        left = self._clamp_motor(left)
        right = self._clamp_motor(right)

        resp = self.robot.drive(left, right)

        actual_l = resp.get("l", left)
        actual_r = resp.get("r", right)
        safety_mode = (resp.get("safety") or {}).get("mode")

        with self._lock:
            self._last_state = state
            self._last_reason = f"{reason}; safety={safety_mode}"
            self._last_error_mm = error_mm
            self._last_cmd = {"left": actual_l, "right": actual_r}
            self._last_zone_snapshot = zones
            self._last_update_ts = time.time()

        print(
            f"[WALL] {state} cmd=({left:.2f},{right:.2f}) "
            f"actual=({actual_l:.2f},{actual_r:.2f}) "
            f"front={zones.get('front_mm')} side={zones.get('side_mm')} "
            f"error={error_mm} safety={safety_mode}",
            flush=True,
        )

    def _step(self):
        with self._lock:
            side = self._side
            target_mm = self._target_mm
            tolerance_mm = self._tolerance_mm
            front_stop_mm = self._front_stop_mm
            base_speed = abs(self._base_speed)
            turn_gain = self._turn_gain
            max_turn = abs(self._max_turn)
            search_turn = abs(self._search_turn)
            wall_lost_mm = self._wall_lost_mm
            forward_sign = self._forward_sign

        zones = self._get_zones()
        front_mm = zones.get("front_mm")
        side_mm = zones.get("side_mm")

        # Stop if obstacle is too close in front
        if front_mm is not None and front_mm <= front_stop_mm:
            self._drive_and_record(
                0.0,
                0.0,
                "front_blocked",
                "front obstacle too close; stopped",
                None,
                zones,
            )
            return

        now = time.time()

        if not hasattr(self, "_last_good_side_mm"):
            self._last_good_side_mm = None
            self._last_good_side_ts = 0.0

        if side_mm is not None and side_mm <= wall_lost_mm:
            self._last_good_side_mm = side_mm
            self._last_good_side_ts = now

        recent_good_side = (
            self._last_good_side_mm is not None
            and now - self._last_good_side_ts <= 0.75
        )

        if (side_mm is None or side_mm > wall_lost_mm) and recent_good_side:
            side_mm = self._last_good_side_mm

        if side_mm is None or side_mm > wall_lost_mm:
            turn = max(search_turn, self._min_motor_power)

            if side == "left":
                left_power = -turn
                right_power = turn
                reason = "left wall lost; rotating left only"
            else:
                left_power = turn
                right_power = -turn
                reason = "right wall lost; rotating right only"

            self._drive_and_record(
                left_power,
                right_power,
                "searching",
                reason,
                None,
                zones,
            )
            return

        # Positive error means too far from wall
        error_mm = float(side_mm) - float(target_mm)

        if abs(error_mm) <= tolerance_mm:
            left_power = base_speed
            right_power = base_speed
            reason = "wall centered"
        else:
            turn = min(abs(error_mm) * turn_gain / 1000.0, max_turn)

            if side == "left":
                if error_mm > 0:
                    # Too far from left wall -> steer left
                    left_power = base_speed - turn
                    right_power = base_speed + turn
                    reason = "left wall too far; turning left"
                else:
                    # Too close to left wall -> steer right
                    left_power = base_speed + turn
                    right_power = base_speed - turn
                    reason = "left wall too close; turning right"
            else:
                if error_mm > 0:
                    # Too far from right wall -> steer right
                    left_power = base_speed + turn
                    right_power = base_speed - turn
                    reason = "right wall too far; turning right"
                else:
                    # Too close to right wall -> steer left
                    left_power = base_speed - turn
                    right_power = base_speed + turn
                    reason = "right wall too close; turning left"

        self._drive_and_record(
            forward_sign * left_power,
            forward_sign * right_power,
            "following",
            reason,
            error_mm,
            zones,
        )