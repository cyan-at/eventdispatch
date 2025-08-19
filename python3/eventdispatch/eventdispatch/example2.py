#!/usr/bin/env python3
'''
Created on 2025-08-02

@author: Charlie Yan

Copyright (c) 2025, Charlie Yan
License: Apache-2.0 (see LICENSE for details)
'''

from .core import *
from .common1 import *
from .composite_semaphore import *
from .example1 import *

# from core import *
# from common1 import *
# from composite_semaphore import *
# from example1 import KeyboardThread

import signal, time, os, sys, random, threading

class PrintReleaseEvent(CommonEvent):
    debug_color = bcolors.WARNING

    def dispatch(self, event_dispatch, *args, **kwargs):
        self.log("PrintReleaseEvent: printing {}".format(args[0]))

    def finish(self, event_dispatch, *args, **kwargs):
        self.log("PrintReleaseEvent finish!", args, kwargs)

        if len(args) <= 1:
            return

        # taken from CSRelease
        ls = list(set(list(args[1])))

        self.blackboard[event_dispatch.cv_name].acquire()
        self.blackboard[event_dispatch.queue_name].extend(
            [

                [
                    "CSRelease",
                    ",".join([str(x) for x in ls]),
                    "",
                    0
                ]
            ])
        self.blackboard[event_dispatch.cv_name].notify(1)
        self.blackboard[event_dispatch.cv_name].release()

        # self.blackboard["input_sem"].release()

class KeyboardThread2(KeyboardThread):
    def cb_1(self, x, mutable_hb, blackboard, ed1):
        if len(x) == 0:
            print("empty")
            return True

        #evaluate the keyboard input
        if x == "0":
            print("turning off dispatch")
            with ed1.dispatch_switch_mutex:
                ed1.dispatch_switch = False

            return True

        elif x == "1":
            print("turning on dispatch")
            with ed1.dispatch_switch_mutex:
                ed1.dispatch_switch = True

            return True

        elif x == "-1":
            print('exiting')

            # the same as signal_handler below (TODO):
            print("notifying all CSWaits")
            if "cs_registry" in blackboard["volatile"]:
                with blackboard["volatile"]["cs_registry_l"]:
                    for k, v in blackboard["volatile"]["cs_registry"].items():
                        for s in v.semaphores.values():
                            s[0]["status"] = -1
                            # or just look at cs.mutable_hb?
                            s[1].release()

            # stop this thread
            with mutable_hb['hb_lock']:
                mutable_hb['hb'] = False

            # stop ed thread
            blackboard[ed1.hb_key] = False
            with blackboard[ed1.mutex_name]:
                blackboard[ed1.cv_name].notify_all()

            return True

        # catch all left numbers
        blocks = []
        j = 0
        i = 1
        while i < len(x):
            left = x[i-1].isnumeric()
            right = x[i].isnumeric()
            if left != right:
                blocks.append(x[j:i])
                j = i
            i += 1
        blocks.append(x[j:i])
        print("DECOMPOSITION: {}".format(blocks))

        # if len(blocks) > 3:
        #     print("input not supported for now")
        #     return True

        # if len(blocks) == 1:
        #     # if blocks[0].isnumeric():
        #     print("input not supported for now")
        #     return True

        if len(blocks) != 2:
            print("!=2 input not supported for now")
            return True

        print(blocks[0])

        if not blocks[0].isnumeric():
            unique_letters = set(list(blocks[0]))
            unique_numbers = set(list(blocks[1]))

            blackboard[ed1.cv_name].acquire()
            blackboard[ed1.queue_name].extend(
                # every number on the right waits for every letter on the left

                # every letter on the left releases itself
                # the CSWait on every letter holds every number
                # until all letters are printed

                [

                    [
                        "PrintReleaseEvent",
                        letter,
                        letter
                    ]
                    for letter in unique_letters
                ] + [
                    [
                        "CSWait",
                        ",".join([str(x) for x in unique_letters]),

                        "CSRelease",
                        ",".join([str(x) for x in unique_numbers]),
                        "",
                        0
                    ]
                ]
            )
            blackboard[ed1.cv_name].notify(1)
            blackboard[ed1.cv_name].release()
        else:
            unique = set(list(blocks[0]))

            blackboard[ed1.cv_name].acquire()
            blackboard[ed1.queue_name].extend(
                [
                    [
                        "CSWait",
                        ",".join([str(x) for x in unique]),

                        "PrintReleaseEvent",
                        x
                    ] for x in blocks[1]
                ])
            blackboard[ed1.cv_name].notify(1)
            blackboard[ed1.cv_name].release()

        return True


def main():
    print("###################")
    print("This program exercises the CSBQCVED CSWait CSRelease mechanism")
    print("Type a number to command the system, of the form ####aaa or aaa#####, where # = [0,9]")
    print("If # comes first, that command will match the # signal with printing the letter(s)")
    print("If a comes first, that command will match printing the letter(s) with producing those # signals")
    print("")
    print("In this way, you can create on-the-fly associations between printing some letters with printing others")
    print("###################")

    # 0. Create `Blackboard` instance(s)
    blackboard = Blackboard()

    # 1. Populate the `Blackboard` with `Event` declarations (name : type pairs)
    blackboard["PrintReleaseEvent"] = PrintReleaseEvent
    blackboard["CSWait"] = CSWait
    blackboard["CSRelease"] = CSRelease

    blackboard["ask"] = True
    blackboard["input_sem"] = threading.Semaphore(1)

    # 2. Create `BlackboardQueueCVED` instance(s) with their individual `name` strings
    ed1 = CSBQCVED(
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
    kthread = KeyboardThread2(mutable_hb, blackboard, ed1)
    kthread.start()

    # 4. Best practice (thread hygiene): on program shutdown
    # notify the `BlackboardQueueCVED` cvs and join their `run` threads
    def signal_handler(signal, frame):
        print("notifying all CSWaits")
        if "cs_registry" in blackboard["volatile"]:
            with blackboard["volatile"]["cs_registry_l"]:
                for k, v in blackboard["volatile"]["cs_registry"].items():
                    for s in v.semaphores.values():
                        s[0]["status"] = -1
                        # or just look at cs.mutable_hb?
                        s[1].release()

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