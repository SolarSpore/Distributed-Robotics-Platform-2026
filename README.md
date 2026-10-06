# Robotics Platform

A modular robotics platform built around Linux, ROS 2, and open hardware.

The platform provides a reusable architecture for building different robots while keeping robot-specific hardware and implementation details in the robot repository.

The ESP32 mecanum rover is the current reference implementation of this platform. Its implementation is maintained separately from the platform itself.

## Architecture

The general architecture is:

    Operator Interface
            |
            v
         ROS 2
            |
       +----+----+
       |         |
       v         v
     Drive   Peripherals
     Control   / Sensors
       |         |
       v         v
    Hardware / Network
            |
            v
          Robot

The platform separates robot responsibilities into independent layers:

- Control — operator input and /cmd_vel
- Drive — conversion of motion commands into hardware commands
- Peripherals — non-drive actuators and sensors
- Robot hardware — firmware, motor controllers, sensors, and physical hardware
- Higher-level behavior — autonomy and future robot behaviors

## Repository Structure

    robotics-platform/
    ├── docs/
    ├── scripts/
    ├── templates/
    │   ├── desktop/
    │   └── ros2/
    │       └── robot_template/
    ├── README.md
    ├── LICENSE
    └── .gitignore

The templates directory contains actual starting files for new robots.

## Robot Implementations

A robot built on this platform should maintain its hardware-specific implementation separately.

For example:

    robotics-platform
            |
            +---- reference implementation
                        |
                        v
               esp32-mecanum-rover

The platform should not require a particular motor controller, sensor, microcontroller, wheel configuration, network protocol, or robot geometry.

Those details belong to the robot implementation.

## ROS 2

The platform uses ROS 2 as the middleware connecting operator interfaces, robot control, hardware bridges, sensors, and future autonomous behavior.

Common interfaces include:

    /cmd_vel
    /odom
    /tf
    /joint_states
    /imu
    /scan
    /camera/*

Not every robot needs every interface.

The platform provides templates and conventions rather than requiring every robot to implement the same hardware.

## Templates

The ROS 2 template provides three initial boundaries:

    joy
     |
     v
    robot_control_node
     |
     v
    /cmd_vel
     |
     v
    robot_motor_bridge
     |
     v
    Drive Hardware

Non-drive hardware is handled separately:

    ROS 2
     |
     v
    robot_peripherals_bridge
     |
     +---- head / actuators
     +---- buzzer
     +---- sensors
     +---- telemetry

These are starting points. A robot implementation can replace or extend them when its requirements differ.

## Development Philosophy

Development follows the hardware-to-software path:

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
    Higher-Level Behavior

Each layer should remain independently testable where practical.

Hardware-specific details should stay out of the generic platform whenever possible.

## Future Integration

The platform is intended to support higher-level integrations such as:

- robot feedback and odometry
- sensor visualization
- autonomous behavior
- multi-robot operation
- home automation integration
- MQTT-based system integration

These are future capabilities rather than requirements for a basic robot.

## Reference Implementation

The ESP32 mecanum rover serves as the current reference implementation.

It demonstrates:

- ROS 2 control
- wireless robot control
- ESP32 firmware
- motor control
- mecanum drive
- peripheral integration
- Steam Deck operation
- Foxglove integration

Its hardware and implementation details belong in the rover repository, not in this generic platform repository.

## License

See LICENSE.
