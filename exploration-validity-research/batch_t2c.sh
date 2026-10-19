#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
r() { local label=$1 ds=$2; shift 2; env "$@" LABEL=$label ./run.sh runall.py $ds 1000 2>&1 | tail -1 | cut -c1-1400; }
C="STOPR=3 MINLEN=1e-6 SKIPS=1"
for s in 3000 6000; do
  r t2c_cseg${s}_base coarse CSEG=$s HOOK=none
  r t2c_cseg${s}_vw1 coarse CSEG=$s HOOK=vw EVERY=1 $C
  r t2c_cseg${s}_vw10 coarse CSEG=$s HOOK=vw EVERY=10 $C
done
