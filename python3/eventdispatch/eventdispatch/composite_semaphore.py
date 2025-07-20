#! /usr/bin/env python3

import os, sys, time
import threading, signal

from .core import *
from .common1 import *

'''
a thread-safe data structure

on the left ('releasing/left')
    a set that you 'tick' down
    but resetting it takes O(1) complexity

    the set is also dynamic:
        when the set is completely full
        you can change its values / keys

        once it is partially tick'd
        this is forbidden

on the right ('acquiring/right')
    a dynamics set of callbacks to fire
    it is free-form here
    per free-form thing, release underlying(s) semaphore
'''
class CompositeSemaphore(object):
    # not really colloidal
    def __init__(self, initial_keys):
        self.left_lock = threading.Lock()

        self.counters = { k : [0, None] for k in initial_keys }

        self.rollover = 100
        self.tick = 1
        self.key_count = len(initial_keys)

        self.right_lock = threading.Lock()
        # semaphores change based on # of clients, not on fixed int
        # key: requester, value: (mutable_shared, semaphore)
        # you update the mutable_shared with result, before you
        # release the semaphore
        # this way, clients that are 'acquiring' you
        # you can unblock in different ways
        self.semaphores = {}

        self.semaphore_lock = threading.Lock()

        self.mutable_hb = {
            "hb" : True,
            "hb_lock" : threading.Lock()
        }

    def add_left(self, k):
        with self.semaphore_lock:
            if not self.mutable_hb["hb"]:
                # print("cs killed")
                return

            if k not in self.counters:
                initial_value = (self.tick - 1) % (self.rollover)
                self.counters[k] = [initial_value, None]
                self.key_count += 1

    def clear_left(self, k):
        with self.semaphore_lock:
            if not self.mutable_hb["hb"]:
                # print("cs killed")
                return

            self.counters.pop(k)
            self.key_count -= 1

    def wraparound_idempotent_increment(
        self, k, identifier=None):
        if self.tick > self.counters[k][0]:
            self.counters[k][0] += 1
            self.counters[k][1] = identifier
            return True
        elif self.tick < self.counters[k][0]:
            # the only time tick < counters[k]
            # is when:
            # counters[k]: MAX-1 -> MAX
            # tick from MAX -> 0
            self.counters[k][0] = 0
            self.counters[k][1] = identifier
            return True
        else:
            # noop if tick == counters[k]
            return False

    def release(self, k, identifier=None):
        go = True
        with self.mutable_hb["hb_lock"]:
            if not self.mutable_hb["hb"]:
                # print("cs dead")
                go = False
        if not go:
            return

        with self.left_lock:
            if k in self.counters:
                # print("counter", self.counters, self.key_count, k)
                if (self.wraparound_idempotent_increment(k, identifier)):
                    # semaphore_lock is locked between
                    # when it is decrementing and reaches 0
                    # this 'frame' is when you cannot edit
                    # the left
                    if not self.semaphore_lock.locked():
                        self.semaphore_lock.acquire()

                    self.key_count = max(0, self.key_count - 1)
                    # print("key_count", self.key_count)

                    if self.key_count == 0:
                        # signal acquire(s)!
                        # consider counters tuple[1]
                        status = identifier if identifier is not None else 1
                        for s in self.semaphores.values():
                            s[0]["status"] = status
                            # or just look at cs.mutable_hb?
                            s[1].release()
                        # do not pop semaphores
                        self.semaphore_lock.release()

                        # 'reset' the semaphore bookkeeping
                        self.tick = (self.tick + 1) % (self.rollover)
                        self.key_count = len(self.counters.keys())
                        # print("DONE!")
                # else:
                    # print("dead", k)
            # else:
            #     print("not found", k)

    def acquire(self, identifier, mutable_shared):
        # decorator?
        go = True
        with self.mutable_hb["hb_lock"]:
            if not self.mutable_hb["hb"]:
                print("cs dead")
                go = False
        if not go:
            return

        with self.right_lock:
            self.semaphores[identifier] = (
                mutable_shared,
                threading.Semaphore(1)
            )
            self.semaphores[identifier][1].acquire()

        self.semaphores[identifier][1].acquire()

def produce_target(sem, x, e, c):
    e.wait(x)

    if not c.heartbeat:
        print("p shutdown")
        return

    print("{} producing {}! ".format(x, x % 9))
    sem.release(x % 9, "producer_{x}")

