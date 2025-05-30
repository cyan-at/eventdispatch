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

This lives outside the `core`, but provides a component you can add in your python program.

0. Define your `Event`s, `Actor` classes
1. Create `Blackboard` instance(s)
2. Populate the `Blackboard` with `Event` declarations (name : type pairs)
3. Create `BlackboardQueueCVED` instance(s) with their individual `name` strings
4. Stand up their `run` targets as threads, stand up your `Actor`s
5. Best practice (thread hygiene): on program shutdown, notify the `BlackboardQueueCVED` cvs and join their `run` threads

Please see <a href="https://github.com/cyan-at/eventdispatch/blob/main/python3/eventdispatch/example1.py" target="_blank">example1</a> program for reference

```python
class BlackboardQueueCVED(EventDispatch):
    def __init__(self, blackboard, name):
        '''
        constructor
        '''

    def prior_cb(self, blackboard):
        '''
        before draining any events in the queue, call this
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