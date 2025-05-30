# [python3-eventdispatch 0.1](https://github.com/cyan-at/eventdispatch)

**eventdispatch** is a Python package for solving the *discrete time synchronization problem* in any computer system. It consists of:

1. A **core** python module, containing the following classes:
    1. **[Blackboard](classes.md#blackboard)**, a thread safe dictionary
    2. **[EventThread](classes.md#eventthread)**, a thread subclass
    3. **[Event](classes.md#event)**, the abstract base class to override
    4. **[EventDispatch](classes.md#eventdispatch)**, which defines core mechanism functions
    5. Various other decorators, helper functions
2. A **aux1** python module, with:
    1. **[BlackboardQueueCVED](classes.md#blackboardqueuecved)**, a example Dispatch subclass that ties the above together
    2. Various other decorators, helper functions
3. **example1** python program

---

* Other synchronization architectures exist such as <a href="https://en.wikipedia.org/wiki/Behavior_tree_(artificial_intelligence,_robotics_and_control)" target="_blank">behavior trees</a> and <a href="https://en.wikipedia.org/wiki/Finite-state_machine" target="_blank">state machines</a>.
* Compared to those architectures, **eventdispatch** is *thin*, *scalable*, inherently *concurrent* and *performant*. **Safety** and **hygiene** are first-order considerations.

* Though inspired from robotics systems, this framework is relevant to the spatial and temporal *uncertainty* in simple and complex systems, and the *volatility* of what is asked of such systems. See [Usage patterns & best practices](usage.md).

* *Dispatch* is a **verb**, not a **noun**. Within a system, more than one component can *dispatch events*.