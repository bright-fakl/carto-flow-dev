#!/bin/sh
# usage: run_extra.sh <pipeline|presets|landmarks> ...   (from the repository root of investigate/default-dt)
for g in "$@"; do
  timeout 3000 uv run python "$(dirname "$0")/run_extra.py" "$g"
done
