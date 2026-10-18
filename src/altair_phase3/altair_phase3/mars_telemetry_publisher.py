#!/usr/bin/env python3
"""
Project Altair - Software Recruitment Batch 24 - Phase 3 Assessment
Task 1: Rover Telemetry Publisher Node
Node Name: mars_telemetry_publisher
Author: Mihiya (Student ID: 240041128)

Description:
Simulates and publishes rover health telemetry once every second (1 Hz).
Message Schema (JSON inside std_msgs/msg/String):
  - battery_pct: float (Unit: %)
  - temperature_c: float (Unit: °C)
  - wheel_speed_mps: float (Unit: m/s)
  - elapsed_s: float (Unit: s)
"""

import json
import math
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MarsTelemetryPublisher(Node):
    def __init__(self):
        super().__init__('mars_telemetry_publisher')

        # Declare configurable parameters
        self.declare_parameter('topic_name', '/rover/telemetry')
        self.declare_parameter('publish_rate_hz', 1.0)
        self.declare_parameter('starting_battery_pct', 28.0)  # Starts close to 25% for rapid demo
        self.declare_parameter('depletion_rate_pct_per_s', 1.0)
        self.declare_parameter('base_temperature_c', 32.0)
        self.declare_parameter('base_wheel_speed_mps', 0.35)

        # Retrieve parameters
        self.topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        rate_hz = self.get_parameter('publish_rate_hz').get_parameter_value().double_value
        self.battery_pct = self.get_parameter('starting_battery_pct').get_parameter_value().double_value
        self.depletion_rate = self.get_parameter('depletion_rate_pct_per_s').get_parameter_value().double_value
        self.base_temp = self.get_parameter('base_temperature_c').get_parameter_value().double_value
        self.wheel_speed = self.get_parameter('base_wheel_speed_mps').get_parameter_value().double_value

        # Publisher setup
        # Standard ROS 2 String message containing JSON payload.
        # Justification:
        # Standard ROS 2 String (std_msgs/msg/String) allows zero-dependency cross-compatibility
        # without requiring a separately compiled custom ROS 2 interface package.
        # It is structured using JSON key-values with explicit units.
        self.publisher_ = self.create_publisher(String, self.topic_name, 10)

        # Timer setup for 1 Hz (or configured rate)
        timer_period = 1.0 / rate_hz
        self.timer = self.create_timer(timer_period, self.publish_telemetry)

        # Monotonic time tracking
        self.start_time = time.monotonic()

        self.get_logger().info(
            f"Mars Telemetry Publisher started. Publishing to '{self.topic_name}' at {rate_hz} Hz.\n"
            f"Initial Battery: {self.battery_pct:.1f}%, Depletion Rate: {self.depletion_rate:.1f}%/s"
        )

    def publish_telemetry(self):
        current_time = time.monotonic()
        elapsed_s = round(current_time - self.start_time, 2)

        # Simulate realistic battery depletion (clamped at 0%)
        self.battery_pct = max(0.0, round(self.battery_pct - self.depletion_rate, 2))

        # Simulate slight internal motor & CPU temperature rise with minor sinusoidal fluctuation
        # Temperature climbs slowly as rover drives, e.g. +0.15 °C per second up to 45 °C
        temp_rise = min(12.0, elapsed_s * 0.15)
        fluctuation = 0.3 * math.sin(elapsed_s * 0.5)
        temperature_c = round(self.base_temp + temp_rise + fluctuation, 2)

        # Simulate wheel speed (stationary if battery is dead, otherwise gentle variation)
        current_wheel_speed = 0.0 if self.battery_pct <= 0.0 else round(self.wheel_speed + 0.02 * math.cos(elapsed_s), 2)

        payload = {
            'battery_pct': self.battery_pct,
            'temperature_c': temperature_c,
            'wheel_speed_mps': current_wheel_speed,
            'elapsed_s': elapsed_s,
            'units': {
                'battery_pct': '%',
                'temperature_c': 'deg_C',
                'wheel_speed_mps': 'm/s',
                'elapsed_s': 's'
            }
        }

        msg = String()
        msg.data = json.dumps(payload)
        self.publisher_.publish(msg)

        self.get_logger().info(
            f"Published Telemetry | Elapsed: {elapsed_s}s | Battery: {self.battery_pct:.1f}% | "
            f"Temp: {temperature_c:.1f}°C | Speed: {current_wheel_speed:.2f} m/s"
        )


def main(args=None):
    rclpy.init(args=args)
    node = MarsTelemetryPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Mars Telemetry Publisher shutting down cleanly.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
