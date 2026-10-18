#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /root/altair_phase3_ws/install/setup.bash
echo "=========================================================="
echo " Project Altair - Task 1: Mars Telemetry Publisher (1 Hz) "
echo "=========================================================="
ros2 run altair_phase3 mars_telemetry_publisher
exec bash
