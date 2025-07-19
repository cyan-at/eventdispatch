#!/bin/bash

# cd eventdispatch/python3/eventdispatch/

# update
# pyproject.toml
# setup.py

rm -rf dist/
python3 -m build
twine upload dist/*

