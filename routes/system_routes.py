import time
from flask import Blueprint, current_app, jsonify


def create_system_blueprint():
    bp = Blueprint("system", __name__)

    @bp.get("/")
    def root():
        return current_app.send_static_file("index.html")

    @bp.get("/health")
    def health():
        return jsonify(ok=True, time=time.time())

    @bp.get("/api/lidar")
    def api_lidar():
        lidar = current_app.config["services"]["lidar"]
        return jsonify(lidar.get_status())

    return bp