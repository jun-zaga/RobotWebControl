import threading
import time

from config import (
    LIDAR_PORT,
    LIDAR_BAUD,
    LIDAR_FRONT_CENTER_DEG,
    LIDAR_REAR_CENTER_DEG,
    LIDAR_ZONE_HALF_ANGLE_DEG,
    LIDAR_FRONT_STOP_MM,
    LIDAR_REAR_STOP_MM,
    LIDAR_STALE_SEC,
)

try:
    from rplidar import RPLidar
except Exception as e:
    RPLidar = None
    print("[LIDAR] import failed:", e, flush=True)


class LidarService:
    def __init__(self):
        self._lidar = None
        self._lock = threading.Lock()
        self._front_min_mm = None
        self._rear_min_mm = None
        self._any_min_mm = None
        self._last_ts = 0.0
        self._status = "disabled"
        self._started = False

    def log(self, msg):
        print(f"[LIDAR] {time.strftime('%H:%M:%S')} | {msg}", flush=True)

    def angle_diff_deg(self, a, b):
        return ((a - b + 180.0) % 360.0) - 180.0

    def start(self):
        if self._started:
            return
        self._started = True
        threading.Thread(target=self._lidar_loop, daemon=True).start()

    def get_status(self):
        with self._lock:
            return {
                "ok": True,
                "status": self._status,
                "front_min_mm": self._front_min_mm,
                "rear_min_mm": self._rear_min_mm,
                "any_min_mm": self._any_min_mm,
                "last_scan_age_sec": (time.time() - self._last_ts) if self._last_ts else None,
                "port": LIDAR_PORT,
                "baud": LIDAR_BAUD,
                "front_center_deg": LIDAR_FRONT_CENTER_DEG,
                "rear_center_deg": LIDAR_REAR_CENTER_DEG,
                "zone_half_angle_deg": LIDAR_ZONE_HALF_ANGLE_DEG,
                "front_stop_mm": LIDAR_FRONT_STOP_MM,
                "rear_stop_mm": LIDAR_REAR_STOP_MM,
            }

    def apply_safety(self, left, right):
        with self._lock:
            front_min = self._front_min_mm
            rear_min = self._rear_min_mm
            last_ts = self._last_ts
            status = self._status

        now = time.time()
        stale = (now - last_ts) > LIDAR_STALE_SEC if last_ts else True

        safety = {
            "mode": "clear",
            "status": status,
            "front_min_mm": front_min,
            "rear_min_mm": rear_min,
            "stale": stale,
        }

        safe_left = float(left)
        safe_right = float(right)

        forward_req = left > 0 or right > 0
        reverse_req = left < 0 or right < 0

        if stale:
            safety["mode"] = "stale"
            return safe_left, safe_right, safety

        # FRONT SAFETY: stop if object is within about 1 foot in front
        if forward_req and front_min is not None and front_min <= LIDAR_FRONT_STOP_MM:
            safety["mode"] = "blocked_front"
            return 0.0, 0.0, safety

        # REAR SAFETY: disabled by default to ignore fixed post behind robot
        if (
            LIDAR_REAR_STOP_MM > 0
            and reverse_req
            and rear_min is not None
            and rear_min <= LIDAR_REAR_STOP_MM
        ):
            safety["mode"] = "blocked_rear"
            return 0.0, 0.0, safety

        return safe_left, safe_right, safety

    def _lidar_loop(self):
        self.log("thread started")

        if RPLidar is None:
            with self._lock:
                self._status = "import_failed"
            self.log("RPLidar import failed")
            return

        while True:
            lidar = None
            try:
                with self._lock:
                    self._status = "connecting"

                self.log(f"opening port={LIDAR_PORT} baud={LIDAR_BAUD}")
                lidar = RPLidar(LIDAR_PORT, baudrate=LIDAR_BAUD, timeout=3)
                self.log("port opened")

                time.sleep(1.0)

                info = lidar.get_info()
                self.log(f"info={info}")

                health = lidar.get_health()
                self.log(f"health={health}")

                lidar.clean_input()
                self.log("input cleaned")

                with self._lock:
                    self._lidar = lidar
                    self._status = "running"

                scan_iter = lidar.iter_scans(max_buf_meas=500)
                self.log("starting scan loop")

                scan_count = 0
                last_summary_ts = 0.0

                for scan in scan_iter:
                    scan_count += 1

                    front_min = None
                    rear_min = None
                    any_min = None
                    valid_points = 0

                    for quality, angle, distance in scan:
                        if distance is None or distance <= 0:
                            continue

                        valid_points += 1

                        if any_min is None or distance < any_min:
                            any_min = distance

                        if abs(self.angle_diff_deg(angle, LIDAR_FRONT_CENTER_DEG)) <= LIDAR_ZONE_HALF_ANGLE_DEG:
                            if front_min is None or distance < front_min:
                                front_min = distance

                        if abs(self.angle_diff_deg(angle, LIDAR_REAR_CENTER_DEG)) <= LIDAR_ZONE_HALF_ANGLE_DEG:
                            if rear_min is None or distance < rear_min:
                                rear_min = distance

                    now = time.time()

                    with self._lock:
                        self._front_min_mm = front_min
                        self._rear_min_mm = rear_min
                        self._any_min_mm = any_min
                        self._last_ts = now
                        self._status = "running"

                    if scan_count <= 5 or (now - last_summary_ts) >= 1.0:
                        self.log(
                            f"scan #{scan_count}: valid_points={valid_points} "
                            f"any_min={any_min} front_min={front_min} rear_min={rear_min}"
                        )
                        last_summary_ts = now

            except Exception as e:
                self.log(f"ERROR: {repr(e)}")

                with self._lock:
                    self._status = f"error: {e}"
                    self._front_min_mm = None
                    self._rear_min_mm = None
                    self._any_min_mm = None
                    self._last_ts = 0.0
                    self._lidar = None

                try:
                    if lidar is not None:
                        lidar.stop()
                        self.log("stop() ok")
                except Exception as e2:
                    self.log(f"stop() failed: {repr(e2)}")

                try:
                    if lidar is not None:
                        lidar.stop_motor()
                        self.log("stop_motor() ok")
                except Exception as e2:
                    self.log(f"stop_motor() failed: {repr(e2)}")

                try:
                    if lidar is not None:
                        lidar.disconnect()
                        self.log("disconnect() ok")
                except Exception as e2:
                    self.log(f"disconnect() failed: {repr(e2)}")

                time.sleep(2.0)