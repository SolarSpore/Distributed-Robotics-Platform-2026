# Steam Deck Robotics Platform

A modular robotics platform built around a Steam Deck running ROS 2 and Foxglove, with ESP32-based robots acting as the hardware endpoints.

The idea is to build the common infrastructure once, then make adding another robot mostly a matter of implementing its hardware interface instead of rebuilding the whole control system.

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

## Architecture

The Steam Deck is the central robotics computer. Foxglove is used for visualization and operator control, while ROS 2 handles communication with the robots.

```text
┌─────────────────────────────────────────────────────────────┐
│                        STEAM DECK                           │
│                                                             │
│  Foxglove Studio                                            │
│         │                                                   │
│         ▼                                                   │
│  Foxglove Bridge                                            │
│         │                                                   │
│         ▼                                                   │
│       ROS 2                                                 │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │ Network
          ▼
     ESP32 Robot
          │
          ▼
     Motor Drivers
          │
          ▼
        Motors
```

The important part is that Foxglove isn't talking directly to the ESP32. It talks to ROS 2 through the Foxglove Bridge, and the robot exposes its own ROS interfaces.

For the first robot, the eventual control path is:

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

`/cmd_vel` is just a ROS 2 topic containing velocity commands. It isn't another service or bridge.

---

## Steam Deck

The Steam Deck is currently running KDE Plasma on Wayland with ROS 2, Foxglove Studio, and the Foxglove Bridge.

Foxglove is installed in a Distrobox container named `foxglove`.

The main executable is:

```text
/opt/Foxglove/foxglove-studio
```

The working desktop launcher is:

```text
~/.local/share/applications/foxglove-foxglove-studio.desktop
```

It launches Foxglove through Distrobox:

```bash
/usr/bin/distrobox-enter -n foxglove -- /opt/Foxglove/foxglove-studio --foreground %U
```

A separate launcher at:

```text
~/.local/bin/foxglove-steamdeck.sh
```

sets the required Wayland environment before starting Foxglove.

### Foxglove Bridge

The ROS 2 bridge runs as a user systemd service:

```text
foxglove-bridge.service
```

It can currently be started with:

```bash
systemctl --user start foxglove-bridge.service
```

The goal is for this to become part of the normal robotics environment rather than something that has to be manually started every time.

---

## First Robot

The first robot is a four-wheel differential-drive platform built around an ESP32.

Hardware:

* ESP32
* 2 × L298N motor drivers
* 4 × yellow DC gear motors

Each L298N controls two motors.

Current GPIO mapping:

```cpp
MotorPins motors[4] = {
    /* M1 FL (Board A, IN1/IN2) */ {26, 27},
    /* M2 FR (Board A, IN3/IN4) */ {18, 19},
    /* M3 RL (Board B, IN1/IN2) */ {21, 22},
    /* M4 RR (Board B, IN3/IN4) */ {23, 25},
};
```

```text
             FRONT

        FL           FR
        │             │
        │             │
        RL           RR

             REAR
```

The ESP32 will eventually take velocity commands from ROS 2 and turn them into the appropriate left and right motor outputs.

---

## ESP32 Firmware

The firmware will be developed with VS Code and PlatformIO using the Arduino framework.

```text
VS Code
   ↓
PlatformIO
   ↓
Arduino framework
   ↓
ESP32
```

The development computer only needs to handle firmware development. It does **not** need ROS 2 installed.

PlatformIO will handle the build environment, dependencies, board configuration, serial monitoring, USB flashing, and eventually OTA updates.

The firmware is intended to grow into a small robot platform rather than remain a single-purpose motor test program. Planned features include Wi-Fi configuration, a fallback access point, OTA updates, motor control, diagnostics, and the ROS interface.

---

## Networking and Recovery

The robot shouldn't become inaccessible just because the normal Wi-Fi network isn't available.

The intended startup behavior is:

```text
ESP32 boots
    │
    ▼
Try configured Wi-Fi
    │
    ├── Connected ──► Normal operation
    │
    └── Failed ─────► Start Robot-XXXX AP
                            │
                            ▼
                       Management / OTA
```

The fallback AP will provide a way to configure the robot and recover it without relying on the rest of the network.

The management interface will eventually provide things such as:

* Wi-Fi configuration
* Firmware updates
* Firmware version
* Robot status
* Reboot
* Diagnostics
* Manual motor testing

OTA is intentionally separate from ROS 2. If the ROS software has a problem, the robot should still be reachable and recoverable.

USB will remain the lowest-level recovery method.

---

## Bringing Up the First Robot

The robot will be built up in stages so that each part can be tested before adding the next one.

