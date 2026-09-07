# Robotics Platform

A modular robotics platform built around **ESP32, ROS 2, Foxglove Studio, and Linux**, with the goal of creating a reusable foundation for multiple robots and autonomous systems.

The platform is being developed from the ground up, starting with a Wi-Fi-connected ESP32 differential-drive robot and expanding toward multi-robot control, telemetry, OTA firmware updates, and integration with broader home automation systems.

## Architecture

```text
                         STEAM DECK
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Foxglove Studio                                            │
│          │                                                  │
│          ▼                                                  │
│  Foxglove Bridge                                            │
│          │                                                  │
│          ▼                                                  │
│        ROS 2                                                │
│          │                                                  │
└──────────┼──────────────────────────────────────────────────┘
           │ Network
           ▼
      ESP32 Robot
           │
           ▼
     Motor Controllers
           │
           ▼
        DC Motors
```

ROS 2 serves as the robotics middleware, while Foxglove provides the primary visualization and operator interface.

The ESP32 handles the robot-side hardware and networking.

## Project Roadmap

```text
┌─────────────────────────────────────────────────────────────┐
│ PROJECT ROADMAP                                             │
├────┬────────────────────────────────────────────────────────┤
│ 01 │ ROS Middleware                              [x]        │
│ 02 │ Foxglove Steam Deck UI                      [x]        │
│ 03 │ Simple ESP32 Bot                            [x]        │
│ 04 │ ESP32 Networking                            [ ]        │
│ 05 │ OTA Firmware Updates                        [ ]        │
│ 06 │ Motor Control                               [ ]        │
│ 07 │ ROS 2 Robot Integration                     [ ]        │
│ 08 │ Foxglove Robot Control                      [ ]        │
│ 09 │ Robot Feedback / Odometry                   [ ]        │
│ 10 │ MQTT ↔ ROS 2 Bridge                         [ ]        │
│ 11 │ Multi-Robot Platform                        [ ]        │
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

| Wheel       | Controller        | GPIO         |
| ----------- | ----------------- | ------------ |
| Front Left  | L298N A / IN1-IN2 | GPIO 26 / 27 |
| Front Right | L298N A / IN3-IN4 | GPIO 18 / 19 |
| Rear Left   | L298N B / IN1-IN2 | GPIO 21 / 22 |
| Rear Right  | L298N B / IN3-IN4 | GPIO 23 / 25 |

The robot will initially be controlled through ROS 2 using `/cmd_vel`.

## Firmware

The ESP32 firmware is being developed with **PlatformIO using the Arduino framework**.

The firmware is intended to provide:

* Motor control
* Wi-Fi configuration
* Fallback access point
* OTA firmware updates
* Web-based management
* ROS-compatible communication
* Future sensor and encoder support

OTA is intentionally designed to remain independent of ROS 2 so the robot can still be recovered and updated if the robotics software stack is unavailable.

## ROS 2

ROS 2 provides the robotics middleware between the operator interface and the robot.

The initial control path is:

```text
Foxglove
    ↓
Foxglove Bridge
    ↓
ROS 2
    ↓
/cmd_vel
    ↓
ESP32
    ↓
Motor Drivers
    ↓
Motors
```

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
│   └── architecture-and-roadmap.md
├── firmware/
│   └── esp32-bot/
├── ros2/
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

This makes it possible to troubleshoot individual layers without requiring the entire system to be operational.

## Current Status

The ROS 2 middleware and Foxglove development environment are established on a Steam Deck running Linux.

The next major milestone is bringing the first ESP32 robot onto the network and establishing the complete control path:

```text
Steam Deck
    ↓
Foxglove
    ↓
ROS 2
    ↓
ESP32
    ↓
L298N ×2
    ↓
4 × DC Motors
```

For the detailed architecture, implementation plan, and development phases, see:

`docs/architecture-and-roadmap.md`
