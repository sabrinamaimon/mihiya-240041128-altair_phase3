#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /root/altair_phase3_ws/install/setup.bash
echo "=========================================================="
echo " Project Altair - Task 1: Mission Control Monitor         "
echo " (Subscribes to /rover/telemetry & alerts when batt < 25%) "
echo "=========================================================="
ros2 run altair_phase3 mission_control_monitor
exec bash
