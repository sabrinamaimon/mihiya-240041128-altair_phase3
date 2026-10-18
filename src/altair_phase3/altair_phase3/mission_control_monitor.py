#!/usr/bin/env python3
"""
Project Altair - Software Recruitment Batch 24 - Phase 3 Assessment
Task 1: Mission Control Monitor Subscriber Node
Node Name: mission_control_monitor
Author: Mihiya (Student ID: 240041128)

Description:
Subscribes to rover telemetry topic, parses incoming JSON telemetry data,
formats and displays all health readings with units, and triggers a visual
warning whenever the rover battery falls below 25%.
"""

import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MissionControlMonitor(Node):
    def __init__(self):
        super().__init__('mission_control_monitor')

        self.declare_parameter('topic_name', '/rover/telemetry')
        self.declare_parameter('warning_battery_threshold', 25.0)

        self.topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        self.battery_threshold = self.get_parameter('warning_battery_threshold').get_parameter_value().double_value

        self.subscription = self.create_subscription(
            String,
            self.topic_name,
            self.telemetry_callback,
            10
        )

        self.get_logger().info(
            f"Mission Control Monitor initialized.\n"
            f"Listening to '{self.topic_name}'. Low battery threshold set to {self.battery_threshold:.1f}%."
        )

    def telemetry_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError as err:
            self.get_logger().error(f"Failed to decode telemetry JSON: {err}")
            return

        battery = data.get('battery_pct', 0.0)
        temp = data.get('temperature_c', 0.0)
        wheel_speed = data.get('wheel_speed_mps', 0.0)
        elapsed = data.get('elapsed_s', 0.0)

        # Formatted readable display
        status_line = (
            f"[MISSION CONTROL] T+{elapsed:06.1f}s | "
            f"Battery: {battery:5.1f} % | "
            f"Internal Temp: {temp:5.1f} °C | "
            f"Wheel Speed: {wheel_speed:4.2f} m/s"
        )

        # Battery warning condition (< 25%)
        if battery < self.battery_threshold:
            self.get_logger().warn(
                f"{status_line}\n"
                f"  >>> [CRITICAL WARNING] BATTERY BELOW {self.battery_threshold:.1f}%! "
                f"Current: {battery:.1f}% - Return to base or initiate solar charge! <<<"
            )
        else:
            self.get_logger().info(status_line)


def main(args=None):
    rclpy.init(args=args)
    node = MissionControlMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Mission Control Monitor shutting down cleanly.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
