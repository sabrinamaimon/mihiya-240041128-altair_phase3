# Project Altair - Phase 3 Video Recording & Demonstration Guide

This guide provides the exact step-by-step commands, timings, and talking points to record high-scoring demonstration videos for each task.

---

## Candidate Video Introduction (Speak Once at Beginning)
> *"Hello! I am Mihiya, a student of the Computer Science and Engineering department, Student ID 240041128. This is my demonstration and technical explanation for Project Altair Software Recruitment Phase 3: The Turtle Has Field Duty."*

---

## Video 1: Task 1 - Rover Telemetry (Target Duration: 60–90 seconds)

### Objective:
Demonstrate two-node communication, simulated telemetry with units, low-battery warning below 25%, parameter modification, and code walkthrough of how data travels.

### Terminal Setup:
* **Terminal 1 (Publisher)**:
  ```bash
  source /opt/ros/humble/setup.bash
  source ~/altair_phase3_ws/install/setup.bash
  ros2 run altair_phase3 mars_telemetry_publisher
  ```
* **Terminal 2 (Subscriber / Mission Control)**:
  ```bash
  source /opt/ros/humble/setup.bash
  source ~/altair_phase3_ws/install/setup.bash
  ros2 run altair_phase3 mission_control_monitor
  ```

### Step-by-Step Script:
1. **Start both nodes**: Watch normal readings output once per second (1 Hz).
   - Point out fields & units: Battery (`%`), Internal Temperature (`°C`), Wheel Speed (`m/s`), Elapsed Time (`s`).
2. **Observe Warning**:
   - Starting at 28.0% and depleting at 1.0%/s, at $T=4\text{s}$ the battery drops to 24.0% (< 25%).
   - Show the red warning banner appear in Mission Control:
     `[CRITICAL WARNING] BATTERY BELOW 25.0%! Current: 24.0%`
3. **Change Parameter (Live Modification)**:
   - Restart publisher with higher depletion rate:
     ```bash
     ros2 run altair_phase3 mars_telemetry_publisher --ros-args -p starting_battery_pct:=24.0
     ```
   - Explain: *"Notice that by setting starting battery to 24%, the warning triggers on the very first published frame."*
4. **Code Walkthrough (How a reading travels)**:
   - Point to `mars_telemetry_publisher.py`: A 1 Hz timer fires `publish_telemetry()`, encodes the telemetry dictionary into a JSON string via `json.dumps()`, wraps it in a standard `std_msgs/msg/String`, and passes it to the DDS publisher.
   - The ROS 2 DDS middleware transports the packet over the `/rover/telemetry` topic to `mission_control_monitor.py`.
   - The subscriber callback decodes it via `json.loads()`, prints the formatted string, and runs the conditional check `battery < 25.0` to trigger the alert.

---

## Video 2: Task 2a - Turtle Driving Practice (Target Duration: 1–2 minutes)

### Objective:
Demonstrate the interactive driving menu, the three patterns (P, R, Z), invalid input handling, clean stop on quit, and explain turning mechanics.

### Terminal Setup:
* **Terminal 1 (Simulator)**:
  ```bash
  source /opt/ros/humble/setup.bash
  ros2 run turtlesim turtlesim_node
  ```
* **Terminal 2 (Controller)**:
  ```bash
  source /opt/ros/humble/setup.bash
  source ~/altair_phase3_ws/install/setup.bash
  ros2 run altair_phase3 turtle_driver
  ```

### Step-by-Step Script:
1. **Show Menu**: Show the terminal displaying `[P, R, Z, Q]`.
2. **Execute 'P' (Patrol)**:
   - Press `P` + Enter.
   - Turtle drives forward for 3.0 seconds, executes a 180° turn ($\pi$ radians), and drives forward 3.0 seconds back to within 0.5 units of the start.
   - Note the clean stop and return to the menu prompt.
3. **Execute 'R' (Rectangle)**:
   - Press `R` + Enter.
   - Turtle traces a rectangle with two distinctly different side lengths (3.0s on the long side, 1.5s on the short side, with 90° CCW turns at each vertex).
   - Comes to a full stop.
4. **Execute 'Z' (Zigzag)**:
   - Press `Z` + Enter.
   - Turtle executes three forward legs, alternating left (+60°) and right (-120°) turns between segments.
   - Comes to a full stop.
5. **Demonstrate Invalid Input**:
   - Type `X`, `INVALID`, or press Enter.
   - Show that the node prints `[INVALID INPUT] Unknown command` without crashing or freezing.
6. **Execute 'Q' (Quit)**:
   - Press `Q`.
   - Show the node publishing zero velocity and shutting down cleanly.
7. **Explain Turning Velocity**:
   - Point to code: *"In `geometry_msgs/msg/Twist`, linear forward/backward speed is controlled by `linear.x`, while rotational turning speed is controlled by `angular.z`. A positive `angular.z` produces a counter-clockwise (left) turn, while a negative `angular.z` produces a clockwise (right) turn."*

