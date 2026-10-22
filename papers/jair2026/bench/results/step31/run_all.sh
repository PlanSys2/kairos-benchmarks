#!/bin/bash
cd ~/ros/ros2/planner_ws
R=bench/results/step31
run() {
  systemd-run --user --scope -q -p MemoryMax=36G -p MemorySwapMax=0 env -i HOME=$HOME PATH=/usr/bin:/bin XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR LD_LIBRARY_PATH=/tmp/claude-1000/-home-fmrico-ros-ros2-planner-ws/bfdf498b-db12-4562-9575-aa5a013e8e38/scratchpad/kbin python3 bench/coverage.py run /tmp/claude-1000/-home-fmrico-ros-ros2-planner-ws/bfdf498b-db12-4562-9575-aa5a013e8e38/scratchpad/kbin/kairos $1 --anytime --timeout $2 --memory $3 --jobs 8 --out $R/kairos2_$1.csv -- --threads 1 > $R/kairos2_$1.log 2>&1
  echo "$(date +%H:%M) $1: $(tail -n1 $R/kairos2_$1.log)"
}
run features 30 3072
run classical 30 3072
run b1 30 3072
run b2 30 3072
run examples 30 3072
run b6 60 2048
