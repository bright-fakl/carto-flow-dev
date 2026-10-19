#!/bin/bash
export NUMBA_NUM_THREADS=8 PYTHONPATH=/home/fakl/cf-validity/src
cd /home/fakl/cf-validity
S=$1; shift; exec uv run --project /home/fakl/carto-flow python /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity/$S "$@"
