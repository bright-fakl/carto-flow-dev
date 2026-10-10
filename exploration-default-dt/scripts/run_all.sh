#!/bin/sh
# usage: run_all.sh <group> [<group> ...]   (from the repository root of investigate/default-dt)
for g in "$@"; do
  timeout 3000 uv run python "$(dirname "$0")/run_sweep.py" "$g"
done
