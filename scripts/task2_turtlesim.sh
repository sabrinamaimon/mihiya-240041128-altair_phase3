#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
echo "=========================================================="
echo " Project Altair - Task 2: Turtlesim Simulator GUI         "
echo "=========================================================="
ros2 run turtlesim turtlesim_node
exec bash
