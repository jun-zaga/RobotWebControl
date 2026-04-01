from flask import Blueprint, current_app, jsonify, request


def create_dialog_blueprint():
    bp = Blueprint("dialog", __name__)

    @bp.post("/api/dialog")
    def api_dialog():
        dialog = current_app.config["services"]["dialog"]
        data = request.get_json(silent=True) or {}
        text = (data.get("text") or "").strip()

        if not text:
            return jsonify(ok=False, error="empty text"), 400

        return jsonify(dialog.process_text(text))

    @bp.post("/api/run_script")
    def api_run_script():
        dialog = current_app.config["services"]["dialog"]
        return jsonify(dialog.run_script_demo())

    return bp