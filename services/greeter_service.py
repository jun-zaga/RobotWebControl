import enum
import threading
import time

import config as cfg


try:
    import speech_recognition as sr
except Exception as e:
    sr = None
    print("[GREETER] speech_recognition import failed:", e, flush=True)


class GreeterState(str, enum.Enum):
    STOPPED = "STOPPED"
    WAITING = "WAITING"
    GREETING = "GREETING"
    LISTENING_FOR_DESTINATION = "LISTENING_FOR_DESTINATION"

    TURNING_AROUND = "TURNING_AROUND"
    WAITING_FOR_CLEAR_FRONT = "WAITING_FOR_CLEAR_FRONT"
    ALIGNING_BODY = "ALIGNING_BODY"
    CENTERING = "CENTERING"
    ALIGNING_BODY_FINAL = "ALIGNING_BODY_FINAL"

    MOVING_TO_T_START = "MOVING_TO_T_START"
    T_START_REACHED = "T_START_REACHED"

    TURNING_LEFT_TO_BATHROOM = "TURNING_LEFT_TO_BATHROOM"
    MOVING_TO_BATHROOM = "MOVING_TO_BATHROOM"
    BATHROOM_REACHED = "BATHROOM_REACHED"

    TURNING_RIGHT_TO_ROBOT_LAB = "TURNING_RIGHT_TO_ROBOT_LAB"
    MOVING_TO_ROBOT_LAB = "MOVING_TO_ROBOT_LAB"
    ROBOT_LAB_REACHED = "ROBOT_LAB_REACHED"

    ERROR = "ERROR"


