# Installing the platform on a Steam Deck

This guide takes a Steam Deck from a fresh system to a working ROS 2 robot computer. It covers:

1. Pixi and a ROS 2 Humble workspace (nothing is installed system-wide)
2. The gamepad
3. Foxglove (the bridge, and Foxglove Studio in a container)
4. Putting the node templates in the right place, editing them and building them
5. Starting everything from a desktop shortcut
6. The bring-up tools, a short note on firmware, and a command cheat sheet

Tested on SteamOS with Pixi 0.79, ROS 2 Humble (RoboStack), a Wayland session and Foxglove Studio 3.1.1. All commands run in Desktop Mode, in Konsole. Paths assume the default `deck` user: launchers and scripts use full `/home/deck/...` paths, because they do not inherit your shell's PATH.

## 0. Folder structure

This is the layout the guide builds. Your robot gets its own folder next to `ros2_ws`.

```text
~/Robotics/
├── ros2_ws/        the Pixi workspace: pixi.toml, pixi.lock, src/ (links to your packages), build/, install/
├── MyRobot/        your robot's ROS packages (one folder per package)
├── Shortcuts/      start and stop scripts for the desktop icons
├── tools/          bring-up scripts copied from template_tools/
└── logs/           one log file per started process
~/Desktop/          the icons that call the scripts in ~/Robotics/Shortcuts
~/.local/bin/       the Foxglove Studio launcher script
~/repos/Distributed-Robotics-Platform-2026/    this repository (templates, tools, docs)
```

## 1. Install Pixi

Pixi runs ROS 2 Humble entirely inside your home folder. Nothing is installed system-wide, so SteamOS updates do not break it and the read-only root filesystem is never touched.

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

Open a new Konsole (the installer adds `~/.pixi/bin` to PATH in `~/.bashrc`) and check:

```bash
pixi --version
```

## 2. Create the ROS 2 workspace

```bash
mkdir -p ~/Robotics && cd ~/Robotics
pixi init ros2_ws -c robostack-humble -c conda-forge
cd ros2_ws
pixi add ros-humble-desktop ros-humble-foxglove-bridge colcon-common-extensions qt-wayland
```

- `ros-humble-desktop`: ROS 2 Humble with the standard tools
- `ros-humble-foxglove-bridge`: serves ROS topics to Foxglove Studio
- `colcon-common-extensions`: the build tool
- `qt-wayland`: lets GUI tools run in the Deck's Wayland session

The first run downloads everything into the workspace's `.pixi` folder and takes several minutes.

## 3. Check that it works

```bash
cd ~/Robotics/ros2_ws
pixi run bash -c 'echo $ROS_DISTRO; ros2 pkg list | wc -l'
```

It should print `humble` and a few hundred packages.

- `pixi run <command>` runs one command inside the environment. Use it in scripts and launchers, and call Pixi by its full path there: `/home/deck/.pixi/bin/pixi`.
- `pixi shell` opens an interactive shell inside the environment, for typing several `ros2` commands.
- Anything that uses your own packages also needs `source install/setup.bash` in the workspace folder, after the first build (section 6).

## 4. The gamepad

With Steam running, the Deck's controls appear as a virtual Xbox 360 gamepad at `/dev/input/js0`:

```bash
ls /dev/input/js*
```

ROS reads it through `joy_node`, which publishes `/joy`. Start it in one Konsole and watch the messages from another:

```bash
cd ~/Robotics/ros2_ws && pixi run ros2 run joy joy_node
```

```bash
cd ~/Robotics/ros2_ws && pixi run ros2 topic echo /joy --once
```

To find the number of each button and axis, run the controller mapper with `joy_node` running. It asks for 25 controls one at a time, waits 10 seconds for each, and prints a summary of the `buttons[i]` and `axes[i]` it saw:

```bash
cd ~/Robotics/ros2_ws && pixi run python3 ~/repos/Distributed-Robotics-Platform-2026/template_tools/joy_list_mapper.py
```

