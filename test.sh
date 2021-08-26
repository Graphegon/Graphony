#!/bin/bash

phmdoctest README.md --setup FIRST --setup-doctest --outfile tests/test_README.py
pytest --doctest-modules tests/
