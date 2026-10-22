#!/bin/bash
# Reruns of the F0 baseline: Metric-FF (non-UTF-8 output) and LPG-TD (retries when it writes
# no plan), 2 lanes of 4
cd "$(dirname "$0")/.."
K=$PWD/src/kairos/build-release/src/cli/kairos
R=bench/results/f0
run() {
  env -u LD_LIBRARY_PATH python3 bench/coverage.py run $K $2 --planutils $1 --timeout 30 \
    --memory 3072 --jobs 4 --out $R/$1_$2.csv > $R/$1_$2.md 2> $R/$1_$2.log
  echo "$(date +%H:%M) $1 $2: $(tail -n 1 $R/$1_$2.md)"
}
(run lpg-td examples; run lpg-td b2; run lpg-td b1) &
run metric-ff b3
wait
echo "$(date +%H:%M) rerun done"