def consume_target(sem, x, delay, c, e):
    if delay > 0:
        e.wait(delay * 5)

    if not c.heartbeat:
        print("c shutdown")
        return

    print("registering {}".format(x))
    mutable_shared = {"status" : 0}

    with c.update2:
        c.count += 1
        c.cv.notify_all()

    sem.acquire(x, mutable_shared)

    print("consumer woken! ",
        mutable_shared["status"])

    with c.update2:
        c.count -= 1
        c.cv.notify_all()

    c.update2.acquire()
    while c.count > 0:
        c.cv.wait()
    c.update2.release()

    if not c.heartbeat:
        print("conumer shutdown")
        return

    if len(c.l) > 0:
        k = c.l.pop(0)
        print("adding key {}".format(k))
        sem.add_left(k)
        c.r.append(k)

    # do not clear until all consumers woken again
    elif len(c.r) > 0:

        k = c.r.pop(0)
        print("clearing key {}".format(k))
        sem.clear_left(k)
        c.s.append(k)

class CompositeSemaphoreWait(CommonEvent):
    debug_color = bcolors.OKGREEN

    def release_instance(self,
        instance_id,
        instance,
        product,
        instance_increment):

        lock_name = "{}_latest_instance_lock".format(instance_id)
        if lock_name not in self.blackboard:
            return

        with self.blackboard[lock_name]:
            if instance_increment != 0:
                self.blackboard["{}_instance_count".format(instance_id)] += instance_increment
            else:
                self.blackboard["{}_instance_count".format(instance_id)] = \
                    self.blackboard["{}_instance_count".format(instance_id)]
            self.blackboard["{}_latest_instance".format(instance_id)].append((
                product, instance))

    def dispatch(self, event_dispatch, *args, **kwargs):
        # only CmdEvent takes the a non-blocking-post-dispatch-throttled semaphore
        # CSWaits are not throttled, by design choice

        # must be unique
        with self.blackboard["volatile"]["cs_registry_l"]:
            if args[0] in self.blackboard["volatile"]["cs_set"]:
                self.log("cs exists, bailing")
                self.mutable_shared["status"] = -1
                return

        self.log("{} cs init + acquiring".format(
            args[0]))

        self.pending = args[2:]
        self.log("pending {}".format(self.pending))

        # hacky: negative cs numbers
        # means timeout == passthrough
        # otherwise, timeout == noop
        l = [int(x) for x in args[0].split(",")]
        self.ATTN_TIMER_IDX_passthrough = l[0] < 0

        self.blackboard["volatile"]["cs_set"].update(l)

        if len(l) > 1:
            self.cs = CompositeSemaphore(
                l
            )
            with self.blackboard["volatile"]["cs_registry_l"]:
                for li in l:
                    # all the lefts point to the same cs
                    self.blackboard["volatile"]["cs_registry"][li] = self.cs

            # tell JsonEvent this cs mouth is open
            with self.blackboard["volatile"]["cs_cv_l"]:
                self.blackboard["volatile"]["cs_cv"].notify_all()
        elif len(l) == 1:
            with self.blackboard["volatile"]["cs_registry_l"]: 
                if l[0] in self.blackboard["volatile"]["cs_registry"]:
                    self.cs = self.blackboard["volatile"]["cs_registry"][
                    l[0]]
                else:
                    self.cs = self.blackboard["volatile"]["cs_registry"][l[0]] =\
                        CompositeSemaphore(l)

            # tell JsonEvent this cs mouth is open
            with self.blackboard["volatile"]["cs_cv_l"]:
                self.blackboard["volatile"]["cs_cv"].notify_all()
        else:
            self.log("no left cs keys!? bypassing")
            self.mutable_shared["status"] = 2
            return

        # self.instance = "{}_{}".format(
        #     self.scmd,
        #     self.event_id
        # )

        self.instance_id = args[1]
        self.instance = args[2:]
        self.release_instance(
            self.instance_id,
            self.instance,
            "semaphored",
            0)

        # hacky!!! TODO(Charlie) cleanup
        # CmdEvent args: ('up', 'JsonEvent_0', 'rsim', '0,1,2,3,4,5,6,7,8,9')
        # pending ('CmdEvent', 'up', 'thermal')
        self.new_pending = tuple(self.pending[:2]) + (args[1],) + tuple(self.pending[2:])
        self.log("new_pending {}".format(self.new_pending))

        self.ls = l
        self.new_key = args[0]

        self.mutable_shared = {"status" : 0}
        self.cs.acquire(
            self.instance,
            self.mutable_shared
        )

    def cleanup(self):
        self.log("cleaning up {}".format(self.ls))
        with self.blackboard["volatile"]["cs_registry_l"]:
            for l in self.ls:
                x = self.blackboard["volatile"]["cs_registry"].pop(l)
                del x

            if self.new_key in self.blackboard["volatile"]["cs_set"]:
                self.log("popping key")
                self.blackboard["volatile"]["cs_set"].remove(
                    self.new_key)

            self.log("after {}".format(
                self.blackboard["volatile"]["cs_registry"].keys())
            )

    def finish(self, event_dispatch, *args, **kwargs):
        self.cleanup()

        if self.mutable_shared["status"] == -1:
            self.log("CompositeSemaphoreWait noop")
            return

        self.log(
            "CompositeSemaphoreWait unblocking {} on {}".format(
            self.mutable_shared["status"],
            self.pending))

        # this is the the last left identifier
        # if it is a timerkill
        # react differently / noop
        if type(self.mutable_shared["status"]) == tuple:
            if self.mutable_shared["status"][1] == ATTN_TIMER_IDX and not self.ATTN_TIMER_IDX_passthrough:
                self.log("LAST LEFT was ATTN_TIMER_IDX, releasing instances")

                self.release_instance(
                    self.instance_id,
                    self.instance,
                    "cs timed out",
                    -1)

                return
            elif self.mutable_shared["status"][1] == ATTN_DUPLEX_IDX and self.ATTN_TIMER_IDX_passthrough:
                self.log("LAST LEFT was ATTN_DUPLEX_IDX, releasing instances")

                self.release_instance(
                    self.instance_id,
                    self.instance,
                    "timeout cs duplex'd",
                    -1)

                return
            else:
                self.log("LAST LEFT passthrough")

                self.release_instance(
                    self.instance_id,
                    self.instance,
                    "cs unblocked",
                    0)

        self.blackboard["ed1_cv"].acquire()
        self.blackboard["ed1_queue"].append(
            self.new_pending
        )
        self.blackboard["ed1_cv"].notify(1)
        self.blackboard["ed1_cv"].release()

