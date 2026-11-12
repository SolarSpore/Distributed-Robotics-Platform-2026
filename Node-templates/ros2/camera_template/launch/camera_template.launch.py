from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'camera_host',
            default_value='',
            description='Address of the camera device (required)',
        ),
        Node(
            package='camera_template',
            executable='camera_bridge_node',
            name='camera_bridge',
            output='screen',
            parameters=[{'camera_host': LaunchConfiguration('camera_host')}],
        ),
    ])
