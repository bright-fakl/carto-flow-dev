#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
for dt in 0.15 0.18 0.22 0.25; do
  LABEL=vw10_dt$dt EVERY=10 MORPH_OPTS="{\"dt\":$dt}" ./run.sh runvw.py county 1000 2>&1 | tail -1 | cut -c1-700
done
for dt in 0.15 0.25; do
  LABEL=base_dt$dt MORPH_OPTS="{\"dt\":$dt}" ./run.sh base.py county 1000 2>&1 | tail -1 | cut -c1-400
done
LABEL=vw10 EVERY=10 ./run.sh runvw.py cd 1000 2>&1 | tail -1 | cut -c1-600
LABEL=vw10_ml1 MAXLEN=1 EVERY=10 ./run.sh runvw.py coarse 1000 2>&1 | tail -1 | cut -c1-900
