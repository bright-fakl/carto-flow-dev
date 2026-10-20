#!/bin/bash
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad
i=1
while true; do
  l=$(sed -n "${i}p" adlogs/queue.txt)
  if [ -z "$l" ]; then sleep 10; [ -f adlogs/queue.stop ] && exit; continue; fi
  set -- $l
  while pgrep -f "drive.py adlogs/jobsA.jsonl" > /dev/null; do sleep 10; done
  python3 validity/drive.py $1 $2
  i=$((i+1))
done
