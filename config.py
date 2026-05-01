from pathlib import Path

# Folder where this config.py file lives.
BASE_DIR = Path(__file__).resolve().parent

# Path to the dialog script used by the robot's speech/dialog system.
SCRIPT_PATH = BASE_DIR / "dialog" / "scripts" / "demo_script.txt"

# -------------------------------------------------
# Drive / watchdog
# -------------------------------------------------

# How long the robot can go without receiving a drive command before auto-stopping.
CMD_TIMEOUT_SEC = 1.0

# How often the watchdog checks whether the robot should be stopped.
WATCHDOG_PERIOD_SEC = 0.10

# Global multiplier for drive output strength.
DRIVE_GAIN = 1.0

# -------------------------------------------------
# LiDAR
# -------------------------------------------------

# Serial port where the LiDAR is connected.
LIDAR_PORT = "/dev/ttyUSB0"

# Baud rate used to communicate with the LiDAR.
LIDAR_BAUD = 115200


# Keeps an angle inside the 0–359 degree range.
def wrap_deg(deg: float) -> float:
    return deg % 360.0


# Ignores very close LiDAR readings that are probably the robot body/mount.
LIDAR_IGNORE_BELOW_MM = 220.0

# -------------------------------------------------
# Main LiDAR safety zones
# -------------------------------------------------

# Direction the robot considers "front" for safety checks.
LIDAR_FRONT_CENTER_DEG = 135.0

# Direction the robot considers "rear" for safety checks.
LIDAR_REAR_CENTER_DEG = wrap_deg(LIDAR_FRONT_CENTER_DEG + 180.0)

# Width of the front safety cone.
LIDAR_FRONT_ZONE_HALF_ANGLE_DEG = 18.0

# Width of the rear safety cone.
LIDAR_REAR_ZONE_HALF_ANGLE_DEG = 10.0

# Distance where the robot treats something in front as too close.
LIDAR_FRONT_STOP_MM = 430

# Distance where the robot treats something behind as too close.
LIDAR_REAR_STOP_MM = 300

# How old LiDAR data can be before it is considered stale/unsafe.
LIDAR_STALE_SEC = 2.0

# -------------------------------------------------
# TTS
# -------------------------------------------------

# Default speaking speed for text-to-speech.
TTS_DEFAULT_RATE = 120

# Default text-to-speech volume.
TTS_DEFAULT_VOL = 1.0

# -------------------------------------------------
# Wall follower tuning
# -------------------------------------------------

# Which side the wall follower uses by default.
WALL_FOLLOW_DEFAULT_SIDE = "right"

# Backup wall-follow distance if side-specific target is not used.
WALL_FOLLOW_TARGET_MM = 700.0

# Desired LiDAR distance from the wall when following the left side.
WALL_FOLLOW_TARGET_LEFT_MM = 460.0

# Desired LiDAR distance from the wall when following the right side.
WALL_FOLLOW_TARGET_RIGHT_MM = 700.0

# How much distance error is allowed before normal correction starts.
WALL_FOLLOW_TOLERANCE_MM = 50

# Distance where the wall is considered lost/far enough to search for it again.
WALL_FOLLOW_WALL_LOST_MM = 1700.0

# Direction multiplier for forward movement.
# Your robot uses negative wheel commands as forward.
WALL_FOLLOW_FORWARD_SIGN = -1.0

# Normal forward speed while following a wall.
WALL_FOLLOW_BASE_SPEED = 0.50

# How strongly the robot corrects when it is too close/far from the wall.
WALL_FOLLOW_TURN_GAIN = 0.15

# Maximum steering correction allowed during normal wall following.
WALL_FOLLOW_MAX_TURN = 0.08

# Turn strength used while searching for a lost wall.
WALL_FOLLOW_SEARCH_TURN = 0.35

# Distance where the front-side wall is considered open, usually meaning a corner.
WALL_FOLLOW_CORNER_OPEN_MM = 400.0

# Turn strength used during corner behavior if the service uses this variable.
WALL_FOLLOW_CORNER_TURN = 0.50

# Distance where the front-side wall is considered too close during corner behavior.
WALL_FOLLOW_CORNER_CLOSE_MM = 0.0

# Distance where a front obstacle should stop/pivot the wall follower.
WALL_FOLLOW_FRONT_STOP_MM = 430.0

# Distance where the front-left/front-right wall is close enough to steer away.
WALL_FOLLOW_FRONT_SIDE_DANGER_MM = 420.0

# How many times per second the wall follower updates.
WALL_FOLLOW_LOOP_HZ = 12.0

# Extra correction for LiDAR offset when following the left wall.
WALL_FOLLOW_LEFT_BODY_OFFSET_MM = 0.0

# Extra correction for LiDAR offset when following the right wall.
WALL_FOLLOW_RIGHT_BODY_OFFSET_MM = 0.0

# Minimum motor command considered strong enough to move the robot.
WALL_FOLLOW_MIN_MOTOR_POWER = 0.18

# -------------------------------------------------
# Wall follow LiDAR zones
# -------------------------------------------------

# Direction used as the wall-follow front zone.
WALL_FOLLOW_FRONT_CENTER_DEG = 135.0

