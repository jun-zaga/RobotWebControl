from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = BASE_DIR / "dialog" / "scripts" / "demo_script.txt"

CMD_TIMEOUT_SEC = 1.0
WATCHDOG_PERIOD_SEC = 0.10

DRIVE_GAIN = 1.0

LIDAR_PORT = "/dev/ttyUSB0"
LIDAR_BAUD = 115200


def wrap_deg(deg: float) -> float:
    return deg % 360.0


# Main lidar safety zones
LIDAR_FRONT_CENTER_DEG = 270.0
LIDAR_REAR_CENTER_DEG = (LIDAR_FRONT_CENTER_DEG + 180.0) % 360.0

LIDAR_FRONT_ZONE_HALF_ANGLE_DEG = 20.0
LIDAR_REAR_ZONE_HALF_ANGLE_DEG = 15.0

LIDAR_FRONT_STOP_MM = 380
LIDAR_REAR_STOP_MM = 1830
LIDAR_STALE_SEC = 2.0

TTS_DEFAULT_RATE = 120
TTS_DEFAULT_VOL = 1.0


# -------------------------------------------------
# Wall follower tuning
# -------------------------------------------------

# Start with left wall following since that is what we are tuning first.
WALL_FOLLOW_DEFAULT_SIDE = "left"

# Target wall distance.
# Your debug log showed the robot around ~355 mm from the left wall,
# with target near ~315 mm, so keep this as the starting target.
WALL_FOLLOW_TARGET_MM = 315.0

# Body offsets. Keep left at 0 unless your left side measurement includes robot body width.
WALL_FOLLOW_RIGHT_BODY_OFFSET_MM = 340.0
WALL_FOLLOW_LEFT_BODY_OFFSET_MM = 0.0

# Obstacle avoidance.
WALL_FOLLOW_FRONT_STOP_MM = 450.0

# Motor/control tuning.
# Your servos use negative values for forward motion.
WALL_FOLLOW_FORWARD_SIGN = -1.0

# Flip this to -1.0 only if corrections steer the wrong way.
WALL_FOLLOW_TURN_SIGN = 1.0

# Less aggressive than before.
WALL_FOLLOW_BASE_SPEED = 1.50
WALL_FOLLOW_MIN_MOTOR_POWER = 1.0
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
# Wall follow zones
# IMPORTANT:
# These are relative to the actual robot front so they stay correct
# when the lidar is rotated.
# -------------------------------------------------

WALL_FOLLOW_FRONT_CENTER_DEG = LIDAR_FRONT_CENTER_DEG
WALL_FOLLOW_FRONT_HALF_ANGLE_DEG = 20.0

WALL_FOLLOW_RIGHT_CENTER_DEG = wrap_deg(LIDAR_FRONT_CENTER_DEG - 90.0)
WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG = 20.0

WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG = wrap_deg(LIDAR_FRONT_CENTER_DEG - 45.0)
WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG = 25.0

WALL_FOLLOW_BACK_RIGHT_CENTER_DEG = wrap_deg(LIDAR_FRONT_CENTER_DEG - 115.0)
WALL_FOLLOW_BACK_RIGHT_HALF_ANGLE_DEG = 20.0

WALL_FOLLOW_LEFT_CENTER_DEG = wrap_deg(LIDAR_FRONT_CENTER_DEG + 90.0)
WALL_FOLLOW_LEFT_HALF_ANGLE_DEG = 20.0

WALL_FOLLOW_FRONT_LEFT_CENTER_DEG = wrap_deg(LIDAR_FRONT_CENTER_DEG + 45.0)
WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG = 25.0

WALL_FOLLOW_BACK_LEFT_CENTER_DEG = wrap_deg(LIDAR_FRONT_CENTER_DEG + 115.0)
WALL_FOLLOW_BACK_LEFT_HALF_ANGLE_DEG = 20.0



# # Greeter FSM / navigation tuning
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
