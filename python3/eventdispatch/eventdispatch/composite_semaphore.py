#! /usr/bin/env python3

import os, sys, time
import threading, signal

from .core import *
from .common1 import *

# from core import *
# from common1 import *

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

#######################################

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


class Collector(object):
    def __init__(self, l):
        self.heartbeat = True

        self.count = 0
        self.update2 = threading.Lock()
        self.cv = threading.Condition(self.update2)

        self.l = l
        self.r = []
        self.s = []

#######################################

class CSWait(CommonEvent):
    debug_color = bcolors.BLUE

    def prior_cb(self, args):
        '''
        override for your use case
        '''
        pass

    def get_pending(self, args):
        '''
        override for your use case
        '''
        self.log("args {}".format(args))
        return list(args[1:])

    def post_cb(self, args):
        '''
        override for your use case
        '''
        pass

    @staticmethod
    def parse_lefts(s):
        tokens = sorted(list(set(s.split(","))))

        return tokens, ",".join(tokens)

    def dispatch(self, event_dispatch, *args, **kwargs):
        # only CmdEvent takes the a non-blocking-post-dispatch-throttled semaphore
        # CSWaits are not throttled, by design choice

        '''
        args[0]:
        int(s), signals

        args[1]:
        ignore

        args[2:]
        arguments for waiting event
        '''
        self.mutable_shared = {"status" : 0}

        ls, identifier = CSWait.parse_lefts(args[0])
        # this must be consistent with dispatch and with CSRelease

        self.ls = ls
        self.identifier = identifier

        if len(ls) == 0:
            self.log("no left cs keys!? bypassing")
            self.mutable_shared["status"] = 2
            return

        #######################

        # self.exception = False

        # must be unique
        with self.blackboard["volatile"]["cs_registry_l"] and self.blackboard["volatile"]["cs_cv_l"]:
            if identifier in self.blackboard["volatile"]["cs_set"]: # implicit no-overlap (black/white matching TODO?)
                self.log("cs exists")
                # self.mutable_shared["status"] = -1
                self.cs = self.blackboard["volatile"]["cs_registry"][self.ls[0]]
            # elif len(set.intersection(
            #     set(self.blackboard["volatile"]["cs_registry"].keys()),
            #     # ids)) == 0:
            #     self.ls)) > 0:
            #     self.log("left overlap caught, rejecting CSWait attempt")
            #     self.exception = True
            #     return
            else:
                self.log("making new cs")
                #######################

                # self.blackboard["volatile"]["cs_set"].update(ls)

                # we use the 'identifier' in cs_set because
                # for now, CSWaits must be non-overlapping
                # as in, 2 CSWaits will never share any lefts
                # and, you can only dispatch a CSWaits of *exactly* the same lefts
                self.blackboard["volatile"]["cs_set"].update([identifier])

                self.cs = CompositeSemaphore(ls)

                for li in ls:
                    # all the lefts point to the same cs
                    self.blackboard["volatile"]["cs_registry"][li] = self.cs

        #######################

        # tell cs_cv waits this cs mouth is open
        with self.blackboard["volatile"]["cs_cv_l"]:
            self.blackboard["volatile"]["cs_cv"].notify_all()

        self.log("{} cs_cv notified".format(
            self.blackboard["volatile"]["cs_set"]))

        #######################

        self.prior_cb(args)

        self.instance = args[2:]

        self.log("{} cs init + acquiring".format(
            identifier))

        # this is the core mechanism
        self.cs.acquire(
            self.instance,
            # separate from what ie release'd, left and right are totally different
            self.mutable_shared
        )

    def cleanup(self):
        self.log("cleaning up {}".format(self.ls))
        with self.blackboard["volatile"]["cs_registry_l"] and self.blackboard["volatile"]["cs_cv_l"]:
            for l in self.ls:
                if l in self.blackboard["volatile"]["cs_registry"]:
                    cs = self.blackboard["volatile"]["cs_registry"].pop(l)
                    del cs

                # self.log("popping cs_set key {}".format(l))
                # self.blackboard["volatile"]["cs_set"].remove(
                #     l)

            # we use the 'identifier' in cs_set because
            # for now, CSWaits must be non-overlapping
            # as in, 2 CSWaits will never share any lefts
            # and, you can only dispatch a CSWaits of *exactly* the same lefts
            if self.identifier in self.blackboard["volatile"]["cs_set"]:
                self.blackboard["volatile"]["cs_set"].remove(
                    self.identifier)

            self.log("after {}, cs_set {}".format(
                self.blackboard["volatile"]["cs_registry"].keys(),
                self.blackboard["volatile"]["cs_set"])
            )

    def finish(self, event_dispatch, *args, **kwargs):
        # if self.exception:
        #     self.log("noop")
        #     return

        self.cleanup()

        if self.mutable_shared["status"] == -1:
            self.log("CSWait noop")
            return

        pending = self.get_pending(args)
        self.log(
            "CSWait unblocking {} on {}".format(
            self.mutable_shared["status"],
            pending))

        self.post_cb(args)

        self.blackboard[event_dispatch.cv_name].acquire()
        self.blackboard[event_dispatch.queue_name].append(
            list(pending)
        )
        self.blackboard[event_dispatch.cv_name].notify(1)
        self.blackboard[event_dispatch.cv_name].release()

        self.log("CSWait done!")

