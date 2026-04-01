import threading
import time

from config import CMD_TIMEOUT_SEC, WATCHDOG_PERIOD_SEC


class SafetyService:
    def __init__(self, rc):
        self.rc = rc
        self.last_cmd_ts = time.time()
        self.action_active = False
        self._lock = threading.Lock()
        self._started = False

    def update_last_cmd_ts(self):
        with self._lock:
            self.last_cmd_ts = time.time()

    def set_action_active(self, active: bool):
        with self._lock:
            self.action_active = bool(active)

    def get_state(self):
        with self._lock:
            return {
                "last_cmd_ts": self.last_cmd_ts,
                "action_active": self.action_active,
            }

    def start(self):
        if self._started:
            return
        self._started = True
        threading.Thread(target=self._watchdog_loop, daemon=True).start()

    def _watchdog_loop(self):
        while True:
            time.sleep(WATCHDOG_PERIOD_SEC)
            with self._lock:
                age = time.time() - self.last_cmd_ts
                action_active = self.action_active

            if (not action_active) and age > CMD_TIMEOUT_SEC:
                try:
                    self.rc.stop()
                except Exception as e:
                    print(f"[WATCHDOG] stop failed: {e}", flush=True)