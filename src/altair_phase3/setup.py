import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'altair_phase3'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Mihiya',
    maintainer_email='candidate@altair.org',
    description='Project Altair Software Recruitment Batch 24 - Phase 3 Assessment ROS 2 Package',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mars_telemetry_publisher = altair_phase3.mars_telemetry_publisher:main',
            'telemetry_pub = altair_phase3.mars_telemetry_publisher:main',
            'mission_control_monitor = altair_phase3.mission_control_monitor:main',
            'turtle_driver = altair_phase3.turtle_driver:main',
            'field_mission = altair_phase3.field_mission:main',
        ],
    },
)
