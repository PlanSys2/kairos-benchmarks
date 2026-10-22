#!/bin/bash
# F0 baseline: Kairos and the planners of planutils on the same suites, 30 s and 3 GB per
# problem, every plan validated by Kairos. Two lanes of 4 processes (8 of the 16 cores).
# Results: bench/results/f0/<planner>_<suite>.csv (and .md with the summary)
cd "$(dirname "$0")/.."
K=$PWD/src/kairos/build-release/src/cli/kairos
R=bench/results/f0
run() {  # planner suite [args]
  local pl=$1 suite=$2; shift 2
  if [ "$pl" = kairos ]; then
    env -u LD_LIBRARY_PATH python3 bench/coverage.py run $K $suite --anytime --timeout 30 \
      --memory 3072 --jobs 4 --out $R/${pl}_$suite.csv > $R/${pl}_$suite.md 2> $R/${pl}_$suite.log
  else
    env -u LD_LIBRARY_PATH python3 bench/coverage.py run $K $suite --planutils $pl --timeout 30 \
      --memory 3072 --jobs 4 --out $R/${pl}_$suite.csv > $R/${pl}_$suite.md 2> $R/${pl}_$suite.log
  fi
  echo "$(date +%H:%M) $pl $suite: $(tail -n 1 $R/${pl}_$suite.md)"
}
lane_a() {
  for pl in optic tfd lpg-td popf; do
    for suite in examples b2 b1; do run $pl $suite; done
  done
}
lane_b() {
  for suite in examples b2 b1 b3 classical; do run kairos $suite; done
  for pl in enhsp-2020 metric-ff; do run $pl b3; done
  run lama classical
}
echo "$(date +%H:%M) start (kairos $($K --version))"
lane_a &
lane_b
wait
echo "$(date +%H:%M) done"
