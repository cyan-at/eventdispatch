# Classes

## Actors

'Actors' is a generic term for system threads/processes/components performing *continuous-time* activities. Components with some internal 'while' loop, some physical transducer, or UI process.

They produce and consume events via some inter-process-communication (IPC) carrier (ROS, TCP, UDP, shared memory, etc.)

## Blackboard

```python
class Blackboard(dict):
	'''
	a thread-safe dictionary
	with a mechanism to notify whenever a key is set
	'''
 	def __init__(self, *args, **kwargs):
 		'''
 		vanilla
 		'''

 	def __setitem__(self, key, value):
 		'''
 		vanilla, plus notify mechanism
 		'''

 	def release_cv(self, key):
 		'''
 		unsubscribe a condition_var (cv)
 		'''

 	def register_payload(self, payload, match_target = None):
 		'''
 		subscribe a cv
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
        '''
```