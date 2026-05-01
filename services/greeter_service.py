import enum
import threading
import time

from config import (
    GREETER_HUMAN_DETECT_MM,
    GREETER_FRONT_OBSTACLE_MM,
    GREETER_WALL_VISIBLE_MM,
    GREETER_OPENING_MM,
    GREETER_FINAL_FORWARD_SEC,
    GREETER_BASE_SPEED,
    GREETER_TURN_SPEED,
    GREETER_WALL_FOLLOW_KP,
    GREETER_TARGET_SIDE_MM,
    GREETER_FRONT_CENTER_DEG,
    GREETER_FRONT_HALF_ANGLE_DEG,
    GREETER_LEFT_CENTER_DEG,
    GREETER_LEFT_HALF_ANGLE_DEG,
    GREETER_RIGHT_CENTER_DEG,
    GREETER_RIGHT_HALF_ANGLE_DEG,
    WALL_FOLLOW_FORWARD_SIGN,
    GREETER_TURN_TIMEOUT_SEC,
    GREETER_TURN_MIN_SEC,
    GREETER_TURN_FRONT_OPEN_MM,
    GREETER_TURN_SIDE_WALL_MM,
    GREETER_TURN_45_SEC,
    GREETER_T_FAR_MM,
    GREETER_T_FAR_TOLERANCE_MM,
    GREETER_T_LEFT_MIN_MM,
    GREETER_T_LEFT_MAX_MM,
    GREETER_T_RIGHT_MIN_MM,
    GREETER_T_RIGHT_MAX_MM,
    GREETER_T_FAR_SEEN_REQUIRED,
)

try:
    import speech_recognition as sr
except Exception as e:
    sr = None
    print("[GREETER] speech_recognition import failed:", e, flush=True)


class GreeterState(str, enum.Enum):
    WAITING = "WAITING"
    GREETING = "GREETING"
    LISTENING = "LISTENING"
    TURNING_AROUND = "TURNING_AROUND"
    ALIGNING_TO_HALLWAY = "ALIGNING_TO_HALLWAY"
    MOVING_TO_T = "MOVING_TO_T"
    TURNING_TO_DESTINATION = "TURNING_TO_DESTINATION"
    FINAL_MOVEMENT = "FINAL_MOVEMENT"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class Destination(str, enum.Enum):
    BATHROOM = "bathroom"
    ROBOT_LAB = "robot lab"


