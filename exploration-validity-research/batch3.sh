#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
LABEL=adv_rk2 ADV=rk2 ./run.sh expb.py county 1000 2>&1 | tail -1 | cut -c1-600
LABEL=adv_rk4 ADV=rk4 ./run.sh expb.py county 1000 2>&1 | tail -1 | cut -c1-600
LABEL=adv_euler4 ADV=euler NSUB=4 ./run.sh expb.py county 1000 2>&1 | tail -1 | cut -c1-600
LABEL=dt0.05 MORPH_OPTS='{"dt":0.05}' ./run.sh base.py county 3000 2>&1 | tail -1 | cut -c1-600
LABEL=floor0.05 VFLOOR=0.05 ./run.sh expb.py county 1000 2>&1 | tail -1 | cut -c1-600
LABEL=floor0.2 VFLOOR=0.2 ./run.sh expb.py county 1000 2>&1 | tail -1 | cut -c1-600
