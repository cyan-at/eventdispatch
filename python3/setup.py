from setuptools import setup, find_packages

setup(
    name='eventdispatch',
    version='0.1.15',
    description='Event Dispatch, a discrete time synchronizer',
    url='http://github.com/cyan-at/eventdispatch',
    author='Charlie Yan',
    author_email='cyanatg@gmail.com',
    license='Apache-2.0',
    install_requires=[],
    packages=find_packages(),
    entry_points=dict(
        console_scripts=['eventdispatch_example1=eventdispatch.example1:main']
    )
)