class GreeterService:
    FRONT_CENTER_DEG = GREETER_FRONT_CENTER_DEG
    LEFT_CENTER_DEG = GREETER_LEFT_CENTER_DEG
    RIGHT_CENTER_DEG = GREETER_RIGHT_CENTER_DEG

    FRONT_HALF_ANGLE_DEG = GREETER_FRONT_HALF_ANGLE_DEG
    LEFT_HALF_ANGLE_DEG = GREETER_LEFT_HALF_ANGLE_DEG
    RIGHT_HALF_ANGLE_DEG = GREETER_RIGHT_HALF_ANGLE_DEG

    def __init__(self, robot_service, lidar_service, tts_service):
        self.robot = robot_service
        self.lidar = lidar_service
        self.tts = tts_service

        self._lock = threading.RLock()
        self._thread = None
        self._running = False
        self._state = GreeterState.STOPPED
        self._destination = None
        self._last_error = None
        self._last_heard = ""
        self._state_entered_at = time.time()

        self.human_detect_mm = GREETER_HUMAN_DETECT_MM
        self.front_obstacle_mm = GREETER_FRONT_OBSTACLE_MM
        self.wall_visible_mm = GREETER_WALL_VISIBLE_MM
        self.opening_mm = GREETER_OPENING_MM

        self.center_target_mm = GREETER_TARGET_SIDE_MM
        self.wall_follow_base_speed = GREETER_BASE_SPEED * WALL_FOLLOW_FORWARD_SIGN
        self.wall_follow_kp = GREETER_WALL_FOLLOW_KP

        self.turn_speed = GREETER_TURN_SPEED
        self.turn_timeout_sec = GREETER_TURN_TIMEOUT_SEC
        self.turn_min_sec = GREETER_TURN_MIN_SEC
        self.turn_front_open_mm = GREETER_TURN_FRONT_OPEN_MM
        self.turn_side_wall_mm = GREETER_TURN_SIDE_WALL_MM
        self.turn_45_sec = GREETER_TURN_45_SEC

        self.final_move_sec = GREETER_FINAL_FORWARD_SEC

        self.t_far_mm = GREETER_T_FAR_MM
        self.t_far_tolerance_mm = GREETER_T_FAR_TOLERANCE_MM
        self.t_left_min_mm = GREETER_T_LEFT_MIN_MM
        self.t_left_max_mm = GREETER_T_LEFT_MAX_MM
        self.t_right_min_mm = GREETER_T_RIGHT_MIN_MM
        self.t_right_max_mm = GREETER_T_RIGHT_MAX_MM
        self.t_far_seen_required = GREETER_T_FAR_SEEN_REQUIRED
        self.t_far_seen_count = 0

        # Keep small because Stuart drives at 0.80.
        self.max_steer = 0.06

        self.align_timeout_sec = 5.0
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
            self._destination = None
            self._last_error = None
            self._last_heard = ""
            self.t_far_seen_count = 0
            self._state_entered_at = time.time()

            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

        print("[GREETER] started", flush=True)
        return self.status()

    def stop(self, reason="manual stop"):
        with self._lock:
            self._running = False
            self._state = GreeterState.STOPPED
            self._last_error = reason

        print(f"[GREETER] stopped: {reason}", flush=True)
        self.robot.stop()
        return self.status()

    def status(self):
        with self._lock:
            return {
                "ok": True,
                "running": self._running,
                "state": self._state.value,
                "destination": self._destination.value if self._destination else None,
                "last_error": self._last_error,
                "last_heard": self._last_heard,
                "state_age_sec": round(time.time() - self._state_entered_at, 2),
                "zones": self._zones_safe(),
                "speech_enabled": sr is not None,
                "angles": {
                    "front_deg": self.FRONT_CENTER_DEG,
                    "left_deg": self.LEFT_CENTER_DEG,
                    "right_deg": self.RIGHT_CENTER_DEG,
                },
                "t_seen_count": self.t_far_seen_count,
                "drive_tuning": {
                    "base_speed": self.wall_follow_base_speed,
                    "turn_speed": self.turn_speed,
                    "max_steer": self.max_steer,
                    "turn_45_sec": self.turn_45_sec,
                    "final_move_sec": self.final_move_sec,
                },
            }

    def set_test_destination(self, destination_text):
        text = str(destination_text or "").lower().strip()

        if "bath" in text or "restroom" in text:
            dest = Destination.BATHROOM
        elif "robot" in text or "lab" in text:
            dest = Destination.ROBOT_LAB
        else:
            return {"ok": False, "error": "destination must be bathroom or robot lab"}

        with self._lock:
            self._destination = dest
            self._last_heard = text

            if self._state in (
                GreeterState.WAITING,
                GreeterState.GREETING,
                GreeterState.LISTENING,
            ):
                self._state = GreeterState.TURNING_AROUND
                self._state_entered_at = time.time()

        return self.status()

    def _set_state(self, state):
        with self._lock:
            self._state = state
            self._state_entered_at = time.time()

            if state == GreeterState.MOVING_TO_T:
                self.t_far_seen_count = 0

        print(f"[GREETER] -> {state.value}", flush=True)

    def _say(self, text, wait_sec=1.0):
        print(f"[GREETER SAY] {text}", flush=True)

        try:
            self.tts.say(text)
        except Exception as e:
            print("[GREETER TTS ERROR]", repr(e), flush=True)

        time.sleep(wait_sec)

    def _zone_min(self, center_deg, half_angle):
        try:
            return self.lidar.get_zone_min(float(center_deg), float(half_angle))
        except Exception as e:
            print("[GREETER LIDAR ERROR]", repr(e), flush=True)
            return None

    def _zones(self):
        return {
            "front_mm": self._zone_min(self.FRONT_CENTER_DEG, self.FRONT_HALF_ANGLE_DEG),
            "left_mm": self._zone_min(self.LEFT_CENTER_DEG, self.LEFT_HALF_ANGLE_DEG),
            "right_mm": self._zone_min(self.RIGHT_CENTER_DEG, self.RIGHT_HALF_ANGLE_DEG),
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
        front = self._zones()["front_mm"]
        return front is not None and 400.0 <= front <= self.human_detect_mm

    def _front_obstacle(self):
        front = self._zones()["front_mm"]
        return front is not None and front <= self.front_obstacle_mm

    def _walls_on_both_sides(self):
        z = self._zones()

        left_ok = z["left_mm"] is not None and z["left_mm"] <= self.wall_visible_mm
        right_ok = z["right_mm"] is not None and z["right_mm"] <= self.wall_visible_mm

        return left_ok and right_ok

    def _far_t_intersection_seen(self):
        z = self._zones()

        front = z["front_mm"]
        left = z["left_mm"]
        right = z["right_mm"]

        front_ok = (
            front is not None
            and abs(front - self.t_far_mm) <= self.t_far_tolerance_mm
        )

        left_ok = (
            left is not None
            and self.t_left_min_mm <= left <= self.t_left_max_mm
        )

        right_ok = (
            right is not None
            and self.t_right_min_mm <= right <= self.t_right_max_mm
        )

        looks_like_t = front_ok and left_ok and right_ok

        if looks_like_t:
            self.t_far_seen_count += 1
        else:
            self.t_far_seen_count = 0

        print(
            f"[GREETER FAR T] count={self.t_far_seen_count}/{self.t_far_seen_required} "
            f"front={front} left={left} right={right} "
            f"front_ok={front_ok} left_ok={left_ok} right_ok={right_ok}",
            flush=True,
        )

        return self.t_far_seen_count >= self.t_far_seen_required

    def _close_t_intersection_seen(self):
        z = self._zones()

        front_wall = z["front_mm"] is not None and z["front_mm"] <= 700.0
        left_open = z["left_mm"] is None or z["left_mm"] >= self.opening_mm
        right_open = z["right_mm"] is None or z["right_mm"] >= self.opening_mm

        return front_wall and left_open and right_open

    def _listen_for_destination(self, timeout=6, phrase_time_limit=5):
        if sr is None:
            raise RuntimeError(
                "speech_recognition is not installed. Run: pip install SpeechRecognition PyAudio"
            )

        recognizer = sr.Recognizer()

        try:
            with sr.Microphone() as source:
                print("[GREETER] listening...", flush=True)
                recognizer.adjust_for_ambient_noise(source, duration=0.6)
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            text = recognizer.recognize_google(audio).lower().strip()

        except sr.WaitTimeoutError:
            print("[GREETER] listen timeout", flush=True)
            return None

        except sr.UnknownValueError:
            print("[GREETER] speech not understood", flush=True)
            return None

        with self._lock:
            self._last_heard = text

        print(f"[GREETER HEARD] {text}", flush=True)

        if "bath" in text or "restroom" in text:
            return Destination.BATHROOM

        if "robot" in text or "lab" in text:
            return Destination.ROBOT_LAB

        return None

    def _turn_in_place_until(self, left_cmd, right_cmd, done_fn, label):
        start = time.time()

        while self._is_running():
            age = time.time() - start
            z = self._zones()

            print(
                f"[GREETER TURN] {label} age={age:.2f} "
                f"front={z['front_mm']} left={z['left_mm']} right={z['right_mm']}",
                flush=True,
            )

            if age >= self.turn_min_sec and done_fn(z):
                print(f"[GREETER TURN] {label} done by sensor", flush=True)
                break

            if age >= self.turn_timeout_sec:
                print(f"[GREETER TURN] {label} timeout fallback", flush=True)
                break

            self.robot.drive(left_cmd, right_cmd)
            time.sleep(0.08)

        self.robot.stop()
        time.sleep(0.20)

    def _turn_in_place_for(self, left_cmd, right_cmd, seconds, label):
        print(f"[GREETER TURN] {label} for {seconds:.2f}s", flush=True)

        end = time.time() + float(seconds)

        while self._is_running() and time.time() < end:
            self.robot.drive(left_cmd, right_cmd)
            time.sleep(0.08)

        self.robot.stop()
        time.sleep(0.20)

    def _turn_around(self):
        def done(z):
            front_open = z["front_mm"] is None or z["front_mm"] >= self.turn_front_open_mm

            side_wall_visible = (
                (z["left_mm"] is not None and z["left_mm"] <= self.turn_side_wall_mm)
                or
                (z["right_mm"] is not None and z["right_mm"] <= self.turn_side_wall_mm)
            )

            return front_open and side_wall_visible

        self._turn_in_place_until(
            self.turn_speed,
            -self.turn_speed,
            done,
            "turn around 180",
        )

    def _turn_left_45(self):
        self._turn_in_place_for(
            -self.turn_speed,
            self.turn_speed,
            self.turn_45_sec,
            "left 45",
        )

    def _turn_right_45(self):
        self._turn_in_place_for(
            self.turn_speed,
            -self.turn_speed,
            self.turn_45_sec,
            "right 45",
        )

    def _centered_hallway_drive(self):
        z = self._zones()

        left_mm = z["left_mm"]
        right_mm = z["right_mm"]

        if self._front_obstacle():
            self.robot.stop()
            print("[GREETER] front obstacle / possible intersection", flush=True)
            return "front obstacle"

        steer = 0.0

        if left_mm is not None and right_mm is not None:
            error = right_mm - left_mm
            steer = self._clamp(error * self.wall_follow_kp, -self.max_steer, self.max_steer)

        elif left_mm is not None:
            error = self.center_target_mm - left_mm
            steer = self._clamp(-error * self.wall_follow_kp, -self.max_steer, self.max_steer)

        elif right_mm is not None:
            error = self.center_target_mm - right_mm
            steer = self._clamp(error * self.wall_follow_kp, -self.max_steer, self.max_steer)

        left_cmd = self._clamp(self.wall_follow_base_speed + steer, -1.0, 1.0)
        right_cmd = self._clamp(self.wall_follow_base_speed - steer, -1.0, 1.0)

        print(
            f"[GREETER DRIVE] left={left_cmd:.2f} right={right_cmd:.2f} "
            f"front={z['front_mm']} left_mm={left_mm} right_mm={right_mm}",
            flush=True,
        )

        self.robot.drive(left_cmd, right_cmd)
        return "driving"

    def _drive_straight_final(self):
        print("[GREETER FINAL] driving straight", flush=True)
        self.robot.drive(self.wall_follow_base_speed, self.wall_follow_base_speed)

    def _is_running(self):
        with self._lock:
            return self._running
        
    def _hallway_ready(self):
        z = self._zones()

        front = z["front_mm"]
        left = z["left_mm"]
        right = z["right_mm"]

        front_clear = front is None or front >= 1000.0

        left_ok = left is not None and 900.0 <= left <= 1800.0
        right_ok = right is not None and 900.0 <= right <= 2400.0

        return front_clear and left_ok and right_ok

    def _run(self):
        try:
            while self._is_running():
                with self._lock:
                    state = self._state
                    age = time.time() - self._state_entered_at

                if state == GreeterState.WAITING:
                    self.robot.stop()

                    if self._human_detected():
                        self._set_state(GreeterState.GREETING)

                elif state == GreeterState.GREETING:
                    self._say("Hello, how can I help you?", wait_sec=1.4)
                    self._set_state(GreeterState.LISTENING)

                elif state == GreeterState.LISTENING:
                    dest = self._listen_for_destination()

                    if dest is None:
                        self._say("Please say bathroom or robot lab.", wait_sec=1.1)
                    else:
                        with self._lock:
                            self._destination = dest

                        self._say("Follow me.", wait_sec=1.0)
                        self._set_state(GreeterState.TURNING_AROUND)

                elif state == GreeterState.TURNING_AROUND:
                    self._turn_around()
                    self._set_state(GreeterState.ALIGNING_TO_HALLWAY)

                elif state == GreeterState.MOVING_TO_T:
                    if not self._hallway_ready():
                        self._centered_hallway_drive()

                    elif self._far_t_intersection_seen():
                        self.robot.stop()
                        self._set_state(GreeterState.TURNING_TO_DESTINATION)

                    elif self._front_obstacle():
                        self.robot.stop()
                        print("[GREETER] obstacle before confirmed T; stopping", flush=True)
                        self._set_state(GreeterState.STOPPED)
                        with self._lock:
                            self._running = False

                    else:
                        self._centered_hallway_drive()

                elif state == GreeterState.MOVING_TO_T:
                    if self._far_t_intersection_seen():
                        self.robot.stop()
                        self._set_state(GreeterState.TURNING_TO_DESTINATION)

                    elif self._close_t_intersection_seen():
                        self.robot.stop()
                        self._set_state(GreeterState.TURNING_TO_DESTINATION)

                    elif self._front_obstacle():
                        self.robot.stop()
                        print("[GREETER] front obstacle before confirmed T; stopping for safety", flush=True)
                        self._set_state(GreeterState.STOPPED)

                        with self._lock:
                            self._running = False

                    else:
                        self._centered_hallway_drive()

                elif state == GreeterState.TURNING_TO_DESTINATION:
                    with self._lock:
                        dest = self._destination

                    # Based on stuart_map2:
                    # bathroom path uses right turn command
                    # robot lab path uses left turn command
                    if dest == Destination.BATHROOM:
                        self._turn_right_45()
                    else:
                        self._turn_left_45()

                    self._set_state(GreeterState.FINAL_MOVEMENT)

                elif state == GreeterState.FINAL_MOVEMENT:
                    end = time.time() + self.final_move_sec

                    while self._is_running() and time.time() < end:
                        if self._front_obstacle():
                            print("[GREETER] final movement stopped early: front obstacle", flush=True)
                            break

                        self._drive_straight_final()
                        time.sleep(1.0 / self.loop_hz)

                    self.robot.stop()

                    with self._lock:
                        dest_text = self._destination.value if self._destination else "destination"

                    self._say(f"We have arrived at the {dest_text}.", wait_sec=1.0)
                    self._set_state(GreeterState.STOPPED)

                    with self._lock:
                        self._running = False

                elif state == GreeterState.STOPPED:
                    self.robot.stop()

                    with self._lock:
                        self._running = False

                    break

                time.sleep(1.0 / self.loop_hz)

        except Exception as e:
            with self._lock:
                self._last_error = repr(e)
                self._state = GreeterState.ERROR
                self._running = False

            print("[GREETER ERROR]", repr(e), flush=True)
            self.robot.stop()

            try:
                self.tts.say("I had a navigation error and stopped.")
            except Exception:
                pass