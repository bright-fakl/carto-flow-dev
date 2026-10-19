#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
r() { local label=$1 ds=$2; shift 2; env "$@" LABEL=$label ./run.sh runall.py $ds 1000 2>&1 | tail -1 | cut -c1-1400; }
C="STOPR=3 MINLEN=1e-6 SKIPS=1"
for dt in 0.18 0.20 0.22; do
  r t4b_cseg6000_inv_dt$dt coarse CSEG=6000 HOOK=none INV=1 MORPH_OPTS="{\"dt\":$dt}"
  r t4b_cseg6000_vw10inv_dt$dt coarse CSEG=6000 HOOK=vw EVERY=10 INV=1 MORPH_OPTS="{\"dt\":$dt}" $C
done
r t4b_cseg6000_vw1inv coarse CSEG=6000 HOOK=vw EVERY=1 INV=1 $C
