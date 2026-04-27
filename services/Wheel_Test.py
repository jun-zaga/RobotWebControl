import time

# Import your robot service the same way your app does
from services.robot_service import RobotService


def test_both_wheels(robot):
    print("\n=== Testing BOTH wheels ===")
    for p in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        print(f"\nPower: {p}")
        robot.drive(-p, -p)  # negative = forward
        time.sleep(2)
        robot.drive(0, 0)
        time.sleep(1)


def test_left_wheel(robot):
    print("\n=== Testing LEFT wheel only ===")
    for p in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        print(f"\nLeft Power: {p}")
        robot.drive(-p, 0)
        time.sleep(2)
        robot.drive(0, 0)
        time.sleep(1)


def test_right_wheel(robot):
    print("\n=== Testing RIGHT wheel only ===")
    for p in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        print(f"\nRight Power: {p}")
        robot.drive(0, -p)
        time.sleep(2)
        robot.drive(0, 0)
        time.sleep(1)


if __name__ == "__main__":
    robot = RobotService()

    print("Starting motor calibration test...")
    print("Make sure robot is on the ground for real results.\n")

    test_both_wheels(robot)
    test_left_wheel(robot)
    test_right_wheel(robot)

    print("\nTest complete.")