from flask import Blueprint, current_app, jsonify, request


def create_greeter_blueprint():
    bp = Blueprint("greeter", __name__)

    @bp.post("/api/greeter/start")
    def api_greeter_start():
        greeter = current_app.config["services"].get("greeter")

        if greeter is None:
            return jsonify(ok=False, error="greeter service missing"), 500

        return jsonify(greeter.start())

    @bp.post("/api/greeter/stop")
    def api_greeter_stop():
        greeter = current_app.config["services"].get("greeter")

        if greeter is None:
            return jsonify(ok=False, error="greeter service missing"), 500

        return jsonify(greeter.stop("api stop"))

    @bp.get("/api/greeter/status")
    def api_greeter_status():
        greeter = current_app.config["services"].get("greeter")

        if greeter is None:
            return jsonify(ok=False, error="greeter service missing"), 500

        return jsonify(greeter.status())

    @bp.post("/api/greeter/test_destination")
    def api_greeter_test_destination():
        """
        Optional typed fallback for testing.
        Body:
        {
            "destination": "bathroom"
        }
        or
        {
            "destination": "robot lab"
        }
        """
        greeter = current_app.config["services"].get("greeter")

        if greeter is None:
            return jsonify(ok=False, error="greeter service missing"), 500

        data = request.get_json(silent=True) or {}
        destination = data.get("destination", "")

        return jsonify(greeter.set_test_destination(destination))

    return bp