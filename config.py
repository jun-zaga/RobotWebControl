from pathlib import Path

# Folder where this config.py file lives.
BASE_DIR = Path(__file__).resolve().parent

# Path to the dialog script used by the robot's speech/dialog system.
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

WALL_FOLLOW_TARGET_MM = 700.0
WALL_FOLLOW_TARGET_LEFT_MM = 460.0
WALL_FOLLOW_TARGET_RIGHT_MM = 700.0

WALL_FOLLOW_TOLERANCE_MM = 50
WALL_FOLLOW_WALL_LOST_MM = 1700.0

# Your robot uses negative wheel commands as forward.
WALL_FOLLOW_FORWARD_SIGN = -1.0

WALL_FOLLOW_BASE_SPEED = 0.50
WALL_FOLLOW_TURN_GAIN = 0.15
WALL_FOLLOW_MAX_TURN = 0.08
WALL_FOLLOW_SEARCH_TURN = 0.35

WALL_FOLLOW_CORNER_OPEN_MM = 400.0
WALL_FOLLOW_CORNER_TURN = 0.50
WALL_FOLLOW_CORNER_CLOSE_MM = 0.0

WALL_FOLLOW_FRONT_STOP_MM = 430.0
WALL_FOLLOW_FRONT_SIDE_DANGER_MM = 420.0

WALL_FOLLOW_LOOP_HZ = 12.0

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
# Obstacle handling
# -------------------------------------------------

WALL_FOLLOW_OBSTACLE_STOP_MM = 500.0
WALL_FOLLOW_OBSTACLE_STOP_SEC = 0.25
WALL_FOLLOW_OBSTACLE_BACKUP_SEC = 0.40
WALL_FOLLOW_OBSTACLE_PIVOT_SEC = 0.45

WALL_FOLLOW_OBSTACLE_BACKUP_SPEED = 0.45
WALL_FOLLOW_OBSTACLE_PIVOT_POWER = 0.75

# -------------------------------------------------
# Final Project Greeter / Person Detection
# -------------------------------------------------

GREETER_HUMAN_DETECT_MM = 1400.0
GREETER_HUMAN_MIN_MM = 250.0
GREETER_HUMAN_SEEN_REQUIRED = 2

# Stuart needs strong power to move.
GREETER_BASE_SPEED = 0.80
GREETER_TURN_SPEED = 0.80

# -------------------------------------------------
# Greeter LiDAR zones
# -------------------------------------------------

# Front / human detection direction.
GREETER_FRONT_CENTER_DEG = 0.0
GREETER_FRONT_HALF_ANGLE_DEG = 20.0

# Basic side readings.
GREETER_LEFT_CENTER_DEG = 225.0
GREETER_LEFT_HALF_ANGLE_DEG = 25.0

GREETER_RIGHT_CENTER_DEG = 45.0
GREETER_RIGHT_HALF_ANGLE_DEG = 25.0

# -------------------------------------------------
# 180 turn tuning
# -------------------------------------------------

# If under-turns, raise toward 2.70–3.00.
# If over-turns, lower toward 2.10.
GREETER_TURN_180_SEC = 2.40

# -------------------------------------------------
# Body alignment using right wall
# -------------------------------------------------

# Front-right and rear-right slices for checking if body is parallel.
GREETER_RIGHT_FRONT_CENTER_DEG = 35.0
GREETER_RIGHT_REAR_CENTER_DEG = 70.0
GREETER_RIGHT_ALIGN_HALF_ANGLE_DEG = 10.0

# Body alignment is good enough for now, so keep this forgiving.
GREETER_BODY_ALIGN_TOLERANCE_MM = 250.0
GREETER_BODY_ALIGN_REQUIRED = 3

# Slow pivot correction before/after centering.
GREETER_BODY_ALIGN_TURN_SPEED = 0.35
GREETER_BODY_ALIGN_TIMEOUT_SEC = 4.0

# Current best direction from testing.
GREETER_BODY_ALIGN_SIGN = -1.0

# LiDAR is about 4 inches from body center.
GREETER_LIDAR_BODY_OFFSET_MM = 100.0

