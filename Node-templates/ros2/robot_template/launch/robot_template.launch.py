from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='robot_template',
            executable='robot_control_node',
            name='robot_control_node',
            output='screen',
        ),

        Node(
            package='robot_template',
            executable='robot_motor_bridge',
            name='robot_motor_bridge',
            output='screen',
        ),

        Node(
            package='robot_template',
            executable='robot_peripherals_bridge',
            name='robot_peripherals_bridge',
            output='screen',
        ),
    ])
