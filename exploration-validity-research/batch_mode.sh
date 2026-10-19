#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
export PROTO=p6 SNAP=25 SCHED=600,150,400 MORPH_OPTS='{"dt":0.2}' VFLOOR=0.3
for mode in none chord replay; do
  METHOD=vw1_$mode LABEL=p6_$mode HOOK=vw EVERY=1 MODE=$mode ./run.sh runall.py county 1000 2>&1 | tail -1 | cut -c1-150
done
METHOD=base LABEL=p6_base HOOK=none ./run.sh runall.py county 1000 2>&1 | tail -1 | cut -c1-150
