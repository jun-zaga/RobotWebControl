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


# -------------------------------------------------
# Main LiDAR safety zones
# Robot front is currently at 270 degrees.
# -------------------------------------------------

LIDAR_FRONT_CENTER_DEG = 270.0
LIDAR_REAR_CENTER_DEG = wrap_deg(LIDAR_FRONT_CENTER_DEG + 180.0)

LIDAR_FRONT_ZONE_HALF_ANGLE_DEG = 20.0
LIDAR_REAR_ZONE_HALF_ANGLE_DEG = 15.0

LIDAR_FRONT_STOP_MM = 300
LIDAR_REAR_STOP_MM = 1830
LIDAR_STALE_SEC = 2.0

# -------------------------------------------------
# TTS
# -------------------------------------------------

TTS_DEFAULT_RATE = 120
TTS_DEFAULT_VOL = 1.0

# -------------------------------------------------
# Wall follower tuning
# Target: about 6 inches / 170 mm from wall.
# Webapp should only choose left/right side.
# Everything else stays fixed here.
# -------------------------------------------------

WALL_FOLLOW_DEFAULT_SIDE = "left"

# Distance behavior

WALL_FOLLOW_TARGET_MM = 170
WALL_FOLLOW_TOLERANCE_MM = 25
WALL_FOLLOW_WALL_LOST_MM = 700

WALL_FOLLOW_BASE_SPEED = 0.9

# Motion behavior
WALL_FOLLOW_MIN_MOTOR_POWER = 0.80
WALL_FOLLOW_MAX_TURN = 0.20
WALL_FOLLOW_TURN_GAIN = .8
WALL_FOLLOW_SEARCH_TURN = 0.45
WALL_FOLLOW_FRONT_STOP_MM = 300

# Loop / correction behavior
WALL_FOLLOW_LOOP_HZ = 12
WALL_FOLLOW_FORWARD_SIGN = -1
WALL_FOLLOW_TURN_SIGN = 1

# Optional body offsets / motor floor
WALL_FOLLOW_LEFT_BODY_OFFSET_MM = 0
WALL_FOLLOW_RIGHT_BODY_OFFSET_MM = 0

# Less aggressive than before.
WALL_FOLLOW_BASE_SPEED = 1.50
WALL_FOLLOW_MIN_MOTOR_POWER = 0.65
WALL_FOLLOW_MAX_TURN = 0.18
WALL_FOLLOW_TURN_GAIN = 0.40
WALL_FOLLOW_SEARCH_TURN = 0.16

# Deadband to prevent twitching.
WALL_FOLLOW_TOLERANCE_MM = 45.0

# Minimum wheel command that overcomes static friction.

# Control loop frequency.
WALL_FOLLOW_LOOP_HZ = 12.0

# If side distance is larger than this, assume wall is lost.
WALL_FOLLOW_WALL_LOST_MM = 900.0


# -------------------------------------------------
# Wall follow LiDAR zones
#
# These match your current wall_follow.py:
#   front      = 270 degrees
#   left side  = 180 degrees
#   right side = 0 degrees
# -------------------------------------------------

WALL_FOLLOW_FRONT_CENTER_DEG = LIDAR_FRONT_CENTER_DEG
WALL_FOLLOW_FRONT_HALF_ANGLE_DEG = 20.0

WALL_FOLLOW_LEFT_CENTER_DEG = 225.0
WALL_FOLLOW_LEFT_HALF_ANGLE_DEG = 12.0

WALL_FOLLOW_FRONT_LEFT_CENTER_DEG = 245.0
WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG = 10.0

WALL_FOLLOW_BACK_LEFT_CENTER_DEG = 205.0
WALL_FOLLOW_BACK_LEFT_HALF_ANGLE_DEG = 10.0

WALL_FOLLOW_RIGHT_CENTER_DEG = 315.0
WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG = 12.0

WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG = 295.0
WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG = 10.0

WALL_FOLLOW_BACK_RIGHT_CENTER_DEG = 335.0
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
