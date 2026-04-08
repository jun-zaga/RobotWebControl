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