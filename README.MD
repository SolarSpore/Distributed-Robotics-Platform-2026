# Robotics Platform

A modular robotics platform built around **ESP32, ROS 2, Foxglove Studio, and Linux**, with the goal of creating a reusable foundation for multiple robots and autonomous systems.

The platform is being developed from the ground up, starting with a Wi-Fi-connected ESP32 differential-drive robot and expanding toward multi-robot control, telemetry, OTA firmware updates, and integration with broader home automation systems.

## Architecture

```text
                              STEAM DECK
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  Gamepad                                                             │
│     │                                                                │
│     ▼                                                                │
│  joy_node   (/joy)                                                   │
│     │                                                                │
│     ▼                                                                │
│  teleop_twist_joy                                                    │
│     │  /cmd_vel  ◄────►  Foxglove Bridge  ◄────►  Foxglove Studio    │
│     ▼                    (display and debug)                         │
│  cmd_vel_to_udp_node                                                 │
│                                                                      │
└─────┬────────────────────────────────────────────────────────────────┘
      │  Wi-Fi (UDP)
      ▼
   ESP32 Robot
      │
      ▼
 Motor Controllers
      │
      ▼
   DC Motors
```

ROS 2 serves as the robotics middleware. The gamepad is the driving input: stock `joy` and `teleop_twist_joy` nodes produce `/cmd_vel`, and a small bridge node turns that into the robot's UDP protocol. Foxglove provides the visualization and debug interface (it can also publish to topics for testing) but is not the primary driving path.

The ESP32 handles the robot-side hardware and networking. It never runs ROS. Its only contract with the control system is the UDP protocol described below.

## Project Roadmap

```text
┌─────────────────────────────────────────────────────────────┐
│ PROJECT ROADMAP                                             │
├────┬────────────────────────────────────────────────────────┤
│ 01 │ ROS Middleware                              [x]        │
│ 02 │ Foxglove Steam Deck UI                      [x]        │
│ 03 │ Simple ESP32 Bot                            [x]        │
│ 04 │ ESP32 Networking                            [x]        │
│ 05 │ OTA Firmware Updates                        [x]        │
│ 06 │ Motor Control                               [x]        │
│ 07 │ ROS 2 Robot Integration                     [x]        │
│ 08 │ Foxglove debug Robot Controls               [x]        │
│ 09 │ Backend Controller > ROS2/Arcade controls   [x]        │
│ 10 │ Tank-mode controller                        [ ]        │
│ 11 │ Foxglove telemetry dashboard                [ ]        │
│ 12 │ Robot Feedback / Odometry                   [ ]        │
│ 13 │ MQTT ↔ ROS 2 Bridge                         [ ]        │
│ 14 │ Multi-Robot Platform                        [ ]        │
└────┴────────────────────────────────────────────────────────┘
```

## First Robot

The first robot is a four-wheel differential-drive platform built around an ESP32.

### Hardware

* ESP32
* 4 × DC gear motors
* 2 × L298N motor drivers
* Wi-Fi connectivity
* Future encoder and sensor support

### Motor Mapping

| Wheel       | GPIO A / GPIO B |
| ----------- | --------------- |
| Front Left  | 23 / 25         |
| Front Right | 26 / 27         |
| Rear Left   | 21 / 22         |
| Rear Right  | 18 / 19         |

Verified with a one-wheel-at-a-time test over raw UDP. Wiring, power, and firmware details live in the robot's own README (`firmware/esp32-bot/README.md`).

The robot is controlled through ROS 2 using `/cmd_vel`, driven from a Steam Deck gamepad.

## Robot Interface (UDP)

Every robot in the platform talks to the control system through a small network protocol, so the firmware and the ROS 2 side stay independent.

| Item | Value |
|---|---|
| Transport | UDP, port `4210` |
| Payload | `"FL,FR,RL,RR"`, each wheel `-255..255` |
| Failsafe | Robot stops all motors after 0.5 s without a valid packet |

**Only one sender should transmit to a robot at a time.** Competing senders (for example a test node sending idle stop packets alongside the drive bridge) interleave their commands and show up as motor stutter.

## Firmware

The ESP32 firmware is developed with **PlatformIO using the Arduino framework**.

Currently implemented:

* UDP motor control with a 500 ms failsafe
* Wi-Fi configuration with fallback access point
* mDNS hostname
* OTA firmware updates

Planned:

* Web-based management
* Sensor and encoder support (for `/odom` and other feedback)

OTA is intentionally designed to remain independent of ROS 2 so the robot can still be recovered and updated if the robotics software stack is unavailable.

## ROS 2

ROS 2 provides the robotics middleware between the operator interface and the robot.

The current control path is:

```text
Steam Deck gamepad
    ↓
joy_node          (/joy)
    ↓
teleop_twist_joy  (/cmd_vel)
    ↓
cmd_vel_to_udp_node
    ↓  UDP "FL,FR,RL,RR" @ 20 Hz
ESP32
    ↓
Motor Drivers
    ↓
Motors
```

Foxglove Studio connects through `foxglove_bridge` to the same ROS topics for display and debugging.

### Packages

| Package | Purpose |
|---|---|
| `rover_teleop` | Launch file and Steam Deck config for `joy_node` + `teleop_twist_joy` |
| `rover_udp_bridge` | `cmd_vel_to_udp_node` (Twist → wheel PWM → UDP) and `raw_wheel_udp_node` (direct wheel testing) |
| `rover_description` | URDF/xacro stub staged for a possible future `ros2_control` migration. Not wired to anything |

