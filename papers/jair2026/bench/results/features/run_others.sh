#!/bin/bash
cd ~/ros/ros2/planner_ws
K=$PWD/src/kairos/build-release/src/cli/kairos
R=bench/results/features
for p in sota:lama-first optic popf sota:enhsp; do
  n=${p#sota:}
  env -u LD_LIBRARY_PATH python3 bench/coverage.py run $K features --planutils $p --timeout 30 --memory 3072 --jobs 8 --out $R/$n.csv > $R/$n.log 2>&1
  echo "$(date +%H:%M) $n: $(tail -n1 $R/$n.log)"
done
