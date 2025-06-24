#!/bin/bash

rm -rf ./debian

sudo rosdep init
rosdep update

rm -rf ./debian
bloom-generate rosdebian

# in a vm, build this on vm's own mount
fakeroot debian/rules clean
fakeroot debian/rules binary
