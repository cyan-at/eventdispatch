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
```

## Event

```python
>>> import lumache
>>> lumache.get_random_ingredients()
['shells', 'gorgonzola', 'parsley']
```

## EventDispatch

```python
>>> import lumache
>>> lumache.get_random_ingredients()
['shells', 'gorgonzola', 'parsley']
```

## bqcved

```python
>>> import lumache
>>> lumache.get_random_ingredients()
['shells', 'gorgonzola', 'parsley']
```