---

## Video 3: Task 2b - The Stop That Did Not Stick (Target Duration: 1–2 minutes)

### Objective:
Narrate the 3 architectural questions using your screen/sketch (refer to `docs/TASK_2B_ANALYSIS.md`).

### Talking Points:
1. **Why the stop didn't stick**:
   - Show diagram. *"The navigation node continuously sends forward commands at 10 Hz (every 100 ms). When the obstacle node sends just one stop message, the motor controller stops, but 100 ms later, the next 10 Hz forward message arrives and overwrites it. Topics don't arbitrate priority!"*
2. **CLI Inspection**:
   - Show `ros2 topic info /cmd_vel --verbose`.
   - Explain: *"This shows `Publisher count: 2`, proving both nodes are simultaneously registered to `/cmd_vel`. However, this output only proves endpoint existence; it does not prove publication frequency or message sequence. For that, we need `ros2 topic hz` and timestamped echoes."*
3. **Robust System Design**:
   - Show supervisor/mux diagram.
   - Explain command ownership (`twist_mux`), latched stop state requiring explicit human service resume (`/resume_mission`), and dual-threshold Schmitt trigger hysteresis ($d_{\text{stop}} < d_{\text{clear}}$) to prevent flickering near the threshold.

---

## Video 4: Task 3 - Three Stops Before Cha (Target Duration: 2–3 minutes)

### Objective:
Demonstrate the complete autonomous mission with mid-route blockage, rejection of resume while blocked, hold-pause after clearing, explicit resume, arrival at all three targets, and final stop.

### Terminal Setup:
* **Terminal 1 (Launch Node)**:
  ```bash
  source /opt/ros/humble/setup.bash
  source ~/altair_phase3_ws/install/setup.bash
  ros2 launch altair_phase3 field.launch.py
  ```
* **Terminal 2 (Mission Commander / Blockage Injector)**:
  ```bash
  source /opt/ros/humble/setup.bash
  ```

### Step-by-Step Script:
1. **Launch Mission**:
   - Run `ros2 launch altair_phase3 field.launch.py`.
   - Turtlesim opens and turtle starts navigating toward **Target 1: Bottle (8.0, 5.5)** using closed-loop heading and distance feedback.
2. **Inject Obstacle / Blockage Mid-Leg**:
   - While moving toward Bottle, run in Terminal 2:
     ```bash
     ros2 topic pub --once /field_blocked std_msgs/msg/Bool "{data: true}"
     ```
   - Watch the turtle halt immediately!
   - Terminal 1 logs: `[HAZARD ALERT] Obstacle detected! /field_blocked = True. Halting robot.`
3. **Attempt Resume While Blocked (Show Rejection)**:
   - In Terminal 2, run:
     ```bash
     ros2 service call /resume_mission std_srvs/srv/Trigger "{}"
     ```
   - Show response: `success: false, message: 'REJECTED: Cannot resume while route is reported BLOCKED.'`
4. **Clear Blockage & Demonstrate No Auto-Resume**:
   - In Terminal 2, run:
     ```bash
     ros2 topic pub --once /field_blocked std_msgs/msg/Bool "{data: false}"
     ```
   - Terminal 1 logs: `[HAZARD CLEARED] Blockage report cleared... Standing by in clear status.`
   - **Crucial Demo Moment**: Pause for 3–5 seconds and show that the turtle **remains completely stopped**!
   - Voiceover: *"Notice that simply clearing the hazard does NOT start the motors. The system requires an explicit authorization decision."*
   - Point to code in `field_mission.py` around line 90:
     `# Receiving False transitions to PAUSED_CLEAR instead of RUNNING.`
5. **Explicit Operator Resume**:
   - In Terminal 2, call:
     ```bash
     ros2 service call /resume_mission std_srvs/srv/Trigger "{}"
     ```
   - Show response: `success: true, message: 'ACCEPTED: Resuming navigation...'`
   - Turtle immediately resumes driving smoothly toward Bottle!
6. **Complete the Waypoints**:
   - Reaches **Bottle (8.0, 5.5)**: Logs `[ARRIVAL] Reached Target 1: 'Bottle'`.
   - Turns and drives to **Mallet (8.0, 8.0)**: Logs `[ARRIVAL] Reached Target 2: 'Mallet'`.
   - Turns and drives back to **Base (5.5, 5.5)**: Logs `[ARRIVAL] Reached Target 3: 'Base'`.
   - Logs: `[MISSION COMPLETE] All waypoints visited. Final Status: DONE.`
   - Turtle remains halted at Base; zero velocity is published; route does not restart!

---

## Video 5: Task 4 - Explain It Like a Reel (Target Duration: 60–90 seconds)
* Follow the dedicated script in `docs/REEL_SCRIPT_TASK4.md`.