# Width of the wall-follow front zone.
WALL_FOLLOW_FRONT_HALF_ANGLE_DEG = 18.0

# Direction used as the wall-follow rear zone.
WALL_FOLLOW_REAR_CENTER_DEG = 315.0

# Width of the wall-follow rear zone.
WALL_FOLLOW_REAR_HALF_ANGLE_DEG = 10.0

# Direction used to read the left wall distance.
WALL_FOLLOW_LEFT_CENTER_DEG = 225.0

# Width of the left wall sensing zone.
WALL_FOLLOW_LEFT_HALF_ANGLE_DEG = 25.0

# Direction used to read the right wall distance.
WALL_FOLLOW_RIGHT_CENTER_DEG = 45.0

# Width of the right wall sensing zone.
WALL_FOLLOW_RIGHT_HALF_ANGLE_DEG = 25.0

# Direction used to check the front-left corner/wall.
WALL_FOLLOW_FRONT_LEFT_CENTER_DEG = 180.0

# Width of the front-left sensing zone.
WALL_FOLLOW_FRONT_LEFT_HALF_ANGLE_DEG = 20.0

# Direction used to check the front-right corner/wall.
WALL_FOLLOW_FRONT_RIGHT_CENTER_DEG = 90.0

# Width of the front-right sensing zone.
WALL_FOLLOW_FRONT_RIGHT_HALF_ANGLE_DEG = 20.0

# Direction used to check the back-left wall.
WALL_FOLLOW_BACK_LEFT_CENTER_DEG = 270.0

# Width of the back-left sensing zone.
WALL_FOLLOW_BACK_LEFT_HALF_ANGLE_DEG = 10.0

# Direction used to check the back-right wall.
WALL_FOLLOW_BACK_RIGHT_CENTER_DEG = 0.0

# Width of the back-right sensing zone.
WALL_FOLLOW_BACK_RIGHT_HALF_ANGLE_DEG = 10.0

# -------------------------------------------------
# Obstacle handling
# -------------------------------------------------

# Distance where a true front obstacle starts the avoid sequence.
WALL_FOLLOW_OBSTACLE_STOP_MM = 500.0

# How long to fully stop before reacting.
WALL_FOLLOW_OBSTACLE_STOP_SEC = 0.25

# How long to reverse away from the obstacle.
WALL_FOLLOW_OBSTACLE_BACKUP_SEC = 0.40

# How long to pivot away before resuming wall follow.
WALL_FOLLOW_OBSTACLE_PIVOT_SEC = 0.45

# Reverse speed during obstacle avoidance.
WALL_FOLLOW_OBSTACLE_BACKUP_SPEED = 0.45

# Pivot strength during obstacle avoidance.
WALL_FOLLOW_OBSTACLE_PIVOT_POWER = 0.75

# -------------------------------------------------
# Final Project Greeter FSM
# -------------------------------------------------

GREETER_HUMAN_DETECT_MM = 1400.0

# Stop distance during autonomous movement.
GREETER_FRONT_OBSTACLE_MM = 650.0

GREETER_WALL_VISIBLE_MM = 1700.0
GREETER_OPENING_MM = 1800.0

# Final straight movement after destination turn.
GREETER_FINAL_FORWARD_SEC = 3.0

# Your robot uses negative wheel commands as forward.
WALL_FOLLOW_FORWARD_SIGN = -1.0

# Stuart needs this much power to move.
GREETER_BASE_SPEED = 0.80
GREETER_TURN_SPEED = 0.80

# Soft correction because Stuart is moving fast.
GREETER_WALL_FOLLOW_KP = 0.00015
GREETER_TARGET_SIDE_MM = 1250.0

# -------------------------------------------------
# Greeter LiDAR zones
# -------------------------------------------------

GREETER_FRONT_CENTER_DEG = 0.0
GREETER_FRONT_HALF_ANGLE_DEG = 20.0

GREETER_LEFT_CENTER_DEG = 225.0
GREETER_LEFT_HALF_ANGLE_DEG = 25.0

GREETER_RIGHT_CENTER_DEG = 45.0
GREETER_RIGHT_HALF_ANGLE_DEG = 25.0

# -------------------------------------------------
# Greeter turn / route tuning
# -------------------------------------------------

GREETER_TURN_TIMEOUT_SEC = 4.0
GREETER_TURN_MIN_SEC = 0.35

GREETER_TURN_FRONT_OPEN_MM = 2400.0
GREETER_TURN_SIDE_WALL_MM = 1700.0

# Calibrated destination turn.
GREETER_TURN_45_SEC = 0.60

# -------------------------------------------------
# Greeter mapped T detection
# Based on stuart_map2.json:
# T start front ~= 1390-1472
# left ~= 1305-1352
# right ~= 1683-2031
# -------------------------------------------------

GREETER_T_FAR_MM = 1450.0
GREETER_T_FAR_TOLERANCE_MM = 450.0

GREETER_T_LEFT_MIN_MM = 1000.0
GREETER_T_LEFT_MAX_MM = 1800.0

GREETER_T_RIGHT_MIN_MM = 1400.0
GREETER_T_RIGHT_MAX_MM = 3300.0

GREETER_T_FAR_SEEN_REQUIRED = 1
