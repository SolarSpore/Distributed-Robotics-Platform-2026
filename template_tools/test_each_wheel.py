#!/usr/bin/env python3
"""
test_each_wheel.py  (template)

Drives each wheel channel alone over raw UDP, bypassing ROS. Use it with the
robot on blocks to verify wiring: the wheels should move one at a time, in the
order listed in WHEEL_NAMES, all forward.

Stop any ROS bridge that sends to the microcontroller before running this --
two senders at once shows up as motor stutter.
"""
import socket, sys, time

# ---- SETTINGS: edit these for your robot --------------------------------
ROBOT_IP = "192.168.X.X"                 # IP address of the microcontroller
ROBOT_PORT = 4210                        # UDP port the firmware listens on
WHEEL_NAMES = ["FL", "FR", "RL", "RR"]   # one entry per channel, in firmware order
TEST_PWM = 200                           # value sent to the wheel under test
RUN_SECONDS = 2.0                        # how long each wheel runs
PAUSE_SECONDS = 1.5                      # pause between wheels
SEND_INTERVAL = 0.05                     # seconds between packets
# Packet format assumed: ASCII "v1,v2,v3,v4". Change the cmd/stop lines below if your firmware differs.
# --------------------------------------------------------------------------

if "X" in ROBOT_IP:
    sys.exit("Edit ROBOT_IP at the top of this file first.")

n = len(WHEEL_NAMES)
stop = ",".join(["0"] * n).encode()
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
addr = (ROBOT_IP, ROBOT_PORT)

try:
    for i, name in enumerate(WHEEL_NAMES):
        values = ["0"] * n
        values[i] = str(TEST_PWM)
        cmd = ",".join(values).encode()
        print("Driving channel", name, "at", TEST_PWM)
        end = time.time() + RUN_SECONDS
        while time.time() < end:
            s.sendto(cmd, addr)
            time.sleep(SEND_INTERVAL)
        s.sendto(stop, addr)
        time.sleep(PAUSE_SECONDS)
    print("done")
finally:
    s.sendto(stop, addr)
