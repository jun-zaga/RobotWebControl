#!/usr/bin/env python3
"""
Wall-follow LiDAR calibration for RobotWebControl.

This is NOT turn/dance calibration. It finds which RPLIDAR angles match the
robot's real FRONT, BACK, LEFT, and RIGHT directions, then writes config.py
constants for wall-follow and front/rear safety.

Run from repo root:
    python3 calibration/wall_follow_lidar_calibration.py
"""

import json
import math
import statistics
import time
from pathlib import Path

RESULT_DIR = Path("calibration_results")
RESULT_DIR.mkdir(exist_ok=True)

SAMPLE_SECONDS = 4.0
MIN_MM = 80.0
MAX_MM = 2500.0
BIN_DEG = 2.0
WINDOW_DEG = 14.0


def angle_diff_deg(a, b):
    return ((float(a) - float(b) + 180.0) % 360.0) - 180.0


def wrap_deg(deg):
    return float(deg) % 360.0


def circular_mean_deg(angles):
    if not angles:
        return None
    x = sum(math.cos(math.radians(a)) for a in angles)
    y = sum(math.sin(math.radians(a)) for a in angles)
    return wrap_deg(math.degrees(math.atan2(y, x)))


def get_lidar_service():
    # Importing app.py creates the app and starts services in this repo.
    from app import app
    return app.config["services"]["lidar"]


def wait_for_lidar(lidar, timeout=20.0):
    print("\nWaiting for LiDAR scans...")
    start = time.time()
    while time.time() - start < timeout:
        status = lidar.get_status()
        if status.get("status") == "running" and status.get("scan_points", 0) > 20:
            print("LiDAR running:", status)
            return True
        print("  status=", status.get("status"), "points=", status.get("scan_points"))
        time.sleep(1.0)
    return False


def read_points(lidar):
    # Uses the repo's private scan buffer because get_status() only returns counts.
    with lidar._lock:
        return list(lidar._last_scan_points), lidar._last_ts


def collect_points(lidar, seconds=SAMPLE_SECONDS):
    end = time.time() + seconds
    points = []
    while time.time() < end:
        scan_points, last_ts = read_points(lidar)
        for angle, distance in scan_points:
            try:
                a = float(angle)
                d = float(distance)
            except Exception:
                continue
            if MIN_MM <= d <= MAX_MM:
                points.append((a, d))
        time.sleep(0.08)
    return points


