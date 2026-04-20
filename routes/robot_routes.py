from flask import Blueprint, current_app, jsonify, request


def create_robot_blueprint():
    bp = Blueprint("robot", __name__)

    @bp.post("/api/drive")
    def api_drive():
        services = current_app.config["services"]
        robot = services["robot"]
        wall = services.get("wall_follow")
        data = request.get_json(silent=True) or {}

        left = data.get("left")
        right = data.get("right")

        is_manual_motion = False
        try:
            l = float(left)
            r = float(right)
            is_manual_motion = abs(l) > 0.02 or abs(r) > 0.02
        except Exception:
            pass

        if wall is not None and wall.is_enabled() and is_manual_motion:
            wall.disable(stop_robot=False, reason="manual drive override")

        try:
            return jsonify(robot.drive(left, right))
        except ValueError as e:
            return jsonify(ok=False, error=str(e)), 400

    @bp.post("/api/stop")
    def api_stop():
        services = current_app.config["services"]
        robot = services["robot"]
        runner = services["runner"]
        tts = services["tts"]
        dialog = services["dialog"]
        wall = services.get("wall_follow")

        if wall is not None:
            wall.disable(stop_robot=False, reason="manual stop")

        robot.stop()
        runner.interrupt_all()
        tts.stop()
        dialog.engine.reset_scope()
        return jsonify(ok=True)

    @bp.post("/api/servo")
    def api_servo():
        robot = current_app.config["services"]["robot"]
        data = request.get_json(silent=True) or {}
        axis = (data.get("axis") or "").strip().lower()
        value = data.get("value")

        try:
            return jsonify(robot.set_servo_axis(axis, value))
        except ValueError as e:
            return jsonify(ok=False, error=str(e)), 400

    @bp.post("/api/head")
    def api_head():
        robot = current_app.config["services"]["robot"]
        data = request.get_json(silent=True) or {}

        try:
            return jsonify(robot.set_head(pan=data.get("pan"), tilt=data.get("tilt")))
        except ValueError as e:
            return jsonify(ok=False, error=str(e)), 400

    @bp.post("/api/waist")
    def api_waist():
        robot = current_app.config["services"]["robot"]
        data = request.get_json(silent=True) or {}

        try:
            return jsonify(robot.set_waist(data.get("pos")))
        except ValueError as e:
            return jsonify(ok=False, error=str(e)), 400

    @bp.post("/api/arms")
    def api_arms():
        robot = current_app.config["services"]["robot"]
        data = request.get_json(silent=True) or {}

        try:
            return jsonify(robot.set_arms(data))
        except ValueError as e:
            return jsonify(ok=False, error=str(e)), 400

    @bp.post("/api/pose")
    def api_pose():
        robot = current_app.config["services"]["robot"]
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()

        if not name:
            return jsonify(ok=False, error="name required"), 400

        try:
            return jsonify(robot.pose(name))
        except ValueError as e:
            return jsonify(ok=False, error=str(e)), 400

    @bp.get("/api/wall_follow")
    def api_wall_follow_status():
        wall = current_app.config["services"].get("wall_follow")
        if wall is None:
            return jsonify(ok=False, error="wall_follow service missing"), 500
        return jsonify(wall.get_status())

    @bp.post("/api/wall_follow/start")
    def api_wall_follow_start():
        wall = current_app.config["services"].get("wall_follow")
        if wall is None:
            return jsonify(ok=False, error="wall_follow service missing"), 500

        data = request.get_json(silent=True) or {}
        try:
            wall.set_params(data)
            return jsonify(
                wall.enable(
                    side=data.get("side"),
                    target_mm=data.get("target_mm"),
                    tolerance_mm=data.get("tolerance_mm"),
                )
            )
        except ValueError as e:
            return jsonify(ok=False, error=str(e)), 400

    @bp.post("/api/wall_follow/stop")
    def api_wall_follow_stop():
        wall = current_app.config["services"].get("wall_follow")
        if wall is None:
            return jsonify(ok=False, error="wall_follow service missing"), 500
        return jsonify(wall.disable(stop_robot=True, reason="api stop"))

    @bp.post("/api/wall_follow/config")
    def api_wall_follow_config():
        wall = current_app.config["services"].get("wall_follow")
        if wall is None:
            return jsonify(ok=False, error="wall_follow service missing"), 500

        data = request.get_json(silent=True) or {}
        try:
            return jsonify(wall.set_params(data))
        except ValueError as e:
            return jsonify(ok=False, error=str(e)), 400

    return bp