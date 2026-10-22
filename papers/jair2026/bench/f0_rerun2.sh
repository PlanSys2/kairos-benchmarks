#!/bin/bash
# After f0_rerun.sh: OPTIC, POPF and TFD again with the fixed reading of stdout (stray
# "(...)" lines counted as invalid plans), 2 lanes of 4
cd "$(dirname "$0")/.."
until grep -q "rerun done" bench/results/f0/progress.log; do sleep 30; done
K=$PWD/src/kairos/build-release/src/cli/kairos
R=bench/results/f0
run() {
  env -u LD_LIBRARY_PATH python3 bench/coverage.py run $K $2 --planutils $1 --timeout 30 \
    --memory 3072 --jobs 4 --out $R/$1_$2.csv > $R/$1_$2.md 2> $R/$1_$2.log
  echo "$(date +%H:%M) $1 $2: $(tail -n 1 $R/$1_$2.md)"
}
(for s in examples b2 b1; do run optic $s; done; for s in examples b2; do run tfd $s; done) &
for s in examples b2 b1; do run popf $s; done; run tfd b1
wait
echo "$(date +%H:%M) rerun2 done"
