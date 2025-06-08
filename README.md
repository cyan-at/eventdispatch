# <a href="https://github.com/cyan-at/eventdispatch" target="_blank">eventdispatch</a>
Event Dispatch: discrete time synchronization

## Documentation

The latest documentation on <a href="https://eventdispatch.readthedocs.io/en/latest/" target="_blank">readthedocs</a>

## python3: apt installation
```
sudo add-apt-repository ppa:cyanatlaunchpad/python3-eventdispatch-ppa
sudo apt update
sudo apt install python3-eventdispatch
```

## python3: <a href="https://pypi.org/project/eventdispatch/" target="_blank">pip</a> installation
```
virtualenv try-eventdispatch
. try-eventdispatch/bin/activate
pip install eventdispatch
```

## Issues/Contributing

I do not expect the `core` module to be volatile much since the mechanism is very straightforward.

Any volatility can arguably be captured in `Event` or `EventDispatch` child classes.

Although archived, I do actively maintain this repo. Please open an issue or file a fork+PR if you have any bugs/bugfixes/features!
