#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /root/altair_phase3_ws/install/setup.bash
echo "=========================================================="
echo " Project Altair - Task 3: Autonomous Waypoint Mission      "
echo " (Bottle (8.0, 5.5) -> Mallet (8.0, 8.0) -> Base (5.5,5.5))"
echo "=========================================================="
ros2 launch altair_phase3 field.launch.py
exec bash
