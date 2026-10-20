#!/bin/bash
# usage: w.sh resfile n  -- waits up to 9.5 min until the file has n lines
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/adlogs
for i in $(seq 1 28); do
  c=0; [ -f $1 ] && c=$(wc -l < $1)
  [ $c -ge $2 ] && break; sleep 20
done
echo "$1: $c lines"
