# [python3-eventdispatch 0.1](https://github.com/cyan-at/eventdispatch)

**eventdispatch** is a Python package for solving the *discrete time synchronization problem* in any computer system. It consists of:

1. A **core** python module, containing the following classes:
    1. **[Blackboard](classes.md#blackboard)**, a thread safe dictionary
    2. **[EventThread](classes.md#eventthread)**, a thread subclass
    3. **[Event](classes.md#event)**, the abstract base class to override
        * Your use case can be decomposed down to `Actors` and `Event` child classes
    4. **[EventDispatch](classes.md#eventdispatch)**, which defines core mechanism functions
    5. Various other decorators, helper functions
2. A **aux1** python module, with:
    1. **[BlackboardQueueCVED](classes.md#blackboardqueuecved)**, a example Dispatch subclass that ties the above together
        * You are encouraged to subclass and override or create your own `EventDispatch` child class
    2. A `CommonEvent` class, with some useful, but not necessary logic
    3. Various other decorators, helper functions
3. A <a href="https://github.com/cyan-at/eventdispatch/blob/main/python3/eventdispatch/eventdispatch/example1.py" target="_blank">example1</a> python program, you can run after installing via command line: `eventdispatch_example1`

---

* Other synchronization architectures exist such as <a href="https://en.wikipedia.org/wiki/Behavior_tree_(artificial_intelligence,_robotics_and_control)" target="_blank">behavior trees</a> and <a href="https://en.wikipedia.org/wiki/Finite-state_machine" target="_blank">state machines</a>.
* Compared to those architectures, **eventdispatch** is *thin*, *scalable*, inherently *concurrent*. **Safety** and **hygiene** are first-order considerations.
    * The number of events active in memory in a system using **EventDispatch** is theoretically limited by the CPU's thread limit.
    * The number of **Events** *defined/declared/dispatchable* in such a system theoretically limited by the machine's runtime memory limit.
    * *Dispatch* is a **verb**, not a **noun**. Within a system, more than one component can *dispatch events*.
* Though inspired from robotics systems, this framework is relevant to any system that deals with *uncertainty* and *volatility*. See [Usage patterns & best practices](usage.md).
