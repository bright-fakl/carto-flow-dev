#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
export PROTO=${PROTO:-q1}
for cfg in ${CONFIGS:-dt0.16 dt0.18 dt0.20 dt0.22 dt0.24 msl800 msl1200}; do
  unset MSL MORPH_OPTS
  case $cfg in dt*) export MORPH_OPTS="{\"dt\":${cfg#dt}}";; msl*) export MSL=${cfg#msl};; esac
  for m in ${METHODS:-q1 q4 q8}; do
    case $m in q1) export REBUILD=1 MINRATIO=0;; q4) export REBUILD=4 MINRATIO=0.6;; q8) export REBUILD=8 MINRATIO=0.6;; esac
    BITS=6 PEVERY=1 METHOD=$m LABEL=${PROTO}_${cfg}_$m ./run.sh pwo_run.py ${DS:-county} ${N:-1000} 2>&1 | tail -1 | cut -c1-130
  done
done
