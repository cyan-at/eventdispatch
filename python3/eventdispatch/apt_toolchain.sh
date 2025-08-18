#!/bin/bash

# cd eventdispatch/python3/eventdispatch/

# update
# debian/changelog
# update line 11 below

debuild -k2024A1A77FE666D2A742FEDA6EE9B8235B1719DD -S

dput ppa:cyanatlaunchpad/python3-eventdispatch-ppa ../python3-eventdispatch_0.2.2_source.changes
