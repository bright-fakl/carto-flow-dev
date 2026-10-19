#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
export PROTO=${PROTO:-p2}
DS=${DS:-county}
METHODS=${METHODS:-"inv vw1inv vw10inv"}
CONFIGS=${CONFIGS:-"dt0.16 dt0.18 dt0.20 dt0.22 dt0.24"}
for cfg in $CONFIGS; do
  unset MSL MORPH_OPTS; N=1000
  case $cfg in
    dt*) export MORPH_OPTS="{\"dt\":${cfg#dt}}";;
    msl*) export MSL=${cfg#msl};;
    n*) N=${cfg#n};;
  esac
  for m in $METHODS; do
    unset HOOK INV EVERY F32 BUDGET
    case $m in
      base) export HOOK=none;;
      inv) export HOOK=none INV=1;;
      vw*inv) export HOOK=vw INV=1 EVERY=$(echo ${m#vw} | sed 's/inv//');;
      vw*f32) export HOOK=vw F32=1 EVERY=$(echo ${m#vw} | sed 's/f32//');;
      vw*) export HOOK=vw EVERY=${m#vw};;
    esac
    METHOD=$m LABEL=${PROTO}_${cfg}_$m ./run.sh runall.py $DS $N 2>&1 | tail -1 | cut -c1-140
  done
done
