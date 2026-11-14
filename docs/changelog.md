# Platform Changelog

Changes to the generic Robotics Platform architecture, templates, tooling, and documentation.

## 2026-11-14

### Documentation

- Added a section on the Steam Deck as the robot computer: why it is versatile, the pros of the layout (modularity, form factor, power), and its cons and limits.
- Replaced the "Why Distributed?" ASCII chart with a Mermaid diagram, and realigned the "What This Is" diagram and the Repository Layout tree.
- Added the camera board and the camera template to the architecture diagrams, the roadmap and the reference-rover lists.

## 2026-11-11

### Templates

- Added `Node-templates/ros2/camera_template/`: a ROS 2 package template for network camera devices (MJPEG over HTTP), with an optional on/off switch and state feedback.

### Documentation

- Added section 7e to `docs/install_guide.md`: using the camera template.

## 2026-10-19

### Documentation

- Added section 8c to `docs/install_guide.md`: using the desktop icon template in `Node-templates/desktop/`.

## 2026-10-18

### Setup guide and documentation

- Added `docs/install_guide.md`: installing Pixi, a ROS 2 Humble workspace and Foxglove on a Steam Deck, using the node templates, and starting a robot from a desktop shortcut.
- Added `ToolsReadme.md` and updated `template_tools/README.md`.
- Rewrote `README.md`: added Getting Started, Documentation and Repository Layout sections, and moved the rover-specific sections to the rover repository's README.
- Renamed `templates/` to `Node-templates/` and updated the path in `docs/architecture-and-roadmap.md`.
- Added `template_tools/` with `hold_all_wheels.py`, `test_each_wheel.py` and `joy_list_mapper.py`.
- Removed the rover's start and stop scripts, desktop icons and tools (`scripts/`): they now live in the rover repository.

## 2026-10-05

### Architecture

- Established the Robotics Platform as a reusable architecture for multiple robots.
- Separated generic platform architecture from robot-specific implementation.
- Defined the reference implementation model for downstream robot repositories.
- Established separate responsibilities for:
  - Control
  - Drive
  - Peripherals
  - Autonomous behavior
  - Robot hardware

### ROS 2 Templates

- Added a generic ROS 2 robot package template.
- Added `robot_control_node` for operator input and `/cmd_vel`.
- Added `robot_motor_bridge` as the hardware-facing drive boundary.
- Added `robot_peripherals_bridge` for non-drive actuators and telemetry.
- Added a generic ROS 2 launch file.
- Added package metadata and Python package configuration.

### Desktop Integration

- Added a generic desktop control launcher template for robot implementations.

### Documentation

- Reworked the main README around the generic platform architecture.
- Documented control architecture and responsibility boundaries.
- Documented the distinction between platform code and robot-specific code.
- Established templates as actual starting files rather than documentation-only examples.

## Reference Implementation

The ESP32 mecanum rover is currently the reference implementation of the platform.

Its hardware, firmware, controller mappings, network configuration, and robot-specific ROS 2 implementation are maintained separately from this repository.

## Future Changes

Future platform changes may include:

- Command arbitration and mode management
- Standardized robot feedback interfaces
- Safety and collision-monitoring interfaces
- Multi-robot support
- Additional ROS 2 templates
- Shared tooling proven across multiple robot implementations

Platform abstractions should be added when they are demonstrated to be useful across multiple robots rather than being created solely around the current reference implementation.
