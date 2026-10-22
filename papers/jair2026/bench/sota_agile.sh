#!/bin/bash
# The others' first plan (agile IPC 2023 configurations, lama-first): time to the first plan on
# the classical suite, for the 100 ms / 1 s columns. Same limits as Kairos: 30 s, 3 GB, 8 jobs.
#   bench/sota_agile.sh OUT_DIR       (from planner_ws)
cd "$(dirname "$0")/.."
K=$PWD/src/kairos/build-release/src/cli/kairos
R=${1:-bench/results/sota}; mkdir -p $R
for p in lama-first maidu-agl levitron-agl fdss-agl; do
  s=$(date +%s)
  env -u LD_LIBRARY_PATH python3 bench/coverage.py run $K classical --planutils sota:$p \
    --timeout 30 --memory 3072 --jobs 8 --out $R/${p}_classical.csv > $R/${p}_classical.log 2>&1
  echo "$(date +%H:%M) $p classical: $(grep -E '\*\*total' $R/${p}_classical.log | head -1) ($(( ($(date +%s) - s) / 60 )) min)"
done
