# Task 2b: The Stop That Did Not Stick (Deep Architectural Analysis)

**Author**: Mihiya (Student ID: 240041128)  
**Project Altair · Recruitment Batch 24 · Phase 3 Assessment**

---

## 1. Why Can a Valid Stop Message Arrive Without Keeping the Rover Stopped?

### The Core Root Cause: Asynchronous Overwrite & Topic Memorylessness
ROS 2 topics are **stateless and memoryless communication pipes** governed by a publish-subscribe bus model. A topic does **not** arbitrate priority, maintain ownership, or merge competing streams from multiple publishers.

In this scenario:
1. The **autonomous navigation node** publishes forward velocity commands (`linear.x = 0.5, angular.z = 0.0`) to `/cmd_vel` periodically at **10 Hz** (one message every 100 ms).
2. The **obstacle detector node** encounters a hazard and fires **a single, one-off zero-velocity message** (`linear.x = 0.0, angular.z = 0.0`) to `/cmd_vel`.
3. The **motor controller** (subscriber) executes whichever message arrived most recently in its subscriber queue.
4. When the stop message arrives at time $t_0$, the motor controller stops the wheels.
5. However, exactly $\approx 100\text{ ms}$ later (at $t_0 + 0.1\text{ s}$), the next scheduled timer tick from the autonomous navigation node arrives on `/cmd_vel` with forward velocity.
6. Because the navigation node is completely unaware that an obstacle stopped the rover, its next forward message **overwrites** the stop command instantly. The rover jerks to a stop for less than a tenth of a second, and immediately resumes driving forward toward the obstacle!

```
Time (ms)  -------------------------------------------------------------------->
Nav Node:       [Forward] ---- (100ms) ----> [Forward] ------------> [Forward]
Obstacle Node:                  [STOP (0,0)]
Topic /cmd_vel: [Forward] ----------> [STOP] ----------> [Forward] (OVERWRITTEN!)
Motor State:    DRIVING ------------> STOPPED (100ms) -> DRIVING FORWARD!
```

---

## 2. ROS 2 CLI Inspection: Command, Output, and Evidence Limits

### The Inspection Command
To inspect the publishers on the topic, run:
```bash
ros2 topic info /cmd_vel --verbose
```

### Expected Output (Annotated Example)
```text
[EXAMPLE OUTPUT]
Type: geometry_msgs/msg/Twist
Publisher count: 2
Subscription count: 1

Node name: /autonomous_nav_node
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Endpoint type: PUBLISHER
GID: 01.0f.a4.12.89.01...
QoS profile:
  Reliability: RELIABLE
  Durability: VOLATILE
  Lifespan: 9223372036854775807 nanoseconds
  Deadline: 9223372036854775807 nanoseconds
  Liveliness: AUTOMATIC
  Liveliness lease duration: 9223372036854775807 nanoseconds

Node name: /obstacle_detector_node
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Endpoint type: PUBLISHER
GID: 01.0f.a4.12.89.02...
QoS profile:
  Reliability: RELIABLE
  Durability: VOLATILE
  ...
```

### What This Output Proves vs. What You Still Need to Observe
* **What the output PROVES**:
  1. It proves there are **multiple publishers** (`Publisher count: 2`) actively registered on `/cmd_vel`.
  2. It identifies the exact competing node endpoints (`/autonomous_nav_node` and `/obstacle_detector_node`).
  3. It proves that the obstacle node is directly publishing to `/cmd_vel` rather than routing through a safety coordinator or supervisor.

* **What the output DOES NOT prove (What you still need to observe)**:
  1. **Message Rates and Frequencies**: `ros2 topic info --verbose` shows active endpoints, but does **not** reveal how often each node publishes. To observe that `/autonomous_nav_node` publishes at 10 Hz while `/obstacle_detector_node` only sent a single pulse, you must run:
     ```bash
     ros2 topic hz /cmd_vel
     ```
  2. **Message Sender Attribution**: Standard `ros2 topic echo /cmd_vel` prints incoming Twist payloads, but the message itself does **not** contain the sender's node name. You cannot tell from payload alone which node emitted which zero or non-zero vector without timestamp correlation or ROS 2 tracing (`ros2 trace` / DDS monitoring).
  3. **Controller Arbitration**: The CLI cannot reveal internal motor controller logic (e.g. timeout watchdog, priority queues, or hardware execution).

