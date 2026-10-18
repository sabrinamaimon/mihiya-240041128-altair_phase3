#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /root/altair_phase3_ws/install/setup.bash
echo "=========================================================="
echo " Project Altair - Task 2a: Turtle Driving Menu            "
echo " (Commands: P=Patrol, R=Rectangle, Z=Zigzag, Q=Quit)      "
echo "=========================================================="
ros2 run altair_phase3 turtle_driver
exec bash
