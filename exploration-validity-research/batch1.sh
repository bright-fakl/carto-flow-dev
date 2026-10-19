#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
for dt in 0.18 0.22; do
  LABEL=base_dt$dt MORPH_OPTS="{\"dt\":$dt}" ./run.sh base.py county 1000 2>&1 | tail -1
  LABEL=vw_dt$dt MORPH_OPTS="{\"dt\":$dt}" ./run.sh runvw.py county 1000 2>&1 | tail -1
done
