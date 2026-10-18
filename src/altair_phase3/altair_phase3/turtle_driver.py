#!/usr/bin/env python3
"""
Project Altair - Software Recruitment Batch 24 - Phase 3 Assessment
Task 2a: Turtle Driving Practice Node
Node Name: turtle_driver
Author: Mihiya (Student ID: 240041128)

Description:
Menu-driven velocity commander for turtlesim (/turtle1/cmd_vel).
Accepted commands:
  P: Patrol - Forward 3s, turn 180 deg, forward 3s (returns near start).
  R: Rectangle - Traces rectangle with distinct side lengths (3.0s and 1.5s).
  Z: Zigzag - 3 forward segments alternating left/right turns.
  Q: Quit - Sends zero velocity and cleanly shuts down node.

Architecture:
Uses a background input thread feeding a thread-safe Queue, coupled with
a 10 Hz state-machine control timer. This avoids blocking the ROS 2 executor,
ensures smooth velocity publishing, and guarantees clean stops between patterns.
"""

import math
import queue
import re
import sys
import threading
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class ActionStep:
    """Represents a single timed motion phase."""
    def __init__(self, linear_x: float, angular_z: float, duration_s: float, description: str):
        self.linear_x = linear_x
        self.angular_z = angular_z
        self.duration_s = duration_s
        self.description = description


