from flask import Blueprint, current_app, jsonify, request


def create_tts_blueprint():
    bp = Blueprint("tts", __name__)

    @bp.get("/api/voices")
    def api_voices():
        tts = current_app.config["services"]["tts"]
        return jsonify(ok=True, voices=tts.list_voices())

    @bp.post("/api/say")
    def api_say():
        tts = current_app.config["services"]["tts"]
        data = request.get_json(silent=True) or {}

        text = (data.get("text") or data.get("custom") or "").strip()
        if not text:
            return jsonify(ok=False, error="text required"), 400

        ok = tts.say(
            text=text,
            voice=data.get("voice"),
            rate=data.get("rate"),
            volume=data.get("volume"),
        )
        return jsonify(ok=ok)

    @bp.post("/api/tts_stop")
    def api_tts_stop():
        tts = current_app.config["services"]["tts"]
        tts.stop()
        return jsonify(ok=True)

    return bp