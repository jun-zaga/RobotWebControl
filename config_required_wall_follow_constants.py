# These constants are referenced by the current services/wall_follow_service.py.
# Add them to config.py if they are missing.

# If the LiDAR is offset toward the left side of the robot, increase this.
# Example: if LiDAR is 200 mm left of robot center, start with:
# WALL_FOLLOW_LEFT_BODY_OFFSET_MM = 200.0
# WALL_FOLLOW_RIGHT_BODY_OFFSET_MM = -200.0
WALL_FOLLOW_LEFT_BODY_OFFSET_MM = 0.0
WALL_FOLLOW_RIGHT_BODY_OFFSET_MM = 0.0

# Keep this at 1.0 unless steering correction is backwards after LiDAR is correct.
WALL_FOLLOW_TURN_SIGN = 1.0

# Prevent tiny commands that only buzz the servos but do not move the robot.
WALL_FOLLOW_MIN_MOTOR_POWER = 0.20

# Back-side look zones. The calibration script will generate better values.
WALL_FOLLOW_BACK_LEFT_CENTER_DEG = 45.0
WALL_FOLLOW_BACK_LEFT_HALF_ANGLE_DEG = 15.0
WALL_FOLLOW_BACK_RIGHT_CENTER_DEG = 315.0
WALL_FOLLOW_BACK_RIGHT_HALF_ANGLE_DEG = 15.0
