# Steam Deck Robotics Platform

A modular robotics platform built around a Steam Deck running ROS 2 and Foxglove, with ESP32-based robots as distributed hardware endpoints.

The goal is to build the software infrastructure once and then make individual robots relatively simple to integrate.

---

## 1. Current Architecture

The current control/visualization stack is:

```text
┌─────────────────────────────────────────────────────────────┐
│                        STEAM DECK                           │
│                                                             │
│  KDE Plasma / Wayland                                      │
│                                                             │
│  ┌─────────────────┐                                       │
│  │ Foxglove Studio │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│  ┌────────▼────────┐                                       │
│  │ Foxglove Bridge │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│  ┌────────▼────────┐                                       │
│  │      ROS 2      │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
└───────────┼─────────────────────────────────────────────────┘
            │ Network
            ▼
       Robot / ESP32
```

ROS 2 provides the robot communication layer.

Foxglove provides the human-facing visualization and control interface.

The Foxglove Bridge connects Foxglove to the ROS 2 graph.

---

# 2. Steam Deck Setup

The Steam Deck is currently running:

* KDE Plasma
* Wayland
* ROS 2 environment
* Foxglove Studio
* Foxglove Bridge

## Foxglove

Foxglove is installed in a Distrobox container named:

```text
foxglove
```

The Foxglove binary is:

```text
/opt/Foxglove/foxglove-studio
```

The working desktop launcher is:

```text
~/.local/share/applications/foxglove-foxglove-studio.desktop
```

It launches:

```bash
/usr/bin/distrobox-enter -n foxglove -- /opt/Foxglove/foxglove-studio --foreground %U
```

A custom launcher also exists:

```text
~/.local/bin/foxglove-steamdeck.sh
```

It explicitly configures the Wayland environment before launching Foxglove.

## Foxglove Bridge

The bridge is configured as a user systemd service:

```text
foxglove-bridge.service
```

It can be started with:

```bash
systemctl --user start foxglove-bridge.service
```

The intention is for the bridge to become part of the normal robotics environment rather than requiring manual startup every time.

---

# 3. ROS 2 / Foxglove Relationship

Foxglove does not directly control the robot hardware.

The relationship is:

```text
Foxglove
    ↓
Foxglove Bridge
    ↓
ROS 2
    ↓
Robot
```

ROS 2 topics provide the actual robot interfaces.

For example:

```text
/cmd_vel
/odom
/tf
/scan
/joint_states
```

depending on the capabilities of the individual robot.

`/cmd_vel` is simply a ROS 2 topic carrying velocity commands. It is **not a separate bridge or service**.

For the first mobile robot:

```text
Foxglove
    ↓
Foxglove Bridge
    ↓
ROS 2 /cmd_vel
    ↓
ESP32
    ↓
Motor controller
    ↓
Motors
```

---

# 4. First Robot

The first robot is an ESP32-based four-wheel differential-drive robot.

Hardware:

* ESP32
* 2 × L298N motor drivers
* 4 × yellow DC gear motors
* 2 motors per L298N

Current motor GPIO mapping:

```cpp
MotorPins motors[4] = {
    /* M1 FL (Board A, IN1/IN2) */ {26, 27},
    /* M2 FR (Board A, IN3/IN4) */ {18, 19},
    /* M3 RL (Board B, IN1/IN2) */ {21, 22},
    /* M4 RR (Board B, IN3/IN4) */ {23, 25},
};
```

Logical wheel layout:

```text
             FRONT

        FL           FR
        │             │
        │             │
        RL           RR

             REAR
```

The ESP32 will ultimately translate ROS velocity commands into left/right motor commands.

---

# 5. ESP32 Development Environment

The ESP32 will be programmed from a normal computer.

**The development computer does not need ROS 2 installed.**

The planned firmware environment is:

```text
VS Code
    ↓
PlatformIO
    ↓
Arduino framework
    ↓
ESP32
```

PlatformIO will handle:

* building firmware
* dependency management
* board configuration
* USB flashing
* serial monitoring
* OTA firmware deployment
* reproducible project configuration

