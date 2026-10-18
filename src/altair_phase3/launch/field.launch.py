#!/usr/bin/env python3
"""
Project Altair - Software Recruitment Batch 24 - Phase 3 Assessment
Task 3 Launch File: field.launch.py
Author: Mihiya (Student ID: 240041128)

Description:
Launches both turtlesim simulator and the autonomous field_mission waypoint node
with a single command:
  ros2 launch altair_phase3 field.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # 1. Turtlesim simulator GUI node
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='sim',
            output='screen'
        ),

        # 2. Project Altair Autonomous Field Mission Controller Node
        Node(
            package='altair_phase3',
            executable='field_mission',
            name='field_mission',
            output='screen'
        )
    ])
