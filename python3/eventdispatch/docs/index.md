# [python3-eventdispatch 0.1](https://github.com/cyan-at/eventdispatch)

**eventdispatch** is a Python package for solving the *discrete time synchronization problem* in any computer system. It consists of:

1. A **core** python module, containing the following classes:
    1. **[Blackboard](classes.md#blackboard)**, a thread safe dictionary
    2. **[EventThread](classes.md#eventthread)**, a thread subclass
    3. **[Event](classes.md#event)**, the abstract base class to override
        * Your use case can be decomposed down to `EventDispatch` and `Event` child classes
    4. **[EventDispatch](classes.md#eventdispatch)**, which defines core mechanism functions
    5. Various other decorators, helper functions
2. A **common1** python module, with:
    1. **[BlackboardQueueCVED](classes.md#blackboardqueuecved)**, a example Dispatch subclass that ties the above together
        * You are encouraged to subclass and override or create your own `EventDispatch` child class
    2. A `CommonEvent` class, with some useful, but not necessary logic
    3. Various other decorators, helper functions
3. A <a href="https://github.com/cyan-at/eventdispatch/blob/main/python3/eventdispatch/eventdispatch/example1.py" target="_blank">example1</a> python program, you can run after installing via command line: `eventdispatch_example1`

---

* EventDispatch is based on the idea that **what happens defines what happens *next***. Independently derived, the idea is a mirror of <a href="https://en.wikipedia.org/wiki/Markov_chain">Markov chains</a>.
    * EventDispatch frames *all computer programs as superpositioned Markov processes*.
    * Control in this architecture is not an external actor taming a plant, but a collective of Markov state transitions, *coexisting* alongside *drift* and *stochasticity*.

* Other synchronization architectures exist such as <a href="https://en.wikipedia.org/wiki/Behavior_tree_(artificial_intelligence,_robotics_and_control)" target="_blank">behavior trees</a> and <a href="https://en.wikipedia.org/wiki/Finite-state_machine" target="_blank">state machines</a>.
* Compared to those architectures, **eventdispatch** is *thin*, *scalable*, inherently *concurrent*.
    * The number of events active in memory in a system using **EventDispatch** is theoretically limited by the CPU's thread limit.
    * The number of **Events** *defined/declared/dispatchable* in such a system theoretically limited by the machine's runtime memory limit.
    * *Dispatch* is a **verb**, not a **noun**. Within a system, more than one component can *dispatch events*.
    * **Events** do not impose any meta-language on the practioner, within the 3 interface functions you are free to write in the *native* language. It remains trivial to express complex behaviours.
* EventDispatch is a mechanism from robotics. However, it is relevant to any system that faces *volatility* in what is asked of it (the right), and *uncertainty* in what it asks of others (the left).  See [Usage patterns & best practices](usage.md).

---

The **EventDispatch** mechanism can be extended to a variety of *messaging mechanisms* in their respective packages, their documentations listed here:

1. [ROS2](https://eventdispatch-ros2.readthedocs.io/en/latest/)

---

For any new messaging mechanism integrations or use case ideas, <a href="mailto:cyanatg@gmail.com">email me!</a>