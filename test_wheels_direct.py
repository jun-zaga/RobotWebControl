import time
from hardware import robot_control as robot

tests = [
    ("LEFT forward only", -0.6, 0.0),
    ("LEFT backward only", 0.6, 0.0),
    ("RIGHT forward only", 0.0, -0.6),
    ("RIGHT backward only", 0.0, 0.6),
    ("BOTH forward", -0.6, -0.6),
    ("BOTH backward", 0.6, 0.6),
    ("PIVOT left", 0.6, -0.6),
    ("PIVOT right", -0.6, 0.6),
]

for name, left, right in tests:
    input(f"\nPress Enter for {name}: left={left}, right={right}")
    robot.drive(left, right)
    time.sleep(1.2)
    robot.stop()
    time.sleep(0.5)

print("\nDone.")