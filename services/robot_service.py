from config import DRIVE_GAIN


class RobotService:
    def __init__(self, rc, lidar_service, safety_service):
        self.rc = rc
        self.lidar = lidar_service
        self.safety = safety_service

    @staticmethod
    def clamp(x, lo, hi):
        return max(lo, min(hi, x))

    @staticmethod
    def is_number(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    def drive(self, left, right, bypass_safety=False):
        if not (self.is_number(left) and self.is_number(right)):
            raise ValueError("left and right must be numbers")

        l = float(self.clamp(float(left) * DRIVE_GAIN, -1.0, 1.0))
        r = float(self.clamp(float(right) * DRIVE_GAIN, -1.0, 1.0))

        if bypass_safety:
            safety = {
                "status": "bypassed",
                "mode": "bypassed",
                "front_min_mm": None,
                "rear_min_mm": None,
                "stale": False,
            }

            print(
                f"[DRIVE] req=({l:.2f},{r:.2f}) safety=bypassed",
                flush=True,
            )

            self.rc.drive(l, r)

            if self.safety is not None:
                self.safety.update_last_cmd_ts()

            return {
                "ok": True,
                "l": l,
                "r": r,
                "safety": safety,
            }

        safe_l, safe_r, safety = self.lidar.apply_safety(l, r)

        print(
            f"[DRIVE] req=({l:.2f},{r:.2f}) safe=({safe_l:.2f},{safe_r:.2f}) "
            f"mode={safety.get('mode')} front={safety.get('front_min_mm')} "
            f"rear={safety.get('rear_min_mm')} stale={safety.get('stale')}",
            flush=True,
        )

        self.rc.drive(safe_l, safe_r)

        if self.safety is not None:
            self.safety.update_last_cmd_ts()

        return {
            "ok": True,
            "l": safe_l,
            "r": safe_r,
            "safety": safety,
        }

    def stop(self):
        self.rc.stop()
        self.safety.update_last_cmd_ts()
        return {"ok": True}

    def set_servo_axis(self, axis, value):
        if not self.is_number(value):
            raise ValueError("value must be a number")

        v = float(self.clamp(value, 0.0, 1.0))

        if axis == "pan":
            self.rc.head_pan(v)
        elif axis == "tilt":
            self.rc.head_tilt(v)
        elif axis == "waist":
            self.rc.waist(v)
        else:
            raise ValueError("unknown axis")

        self.safety.update_last_cmd_ts()
        return {"ok": True}

    def set_head(self, pan=None, tilt=None):
        if pan is not None:
            if not self.is_number(pan):
                raise ValueError("pan must be a number")
            self.rc.head_pan(float(self.clamp(pan, 0.0, 1.0)))

        if tilt is not None:
            if not self.is_number(tilt):
                raise ValueError("tilt must be a number")
            self.rc.head_tilt(float(self.clamp(tilt, 0.0, 1.0)))

        self.safety.update_last_cmd_ts()
        return {"ok": True}

    def set_waist(self, pos):
        if not self.is_number(pos):
            raise ValueError("pos must be a number")
        self.rc.waist(float(self.clamp(pos, 0.0, 1.0)))
        self.safety.update_last_cmd_ts()
        return {"ok": True}

    def set_arms(self, data):
        def is01(x):
            return self.is_number(x) and 0.0 <= float(x) <= 1.0

        def clamp01(x):
            return float(self.clamp(float(x), 0.0, 1.0))

        lj = data.get("left_joints")
        rj = data.get("right_joints")

        if lj is None:
            lj = [data.get(f"left_{i}") for i in range(1, 7)]
        if rj is None:
            rj = [data.get(f"right_{i}") for i in range(1, 7)]

        if all(v is None for v in lj):
            lj = [None] * 6
            lj[0] = data.get("left_shoulder")
            lj[1] = data.get("left_elbow")
            lj[5] = data.get("left_hand")

        if all(v is None for v in rj):
            rj = [None] * 6
            rj[0] = data.get("right_shoulder")
            rj[1] = data.get("right_elbow")
            rj[5] = data.get("right_hand")

        for i in range(6):
            v = lj[i]
            if v is not None:
                if not is01(v):
                    raise ValueError("arm values must be numbers 0..1")
                self.rc.left_joint(i + 1, clamp01(v))

        for i in range(6):
            v = rj[i]
            if v is not None:
                if not is01(v):
                    raise ValueError("arm values must be numbers 0..1")
                self.rc.right_joint(i + 1, clamp01(v))

        self.safety.update_last_cmd_ts()
        return {"ok": True}

    def pose(self, name):
        pose_data = self.rc.pose(name)
        if not pose_data:
            raise ValueError(f"unknown pose: {name}")

        self.safety.update_last_cmd_ts()

        resp = {"ok": True, "name": name}
        if pose_data.get("left") is not None:
            resp["left_joints"] = pose_data["left"]
        if pose_data.get("right") is not None:
            resp["right_joints"] = pose_data["right"]
        return resp