The Arduino framework provides the familiar ESP32 programming model while PlatformIO manages the actual project.

---

# 6. ESP32 Networking

The ESP32 should remain manageable even when it cannot reach the normal Wi-Fi network.

The intended behavior is:

```text
                    ESP32 BOOT
                        │
                        ▼
                Try configured Wi-Fi
                        │
              ┌─────────┴─────────┐
              │                   │
           SUCCESS              FAILURE
              │                   │
              ▼                   ▼
        Normal Wi-Fi          Start fallback AP
              │                   │
              │             Robot-XXXX
              │                   │
              └─────────┬─────────┘
                        ▼
                 Management / OTA
```

This means the robot has a recovery path that does not depend on the home network.

The fallback access point will eventually provide a management interface for things such as:

* firmware updates
* Wi-Fi configuration
* robot status
* rebooting
* firmware version
* diagnostics
* potentially manual motor testing

OTA management should remain independent of ROS 2.

If ROS 2 is broken, the robot should still be recoverable.

---

# 7. Development Roadmap

The first robot will be developed incrementally.

## Phase 1 — ESP32 Bring-Up

Connect the ESP32 to the development computer over USB.

Verify:

```text
ESP32 powers on
        ↓
Firmware flashes
        ↓
Serial output works
        ↓
ESP32 boots successfully
```

No ROS or motors yet.

---

## Phase 2 — Networking

Implement:

```text
ESP32
 ├── Connect to configured Wi-Fi
 └── Fall back to AP if connection fails
```

Verify that the ESP32 can be reached over the network.

---

## Phase 3 — OTA

Implement firmware updates over the network.

Target workflow:

```text
First installation:

Computer ──USB──> ESP32


Normal development:

Computer ──Wi-Fi──> ESP32
                    │
                    └── OTA firmware update


No normal Wi-Fi:

Computer ──Robot AP──> ESP32
                       │
                       └── OTA firmware update
```

USB remains available as a recovery method.

---

## Phase 4 — Motor Bring-Up

Before involving ROS 2, verify the physical motor system independently.

Test each motor:

```text
FL forward
FL reverse
FL stop

FR forward
FR reverse
FR stop

RL forward
RL reverse
RL stop

RR forward
RR reverse
RR stop
```

This establishes the correct GPIO, motor-driver, wiring, and direction behavior.

---

## Phase 5 — Differential Drive

Combine the four motors into a differential-drive base.

Conceptually:

```text
LEFT SIDE             RIGHT SIDE

FL ─┐                  ┌─ FR
    ├── LEFT           ├── RIGHT
RL ─┘                  └─ RR
```

A forward command should produce forward motion.

A turning command should produce opposing wheel velocities as appropriate.

Motor direction inversions will be handled in firmware according to the physical mounting of the motors.

---

## Phase 6 — ESP32 ↔ ROS 2

Add the ROS-compatible communication layer.

The ESP32 becomes a networked ROS 2 robot endpoint:

```text
ROS 2
  │
  │ Network
  ▼
ESP32
```

The development computer still does not need ROS 2.

ROS 2 lives on the robotics side of the architecture, primarily on the Steam Deck.

---

## Phase 7 — `/cmd_vel`

Connect ROS velocity commands to the differential-drive controller:

```text
/cmd_vel
    ↓
ESP32 ROS interface
    ↓
Differential-drive mixer
    ↓
Left / Right velocity
    ↓
4 motor outputs
```

At this point, ROS 2 can command the physical robot.

---

## Phase 8 — Foxglove Control

Once `/cmd_vel` works through ROS 2, Foxglove becomes the high-level interface:

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

This is the first complete end-to-end robotics pipeline.

---

# 8. Future Robot Feedback

The initial robot can operate without odometry.

Later, encoders and sensors can be added.

For example:

```text
                    ┌── /cmd_vel
                    │
Foxglove ↔ ROS 2 ↔ ESP32
                    │
                    ├── Motor control
                    │
                    ├── Encoders
                    │      ↓
                    │   Odometry
                    │      ↓
                    │   /odom
                    │
                    ├── IMU
                    │
                    └── Other sensors
```

