import os
import time

# ---------- Maestro setup ----------
USE_MOCK = os.getenv("ROBOT_MOCK", "0") == "1"

if not USE_MOCK:
    import maestro
    servo = maestro.Controller()
else:
    servo = None
    print("[ROBOT_MOCK=1] Hardware disabled (no serial).")

# Channels
LEFT_WHEEL  = 0
RIGHT_WHEEL = 1
HEAD_PAN    = 4
HEAD_TILT   = 3
WAIST       = 2

# ---------- Safe ranges ----------
WHEEL_CENTER = 6000
WHEEL_RANGE  = 1000        # max +/- from center

PAN_MIN, PAN_MAX     = 4500, 7500
TILT_MIN, TILT_MAX   = 4700, 7300
WAIST_MIN, WAIST_MAX = 4600, 7400

# ---------- Maestro tuning ----------
if servo is not None:
    servo.setAccel(LEFT_WHEEL, 4)
    servo.setAccel(RIGHT_WHEEL, 4)
    servo.setSpeed(LEFT_WHEEL, 10)
    servo.setSpeed(RIGHT_WHEEL, 10)

# ---------- Helpers ----------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def norm_to_range(n, lo, hi):
    n = 1 - n  # flip direction
    return int(lo + n * (hi - lo))


def wheel_target(n):
    # n in [-1,1]
    return int(WHEEL_CENTER + clamp(n, -1.0, 1.0) * WHEEL_RANGE)

def _mock(label: str, **kwargs):
    # lightweight mock logger
    args = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    print(f"[MOCK:{label}] {args}".strip())

# ---------- Required API ----------
POWER_GAIN = 1.8   # try 1.1 → 1.8
MAX_POWER  = 1.0    # keep at 1.0 unless you also change wheel_target scaling

def clamp01(x):
    return max(-1.0, min(1.0, x))

def drive(l: float, r: float) -> None:
    l = clamp01(l * POWER_GAIN)
    r = clamp01(r * POWER_GAIN)

    if servo is None:
        print(f"[MOCK] drive L={l:.2f} R={r:.2f}")
        return

    servo.setTarget(LEFT_WHEEL,  wheel_target(l))
    servo.setTarget(RIGHT_WHEEL, wheel_target(r))
    print(f"[drive] L={l:.2f} R={r:.2f}")


def head_pan(pan: float) -> None:
    tgt = norm_to_range(pan, PAN_MIN, PAN_MAX)
    if servo is None:
        _mock("pan", target=tgt, pan=f"{pan:.2f}")
        return
    servo.setTarget(HEAD_PAN, tgt)
    print(f"[pan] {tgt}")

def head_tilt(tilt: float) -> None:
    tgt = norm_to_range(tilt, TILT_MIN, TILT_MAX)
    if servo is None:
        _mock("tilt", target=tgt, tilt=f"{tilt:.2f}")
        return
    servo.setTarget(HEAD_TILT, tgt)
    print(f"[tilt] {tgt}")

def waist(pos: float) -> None:
    tgt = norm_to_range(pos, WAIST_MIN, WAIST_MAX)
    if servo is None:
        _mock("waist", target=tgt, pos=f"{pos:.2f}")
        return
    servo.setTarget(WAIST, tgt)
    print(f"[waist] {tgt}")

def stop() -> None:
    if servo is None:
        _mock("stop")
        return
    servo.setTarget(LEFT_WHEEL, WHEEL_CENTER)
    servo.setTarget(RIGHT_WHEEL, WHEEL_CENTER)
    print("[STOP] wheels neutral")

# Optional voice hook (keep for grading)
PHRASES = {
    1: "Hello, Hunter.",
    2: "Hunter is so cool.",
    3: "Please do not touch my wheels.",
    4: "Hunter is the greatest."
}

def say(phrase_id: int) -> bool:
    phrase = PHRASES.get(phrase_id)
    if not phrase:
        return False
    if servo is None:
        _mock("say", phraseId=phrase_id, phrase=phrase)
        return True
    print(f"[say] {phrase}")
    return True
