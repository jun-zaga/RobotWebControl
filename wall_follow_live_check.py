#!/usr/bin/env python3
"""
Live wall-follow LiDAR zone checker.

Run after pasting the constants from wall_follow_lidar_calibration.py into config.py.
It prints front/back/left/right and wall-follow side zones so you can verify
that left really means robot-left and right really means robot-right.

Run from repo root:
    python3 calibration/wall_follow_live_check.py
"""

import time
from app import app
from config import *

lidar = app.config["services"]["lidar"]
wall = app.config["services"].get("wall_follow")


def zone(center, half):
    try:
        return lidar.get_zone_min(center, half)
    except Exception:
        return None


def fmt(v):
    if v is None:
        return "----"
    return f"{float(v):6.0f}"


def main():
    print("Waiting for LiDAR...")
    while True:
        s = lidar.get_status()
        if s.get("status") == "running" and s.get("scan_points", 0) > 20:
            break
        print("status=", s.get("status"), "points=", s.get("scan_points"))
        time.sleep(1.0)

    print("\nMove your hand/cardboard near each side of the robot.")
    print("The matching column should drop first. Ctrl+C to stop.\n")

    while True:
        front = zone(WALL_FOLLOW_FRONT_CENTER_DEG, WALL_FOLLOW_FRONT_HALF_ANGLE_DEG)
        left = zone(WALL_FOLLOW_LEFT_CENTER_DEG, WALL_FOLLOW_LEFT_HALF_ANGLE_DEG)
        right = zone(WALL_FOLLOW_RIGHT_CENTER_DEG, WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG)
        rear = zone(LIDAR_REAR_CENTER_DEG, LIDAR_REAR_ZONE_HALF_ANGLE_DEG)

        fl = zone(WALL_FOLLOW_FRONT_LEFT_CENTER_DEG, WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG)
        fr = zone(WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG, WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG)

        bl = None
        br = None
        if "WALL_FOLLOW_BACK_LEFT_CENTER_DEG" in globals():
            bl = zone(WALL_FOLLOW_BACK_LEFT_CENTER_DEG, WALL_FOLLOW_BACK_LEFT_HALF_ANGLE_DEG)
        if "WALL_FOLLOW_BACK_RIGHT_CENTER_DEG" in globals():
            br = zone(WALL_FOLLOW_BACK_RIGHT_CENTER_DEG, WALL_FOLLOW_BACK_RIGHT_HALF_ANGLE_DEG)

        line = (
            f"front={fmt(front)}  back={fmt(rear)}  "
            f"left={fmt(left)}  right={fmt(right)}  "
            f"frontL={fmt(fl)}  frontR={fmt(fr)}  backL={fmt(bl)}  backR={fmt(br)}"
        )
        if wall is not None:
            wz = wall.get_status().get("last_zone_snapshot", {})
            if wz:
                line += f"  | wall_side={fmt(wz.get('side_mm'))} source={wz.get('side_source')}"
        print(line, flush=True)
        time.sleep(0.35)


if __name__ == "__main__":
    main()
