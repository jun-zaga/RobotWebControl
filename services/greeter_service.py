# import enum
# import threading
# import time

# from config import (
# GREETER_HUMAN_DETECT_MM,
# GREETER_FRONT_OBSTACLE_MM,
# GREETER_WALL_VISIBLE_MM,
# GREETER_OPENING_MM,
# GREETER_TURN_180_SEC,
# GREETER_TURN_90_SEC,
# GREETER_FINAL_FORWARD_SEC,
# GREETER_BASE_SPEED,
# GREETER_TURN_SPEED,
# GREETER_WALL_FOLLOW_KP,
# GREETER_TARGET_SIDE_MM,
# )

# try:
#     import speech_recognition as sr
# except Exception as e:
#     sr = None
#     print("[GREETER] speech_recognition import failed:", e, flush=True)




# class GreeterState(str, enum.Enum):
#     WAITING = "WAITING"
#     GREETING = "GREETING"
#     LISTENING = "LISTENING"
#     TURNING_AROUND = "TURNING_AROUND"
#     ALIGNING_TO_HALLWAY = "ALIGNING_TO_HALLWAY"
#     MOVING_TO_T = "MOVING_TO_T"
#     TURNING_TO_DESTINATION = "TURNING_TO_DESTINATION"
#     FINAL_MOVEMENT = "FINAL_MOVEMENT"
#     STOPPED = "STOPPED"
#     ERROR = "ERROR"


# class Destination(str, enum.Enum):
#     BATHROOM = "bathroom"
#     ROBOT_LAB = "robot lab"


# class GreeterService:
#     """
#     Autonomous greeter FSM for the hallway guide mode.

#     State transitions:
#       WAITING -> GREETING when a human is detected in front by LIDAR
#       GREETING -> LISTENING after TTS greeting
#       LISTENING -> TURNING_AROUND after speech command parses to destination
#       TURNING_AROUND -> ALIGNING_TO_HALLWAY after timed 180 turn
#       ALIGNING_TO_HALLWAY -> MOVING_TO_T when both side walls are visible
#       MOVING_TO_T -> TURNING_TO_DESTINATION when front wall + both side openings are detected
#       TURNING_TO_DESTINATION -> FINAL_MOVEMENT after timed left/right turn
#       FINAL_MOVEMENT -> STOPPED after 5 seconds
#     """

#     # LIDAR zones are based on the repo's current convention: front center is 270 deg.
#     FRONT_CENTER_DEG = 270.0
#     LEFT_CENTER_DEG = 0.0
#     RIGHT_CENTER_DEG = 180.0

#     def __init__(self, robot_service, lidar_service, tts_service):
#         self.robot = robot_service
#         self.lidar = lidar_service
#         self.tts = tts_service
#         self._lock = threading.RLock()
#         self._thread = None
#         self._running = False
#         self._state = GreeterState.STOPPED
#         self._destination = None
#         self._last_error = None
#         self._last_heard = ""
#         self._state_entered_at = time.time()

#         # Tunables come from config.py
#         self.human_detect_mm = GREETER_HUMAN_DETECT_MM
#         self.front_obstacle_mm = GREETER_FRONT_OBSTACLE_MM
#         self.wall_visible_mm = GREETER_WALL_VISIBLE_MM
#         self.opening_mm = GREETER_OPENING_MM

#         self.center_target_mm = GREETER_TARGET_SIDE_MM
#         self.wall_follow_base_speed = GREETER_BASE_SPEED
#         self.wall_follow_kp = GREETER_WALL_FOLLOW_KP
#         self.turn_speed = GREETER_TURN_SPEED
#         self.turn_180_sec = GREETER_TURN_180_SEC
#         self.turn_90_sec = GREETER_TURN_90_SEC
#         self.final_move_sec = GREETER_FINAL_FORWARD_SEC

#         # Local safety defaults
#         self.max_steer = 0.28
#         self.align_timeout_sec = 5.0
#         self.loop_hz = 10.0

#     @staticmethod
#     def _angle_diff_deg(a, b):
#         return ((a - b + 180.0) % 360.0) - 180.0

#     @staticmethod
#     def _clamp(x, lo, hi):
#         return max(lo, min(hi, x))

