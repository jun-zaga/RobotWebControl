import json
import time
from pathlib import Path


class MapBuilderService:
    def __init__(self, lidar_service, robot_service):
        self.lidar = lidar_service
        self.robot = robot_service

        self.points = []
        self.steps = []
        self.output_path = Path("stuart_greeter_map.json")

    def _zone_min(self, center_deg, half_angle):
        try:
            return self.lidar.get_zone_min(float(center_deg), float(half_angle))
        except Exception:
            return None

    def snapshot(self):
        return {
            "timestamp": time.time(),
            "greeter_zones": {
                "front_mm": self._zone_min(0.0, 20.0),
                "left_mm": self._zone_min(225.0, 25.0),
                "right_mm": self._zone_min(45.0, 25.0),
            },
            "scan_8": {
                "0": self._zone_min(0.0, 15.0),
                "45": self._zone_min(45.0, 15.0),
                "90": self._zone_min(90.0, 15.0),
                "135": self._zone_min(135.0, 15.0),
                "180": self._zone_min(180.0, 15.0),
                "225": self._zone_min(225.0, 15.0),
                "270": self._zone_min(270.0, 15.0),
                "315": self._zone_min(315.0, 15.0),
            },
        }

    def drive(self, left, right, label="manual_drive"):
        try:
            left = float(left)
            right = float(right)
        except Exception:
            return {"ok": False, "error": "left and right must be numbers"}

        drive_result = self.robot.drive(left, right)

        step = {
            "index": len(self.steps) + 1,
            "type": "drive",
            "label": label,
            "left": left,
            "right": right,
            "timestamp": time.time(),
            "snapshot": self.snapshot(),
        }

        self.steps.append(step)

        return {
            "ok": True,
            "drive_result": drive_result,
            "step": step,
            "step_count": len(self.steps),
        }

    def stop(self, label="manual_stop"):
        drive_result = self.robot.drive(0, 0)

        step = {
            "index": len(self.steps) + 1,
            "type": "stop",
            "label": label,
            "left": 0,
            "right": 0,
            "timestamp": time.time(),
            "snapshot": self.snapshot(),
        }

        self.steps.append(step)

        return {
            "ok": True,
            "drive_result": drive_result,
            "step": step,
            "step_count": len(self.steps),
        }

    def mark_point(self, label, notes=""):
        label = str(label or "").strip()
        notes = str(notes or "").strip()

        if not label:
            return {"ok": False, "error": "label is required"}

        point = {
            "index": len(self.points) + 1,
            "label": label,
            "notes": notes,
            "timestamp": time.time(),
            "step_index": len(self.steps),
            "snapshot": self.snapshot(),
        }

        self.points.append(point)

        return {
            "ok": True,
            "point": point,
            "points": self.points,
            "steps": self.steps,
        }

    def clear(self):
        self.points = []
        self.steps = []

        return {
            "ok": True,
            "points": self.points,
            "steps": self.steps,
        }

    def status(self):
        return {
            "ok": True,
            "point_count": len(self.points),
            "step_count": len(self.steps),
            "points": self.points,
            "steps": self.steps[-25:],
            "snapshot": self.snapshot(),
            "output_path": str(self.output_path),
        }

    def save(self):
        data = {
            "name": "stuart_greeter_map",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "notes": [
                "front angle is 0 degrees",
                "left greeter angle is 225 degrees",
                "right greeter angle is 45 degrees",
                "measurements are LiDAR millimeters",
                "points are labeled important locations",
                "steps are the drive commands used between points",
            ],
            "points": self.points,
            "steps": self.steps,
        }

        self.output_path.write_text(json.dumps(data, indent=2))

        return {
            "ok": True,
            "saved_to": str(self.output_path),
            "point_count": len(self.points),
            "step_count": len(self.steps),
            "map": data,
        }