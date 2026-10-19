#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
for n in 200 400 800; do for c in base vw1 vw10; do ./run.sh fine.py $c $n 2>&1 | tail -1 | cut -c1-200; done; done
