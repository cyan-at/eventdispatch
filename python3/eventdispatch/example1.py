#!/usr/bin/env python3
'''
Created on 2025-05-23

@author: Charlie Yan

Copyright (c) 2025, Charlie Yan
License: Apache-2.0 (see LICENSE for details)
'''

from .core import *
from .aux1 import *

import signal, time, os, sys, random, threading

# these are examples Event classes
# together, they define the drift and control in a system
# defined here, they are registered as key-value paris in the Blackboard instance below

class WorkItemEvent(CommonEvent):
    debug_color = bcolors.WARNING

    def dispatch(self, event_dispatch, *args, **kwargs):
        self.log("WorkItemEvent: {} remaining items".format(args[0]))

        self.blackboard[event_dispatch.cv_name].acquire()
        self.blackboard[event_dispatch.queue_name].extend([
            [
                "UncertaintEvent1",
                args[0]-1
            ],
            [
                "UncertaintEvent2",
                args[0]-1
            ]
        ])
        self.blackboard[event_dispatch.cv_name].notify(1)
        self.blackboard[event_dispatch.cv_name].release()

    def finish(self, event_dispatch, *args, **kwargs):
        self.log("finish!", args, kwargs)

class UncertaintEvent1(CommonEvent):
    debug_color = bcolors.CYAN

    def dispatch(self, event_dispatch, *args, **kwargs):
        self.log("dispatch!", args, kwargs)

        time.sleep(random.randint(1, 5))

        with self.blackboard["result_mutex"]:
            self.blackboard["result1"] = random.randint(1, 5)

    def finish(self, event_dispatch, *args, **kwargs):
        self.log("finish!", args, kwargs)

        with self.blackboard["result_mutex"]:
            if self.blackboard["result2"] > 0:
                self.log("UncertaintEvent2 wins")
  
                s = self.blackboard["result1"] + self.blackboard["result2"]
                self.blackboard["result1"] = 0
                self.blackboard["result2"] = 0

                self.blackboard[event_dispatch.cv_name].acquire()
                self.blackboard[event_dispatch.queue_name].extend([
                    [
                        "CheckEvent1",
                        args[0],
                        s
                    ],
                ])
                self.blackboard[event_dispatch.cv_name].notify(1)
                self.blackboard[event_dispatch.cv_name].release()

class UncertaintEvent2(CommonEvent):
    debug_color = bcolors.MAGENTA

    def dispatch(self, event_dispatch, *args, **kwargs):
        self.log("dispatch!", args, kwargs)

        time.sleep(random.randint(1, 10))

        with self.blackboard["result_mutex"]:
            self.blackboard["result2"] = random.randint(1, 10)

    def finish(self, event_dispatch, *args, **kwargs):
        self.log("finish!", args, kwargs)

        with self.blackboard["result_mutex"]:
            if self.blackboard["result1"] > 0:
                self.log("UncertaintEvent1 wins")

                s = self.blackboard["result1"] + self.blackboard["result2"]
                self.blackboard["result1"] = 0
                self.blackboard["result2"] = 0

                self.blackboard[event_dispatch.cv_name].acquire()
                self.blackboard[event_dispatch.queue_name].extend([
                    [
                        "CheckEvent1",
                        args[0],
                        s
                    ],
                ])
                self.blackboard[event_dispatch.cv_name].notify(1)
                self.blackboard[event_dispatch.cv_name].release()

class CheckEvent1(CommonEvent):
    debug_color = bcolors.RED

    def dispatch(self, event_dispatch, *args, **kwargs):
        self.log("dispatch!", args, kwargs)

        s = args[1]
        self.log("sum", s)

        if s > 5 and args[0] > 0:
            self.log("results big enough to continue")

            self.blackboard[event_dispatch.cv_name].acquire()
            self.blackboard[event_dispatch.queue_name].extend([
                [
                    "WorkItemEvent",
                    args[0],
                ],
            ])
            self.blackboard[event_dispatch.cv_name].notify(1)
            self.blackboard[event_dispatch.cv_name].release()
        else:
            self.log("results not big enough or drained WorkItems, asking again")

            self.blackboard["input_sem"].release()

    def finish(self, event_dispatch, *args, **kwargs):
        self.log("finish!", args, kwargs)

