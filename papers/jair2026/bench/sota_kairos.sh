#!/bin/bash
# Kairos on the suites of bench/sota_battery.sh (same conditions), into the same OUT_DIR
#   bench/sota_kairos.sh OUT_DIR       (from planner_ws)
cd "$(dirname "$0")/.."
K=$PWD/src/kairos/build-release/src/cli/kairos
R=${1:-bench/results/sota}; mkdir -p $R
run() {  # SUITE TIMEOUT MEMORY
  local s=$(date +%s)
  env -u LD_LIBRARY_PATH python3 bench/coverage.py run $K $1 --anytime --timeout $2 --memory $3 \
    --jobs 8 --out $R/kairos_$1.csv -- --threads 1 > $R/kairos_$1.log 2>&1
  echo "$(date +%H:%M) kairos $1: $(grep -E '\*\*total' $R/kairos_$1.log | head -1) ($(( ($(date +%s) - s) / 60 )) min)"
}
# The current code (M2 ties and the classical portfolio included)
env -u LD_LIBRARY_PATH cmake --build src/kairos/build-release -j8 > $R/kairos_build.log 2>&1 || {
  echo "build failed"; tail -20 $R/kairos_build.log; exit 1; }
run classical 30 3072
run b3 30 3072
run b1 30 3072
run b2 30 3072
run examples 30 3072
run b6 60 2048