Those numbers go into your control node's parameters (section 7).

## 5. Foxglove

Foxglove has two parts. `foxglove_bridge` is a ROS node: it comes from Pixi (section 2) and serves ROS topics over a WebSocket on port 8765. Foxglove Studio is the viewer, and it runs in a container because SteamOS does not allow system-wide installs.

### 5a. The bridge

```bash
cd ~/Robotics/ros2_ws && pixi run ros2 launch foxglove_bridge foxglove_bridge_launch.xml
```

Leave it running (Ctrl+C stops it). The desktop shortcut in section 8 starts it for you.

### 5b. Foxglove Studio in a Distrobox container

SteamOS 3.5 and later ships with Distrobox and Podman, so no setup is needed first. Create an Ubuntu container named `foxglove`:

```bash
distrobox create --name foxglove --image ubuntu:24.04
distrobox enter foxglove -- echo "container ready"
```

Download the Linux amd64 `.deb` package of Foxglove Studio from Foxglove's website into `~/Downloads`. The container shares your home folder, so it can see the file. Check the file name, then install it inside the container:

```bash
ls ~/Downloads/*.deb
distrobox enter foxglove -- sudo apt update
distrobox enter foxglove -- sudo apt install -y ~/Downloads/foxglove-studio-*.deb
distrobox enter foxglove -- bash -c 'dpkg -l | grep -i foxglove; ls /opt/Foxglove | head'
```

Expected: a line for `foxglove-studio` and the application's files in `/opt/Foxglove`. If the file name is different, change the `foxglove-studio-*.deb` part.

These commands rebuild the container this guide was written on. They have not yet been run from a clean Deck, so report any step that fails.

### 5c. A launcher for Foxglove Studio

The script sets the variables the Wayland session needs, then runs Studio fullscreen inside the container:

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/foxglove-steamdeck.sh <<'EOF'
#!/bin/bash

export XDG_RUNTIME_DIR=/run/user/1000
export WAYLAND_DISPLAY=wayland-0
export QT_QPA_PLATFORM=wayland

exec /usr/bin/distrobox-enter -n foxglove -- \
  /opt/Foxglove/foxglove-studio \
  --ozone-platform=wayland \
  --start-fullscreen \
  --foreground
