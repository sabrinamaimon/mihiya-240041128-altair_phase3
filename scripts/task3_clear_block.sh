#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
echo ">>> Clearing Hazard Blockage: /field_blocked = False <<<"
ros2 topic pub --once /field_blocked std_msgs/msg/Bool "{data: false}"
echo "Blockage cleared! Notice turtle stays STOPPED (no auto-resume)."
sleep 3