`ros2_control` / `diff_drive_controller` is intentionally deferred. Without wheel encoders it would run open-loop and add nothing over the current bridge. It becomes worthwhile once encoders and odometry exist.

### Operator controls (Steam Deck, arcade mode)

| Input | Action |
|---|---|
| **L1** (hold) | Deadman switch. The robot only drives while held |
| Left stick up / down | Forward / reverse |
| Left stick left / right | Turn left / right (pivots with no forward input) |
| **R1** (hold with L1) | Turbo |

Releasing L1 stops the robot. Tank mode (hold A, left stick = left wheels, right stick = right wheels) is planned.

Steam Deck indices, from calibration: A=0, B=1, X=2, Y=3, L1=9, R1=10, L2 = axis 4, R2 = axis 5. L2 and R2 are analog-only with no digital button, so the deadman is L1. The Steam Gamepad controller template must be applied so the Deck's controls act as a gamepad rather than a mouse.

### Bridge behavior and settings

`cmd_vel_to_udp_node` resends the last command at a fixed 20 Hz, sends zeros if no `/cmd_vel` arrives for 0.5 s, and sends a final stop when it exits.

| Parameter | Value in use | Notes |
|---|---|---|
| `max_linear_speed` | 1.5 | m/s that maps to PWM 255. `cmd_vel_launch.py` defaults to 0.5, so override it |
| `min_pwm` | 110 | Lowest PWM given to a non-zero command, which works around the L298N motor stall zone. Default 0 |
| `wheel_separation` | 0.30 | Meters. Not yet measured on the real robot |

`cmd_vel_launch.py` does not expose `min_pwm`, so the bridge is started with `ros2 run`:

```bash
ros2 run rover_udp_bridge cmd_vel_to_udp_node --ros-args -p max_linear_speed:=1.5 -p min_pwm:=110
```

Teleop scaling lives in `rover_teleop/config/steamdeck.config.yaml`: `scale_linear.x` 0.7 (turbo 1.5), `scale_angular.yaw` 4.0 for both normal and turbo, `joy_node` deadzone 0.1 and `autorepeat_rate` 20 Hz. The angular value is a tuning number, not real rad/s.

### Running it

On the Steam Deck, the **Rover Controls** desktop icon starts teleop, the bridge, and `foxglove_bridge` detached (logs in `~/Robotics/logs/`). **Stop Rover Controls** shuts them down. Manually, in a `pixi shell` with the workspace sourced, one command per terminal:

```bash
ros2 launch rover_teleop joy_teleop_launch.py
ros2 run rover_udp_bridge cmd_vel_to_udp_node --ros-args -p max_linear_speed:=1.5 -p min_pwm:=110
```

Before starting the bridge, `pgrep -af "cmd_vel_to_udp_node|raw_wheel_udp_node"` should print nothing. Then Foxglove Studio connects to `ws://<deck-ip>:8765`.

Environment notes:

* ROS 2 Humble runs on the Steam Deck via Pixi/RoboStack (SteamOS has no native ROS).
* Build packages with `colcon build --symlink-install` so edits to launch files and config take effect without rebuilding. When config seems ignored, check the installed copy under `install/<pkg>/share/`.
* `joy_node` prints harmless `Unknown event type 1623/1624` messages (the Deck's gyro and trackpad reports).
* Desktop launchers don't inherit the shell `PATH`, so launcher scripts use absolute paths (for example `/home/deck/.pixi/bin/pixi`).

Future robot interfaces may include:

```text
/cmd_vel
/odom
/tf
/joint_states
/imu
/scan
/camera/*
```

## MQTT Integration

MQTT will eventually provide an integration boundary between the robotics platform and other systems such as Home Assistant and ESPHome.

```text
                    ROS 2
                  /       \
                 /         \
          Robots          ROS Tools
                 \
                  \
             MQTT Bridge
                   │
                  MQTT
               /       \
      Home Assistant   ESPHome
```

MQTT is not part of the initial robot control path. ROS 2 remains the native robotics layer, while MQTT provides broader IoT integration.

## Repository Structure

```text
robotics-platform/
├── README.md
├── docs/
│   ├── architecture-and-roadmap.md
│   ├── changelog.md
│   └── controls.txt
├── firmware/
│   └── esp32-bot/
│       └── README.md        # robot-specific: wiring, power, firmware, OTA
├── ros2/
│   ├── rover_teleop/
│   ├── rover_udp_bridge/
│   └── rover_description/
└── mqtt-bridge/
```

## Development Philosophy

The platform is being built incrementally rather than attempting to solve the entire robotics stack at once.

Each layer should remain independently testable:

```text
Hardware
   ↓
Firmware
   ↓
Networking
   ↓
ROS 2
   ↓
Operator Interface
   ↓
Higher-Level Integration
```

This makes it possible to troubleshoot individual layers without requiring the entire system to be operational. Bring-up on the first robot followed this in practice: each wheel was verified alone over raw UDP before the ROS 2 bridge was involved, which is how a wiring-order mismatch and a competing sender were found.

## Current Status

The full control path is working: a Steam Deck gamepad drives the first ESP32 robot through ROS 2 in arcade mode, with a one-click start/stop from the Deck desktop. Foxglove is connected for display and debugging.

Next milestones:

* Tank-mode controller
* Foxglove telemetry dashboard
* Encoders and odometry (which also unlock `ros2_control`)
* MQTT ↔ ROS 2 bridge

For the detailed architecture, implementation plan, and development phases, see:

`docs/architecture-and-roadmap.md`

For the robot itself (wiring, power notes, firmware, OTA), see:

`firmware/esp32-bot/README.md`
