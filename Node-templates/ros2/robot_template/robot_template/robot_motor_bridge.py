#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist


class RobotMotorBridge(Node):
    """
    Generic /cmd_vel -> hardware bridge template.

    The ROS interface is intentionally generic. The implementation of
    send_drive_command(), stop_hardware(), and shutdown_hardware() should
    be replaced by the actual robot's transport/hardware protocol.
    """

    def __init__(self):
        super().__init__('robot_motor_bridge')

        self.declare_parameter('send_rate_hz', 20.0)
        self.declare_parameter('cmd_vel_timeout', 0.5)

        self.send_rate_hz = self.get_parameter(
            'send_rate_hz').value
        self.cmd_vel_timeout = self.get_parameter(
            'cmd_vel_timeout').value

        self.last_cmd = Twist()
        self.last_cmd_time = self.get_clock().now()

        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10,
        )

        self.timer = self.create_timer(
            1.0 / self.send_rate_hz,
            self.send_command,
        )

    def cmd_vel_callback(self, msg: Twist):
        self.last_cmd = msg
        self.last_cmd_time = self.get_clock().now()

    def send_command(self):
        age = (
            self.get_clock().now() - self.last_cmd_time
        ).nanoseconds / 1e9

        if age > self.cmd_vel_timeout:
            self.stop_hardware()
            return

        self.send_drive_command(self.last_cmd)

    def send_drive_command(self, msg: Twist):
        """
        Replace this with the robot-specific hardware protocol.

        Examples:
        - UDP
        - serial
        - CAN
        - micro-ROS
        - vendor API
        """
        pass

    def stop_hardware(self):
        """Send a safe zero-motion command to the hardware."""
        pass

    def shutdown_hardware(self):
        """Perform final hardware shutdown/stop handling."""
        self.stop_hardware()


def main(args=None):
    rclpy.init(args=args)

    node = RobotMotorBridge()

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
