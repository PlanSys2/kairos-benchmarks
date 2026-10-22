#!/bin/bash
# PDDL+ suite (hstairs and SMTPlan's benchmarks): Kairos, ENHSP (sat-hadd, steps of 0.1 s) and
# SMTPlan+, 30 s and 3 GB each
#   bench/pddlplus_battery.sh [OUT_DIR [PLANNERS...]]   (from planner_ws; all by default)
cd "$(dirname "$0")/.."
K=$PWD/src/kairos/build-release/src/cli/kairos
R=${1:-bench/results/pddlplus}; mkdir -p $R; shift
WHO=${*:-kairos enhsp smtplan}
env -u LD_LIBRARY_PATH cmake --build src/kairos/build-release -j8 > $R/kairos_build.log 2>&1 || {
  echo "build failed"; tail -20 $R/kairos_build.log; exit 1; }
run() {  # NAME JOBS ARGS...
  local name=$1 jobs=$2 s=$(date +%s); shift 2
  env -u LD_LIBRARY_PATH python3 bench/coverage.py run $K pddlplus --timeout 30 --memory 3072 \
    --jobs $jobs --out $R/$name.csv "$@" > $R/$name.log 2>&1
  echo "$(date +%H:%M) $name: $(grep -E '\*\*total' $R/$name.log | head -1) ($(( ($(date +%s) - s) / 60 )) min)"
}
for w in $WHO; do
  case $w in
    kairos) run kairos 8 --anytime -- --threads 1;;
    enhsp) run enhsp 4 --planutils sota:enhsp-pddlplus;;
    smtplan) run smtplan 4 --planutils smtplan;;
  esac
done
