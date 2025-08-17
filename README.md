# <a href="https://github.com/cyan-at/eventdispatch" target="_blank">eventdispatch</a>
Event Dispatch: discrete time synchronization, Markov-chain control

## Documentation

The latest documentation on <a href="https://eventdispatch.readthedocs.io/en/latest/" target="_blank">readthedocs</a>

## python3: apt installation
```
sudo add-apt-repository ppa:cyanatlaunchpad/python3-eventdispatch-ppa
sudo apt update
sudo apt install python3-eventdispatch
```

## python3: <a href="https://pypi.org/project/eventdispatch/" target="_blank">pip</a> installation
```
virtualenv try-eventdispatch
. try-eventdispatch/bin/activate
pip install eventdispatch
```

## ROS2

Follow the instructions on the [Releases page](https://github.com/cyan-at/eventdispatch/releases/tag/ros2-jazzy)

1. stand up the `ed_node` instance via the launch file:
    ```
    ros2 launch eventdispatch_ros2 example1.launch events_module_path:=/home/charlieyan1/Dev/jim/eventdispatch/ros2 node_name:=example1
    ```

2. then trigger the `example1` `ed_node` instance via a `ROSEvent`:
    ```
    ros2 topic pub --once /example1/dispatch eventdispatch_ros2_interfaces/msg/ROSEvent "{string_array: ['WorkItemEvent'], int_array: [1]}"
    ```

3. you can also trigger a service call:
    ```
    ros2 service call /example1/dispatch eventdispatch_ros2_interfaces/srv/ROSEvent "{string_array: ['WorkItemEvent'], int_array: [1]}"
    ```

## Issues/Contributing

I do not expect the `core` module to be volatile much since the mechanism is very straightforward.

Any volatility can arguably be captured in `Event` or `EventDispatch` child classes.

Though it may be archived, I do actively maintain this repo. Please open an issue or file a fork+PR if you have any bugs/bugfixes/features!
