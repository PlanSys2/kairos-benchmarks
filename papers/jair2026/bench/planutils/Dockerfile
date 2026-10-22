# Planners to compare Kairos with, from planutils (https://github.com/AI-Planning/planutils):
#   docker build -t kairos/planutils:benchmark bench/planutils   (from planner_ws)
# Used by bench/coverage.py --planutils NAME. Apptainer runs inside, hence --privileged there.
FROM aiplanning/planutils:latest
RUN yes | planutils install optic tfd popf lpg-td metric-ff enhsp-2020 lama val smtplan
