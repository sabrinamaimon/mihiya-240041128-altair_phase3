#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
echo ">>> Injecting Hazard Blockage: /field_blocked = True <<<"
ros2 topic pub --once /field_blocked std_msgs/msg/Bool "{data: true}"
echo "Blockage sent! Turtle should halt immediately."
sleep 3