class CSRelease(CommonEvent):
    debug_color = bcolors.MAGENTA

    def get_release_status(self, args):
        '''
        override for your use case
        '''
        self.log("releasing on {}, {}".format(args[0], args[2]))
        return int(args[2])

    def prior_cb(self, args):
        '''
        override for your use case
        '''
        if len(args) != (2+1):
            self.log("ARGS {}".format(len(args)))
            return False

        return True

    def dispatch(self, event_dispatch, *args, **kwargs):
        if not self.prior_cb(args):
            return

        ls, identifier = CSWait.parse_lefts(args[0])

        with self.blackboard["volatile"]["cs_registry_l"]:
            for l in ls:
                if l not in self.blackboard["volatile"]["cs_registry"]:
                    continue
                self.blackboard["volatile"]["cs_registry"][l].release(
                    l,
                    (self.instance, self.get_release_status(args)))

        self.log("CSRelease dispatch done!")

    def finish(self, event_dispatch, *args, **kwargs):
        pass

#######################################

class CSBQCVED(BlackboardQueueCVED):
    '''
    Of all the events flowing through
    CS* events will be dispatched prior to any
    of its peers
    '''
    def register_blackboard_assets(self, blackboard, name):
        super(CSBQCVED, self).register_blackboard_assets(
            blackboard, name)

        blackboard["volatile"] = {}

        # every left token is mapped to a CS through cs_registry
        blackboard["volatile"]["cs_registry_l"] = threading.Lock()
        blackboard["volatile"]["cs_registry"] = {}

        # the set of unique left tokens
        blackboard["volatile"]["cs_set"] = set()

        # cs_set is signaled via cs_cv
        blackboard["volatile"]["cs_cv_l"] = threading.Lock()
        blackboard["volatile"]["cs_cv"] = threading.Condition(
            blackboard["volatile"]["cs_cv_l"])

    def prior_cb(self, blackboard):
        '''
        avoid overriding this
        '''
        self.log("CSBQCVED: prior_cb")

        cs_instances = []
        expected_cs_ids = set()
        non_cs_instances = []
        for instance in blackboard[self.queue_name]:
            if instance[0] in ["CSWait"]: # CSRelease, we only demand open-the-mouth on CSWait, CSRelease we don't care
                ids, identifier = CSWait.parse_lefts(instance[1])
                self.log("instance[1] {}, identifier: {}".format(instance[1], identifier))

                # reject overlap at the dispatch level
                # instead of in event
                with blackboard["volatile"]["cs_registry_l"] and blackboard["volatile"]["cs_cv_l"]:
                    if identifier in self.blackboard["volatile"]["cs_set"]:
                        cs_instances.append(instance)
                    elif len(set.intersection(
                        set(blackboard["volatile"]["cs_registry"].keys()),
                        # ids)) == 0:
                        ids)) > 0:
                        self.log("left overlap caught, rejecting CSWait attempt")
                    else:
                        cs_instances.append(instance)

                # expected_cs_ids.update(ids)

                # we use the 'identifier' in cs_set because
                # for now, CSWaits must be non-overlapping
                # as in, 2 CSWaits will never share any lefts
                # and, you can only dispatch a CSWaits of *exactly* the same lefts
                expected_cs_ids.update([identifier])
            else:
                non_cs_instances.append(instance)

        self.log("CS_INSTANCES {}!!!!!".format(cs_instances))
        self.log("non_cs_instances {}!!!!!".format(non_cs_instances))

        blackboard[self.queue_name] = non_cs_instances

        if len(cs_instances) == 0:
            self.log("prior_cb DONE!!!!")
            return

        for cs_instance in cs_instances:
            self.do_dispatch(blackboard, cs_instance)

        self.log("expected_cs_ids {}!!!!!".format(expected_cs_ids))
        if len(expected_cs_ids) > 0:
            self.blackboard["volatile"]["cs_cv_l"].acquire()
            while len(set.intersection(
                self.blackboard["volatile"]["cs_set"],
                # ids)) == 0:
                expected_cs_ids)) < len(expected_cs_ids):
                self.blackboard["volatile"]["cs_cv"].wait()
            self.blackboard["volatile"]["cs_cv_l"].release()

        self.log("prior_cb DONE!!!!")

    def post_cb(self, blackboard):
        '''
        override for your use case
        '''
        self.log("POST_CB!")

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