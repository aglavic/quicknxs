#!/bin/sh
CMD_2TO3=${1:-2to3}
$CMD_2TO3 -wn -j 2 --no-diffs setup.py dist_data/update_version.py scripts/quicknxs tests/*.py quicknxs/*.py quicknxs/config/*.py 