def strongest_near_object_angle(points):
    """
    Pick the angle cluster with the most close readings.
    This works best when the user places a board/box/wall close to one side.
    """
    if not points:
        return None, {}

    # Favor close objects, but still require repeated readings.
    # score = count of nearby points weighted by closeness.
    candidates = []
    centers = [i * BIN_DEG for i in range(int(360 / BIN_DEG))]
    for center in centers:
        near = [(a, d) for a, d in points if abs(angle_diff_deg(a, center)) <= WINDOW_DEG]
        if len(near) < 10:
            continue
        distances = [d for _, d in near]
        close_score = sum(max(0.0, (MAX_MM - d) / MAX_MM) for d in distances)
        candidates.append((close_score, center, near))

    if not candidates:
        return None, {}

    candidates.sort(reverse=True, key=lambda x: x[0])
    score, rough_center, near = candidates[0]

    # Refine with only the closer half of readings in the winning window.
    distances = sorted(d for _, d in near)
    cutoff = distances[max(0, min(len(distances) - 1, len(distances) // 2))]
    close_angles = [a for a, d in near if d <= cutoff]
    refined = circular_mean_deg(close_angles) or rough_center

    stats = {
        "score": round(score, 2),
        "rough_center_deg": round(rough_center, 1),
        "refined_center_deg": round(refined, 1),
        "samples": len(near),
        "median_mm": round(statistics.median(distances), 1),
        "min_mm": round(min(distances), 1),
        "max_mm": round(max(distances), 1),
    }
    return refined, stats


def prompt_side(side_name):
    print("\n" + "=" * 70)
    print(f"CALIBRATE {side_name.upper()}")
    print("Place a flat box/cardboard/wall about 12-24 inches from that side.")
    print("Keep other close objects away if possible.")
    input("Press Enter to sample...")


def sample_side(lidar, side_name):
    prompt_side(side_name)
    points = collect_points(lidar)
    angle, stats = strongest_near_object_angle(points)
    print(f"Detected {side_name}: angle={angle:.1f} deg | stats={stats}")
    good = input("Use this angle? [Y/n] ").strip().lower()
    if good == "n":
        manual = float(input(f"Enter manual angle for {side_name}: ").strip())
        angle = wrap_deg(manual)
        stats["manual_override"] = True
    return angle, stats


def midpoint_angle(a, b):
    # Circular midpoint from a toward b by shortest path.
    return wrap_deg(a + angle_diff_deg(b, a) / 2.0)


def half_angle_between(a, b, default=15.0):
    gap = abs(angle_diff_deg(b, a))
    return round(max(8.0, min(25.0, gap / 2.0 * 0.65)), 1) if gap else default


def build_constants(front, back, left, right):
    front_left = midpoint_angle(front, left)
    front_right = midpoint_angle(front, right)
    back_left = midpoint_angle(back, left)
    back_right = midpoint_angle(back, right)

    return {
        "LIDAR_FRONT_CENTER_DEG": round(front, 1),
        "LIDAR_REAR_CENTER_DEG": round(back, 1),
        "LIDAR_FRONT_ZONE_HALF_ANGLE_DEG": 20.0,
        "LIDAR_REAR_ZONE_HALF_ANGLE_DEG": 15.0,
        "WALL_FOLLOW_FRONT_CENTER_DEG": round(front, 1),
        "WALL_FOLLOW_FRONT_HALF_ANGLE_DEG": 20.0,
        "WALL_FOLLOW_LEFT_CENTER_DEG": round(left, 1),
        "WALL_FOLLOW_LEFT_HALF_ANGLE_DEG": 18.0,
        "WALL_FOLLOW_RIGHT_CENTER_DEG": round(right, 1),
        "WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG": 18.0,
        "WALL_FOLLOW_FRONT_LEFT_CENTER_DEG": round(front_left, 1),
        "WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG": half_angle_between(front, left),
        "WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG": round(front_right, 1),
        "WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG": half_angle_between(front, right),
        "WALL_FOLLOW_BACK_LEFT_CENTER_DEG": round(back_left, 1),
        "WALL_FOLLOW_BACK_LEFT_HALF_ANGLE_DEG": half_angle_between(back, left),
        "WALL_FOLLOW_BACK_RIGHT_CENTER_DEG": round(back_right, 1),
        "WALL_FOLLOW_BACK_RIGHT_HALF_ANGLE_DEG": half_angle_between(back, right),
    }


def write_outputs(constants, raw):
    json_path = RESULT_DIR / "wall_follow_lidar_calibration.json"
    patch_path = RESULT_DIR / "wall_follow_lidar_config_patch.py"

    payload = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "constants": constants,
        "raw_samples": raw,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Paste/replace these values in config.py",
        "# Generated by calibration/wall_follow_lidar_calibration.py",
        "",
    ]
    for key, value in constants.items():
        lines.append(f"{key} = {value}")

    # These are required by the current wall_follow_service.py in the repo.
    lines += [
        "",
        "# Body offset compensation. Start at 0, then adjust after live checks.",
        "WALL_FOLLOW_LEFT_BODY_OFFSET_MM = 0.0",
        "WALL_FOLLOW_RIGHT_BODY_OFFSET_MM = 0.0",
        "",
        "# Steering/motor direction helpers used by wall_follow_service.py.",
        "WALL_FOLLOW_TURN_SIGN = 1.0",
        "WALL_FOLLOW_MIN_MOTOR_POWER = 0.20",
    ]
    patch_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\nWrote:")
    print(" ", json_path)
    print(" ", patch_path)
    print("\nSuggested config.py patch:\n")
    print(patch_path.read_text())


def main():
    lidar = get_lidar_service()
    if not wait_for_lidar(lidar):
        raise SystemExit("LiDAR did not start. Check USB port, power, and rplidar install.")

    raw = {}
    front, raw["front"] = sample_side(lidar, "front")
    left, raw["left"] = sample_side(lidar, "left")
    right, raw["right"] = sample_side(lidar, "right")
    back, raw["back"] = sample_side(lidar, "back")

    constants = build_constants(front=front, back=back, left=left, right=right)
    write_outputs(constants, raw)

    print("\nNext: run wall_follow_live_check.py to verify left/right/front/back live.")


if __name__ == "__main__":
    main()
