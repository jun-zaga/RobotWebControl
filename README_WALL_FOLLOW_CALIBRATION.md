# Wall-follow LiDAR calibration

This replaces the old angle/dance calibration idea. These files are for making wall-follow detect the robot's real **front, back, left, and right** correctly.

## Files

- `wall_follow_lidar_calibration.py`
  - interactive calibration for LiDAR orientation
  - samples front, left, right, back
  - writes constants to `calibration_results/wall_follow_lidar_config_patch.py`

- `wall_follow_live_check.py`
  - live checker after you paste the constants into `config.py`
  - move your hand/cardboard around the robot and verify the matching side drops

## Install

Copy the `calibration/` folder into the repo root:

```bash
cd ~/RobotWebControl
mkdir -p calibration
cp -r /path/to/calibration/* calibration/
```

## Run

```bash
cd ~/RobotWebControl
python3 calibration/wall_follow_lidar_calibration.py
```

It will ask you to place a flat object/wall near:

1. front
2. left
3. right
4. back

Then paste the generated constants from:

```bash
calibration_results/wall_follow_lidar_config_patch.py
```

into `config.py`.

## Verify

Restart the app/services, then run:

```bash
python3 calibration/wall_follow_live_check.py
```

Expected behavior:

- put hand/cardboard in front → `front` drops
- put it behind → `back` drops
- put it on robot-left → `left` drops
- put it on robot-right → `right` drops

## Important notes

- This calibrates LiDAR zones, not motor turning.
- Keep the robot still while sampling.
- Use a flat board/cardboard if your hand gives noisy readings.
- If left/right are swapped, rerun calibration or manually swap `WALL_FOLLOW_LEFT_CENTER_DEG` and `WALL_FOLLOW_RIGHT_CENTER_DEG`.
- If front/back safety is swapped, swap `LIDAR_FRONT_CENTER_DEG` and `LIDAR_REAR_CENTER_DEG`.
