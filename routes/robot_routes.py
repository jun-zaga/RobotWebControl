from flask import Blueprint, current_app, jsonify, request


def create_robot_blueprint():
    bp = Blueprint("robot", __name__)

    @bp.post("/api/drive")
    def api_drive():
        robot = current_app.config["services"]["robot"]
        data = request.get_json(silent=True) or {}

        try:
            return jsonify(robot.drive(data.get("left"), data.get("right")))
        except ValueError as e:
            return jsonify(ok=False, error=str(e)), 400

    @bp.post("/api/stop")
    def api_stop():
        services = current_app.config["services"]
        robot = services["robot"]
        runner = services["runner"]
        tts = services["tts"]
        dialog = services["dialog"]

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

    return bp