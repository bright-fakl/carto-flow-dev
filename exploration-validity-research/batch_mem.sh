#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
export PROTO=m
run() { # label, env assignments...
  local label=$1; shift
  env "$@" METHOD=$label LABEL=m_$label ./run.sh runall.py county 1000 2>&1 | tail -1 | cut -c1-1500
}
run base HOOK=none
run vw10 HOOK=vw EVERY=10
run vw10_f32 HOOK=vw EVERY=10 F32=1
run vw10_b128 HOOK=vw EVERY=10 BUDGET=128
run vw10_f32_b64 HOOK=vw EVERY=10 F32=1 BUDGET=64
run vw20 HOOK=vw EVERY=20
run vw20_f32_b128 HOOK=vw EVERY=20 F32=1 BUDGET=128
run vw1 HOOK=vw EVERY=1
