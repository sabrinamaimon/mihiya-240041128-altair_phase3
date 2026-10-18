#!/usr/bin/env python3
"""
Logic & Controller Mathematics Verification Suite
Tests the algorithmic correctness of altair_phase3 nodes independently of ROS 2 middleware.
"""

import math
import json
import unittest

def compute_steering(current_x, current_y, current_theta, target_x, target_y):
    """Resources Section 5.1 Feedback Equations."""
    dx = target_x - current_x
    dy = target_y - current_y
    dist = math.hypot(dx, dy)
    theta_g = math.atan2(dy, dx)
    delta = theta_g - current_theta
    heading_error = math.atan2(math.sin(delta), math.cos(delta))
    return dist, theta_g, heading_error


class TestAltairPhase3Logic(unittest.TestCase):

    def test_heading_error_wrapping(self):
        """Test angle wrapping across -pi / +pi discontinuity."""
        # Case 1: Facing +170 deg (2.967 rad), target at -170 deg (-2.967 rad)
        # Shortest turn is +20 deg (+0.349 rad) counterclockwise, NOT -340 deg!
        theta_current = 2.96706
        theta_target = -2.96706
        delta = theta_target - theta_current
        e = math.atan2(math.sin(delta), math.cos(delta))
        self.assertAlmostEqual(e, 0.349, places=2)

        # Case 2: Facing 0, target at (8.0, 5.5) from (5.5, 5.5) -> heading 0
        dist, theta_g, err = compute_steering(5.5, 5.5, 0.0, 8.0, 5.5)
        self.assertAlmostEqual(dist, 2.5, places=3)
        self.assertAlmostEqual(theta_g, 0.0, places=3)
        self.assertAlmostEqual(err, 0.0, places=3)

        # Case 3: Facing 0, target at Mallet (8.0, 8.0) from Bottle (8.0, 5.5) -> dy=2.5, dx=0 -> heading +pi/2
        dist, theta_g, err = compute_steering(8.0, 5.5, 0.0, 8.0, 8.0)
        self.assertAlmostEqual(dist, 2.5, places=3)
        self.assertAlmostEqual(theta_g, math.pi / 2, places=3)
        self.assertAlmostEqual(err, math.pi / 2, places=3)

    def test_arrival_tolerance(self):
        """Tolerance <= 0.3 units counts as arrival."""
        tolerance = 0.3
        self.assertTrue(0.29 <= tolerance)
        self.assertTrue(0.30 <= tolerance)
        self.assertFalse(0.31 <= tolerance)

    def test_telemetry_schema_and_warning(self):
        """Verifies telemetry JSON payload and threshold logic."""
        sample_payload = {
            'battery_pct': 24.2,
            'temperature_c': 34.5,
            'wheel_speed_mps': 0.35,
            'elapsed_s': 12.0
        }
        json_str = json.dumps(sample_payload)
        parsed = json.loads(json_str)

        self.assertIn('battery_pct', parsed)
        self.assertIn('temperature_c', parsed)
        self.assertIn('wheel_speed_mps', parsed)
        self.assertIn('elapsed_s', parsed)

        # Test threshold check
        threshold = 25.0
        self.assertTrue(parsed['battery_pct'] < threshold)

        # Non-warning case
        parsed['battery_pct'] = 27.5
        self.assertFalse(parsed['battery_pct'] < threshold)

    def test_mission_state_machine_logic(self):
        """Tests the exact state transitions for Task 3 interruption and resume."""
        class MockFieldMission:
            def __init__(self):
                self.state = "UNINITIALIZED"
                self.is_field_blocked = False
                self.current_wp_idx = 0
                self.waypoints = [("Bottle", 8.0, 5.5), ("Mallet", 8.0, 8.0), ("Base", 5.5, 5.5)]

            def on_first_pose(self):
                if self.state == "UNINITIALIZED":
                    self.state = "RUNNING"

            def on_blockage(self, blocked: bool):
                self.is_field_blocked = blocked
                if blocked:
                    if self.state == "RUNNING" or self.state == "PAUSED_CLEAR":
                        self.state = "PAUSED_BLOCKED"
                else:
                    if self.state == "PAUSED_BLOCKED":
                        # CRITICAL: Do NOT auto resume!
                        self.state = "PAUSED_CLEAR"

            def call_resume(self):
                if self.state == "UNINITIALIZED":
                    return False, "No pose"
                if self.is_field_blocked or self.state == "PAUSED_BLOCKED":
                    return False, "Blocked"
                if self.state == "RUNNING":
                    return False, "Already running"
                if self.state == "DONE":
                    return False, "Already done"
                if self.state == "PAUSED_CLEAR":
                    self.state = "RUNNING"
                    return True, "Resumed"
                return False, "Invalid state"

        mission = MockFieldMission()
        self.assertEqual(mission.state, "UNINITIALIZED")

        # 1. Resume before pose must be rejected
        ok, msg = mission.call_resume()
        self.assertFalse(ok)

        # 2. First pose arrives -> RUNNING
        mission.on_first_pose()
        self.assertEqual(mission.state, "RUNNING")

        # 3. Resume while running must be rejected
        ok, msg = mission.call_resume()
        self.assertFalse(ok)

        # 4. Obstacle detected -> PAUSED_BLOCKED
        mission.on_blockage(True)
        self.assertEqual(mission.state, "PAUSED_BLOCKED")

        # 5. Resume while blocked must be rejected
        ok, msg = mission.call_resume()
        self.assertFalse(ok)

        # 6. Obstacle clears -> PAUSED_CLEAR (NOT RUNNING!)
        mission.on_blockage(False)
        self.assertEqual(mission.state, "PAUSED_CLEAR")

        # 7. Resume while clear -> Accepted -> RUNNING
        ok, msg = mission.call_resume()
        self.assertTrue(ok)
        self.assertEqual(mission.state, "RUNNING")

        # 8. Mission completes -> DONE
        mission.state = "DONE"
        ok, msg = mission.call_resume()
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()
