# Classes

## Actors

'Actors' is a generic term for system threads/processes/components performing *continuous-time* activities. Components with some internal 'while' loop, some physical transducer, or UI process.

They produce and consume events via some inter-process-communication (IPC) carrier (ROS, TCP, UDP, shared memory, etc.)

## Blackboard

Define `Event` subclasses as `<Event name>`:`Event type` pairs in this dictionary

```python
class Blackboard(dict):
	'''
	a thread-safe dictionary
	with a mechanism to notify whenever a key is set
	'''
 	def __init__(self, *args, **kwargs):
 		'''
 		vanilla + mutex
 		'''

 	def __setitem__(self, key, value):
 		'''
 		vanilla, plus mutex
 		'''

    def __getitem__(self, key):
        '''
        vanilla, plus mutex
        '''

    def __delitem__(self, key):
        '''
        vanilla, plus mutex
        '''
```

## EventThread

```python
class EventThread(threading.Thread):
    '''
    a thread, with callback, oneshot, delay, terminate additions
    '''
    def __init__(self,
        callback = None,
        oneshot = True,
        delay_secs = None,
        *args, **kwargs):
        '''
        a thread, with callback, oneshot, delay, terminate additions
        '''

    def terminate(self):
        '''
        cooperative support
        '''

    def stopped(self):
        '''
        cooperative support
        '''

    def run(self):
        '''
        a wrapper around base class's run
        '''
```

## Event

```python
class Event(object):
    '''
    an interface / abstract-base-class
    child classes must override deserialize, dispatch, and finish
    '''

    def __init__(self, event_id, *args, **kwargs):
        '''
        constructor
        '''

    def get_id(self):
        '''
        every event has an id, internal to this dispatch instance
        '''

    @staticmethod
    def deserialize(ed, blackboard, *args, **kwargs):
        '''
        Child Event types MUST override
        It defines how an array is deserialized into an Event instance
        '''

    def dispatch(self, event_dispatch, *args, **kwargs):
        '''
        Child Event types MUST override

        Consider this function as
        'injecting' drift and uncertainty into the system
        '''

    def finish(self, event_dispatch, *args, **kwargs):
        '''
        Child Event types MUST override

        Consider this function as
        'injecting' control into the system
        '''
```

## EventDispatch

```python
class EventDispatch(object):
    def __init__(self, blackboard = None : dict, ed_id = None : str):
        '''
        constructor
        '''

    def reserve_event_id(self):
        '''
        at any one time, event ids must be unique / no collisions
        '''

    def release_event_id(self, event_id):
        '''
        event id hygiene
        '''

    def dispatch(self, event, *args, **kwargs):
        '''
        CORE function 1: spawn a thread with a constructed event
        '''

    def dispatch_finish(self, event, *args, **kwargs):
        '''
        CORE function 2: call an event's finish method
        and hygiene
        '''
```

## BlackboardQueueCVED

This lives outside the `core` in `common1`, but provides a component you can add in your python program.

0. Define your `Event`s, `Actor`s classes
1. Create `Blackboard` instance(s)
2. Populate the `Blackboard` with `Event` declarations (name : type pairs)
3. Create `BlackboardQueueCVED` instance(s) with their individual `name` strings
4. Stand up their `run` targets as threads, stand up your `Actor`s
5. Best practice (thread hygiene): on program shutdown, notify the `BlackboardQueueCVED` cvs and join their `run` threads

Please see <a href="https://github.com/cyan-at/eventdispatch/blob/main/python3/eventdispatch/eventdispatch/example1.py" target="_blank">example1</a> program for reference

```python
class BlackboardQueueCVED(EventDispatch):
    def __init__(self, blackboard, name):
        '''
        constructor
        '''

    def prior_cb(self, blackboard):
        '''
        before draining any events in the queue, call this

        override this in CSBQCVED, for your use case
        '''

    def post_cb(self, blackboard):
        '''
        after draining all events in the queue, call this
        '''

    def register_blackboard_assets(self, blackboard, name):
        '''
        populate a blackboard with this dispatch's supporting data
        heartbeat
        mutex
        queue
        condition variable
        etc.
        '''

    def log(self, msg, params = None):
        '''
        supporting log function
        '''

    def reserve_event_id(self):
        '''
        return a event_id for a new event, override
        '''

    def release_event_id(self, event_id):
        '''
        free event_id
        override your use case
        '''

    def do_dispatch(self, blackboard, serialized_class_args):
        '''
        stubbed out to support CSBQCVED

        avoid overriding this
        '''

    def run(self, blackboard, # expected, dict
        prefix, # expected, str
        empty_cv_name = None, # expected, str
        debug_color = None):
        '''
        main thread target
        the empty_cv_name, if given, will be notified
        whenever the queue is drained

        to 'dispatch' an event
        0. make sure the 'EventName' : EventClass is a pair in the Blackboard
        1. append ['EventName', 'arg1', arg2...] on this Dispatch's queue
        2. notify the dispatch's cv
        '''
``` 

## CompositeSemaphore

While a n-semaphore doesn't maintain distinction of what 'release's it, this class distinguishes between `left` signals

In addition, this class supports *multiple simultaneous* Events `acquire`ing it. And when they can finally acquire, they have metadata in `mutable_shared` in case that acquire was unblocked from various left activity (success, failure, timeout, etc.)

Please see <a href="https://github.com/cyan-at/eventdispatch/blob/main/python3/eventdispatch/eventdispatch/composite_semaphore.py" target="_blank">composite_semaphore</a> program for reference

```python
class CompositeSemaphore(object):
    def add_left(self, k)

    def clear_left(self, k)

    def wraparound_idempotent_increment(
        self, k, identifier=None)

    def release(self, k, identifier=None)

    def acquire(self, identifier, mutable_shared)
``` 

## CSWait

This Event subclass bookkeeps, in a `cs_set`, `cs_registry` and finds or constructs a `CompositeSemaphore`, and acquires on it.

It also exposes some callbacks to override for your usecase

```python
class CSWait(CommonEvent):
    def prior_cb(self, args)
        '''
        override for your use case
        '''

    def get_pending(self, args)
        '''
        override for your use case
        '''

    def post_cb(self, args)
        '''
        override for your use case
        '''

    @staticmethod
    def parse_lefts(s)

    def dispatch(self, event_dispatch, *args, **kwargs)

    def cleanup(self)

    def finish(self, event_dispatch, *args, **kwargs)
``` 

## CSRelease

This Event subclass bookkeeps, finds any `CompositeSemaphore`s in `cs_registry` and releases on them

It also exposes some callbacks to override for your usecase

```python
class CSRelease(CommonEvent):
    def get_release_status(self, args)
        '''
        override for your use case
        '''

    def prior_cb(self, args)
        '''
        override for your use case
        '''

    def dispatch(self, event_dispatch, *args, **kwargs)

    def finish(self, event_dispatch, *args, **kwargs)
``` 

## CSBQCVED

The core part of this class are the `register_blackboard_assets` and `prior_cb` functions. It is recommended you do NOT override these

* `register_blackboard_assets`
    - This function adds things to the blackboard that the CS* mechanism needs

* `prior_cb`
    - Of all the event batches flowing through this Dispatch, it treats `CSWait`s above the rest.
    - It makes sure `CSWait`s are dispatched and their `CompositeSemaphores` are in place before all other events are dispatched

```python
class CSBQCVED(BlackboardQueueCVED):

    def register_blackboard_assets(self, blackboard, name)

    def prior_cb(self, blackboard)
        '''
        avoid overriding this
        '''

    def post_cb(self, blackboard)
        '''
        override for your use case
        '''
``` 