#     def start(self):
#         with self._lock:
#             if self._running:
#                 return self.status()
#             self._running = True
#             self._state = GreeterState.WAITING
#             self._destination = None
#             self._last_error = None
#             self._last_heard = ""
#             self._state_entered_at = time.time()
#             self._thread = threading.Thread(target=self._run, daemon=True)
#             self._thread.start()
#             return self.status()

#     def stop(self, reason="manual stop"):
#         with self._lock:
#             self._running = False
#             self._state = GreeterState.STOPPED
#             self._last_error = reason
#         self.robot.stop()
#         return self.status()

#     def status(self):
#         with self._lock:
#             zones = self._zones()
#             return {
#                 "ok": True,
#                 "running": self._running,
#                 "state": self._state.value,
#                 "destination": self._destination.value if self._destination else None,
#                 "last_error": self._last_error,
#                 "last_heard": self._last_heard,
#                 "state_age_sec": round(time.time() - self._state_entered_at, 2),
#                 "zones": zones,
#                 "speech_enabled": sr is not None,
#             }

#     def _set_state(self, state):
#         with self._lock:
#             self._state = state
#             self._state_entered_at = time.time()
#         print(f"[GREETER] -> {state.value}", flush=True)

#     def _say(self, text, wait_sec=1.0):
#         print(f"[GREETER SAY] {text}", flush=True)
#         self.tts.say(text)
#         time.sleep(wait_sec)

#     def _zone_min(self, center_deg, half_angle=18.0):
#         return self.lidar.get_zone_min(center_deg, half_angle)

#     def _zones(self):
#         front = self._zone_min(self.FRONT_CENTER_DEG, 18.0)
#         left = self._zone_min(self.LEFT_CENTER_DEG, 22.0)
#         right = self._zone_min(self.RIGHT_CENTER_DEG, 22.0)
#         return {"front_mm": front, "left_mm": left, "right_mm": right}

#     def _human_detected(self):
#         front = self._zones()["front_mm"]
#         return front is not None and 450.0 <= front <= self.human_detect_mm

#     def _walls_on_both_sides(self):
#         z = self._zones()
#         left_ok = z["left_mm"] is not None and z["left_mm"] <= self.wall_visible_mm
#         right_ok = z["right_mm"] is not None and z["right_mm"] <= self.wall_visible_mm
#         return left_ok and right_ok

#     def _front_obstacle(self):
#         front = self._zones()["front_mm"]
#         return front is not None and front <= self.front_obstacle_mm

#     def _at_t_intersection(self):
#         z = self._zones()
#         front_wall = z["front_mm"] is not None and z["front_mm"] <= 700.0
#         left_open = z["left_mm"] is None or z["left_mm"] >= self.opening_mm
#         right_open = z["right_mm"] is None or z["right_mm"] >= self.opening_mm
#         return front_wall and left_open and right_open

#     def _listen_for_destination(self, timeout=6, phrase_time_limit=5):
#         if sr is None:
#             raise RuntimeError("speech_recognition is not installed. Run: pip install SpeechRecognition PyAudio")

#         recognizer = sr.Recognizer()
#         with sr.Microphone() as source:
#             recognizer.adjust_for_ambient_noise(source, duration=0.6)
#             audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

#         text = recognizer.recognize_google(audio).lower().strip()
#         with self._lock:
#             self._last_heard = text
#         print(f"[GREETER HEARD] {text}", flush=True)

#         if "bath" in text or "restroom" in text:
#             return Destination.BATHROOM
#         if "robot" in text or "lab" in text:
#             return Destination.ROBOT_LAB
#         return None

#     def _drive_for(self, left, right, seconds, stop=True):
#         end = time.time() + float(seconds)
#         while self._running and time.time() < end:
#             self.robot.drive(left, right)
#             time.sleep(0.08)
#         if stop:
#             self.robot.stop()
#             time.sleep(0.15)

#     def _turn_left_90(self):
#         self._drive_for(-self.turn_speed, self.turn_speed, self.turn_90_sec)

#     def _turn_right_90(self):
#         self._drive_for(self.turn_speed, -self.turn_speed, self.turn_90_sec)

#     def _turn_around(self):
#         self._drive_for(self.turn_speed, -self.turn_speed, self.turn_180_sec)

