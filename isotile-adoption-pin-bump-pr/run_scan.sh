#!/bin/bash
# Offset scan with three configurations, one after the other.
SP=/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad
D=/home/fakl/carto-flow-dev/isotile-adoption-pin-bump-pr
W=/home/fakl/carto-flow/.claude/worktrees/agent-aa4901a28886b4ddd
cd /tmp
PYTHONPATH=$SP/mainsrc/src $SP/venv_old/bin/python $D/offset_scan.py oldpin $SP/S_old.json > $D/scan_oldpin.log 2>&1
PYTHONPATH=$W/src $SP/venv_new/bin/python $D/offset_scan.py newpin $SP/S_new.json > $D/scan_newpin.log 2>&1
PYTHONPATH=$W/src $SP/venv_new/bin/python $D/offset_scan.py straight $SP/S_straight.json straight > $D/scan_newpin_straight.log 2>&1
echo done
