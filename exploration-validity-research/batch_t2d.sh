#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
r() { local label=$1 ds=$2; shift 2; env "$@" LABEL=$label ./run.sh runall.py $ds 1000 2>&1 | tail -1 | cut -c1-1400; }
C="STOPR=3 MINLEN=1e-6 SKIPS=1"
r t2d_cseg10000_base coarse CSEG=10000 HOOK=none
r t2d_cseg10000_vw10 coarse CSEG=10000 HOOK=vw EVERY=10 $C
r t2d_cseg10000_vw3 coarse CSEG=10000 HOOK=vw EVERY=3 $C
for dt in 0.18 0.22; do
  r t2d_cseg6000_base_dt$dt coarse CSEG=6000 HOOK=none MORPH_OPTS="{\"dt\":$dt}"
  r t2d_cseg6000_vw10_dt$dt coarse CSEG=6000 HOOK=vw EVERY=10 MORPH_OPTS="{\"dt\":$dt}" $C
done
r t2d_cseg6000_vw10_f32 coarse CSEG=6000 HOOK=vw EVERY=10 F32=1 BUDGET=64 $C
r t2d_cseg6000_vw10inv coarse CSEG=6000 HOOK=vw EVERY=10 INV=1 $C
