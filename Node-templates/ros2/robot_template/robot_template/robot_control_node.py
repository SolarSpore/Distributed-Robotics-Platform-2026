#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy


class RobotControlNode(Node):
    """
    Generic gamepad-to-Twist controller template.

    This deliberately contains only the platform-level control pattern.
    Robot-specific modes, button mappings, and special controls belong in
    the robot implementation derived from this template.
    """

    def __init__(self):
        super().__init__('robot_control_node')

        self.declare_parameter('enable_button', 0)
        self.declare_parameter('turbo_button', 1)

        self.declare_parameter('axis_linear', 1)
        self.declare_parameter('axis_angular', 0)

        self.declare_parameter('scale_linear', 0.5)
        self.declare_parameter('scale_angular', 1.0)

        self.enable_button = self.get_parameter(
            'enable_button').value
        self.turbo_button = self.get_parameter(
            'turbo_button').value

        self.axis_linear = self.get_parameter(
            'axis_linear').value
        self.axis_angular = self.get_parameter(
            'axis_angular').value

        self.scale_linear = self.get_parameter(
            'scale_linear').value
        self.scale_angular = self.get_parameter(
            'scale_angular').value

        self.joy_subscription = self.create_subscription(
            Joy,
            'joy',
            self.joy_callback,
            10,
        )

        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            'cmd_vel',
            10,
        )

    def joy_callback(self, msg: Joy):
        enabled = (
            self.enable_button < len(msg.buttons)
            and msg.buttons[self.enable_button]
        )

        twist = Twist()

        if not enabled:
            self.cmd_vel_publisher.publish(twist)
            return

        linear = 0.0
        angular = 0.0

        if self.axis_linear < len(msg.axes):
            linear = msg.axes[self.axis_linear]

        if self.axis_angular < len(msg.axes):
            angular = msg.axes[self.axis_angular]

        scale = 1.0

        if (
            self.turbo_button < len(msg.buttons)
            and msg.buttons[self.turbo_button]
        ):
            scale = 2.0

        twist.linear.x = linear * self.scale_linear * scale
        twist.angular.z = angular * self.scale_angular * scale

        self.cmd_vel_publisher.publish(twist)


def main(args=None):
    rclpy.init(args=args)

    node = RobotControlNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