class GreeterService:
    """
    Final project greeter.

    Flow:
      WAITING
      -> human detected
      -> greet
      -> listen for bathroom / robot lab
      -> turn around
      -> center
      -> move to T start
      -> route left to bathroom OR right to robot lab
    """

    def __init__(self, robot_service, lidar_service, tts_service=None):
        self.robot = robot_service
        self.lidar = lidar_service
        self.tts = tts_service

        self._lock = threading.RLock()
        self._thread = None
        self._running = False
        self._state = GreeterState.STOPPED
        self._state_entered_at = time.time()
        self._last_error = None
        self._last_cmd = {"left": 0.0, "right": 0.0}

        self._destination = None
        self._last_heard = None

        self._centered_count = 0
        self._human_seen_count = 0
        self._body_aligned_count = 0
        self._t_start_seen_count = 0

        # -------------------------------------------------
        # LiDAR zones
        # -------------------------------------------------

        self.front_center_deg = getattr(cfg, "GREETER_FRONT_CENTER_DEG", 0.0)
        self.front_half_angle_deg = getattr(cfg, "GREETER_FRONT_HALF_ANGLE_DEG", 20.0)

        self.left_center_deg = getattr(cfg, "GREETER_LEFT_CENTER_DEG", 225.0)
        self.left_half_angle_deg = getattr(cfg, "GREETER_LEFT_HALF_ANGLE_DEG", 25.0)

        self.right_center_deg = getattr(cfg, "GREETER_RIGHT_CENTER_DEG", 45.0)
        self.right_half_angle_deg = getattr(cfg, "GREETER_RIGHT_HALF_ANGLE_DEG", 25.0)

        # -------------------------------------------------
        # Human detection
        # -------------------------------------------------

        self.human_detect_mm = getattr(cfg, "GREETER_HUMAN_DETECT_MM", 1400.0)
        self.human_min_mm = getattr(cfg, "GREETER_HUMAN_MIN_MM", 250.0)
        self.human_seen_required = getattr(cfg, "GREETER_HUMAN_SEEN_REQUIRED", 2)

        # -------------------------------------------------
        # Voice destination
        # -------------------------------------------------

        self.destination_listen_timeout_sec = getattr(
            cfg, "GREETER_DESTINATION_LISTEN_TIMEOUT_SEC", 4.0
        )
        self.destination_phrase_time_limit_sec = getattr(
            cfg, "GREETER_DESTINATION_PHRASE_TIME_LIMIT_SEC", 4.0
        )

        # -------------------------------------------------
        # Movement
        # -------------------------------------------------

        self.base_speed = -abs(getattr(cfg, "GREETER_BASE_SPEED", 0.80))
        self.turn_speed = abs(getattr(cfg, "GREETER_TURN_SPEED", 0.80))
        self.turn_180_sec = getattr(cfg, "GREETER_TURN_180_SEC", 2.40)

        # -------------------------------------------------
        # Right-wall centering
        # -------------------------------------------------

        self.left_target_mm = getattr(cfg, "GREETER_CENTER_LEFT_TARGET_MM", 700.0)
        self.right_target_mm = getattr(cfg, "GREETER_CENTER_RIGHT_TARGET_MM", 1600.0)
        self.center_tolerance_mm = getattr(cfg, "GREETER_CENTER_TOLERANCE_MM", 175.0)

        self.front_danger_mm = getattr(cfg, "GREETER_CENTER_FRONT_DANGER_MM", 500.0)
        self.side_danger_mm = getattr(cfg, "GREETER_CENTER_SIDE_DANGER_MM", 500.0)
        self.front_clear_mm = getattr(cfg, "GREETER_CENTER_FRONT_CLEAR_MM", 750.0)

        self.kp = getattr(cfg, "GREETER_CENTER_KP", 0.00020)
        self.max_steer = getattr(cfg, "GREETER_CENTER_MAX_STEER", 0.06)
        self.min_forward_power = getattr(cfg, "GREETER_CENTER_MIN_POWER", 0.70)
        self.timeout_sec = getattr(cfg, "GREETER_CENTER_TIMEOUT_SEC", 10.0)
        self.wait_clear_timeout_sec = getattr(cfg, "GREETER_WAIT_CLEAR_TIMEOUT_SEC", 4.0)

        self.steer_sign = getattr(cfg, "GREETER_CENTER_STEER_SIGN", -1.0)

        # -------------------------------------------------
        # Body alignment
        # -------------------------------------------------

        self.right_front_center_deg = getattr(cfg, "GREETER_RIGHT_FRONT_CENTER_DEG", 35.0)
        self.right_rear_center_deg = getattr(cfg, "GREETER_RIGHT_REAR_CENTER_DEG", 70.0)
        self.right_align_half_angle_deg = getattr(cfg, "GREETER_RIGHT_ALIGN_HALF_ANGLE_DEG", 10.0)

        self.body_align_tolerance_mm = getattr(cfg, "GREETER_BODY_ALIGN_TOLERANCE_MM", 250.0)
        self.body_align_required = getattr(cfg, "GREETER_BODY_ALIGN_REQUIRED", 3)
        self.body_align_turn_speed = getattr(cfg, "GREETER_BODY_ALIGN_TURN_SPEED", 0.35)
        self.body_align_timeout_sec = getattr(cfg, "GREETER_BODY_ALIGN_TIMEOUT_SEC", 4.0)
        self.body_align_sign = getattr(cfg, "GREETER_BODY_ALIGN_SIGN", -1.0)

        # -------------------------------------------------
        # Move to start of T
        # -------------------------------------------------

        self.t_start_front_mm = getattr(cfg, "GREETER_T_START_FRONT_MM", 2500.0)
        self.t_start_front_tolerance_mm = getattr(cfg, "GREETER_T_START_FRONT_TOLERANCE_MM", 350.0)

        self.t_start_left_min_mm = getattr(cfg, "GREETER_T_START_LEFT_MIN_MM", 700.0)
        self.t_start_left_max_mm = getattr(cfg, "GREETER_T_START_LEFT_MAX_MM", 1800.0)

        self.t_start_right_min_mm = getattr(cfg, "GREETER_T_START_RIGHT_MIN_MM", 900.0)
        self.t_start_right_max_mm = getattr(cfg, "GREETER_T_START_RIGHT_MAX_MM", 2200.0)

        self.t_start_seen_required = getattr(cfg, "GREETER_T_START_SEEN_REQUIRED", 3)
        self.move_to_t_timeout_sec = getattr(cfg, "GREETER_MOVE_TO_T_TIMEOUT_SEC", 14.0)
        self.move_to_t_base_speed = -abs(getattr(cfg, "GREETER_MOVE_TO_T_BASE_SPEED", 0.80))

        # -------------------------------------------------
        # Bathroom route
        # -------------------------------------------------

        self.bathroom_turn_speed = abs(getattr(cfg, "GREETER_BATHROOM_TURN_SPEED", 0.80))
        self.bathroom_left_turn_sec = getattr(cfg, "GREETER_BATHROOM_LEFT_TURN_SEC", 0.45)
        self.bathroom_turn_sign = getattr(cfg, "GREETER_BATHROOM_TURN_SIGN", -1.0)

        self.bathroom_forward_sec = getattr(cfg, "GREETER_BATHROOM_FORWARD_SEC", 5.0)
        self.bathroom_forward_speed = -abs(getattr(cfg, "GREETER_BATHROOM_FORWARD_SPEED", 0.80))

        # -------------------------------------------------
        # Robot lab route
        # -------------------------------------------------

        self.robot_lab_turn_speed = abs(getattr(cfg, "GREETER_ROBOT_LAB_TURN_SPEED", 0.80))
        self.robot_lab_right_turn_sec = getattr(cfg, "GREETER_ROBOT_LAB_RIGHT_TURN_SEC", 0.45)

        # Opposite of bathroom.
        self.robot_lab_turn_sign = getattr(cfg, "GREETER_ROBOT_LAB_TURN_SIGN", 1.0)

        self.robot_lab_forward_sec = getattr(cfg, "GREETER_ROBOT_LAB_FORWARD_SEC", 5.0)
        self.robot_lab_forward_speed = -abs(getattr(cfg, "GREETER_ROBOT_LAB_FORWARD_SPEED", 0.80))

        self.loop_hz = 10.0

    @staticmethod
    def _clamp(x, lo, hi):
        return max(lo, min(hi, x))

    def start(self):
        with self._lock:
            if self._running:
                return self.status()

            self._running = True
            self._state = GreeterState.WAITING
            self._state_entered_at = time.time()
            self._last_error = None
            self._last_cmd = {"left": 0.0, "right": 0.0}

            self._destination = None
            self._last_heard = None

            self._centered_count = 0
            self._human_seen_count = 0
            self._body_aligned_count = 0
            self._t_start_seen_count = 0

            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

        print("[GREETER] started, waiting for human", flush=True)
        return self.status()

    def stop(self, reason="manual stop"):
        self.robot.stop()

        with self._lock:
            self._running = False
            self._state = GreeterState.STOPPED
            self._last_error = reason
            self._last_cmd = {"left": 0.0, "right": 0.0}

        print(f"[GREETER] stopped: {reason}", flush=True)
        return self.status()

    def status(self):
        z = self._zones_safe()
        align = self._right_wall_alignment_safe()

        with self._lock:
            return {
                "ok": True,
                "running": self._running,
                "state": self._state.value,
                "state_age_sec": round(time.time() - self._state_entered_at, 2),
                "last_error": self._last_error,
                "last_cmd": self._last_cmd,
                "destination": self._destination,
                "last_heard": self._last_heard,
                "zones": z,
                "human_debug": {
                    "human_detect_mm": self.human_detect_mm,
                    "human_min_mm": self.human_min_mm,
                    "human_seen_count": self._human_seen_count,
                    "human_seen_required": self.human_seen_required,
                },
                "turn_debug": {
                    "turn_speed": self.turn_speed,
                    "turn_180_sec": self.turn_180_sec,
                },
                "center_debug": self._center_debug(z),
                "body_align_debug": {
                    "front_right": align["front_right"],
                    "rear_right": align["rear_right"],
                    "error": align["error"],
                    "aligned_count": self._body_aligned_count,
                    "required": self.body_align_required,
                    "tolerance_mm": self.body_align_tolerance_mm,
                    "body_align_sign": self.body_align_sign,
                },
                "t_start_debug": self._t_start_debug(z),
                "bathroom_debug": {
                    "turn_speed": self.bathroom_turn_speed,
                    "left_turn_sec": self.bathroom_left_turn_sec,
                    "turn_sign": self.bathroom_turn_sign,
                    "forward_sec": self.bathroom_forward_sec,
                    "forward_speed": self.bathroom_forward_speed,
                },
                "robot_lab_debug": {
                    "turn_speed": self.robot_lab_turn_speed,
                    "right_turn_sec": self.robot_lab_right_turn_sec,
                    "turn_sign": self.robot_lab_turn_sign,
                    "forward_sec": self.robot_lab_forward_sec,
                    "forward_speed": self.robot_lab_forward_speed,
                },
                "speech_enabled": sr is not None,
                "note": "HUMAN_DETECT + DESTINATION + CENTER + MOVE_TO_T + BATHROOM_OR_ROBOT_LAB",
            }

    def set_test_destination(self, destination_text):
        """
        UI test buttons call this.

        Accepted:
          - bathroom
          - robot lab
          - lab
        """
        dest = self._normalize_destination(destination_text)

        with self._lock:
            self._destination = dest
            self._last_heard = str(destination_text)

            if self._running and self._state == GreeterState.LISTENING_FOR_DESTINATION:
                self._state = GreeterState.TURNING_AROUND
                self._state_entered_at = time.time()

        print(f"[GREETER] destination set from UI: {destination_text} -> {dest}", flush=True)
        return self.status()

    def _normalize_destination(self, text):
        s = (text or "").strip().lower()

        if "bath" in s:
            return "bathroom"

        if "robot" in s or "lab" in s:
            return "robot_lab"

        return None

    def _set_state(self, state):
        with self._lock:
            self._state = state
            self._state_entered_at = time.time()

            if state in (GreeterState.ALIGNING_BODY, GreeterState.ALIGNING_BODY_FINAL):
                self._body_aligned_count = 0

            if state == GreeterState.CENTERING:
                self._centered_count = 0

            if state == GreeterState.MOVING_TO_T_START:
                self._t_start_seen_count = 0

        print(f"[GREETER] -> {state.value}", flush=True)

    def _say(self, text, wait_sec=1.0):
        print(f"[GREETER SAY] {text}", flush=True)

        if self.tts is not None:
            try:
                self.tts.say(text)
            except Exception as e:
                print("[GREETER TTS ERROR]", repr(e), flush=True)

        time.sleep(wait_sec)

    def _listen_for_destination(self):
        """
        Earlier-style forgiving voice detection:
        - keeps listening for bathroom / robot lab
        - does not kill the greeter on one bad recognition
        - updates last_heard so the UI shows what happened
        """
        if sr is None:
            print("[GREETER LISTEN] speech recognition unavailable", flush=True)

            with self._lock:
                self._last_heard = "speech_recognition unavailable"

            return None

        try:
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = getattr(cfg, "GREETER_VOICE_ENERGY_THRESHOLD", 300)
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = getattr(cfg, "GREETER_VOICE_PAUSE_THRESHOLD", 0.8)

            with sr.Microphone() as source:
                print("[GREETER LISTEN] calibrating mic...", flush=True)
                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=getattr(cfg, "GREETER_VOICE_AMBIENT_SEC", 0.35),
                )

                print("[GREETER LISTEN] say: bathroom or robot lab", flush=True)
                audio = recognizer.listen(
                    source,
                    timeout=getattr(cfg, "GREETER_VOICE_TIMEOUT_SEC", 6.0),
                    phrase_time_limit=getattr(cfg, "GREETER_VOICE_PHRASE_LIMIT_SEC", 5.0),
                )

            heard = recognizer.recognize_google(audio)
            heard_clean = heard.strip().lower()
            dest = self._normalize_destination(heard_clean)

            with self._lock:
                self._last_heard = heard
                if dest is not None:
                    self._destination = dest

            print(f"[GREETER LISTEN] heard={heard!r} dest={dest}", flush=True)
            return dest

        except sr.WaitTimeoutError:
            with self._lock:
                self._last_heard = "LISTEN_TIMEOUT"

            print("[GREETER LISTEN] timeout waiting for speech", flush=True)
            return None

        except sr.UnknownValueError:
            with self._lock:
                self._last_heard = "UNKNOWN_SPEECH"

            print("[GREETER LISTEN] heard audio but could not understand", flush=True)
            return None

        except Exception as e:
            with self._lock:
                self._last_heard = f"LISTEN_ERROR: {repr(e)}"

            print("[GREETER LISTEN ERROR]", repr(e), flush=True)
            return None

    def _zone_min(self, center_deg, half_angle):
        try:
            return self.lidar.get_zone_min(float(center_deg), float(half_angle))
        except Exception as e:
            print("[GREETER LIDAR ERROR]", repr(e), flush=True)
            return None

    def _zones(self):
        return {
            "front_mm": self._zone_min(self.front_center_deg, self.front_half_angle_deg),
            "left_mm": self._zone_min(self.left_center_deg, self.left_half_angle_deg),
            "right_mm": self._zone_min(self.right_center_deg, self.right_half_angle_deg),
        }

    def _zones_safe(self):
        try:
            return self._zones()
        except Exception:
            return {
                "front_mm": None,
                "left_mm": None,
                "right_mm": None,
            }

    def _human_detected(self):
        z = self._zones()
        front = z["front_mm"]

        seen = (
            front is not None
            and self.human_min_mm <= front <= self.human_detect_mm
        )

        if seen:
            self._human_seen_count += 1
        else:
            self._human_seen_count = 0

        print(
            f"[GREETER HUMAN] front={front} "
            f"seen={seen} count={self._human_seen_count}/{self.human_seen_required}",
            flush=True,
        )

        return self._human_seen_count >= self.human_seen_required

    def _front_clear_for_centering(self):
        z = self._zones()
        front = z["front_mm"]

        clear = front is None or front >= self.front_clear_mm

        print(
            f"[GREETER CLEAR CHECK] front={front} clear={clear}",
            flush=True,
        )

        return clear

    def _center_debug(self, z):
        left = z.get("left_mm")
        right = z.get("right_mm")

        left_error = None if left is None else left - self.left_target_mm
        right_error = None if right is None else right - self.right_target_mm

        if left_error is not None and right_error is not None:
            balance_error = right_error - left_error
        else:
            balance_error = None

        return {
            "left_target_mm": self.left_target_mm,
            "right_target_mm": self.right_target_mm,
            "left_error": left_error,
            "right_error": right_error,
            "balance_error": balance_error,
            "centered_count": self._centered_count,
            "steer_sign": self.steer_sign,
        }

    def _t_start_debug(self, z):
        front = z.get("front_mm")
        left = z.get("left_mm")
        right = z.get("right_mm")

        front_ok = (
            front is not None
            and abs(front - self.t_start_front_mm) <= self.t_start_front_tolerance_mm
        )

        left_ok = (
            left is not None
            and self.t_start_left_min_mm <= left <= self.t_start_left_max_mm
        )

        right_ok = (
            right is not None
            and self.t_start_right_min_mm <= right <= self.t_start_right_max_mm
        )

        return {
            "target_front_mm": self.t_start_front_mm,
            "front_tolerance_mm": self.t_start_front_tolerance_mm,
            "front_ok": front_ok,
            "left_wall_ok": left_ok,
            "right_wall_ok": right_ok,
            "seen_count": self._t_start_seen_count,
            "seen_required": self.t_start_seen_required,
        }

    def _danger_stop_needed(self):
        z = self._zones()

        front = z["front_mm"]
        left = z["left_mm"]
        right = z["right_mm"]

        front_danger = front is not None and front <= self.front_danger_mm
        left_danger = left is not None and left <= self.side_danger_mm
        right_danger = right is not None and right <= self.side_danger_mm

        if front_danger or left_danger or right_danger:
            print(
                f"[GREETER DANGER] front={front} left={left} right={right}",
                flush=True,
            )
            return True

        return False

    def _is_centered(self):
        z = self._zones()

        front = z["front_mm"]
        left = z["left_mm"]
        right = z["right_mm"]

        front_safe = front is None or front > self.front_danger_mm
        left_safe = left is None or left > self.side_danger_mm
        right_safe = right is not None and right > self.side_danger_mm

        right_ok = (
            right is not None
            and abs(right - self.right_target_mm) <= self.center_tolerance_mm
        )

        print(
            f"[GREETER RIGHT CHECK] front={front} left={left} right={right} "
            f"front_safe={front_safe} left_safe={left_safe} "
            f"right_safe={right_safe} right_ok={right_ok}",
            flush=True,
        )

        return front_safe and left_safe and right_safe and right_ok

    def _t_start_seen(self):
        z = self._zones()

        front = z["front_mm"]
        left = z["left_mm"]
        right = z["right_mm"]

        front_ok = (
            front is not None
            and abs(front - self.t_start_front_mm) <= self.t_start_front_tolerance_mm
        )

        left_wall_ok = (
            left is not None
            and self.t_start_left_min_mm <= left <= self.t_start_left_max_mm
        )

        right_wall_ok = (
            right is not None
            and self.t_start_right_min_mm <= right <= self.t_start_right_max_mm
        )

        # Important:
        # For the robot lab path, the left side can open up at the T.
        # So do NOT require left_wall_ok anymore.
        seen = front_ok and right_wall_ok

        if seen:
            self._t_start_seen_count += 1
        else:
            self._t_start_seen_count = 0

        print(
            f"[GREETER T START] front={front} left={left} right={right} "
            f"front_ok={front_ok} left_wall_ok={left_wall_ok} right_wall_ok={right_wall_ok} "
            f"seen={seen} count={self._t_start_seen_count}/{self.t_start_seen_required}",
            flush=True,
        )

        return self._t_start_seen_count >= self.t_start_seen_required

    def _right_wall_alignment_safe(self):
        try:
            return self._right_wall_alignment()
        except Exception:
            return {
                "ok": False,
                "front_right": None,
                "rear_right": None,
                "error": None,
            }

    def _right_wall_alignment(self):
        front_right = self._zone_min(
            self.right_front_center_deg,
            self.right_align_half_angle_deg,
        )

        rear_right = self._zone_min(
            self.right_rear_center_deg,
            self.right_align_half_angle_deg,
        )

        if front_right is None or rear_right is None:
            return {
                "ok": False,
                "front_right": front_right,
                "rear_right": rear_right,
                "error": None,
            }

        error = front_right - rear_right

        return {
            "ok": True,
            "front_right": front_right,
            "rear_right": rear_right,
            "error": error,
        }

    def _align_body_to_right_wall(self):
        data = self._right_wall_alignment()

        print(
            f"[GREETER ALIGN BODY] "
            f"front_right={data['front_right']} "
            f"rear_right={data['rear_right']} "
            f"error={data['error']} "
            f"count={self._body_aligned_count}/{self.body_align_required}",
            flush=True,
        )

        if not data["ok"]:
            self.robot.stop()

            with self._lock:
                self._last_cmd = {"left": 0.0, "right": 0.0}

            self._body_aligned_count = 0
            return False

        error = data["error"]

        if abs(error) <= self.body_align_tolerance_mm:
            self.robot.stop()

            with self._lock:
                self._last_cmd = {"left": 0.0, "right": 0.0}

            self._body_aligned_count += 1
            return self._body_aligned_count >= self.body_align_required

        self._body_aligned_count = 0

        turn_speed = self.body_align_turn_speed

        if error > 0:
            left_cmd = self.body_align_sign * turn_speed
            right_cmd = self.body_align_sign * -turn_speed
        else:
            left_cmd = self.body_align_sign * -turn_speed
            right_cmd = self.body_align_sign * turn_speed

        with self._lock:
            self._last_cmd = {
                "left": left_cmd,
                "right": right_cmd,
            }

        self.robot.drive(left_cmd, right_cmd)
        return False

    def _compute_right_wall_command(self, base_speed=None):
        z = self._zones()

        right = z["right_mm"]

        if right is None:
            print("[GREETER] no right wall reading; stopping", flush=True)
            return 0.0, 0.0

        if base_speed is None:
            base_speed = self.base_speed

        error = right - self.right_target_mm

        steer = self.steer_sign * self._clamp(
            error * self.kp,
            -self.max_steer,
            self.max_steer,
        )

        left_cmd = base_speed + steer
        right_cmd = base_speed - steer

        left_cmd = self._clamp(left_cmd, -1.0, -self.min_forward_power)
        right_cmd = self._clamp(right_cmd, -1.0, -self.min_forward_power)

        print(
            f"[GREETER RIGHT-WALL] front={z['front_mm']} "
            f"left_mm={z['left_mm']} right_mm={right} "
            f"target={self.right_target_mm} error={error} "
            f"steer={steer:.3f} "
            f"cmd_left={left_cmd:.2f} cmd_right={right_cmd:.2f}",
            flush=True,
        )

        return left_cmd, right_cmd

    def _drive_right_wall(self, base_speed=None):
        left_cmd, right_cmd = self._compute_right_wall_command(base_speed=base_speed)

        with self._lock:
            self._last_cmd = {
                "left": left_cmd,
                "right": right_cmd,
            }

        self.robot.drive(left_cmd, right_cmd)

    def _turn_around_180(self):
        print(
            f"[GREETER TURN] fixed 180 speed={self.turn_speed:.2f} "
            f"sec={self.turn_180_sec:.2f}",
            flush=True,
        )

        end = time.time() + float(self.turn_180_sec)

        while self._is_running() and time.time() < end:
            self.robot.drive(self.turn_speed, -self.turn_speed)

            with self._lock:
                self._last_cmd = {
                    "left": self.turn_speed,
                    "right": -self.turn_speed,
                }

            time.sleep(0.08)

        self.robot.stop()

        with self._lock:
            self._last_cmd = {"left": 0.0, "right": 0.0}

        time.sleep(0.30)

    def _turn_left_to_bathroom(self):
        print(
            f"[GREETER BATHROOM TURN] speed={self.bathroom_turn_speed:.2f} "
            f"sec={self.bathroom_left_turn_sec:.2f} sign={self.bathroom_turn_sign}",
            flush=True,
        )

        left_cmd = self.bathroom_turn_sign * -self.bathroom_turn_speed
        right_cmd = self.bathroom_turn_sign * self.bathroom_turn_speed

        self._timed_drive(left_cmd, right_cmd, self.bathroom_left_turn_sec)

    def _turn_right_to_robot_lab(self):
        print(
            f"[GREETER ROBOT LAB TURN] speed={self.robot_lab_turn_speed:.2f} "
            f"sec={self.robot_lab_right_turn_sec:.2f} sign={self.robot_lab_turn_sign}",
            flush=True,
        )

        left_cmd = self.robot_lab_turn_sign * self.robot_lab_turn_speed
        right_cmd = self.robot_lab_turn_sign * -self.robot_lab_turn_speed

        self._timed_drive(left_cmd, right_cmd, self.robot_lab_right_turn_sec)

    def _timed_drive(self, left_cmd, right_cmd, seconds):
        end = time.time() + float(seconds)

        while self._is_running() and time.time() < end:
            self.robot.drive(left_cmd, right_cmd)

            with self._lock:
                self._last_cmd = {
                    "left": left_cmd,
                    "right": right_cmd,
                }

            time.sleep(0.08)

        self.robot.stop()

        with self._lock:
            self._last_cmd = {"left": 0.0, "right": 0.0}

        time.sleep(0.25)

    def _move_forward_timed(self, seconds, speed, error_reason):
        print(
            f"[GREETER FORWARD] speed={speed:.2f} sec={seconds:.2f}",
            flush=True,
        )

        end = time.time() + float(seconds)

        while self._is_running() and time.time() < end:
            if self._danger_stop_needed():
                self._set_state(GreeterState.STOPPED)
                self._stop_running(error_reason)
                return False

            self.robot.drive(speed, speed)

            with self._lock:
                self._last_cmd = {
                    "left": speed,
                    "right": speed,
                }

            time.sleep(0.08)

        self.robot.stop()

        with self._lock:
            self._last_cmd = {"left": 0.0, "right": 0.0}

        return True

    def _is_running(self):
        with self._lock:
            return self._running

    def _stop_running(self, error=None):
        self.robot.stop()

        with self._lock:
            self._running = False
            self._last_error = error
            self._last_cmd = {"left": 0.0, "right": 0.0}

    def _finish_success(self, state):
        self.robot.stop()
        self._set_state(state)

        with self._lock:
            self._running = False
            self._last_error = None
            self._last_cmd = {"left": 0.0, "right": 0.0}

    def _run(self):
        try:
            center_start = None
            clear_wait_start = None
            align_start = None
            final_align_start = None
            move_to_t_start = None

            time.sleep(0.4)

            while self._is_running():
                with self._lock:
                    state = self._state
                    destination = self._destination

                if state == GreeterState.WAITING:
                    self.robot.stop()

                    with self._lock:
                        self._last_cmd = {"left": 0.0, "right": 0.0}

                    if self._human_detected():
                        self._set_state(GreeterState.GREETING)

                elif state == GreeterState.GREETING:
                    self.robot.stop()
                    self._say(
                        "Hello. Where would you like to go? Say bathroom or robot lab.",
                        wait_sec=1.2,
                    )
                    self._set_state(GreeterState.LISTENING_FOR_DESTINATION)

                elif state == GreeterState.LISTENING_FOR_DESTINATION:
                    listen_start = time.time()
                    destination = None

                    while self._is_running():
                        with self._lock:
                            destination = self._destination

                        if destination in ("bathroom", "robot_lab"):
                            break

                        if time.time() - listen_start >= getattr(cfg, "GREETER_DESTINATION_TOTAL_LISTEN_SEC", 20.0):
                            self._say("I did not hear bathroom or robot lab. Please use the button.", wait_sec=0.8)

                            with self._lock:
                                self._last_error = "destination listen timeout"

                            print("[GREETER LISTEN] total destination listen timeout", flush=True)
                            time.sleep(0.2)
                            continue

                        self._say("Please say bathroom or robot lab.", wait_sec=0.6)
                        destination = self._listen_for_destination()

                        if destination in ("bathroom", "robot_lab"):
                            break

                        time.sleep(0.3)

                    if destination in ("bathroom", "robot_lab"):
                        self._say("Okay. Follow me.", wait_sec=0.7)
                        self._set_state(GreeterState.TURNING_AROUND)

                elif state == GreeterState.TURNING_AROUND:
                    self._turn_around_180()
                    clear_wait_start = time.time()
                    self._set_state(GreeterState.WAITING_FOR_CLEAR_FRONT)

                elif state == GreeterState.WAITING_FOR_CLEAR_FRONT:
                    self.robot.stop()

                    if clear_wait_start is None:
                        clear_wait_start = time.time()

                    if self._front_clear_for_centering():
                        align_start = time.time()
                        self._set_state(GreeterState.ALIGNING_BODY)

                    elif time.time() - clear_wait_start >= self.wait_clear_timeout_sec:
                        print("[GREETER] front did not clear; stopping", flush=True)
                        self._set_state(GreeterState.STOPPED)
                        self._stop_running("front did not clear")
                        break

                elif state == GreeterState.ALIGNING_BODY:
                    if align_start is None:
                        align_start = time.time()

                    if time.time() - align_start >= self.body_align_timeout_sec:
                        print("[GREETER] body align timeout; moving to centering", flush=True)
                        center_start = time.time()
                        self._set_state(GreeterState.CENTERING)

                    elif self._danger_stop_needed():
                        self._set_state(GreeterState.STOPPED)
                        self._stop_running("danger stop while aligning body")
                        break

                    elif self._align_body_to_right_wall():
                        center_start = time.time()
                        self._set_state(GreeterState.CENTERING)

                elif state == GreeterState.CENTERING:
                    if center_start is None:
                        center_start = time.time()

                    age = time.time() - center_start

                    if age >= self.timeout_sec:
                        print("[GREETER] center timeout; going to final body alignment", flush=True)
                        final_align_start = time.time()
                        self._set_state(GreeterState.ALIGNING_BODY_FINAL)

                    elif self._danger_stop_needed():
                        self._set_state(GreeterState.STOPPED)
                        self._stop_running("danger stop while centering")
                        break

                    else:
                        if self._is_centered():
                            self._centered_count += 1
                        else:
                            self._centered_count = 0

                        if self._centered_count >= 5:
                            self.robot.stop()
                            final_align_start = time.time()
                            self._set_state(GreeterState.ALIGNING_BODY_FINAL)
                        else:
                            self._drive_right_wall(base_speed=self.base_speed)

                elif state == GreeterState.ALIGNING_BODY_FINAL:
                    if final_align_start is None:
                        final_align_start = time.time()

                    if time.time() - final_align_start >= self.body_align_timeout_sec:
                        print("[GREETER] final body align timeout; moving to T start", flush=True)
                        move_to_t_start = time.time()
                        self._set_state(GreeterState.MOVING_TO_T_START)

                    elif self._danger_stop_needed():
                        self._set_state(GreeterState.STOPPED)
                        self._stop_running("danger stop during final body alignment")
                        break

                    elif self._align_body_to_right_wall():
                        self.robot.stop()
                        move_to_t_start = time.time()
                        self._set_state(GreeterState.MOVING_TO_T_START)

                elif state == GreeterState.MOVING_TO_T_START:
                    if move_to_t_start is None:
                        move_to_t_start = time.time()

                    age = time.time() - move_to_t_start

                    if age >= self.move_to_t_timeout_sec:
                        print("[GREETER] move to T timeout; stopping", flush=True)
                        self._set_state(GreeterState.STOPPED)
                        self._stop_running("move to T timeout")
                        break

                    if self._danger_stop_needed():
                        self._set_state(GreeterState.STOPPED)
                        self._stop_running("danger stop while moving to T")
                        break

                    if self._t_start_seen():
                        print("[GREETER] T start reached", flush=True)
                        self.robot.stop()

                        with self._lock:
                            destination = self._destination

                        if destination == "robot_lab":
                            self._set_state(GreeterState.TURNING_RIGHT_TO_ROBOT_LAB)
                        else:
                            self._set_state(GreeterState.TURNING_LEFT_TO_BATHROOM)
                    else:
                        self._drive_right_wall(base_speed=self.move_to_t_base_speed)

                elif state == GreeterState.TURNING_LEFT_TO_BATHROOM:
                    self._turn_left_to_bathroom()
                    self._set_state(GreeterState.MOVING_TO_BATHROOM)

                elif state == GreeterState.MOVING_TO_BATHROOM:
                    ok = self._move_forward_timed(
                        self.bathroom_forward_sec,
                        self.bathroom_forward_speed,
                        "danger stop while moving to bathroom",
                    )

                    if ok:
                        print("[GREETER] bathroom reached", flush=True)
                        self._say("We have arrived at the bathroom.", wait_sec=1.0)
                        self._finish_success(GreeterState.BATHROOM_REACHED)

                    break

                elif state == GreeterState.TURNING_RIGHT_TO_ROBOT_LAB:
                    self._turn_right_to_robot_lab()
                    self._set_state(GreeterState.MOVING_TO_ROBOT_LAB)

                elif state == GreeterState.MOVING_TO_ROBOT_LAB:
                    ok = self._move_forward_timed(
                        self.robot_lab_forward_sec,
                        self.robot_lab_forward_speed,
                        "danger stop while moving to robot lab",
                    )

                    if ok:
                        print("[GREETER] robot lab reached", flush=True)
                        self._say("We have arrived at the robot lab.", wait_sec=1.0)
                        self._finish_success(GreeterState.ROBOT_LAB_REACHED)

                    break

                elif state in (
                    GreeterState.T_START_REACHED,
                    GreeterState.BATHROOM_REACHED,
                    GreeterState.ROBOT_LAB_REACHED,
                    GreeterState.STOPPED,
                ):
                    self._stop_running(self._last_error)
                    break

                time.sleep(1.0 / self.loop_hz)

        except Exception as e:
            self.robot.stop()

            with self._lock:
                self._running = False
                self._state = GreeterState.ERROR
                self._last_error = repr(e)
                self._last_cmd = {"left": 0.0, "right": 0.0}

            print("[GREETER ERROR]", repr(e), flush=True)