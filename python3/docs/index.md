# [python3-eventdispatch 0.1.0](https://github.com/cyan-at/eventdispatch)

**eventdispatch** is a Python package for solving the *discrete time synchronization problem* in any computer system. It consists of:

1. A **core** python module, containing the following classes:
    1. **[Blackboard](classes.md#blackboard)**, a thread safe dictionary
    2. **[EventThread](classes.md#eventthread)**, a thread subclass
    3. **[Event](classes.md#event)**, the abstract base class to override
    4. **[EventDispatch](classes.md#eventdispatch)**, which defines core mechanism functions
    5. **[BlackboardQueueCVED](classes.md#bqcved)**, a example Dispatch subclass that ties the above together
    6. Various other decorators, helper functions
2. **ed_node** python program, a work in progress

---

* Other synchronization architectures exist such as [behavior trees](https://en.wikipedia.org/wiki/Behavior_tree_(artificial_intelligence,_robotics_and_control)) and [state machines](https://en.wikipedia.org/wiki/Finite-state_machine).

* Compared to those architectures, **eventdispatch** is *thin*, *scalable*, inherently *concurrent* and *performant*. **Safety** and **hygiene** are first-order considerations.

* Though inspired from robotics systems, this framework is relevant to the spatial and temporal *uncertainty* in simple and complex systems, and the *volatility* of what is asked of such systems. See [Usage patterns & best practices](usage.md).

* *Dispatch* is a **verb**, not a **noun**. Within a system, more than one component can *dispatch events*.