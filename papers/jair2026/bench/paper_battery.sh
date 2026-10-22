#!/bin/bash
# The article's runs: Kairos 1.0.6 (installed apart, so rebuilds do not touch it) on every
# suite with the limits of the other planners' runs, then the ablations the CLI allows.
#   bench/paper_battery.sh [OUT_DIR] [support|main|validator|ablation|all]   (from planner_ws)
cd "$(dirname "$0")/.."
R=${1:-bench/results/paper}; WHAT=${2:-all}; mkdir -p $R
P=$PWD/$R/install
if [ ! -x $P/bin/kairos ]; then
  git -C src/kairos describe --tags --exact-match HEAD | grep -qx 1.0.6 || {
    echo "src/kairos is not at 1.0.6"; exit 1; }
  env -u LD_LIBRARY_PATH cmake --install src/kairos/build-release --prefix $P > $R/install.log 2>&1 || {
    echo "install failed"; tail $R/install.log; exit 1; }
fi
K=$P/bin/kairos
env -u LD_LIBRARY_PATH $K --version
run() {  # NAME SUITE TIMEOUT MEMORY [KAIROS ARGS...]
  local name=$1 suite=$2 t=$3 m=$4; shift 4
  local s=$(date +%s)
  env -u LD_LIBRARY_PATH python3 bench/coverage.py run $K $suite --anytime --timeout $t \
    --memory $m --jobs 8 --out $R/${name}_$suite.csv --keep-plans $R/plans_$name -- --threads 1 "$@" > $R/${name}_$suite.log 2>&1
  echo "$(date +%H:%M) $name $suite: $(grep -E '\*\*total' $R/${name}_$suite.log | head -1) ($(( ($(date +%s) - s) / 60 )) min)"
}
# Support table: one trivial task per feature, every planner (10 s, 2 GB)
if [ $WHAT = support ] || [ $WHAT = all ]; then
  run kairos probes 10 2048
  for p in lama metric-ff-s0 popf optic tfd lpg-td smtplan sota:enhsp sota:enhsp-pddlplus sota:nextflap sota:powerlifted; do
    n=${p#sota:}
    env -u LD_LIBRARY_PATH python3 bench/coverage.py run $K probes --planutils $p --timeout 10 \
      --memory 2048 --jobs 8 --out $R/${n}_probes.csv --keep-plans $R/plans_$n > $R/${n}_probes.log 2>&1
    echo "$(date +%H:%M) $n probes: $(grep -E '\*\*total' $R/${n}_probes.log | head -1)"
  done
fi
SUITES="classical b3 b1 b2 examples prefs durations pddlplus htg features"
if [ $WHAT = main ] || [ $WHAT = all ]; then
  for s in $SUITES; do
    run kairos $s 30 3072
  done
  run kairos b6 60 2048
fi
# Kairos's validator against VAL on every plan of the main run and two broken variants of each
if [ $WHAT = validator ] || [ $WHAT = all ]; then
  env -u LD_LIBRARY_PATH python3 bench/val_compare.py $K $R/plans_kairos $SUITES b6 \
    --out $R/val_compare.csv > $R/val_compare.md 2>&1
  echo "$(date +%H:%M) validator: $(sed -n 3,20p $R/val_compare.md | grep -c '^|') suites"
fi
if [ $WHAT = ablation ] || [ $WHAT = all ]; then
  # Temporal engines: M2 only, M3 only (POPF-like)
  for s in b1 b2; do
    run m2 $s 30 3072 --engine m2
    run m3 $s 30 3072 --engine m3
  done
  # Search: plain lazy FF, and LAMA without the novelty fallback
  for s in classical b3; do
    run ff $s 30 3072 --search ff
    run lama $s 30 3072 --search lama
  done
  # Without incremental goals
  run lama b6 60 2048 --search lama
fi
