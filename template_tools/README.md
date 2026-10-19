# template_tools

Generic bring-up scripts for a new robot. Copy them into your robot's repo,
edit the SETTINGS block at the top of the wheel scripts, and run them.

| Script | Purpose |
|---|---|
| `hold_all_wheels.py <pwm>` | Holds every channel at one PWM value. Use it to find the motor stall zone and check for jitter. |
| `test_each_wheel.py` | Drives each channel alone to verify wiring and channel order. |
| `joy_list_mapper.py` | Asks for 25 named controls one at a time, waits 10 s for each, and prints a summary of the `buttons[i]` and `axes[i]` that registered. It needs `joy_node` running, and uses ROS, so run it with `pixi run python3`. Edit `CONTROLS_TO_TEST` to change the list. |

The two wheel scripts send raw UDP to the microcontroller and bypass ROS, so
stop any ROS bridge sending to the same board first. Both refuse to run until
`ROBOT_IP` is edited. They assume an ASCII packet of comma-separated values
(`v1,v2,v3,v4`). Change the packet lines if your firmware differs.
