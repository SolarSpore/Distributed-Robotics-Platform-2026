#!/bin/bash
# Rover Controls: teleop (rover_control) + UDP bridge (rover_motor_bridge) +
# foxglove_bridge, all detached. Meant to run from a desktop icon, not a
# terminal. Intended location on the Steam Deck: ~/Robotics/start_rover_controls.sh
PIXI=/home/deck/.pixi/bin/pixi
WS=/home/deck/Robotics/ros2_ws
LOGDIR=/home/deck/Robotics/logs
LOCKFILE=/tmp/rover_controls.lock

mkdir -p "$LOGDIR"
cd "$WS" || exit 1

# Refuse to run a second copy while one is already starting or running.
# Without this, a double-click (or a click while an earlier launch is still
# mid-startup) stacks a second full set of nodes on top of the first, and
# both send competing commands to the ESP32.
exec 9>"$LOCKFILE"
if ! flock -n 9; then
  echo "Rover Controls is already starting/running (lock held). Not launching again."
  command -v notify-send >/dev/null && notify-send "Rover Controls" "Already running - not starting a second copy."
  exit 1
fi

wait_gone() {  # $1 = pkill pattern, $2 = seconds to wait
  local pattern="$1" timeout="$2" waited=0
  while pgrep -f "$pattern" > /dev/null; do
    if [ "$waited" -ge "$timeout" ]; then
      echo "Force-killing leftover: $pattern"
      pkill -9 -f "$pattern"
      sleep 1
      break
    fi
    sleep 0.5
    waited=$((waited + 1))
  done
}

# Ask nicely first, then wait, then force.
pkill -INT -f rover_motor_bridge
pkill -f rover_wheel_test
pkill -f rover_control.launch
pkill -f "joy_node|teleop_node|rover_control_node"
pkill -f foxglove_bridge_launch
pkill -f "foxglove_bridge"

for pattern in rover_motor_bridge rover_wheel_test rover_control.launch "joy_node|teleop_node|rover_control_node" foxglove_bridge_launch foxglove_bridge; do
  wait_gone "$pattern" 6
done

start() {  # $1 = log name, $2 = ros2 command
  # 9>&- closes the lock fd before the process is backgrounded, so this
  # long-running child (and everything it execs into) doesn't inherit it.
  # Without this, the lock stays held for as long as the rover session is
  # running even after this script exits, and a later "already running"
  # check can wrongly fire hours later against a process with no name match.
  setsid nohup "$PIXI" run bash -c "source install/setup.bash && exec $2" \
    9>&- > "$LOGDIR/$1.log" 2>&1 < /dev/null &
  disown $!
}

start foxglove "ros2 launch foxglove_bridge foxglove_bridge_launch.xml -a"
start teleop "ros2 launch rover_control rover_control.launch.py"
sleep 3
start bridge "ros2 launch rover_motor_bridge rover_motor_bridge.launch.py max_linear_speed:=1.5 min_pwm:=110"

command -v notify-send >/dev/null && notify-send "Rover Controls" "Started. Hold L1 to drive."
