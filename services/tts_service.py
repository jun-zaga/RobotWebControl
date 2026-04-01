import queue
import threading

from config import TTS_DEFAULT_RATE, TTS_DEFAULT_VOL

try:
    import pyttsx3
except Exception as e:
    pyttsx3 = None
    print("[TTS] import failed:", e, flush=True)


class TTSService:
    def __init__(self):
        self._q = queue.Queue()
        self._engine = None
        self._engine_lock = threading.Lock()
        threading.Thread(target=self._worker, daemon=True).start()

    def _init(self):
        if pyttsx3 is None:
            return None
        if self._engine is None:
            self._engine = pyttsx3.init()
        return self._engine

    def list_voices(self):
        if pyttsx3 is None:
            return []
        engine = self._init()
        try:
            voices = engine.getProperty("voices") or []
            return [{"id": v.id, "name": getattr(v, "name", None) or v.id} for v in voices]
        except Exception:
            return []

    def stop(self):
        try:
            while True:
                self._q.get_nowait()
                self._q.task_done()
        except queue.Empty:
            pass

        if self._engine is not None:
            try:
                self._engine.stop()
            except Exception:
                pass

    def say(self, text: str, voice=None, rate=None, volume=None) -> bool:
        text = (text or "").strip()
        if not text:
            return False

        if pyttsx3 is None:
            print("[TTS missing] text:", text, flush=True)
            return False

        self._q.put(
            {
                "text": text,
                "voice": voice,
                "rate": rate if rate is not None else TTS_DEFAULT_RATE,
                "volume": volume if volume is not None else TTS_DEFAULT_VOL,
            }
        )
        return True

    def _worker(self):
        while True:
            item = self._q.get()
            try:
                if pyttsx3 is None:
                    continue

                engine = self._init()
                with self._engine_lock:
                    if item.get("voice"):
                        try:
                            engine.setProperty("voice", item["voice"])
                        except Exception:
                            pass

                    try:
                        engine.setProperty("rate", int(item["rate"]))
                    except Exception:
                        pass

                    try:
                        engine.setProperty("volume", float(item["volume"]))
                    except Exception:
                        pass

                    engine.say(item["text"])
                    engine.runAndWait()
            except Exception as e:
                print("[TTS ERROR]", e, flush=True)
            finally:
                self._q.task_done()