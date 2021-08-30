#!/bin/bash

phmdoctest README.md --setup FIRST --teardown LAST --setup-doctest --outfile graphony/tests/test_README.py
python -m pytest --doctest-modules graphony/tests
