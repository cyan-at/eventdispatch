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

# ros2 topic pub --once /example1/dispatch eventdispatch_ros2_interfaces/msg/ROSEvent "{string_array: ['WorkItemEvent'], int_array: [3]}"

class ROS2QueueCVED(BlackboardQueueCVED, Node):
    def __init__(self, blackboard, name):
        BlackboardQueueCVED.__init__(self,
            blackboard, name + "_dispatch")
        Node.__init__(self, name + "_dispatch")

        self.declare_parameter(
            'events_module_path', '')
        self.events_module_path = self.get_parameter(
            'events_module_path').value

        self.callback_group = ReentrantCallbackGroup()
        self.create_service(EventSrv,
            '~/dispatch',
            self.srv_dispatch_cb,
            callback_group=self.callback_group # necessary
        )

        # https://docs.ros.org/en/rolling/Concepts/Intermediate/About-Quality-of-Service-Settings.html
        qos = QoSProfile(
            history=rclpy.qos.QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=rclpy.qos.QoSReliabilityPolicy.RELIABLE,
            durability=rclpy.qos.DurabilityPolicy.VOLATILE)
        self.create_subscription(
            EventMsg,
            '~/dispatch',
            self.msg_dispatch_cb,
            qos,
        )

    def dispatch_helper(self, rosevent):
        '''
        rosevent: obj that contains string_array, float_array, int_array
        
        for now, this is one event at a time
        TODO(implementer) dispatch more than one at a time
        '''
        payload = rosevent.string_array
        payload.extend(rosevent.int_array)
        payload.extend(rosevent.float_array)

        self.get_logger().warn('payload {}'.format(
            payload))

        if len(payload) > 0:
            self.get_logger().warn('going!!! {}'.format(
                len(payload)))

            # queue-and-notify pattern for maximum client responsiveness
            self.blackboard[self.cv_name].acquire()
            self.blackboard[self.queue_name].append(
                payload
            )
            self.blackboard[self.cv_name].notify(1)
            self.blackboard[self.cv_name].release()

    def msg_dispatch_cb(self, msg):
        self.get_logger().warn("msg_dispatch_cb {}".format(
            msg.string_array))

        self.dispatch_helper(msg)

    def srv_dispatch_cb(self, req, response):
        self.get_logger().warn("srv_dispatch_cb {}".format(
            req.string_array))

        self.dispatch_helper(req)

        return response

def main(args=None):
    ##### actors / iterables

    blackboard = Blackboard(volatile={
    })

    rclpy.init(args=args)

    node = ROS2QueueCVED(blackboard, "ros_ed")

    ##### event declarations
    if len(node.events_module_path) == 0:
        node.get_logger().warn('empty events module path, noop')
        sys.exit(0)

    sys.path.append(os.path.abspath(node.events_module_path))
    from events import event_dict, initial_events, events_module_update_blackboard
    node.get_logger().warn(
        "loaded {} events, {} initial_events".format(
            len(event_dict.keys()),
            len(initial_events))
        )
    blackboard.update(event_dict) # TODO(implementer) put this under a 'volatiles' key

    ##### volatiles

    events_module_update_blackboard(blackboard)

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

    ##### lifecycle

    blackboard["ros_ed_thread"].start()

    node.get_logger().info("ros_ed_thread started")

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
