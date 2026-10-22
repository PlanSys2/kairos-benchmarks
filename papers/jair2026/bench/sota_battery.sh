#!/bin/bash
# The state-of-the-art planners of sota/Dockerfile on the suites each one plans (Kairos:
# sota_kairos.sh; their first plans: sota_agile.sh): 30 s and 3 GB per problem (B6: 60 s, 2 GB), 8 jobs of one CPU each.
#   bench/sota_battery.sh OUT_DIR       (from planner_ws)
cd "$(dirname "$0")/.."
K=$PWD/src/kairos/build-release/src/cli/kairos
R=${1:-bench/results/sota}; mkdir -p $R
run() {  # NAME SUITE [ARGS...]
  local name=$1 suite=$2; shift 2
  local s=$(date +%s)
  env -u LD_LIBRARY_PATH python3 bench/coverage.py run $K $suite "$@" --jobs 8 \
    --out $R/${name}_$suite.csv > $R/${name}_$suite.log 2>&1
  echo "$(date +%H:%M) $name $suite: $(grep -E '\*\*total' $R/${name}_$suite.log | head -1) ($(( ($(date +%s) - s) / 60 )) min)"
}
# Classical: IPC 2023 winners and Dual-BFWS
for p in maidu levitron fdss decstar dual-bfws; do
  run $p classical --planutils sota:$p --timeout 30 --memory 3072
done
# Numeric
for p in lnm enhsp; do
  run $p b3 --planutils sota:$p --timeout 30 --memory 3072
done
# Temporal and numeric: NextFLAP
for s in b1 b2 examples prefs; do
  run nextflap $s --planutils sota:nextflap --timeout 30 --memory 3072
done
