# Architecture and Roadmap

## Purpose

The Robotics Platform provides a reusable software architecture for
Linux-based robots using ROS 2.

The platform separates operator control, robot drive, peripherals,
hardware communication, and higher-level behavior so that different robot
implementations can share the same general architecture without requiring
identical hardware.

The ESP32 mecanum rover is the current reference implementation.

## Core Architecture

The intended high-level architecture is:

    Operator Interface
            |
            v
        ROS 2 / joy
            |
            v
    +-------------------+
    | Control Node      |
    |                   |
    | Operator input    |
    | mode handling     |
    | /cmd_vel output   |
    +-------------------+
            |
            v
         /cmd_vel
            |
            v
    +-------------------+
    | Drive Node        |
    |                   |
    | motion processing |
    | drive interface   |
    +-------------------+
            |
            v
      Drive Hardware

Non-drive hardware is separated from the drive path:

    ROS 2
      |
      v
    +------------------------+
    | Peripherals Node       |
    |                        |
    | actuators              |
    | sensors                |
    | telemetry              |
    +------------------------+
      |
      +---- head / actuators
      +---- buzzer
      +---- sensors
      +---- telemetry

Higher-level behavior can eventually operate above both:

    Operator Control
          |
          v
       /cmd_vel
          |
       +--+----------------+
       |                   |
       v                   v
    Drive Node       Peripherals Node
       |                   |
       v                   v
    Hardware            Hardware

    Autonomous Behavior
          |
          +---- references drive interfaces
          |
          +---- references peripheral interfaces

The autonomy layer is not required for manual operation.

## Responsibility Boundaries

### Control

The control node converts operator input into robot control commands.

Responsibilities include:

- reading controller input
- deadman controls
- control modes
- speed scaling
- publishing `/cmd_vel`

It should not contain hardware-specific motor communication.

### Drive

The drive node handles the robot's movement interface.

Responsibilities include:

- consuming `/cmd_vel`
- converting motion commands into the robot's drive representation
- communicating with drive hardware
- command timeout and safe stopping
- drive-specific hardware behavior

The exact implementation depends on the robot.

A differential-drive robot, mecanum robot, tracked robot, or other platform
does not need to use the same drive implementation.

### Peripherals

The peripherals node handles hardware that is not part of the primary drive
system.

Examples include:

- head or camera servos
- buzzers
- LEDs
- ultrasonic sensors
- environmental sensors
- other auxiliary actuators
- telemetry

Keeping these separate prevents unrelated hardware from becoming coupled to
the drive implementation.

### Autonomous Behavior

Autonomous behavior is a higher-level layer.

It may consume sensor data and issue movement or peripheral commands, but it
should not directly manipulate motor-controller hardware.

A future autonomous node can therefore operate through the same interfaces
used by manual control.

## Robot-Specific Implementation

The platform deliberately does not define:

- specific GPIO assignments
- motor controller hardware
- wheel dimensions
- wheel geometry
- microcontroller models
- UDP packet formats
- network addresses
- sensor wiring
- controller-specific button mappings

Those belong to the robot implementation.

The reference ESP32 mecanum rover contains those details in its own
repository.

## ROS 2 Interfaces

Common interfaces may include:

    /cmd_vel
    /odom
    /tf
    /joint_states
    /imu
    /scan
    /camera/*

A robot only needs to implement the interfaces appropriate to its hardware
and capabilities.

## Hardware Boundary

The intended software stack is:

    Hardware
       |
       v
    Firmware
       |
       v
    Network / Transport
       |
       v
    ROS 2 Bridge
       |
       v
    Robot Interfaces
       |
       +---- Control
       +---- Drive
       +---- Peripherals
       +---- Sensors
       |
       v
    Higher-Level Behavior

The transport may be UDP, serial, CAN, ROS-native communication, or another
mechanism appropriate to the robot.

The platform does not require a universal hardware protocol.

## Reference Implementation

The ESP32 mecanum rover is the current reference implementation.

It demonstrates the platform using:

- Steam Deck Linux
- ROS 2
- Foxglove
- ESP32 firmware
- wireless communication
- motor controllers
- mecanum drive
- auxiliary peripherals

The rover's hardware-specific implementation is intentionally separate from
this platform repository.

## Development Philosophy

Development follows the hardware-to-software path:

    Hardware
       |
       v
    Firmware
       |
       v
    Networking
       |
       v
    ROS 2
       |
       v
    Operator Interface
       |
       v
    Higher-Level Behavior

Each layer should remain independently testable where practical.

The platform should only generalize patterns that have demonstrated value
across actual robot implementations.

## Future Architecture

Potential future components include:

### Command Arbitration

A command multiplexer such as `twist_mux` may eventually arbitrate between
manual control, autonomous behavior, safety systems, and other command
sources.

### Safety Layer

A future safety or collision-monitoring layer may be placed between command
sources and the drive interface.

### Robot Feedback

Encoders, IMUs, and other sensors can eventually provide:

    /odom
    /tf
    /joint_states
    /imu

### Multi-Robot Support

The platform may eventually support multiple robots operating from the same
ROS 2 environment.

### System Integration

MQTT may provide an integration boundary between ROS 2 robots and systems
such as home automation.

MQTT is not part of the basic robot control path.

## Roadmap

### Current

- ROS 2 platform architecture
- reusable robot templates
- operator control interface
- drive interface
- peripheral interface
- Linux-based operator computer
- reference ESP32 robot implementation
- Foxglove integration

### Near Term

- formalize common ROS 2 interfaces
- improve robot templates
- document robot implementation structure
- separate rover tooling from platform tooling
- establish the reference rover as a downstream implementation

### Future

- robot feedback and odometry
- encoder integration
- IMU integration
- sensor visualization
- autonomous behavior
- command arbitration
- safety monitoring
- multi-robot operation
- MQTT system integration

Future components should be added when they solve a demonstrated need
rather than being required by the platform from the beginning.
