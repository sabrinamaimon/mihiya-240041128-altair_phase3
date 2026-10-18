#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
echo ">>> Requesting Operator Resume Authorization: /resume_mission <<<"
ros2 service call /resume_mission std_srvs/srv/Trigger "{}"
sleep 3
