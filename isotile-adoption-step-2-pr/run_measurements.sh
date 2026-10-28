#!/bin/sh
# Memory and timing, old (step 1, dense) and new (step 2, sparse) one after the other, nothing else running.
#   run_measurements.sh <checkout of step 2> <src directory of step 1> <output directory>
set -e
NEW=$1
OLD_SRC=$2
OUT=$3
HERE=$(dirname "$0")
cd "$NEW"

for t in hexagon square; do
  PYTHONPATH=$OLD_SRC uv run python "$HERE/memory_check.py" step1-dense $t
  uv run python "$HERE/memory_check.py" step2-sparse $t
done > "$OUT/memory_output.txt" 2>&1

# best of 3, old and new alternating by case group
PYTHONPATH=$OLD_SRC uv run python "$HERE/identity_check.py" run step1-dense "$OUT/layouts_old.pkl" --repeat 3 > "$OUT/timing_old.txt" 2>&1
uv run python "$HERE/identity_check.py" run step2-sparse "$OUT/layouts_new.pkl" --repeat 3 > "$OUT/timing_new.txt" 2>&1
uv run python "$HERE/identity_check.py" compare "$OUT/layouts_old.pkl" "$OUT/layouts_new.pkl" > "$OUT/identity_and_timing.txt" 2>&1 || true
echo finished
