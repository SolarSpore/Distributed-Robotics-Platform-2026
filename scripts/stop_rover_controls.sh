#!/bin/bash
# Intended location on the Steam Deck: ~/Robotics/stop_rover_controls.sh
pkill -INT -f rover_motor_bridge
pkill -f rover_wheel_test
pkill -f rover_control.launch
pkill -f "joy_node|teleop_node|rover_control_node"
pkill -f foxglove_bridge_launch
pkill -f "foxglove_bridge"
command -v notify-send >/dev/null && notify-send "Rover Controls" "Stopped."