EOF
chmod +x ~/.local/bin/foxglove-steamdeck.sh
```

And a desktop icon that runs it:

```bash
cat > ~/Desktop/foxglove-steamdeck.desktop <<'EOF'
[Desktop Entry]
Name=Foxglove Studio
Comment=Robot visualization and control
Exec=/home/deck/.local/bin/foxglove-steamdeck.sh
Terminal=false
Type=Application
Icon=foxglove-studio
Categories=Development;Utility;
StartupNotify=true
EOF
chmod +x ~/Desktop/foxglove-steamdeck.desktop
```

KDE may ask you to right-click a new icon and allow it to run, the first time.

### 5d. Connect

Start the bridge (section 5a), open Foxglove Studio, choose Open connection, pick Foxglove WebSocket, and enter:

```text
ws://localhost:8765
```

Foxglove can export a layout (your arrangement of panels) as a JSON file and import it again. Keep exported layouts in your robot's repository so the dashboard can be rebuilt on another Deck.

## 6. Build and run your robot's packages

Put your ROS packages (or symlinks to them) in `ros2_ws/src/`, then build:

```bash
cd ~/Robotics/ros2_ws
pixi run colcon build --symlink-install
```

Run one node, or list topics:

```bash
pixi run bash -c 'source install/setup.bash && ros2 run <package> <executable>'
pixi run bash -c 'source install/setup.bash && ros2 topic list'
```

`--symlink-install` makes Python edits take effect without rebuilding. Rebuild after changing `setup.py`, `package.xml` or launch files.

## 7. Use the node templates

The repository has a starting package in `Node-templates/ros2/robot_template`. It is a pattern, not a driver: it contains no IP address, port, pin or controller mapping. You copy it, rename it, and fill in your robot's hardware.

| File in the package | What it is | What you edit |
|---|---|---|
| `robot_control_node.py` | Reads `joy`, publishes `cmd_vel` | Parameters: `enable_button` (default 0), `turbo_button` (1), `axis_linear` (1), `axis_angular` (0), `scale_linear` (0.5), `scale_angular` (1.0). Turbo doubles the speed |
| `robot_motor_bridge.py` | Reads `cmd_vel`, sends a drive command at `send_rate_hz` (20) and stops after `cmd_vel_timeout` (0.5 s) | The empty functions `send_drive_command`, `stop_hardware` and `shutdown_hardware` |
| `robot_peripherals_bridge.py` | Reads `head/angle` (Float32) and `buzzer/beep` (Int32), publishes `ultrasonic/range` (Range) | The empty functions `send_head_command`, `send_buzzer_command`, `poll_telemetry` and `shutdown_hardware` |
| `launch/robot_template.launch.py` | Starts the three nodes | Nothing, unless you add nodes |
| `package.xml`, `setup.py`, `setup.cfg` | Package definition | Only the name (done by the commands below) and the description |

### 7a. Get the repository

```bash
mkdir -p ~/repos
git clone https://github.com/SolarSpore/Distributed-Robotics-Platform-2026.git ~/repos/Distributed-Robotics-Platform-2026
```

### 7b. Copy the template and rename it

Pick a package name (lowercase letters and underscores) and a folder for your robot's packages. These commands copy the template, rename its folders and files, and replace the name everywhere inside the copy. The original in the repository is not touched.

```bash
NAME=my_robot              # EDIT: your package name
ROBOT=~/Robotics/MyRobot   # EDIT: the folder that holds your robot's packages
mkdir -p "$ROBOT"
cp -r ~/repos/Distributed-Robotics-Platform-2026/Node-templates/ros2/robot_template "$ROBOT/$NAME"
cd "$ROBOT/$NAME"
mv robot_template "$NAME"
mv resource/robot_template "resource/$NAME"
mv launch/robot_template.launch.py "launch/$NAME.launch.py"
grep -rl robot_template . --exclude-dir=__pycache__ | xargs sed -i "s/robot_template/$NAME/g"
```

Check the result. The first command should print nothing, and the second should show your new name in every path:

```bash
grep -rn robot_template . --exclude-dir=__pycache__
find . -type f | sort
```

The three nodes keep their names (`robot_control_node`, `robot_motor_bridge`, `robot_peripherals_bridge`). Rename them later if you wish, in `setup.py` (`entry_points`) and in the launch file.

### 7c. Edit the nodes

Open the files in any editor, for example Kate:

```bash
kate "$ROBOT/$NAME/$NAME/robot_motor_bridge.py" "$ROBOT/$NAME/$NAME/robot_peripherals_bridge.py" "$ROBOT/$NAME/$NAME/robot_control_node.py" &
```

Fill in the empty functions with your robot's own protocol (UDP, serial, CAN, a vendor API). Keep the structure and the safety behavior: the command timeout, the stop on shutdown, and the deadman (`enable_button`). Keep robot-specific values (IP addresses, ports, pins, wheel geometry, button numbers) in parameters with defaults, not scattered through the code.

### 7d. Link it into the workspace, build and run

```bash
ln -s "$ROBOT/$NAME" ~/Robotics/ros2_ws/src/$NAME
cd ~/Robotics/ros2_ws
pixi run colcon build --symlink-install --packages-select $NAME
pixi run bash -c "source install/setup.bash && ros2 launch $NAME $NAME.launch.py"
```

The template launch file starts only the three template nodes. Start `joy_node` in another Konsole (section 4). To check the control node, hold button 0 (A) and move the left stick, then watch the output in a third Konsole:

```bash
cd ~/Robotics/ros2_ws && pixi run ros2 topic echo /cmd_vel
```

Set parameters when running a node directly:

```bash
pixi run bash -c "source install/setup.bash && ros2 run $NAME robot_control_node --ros-args -p enable_button:=9 -p axis_linear:=1"
```

## 8. Start everything from a desktop shortcut

A shortcut is a `.desktop` file on the Desktop. Its `Exec=` line holds the full path of a script. The script does the work: it calls Pixi by its full path, enters the workspace, and starts each part detached, with one log file per part. One click can start the Foxglove bridge, `joy_node` and your robot's launch file together.

### 8a. The scripts

These start and stop `foxglove_bridge`, `joy_node` and your launch file. Change `NAME` in both files to your package name. Stopping sends Ctrl+C (SIGINT) first, so your bridge's shutdown code runs and the hardware gets its stop command.

```bash
mkdir -p ~/Robotics/Shortcuts ~/Robotics/logs
cat > ~/Robotics/Shortcuts/start_my_robot.sh <<'EOF'
#!/bin/bash
# Starts foxglove_bridge, joy_node and the robot's launch file, all detached.
NAME=my_robot                     # EDIT: your package name
PIXI=/home/deck/.pixi/bin/pixi
WS=/home/deck/Robotics/ros2_ws
LOGDIR=/home/deck/Robotics/logs
LOCKFILE=/tmp/$NAME.lock