# -------------------------------------------------
# Right-wall centering tuning
# -------------------------------------------------

# Current best target after testing.
GREETER_CENTER_RIGHT_TARGET_MM = 1600.0

# Kept mostly for debug; right wall is the main centering source now.
GREETER_CENTER_LEFT_TARGET_MM = 700.0

# Tight enough to avoid accepting too far from the right wall.
GREETER_CENTER_TOLERANCE_MM = 175.0

# Steering correction.
GREETER_CENTER_KP = 0.00020
GREETER_CENTER_MAX_STEER = 0.06
GREETER_CENTER_MIN_POWER = 0.70

# Current best direction from testing.
GREETER_CENTER_STEER_SIGN = -1.0

# -------------------------------------------------
# Greeter safety
# -------------------------------------------------

# Front clear threshold after 180.
GREETER_CENTER_FRONT_CLEAR_MM = 750.0

# Hard danger stop while aligning/centering/moving.
GREETER_CENTER_FRONT_DANGER_MM = 500.0
GREETER_CENTER_SIDE_DANGER_MM = 500.0

# Timeouts.
GREETER_CENTER_TIMEOUT_SEC = 10.0
GREETER_WAIT_CLEAR_TIMEOUT_SEC = 4.0

# -------------------------------------------------
# Move to start of T
# -------------------------------------------------

# Top of T is expected around 9 ft ahead.
# 9 ft ~= 2740 mm.
GREETER_T_START_FRONT_MM = 2150.0
GREETER_T_START_FRONT_TOLERANCE_MM = 350.0

# Robot should still be in the hallway when it sees the T cap.
GREETER_T_START_LEFT_MIN_MM = 700.0
GREETER_T_START_LEFT_MAX_MM = 1800.0

GREETER_T_START_RIGHT_MIN_MM = 900.0
GREETER_T_START_RIGHT_MAX_MM = 2200.0

GREETER_T_START_SEEN_REQUIRED = 2
GREETER_MOVE_TO_T_TIMEOUT_SEC = 14.0

# Use same strong forward speed.
GREETER_MOVE_TO_T_BASE_SPEED = 0.80


# -------------------------------------------------
# Bathroom route after T-start
# -------------------------------------------------

GREETER_BATHROOM_TURN_SPEED = 0.80

# If it only turns ~45 degrees, raise this.
# If it over-turns, lower this.
GREETER_BATHROOM_LEFT_TURN_SEC = .65

# Flip to -1.0 if this turns right instead of left.
GREETER_BATHROOM_TURN_SIGN = -1.0

# After turning left, drive toward bathroom.
GREETER_BATHROOM_FORWARD_SEC = 5.0
GREETER_BATHROOM_FORWARD_SPEED = 0.80

# -------------------------------------------------
# Voice destination selection
# -------------------------------------------------

GREETER_DESTINATION_LISTEN_TIMEOUT_SEC = 4.0
GREETER_DESTINATION_PHRASE_TIME_LIMIT_SEC = 4.0

# -------------------------------------------------
# Voice destination detection
# -------------------------------------------------

GREETER_VOICE_TIMEOUT_SEC = 6.0
GREETER_VOICE_PHRASE_LIMIT_SEC = 5.0
GREETER_VOICE_AMBIENT_SEC = 0.35
GREETER_VOICE_ENERGY_THRESHOLD = 300
GREETER_VOICE_PAUSE_THRESHOLD = 0.8

# Keeps retrying instead of stopping after one failed listen.
GREETER_DESTINATION_TOTAL_LISTEN_SEC = 20.0

# -------------------------------------------------
# Robot Lab route after T-start
# -------------------------------------------------

GREETER_ROBOT_LAB_TURN_SPEED = 0.80

# Start by mirroring your working bathroom turn time.
GREETER_ROBOT_LAB_RIGHT_TURN_SEC = 0.05

# Opposite of bathroom.
# Flip to -1.0 if it turns left instead of right.
GREETER_ROBOT_LAB_TURN_SIGN = -1.0

GREETER_ROBOT_LAB_FORWARD_SEC = 4.0
GREETER_ROBOT_LAB_FORWARD_SPEED = 0.80

