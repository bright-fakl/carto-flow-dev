#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
LABEL=pw6_safe0.02 SAFE=1 TOL=0.02 BITS=6 ./run.sh pwrun_h.py county 1000 2>&1 | tail -3 | cut -c1-900
