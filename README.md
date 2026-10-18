# Project Altair · Software Recruitment Batch 24 · Phase 3

## The Turtle Has Field Duty: A Practical Introduction to ROS 2


**Target Environment**: Ubuntu 22.04 LTS (ROS 2 Humble) / Ubuntu 24.04 LTS (ROS 2 Jazzy)  

---

## 1. System Requirements & Dependencies

This repository implements Phase 3 tasks for Project Altair Software Recruitment using ROS 2 (Humble / Jazzy).

### Core Dependencies:
* ROS 2 Distribution: `ros-humble-desktop` or `ros-jazzy-desktop`
* `ros-humble-turtlesim` (or `ros-jazzy-turtlesim`)
* `python3-colcon-common-extensions`
* Standard ROS 2 interface packages:
  - `rclpy`
  - `std_msgs`
  - `geometry_msgs`
  - `std_srvs`
  - `turtlesim`

### Installation Command (Ubuntu):
```bash
# Sourcing base ROS 2 (e.g. Humble)
source /opt/ros/humble/setup.bash

# Install turtlesim simulator and colcon build tools
sudo apt update && sudo apt install -y \
  ros-humble-turtlesim \
  python3-colcon-common-extensions
```

---

## 2. Workspace Setup & Build Instructions

Follow the exact workspace layout specified in Phase 3 Resources:

```bash
# 1. Create and navigate to the workspace
mkdir -p ~/altair_phase3_ws/src
cd ~/altair_phase3_ws/src

# 2. Clone this repository into src/
git clone https://github.com/sabrinamaimon/mihiya-240041128-altair_phase3.git altair_phase3

# 3. Build the workspace using colcon
cd ~/altair_phase3_ws
colcon build --symlink-install --packages-select altair_phase3

# 4. Source the overlay setup file (run this in every new terminal)
source /opt/ros/humble/setup.bash
source ~/altair_phase3_ws/install/setup.bash
```

---

## 3. Package Structure & Registered Executables

The `altair_phase3` package provides the following nodes:

| Executable Name | Module Path | Purpose |
| :--- | :--- | :--- |
| `mars_telemetry_publisher` | `altair_phase3.mars_telemetry_publisher:main` | Task 1: 1 Hz telemetry publisher with units & simulated battery/temperature |
| `telemetry_pub` | `altair_phase3.mars_telemetry_publisher:main` | Task 1: Convenient alias for publisher |
| `mission_control_monitor` | `altair_phase3.mission_control_monitor:main` | Task 1: Mission control subscriber with low-battery warning (< 25%) |
| `turtle_driver` | `altair_phase3.turtle_driver:main` | Task 2a: Menu-driven controller (`P`, `R`, `Z`, `Q`) |
| `field_mission` | `altair_phase3.field_mission:main` | Task 3: Autonomous waypoint navigation with pause & safe resume |

---

## 4. Run Instructions by Task

### Task 1: Rover Telemetry (1 Hz with Low-Battery Warning)
In **Terminal A** (Publisher):
```bash
source ~/altair_phase3_ws/install/setup.bash
ros2 run altair_phase3 mars_telemetry_publisher
```
In **Terminal B** (Mission Control Monitor):
```bash
source ~/altair_phase3_ws/install/setup.bash
ros2 run altair_phase3 mission_control_monitor
```
* **Custom parameter demo (e.g. instant low battery warning)**:
  ```bash
  ros2 run altair_phase3 mars_telemetry_publisher --ros-args -p starting_battery_pct:=24.0
  ```

---

### Task 2a: Turtle Driving Practice (Interactive Menu)
In **Terminal A** (Simulator):
```bash
ros2 run turtlesim turtlesim_node
```
In **Terminal B** (Controller):
```bash
source ~/altair_phase3_ws/install/setup.bash
ros2 run altair_phase3 turtle_driver
```
* Select commands from terminal menu:
  - `P` : **Patrol** (Forward 3s $\to$ turn 180° $\to$ return ~3s near start)
  - `R` : **Rectangle** (Traces 3.0m $\times$ 1.5m rectangle with 90° turns)
  - `Z` : **Zigzag** (3 forward segments with alternating turns)
  - `Q` : **Quit** (Sends stop velocity and cleanly shuts down)
* Enter invalid characters (e.g. `X`) to demonstrate robust, crash-free input handling.

---

### Task 2b: Architectural Analysis ("The Stop That Did Not Stick")
* See complete analysis, CLI output proofs, and supervisor architecture in [`docs/TASK_2B_ANALYSIS.md`](docs/TASK_2B_ANALYSIS.md).

---

### Task 3: Three Stops Before Cha (Autonomous Waypoints & Interruption)

#### One-Command Launch:
We provide a unified launch file that starts both `turtlesim` and `field_mission`:
```bash
source ~/altair_phase3_ws/install/setup.bash
ros2 launch altair_phase3 field.launch.py
```

#### How the Launch File Works:
`field.launch.py` uses `launch_ros.actions.Node` to concurrently instantiate:
1. `turtlesim/turtlesim_node`: Simulator window.
2. `altair_phase3/field_mission`: Closed-loop controller node that awaits first pose and navigates targets in sequence:
   - Target 1: **Bottle** $(8.0, 5.5)$
   - Target 2: **Mallet** $(8.0, 8.0)$
   - Target 3: **Base** $(5.5, 5.5)$

#### Demonstrating the Interruption & Safe Resume:
In a second terminal:
```bash
source /opt/ros/humble/setup.bash

# 1. Inject Blockage Mid-Leg (Turtle halts immediately!)
ros2 topic pub --once /field_blocked std_msgs/msg/Bool "{data: true}"

# 2. Attempt to Resume While Blocked (Rejected!)
ros2 service call /resume_mission std_srvs/srv/Trigger "{}"

# 3. Clear Blockage Report (Turtle stays stationary - NO auto resume!)
ros2 topic pub --once /field_blocked std_msgs/msg/Bool "{data: false}"

# 4. Operator Authorization Decision (Turtle resumes navigation!)
ros2 service call /resume_mission std_srvs/srv/Trigger "{}"
```

---

## 5. Task 4: Explain It Like a Reel
* Complete 60–90s spoken script, everyday FM radio analogy, and code walkthrough: [`docs/REEL_SCRIPT_TASK4.md`](docs/REEL_SCRIPT_TASK4.md).

---

## 6. Video Walkthrough & Recording Script
* Detailed recording checklist, screen layout, and timestamps: [`docs/VIDEO_DEMO_WALKTHROUGH.md`](docs/VIDEO_DEMO_WALKTHROUGH.md).

