# Tools

Generic helper scripts for bringing up a new robot. They live in [`template_tools/`](template_tools/). Copy them into your robot's own folder before editing them.

| Tool | What it does | Run it with |
|---|---|---|
| `hold_all_wheels.py` | Holds every motor channel at one PWM value, to find the motor stall zone and check for jitter | `python3 hold_all_wheels.py <pwm>` |
| `test_each_wheel.py` | Drives each motor channel alone, to check wiring and channel order | `python3 test_each_wheel.py` |
| `joy_list_mapper.py` | Walks through 25 named controls (buttons, d-pad, sticks, triggers), waits 10 seconds for each, and prints a summary of the `buttons[i]` and `axes[i]` that registered | `cd ~/Robotics/ros2_ws && pixi run python3 <path>/joy_list_mapper.py` |

## Before you run the wheel tools

* Edit the SETTINGS block at the top of the file. Both scripts refuse to run until `ROBOT_IP` is changed from its placeholder.
* Both send raw UDP to the microcontroller and bypass ROS, so stop any ROS bridge that sends to the same board first. Two senders at once make the motors stutter.
* They assume an ASCII packet of comma-separated values (`v1,v2,v3,v4`). Change the packet lines if your firmware uses a different format.

## Before you run the controller mapper

It listens to `/joy`, so `joy_node` must be running (see the setup guide). It uses ROS, so run it through Pixi from the workspace folder. Edit the `CONTROLS_TO_TEST` list in the file to change which controls it asks for.
