# Task 4: "Explain It Like a Reel" - Spoken Video Script (60–90s)

**Speaker**: Mihiya (Student ID: 240041128)  
**Tone**: Casual, clear, energetic, confident. (Can be spoken in English, Bangla, or mixed Banglish).  
**Visuals on screen**: Split screen showing terminal with `mars_telemetry_publisher` on left and `mission_control_monitor` on right.

---

### [00:00 - 00:20] Hook & Everyday Analogy
"Hey everyone! When someone first hears 'ROS 2 publisher, subscriber, and topic', it sounds like abstract networking jargon. But think of it like an FM radio broadcast.

Imagine a radio host broadcasting commentary on 89.2 FM. The host doesn't need to know who is listening, and they don't dial individual phone numbers. They just speak into the microphone and transmit onto 89.2 FM. Anyone with a radio tuned to 89.2 FM hears the audio instantly. If ten tea stalls tune in, all ten hear it simultaneously. And if nobody tunes in at 3 AM? The transmitter still broadcasts smoothly without crashing.

In ROS 2, that broadcast frequency is a **Topic**!"

---

### [00:20 - 00:45] Pointing Out Our Real Code Components
"Let's look at our real code right here on my screen:
1. **The Publisher**: Our node `mars_telemetry_publisher`.
2. **The Topic**: `/rover/telemetry`.
3. **The Message Type**: `std_msgs/msg/String`, carrying a structured JSON payload with battery percentage, internal temperature, wheel speed, and elapsed time.
4. **The Subscriber**: `mission_control_monitor`.

Because topics are decoupled, we could easily launch a third node—like a black-box data logger or `ros2 topic echo`—and it would receive the exact same telemetry stream without touching a single line of our publisher's code!"

---

### [00:45 - 01:10] The Small Change & What The Subscriber Sees
"Now watch this quick live change:
In `mars_telemetry_publisher.py`, our default starting battery is 28%, depleting by 1% per second. Notice in the right terminal: at $T+0$ to $T+3$ seconds, Mission Control prints normal green telemetry info. But the moment battery drops to 24%, Mission Control immediately raises a red `[CRITICAL WARNING]` alert!

Now, let's change the parameter `--ros-args -p starting_battery_pct:=24.0`.
We re-run: the publisher emits 23.0% immediately on tick 1, and the subscriber instantly triggers the low-battery alarm from the very first second!"

---

### [01:10 - 01:30] What I Initially Misunderstood & What Made It Click
"One big thing I initially misunderstood was thinking a topic acted like an email inbox or database queue—where messages wait around forever until a subscriber opens them.

When I started my subscriber 10 seconds after the publisher, I wondered why it didn't print the older messages! That’s when it clicked: standard ROS 2 topics use **volatile durability**. It's a live stream—just like live radio, you only hear what's broadcast after you tune in!

That's the publisher-subscriber model in 90 seconds. Keep your nodes small, your topics typed, and your cha hot!"

---

## Banglish / Alternate Version for Reel:
*(Optional for recording in candidate's natural language)*:
"Assalamu Alaikum! ROS 2-er publisher-subscriber concept ta sohoje bujhar jonno FM radio-r kotha chinta kora jay..." (Included in candidate notes).
