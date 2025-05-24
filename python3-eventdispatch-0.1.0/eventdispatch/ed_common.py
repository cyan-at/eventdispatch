from __future__ import print_function

import sys, os, time

def python2_makedirs_wrapper(path):
  try:
    os.makedirs(path)
  except OSError as e:
    if e.errno != errno.EEXIST:
      raise

def python3_makedirs_wrapper(path):
  os.makedirs(
      path,
      exist_ok=True)

PYTHON2 = False
makedirs_wrapper = python3_makedirs_wrapper
if sys.version_info.major == 2:
  PYTHON2 = True
  import errno
  makedirs_wrapper = python2_makedirs_wrapper

import threading, collections
from threading import Condition, Lock, Thread

class bcolors:
    # https://godoc.org/github.com/whitedevops/colors
    DEFAULT = "\033[39m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    LGRAY = "\033[37m"
    DARKGRAY = "\033[90m"
    FAIL = "\033[91m"
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    OKBLUE = '\033[94m'
    HEADER = '\033[95m'
    LIGHTCYAN = '\033[96m'
    WHITE = "\033[97m"

    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = "\033[2m"
    UNDERLINE = '\033[4m'
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"

    BG_DEFAULT = "\033[49m"
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_GRAY = "\033[47m"
    BG_DKGRAY = "\033[100m"
    BG_LRED = "\033[101m"
    BG_LGREEN = "\033[102m"
    BG_LYELLOW = "\033[103m"
    BG_LBLUE = "\033[104m"
    BG_LMAGENTA = "\033[105m"
    BG_LCYAN = "\033[106m"
    BG_WHITE = "\033[107m"

def nonempty_queue_exists(
  blackboard,
  admissible_nonempty_keys,
  verbose = False):
  for k in blackboard.keys():
    if k[-6:] == "_queue":
      mutex_k = k[:-6] + "_mutex"
      blackboard[mutex_k].acquire()
      queue_size = len(blackboard[k])
      blackboard[mutex_k].release()
      if verbose:
        print("%s queue_size %d" % (k, queue_size))
        print(blackboard[k])
      if queue_size > 0:
        if verbose:
          print("nonempty k: ", k, queue_size)
        if k not in admissible_nonempty_keys:
          return True
  return False

def wrap_instance_method(instance, method_name, wrapper_with_args):
  wrapped_method = wrapper_with_args(getattr(instance, method_name))
  setattr(instance, method_name, wrapped_method)

def call_when_switch_turned_on(obj, switch, switch_lock):
    def decorator(func):  # func should return void
        def wrapper(*args, **kwargs):
            lock_obj = getattr(obj, switch_lock)
            lock_obj.acquire()  # optionally, non-blocking acquire
            switch_state = getattr(obj, switch)
            if (not switch_state):  # tells you lock state @ this call, it may be released immediately after
                lock_obj.release() # 2019-01-09 SUPER #IMPORTANT
                raise Exception("call_when_switch_turned_on: off, doing nothing")
            res = func(*args, **kwargs)
            lock_obj.release()
            return res
        return wrapper
    return decorator

def wrap_with_prints(pre_msg, post_msg):
  '''useful for for example printing with color'''
  def decorator(func):
    def wrapper(*args, **kwargs):
      print(pre_msg, end="")
      res = func(*args, **kwargs)
      print(post_msg, end="")
      return res
    return wrapper
  return decorator

def call_with_threading_lock(lock_obj):
    def decorator(func):  # func should return void
        def wrapper(*args, **kwargs):
            '''
            if (lock_obj.locked()):  # tells you lock state @ this call, it may be released immediately after
                # 01/08/2019 Sander - Commented this because it was spamming the terminal
                # print bcolors.FAIL + "call_with_threading_lock: locked, doing nothing" + bcolors.ENDC
                return None
            lock_obj.acquire()  # optionally, non-blocking acquire
            res = func(*args, **kwargs)
            if lock_obj.locked():
                lock_obj.release()
            '''
            with lock_obj:
              res = func(*args, **kwargs)
            return res
        return wrapper
    return decorator

class EventThread(threading.Thread):
  """Thread class with a stop() method. The thread itself has to check
  regularly for the stopped() condition."""

  def __init__(self,
    callback = None,
    oneshot = True,
    delay_secs = None,
    *args, **kwargs):
    super(EventThread, self).__init__(*args, **kwargs)
    self.callback = callback
    self.oneshot = oneshot
    self.delay_secs = delay_secs

    # IMPORTANT, threading library
    # wants to call a function _stop()
    # so we must name this to not override that
    self._stop_event = threading.Event()

  def terminate(self):
    self._stop_event.set()

  def stopped(self):
    return self._stop_event.isSet()

  def run(self):
    # print "starting up stoppable thread"
    if self.delay_secs is not None:
      time.sleep(self.delay_secs)
    super(EventThread, self).run()
    if self.oneshot:
      self.terminate()
    if self.callback:
      self.callback()

class Event(object):
  def __init__(self, event_id, *args, **kwargs):
    self.event_id = event_id
    # note: on construction, does NOT have/need a blackboard
    # when dispatched, it MAY have a blackboard (access to actors)
    self.blackboard = None

    # note: on construction, does NOT have/need an ED
    # when dispatched, it MUST have an ED (access to dispatch, events)
    self.event_dispatch = None
    # not fixed, can be changed across different dispatches

  # methods for the child to override
  def get_id(self):
    # return self.__class__.__name__ + "@" + str(self.event_id)
    return self.event_id

  @staticmethod
  def deserialize(ed, blackboard, *args, **kwargs):
    # up to the Event class to define
    # returns 2 tuples, constructor_args, dispatch_args
    # unlike dispatch / finish, involves no instance
    raise NotImplementedError

  def dispatch(self, event_dispatch, *args, **kwargs):
    # CAN EITHER PASS IN ARGS OR KWARGS HERE
    # OR SET THEM IN CONSTRUCTOR
    # OR SET THEM IN THE BLACKBOARD
    # unlike deserialize / finish, happens in its own thread
    if self.get_id() not in event_dispatch.mutex_registry:
      # when dispatched, it MUST have an ED (access to dispatch, events)
      self.event_dispatch = event_dispatch

      # dynamic registration in ED mutex_registry
      # will let OTHER events block on this event's state
      # ex:
      # event_dispatch.mutex_registry[self.get_id()] = Lock()

      # when dispatched, it MAY have a blackboard (access to actors)
      # ex:
      # self.blackboard = args[0]

  def finish(self, event_dispatch, *args, **kwargs):
    # unlike deserialize / dispatch, involves other events

    # BEST PRACTICE:
    # you should deal with OUTCOMES here
    # do risky / uncertain stuff inside dispatch
    # and deal with the outcomes here
    raise NotImplementedError

class EventDispatch(object):
  def __init__(self, blackboard = None, ed_id = None):
    self.thread_registry = {}
    self.event_id_pool = set()
    self.event_id_pool_all = set()
    self.mutex_registry = {}

    self.dispatch_mutex = threading.Lock()
    self.dispatch_switch_mutex = threading.Lock()
    self.dispatch_switch = True
    wrap_instance_method(self, 'dispatch',
      call_when_switch_turned_on(
        self, "dispatch_switch",
        "dispatch_switch_mutex")) # [example] decorator
    # safety mechanism:
    # if any event sets the switch off
    # no other events are dispatched
    # until the switch is cleared

    if (blackboard is not None and ed_id is not None):
      # give an ED a blackboard on which other EDs live
      # for when there is no ROS infrastructure for example
      self.blackboard = blackboard
      self.ed_id = ed_id
      self.blackboard[ed_id] = self # register self on blackboard

  # something child ED class can override
  def reserve_event_id(self):
    print("reserve_event_id!", self.event_id_pool)
    if len(self.event_id_pool) > 0:
      return self.event_id_pool.pop()
    else:
      new_id = len(self.event_id_pool_all)
      self.event_id_pool_all.add(new_id)
      return new_id

  def release_event_id(self, event_id):
    # return event_id to pool
    self.event_id_pool.add(event_id)

  def dispatch(self, event, *args, **kwargs):
    with self.dispatch_mutex:
      # print("dispatching %s" % (event.get_id())) # debug
      self.thread_registry[event.get_id()] = EventThread(
        target=lambda args = args, kwargs = kwargs:\
          event.dispatch(self, *args, **kwargs),
        # note that the event is dispatched with a reference
        # to the event dispatch, giving access / control
        # over other events
        callback=lambda event = event, args = args, kwargs = kwargs:\
          self.dispatch_finish(event, *args, **kwargs))
    self.thread_registry[event.get_id()].start()

  def dispatch_finish(self, event, *args, **kwargs):
    with self.dispatch_mutex:
      event_id = event.get_id()
      self.thread_registry.pop(event_id, None)

    # self.log("finishing %s" % (event.get_id())) # debug
    event.finish(self, *args, **kwargs)
    # ONLY the event defines what is dispatched next
    # this includes multiple subsequent concurrent events

    self.release_event_id(event_id)

  def log(self, msg, params = None):
    # for children to override
    print(msg)

# 2018-01-11 often we spawn child threads but if they fail at any point
# the parent thread cannot know beyond a callback indirectly that the
# child succeeded, or failed cannot know at all
# this decorator is a tool against that and the notify_func_done, notify_func_fail
# is a way to more directly know that the func finished or failed explicitly
def watchdog_try_to_run_and_notify_failure(result_key,
  notify_func_done = None,
  notify_func_fail = None):
  def decorator(func):
    def wrapper(*args, **kwargs):
      try:
        func(*args, **kwargs)
        if notify_func_done is not None:
          notify_func_done(result_key, "done")
        # notify_func not only catches failures but more directly good outcomes
      except: # 2019-01-11 more generic Errors != Exceptions etc.
        print("failed trying something")
        if notify_func_fail is not None:
          notify_func_fail(result_key, sys.exc_info())
        # more directly catch failures
    return wrapper
  return decorator

class Blackboard(dict):
  def __init__(self, *args, **kwargs):
    self.mutex = Lock()
    self.store = dict()
    self.update(dict(*args, **kwargs))  # use the free update to set keys

    # free cvs
    self.cv_pool_lock = Lock()
    self.cv_pool = []
    self.cvs = {}

  def release_cv(self, key):
    print("RELEASING CV", key)
    with self.cv_pool_lock:
      if key not in self.cvs:
        print("RELEASING MISSING CV!", key)
      else:
        cv_set = self.cvs.pop(key)
        cv_set['count'] = 0
        cv_set.pop('match_target')
        self.cv_pool.append(cv_set)

  def register_payload(self, payload, match_target = None):
    with self.cv_pool_lock:
      if len(self.cv_pool) > 0:
        cv_set = self.cv_pool.pop(0)
      else:
        lock = threading.Lock()
        cv_set = {
          'l' : lock,
          'cv' : threading.Condition(lock),
          'count' : 0,
          'queue' : [],
          # pattern: if the mouth is not open before you feed it, using a queue is one solution
          # the other solution is to enforce the sync using some blocking logic
        }
      cv_set["match_target"] = match_target

      self.cvs[payload] = cv_set
    return cv_set

  # def __getitem__(self, key):
  #   return super().__getitem__(key)

  def __setitem__(self, key, value):
    super(Blackboard, self).__setitem__(key, value)
    if key in self.cvs:
      print("blackboard notifying",
        key,
        value)
      self.cvs[key]['queue'].append(value)
      with self.cvs[key]['l']:
          self.cvs[key]['cv'].notify_all()

  def __delitem__(self, key):
    super().__delitem__(key)

class BlackboardQueueCVED(EventDispatch):
  def __init__(self, blackboard, name):
    super(BlackboardQueueCVED, self).__init__(
      blackboard, name + "_dispatch")

    self.register_blackboard_assets(
      blackboard, name)

    self.event_id_max = 0

  def register_blackboard_assets(
    self, blackboard, name):
    self.name = name

    self.hb_key = name + "_hb"
    if self.hb_key not in blackboard:
      blackboard[self.hb_key] = True
    # assert(self.hb_key in blackboard)

    self.mutex_name = name + "_mutex"
    if self.mutex_name not in blackboard:
      # without creating one explicitly
      # condition has underlying mutex
      blackboard[self.mutex_name] = Lock()
    # assert(self.mutex_name in blackboard)

    self.cv_name = name + "_cv"
    if self.cv_name not in blackboard:
      blackboard[self.cv_name] = Condition(
        blackboard[self.mutex_name])
    # assert(self.cv_name in blackboard)

    self.queue_name = name + "_queue"
    if self.queue_name not in blackboard:
      blackboard[self.queue_name] = []
    # assert(self.queue_name in blackboard)

  def prior_cb(self, blackboard):
    pass

  def post_cb(self, blackboard):
    self.log("post_cb!!! {}".format(len(blackboard[self.queue_name])))

  def run(self,
    blackboard, # expected, dict
    prefix, # expected, str
    empty_cv_name = None, # expected, str
    debug_color = None):
    assert(blackboard is not None)

    if (debug_color is not None):
      wrap_instance_method(self, 'log',
        wrap_with_prints(debug_color, bcolors.ENDC))
      # [example] decorator

    while(blackboard[self.hb_key]):
      blackboard[self.mutex_name].acquire()
      # syntax in while bool expression (cv predicate) is key
      while blackboard[self.hb_key] and (
        len(blackboard[self.queue_name]) == 0):
        blackboard[self.cv_name].wait()
        # Wait until notified or until a timeout occurs.
        # If the calling thread has not acquired the lock
        # when this method is called,
        # a RuntimeError is raised.
        # add conditions (predicates) to protect
        # against spurious wakeups prior or after
        # condition is actually met
      blackboard[self.mutex_name].release()

      # could be woken from shutdown procedure
      if len(blackboard[self.queue_name]) == 0:
        self.log("woken from shutdown")
        break

      # for now, expose this so other types can override it
      # so we don't need to re-write the whole thing
      self.prior_cb(blackboard)

      ##### core ED logic ####################################
      while len(blackboard[self.queue_name]) > 0:
        serialized_class_args = blackboard[self.queue_name].pop(0)

        # s (serialized_event) expected to be
        # array of [<class>, args]
        if len(serialized_class_args) >= 1:
          # deserialize & dispatch
          # print("s[0]", s[0])
          try:
            constructor_args, dispatch_args = blackboard[
              serialized_class_args[0]].deserialize(
                self,
                blackboard,
                serialized_class_args[1:])
            # mechanism
            self.dispatch(
              blackboard[serialized_class_args[0]](
                *constructor_args),
              *dispatch_args)
          except Exception as e:
            self.log(self.ed_id
              + " failed dispatch %s, exception %s" % (
                str(serialized_class_args), str(e)))
      ########################################################

      self.post_cb(blackboard)

      # ED tries to 'cleanup'
      if empty_cv_name is not None:
        if len(blackboard[self.queue_name]) == 0 and\
          empty_cv_name in blackboard:
          self.log("notifying " + empty_cv_name)
          blackboard[empty_cv_name].acquire()
          blackboard[empty_cv_name].notify_all()
          blackboard[empty_cv_name].release()

    self.log(self.name + " shutdown")

  def log(self, msg, params = None):
    print(msg)

  def reserve_event_id(self):
    x = self.event_id_max
    self.event_id_max = (self.event_id_max + 1) % (30000)
    return x

  def release_event_id(self, event_id):
    pass
