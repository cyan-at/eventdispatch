import os
from setuptools import setup
from glob import glob

package_name = 'eventdispatch_ros2'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch'))),
    ],
    zip_safe=True,
    maintainer='Charlie Yan',
    maintainer_email='cyanatg@gmail.com',
    description='ROS2 Jazzy wrapper for python3-eventdispatch',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
              'ed_node = eventdispatch_ros2.ed_node:main',
        ],
    },
)
