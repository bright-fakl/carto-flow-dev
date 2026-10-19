#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
r() { local label=$1 ds=$2; shift 2; env "$@" LABEL=$label ./run.sh runall.py $ds 1000 2>&1 | tail -1 | cut -c1-1300; }
C="STOPR=3 MINLEN=1e-6 SKIPS=1"
r t2b_coarse_base coarse HOOK=none
r t2b_coarse_f10 coarse HOOK=vw EVERY=1 FLAT=0.25 FLATREL=0.1 $C
r t2b_coarse_f10e2 coarse HOOK=vw EVERY=2 FLAT=0.25 FLATREL=0.1 $C
r t2b_coarse_f10e3 coarse HOOK=vw EVERY=3 FLAT=0.25 FLATREL=0.1 $C
r t2b_coarse_f10_f32 coarse HOOK=vw EVERY=1 FLAT=0.25 FLATREL=0.1 F32=1 $C
r t2b_mid2000_base mid MSEG=2000 HOOK=none
r t2b_mid2000_vw1 mid MSEG=2000 HOOK=vw EVERY=1 $C
r t2b_mid2000_vw10 mid MSEG=2000 HOOK=vw EVERY=10 $C
r t2b_mid2000_flat1 mid MSEG=2000 HOOK=vw EVERY=1 FLAT=0.25 FLATREL=0.1 $C
r t2b_mid3000_base mid MSEG=3000 HOOK=none
r t2b_mid3000_vw10 mid MSEG=3000 HOOK=vw EVERY=10 $C
r t2b_mid3000_flat1 mid MSEG=3000 HOOK=vw EVERY=1 FLAT=0.25 FLATREL=0.1 $C
