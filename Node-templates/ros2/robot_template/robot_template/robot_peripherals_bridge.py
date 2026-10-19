#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Range
from std_msgs.msg import Float32, Int32


class RobotPeripheralsBridge(Node):
    """
    Generic peripheral/telemetry bridge template.

    This is intentionally a pattern rather than a fake universal protocol.
    Replace the hardware-specific sections with the robot's actual
    peripheral transport and message handling.
    """

    def __init__(self):
        super().__init__('robot_peripherals_bridge')

        self.head_subscription = self.create_subscription(
            Float32,
            'head/angle',
            self.head_callback,
            10,
        )

        self.buzzer_subscription = self.create_subscription(
            Int32,
            'buzzer/beep',
            self.buzzer_callback,
            10,
        )

        self.range_publisher = self.create_publisher(
            Range,
            'ultrasonic/range',
            10,
        )

        self.declare_parameter('telemetry_poll_hz', 10.0)

        rate = self.get_parameter(
            'telemetry_poll_hz').value

        self.timer = self.create_timer(
            1.0 / rate,
            self.poll_telemetry,
        )

    def head_callback(self, msg: Float32):
        self.send_head_command(msg.data)

    def buzzer_callback(self, msg: Int32):
        self.send_buzzer_command(msg.data)

    def send_head_command(self, angle):
        """Replace with the robot-specific head/actuator protocol."""
        pass

    def send_buzzer_command(self, value):
        """Replace with the robot-specific buzzer protocol."""
        pass

    def poll_telemetry(self):
        """
        Read hardware telemetry and publish ROS messages.

        Replace this with the actual robot telemetry implementation.
        """
        pass

    def shutdown_hardware(self):
        """Release or safely stop peripherals."""
        pass


def main(args=None):
    rclpy.init(args=args)

    node = RobotPeripheralsBridge()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown_hardware()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
