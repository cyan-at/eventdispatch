# Usage

## Best practices

* Events should only exist *as needed*.
* Events should be *short-lived*, relying on [actors](classes.md#actors) to focus on *continuous time* tasks.
* Events should be as **state-less** as possible, instead relying on [blackboard](classes.md#blackboard)s to store state.
* Keep your Event definitions DRY, push as much variance into arguments.
* Think in terms of 'levels': decompose your use case to the [event](classes.md#event) level, and *mechanism* level changes belong in the 'lower' [dispatch](classes.md#eventdispatch) level.
* Instead of thinking *before* and *after*, think in terms of **left** and **right**. What is to the **left** of an Event? What is to the **right** of it?

## Patterns

* To deal with *temporal uncertainty*, sibling threads are dispatched together, and whichever finishes first, *interrupts / kills* sibling events.
* To deal with *spatial* uncertainty, Event(s) most collocated to that uncertainty deal with it immediately in their `finish` functions, or downstream dispatched events infer from blackboard state
* Events have read/write access to the dispatch, and can suspend/resume/alter the way all events are dispatched through this access. Practioners are encouraged to implement **safety** behavior through this axis.

* The rate that events fire in the system can be very *bursty*. In one minute, no events will fire, and in the next, *hundreds*. Two patterns help prevent event / data traffic loss:
	* 'Open-the-mouth-before-you-feed-it' : For example, make sure any `condition_variable` is waited upon before you notify it.
	* 'Buffer-and-drain' : Producers populate some buffer, and whoever reads it, drains it completely every time.

* To deal with *volatility* in connections between Events, consider using `CSWait`+`CSRelease` in a `CSBQCVED` dispatch.

## Example Use Cases

1. See <a href="https://github.com/cyan-at/eventdispatch/blob/main/python3/eventdispatch/eventdispatch/example1.py" target="_blank">example1</a>
1. See <a href="https://github.com/cyan-at/eventdispatch/blob/main/python3/eventdispatch/eventdispatch/example2.py" target="_blank">example2</a>

---
**LEMMA**

Because computers control **synchronization**, they implement *differential equations* of the standard form \(\dot{x} = f(x) + b(u) + g(w)\), the terms being:

* Drift \(f(x)\)
* Diffusion \(g(w)\)
* Control \(b(u)\)

Geometrically you can see computers existing in a *n-dimensional* [phase portrait](https://en.wikipedia.org/wiki/Phase_portrait) where [actors](classes.md#actors) and the *full system* propagate the system across an *n-dimensional state vector* \(x\)

Systems *co-locate* the state vector \(x\) with the relevant eventdispatch(s), which manage and invoke **drift** and **control**. It follows that all eventdispatch systems are **n-dimensional nonlinear controllers**

Events explicitly define \(f(x)\) and \(b(u)\)

Introducing \(f(x)\) and \(b(u)\) into a system *always* introduces some magnitude of \(g(w)\)

Often (consider [SGD](https://en.wikipedia.org/wiki/Stochastic_gradient_descent), or dithering) this kind of **uncertainty** is **necessary**, injecting noise is **intentional**

There is **no guarantee of stability nor optimality**, that is left to the implementation

---

---
**NOTE**

Because this framework relies on python's `threading` library, the *exact ordering* of things is not always deterministic, especially at the micro / high-traffic levels.

Implementation must be careful about **race conditions** and consider the lower level OS / kernel scheduling implications.

Practioners are encouraged to be familiar with threading / operating-system cs course concepts

---