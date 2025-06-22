#! /usr/bin/env python3

import os, sys, time
file_directory = os.path.dirname(os.path.abspath(__file__)) + "/"

from eventdispatch.core import *
from eventdispatch.aux1 import *

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, DurabilityPolicy
from rcl_interfaces.msg import ParameterDescriptor

from eventdispatch_ros2_interfaces.srv import ROSEvent as EventSrv
from eventdispatch_ros2_interfaces.msg import ROSEvent as EventMsg

class ROS2QueueCVED(BlackboardQueueCVED, Node):
    def __init__(self, blackboard, name):
        BlackboardQueueCVED.__init__(self,
            blackboard, name + "_dispatch")
        Node.__init__(self, name + "_dispatch")

        self.callback_group = ReentrantCallbackGroup()
        self.create_service(EventSrv,
            '~/dispatch',
            self.dispatch_cb,
            callback_group=self.callback_group # necessary
        )

    def dispatch_cb(self, req, response):
        self.get_logger().warn("dispatch_cb {}".format(
            req.string_array))

        if len(req.string_array) > 0:
            # queue-and-notify pattern for maximum client responsiveness
            self.blackboard[self.cv_name].acquire()
            self.blackboard[self.queue_name].append(
                req.string_array
            )
            self.blackboard[self.cv_name].notify(1)
            self.blackboard[self.cv_name].release()

        return response

def main(args=None):
    ##### actors / iterables

    blackboard = Blackboard(volatile={
    })

    rclpy.init(args=args)

    node = ROS2QueueCVED(blackboard, "ros_ed")

    blackboard["ros_ed_thread"] = Thread(
    target=node.run,
    args=(blackboard,
        "ros_ed",

        # "done",
        None,

        bcolors.DARKGRAY,
        # None
    ))
    blackboard["ros_ed"] = node

    ##### event declarations

    ##### volatiles

    ##### lifecycle

    blackboard["ros_ed_thread"].start()

    ### dispatch any 'initiail condition' events here

    executor = MultiThreadedExecutor()
    try:
        rclpy.spin(node, executor)
    except KeyboardInterrupt:
        pass
    except rclpy.executors.ExternalShutdownException:
        pass
    finally:
        print("killing ros_ed_thread")
        blackboard[node.hb_key] = False
        with blackboard[node.mutex_name]:
            blackboard[node.cv_name].notify_all()
        blackboard["ros_ed_thread"].join()

        rclpy.try_shutdown()
        node.destroy_node()

if __name__ == '__main__':
    main()
