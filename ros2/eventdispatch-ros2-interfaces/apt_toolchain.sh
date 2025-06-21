#!/bin/bash

rm -rf ./debian

sudo rosdep init
rosdep update

rm -rf ./debian
bloom-generate rosdebian

fakeroot debian/rules clean
fakeroot debian/rules binary
