#!/bin/bash

debuild -k2024A1A77FE666D2A742FEDA6EE9B8235B1719DD -S

dput ppa:cyanatlaunchpad/python3-eventdispatch-ppa ../python3-eventdispatch_0.1.10_source.changes
