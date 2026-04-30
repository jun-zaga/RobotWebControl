from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = BASE_DIR / "dialog" / "scripts" / "demo_script.txt"

# -------------------------------------------------
# Drive / watchdog
# -------------------------------------------------

CMD_TIMEOUT_SEC = 1.0
WATCHDOG_PERIOD_SEC = 0.10

DRIVE_GAIN = 1.0

# -------------------------------------------------
# LiDAR
# -------------------------------------------------

LIDAR_PORT = "/dev/ttyUSB0"
LIDAR_BAUD = 115200


def wrap_deg(deg: float) -> float:
    return deg % 360.0


# Ignore robot body/mount false readings.
LIDAR_IGNORE_BELOW_MM = 220.0

# -------------------------------------------------
# Main LiDAR safety zones
# -------------------------------------------------

LIDAR_FRONT_CENTER_DEG = 135.0
LIDAR_REAR_CENTER_DEG = wrap_deg(LIDAR_FRONT_CENTER_DEG + 180.0)

LIDAR_FRONT_ZONE_HALF_ANGLE_DEG = 18.0
LIDAR_REAR_ZONE_HALF_ANGLE_DEG = 10.0

LIDAR_FRONT_STOP_MM = 430
LIDAR_REAR_STOP_MM = 300
LIDAR_STALE_SEC = 2.0

# -------------------------------------------------
# TTS
# -------------------------------------------------

TTS_DEFAULT_RATE = 120
TTS_DEFAULT_VOL = 1.0

# -------------------------------------------------
# Wall follower tuning
# -------------------------------------------------

WALL_FOLLOW_DEFAULT_SIDE = "right"

# Fallback target.
WALL_FOLLOW_TARGET_MM = 700.0

# Safer wall-follow distance:
# - left target is smaller because LiDAR is mounted on the left side
# - right target is larger because LiDAR is farther from the right wall
# Goal: roughly 10–14 inches from the wall instead of 6 inches.
WALL_FOLLOW_TARGET_LEFT_MM = 460.0
WALL_FOLLOW_TARGET_RIGHT_MM = 700.0

WALL_FOLLOW_TOLERANCE_MM = 75.0

# Larger because we are intentionally following farther from the wall.
WALL_FOLLOW_WALL_LOST_MM = 1700.0

# Robot convention: negative command = forward.
WALL_FOLLOW_FORWARD_SIGN = -1.0

# Robot needs high base speed to move.
WALL_FOLLOW_BASE_SPEED = 0.85

# Calmer steering so it does not overcorrect / spin around.
WALL_FOLLOW_TURN_GAIN = 0.50
WALL_FOLLOW_MAX_TURN = 0.50
WALL_FOLLOW_SEARCH_TURN = 0.50

# Corner behavior.
WALL_FOLLOW_CORNER_TURN = 0.35
WALL_FOLLOW_CORNER_OPEN_MM = 500.0
WALL_FOLLOW_CORNER_CLOSE_MM = 0.0

# Front obstacle tuning.
WALL_FOLLOW_FRONT_STOP_MM = 430.0
WALL_FOLLOW_FRONT_SIDE_DANGER_MM = 420.0

# Control loop speed.
WALL_FOLLOW_LOOP_HZ = 12.0

# Keep these 0 because left/right targets already include sensor offset.
WALL_FOLLOW_LEFT_BODY_OFFSET_MM = 0.0
WALL_FOLLOW_RIGHT_BODY_OFFSET_MM = 0.0

WALL_FOLLOW_MIN_MOTOR_POWER = 0.18

# -------------------------------------------------
# Wall follow LiDAR zones
# -------------------------------------------------

WALL_FOLLOW_FRONT_CENTER_DEG = 135.0
WALL_FOLLOW_FRONT_HALF_ANGLE_DEG = 18.0

WALL_FOLLOW_REAR_CENTER_DEG = 315.0
WALL_FOLLOW_REAR_HALF_ANGLE_DEG = 10.0

WALL_FOLLOW_LEFT_CENTER_DEG = 225.0
WALL_FOLLOW_LEFT_HALF_ANGLE_DEG = 25.0

WALL_FOLLOW_RIGHT_CENTER_DEG = 45.0
WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG = 25.0

WALL_FOLLOW_FRONT_LEFT_CENTER_DEG = 180.0
WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG = 20.0

WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG = 90.0
WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG = 20.0

WALL_FOLLOW_BACK_LEFT_CENTER_DEG = 270.0
WALL_FOLLOW_BACK_LEFT_HALF_ANGLE_DEG = 10.0

WALL_FOLLOW_BACK_RIGHT_CENTER_DEG = 0.0
WALL_FOLLOW_BACK_RIGHT_HALF_ANGLE_DEG = 10.0

# -------------------------------------------------
# Greeter FSM / navigation tuning
# currently unused
# -------------------------------------------------

# GREETER_HUMAN_DETECT_MM = 900
# GREETER_FRONT_OBSTACLE_MM = 450

# GREETER_WALL_VISIBLE_MM = 1200
# GREETER_OPENING_MM = 1600

# GREETER_TURN_180_SEC = 1.8
# GREETER_TURN_90_SEC = 0.85
# GREETER_FINAL_FORWARD_SEC = 5.0

# GREETER_BASE_SPEED = 0.22
# GREETER_TURN_SPEED = 0.25
# GREETER_WALL_FOLLOW_KP = 0.00035

# GREETER_TARGET_SIDE_MM = 550
# GREETER_CENTER_DEADBAND_MM = 80
# GREETER_STATUS_POLL_SEC = 0.25