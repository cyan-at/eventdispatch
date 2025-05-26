# python3-eventdispatch

**eventdispatch** is a Python package for solving the *discrete time synchronization problem* in any computer system. It consists of:

1. **ed_common** python module, containing the following classes:
    1. **[EventDispatch](classes#eventdispatch)**, which defines core mechanism functions
    2. **[EventThread](classes#eventthread)**, a thread subclass
    3. **[Event](classes#event)**, the abstract base class to override
    4. **[Blackboard](classes#blackboard)**, a thread safe dictionary
    5. **[BlackboardQueueCVED](classes#bqcved)**, a example Dispatch subclass that ties the above together
2. **ed_node** python program, a work in progress

---

* Other synchronization architectures exist such as [behavior trees](https://en.wikipedia.org/wiki/Behavior_tree_(artificial_intelligence,_robotics_and_control)) and [state machines](https://en.wikipedia.org/wiki/Finite-state_machine).

* Compared to those architectures, **eventdispatch** is *thin*, *scalable*, inherently *concurrent* and *performant*. **Safety** and **hygiene** are first-order considerations.

* It is designed to deal with the spatial and temporal *uncertainty* in complex systems, and the *volatility* of what is asked of such systems. [Usage patterns & best practices](usage) will indicate how this is done.

* Although originally designed for robotics systems, the **eventdispatch** framework is relevant in any system where synchronization is important, deals with any **uncertainty**.

* Within a system, more than one component can and should *dispatch events*; *dispatch* is a **verb**, not a **noun**, related to [double dispatch](https://en.wikipedia.org/wiki/Double_dispatch)