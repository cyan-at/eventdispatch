from setuptools import setup, find_packages

setup(
    name='eventdispatch',
    version='0.1.5',
    description='Event Dispatch, a discrete time synchronizer',
    url='http://github.com/cyan-at/eventdispatch',
    author='Charlie Yan',
    author_email='cyanatg@gmail.com',
    license='Apache-2.0',
    install_requires=['requests'],
    packages=find_packages(),
    entry_points=dict(
        console_scripts=['rq=eventdispatch.main:display_quote']
    )
)