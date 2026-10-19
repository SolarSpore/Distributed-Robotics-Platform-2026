#!/usr/bin/env python3
"""
hold_all_wheels.py  (template)

Holds every wheel at one PWM value over raw UDP, bypassing ROS. Use it during
bring-up to find the stall zone of your motors/driver and to check for jitter
independent of the ROS/joystick path.

Usage: python3 hold_all_wheels.py <pwm>

Stop any ROS bridge that sends to the microcontroller before running this --
two senders at once shows up as motor stutter.
"""
import socket, sys, time

# ---- SETTINGS: edit these for your robot --------------------------------
ROBOT_IP = "192.168.X.X"   # IP address of the microcontroller
ROBOT_PORT = 4210          # UDP port the firmware listens on
NUM_WHEELS = 4             # comma-separated channels the firmware expects
HOLD_SECONDS = 8           # how long to hold the value
SEND_INTERVAL = 0.05       # seconds between packets (keep below the firmware failsafe timeout)
# Packet format assumed: ASCII "v1,v2,v3,v4". Change the cmd/stop lines below if your firmware differs.
# --------------------------------------------------------------------------

if "X" in ROBOT_IP:
    sys.exit("Edit ROBOT_IP at the top of this file first.")
if len(sys.argv) != 2:
    sys.exit("Usage: python3 hold_all_wheels.py <pwm>")

pwm = int(sys.argv[1])
cmd = ",".join([str(pwm)] * NUM_WHEELS).encode()
stop = ",".join(["0"] * NUM_WHEELS).encode()
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
addr = (ROBOT_IP, ROBOT_PORT)

print("Holding", cmd, "for", HOLD_SECONDS, "s")
try:
    end = time.time() + HOLD_SECONDS
    while time.time() < end:
        s.sendto(cmd, addr)
        time.sleep(SEND_INTERVAL)
finally:
    s.sendto(stop, addr)
