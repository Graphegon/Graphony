#!/bin/bash

phmdoctest README.md --setup FIRST --teardown LAST --setup-doctest --outfile graphony/tests/test_README.py
pytest --doctest-modules graphony/tests
