from flask import Blueprint, current_app, jsonify, request


def create_map_blueprint():
    bp = Blueprint("map_builder", __name__)

    def get_map_builder():
        services = current_app.config["services"]
        return services.get("map_builder")

    @bp.get("/api/map/status")
    def api_map_status():
        mapper = get_map_builder()

        if mapper is None:
            return jsonify(ok=False, error="map builder service missing"), 500

        return jsonify(mapper.status())

    @bp.post("/api/map/drive")
    def api_map_drive():
        mapper = get_map_builder()

        if mapper is None:
            return jsonify(ok=False, error="map builder service missing"), 500

        data = request.get_json(silent=True) or {}

        left = data.get("left", 0)
        right = data.get("right", 0)
        label = data.get("label", "manual_drive")

        return jsonify(mapper.drive(left, right, label))

    @bp.post("/api/map/stop")
    def api_map_stop():
        mapper = get_map_builder()

        if mapper is None:
            return jsonify(ok=False, error="map builder service missing"), 500

        data = request.get_json(silent=True) or {}
        label = data.get("label", "manual_stop")

        return jsonify(mapper.stop(label))

    @bp.post("/api/map/mark")
    def api_map_mark():
        mapper = get_map_builder()

        if mapper is None:
            return jsonify(ok=False, error="map builder service missing"), 500

        data = request.get_json(silent=True) or {}

        label = data.get("label", "")
        notes = data.get("notes", "")

        return jsonify(mapper.mark_point(label, notes))

    @bp.post("/api/map/save")
    def api_map_save():
        mapper = get_map_builder()

        if mapper is None:
            return jsonify(ok=False, error="map builder service missing"), 500

        return jsonify(mapper.save())

    @bp.post("/api/map/clear")
    def api_map_clear():
        mapper = get_map_builder()

        if mapper is None:
            return jsonify(ok=False, error="map builder service missing"), 500

        return jsonify(mapper.clear())

    return bp