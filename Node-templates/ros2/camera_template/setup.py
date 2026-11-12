import os
from glob import glob

from setuptools import setup

package_name = 'camera_template'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='you',
    maintainer_email='you@example.com',
    description='Template: network camera bridge for ROS 2.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'camera_bridge_node = camera_template.camera_bridge_node:main',
        ],
    },
)