mkdir -p "$LOGDIR"
cd "$WS" || exit 1

# Refuse to start a second copy while one is starting.
exec 9>"$LOCKFILE"
if ! flock -n 9; then
  command -v notify-send >/dev/null && notify-send "$NAME" "Already starting or running."
  exit 1
fi

# Stop leftovers from an earlier run.
pkill -INT -f "ros2_ws/install/$NAME"
pkill -f "ros2 launch $NAME"
pkill -f joy_node
pkill -f foxglove_bridge
sleep 2

start() {  # $1 = log name, $2 = ros2 command
  setsid nohup "$PIXI" run bash -c "source install/setup.bash && exec $2" \
    9>&- > "$LOGDIR/$1.log" 2>&1 < /dev/null &
  disown $!
}

start foxglove "ros2 launch foxglove_bridge foxglove_bridge_launch.xml"
start joy "ros2 run joy joy_node"
start robot "ros2 launch $NAME $NAME.launch.py"

command -v notify-send >/dev/null && notify-send "$NAME" "Started."
EOF

cat > ~/Robotics/Shortcuts/stop_my_robot.sh <<'EOF'
#!/bin/bash
NAME=my_robot                     # EDIT: your package name
pkill -INT -f "ros2_ws/install/$NAME"
pkill -f "ros2 launch $NAME"
pkill -f joy_node
pkill -f foxglove_bridge
command -v notify-send >/dev/null && notify-send "$NAME" "Stopped."
EOF
chmod +x ~/Robotics/Shortcuts/start_my_robot.sh ~/Robotics/Shortcuts/stop_my_robot.sh
```

Why the details matter:

- `9>&-` closes the lock file for the started process, so the lock is released as soon as the script exits.
- `setsid nohup ... &` plus `disown` detach each process, so closing the launcher does not stop it.
- The `pkill` patterns match the workspace path and the launch command, not just the package name, so an editor with one of your files open is not stopped.
- Do not run the template's `joy_node` twice: two `joy_node`s fight over the gamepad.

### 8b. The icons

```bash
cat > ~/Desktop/MyRobotControls.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=My Robot Controls
Comment=Start the robot (right-click for Stop)
Exec=/home/deck/Robotics/Shortcuts/start_my_robot.sh
Icon=input-gaming
Terminal=false
Categories=Utility;
Actions=Stop;

