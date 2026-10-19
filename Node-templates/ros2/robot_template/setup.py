from setuptools import find_packages, setup

package_name = 'robot_template'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        (
            'share/' + package_name,
            ['package.xml'],
        ),
        (
            'share/' + package_name + '/launch',
            ['launch/robot_template.launch.py'],
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    description='Generic ROS 2 robot platform template.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'robot_control_node = robot_template.robot_control_node:main',
            'robot_motor_bridge = robot_template.robot_motor_bridge:main',
            'robot_peripherals_bridge = robot_template.robot_peripherals_bridge:main',
        ],
    },
)