# this is an example of an 'Actor' / 'continuous-time' process
# a specialist in the system, that injects entrypoint Event(s)
# into the system
class KeyboardThread(threading.Thread):
    def __init__(self, mutable_hb, blackboard, ed1):
        self.mutable_hb = mutable_hb
        self.blackboard = blackboard
        self.ed1 = ed1

        super(KeyboardThread, self).__init__()

    def my_callback(self, x, mutable_hb, blackboard, ed1):
        if len(x) == 0:
            print("empty")
            return True

        x = int(x)

        #evaluate the keyboard input
        if x == 0:
            print("turning off dispatch")
            with ed1.dispatch_switch_mutex:
                ed1.dispatch_switch = False

            return True

        elif x == 1:
            print("turning on dispatch")
            with ed1.dispatch_switch_mutex:
                ed1.dispatch_switch = True

            return True

        elif x == -1:
            print('exiting')

            # stop this thread
            with mutable_hb['hb_lock']:
                mutable_hb['hb'] = False

            # stop ed thread
            blackboard[ed1.hb_key] = False
            with blackboard[ed1.mutex_name]:
                blackboard[ed1.cv_name].notify_all()

            return True

        elif x >= 2 and x <= 5:
            print("dispatching WorkItemEvent(%d)" % (x))

            blackboard[ed1.cv_name].acquire()
            blackboard[ed1.queue_name].append(
            [
                "WorkItemEvent",
                (
                    x
                )
            ])
            blackboard[ed1.cv_name].notify(1)
            blackboard[ed1.cv_name].release()

            release = False
            with ed1.dispatch_switch_mutex:
                if not ed1.dispatch_switch:
                    release = True

            return release

        return False

    def run(self):
        local_hb = True

        while local_hb:
            self.blackboard["input_sem"].acquire()

            if not self.blackboard["ask"]:
                print("no longer asking, break")
                break

            x = input('enter a number 2-5, 0 to turn off dispatch, 1 to turn on dispatch, -1 to exit\n')

            release = self.my_callback(x, self.mutable_hb, self.blackboard, self.ed1)
            if release:
                self.blackboard["input_sem"].release()

            with self.mutable_hb['hb_lock']:
                local_hb = self.mutable_hb['hb']

def main():
    print("###################")
    print("This program exercises some EventDispatch best practices and patterns")
    print("Type a number to command the system")
    print("Some commands will dispatch Events, which in turn dispatch other Events")
    print("###################")

    # 0. Create `Blackboard` instance(s)
    blackboard = Blackboard()

    # 1. Populate the `Blackboard` with `Event` declarations (name : type pairs)
    blackboard["WorkItemEvent"] = WorkItemEvent
    blackboard["UncertaintEvent1"] = UncertaintEvent1
    blackboard["UncertaintEvent2"] = UncertaintEvent2
    blackboard["CheckEvent1"] = CheckEvent1

    blackboard["result_mutex"] = threading.Lock()
    blackboard["result1"] = 0
    blackboard["result2"] = 0

    blackboard["ask"] = True
    blackboard["input_sem"] = threading.Semaphore(1)

    # 2. Create `BlackboardQueueCVED` instance(s) with their individual `name` strings
    ed1 = BlackboardQueueCVED(
        blackboard,
        "ed1"
    )
    blackboard["ed1"] = ed1

    # 3. Stand up their `run` targets as threads
    blackboard["ed1_thread"] = Thread(
        target=ed1.run,
        args=(
            blackboard,
            "ed1",
            None,
            bcolors.OKGREEN,
        ))
    blackboard["ed1_thread"].start()

    # main thread goes here
    mutable_hb = {
        "hb_lock" : threading.Lock(),
        "hb" : True,
    }
    kthread = KeyboardThread(mutable_hb, blackboard, ed1)
    kthread.start()

    # 4. Best practice (thread hygiene): on program shutdown
    # notify the `BlackboardQueueCVED` cvs and join their `run` threads
    def signal_handler(signal, frame):
        print("killing ed1_thread")
        blackboard[ed1.hb_key] = False
        with blackboard[ed1.mutex_name]:
            blackboard[ed1.cv_name].notify_all()
        blackboard["ed1_thread"].join()

        blackboard["ask"] = False
        blackboard["input_sem"].release()

        print("shutting down")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    blackboard["ed1_thread"].join()
    kthread.join()

if __name__ == '__main__':
    main()