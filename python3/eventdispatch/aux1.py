'''
Created on 2025-05-23

@author: Charlie Yan

Copyright (c) 2025, Charlie Yan
License: Apache-2.0 (see LICENSE for details)
'''
from .core import *

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

class CommonEvent(Event):
    debug_color = bcolors.LIGHTCYAN

    def __init__(self, event_id, *args, **kwargs):
        super(CommonEvent, self).__init__(
            event_id, *args, **kwargs)
        self._exception = False
        self.blackboard = args[0]
        self.instance = ""

        wrap_instance_method(self, 'log',
            wrap_with_prints(self.debug_color, bcolors.ENDC))

    def log(self, *args):
        print(*args)

    @staticmethod
    def deserialize(ed, blackboard, *args, **kwargs):
        tokens = args[0]
        # ed.log("TOKENS! {}".format(tokens))
        if len(tokens) < 1:
            raise Exception("not enough tokens", len(tokens))

        return (ed.reserve_event_id(), blackboard), tuple(tokens)

class BlackboardQueueCVED(EventDispatch):
    def __init__(self, blackboard, name):
        super(BlackboardQueueCVED, self).__init__(
            blackboard, name + "_dispatch")

        self.register_blackboard_assets(
            blackboard, name)

        self.event_id_max = 0

    def prior_cb(self, blackboard):
        pass

    def post_cb(self, blackboard):
        self.log("post_cb!!! {}".format(len(blackboard[self.queue_name])))

    def register_blackboard_assets(self, blackboard, name):
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

    def log(self, msg, params = None):
        print(msg)

    def reserve_event_id(self):
        x = self.event_id_max
        self.event_id_max = (self.event_id_max + 1) % (30000)
        return x

    def release_event_id(self, event_id):
        pass

    def run(self, blackboard, # expected, dict
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
            while len(blackboard[self.queue_name]) > 0: # buffer and [drain]
                serialized_class_args = blackboard[self.queue_name].pop(0)

                # s (serialized_event) expected to be
                # array of [<class>, args]
                if len(serialized_class_args) == 0:
                    continue

                # deserialize & dispatch
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

