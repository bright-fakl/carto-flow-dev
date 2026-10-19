#!/bin/bash
# fixed-schedule protocol: per-level iteration counts, stall rule off
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
export PROTO=p3 SCHED=${SCHED:-600,150,400}
for cfg in ${CONFIGS:-dt0.16 dt0.18 dt0.20 dt0.22 dt0.24}; do
  export MORPH_OPTS="{\"dt\":${cfg#dt}}"
  for m in ${METHODS:-base vw1 vw10}; do
    unset HOOK INV EVERY
    case $m in base) export HOOK=none;; inv) export HOOK=none INV=1;; vw*inv) export HOOK=vw INV=1 EVERY=$(echo ${m#vw} | sed 's/inv//');; vw*) export HOOK=vw EVERY=${m#vw};; esac
    METHOD=$m LABEL=${PROTO}_${cfg}_$m ./run.sh runall.py county 1000 2>&1 | tail -1 | cut -c1-200
  done
done