### 1. ESP32

Start with USB.

```text
Computer → ESP32
```

Verify that firmware can be flashed, the board boots reliably, and serial diagnostics work.

### 2. Networking

Add normal Wi-Fi and the fallback AP.

```text
ESP32
 ├── Normal Wi-Fi
 └── Fallback AP
```

At this point the robot should be reachable over the network without involving ROS 2.

### 3. OTA

Once networking works, move firmware updates from USB to Wi-Fi.

USB stays available for recovery.

### 4. Motors

Test all four motor channels individually.

```text
FL → forward / reverse / stop
FR → forward / reverse / stop
RL → forward / reverse / stop
RR → forward / reverse / stop
```

This is where wiring, GPIO assignments, motor direction, and the L298N configuration get verified.

### 5. Differential Drive

Once the individual motors work, treat them as a single drive base.

A velocity command will be converted into left and right wheel speeds, which are then applied to the front and rear motors on each side.

```text
             Command
                │
                ▼
       Differential Drive
          /           \
         ▼             ▼
     Left side      Right side
       FL + RL        FR + RR
```

### 6. ROS 2

The next step is connecting the ESP32 to the ROS 2 system running on the Steam Deck.

```text
Steam Deck
    │
   ROS 2
    │
 Network
    │
  ESP32
```

The exact ESP32 ROS 2 interface will be chosen during implementation rather than locking the project into a solution before testing it.

### 7. `/cmd_vel`

Once the ROS interface is working, subscribe to `/cmd_vel` and feed those commands into the differential-drive controller.

```text
/cmd_vel
    ↓
ESP32 ROS interface
    ↓
Differential-drive controller
    ↓
Left / Right motor commands
    ↓
4 motors
```

This is the point where ROS 2 can actually drive the physical robot.

### 8. Foxglove

Finally, put Foxglove at the front of the system.

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
L298N × 2
    ↓
4 motors
```

That gives us the first complete path from the operator interface to the hardware.

---

## Robot Feedback

The first version doesn't need encoders or odometry. The initial goal is simply reliable command and control.

Once the basic robot works, sensors can be added without changing the overall architecture.

For example:

```text
ESP32
 ├── Motor control
 ├── Wheel encoders
 │       ↓
 │     Odometry
 │       ↓
 │     /odom
 ├── IMU
 └── Other sensors
```

Depending on the hardware eventually added, the robot could expose interfaces such as:

```text
/cmd_vel
/odom
/tf
/joint_states
/scan
/imu
/camera/...
```

---

## MQTT Integration

MQTT comes later.

It isn't needed to drive the first robot, and it shouldn't sit in the middle of the ROS 2 control path.

Instead, a separate MQTT ↔ ROS 2 service will eventually connect the robotics system to the rest of the home network.

```text
                         ROS 2
                    /      |      \
                   /       |       \
              Robot A   Robot B   ROS tools
                             |
                             |
                      MQTT ↔ ROS 2
                             |
                            MQTT
                             |
               ┌─────────────┼─────────────┐
               │             │             │
        Home Assistant    ESPHome      Other systems
```

ROS 2 remains responsible for robotics. MQTT provides a convenient interface for systems that don't need to know anything about ROS.

---

## Repository Structure

```text
steam-deck-robotics/
├── README.md
├── docs/
│   └── architecture-and-roadmap.md
├── firmware/
│   └── esp32-bot/
├── ros2/
└── mqtt-bridge/
```

The root README is intended to stay relatively short. Detailed setup notes, architecture decisions, and implementation details will live under `docs/`.

---

## Current Status

The Steam Deck side of the platform is established:

* ROS 2 environment is working
* Foxglove Studio is installed and launching correctly
* Foxglove Bridge is installed
* Foxglove Bridge runs as a user systemd service
* The first robot hardware has been selected and mapped
* The basic ROS 2 → Foxglove architecture is defined

The next step is deliberately back on the hardware side:

1. Set up the ESP32 PlatformIO project
2. Flash the first firmware over USB
3. Get reliable serial diagnostics
4. Add Wi-Fi
5. Add the fallback AP
6. Add OTA
7. Bring up the four motor channels
8. Implement differential drive
9. Connect the robot to ROS 2
10. Subscribe to `/cmd_vel`
11. Drive the robot through Foxglove

## First Real Milestone

The first major milestone is not MQTT, autonomy, odometry, or multi-robot support.

It's this:

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
L298N × 2
    ↓
4 motors
    ↓
Robot moves
```

Once that works, the basic robotics platform has proven its end-to-end control path. Everything after that builds on something real.