#     def _centered_hallway_drive(self):
#         z = self._zones()
#         left_mm = z["left_mm"]
#         right_mm = z["right_mm"]

#         # Stop for any person/object in front during navigation.
#         if self._front_obstacle():
#             self.robot.stop()
#             return "front obstacle"

#         steer = 0.0
#         if left_mm is not None and right_mm is not None:
#             # Positive error means robot is closer to left wall, so steer right.
#             error = right_mm - left_mm
#             steer = self._clamp(error * self.wall_follow_kp, -self.max_steer, self.max_steer)
#         elif left_mm is not None:
#             error = self.center_target_mm - left_mm
#             steer = self._clamp(-error * self.wall_follow_kp, -self.max_steer, self.max_steer)
#         elif right_mm is not None:
#             error = self.center_target_mm - right_mm
#             steer = self._clamp(error * self.wall_follow_kp, -self.max_steer, self.max_steer)

#         left_cmd = self._clamp(self.wall_follow_base_speed + steer, -1.0, 1.0)
#         right_cmd = self._clamp(self.wall_follow_base_speed - steer, -1.0, 1.0)
#         self.robot.drive(left_cmd, right_cmd)
#         return "driving"

#     def _run(self):
#         try:
#             while self._running:
#                 with self._lock:
#                     state = self._state
#                     age = time.time() - self._state_entered_at

#                 if state == GreeterState.WAITING:
#                     self.robot.stop()
#                     if self._human_detected():
#                         self._set_state(GreeterState.GREETING)

#                 elif state == GreeterState.GREETING:
#                     self._say("Hello, how can I help you?", wait_sec=1.4)
#                     self._set_state(GreeterState.LISTENING)

#                 elif state == GreeterState.LISTENING:
#                     dest = self._listen_for_destination()
#                     if dest is None:
#                         self._say("Please say bathroom or robot lab.", wait_sec=1.1)
#                     else:
#                         with self._lock:
#                             self._destination = dest
#                         self._say("Follow me.", wait_sec=1.0)
#                         self._set_state(GreeterState.TURNING_AROUND)

#                 elif state == GreeterState.TURNING_AROUND:
#                     self._turn_around()
#                     self._set_state(GreeterState.ALIGNING_TO_HALLWAY)

#                 elif state == GreeterState.ALIGNING_TO_HALLWAY:
#                     if self._walls_on_both_sides() or age >= self.align_timeout_sec:
#                         self._set_state(GreeterState.MOVING_TO_T)
#                     else:
#                         self._centered_hallway_drive()

#                 elif state == GreeterState.MOVING_TO_T:
#                     if self._at_t_intersection():
#                         self.robot.stop()
#                         self._set_state(GreeterState.TURNING_TO_DESTINATION)
#                     else:
#                         self._centered_hallway_drive()

#                 elif state == GreeterState.TURNING_TO_DESTINATION:
#                     with self._lock:
#                         dest = self._destination
#                     if dest == Destination.BATHROOM:
#                         self._turn_right_90()
#                     else:
#                         self._turn_left_90()
#                     self._set_state(GreeterState.FINAL_MOVEMENT)

#                 elif state == GreeterState.FINAL_MOVEMENT:
#                     end = time.time() + self.final_move_sec
#                     while self._running and time.time() < end:
#                         self._centered_hallway_drive()
#                         time.sleep(1.0 / self.loop_hz)
#                     self.robot.stop()
#                     with self._lock:
#                         dest_text = self._destination.value if self._destination else "destination"
#                     self._say(f"We have arrived at the {dest_text}.", wait_sec=1.0)
#                     self._set_state(GreeterState.STOPPED)
#                     with self._lock:
#                         self._running = False

#                 elif state == GreeterState.STOPPED:
#                     self.robot.stop()
#                     with self._lock:
#                         self._running = False
#                     break

#                 time.sleep(1.0 / self.loop_hz)

#         except Exception as e:
#             with self._lock:
#                 self._last_error = repr(e)
#                 self._state = GreeterState.ERROR
#                 self._running = False
#             print("[GREETER ERROR]", repr(e), flush=True)
#             self.robot.stop()
#             self.tts.say("I had a navigation error and stopped.")
