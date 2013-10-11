#!/bin/sh
CMD_2TO3=${1:-2to3}
$CMD_2TO3 -w setup.py scripts/*.py scripts/quicknxs tests/*.py quicknxs/*.py
