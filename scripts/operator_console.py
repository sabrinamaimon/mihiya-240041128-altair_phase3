#!/usr/bin/env python3
"""
Project Altair - Mission Operator Console (Task 3)
Ultra-fast, instantaneous ROS 2 operator interface.
Pre-initializes ROS 2 publishers and clients so commands execute in < 1 millisecond.
"""

import sys
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from std_msgs.msg import Bool
from std_srvs.srv import Trigger


class MissionOperator(Node):
    def __init__(self):
        super().__init__('mission_operator_console')
        
        qos_reliable = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        self.blockage_pub = self.create_publisher(Bool, '/field_blocked', qos_reliable)
        self.resume_cli = self.create_client(Trigger, '/resume_mission')
        
    def inject_blockage(self):
        msg = Bool()
        msg.data = True
        self.blockage_pub.publish(msg)
        print("\n>>> [HAZARD INJECTED] /field_blocked = True -> Turtle halts immediately! <<<\n")

    def clear_blockage(self):
        msg = Bool()
        msg.data = False
        self.blockage_pub.publish(msg)
        print("\n>>> [HAZARD CLEARED] /field_blocked = False -> Turtle remains stationary (PAUSED_CLEAR) <<<\n")

    def call_resume(self):
        if not self.resume_cli.service_is_ready():
            # Wait up to 1 second for service
            ready = self.resume_cli.wait_for_service(timeout_sec=1.0)
            if not ready:
                print("\n[WARNING] /resume_mission service not available (is field_mission running?).\n")
                return
            
        req = Trigger.Request()
        future = self.resume_cli.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=1.5)
            
        if future.done():
            resp = future.result()
            status_str = "ACCEPTED" if resp.success else "REJECTED"
            print(f"\n>>> [/resume_mission RESPONSE: {status_str}] Success={resp.success} | Message: {resp.message} <<<\n")
        else:
            print("\n>>> [/resume_mission] Request timed out. <<<\n")


def print_menu():
    print("=" * 60)
    print("    PROJECT ALTAIR - MISSION OPERATOR CONSOLE (Task 3)    ")
    print("=" * 60)
    print("  [B] : Inject Blockage      (/field_blocked = true)")
    print("  [R] : Request Resume       (/resume_mission)")
    print("  [C] : Clear Blockage       (/field_blocked = false)")
    print("  [Q] : Quit Console")
    print("=" * 60)
    print("")


def main():
    rclpy.init()
    node = MissionOperator()
    
    # Process DDS discovery
    rclpy.spin_once(node, timeout_sec=0.2)
    print_menu()
    
    try:
        while rclpy.ok():
            try:
                raw = input("Enter Action [B, R, C, Q]: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
                
            if not raw:
                continue
                
            # Filter non-printable escape characters (like Mac Option key glitches)
            clean = "".join(c for c in raw if c.isalnum()).upper()
            if not clean:
                continue
                
            choice = clean[0]
            if choice == 'B':
                node.inject_blockage()
            elif choice == 'R':
                node.call_resume()
            elif choice == 'C':
                node.clear_blockage()
            elif choice == 'Q':
                print("Exiting operator console.")
                break
            else:
                print(f"Invalid option '{choice}'. Please type B, R, C, or Q.")
                
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
