#!/usr/bin/env python3
"""
Project Altair - Software Recruitment Batch 24 - Phase 3 Assessment
Task 3: Autonomous Waypoint Mission Node with Interruption and Resume
Node Name: field_mission
Author: Mihiya (Student ID: 240041128)

Description:
Executes closed-loop waypoint navigation for turtlesim across three field points:
  1. Bottle: (8.0, 5.5)
  2. Mallet: (8.0, 8.0)
  3. Base:   (5.5, 5.5)
Criteria:
  - Arrival threshold: distance <= 0.3 turtlesim units.
  - Subscribes to /field_blocked (std_msgs/msg/Bool). When True, halts immediately.
  - When /field_blocked becomes False, holds position (does NOT auto-resume).
  - Resumes ONLY on valid call to /resume_mission (std_srvs/srv/Trigger).
  - Rejects resume while blocked, running, completed, or before initial pose.
"""

import math
from enum import Enum, auto
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from std_msgs.msg import Bool
from std_srvs.srv import Trigger


class MissionState(Enum):
    UNINITIALIZED = auto()
    RUNNING = auto()
    PAUSED_BLOCKED = auto()
    PAUSED_CLEAR = auto()
    DONE = auto()


class FieldMission(Node):
    def __init__(self):
        super().__init__('field_mission')

        # Mission Waypoints: Bottle -> Mallet -> Base
        self.waypoints = [
            ("Bottle", 8.0, 5.5),
            ("Mallet", 8.0, 8.0),
            ("Base",   5.5, 5.5)
        ]
        self.current_wp_idx = 0
        self.arrival_tolerance = 0.3  # Arrival threshold in turtlesim units

        # State tracking
        self.state = MissionState.UNINITIALIZED
        self.pose = None
        self.is_field_blocked = False

        # Controller gains
        self.k_linear = 0.3
        self.k_angular = 1.8
        self.max_linear_speed = 0.25
        self.max_angular_speed = 1.8

        # Reliable QoS for safety critical blockage notifications
        qos_reliable = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )

        # Publishers & Subscribers
        self.cmd_vel_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.pose_sub = self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.blockage_sub = self.create_subscription(Bool, '/field_blocked', self.blockage_callback, qos_reliable)

        # Service for explicit operator resume
        self.resume_srv = self.create_service(Trigger, '/resume_mission', self.resume_service_callback)

        # 10 Hz Control Loop Timer
        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info("Field Mission node started. Waiting for initial turtle pose...")

    def pose_callback(self, msg: Pose):
        self.pose = msg
        # Transition from uninitialized to running once first pose is received
        if self.state == MissionState.UNINITIALIZED:
            self.state = MissionState.RUNNING
            wp_name, wx, wy = self.waypoints[self.current_wp_idx]
            self.get_logger().info(
                f"Initial pose received: (x={msg.x:.2f}, y={msg.y:.2f}, theta={msg.theta:.2f}). "
                f"Starting mission toward Target 1: '{wp_name}' ({wx:.1f}, {wy:.1f})."
            )

    def blockage_callback(self, msg: Bool):
        previous_blocked = self.is_field_blocked
        self.is_field_blocked = msg.data

        if self.is_field_blocked:
            self.get_logger().warn("[HAZARD ALERT] Obstacle detected! /field_blocked = True. Halting robot.")
            if self.state == MissionState.RUNNING:
                self.state = MissionState.PAUSED_BLOCKED
            elif self.state == MissionState.PAUSED_CLEAR:
                self.state = MissionState.PAUSED_BLOCKED
            self.publish_zero_velocity()
        else:
            if previous_blocked:
                self.get_logger().info("[HAZARD CLEARED] Blockage report cleared. /field_blocked = False.")
                if self.state == MissionState.PAUSED_BLOCKED:
                    # =========================================================================
                    # CRITICAL LINE PREVENTING AUTOMATIC RESUME:
                    # Receiving False clears the blockage flag, but transitions to PAUSED_CLEAR
                    # instead of RUNNING. The robot remains stationary with zero velocity until
                    # the operator explicitly authorizes motion via the /resume_mission service!
                    # =========================================================================
                    self.state = MissionState.PAUSED_CLEAR
                    self.get_logger().info(
                        "[MISSION PAUSED] Standing by in clear status. Awaiting operator /resume_mission call."
                    )

    def resume_service_callback(self, request: Trigger.Request, response: Trigger.Response) -> Trigger.Response:
        """Handles operator resume decision."""
        # 1. Reject if no pose yet
        if self.pose is None or self.state == MissionState.UNINITIALIZED:
            response.success = False
            response.message = "REJECTED: No turtle pose received yet."
            self.get_logger().warn(f"Resume Request -> {response.message}")
            return response

        # 2. Reject if route is still blocked
        if self.is_field_blocked or self.state == MissionState.PAUSED_BLOCKED:
            response.success = False
            response.message = "REJECTED: Cannot resume while route is reported BLOCKED."
            self.get_logger().warn(f"Resume Request -> {response.message}")
            return response

        # 3. Reject if already running
        if self.state == MissionState.RUNNING:
            response.success = False
            response.message = "REJECTED: Mission is already active and running."
            self.get_logger().warn(f"Resume Request -> {response.message}")
            return response

        # 4. Reject if mission already completed
        if self.state == MissionState.DONE:
            response.success = False
            response.message = "REJECTED: Mission has already finished (DONE)."
            self.get_logger().warn(f"Resume Request -> {response.message}")
            return response

        # 5. Authorize resume from PAUSED_CLEAR
        if self.state == MissionState.PAUSED_CLEAR:
            self.state = MissionState.RUNNING
            self.max_linear_speed = 0.8  # Nominal cruising speed for remaining waypoints
            self.k_linear = 0.8
            target_name, tx, ty = self.waypoints[self.current_wp_idx]
            response.success = True
            response.message = f"ACCEPTED: Resuming navigation toward Target {self.current_wp_idx + 1} ({target_name})."
            self.get_logger().info(f"Resume Request -> {response.message}")
            return response

        response.success = False
        response.message = f"REJECTED: Cannot resume from state {self.state.name}."
        return response

    def control_loop(self):
        """10 Hz closed-loop control tick."""
        # Only drive when actively in RUNNING state
        if self.state != MissionState.RUNNING:
            self.publish_zero_velocity()
            return

        if self.pose is None:
            return

        # Current target coordinates
        target_name, target_x, target_y = self.waypoints[self.current_wp_idx]

        # Resources Section 5.1 Feedback Equations:
        # 1. dx = x_g - x, dy = y_g - y
        dx = target_x - self.pose.x
        dy = target_y - self.pose.y

        # 2. Euclidean distance: d = sqrt(dx^2 + dy^2)
        dist = math.hypot(dx, dy)

        # 3. Desired heading: theta_g = atan2(dy, dx)
        desired_theta = math.atan2(dy, dx)

        # 4. Heading error delta: delta = theta_g - theta
        delta = desired_theta - self.pose.theta

        # 5. Shortest signed heading error: e = atan2(sin(delta), cos(delta))
        heading_error = math.atan2(math.sin(delta), math.cos(delta))

        # Check for waypoint arrival
        if dist <= self.arrival_tolerance:
            self.get_logger().info(
                f"[ARRIVAL] Reached Target {self.current_wp_idx + 1}: '{target_name}' "
                f"(Distance: {dist:.3f} <= {self.arrival_tolerance})."
            )
            self.current_wp_idx += 1

            # Check if all waypoints are finished
            if self.current_wp_idx >= len(self.waypoints):
                self.state = MissionState.DONE
                self.publish_zero_velocity()
                self.get_logger().info("[MISSION COMPLETE] All waypoints visited. Final Status: DONE.")
                return

            next_name, nx, ny = self.waypoints[self.current_wp_idx]
            self.get_logger().info(f"Proceeding to Target {self.current_wp_idx + 1}: '{next_name}' ({nx:.1f}, {ny:.1f}).")
            return

        # Compute velocity commands
        twist = Twist()

        # If heading error is large, prioritize rotation before driving fast
        if abs(heading_error) > 0.25:  # ~14 degrees
            twist.linear.x = 0.05 if dist > 1.0 else 0.0
            twist.angular.z = max(-self.max_angular_speed, min(self.max_angular_speed, self.k_angular * heading_error))
        else:
            # Heading roughly aligned: drive forward and smoothly steer
            linear_cmd = self.k_linear * dist
            twist.linear.x = max(0.15, min(self.max_linear_speed, linear_cmd))
            twist.angular.z = max(-self.max_angular_speed, min(self.max_angular_speed, self.k_angular * heading_error))

        self.cmd_vel_pub.publish(twist)

    def publish_zero_velocity(self):
        """Sends zero Twist to ensure robot stays stopped when paused or finished."""
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = FieldMission()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Field Mission shutting down cleanly.")
    finally:
        node.publish_zero_velocity()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
