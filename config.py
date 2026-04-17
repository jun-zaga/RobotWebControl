from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = BASE_DIR / "dialog" / "scripts" / "demo_script.txt"

CMD_TIMEOUT_SEC = 1.0
WATCHDOG_PERIOD_SEC = 0.10

DRIVE_GAIN = 1.50

LIDAR_PORT = "/dev/ttyUSB0"
LIDAR_BAUD = 115200

# Change this if your lidar is mounted differently.
# Good first guess for your setup:
LIDAR_FRONT_CENTER_DEG = 90.0
LIDAR_REAR_CENTER_DEG = (LIDAR_FRONT_CENTER_DEG + 180.0) % 360.0

# Wider cone for testing/calibration so detection actually happens.
LIDAR_FRONT_ZONE_HALF_ANGLE_DEG = 60.0
LIDAR_REAR_ZONE_HALF_ANGLE_DEG = 15.0

# 1 foot ~= 304.8 mm
LIDAR_FRONT_STOP_MM = 915
LIDAR_REAR_STOP_MM = 1830

# If lidar data goes stale while driving forward, stop.
LIDAR_STALE_SEC = 1.0

TTS_DEFAULT_RATE = 120
TTS_DEFAULT_VOL = 1.0

# ---------------------------
# Wall follower tuning
# ---------------------------
WALL_FOLLOW_DEFAULT_SIDE = "right"
WALL_FOLLOW_TARGET_MM = 305.0          # about 1 foot from wall
WALL_FOLLOW_TOLERANCE_MM = 60.0        # deadband to reduce twitching
WALL_FOLLOW_FRONT_STOP_MM = 380.0      # tighter than lidar safety stop for smoother turns
WALL_FOLLOW_BASE_SPEED = 0.22          # forward is negative in your drive convention
WALL_FOLLOW_TURN_GAIN = 1.2
WALL_FOLLOW_MAX_TURN = 0.18
WALL_FOLLOW_SEARCH_TURN = 0.16
WALL_FOLLOW_LOOP_HZ = 12.0
WALL_FOLLOW_WALL_LOST_MM = 900.0

# Zone layout from the assignment's suggested angles.
WALL_FOLLOW_FRONT_CENTER_DEG = 0.0
WALL_FOLLOW_FRONT_HALF_ANGLE_DEG = 20.0

WALL_FOLLOW_RIGHT_CENTER_DEG = 270.0
WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG = 20.0
WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG = 315.0
WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG = 25.0
WALL_FOLLOW_BACK_RIGHT_CENTER_DEG = 245.0
WALL_FOLLOW_BACK_RIGHT_HALF_ANGLE_DEG = 20.0

WALL_FOLLOW_LEFT_CENTER_DEG = 90.0
WALL_FOLLOW_LEFT_HALF_ANGLE_DEG = 20.0
WALL_FOLLOW_FRONT_LEFT_CENTER_DEG = 45.0
WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG = 25.0
WALL_FOLLOW_BACK_LEFT_CENTER_DEG = 115.0
WALL_FOLLOW_BACK_LEFT_HALF_ANGLE_DEG = 20.0