class TurtleDriver(Node):
    def __init__(self):
        super().__init__('turtle_driver')

        self.cmd_vel_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        # Thread-safe queue for terminal commands
        self.command_queue = queue.Queue()
        self.running = True

        # State machine variables
        self.is_executing = False
        self.current_pattern_name = ""
        self.action_plan = []
        self.current_step_idx = 0
        self.step_start_time = 0.0

        # Control loop at 10 Hz
        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.control_tick)

        # Start interactive terminal input thread
        self.input_thread = threading.Thread(target=self.terminal_input_loop, daemon=True)
        self.input_thread.start()

        self.print_banner()

    def print_banner(self):
        print("\n" + "=" * 60)
        print("  PROJECT ALTAIR - TURTLE DRIVER (Task 2a)")
        print("=" * 60)
        print("  P : Patrol    (Forward 3s -> 180° turn -> Return ~3s)")
        print("  R : Rectangle (Traces 3.0m x 1.5m rectangle)")
        print("  Z : Zigzag    (3 forward legs with alternating turns)")
        print("  Q : Quit cleanly")
        print("=" * 60)
        print("\nEnter command [P, R, Z, Q]: ", end="", flush=True)

    def terminal_input_loop(self):
        """Dedicated thread to read terminal inputs without blocking ROS 2 executor."""
        while self.running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                # Strip ANSI escape codes (e.g. ^[ from Mac Option/Alt keys) and control chars
                clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', line).strip().upper()
                # Extract first command letter if P, R, Z, or Q exists
                match = re.search(r'[PRZQ]', clean)
                if match:
                    self.command_queue.put(match.group(0))
                elif clean:
                    self.command_queue.put(clean)
            except Exception as e:
                self.get_logger().error(f"Input error: {e}")
                break

    def control_tick(self):
        """10 Hz control callback managing command intake and step execution."""
        now = time.monotonic()

        # 1. Process new command if idle
        if not self.is_executing:
            try:
                cmd = self.command_queue.get_nowait()
                self.handle_command(cmd)
            except queue.Empty:
                pass
            return

        # 2. If executing a pattern, handle active action step
        if self.current_step_idx >= len(self.action_plan):
            # Pattern complete! Stop turtle and return to idle
            self.stop_turtle()
            self.is_executing = False
            self.get_logger().info(f"Finished pattern '{self.current_pattern_name}'. Waiting for next command.")
            print("\nEnter command [P, R, Z, Q]: ", end="", flush=True)
            return

        current_step = self.action_plan[self.current_step_idx]

        # Check if current step duration has expired
        if now - self.step_start_time >= current_step.duration_s:
            self.current_step_idx += 1
            self.step_start_time = now
            if self.current_step_idx < len(self.action_plan):
                next_step = self.action_plan[self.current_step_idx]
                self.get_logger().info(f"Step {self.current_step_idx + 1}/{len(self.action_plan)}: {next_step.description}")
            return

        # Publish velocity for active step
        twist = Twist()
        twist.linear.x = float(current_step.linear_x)
        twist.angular.z = float(current_step.angular_z)
        self.cmd_vel_pub.publish(twist)

    def handle_command(self, cmd: str):
        """Validates command and generates action sequence."""
        if cmd == 'P':
            self.start_pattern("Patrol", self.generate_patrol())
        elif cmd == 'R':
            self.start_pattern("Rectangle", self.generate_rectangle())
        elif cmd == 'Z':
            self.start_pattern("Zigzag", self.generate_zigzag())
        elif cmd == 'Q':
            self.get_logger().info("Quit requested. Sending stop velocity...")
            self.stop_turtle()
            self.running = False
            rclpy.shutdown()
        else:
            print(f"\n[INVALID INPUT] Unknown command '{cmd}'. Please enter P, R, Z, or Q.")
            print("Enter command [P, R, Z, Q]: ", end="", flush=True)

    def start_pattern(self, name: str, plan: list):
        self.current_pattern_name = name
        self.action_plan = plan
        self.current_step_idx = 0
        self.step_start_time = time.monotonic()
        self.is_executing = True
        self.get_logger().info(f"Starting pattern '{name}' ({len(plan)} steps).")
        if plan:
            self.get_logger().info(f"Step 1/{len(plan)}: {plan[0].description}")

    def generate_patrol(self) -> list:
        """
        P: Patrol pattern.
        Drive forward for 3.0s, turn 180 degrees (PI radians), drive forward 3.0s.
        Angular speed = PI / 2.0 rad/s for 2.0s = PI rad (180 deg).
        """
        turn_rate = math.pi / 2.0  # 90 deg/s
        turn_duration = 2.0         # 2.0s -> 180 deg
        forward_speed = 1.0
        forward_duration = 3.0

        return [
            ActionStep(linear_x=forward_speed, angular_z=0.0, duration_s=forward_duration, description="Driving forward (3.0s)"),
            ActionStep(linear_x=0.0, angular_z=0.0, duration_s=0.2, description="Settling stop"),
            ActionStep(linear_x=0.0, angular_z=turn_rate, duration_s=turn_duration, description="Turning 180° counter-clockwise"),
            ActionStep(linear_x=0.0, angular_z=0.0, duration_s=0.2, description="Settling stop"),
            ActionStep(linear_x=forward_speed, angular_z=0.0, duration_s=forward_duration, description="Returning to start point (3.0s)"),
            ActionStep(linear_x=0.0, angular_z=0.0, duration_s=0.2, description="Final stop")
        ]

    def generate_rectangle(self) -> list:
        """
        R: Rectangle pattern.
        Two clearly different side lengths: Long side = 3.0s, Short side = 1.5s.
        90° turn: Angular speed = PI / 2.0 rad/s for 1.0s = PI/2 rad (90 deg).
        """
        v = 1.0
        w = math.pi / 2.0
        turn_dur = 1.0

        plan = []
        sides = [
            ("Long side 1 (3.0s)", 3.0),
            ("Short side 1 (1.5s)", 1.5),
            ("Long side 2 (3.0s)", 3.0),
            ("Short side 2 (1.5s)", 1.5),
        ]
        for name, dur in sides:
            plan.append(ActionStep(linear_x=v, angular_z=0.0, duration_s=dur, description=f"Driving {name}"))
            plan.append(ActionStep(linear_x=0.0, angular_z=0.0, duration_s=0.1, description="Corner stop"))
            plan.append(ActionStep(linear_x=0.0, angular_z=w, duration_s=turn_dur, description="Turning 90° CCW"))
            plan.append(ActionStep(linear_x=0.0, angular_z=0.0, duration_s=0.1, description="Corner stop"))
        return plan

    def generate_zigzag(self) -> list:
        """
        Z: Zigzag pattern.
        Three forward segments, alternating left (+60°) and right (-120°) turns.
        """
        v = 1.0
        turn_rate = math.pi / 3.0  # 60 deg/s

        return [
            # Segment 1
            ActionStep(linear_x=v, angular_z=0.0, duration_s=2.0, description="Forward segment 1 (2.0s)"),
            ActionStep(linear_x=0.0, angular_z=0.0, duration_s=0.1, description="Pause"),
            # Turn Left 60 deg
            ActionStep(linear_x=0.0, angular_z=turn_rate, duration_s=1.0, description="Turn Left 60°"),
            ActionStep(linear_x=0.0, angular_z=0.0, duration_s=0.1, description="Pause"),
            # Segment 2
            ActionStep(linear_x=v, angular_z=0.0, duration_s=2.0, description="Forward segment 2 (2.0s)"),
            ActionStep(linear_x=0.0, angular_z=0.0, duration_s=0.1, description="Pause"),
            # Turn Right 120 deg
            ActionStep(linear_x=0.0, angular_z=-turn_rate, duration_s=2.0, description="Turn Right 120°"),
            ActionStep(linear_x=0.0, angular_z=0.0, duration_s=0.1, description="Pause"),
            # Segment 3
            ActionStep(linear_x=v, angular_z=0.0, duration_s=2.0, description="Forward segment 3 (2.0s)"),
            ActionStep(linear_x=0.0, angular_z=0.0, duration_s=0.2, description="Final stop")
        ]

    def stop_turtle(self):
        """Sends an explicit zero velocity Twist to guarantee stopping."""
        stop_twist = Twist()
        self.cmd_vel_pub.publish(stop_twist)


def main(args=None):
    rclpy.init(args=args)
    node = TurtleDriver()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.stop_turtle()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
