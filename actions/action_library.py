import time


def _check_stop(stop_event):
    if stop_event.is_set():
        raise RuntimeError("interrupted")


def _sleepy_head_tilt(rc, stop_event, poses, cap=3.0):
    start = time.time()
    for p in poses:
        _check_stop(stop_event)
        if (time.time() - start) > cap:
            raise RuntimeError(f"action exceeded cap of {cap}s")
        rc.head_tilt(p)
        time.sleep(0.35)


def _sleepy_head_pan(rc, stop_event, poses, cap=3.0):
    start = time.time()
    for p in poses:
        _check_stop(stop_event)
        if (time.time() - start) > cap:
            raise RuntimeError(f"action exceeded cap of {cap}s")
        rc.head_pan(p)
        time.sleep(0.35)


def head_yes(rc, stop_event):
    _sleepy_head_tilt(rc, stop_event, [0.35, 0.65, 0.50], cap=3.0)


def head_no(rc, stop_event):
    _sleepy_head_pan(rc, stop_event, [0.25, 0.75, 0.50], cap=3.0)


def arm_raise(rc, stop_event):
    start = time.time()
    _check_stop(stop_event)
    rc.left_joint(1, 0.95)
    rc.left_joint(3, 0.05)
    time.sleep(0.8)
    _check_stop(stop_event)
    if (time.time() - start) > 4.0:
        raise RuntimeError("action exceeded cap of 4.0s")
    rc.left_arm([0.50] * 6)


def dance90(rc, stop_event):
    start = time.time()

    spin_power = 1.0
    left_90_time = 3.0
    right_90_time = 3.0

    steps = [
        (-spin_power, spin_power, left_90_time),
        (spin_power, -spin_power, right_90_time),
        (spin_power, -spin_power, right_90_time),
        (-spin_power, spin_power, left_90_time),
    ]

    for l, r, delay in steps:
        _check_stop(stop_event)
        if (time.time() - start) > 14.0:
            raise RuntimeError("action exceeded cap of 14.0s")
        rc.drive(l, r)
        time.sleep(delay)
        rc.stop()
        time.sleep(0.2)


ACTIONS = {
    "head_yes": head_yes,
    "head_no": head_no,
    "arm_raise": arm_raise,
    "dance90": dance90,
}