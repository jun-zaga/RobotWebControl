import queue
import threading


class ActionRunner:
    def __init__(self, rc, actions, on_state_change=None):
        self.rc = rc
        self.actions = actions
        self.q = queue.Queue()
        self.stop_event = threading.Event()
        self.on_state_change = on_state_change or (lambda s: None)

        self.worker = threading.Thread(target=self._loop, daemon=True)
        self.worker.start()

    def enqueue_actions(self, actions):
        if not actions:
            return
        self.q.put(list(actions))

    def interrupt_all(self):
        print("[ACTION] interrupt requested", flush=True)
        self.stop_event.set()

        try:
            while True:
                self.q.get_nowait()
                self.q.task_done()
        except queue.Empty:
            pass

        try:
            self.rc.stop()
        except Exception as e:
            print("[ACTION] rc.stop failed:", e, flush=True)

        self.stop_event.clear()

    def _loop(self):
        while True:
            names = self.q.get()
            self.on_state_change("EXEC_ACTIONS")
            try:
                for name in names:
                    if self.stop_event.is_set():
                        break
                    self._run_one(name)
            finally:
                try:
                    self.rc.stop()
                except Exception:
                    pass
                self.on_state_change("IDLE")
                self.q.task_done()

    def _run_one(self, name):
        print(f"[ACTION START] {name}", flush=True)
        try:
            fn = self.actions.get(name)
            if not fn:
                print(f"[ACTION WARN] unknown action <{name}>", flush=True)
                return
            fn(self.rc, self.stop_event)
        except Exception as e:
            print(f"[ACTION ERROR] {name}: {e}", flush=True)
        finally:
            try:
                self.rc.stop()
            except Exception:
                pass
            print(f"[ACTION END] {name}", flush=True)