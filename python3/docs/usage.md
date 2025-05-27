Best practices
=====

* Events should only exist *as needed*.
* Events should be *short-lived*, relying on [actors](classes#actors) to focus on *continuous time* tasks.
* Events should be as **state-less** as possible, instead relying on [blackboard](classes#blackboard)s to store state.
* Keep your Event definitions DRY, push as much variance into arguments.
* Whenever possible, decompose your use case to the [event](classes#event) level, not further to the [dispatch](classes#dispatch) level unless absolutely necessary.

Patterns
=====

* To deal with *temporal uncertainty*, sibling threads are dispatched together, and whichever finishes first, *interrupts / kills* sibling events.
* To deal with *spatial* uncertainty, Event(s) most collocated to that uncertainty deal with it immediately in their `finish` functions, or downstream dispatched events infer from blackboard state
* Events have read/write access to the dispatch, and can suspend/resume/alter the way all events are dispatched through this access. Safety implementations rely on this mechanism.

* The rate that events fire in the system can be very *bursty*. In one minute, no events will fire, and in the next, *hundreds*. Two patterns help prevent event / data traffic loss:
	* 'Open-the-mouth-before-you-feed-it' : For example, make sure any `condition_variable` is waited upon before you notify it.
	* 'Buffer-and-drain' : Producers populate some buffer, and whoever reads it, drains it completely every time.

Example Use Cases
=====
(TODO)