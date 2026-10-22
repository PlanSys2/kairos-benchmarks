"""A unified-planning engine (tamer, aries) on a PDDL domain and problem.

    run_up.py ENGINE DOMAIN PROBLEM

Prints the plan as timed lines (or sequential ones), after "@@status STATUS".
"""
import re
import sys
import tempfile

from unified_planning.io import PDDLReader
from unified_planning.shortcuts import OneshotPlanner, get_environment

engine, domain, problem = sys.argv[1:4]
# Its parser rejects an empty (:functions) section, which PlanSys2 domains have
with open(domain) as f:
    text = re.sub(r';[^\n]*', '', f.read())
text = re.sub(r'\(:functions\s*\)', '', text)
with tempfile.NamedTemporaryFile('w', suffix='.pddl', delete=False) as f:
    f.write(text)
    domain = f.name
get_environment().credits_stream = None
task = PDDLReader().parse_problem(domain, problem)
with OneshotPlanner(name=engine) as planner:
    result = planner.solve(task)
print('@@status', result.status.name)
plan = result.plan
if plan is not None:
    if hasattr(plan, 'timed_actions'):
        for start, a, dur in plan.timed_actions:
            args = ' '.join(str(p) for p in a.actual_parameters)
            line = '%.3f: (%s %s)' % (float(start), a.action.name, args)
            print(line + (' [%.3f]' % float(dur) if dur is not None else ''))
    else:
        for a in plan.actions:
            print('(%s %s)' % (a.action.name, ' '.join(str(p) for p in a.actual_parameters)))
