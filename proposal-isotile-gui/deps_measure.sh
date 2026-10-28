#!/bin/bash
# Installed size and package count of the GUI today (pyproject at eb7b79e, carto-flow 2.0.0 from PyPI) against the ported GUI
# (isotile from the GitHub archive of a4625b7 instead of carto-flow). uv 0.8.17, Python 3.12, Linux x86_64, warm uv cache.
# Run: GUI=<git archive of eb7b79e> bash deps_measure.sh > deps_measure.txt
set -e
W=$(mktemp -d)
cd "$W"
uv venv --python 3.12 old -q
uv venv --python 3.12 new -q
S=$(date +%s.%N)
uv pip install -q --python old/bin/python "$GUI"
E=$(date +%s.%N)
echo "old: install $(echo "$E - $S" | bc) s, $(uv pip list --python old/bin/python | tail -n +3 | wc -l) packages, $(du -sm old/lib/python3.12/site-packages | cut -f1) MB"
S=$(date +%s.%N)
uv pip install -q --python new/bin/python "isotile @ https://github.com/bright-fakl/isotile/archive/a4625b7a28a9eb52f2403909a44f61a1447ee2e5.zip" "panel>=1.4" "param>=2.1" "bokeh>=3.4" "svgwrite>=1.4" "matplotlib>=3.9" "shapely>=2.1"
E=$(date +%s.%N)
echo "new: install $(echo "$E - $S" | bc) s, $(uv pip list --python new/bin/python | tail -n +3 | wc -l) packages, $(du -sm new/lib/python3.12/site-packages | cut -f1) MB"
echo "largest directories, old:"; du -sm old/lib/python3.12/site-packages/* | sort -rn | head -6
echo "largest directories, new:"; du -sm new/lib/python3.12/site-packages/* | sort -rn | head -6
echo "pandas is required by:"; uv pip show --python new/bin/python pandas | grep -i required-by
echo "only in old:"; comm -23 <(uv pip list --python old/bin/python --format freeze | cut -d= -f1 | sort) <(uv pip list --python new/bin/python --format freeze | cut -d= -f1 | sort) | tr '\n' ' '
echo
rm -rf "$W"
