from flask import Flask

import hardware.robot_control as rc
from actions.action_library import ACTIONS
from actions.action_runner import ActionRunner
from config import SCRIPT_PATH
from dialog.dialog_engine import DialogEngine

from routes.dialog_routes import create_dialog_blueprint
from routes.robot_routes import create_robot_blueprint
from routes.system_routes import create_system_blueprint
from routes.tts_routes import create_tts_blueprint
from routes.greeter_routes import create_greeter_blueprint
from routes.map_routes import create_map_blueprint

from services.dialog_service import DialogService
from services.lidar_service import LidarService
from services.robot_service import RobotService
from services.safety_service import SafetyService
from services.tts_service import TTSService
from services.wall_follow_service import WallFollowService
from services.greeter_service import GreeterService
from services.map_builder_service import MapBuilderService


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")

    engine = DialogEngine(seed=7)
    engine.load_script(str(SCRIPT_PATH))

    safety = SafetyService(rc)
    tts = TTSService()
    lidar = LidarService()
    robot = RobotService(rc=rc, lidar_service=lidar, safety_service=safety)
    wall_follow = WallFollowService(robot_service=robot, lidar_service=lidar)

    greeter = GreeterService(
        robot_service=robot,
        lidar_service=lidar,
        tts_service=tts,
    )

    map_builder = MapBuilderService(
        lidar_service=lidar,
        robot_service=robot,
    )

    def on_action_state_change(name: str):
        print(f"[STATE] -> {name}", flush=True)
        safety.set_action_active(name == "EXEC_ACTIONS")
        safety.update_last_cmd_ts()

    runner = ActionRunner(
        rc=rc,
        actions=ACTIONS,
        on_state_change=on_action_state_change,
    )

    dialog = DialogService(
        engine=engine,
        runner=runner,
        tts=tts,
        rc=rc,
        safety=safety,
    )

    app.config["services"] = {
        "robot": robot,
        "dialog": dialog,
        "tts": tts,
        "lidar": lidar,
        "safety": safety,
        "runner": runner,
        "wall_follow": wall_follow,
        "greeter": greeter,
        "map_builder": map_builder,
    }

    app.register_blueprint(create_robot_blueprint())
    app.register_blueprint(create_dialog_blueprint())
    app.register_blueprint(create_tts_blueprint())
    app.register_blueprint(create_system_blueprint())
    app.register_blueprint(create_greeter_blueprint())
    app.register_blueprint(create_map_blueprint())

    safety.start()
    lidar.start()
    wall_follow.start()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)