Eventually the robot can expose:

```text
/cmd_vel
/odom
/tf
/joint_states
/scan
/imu
/camera/...
```

as hardware is added.

---

# 9. Future MQTT Integration

MQTT is **not part of the first robot's direct control path**.

The primary robotics path remains:

```text
Foxglove
    ↓
Foxglove Bridge
    ↓
ROS 2
    ↓
Robot
```

A separate MQTT ↔ ROS 2 bridge/service will be developed later.

Its purpose is to allow the broader home automation/network ecosystem to communicate with the robotics ecosystem without forcing every system to understand ROS 2.

The eventual architecture can look like:

```text
                         ┌───────────────┐
                         │    Foxglove   │
                         └───────┬───────┘
                                 │
                         Foxglove Bridge
                                 │
                                 ▼
                              ROS 2
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
           Robot A            Robot B          ROS tools
            ESP32              ESP32
              │                  │
              └──────────────────┘


                    Separate integration layer

                     MQTT ↔ ROS 2 Bridge
                            │
                            ▼
                         MQTT
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        Home Assistant   ESPHome       Other systems
```

The MQTT bridge should be treated as an **integration boundary**, not as a replacement for ROS 2.

ROS 2 remains the native robotics communication layer.

MQTT remains useful for broader IoT/home-automation communication.

---

# 10. Overall Target Architecture

The eventual system is intended to have several independent layers:

```text
┌──────────────────────────────────────────────────────────────┐
│                       USER INTERFACE                         │
│                                                              │
│                         Foxglove                             │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                     ROBOTICS INTERFACE                       │
│                                                              │
│                     Foxglove Bridge                          │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                        ROBOTICS CORE                         │
│                                                              │
│                           ROS 2                              │
└───────────────┬────────────────────────────┬─────────────────┘
                │                            │
                ▼                            ▼
          ESP32 Robots                 ROS 2 Applications
                │
                ▼
       Hardware / Sensors


                     SEPARATE INTEGRATION
                             │
                             ▼
                       MQTT ↔ ROS 2
                             │
                             ▼
                            MQTT
                             │
                             ▼
                 Home Automation / IoT
```

The important architectural principle is that these layers remain loosely coupled.

A robot should not require Foxglove to operate.

ROS 2 should not depend on MQTT.

MQTT devices should not need to understand ROS 2 internally.

OTA should not depend on ROS 2.

The Steam Deck provides the central robotics environment, while individual robots remain distributed hardware endpoints.

---

# 11. Current Status

### Completed

* Steam Deck running KDE Plasma / Wayland
* Foxglove installed in Distrobox
* Working Foxglove desktop launcher
* Custom Wayland launcher
* Foxglove Bridge installed
* Foxglove Bridge configured as a user systemd service
* ROS 2 ↔ Foxglove architecture established
* `/cmd_vel` identified as the intended initial robot command interface
* Gaming Mode approach abandoned in favor of the working Desktop Mode launcher

### Next

1. Set up PlatformIO
2. Identify and connect the ESP32
3. Flash initial firmware over USB
4. Establish serial diagnostics
5. Implement Wi-Fi connection
6. Implement fallback AP
7. Establish OTA firmware updates
8. Test the four L298N motor channels
9. Build the differential-drive controller
10. Establish ESP32 ↔ ROS 2 communication
11. Connect `/cmd_vel`
12. Drive the robot from Foxglove

### Later

* Wheel encoders
* `/odom`
* `/tf`
* IMU
* Additional sensors
* Cameras
* Autonomous behaviors
* MQTT ↔ ROS 2 bridge
* Integration with Home Assistant and the broader home automation system
* Additional robots

---

## The First Milestone

The immediate goal is deliberately small:

```text
ESP32
  ↓
Wi-Fi
  ↓
ROS 2
  ↓
/cmd_vel
  ↓
4 motors
  ↓
Robot moves
```

Then:

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

Once that works, the first robot is officially a ROS 2 robot rather than simply an ESP32 car.
