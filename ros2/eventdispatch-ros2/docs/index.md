# [eventdispatch-ros2 0.1.0](https://github.com/cyan-at/eventdispatch)

**eventdispatch-ros2** is a ROS2 package integrating [python3-eventdispatch](https://eventdispatch.readthedocs.io/en/latest/) with the [ROS2](https://docs.ros.org/en/foxy/index.html) ecosystem.

It consists of a `ed_node` **ROS node** and a `example.launch` to run it.

1. The node is designed to be instantiated >=1 times in a system.
2. Each `ed_node` instance can have a unique `node_name` and `events_module_path` parameter
3. The `events_module_path` is a filepath on the computer where the node expects a `events.py` python module
    * An example `events.py` module is [provided](https://github.com/cyan-at/eventdispatch/blob/main/ros2/events.py). This module contains [Event](https://eventdispatch.readthedocs.io/en/latest/classes/#event) definitions that implement a `ROS2` counterpart to the [example1 program in python3-evendispatch](https://github.com/cyan-at/eventdispatch/blob/main/python3/eventdispatch/eventdispatch/example1.py)
    * The idea is to keep system-level logic in these modules, and stand up EventDispatch instance(s) in `ROS2 launch files`
4. The `ed_node` exposes the dispatch as a `ROS2 service` and `ROS2 topic`, how to exercise them can be found [here](https://github.com/cyan-at/eventdispatch?tab=readme-ov-file#ros2)
