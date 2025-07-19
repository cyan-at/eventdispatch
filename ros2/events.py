from eventdispatch.core import Event
from eventdispatch.common1 import *

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
        self.log("WorkItemEvent finish!", args, kwargs)

class UncertaintEvent1(CommonEvent):
    debug_color = bcolors.CYAN

    def dispatch(self, event_dispatch, *args, **kwargs):
        self.log("UncertaintEvent1 dispatch!", args, kwargs)

        time.sleep(random.randint(1, 5))

        with self.blackboard["result_mutex"]:
            self.blackboard["result1"] = random.randint(1, 5)

    def finish(self, event_dispatch, *args, **kwargs):
        self.log("UncertaintEvent1 finish!", args, kwargs)

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
        self.log("UncertaintEvent2 dispatch!", args, kwargs)

        time.sleep(random.randint(1, 10))

        with self.blackboard["result_mutex"]:
            self.blackboard["result2"] = random.randint(1, 10)

    def finish(self, event_dispatch, *args, **kwargs):
        self.log("UncertaintEvent2 finish!", args, kwargs)

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
        self.log("CheckEvent1 dispatch!", args, kwargs)

        s = args[1]
        self.log("CheckEvent1 sum", s)

        if s > 5 and args[0] > 0:
            self.log("CheckEvent1: sum big enough to continue")

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
            self.log("CheckEvent1: sum <= 5 or drained remaining WorkItems, prompting again")

            self.blackboard["input_sem"].release()

    def finish(self, event_dispatch, *args, **kwargs):
        self.log("CheckEvent1 finish!", args, kwargs)

event_dict = {
    'WorkItemEvent' : WorkItemEvent,
    'UncertaintEvent1' : UncertaintEvent1,
    'UncertaintEvent2' : UncertaintEvent2,
    'CheckEvent1' : CheckEvent1,
}

initial_events = [

]

def events_module_update_blackboard(blackboard):
    '''
    blackboard is the mutable Blackboard object
    '''
    blackboard["result_mutex"] = threading.Lock()
    blackboard["result1"] = 0
    blackboard["result2"] = 0

    blackboard["input_sem"] = threading.Semaphore(1)
