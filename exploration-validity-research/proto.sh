#!/bin/bash
# protocol: perturbed configurations x methods; appends to out/protocol.jsonl
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
export PROTO=${PROTO:-p1}
METHODS=${METHODS:-"base vw1 vw10"}
CONFIGS=${CONFIGS:-"dt0.16 dt0.18 dt0.20 dt0.22 dt0.24 msl800 msl1200 n400 n700"}
for cfg in $CONFIGS; do
  unset MSL MORPH_OPTS; N=1000
  case $cfg in
    dt*) export MORPH_OPTS="{\"dt\":${cfg#dt}}";;
    msl*) export MSL=${cfg#msl};;
    n*) N=${cfg#n};;
  esac
  for m in $METHODS; do
    case $m in
      base) METHOD=$m LABEL=${PROTO}_${cfg}_$m ./run.sh base.py county $N 2>&1 | tail -1 | cut -c1-120;;
      vw*) METHOD=$m LABEL=${PROTO}_${cfg}_$m EVERY=${m#vw} ./run.sh runvw.py county $N 2>&1 | tail -1 | cut -c1-120;;
      *) echo unknown $m;;
    esac
  done
done
