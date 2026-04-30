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


# -------------------------------------------------
# Drive channels
# -------------------------------------------------
# Your channel test showed:
#   channel 0 = TURN / steering mixer
#   channel 1 = DRIVE / throttle mixer
#
# channel 0 @ 5200 -> left forward, right backward
# channel 0 @ 6800 -> left backward, right forward
# channel 1 @ 5200 -> both forward
# channel 1 @ 6800 -> both backward

TURN_CHANNEL = 0
DRIVE_CHANNEL = 1

TURN_CENTER = 6000
DRIVE_CENTER = 6000

TURN_RANGE = 1300
DRIVE_RANGE = 1300

TURN_INVERT = False
DRIVE_INVERT = False

TURN_MIN_POWER = 0.35
DRIVE_MIN_POWER = 0.35


# -------------------------------------------------
# Servo channels
# -------------------------------------------------

WAIST = 2
HEAD_TILT = 3
HEAD_PAN = 4

LEFT_ARM_CHANNELS = [5, 6, 7, 8, 9, 10]
RIGHT_ARM_CHANNELS = [11, 12, 13, 14, 15, 16]

PAN_MIN, PAN_MAX = 4500, 7500
TILT_MIN, TILT_MAX = 4700, 7300
WAIST_MIN, WAIST_MAX = 4600, 7400

ARM_CENTER = 5900
ARM_HALF_RANGE = 1600

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


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def norm_to_range(n01, lo, hi):
    n01 = clamp(float(n01), 0.0, 1.0)
    return int(lo + n01 * (hi - lo))


def apply_min_power(x, min_power):
    x = clamp(float(x), -1.0, 1.0)

    if abs(x) < 0.02:
        return 0.0

    if abs(x) < min_power:
        return min_power if x > 0 else -min_power

    return x


def target_from_power(power, center, pulse_range, invert=False):
    power = clamp(float(power), -1.0, 1.0)

    if invert:
        power = -power

    return int(center + power * pulse_range)


def arm_target(pos01):
    pos01 = clamp(float(pos01), 0.0, 1.0)
    return int(ARM_CENTER + (pos01 - 0.5) * 2 * ARM_HALF_RANGE)


def _set_target(ch, target, label):
    target = int(target)

    if servo is None:
        print(f"[MOCK:{label}] ch={ch} target={target}", flush=True)
        return

    servo.setTarget(ch, target)


# -------------------------------------------------
# Drive
# -------------------------------------------------

def drive(l, r):
    """
    Tank input -> throttle/steering mixer output.

    Input convention:
      l/r negative = forward
      l/r positive = backward

    Hardware reality:
      channel 0 = turn mixer
      channel 1 = drive mixer

    Examples:
      drive(-0.5, -0.5) -> both forward
      drive( 0.5,  0.5) -> both backward
      drive(-0.5,  0.0) -> gentle right turn, left-side push
      drive( 0.0, -0.5) -> gentle left turn, right-side push
      drive( 0.5, -0.5) -> pivot one way
      drive(-0.5,  0.5) -> pivot other way
    """
    raw_l = clamp(float(l), -1.0, 1.0)
    raw_r = clamp(float(r), -1.0, 1.0)

    # Mixer wiring swaps left/right behavior, so correct it here.
    raw_l, raw_r = raw_r, raw_l

    if abs(raw_l) < 0.05:
        raw_l = 0.0
    if abs(raw_r) < 0.05:
        raw_r = 0.0

    # Tank-to-mixer conversion.
    drive_power = (raw_l + raw_r) / 2.0
    turn_power = (raw_r - raw_l) / 2.0

    drive_power = apply_min_power(drive_power, DRIVE_MIN_POWER)
    turn_power = apply_min_power(turn_power, TURN_MIN_POWER)

    drive_target = target_from_power(
        drive_power,
        DRIVE_CENTER,
        DRIVE_RANGE,
        DRIVE_INVERT,
    )

    turn_target = target_from_power(
        turn_power,
        TURN_CENTER,
        TURN_RANGE,
        TURN_INVERT,
    )

    print(
        f"[HW DRIVE] tank=({raw_l:.2f},{raw_r:.2f}) "
        f"mixed drive={drive_power:.2f} turn={turn_power:.2f} "
        f"targets turn_ch{TURN_CHANNEL}={turn_target} "
        f"drive_ch{DRIVE_CHANNEL}={drive_target}",
        flush=True,
    )

    _set_target(TURN_CHANNEL, turn_target, "turn_channel")
    _set_target(DRIVE_CHANNEL, drive_target, "drive_channel")

    return {
        "ok": True,
        "l": raw_l,
        "r": raw_r,
        "drive_power": drive_power,
        "turn_power": turn_power,
        "turn_target": turn_target,
        "drive_target": drive_target,
    }


def stop():
    _set_target(TURN_CHANNEL, TURN_CENTER, "turn_stop")
    _set_target(DRIVE_CHANNEL, DRIVE_CENTER, "drive_stop")

    return {
        "ok": True,
        "l": 0,
        "r": 0,
        "drive_power": 0,
        "turn_power": 0,
        "turn_target": TURN_CENTER,
        "drive_target": DRIVE_CENTER,
    }


# -------------------------------------------------
# Head / waist
# -------------------------------------------------

def head_pan(pos01):
    target = norm_to_range(pos01, PAN_MIN, PAN_MAX)
    _set_target(HEAD_PAN, target, "head_pan")
    return {"ok": True, "channel": HEAD_PAN, "target": target}


def head_tilt(pos01):
    target = norm_to_range(pos01, TILT_MIN, TILT_MAX)
    _set_target(HEAD_TILT, target, "head_tilt")
    return {"ok": True, "channel": HEAD_TILT, "target": target}


def waist(pos01):
    target = norm_to_range(pos01, WAIST_MIN, WAIST_MAX)
    _set_target(WAIST, target, "waist")
    return {"ok": True, "channel": WAIST, "target": target}


# -------------------------------------------------
# Arms
# -------------------------------------------------

def left_joint(i: int, pos01: float):
    if i < 1 or i > 6:
        raise ValueError("left_joint index must be 1..6")

    if LEFT_INV.get(i, False):
        pos01 = 1.0 - float(pos01)

    ch = LEFT_ARM_CHANNELS[i - 1]
    tgt = arm_target(pos01)
    _set_target(ch, tgt, f"left_j{i}")

    return {"ok": True, "channel": ch, "target": tgt}


def right_joint(i: int, pos01: float):
    if i < 1 or i > 6:
        raise ValueError("right_joint index must be 1..6")

    if RIGHT_INV.get(i, False):
        pos01 = 1.0 - float(pos01)

    ch = RIGHT_ARM_CHANNELS[i - 1]
    tgt = arm_target(pos01)
    _set_target(ch, tgt, f"right_j{i}")

    return {"ok": True, "channel": ch, "target": tgt}


def left_arm(vals):
    results = []

    for i, v in enumerate(vals, start=1):
        results.append(left_joint(i, v))

    return {"ok": True, "results": results}


def right_arm(vals):
    results = []

    for i, v in enumerate(vals, start=1):
        results.append(right_joint(i, v))

    return {"ok": True, "results": results}


def arms_neutral():
    left = left_arm(NEUTRAL_L)
    right = right_arm(NEUTRAL_R)

    return {
        "ok": True,
        "left": left,
        "right": right,
    }


def pose(name):
    p = POSES.get(name)

    if not p:
        return False

    result = {"ok": True, "pose": name}

    if p["left"] is not None:
        result["left"] = left_arm(p["left"])

    if p["right"] is not None:
        result["right"] = right_arm(p["right"])

    return result