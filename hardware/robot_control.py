import os

USE_MOCK = os.getenv("ROBOT_MOCK", "0") == "1"

servo = None
if not USE_MOCK:
    try:
        from . import maestro
        servo = maestro.Controller()
        print("[HW] Maestro connected", flush=True)
    except Exception as e:
        servo = None
        USE_MOCK = True
        print(f"[WARN] Maestro not available, running MOCK mode. Reason: {e}", flush=True)
else:
    print("[ROBOT_MOCK=1] Hardware disabled", flush=True)


LEFT_WHEEL = 0
RIGHT_WHEEL = 1
WAIST = 2
HEAD_TILT = 3
HEAD_PAN = 4

LEFT_ARM_CHANNELS = [5, 6, 7, 8, 9, 10]
RIGHT_ARM_CHANNELS = [11, 12, 13, 14, 15, 16]

# Continuous servo calibration.
# 6000 = neutral/stop on Maestro target units.
# Negative command should move BOTH drive wheels forward on your robot.
LEFT_WHEEL_CENTER = 6000
RIGHT_WHEEL_CENTER = 6000

# Right wheel gets extra pulse range because it has been anchoring/stalling under load.
LEFT_WHEEL_RANGE = 250
RIGHT_WHEEL_RANGE = 1000

PAN_MIN, PAN_MAX = 4500, 7500
TILT_MIN, TILT_MAX = 4700, 7300
WAIST_MIN, WAIST_MAX = 4600, 7400

ARM_CENTER = 5900
ARM_HALF_RANGE = 1600

# Direction-specific gains after command sign is known.
# Based on your tests, negative is forward for both wheels.
LEFT_FWD_GAIN = 1.00
LEFT_REV_GAIN = 1.00
RIGHT_FWD_GAIN = 1.00
RIGHT_REV_GAIN = 1.00

LEFT_INV = {1: True, 3: True}
RIGHT_INV = {1: True, 3: True}

NEUTRAL_L = [0.50] * 6
NEUTRAL_R = [0.50] * 6

RAISE_L = [0.95, 0.50, 0.00, 0.50, 0.50, 0.50]
RAISE_R = [0.00, 0.50, 0.95, 0.50, 0.50, 0.50]

HANDS_OPEN_L = [0.50, 0.50, 0.50, 0.50, 0.50, 0.05]
HANDS_OPEN_R = [0.50, 0.50, 0.50, 0.50, 0.50, 0.05]
HANDS_CLOSE_L = [0.50, 0.50, 0.50, 0.50, 0.50, 0.95]
HANDS_CLOSE_R = [0.50, 0.50, 0.50, 0.50, 0.50, 0.95]

POSES = {
    "arms_neutral": {"left": NEUTRAL_L, "right": NEUTRAL_R},
    "raise_left": {"left": RAISE_L, "right": None},
    "raise_right": {"left": None, "right": RAISE_R},
    "hands_open": {"left": HANDS_OPEN_L, "right": HANDS_OPEN_R},
    "hands_close": {"left": HANDS_CLOSE_L, "right": HANDS_CLOSE_R},
}


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def norm_to_range(n01, lo, hi):
    n01 = clamp(float(n01), 0.0, 1.0)
    return int(lo + n01 * (hi - lo))


def wheel_target(n, center, wheel_range):
    n = clamp(float(n), -1.0, 1.0)
    return int(center + n * wheel_range)


def arm_target(pos01):
    pos01 = clamp(float(pos01), 0.0, 1.0)
    return int(ARM_CENTER + (pos01 - 0.5) * 2 * ARM_HALF_RANGE)


def _set_target(ch, target, label):
    if servo is None:
        print(f"[MOCK:{label}] ch={ch} target={target}", flush=True)
        return
    servo.setTarget(ch, int(target))


def drive(l, r):
    l = clamp(float(l), -1.0, 1.0)
    r = clamp(float(r), -1.0, 1.0)

    # Negative is forward for both wheels based on your wheel tests.
    if l < 0:
        l *= LEFT_FWD_GAIN
    else:
        l *= LEFT_REV_GAIN

    if r < 0:
        r *= RIGHT_FWD_GAIN
    else:
        r *= RIGHT_REV_GAIN

    l = clamp(l, -1.0, 1.0)
    r = clamp(r, -1.0, 1.0)

    left_target = wheel_target(l, LEFT_WHEEL_CENTER, LEFT_WHEEL_RANGE)
    right_target = wheel_target(r, RIGHT_WHEEL_CENTER, RIGHT_WHEEL_RANGE)

    print(
        f"[HW DRIVE] cmd=({l:.2f},{r:.2f}) "
        f"targets=({left_target},{right_target})",
        flush=True,
    )

    _set_target(LEFT_WHEEL, left_target, "left_wheel")
    _set_target(RIGHT_WHEEL, right_target, "right_wheel")


def stop():
    _set_target(LEFT_WHEEL, LEFT_WHEEL_CENTER, "left_wheel_stop")
    _set_target(RIGHT_WHEEL, RIGHT_WHEEL_CENTER, "right_wheel_stop")


def head_pan(pos01):
    _set_target(HEAD_PAN, norm_to_range(pos01, PAN_MIN, PAN_MAX), "head_pan")


def head_tilt(pos01):
    _set_target(HEAD_TILT, norm_to_range(pos01, TILT_MIN, TILT_MAX), "head_tilt")


def waist(pos01):
    _set_target(WAIST, norm_to_range(pos01, WAIST_MIN, WAIST_MAX), "waist")


def left_joint(i: int, pos01: float):
    if i < 1 or i > 6:
        raise ValueError("left_joint index must be 1..6")
    if LEFT_INV.get(i, False):
        pos01 = 1.0 - float(pos01)
    ch = LEFT_ARM_CHANNELS[i - 1]
    tgt = arm_target(pos01)
    _set_target(ch, tgt, f"left_j{i}")


def right_joint(i: int, pos01: float):
    if i < 1 or i > 6:
        raise ValueError("right_joint index must be 1..6")
    if RIGHT_INV.get(i, False):
        pos01 = 1.0 - float(pos01)
    ch = RIGHT_ARM_CHANNELS[i - 1]
    tgt = arm_target(pos01)
    _set_target(ch, tgt, f"right_j{i}")


def left_arm(vals):
    for i, v in enumerate(vals, start=1):
        left_joint(i, v)


def right_arm(vals):
    for i, v in enumerate(vals, start=1):
        right_joint(i, v)


def arms_neutral():
    left_arm(NEUTRAL_L)
    right_arm(NEUTRAL_R)


def pose(name):
    p = POSES.get(name)
    if not p:
        return False

    if p["left"] is not None:
        left_arm(p["left"])
    if p["right"] is not None:
        right_arm(p["right"])

    return p