---

## 3. How to Arrange the Command Path: Command Ownership & Safe Resume

To prevent competing publishers from clobbering each other, we must establish **clear command ownership** and a **state-latched safety supervisor**.

### Architecture: Priority Command Multiplexer & State-Latched Supervisor

```
+--------------------------+
|  Autonomous Navigation   |-----> /nav_cmd_vel (10 Hz)
+--------------------------+             |
                                         v
+--------------------------+      +-------------------------+      +------------------+
|  Obstacle Detector       |----->| Altair Twist Mux /      |----->| Motor Controller |
|  (with Dual Hysteresis)  |      | Safety Supervisor Node  |      | (/cmd_vel)       |
+--------------------------+      +-------------------------+      +------------------+
             |                               ^
     /field_blocked                          |
             |                               |
             +-------------------------------+
                             ^
                             | /resume_mission (std_srvs/srv/Trigger)
                     [Operator Console]
```

### 1. Dedicated Command Routing (Twist Mux / Supervisor)
* The autonomous navigation node must **never** publish directly to the hardware `/cmd_vel` topic. Instead, it publishes to an intermediate topic, e.g. `/nav_cmd_vel`.
* A **Safety Supervisor / Command Multiplexer node** (`twist_mux` or custom Altair supervisor) is the **sole publisher** to the hardware `/cmd_vel`.
* The supervisor listens to:
  - `/nav_cmd_vel` (priority 10 - lowest)
  - `/teleop_cmd_vel` (priority 50 - intermediate)
  - `/obstacle_stop` or safety latch (priority 100 - highest)

### 2. Latching State Machine with Explicit Resume
* When an obstacle is detected, the supervisor enters `ESTOP` / `LATCHED_PAUSED` state.
* The supervisor continuously publishes zero velocity (`linear=0, angular=0`) at 10 Hz, actively overriding any lower-priority navigation commands.
* **Separation of "Clear" vs "Authorized"**:
  - When the obstacle disappears, the obstacle topic publishes `blocked = false`.
  - **Crucial Rule**: The supervisor clears the obstruction flag, but **remains in PAUSED state**.
  - Motion is **only** resumed when the human operator explicitly sends a confirmation service call (`/resume_mission`).

### 3. Handling Sensor Flickering Near Threshold (Hysteresis & Debouncing)
When an obstacle hovers right at the detection boundary (e.g., $1.0\text{ m}$), sensor noise causes the reading to oscillate rapidly above and below the threshold ($0.99\text{ m} \leftrightarrow 1.01\text{ m}$), causing rapid alternating stop-go jitter.

We solve this using **Dual-Threshold Schmitt-Trigger Hysteresis** and **Temporal Debouncing**:
1. **Dual Distance Thresholds**:
   - Trigger Stop when: $d < d_{\text{stop}} = 1.0\text{ m}$.
   - Clear Obstacle only when: $d > d_{\text{clear}} = 1.3\text{ m}$ (a $30\text{ cm}$ safety buffer).
2. **Persistence Filter / Debounce Window**:
   - The obstacle signal must remain clear for at least $N = 10$ consecutive cycles (e.g. $1.0\text{ second}$) before the supervisor transitions from `BLOCKED` to `PAUSED_CLEAR`.
   - This eliminates false-positive clearing from momentary sensor dropouts.

---

## Summary Table for Quick Reference

| Problem Aspect | Root Cause in Naive System | Robust Architecture Solution |
| :--- | :--- | :--- |
| **Stop does not stick** | 10 Hz nav messages overwrite single stop pulse on shared topic | Dedicated supervisor/mux is sole owner of `/cmd_vel` |
| **Unintended restart** | Clearing hazard automatically restarts motors | Latched state machine requiring explicit `/resume_mission` |
| **Threshold flickering** | Single distance boundary oscillates with sensor noise | Dual-threshold hysteresis ($d_{\text{stop}} < d_{\text{clear}}$) + temporal debounce |