[Desktop Action Stop]
Name=Stop My Robot
Exec=/home/deck/Robotics/Shortcuts/stop_my_robot.sh
EOF
chmod +x ~/Desktop/MyRobotControls.desktop
```

Double-click the icon to start. Right-click it and choose Stop to stop. Each part writes its own log in `~/Robotics/logs`:

```bash
ls -l ~/Robotics/logs
tail -n 5 ~/Robotics/logs/robot.log
```

## 9. Bring-up tools

`template_tools/` has generic scripts for a new robot. Copy them into your robot's folder, edit the SETTINGS block at the top of each file, and run them with the robot on blocks:

```bash
mkdir -p ~/Robotics/tools
cp -n ~/repos/Distributed-Robotics-Platform-2026/template_tools/*.py ~/Robotics/tools/
```

- `hold_all_wheels.py <pwm>` holds every motor channel at one PWM value, to find the stall zone and check for jitter.
- `test_each_wheel.py` drives each channel alone, to check wiring and channel order.

Both send raw UDP to the microcontroller and bypass ROS. They refuse to run until `ROBOT_IP` is edited, and they assume an ASCII packet of comma-separated values (`v1,v2,v3,v4`): change the packet lines if your firmware differs. Stop any ROS bridge that sends to the same board first, because two senders at once make the motors stutter. See `ToolsReadme.md` for every tool.

## 10. Firmware

The microcontroller side is specific to each robot, so the platform does not provide firmware. The usual setup is a separate PC (a laptop works well) with Visual Studio Code and the PlatformIO IDE extension: create or open a PlatformIO project for your board, upload over USB the first time, and add OTA (over-the-air) upload once the board is on your Wi-Fi. A robot repository built on this platform should document its own flashing steps.

## 11. Command cheat sheet

| Task | Command |
|---|---|
| Install Pixi | `curl -fsSL https://pixi.sh/install.sh \| bash` |
| Check the environment | `cd ~/Robotics/ros2_ws && pixi run bash -c 'echo $ROS_DISTRO'` |
| Interactive shell | `cd ~/Robotics/ros2_ws && pixi shell` |
| Build everything | `cd ~/Robotics/ros2_ws && pixi run colcon build --symlink-install` |
| Build one package | `pixi run colcon build --symlink-install --packages-select <package>` |
| Run a node | `pixi run bash -c 'source install/setup.bash && ros2 run <package> <executable>'` |
| Launch a package | `pixi run bash -c 'source install/setup.bash && ros2 launch <package> <file>.launch.py'` |
| List topics | `pixi run bash -c 'source install/setup.bash && ros2 topic list'` |
| Watch a topic | `pixi run bash -c 'source install/setup.bash && ros2 topic echo /cmd_vel'` |
| Start the Foxglove bridge | `pixi run ros2 launch foxglove_bridge foxglove_bridge_launch.xml` |
| Find button numbers | `pixi run python3 ~/repos/Distributed-Robotics-Platform-2026/template_tools/joy_list_mapper.py` |
| See what is running | `pgrep -af "joy_node\|foxglove_bridge\|ros2 launch" \| cut -c1-110` |

## 12. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `pixi: command not found` in a Konsole | The shell has not reloaded PATH | Open a new Konsole |
| An icon does nothing | A launcher does not use your PATH | Use full paths in the script (`/home/deck/.pixi/bin/pixi`), and check the `Exec=` path and `chmod +x` |
| `Package '<name>' not found` | The workspace was not sourced or not built | Build, then run through `pixi run bash -c 'source install/setup.bash && ...'` |
| Motors stutter | Two things are sending to the same board | Stop the bridge before using the raw UDP tools, and never run two bridges for one port |
| Controls behave strangely | Two `joy_node`s are running | `pkill -f joy_node`, then start one |
| No data in Foxglove | The bridge is not running, or the URL is wrong | Start the bridge, and connect to `ws://localhost:8765` |
| An icon asks permission | KDE does not trust a new `.desktop` file | Right-click it and allow it to run |