class CSRelease(CommonEvent):
    debug_color = bcolors.MAGENTA

    def dispatch(self, event_dispatch, *args, **kwargs):
        if len(args) != (2+1):
            self.log("ARGS {}".format(len(args)))
            return

        cs_list = [int(x) for x in args[0].split(",")]
        duplex_or_timeout = int(args[2])

        self.log("releasing on {}, {}".format(args[0], args[2]))

        for cs in cs_list:
            with self.blackboard["volatile"]["cs_registry_l"]:
                if cs not in self.blackboard["volatile"]["cs_registry"]:
                    continue
                self.blackboard["volatile"]["cs_registry"][cs].release(
                    cs,
                    (self.instance, duplex_or_timeout))

    def finish(self, event_dispatch, *args, **kwargs):
        pass

class Collector(object):
    def __init__(self, l):
        self.heartbeat = True

        self.count = 0
        self.update2 = threading.Lock()
        self.cv = threading.Condition(self.update2)

        self.l = l
        self.r = []
        self.s = []

def main():
    s = 4

    sem1 = CompositeSemaphore([x for x in range(s)])

    keys_to_add = Collector([4,5,6,7,8])

    c_events = [threading.Event() for x in range(s*4)]
    c_threads = [threading.Thread(
        target=lambda sem1=sem1, add=keys_to_add, x=x: consume_target(sem1, x, x // 5, add, c_events[x]))\
        for x in range(s*4)] # s*3:
    for th in c_threads:
        th.start()

    events = [threading.Event() for x in range(s*6)]
    p_threads = [threading.Thread(
        target=lambda sem1=sem1, x=x: produce_target(sem1, x, events[x], keys_to_add))\
        for x in range(s*6)] # s*4, s*2:
    for th in p_threads:
        th.start()

    def signal_handler(signal, frame):
        print("killing all threads")

        with sem1.mutable_hb["hb_lock"]:
            sem1.mutable_hb["hb"] = False

        keys_to_add.heartbeat = False

        #############################

        for e in c_events:
            e.set()

        for e in events:
            e.set()

        print("notifying all")
        for s in sem1.semaphores.values():
            s[0]["status"] = -1
            s[1].release()

        with keys_to_add.update2:
            keys_to_add.cv.notify_all()

        #############################

        print("shutting down")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    for th in c_threads:
        th.join()
    for th in p_threads:
        th.join()

if __name__ == "__main__":
    main()