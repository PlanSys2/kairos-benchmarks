#!/usr/bin/env python3
# Copyright 2026 Intelligent Robotics Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Coverage and time of the kairos executable on benchmark suites of the corpus.

Run:      coverage.py run KAIROS SUITE --out results.csv [--timeout 30] [--jobs 6] [-- ARGS]
          coverage.py run KAIROS SUITE --out popf.csv --popf POPF   (POPF, validated by KAIROS)
          coverage.py run KAIROS SUITE --out optic.csv --planutils optic  (any planutils planner)
Compare:  coverage.py compare base.csv new.csv

Suites (under $KAIROS_PDDL_CORPUS, default ~/.cache/kairos/corpus):
  b3         IPC 2002, 2023 and 2026 numeric, 10 instances per domain (1, 3, 5, ... 19)
  classical  IPC 2023 satisficing and IPC 1998-2014 satisficing domains, 10 per domain
  b1         IPC 2002-2014 temporal domains, 5 instances per domain
  b2         required concurrency and temporal numeric (IPC 2011/2014, time2processes), 5 each
  quick      2 instances per domain of b3 and classical, for a fast check
  examples   the problems of docs/examples
  prefs      IPC 2006 preferences and trajectory constraints (PDDL3), 5 instances per domain
  durations  problems that need a duration between its bounds (bench/durations/gen.py)
  htg        hard-to-ground classical domains (~/.cache/kairos/sota/htg-domains), 5 per folder
  pddlplus   hstairs PDDL+ domains (processes, events, global constraints) and SMTPlan's
             benchmarks (~/.cache/kairos/sota/KCL-Planning_SMTPlan), 10 per domain
  combat     PlanSys2's combat example (bench/combat, a snapshot): scenarios and minimal problems
  b6         PlanSys2 problems scaled XS..XXL (b6/gen.py, under $KAIROS_B6, default
             ~/.cache/kairos/b6); --only filters by "b6/FAMILY/LEVEL"

--planutils up:tamer or up:aries runs that engine of unified-planning in the image
kairos/up:benchmark (up/Dockerfile) the same way.

--planutils sota:NAME runs a planner of the image kairos/sota:benchmark (sota/Dockerfile),
built from source: maidu and levitron (Scorpion, IPC 2023 satisficing winners), fdss (Fast
Downward Stone Soup 2023), decstar (IPC 2023 agile winner), dual-bfws, lnm (LNM-Plan, IPC 2023
numeric winner), enhsp (current ENHSP), nextflap (temporal and numeric).

--planutils NAME runs a planner of planutils (https://github.com/AI-Planning/planutils) in a
throwaway container of the image kairos/planutils:benchmark (planutils with the planners
installed, see planutils/Dockerfile), with the memory limit and one CPU; its time is
measured inside the container, so Docker's start-up does not count. Its last plan (anytime
planners keep improving until the timeout) is validated by KAIROS.

Extra ARGS after "--" go to kairos (for instance --search lama). Every plan kairos prints has
been validated by it. The agile score of a solved instance is 1 if it took at most 1 s, else
1 - log(t) / log(timeout), as in the IPC agile track.
"""

import argparse
import concurrent.futures
import csv
import glob
import math
import json
import os
import re
import subprocess
import sys
import tempfile
import time

CORPUS = os.environ.get('KAIROS_PDDL_CORPUS', os.path.expanduser('~/.cache/kairos/corpus'))
POTASSCO = 'potassco_pddl-instances'
CLASSICAL_OLD = [
    'ipc-1998/domains/logistics-round-1-strips',
    'ipc-2000/domains/blocks-strips-typed',
    'ipc-2000/domains/freecell-strips-typed',
    'ipc-2002/domains/depots-strips-automatic',
    'ipc-2002/domains/driverlog-strips-automatic',
    'ipc-2002/domains/rovers-strips-automatic',
    'ipc-2004/domains/airport-nontemporal-strips',
    'ipc-2004/domains/pipesworld-no-tankage-nontemporal-strips',
    'ipc-2006/domains/tpp-propositional-strips',
    'ipc-2006/domains/trucks-propositional-strips',
    'ipc-2008/domains/elevators-sequential-satisficing-strips',
    'ipc-2008/domains/sokoban-sequential-satisficing-strips',
    'ipc-2008/domains/woodworking-sequential-satisficing-strips',
    'ipc-2011/domains/barman-sequential-satisficing',
    'ipc-2011/domains/nomystery-sequential-satisficing',
    'ipc-2011/domains/parking-sequential-satisficing',
    'ipc-2011/domains/visitall-sequential-satisficing',
    'ipc-2014/domains/childsnack-sequential-satisficing',
    'ipc-2014/domains/floortile-sequential-satisficing',
    'ipc-2014/domains/hiking-sequential-satisficing',
]


NUMERIC_OLD = [
    'ipc-2002/domains/depots-numeric-automatic',
    'ipc-2002/domains/driverlog-numeric-automatic',
    'ipc-2002/domains/rovers-numeric-automatic',
    'ipc-2002/domains/satellite-numeric-automatic',
    'ipc-2002/domains/zenotravel-numeric-automatic',
    'ipc-2002/domains/settlers-numeric-automatic',
]


TEMPORAL = [
    'ipc-2002/domains/depots-time-automatic',
    'ipc-2002/domains/driverlog-time-automatic',
    'ipc-2002/domains/rovers-time-automatic',
    'ipc-2002/domains/satellite-time-automatic',
    'ipc-2002/domains/zenotravel-time-automatic',
    'ipc-2004/domains/airport-temporal-strips',
    'ipc-2004/domains/airport-temporal-time-windows-strips',
    'ipc-2004/domains/pipesworld-no-tankage-temporal-strips',
    'ipc-2004/domains/pipesworld-no-tankage-temporal-deadlines-strips',
    'ipc-2004/domains/satellite-time-strips',
    'ipc-2004/domains/satellite-time-time-windows-strips',
    'ipc-2004/domains/umts-temporal-strips',
    'ipc-2004/domains/umts-temporal-time-windows-strips',
    'ipc-2006/domains/openstacks-time-strips',
    'ipc-2006/domains/pathways-metric-time',
    'ipc-2006/domains/rovers-metric-time',
    'ipc-2006/domains/storage-time',
    'ipc-2006/domains/tpp-metric-time',
    'ipc-2006/domains/trucks-time-strips',
    'ipc-2006/domains/trucks-time-constraints-timed-initial-literals',
    'ipc-2008/domains/crew-planning-temporal-satisficing-strips',
    'ipc-2008/domains/elevator-temporal-satisficing-strips',
    'ipc-2008/domains/model-train-temporal-satisficing-numeric-fluents',
    'ipc-2008/domains/openstacks-temporal-satisficing-strips',
    'ipc-2008/domains/parc-printer-temporal-satisficing-strips',
    'ipc-2008/domains/peg-solitaire-temporal-satisficing-strips',
    'ipc-2008/domains/sokoban-temporal-satisficing-strips',
    'ipc-2008/domains/transport-temporal-satisficing-numeric-fluents',
    'ipc-2008/domains/woodworking-temporal-satisficing-numeric-fluents',
    'ipc-2011/domains/crew-planning-temporal-satisficing',
    'ipc-2011/domains/elevator-temporal-satisficing',
    'ipc-2011/domains/floor-tile-temporal-satisficing',
    'ipc-2011/domains/openstacks-temporal-satisficing',
    'ipc-2011/domains/parc-printer-temporal-satisficing',
    'ipc-2011/domains/parking-temporal-satisficing',
    'ipc-2011/domains/peg-solitaire-temporal-satisficing',
    'ipc-2011/domains/sokoban-temporal-satisficing',
    'ipc-2011/domains/storage-temporal-satisficing',
    'ipc-2014/domains/driver-log-temporal-satisficing',
    'ipc-2014/domains/floor-tile-temporal-satisficing',
    'ipc-2014/domains/map-analyzer-temporal-satisficing',
    'ipc-2014/domains/parking-temporal-satisficing',
    'ipc-2014/domains/road-traffic-accident-management-temporal-satisficing',
    'ipc-2014/domains/satellite-temporal-satisficing',
    'ipc-2014/domains/storage-temporal-satisficing',
]
CONCURRENCY = [
    'ipc-2011/domains/match-cellar-temporal-satisficing',
    'ipc-2011/domains/turn-and-open-temporal-satisficing',
    'ipc-2011/domains/temporal-machine-shop-temporal-satisficing',
    'ipc-2014/domains/match-cellar-temporal-satisficing',
    'ipc-2014/domains/turn-and-open-temporal-satisficing',
    'ipc-2014/domains/temporal-machine-shop-temporal-satisficing',
    'ipc-2004/domains/airport-temporal-time-windows-compiled-strips',
    'ipc-2004/domains/satellite-time-time-windows-compiled-strips',
]
TIME2PROCESSES = ['MatchCellar', 'temporal_plant_watering', 'temporal_sailing']


def natural(name):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', name)]


def numeric_domains():
    out = []
    for dataset in ('ipc2023-numeric_ipc2023-dataset', 'ipc2026-numeric_ipc2026-dataset'):
        base = os.path.join(CORPUS, dataset)
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base)):
            folder = os.path.join(base, d)
            inst = os.path.join(folder, 'instances')
            if not os.path.isdir(inst):
                continue
            domains = [f for f in os.listdir(folder) if f.endswith('.pddl')]
            if len(domains) != 1:
                continue
            problems = sorted(os.listdir(inst), key=natural)
            out.append((dataset.split('_')[0] + '/' + d, os.path.join(folder, domains[0]),
                        [os.path.join(inst, p) for p in problems]))
    for rel in NUMERIC_OLD:
        d = potassco(rel)
        if d:
            out.append(d)
    return out


def potassco(rel):
    folder = os.path.join(CORPUS, POTASSCO, rel)
    inst = os.path.join(folder, 'instances')
    if not os.path.isdir(inst):
        return None
    pairs = []
    for p in sorted(os.listdir(inst), key=natural):
        m = re.search(r'(\d+)', p)
        per = os.path.join(folder, 'domains', 'domain-%s.pddl' % m.group(1)) if m else ''
        domain = per if os.path.exists(per) else os.path.join(folder, 'domain.pddl')
        pairs.append((domain, os.path.join(inst, p)))
    return (rel.split('/')[0] + '/' + rel.split('/')[-1], pairs, None)


def classical_domains():
    out = []
    sat = os.path.join(CORPUS, 'ipc2023-classical_ipc2023-dataset', 'sat')
    if os.path.isdir(sat):
        for d in sorted(os.listdir(sat)):
            folder = os.path.join(sat, d)
            problems = sorted((f for f in os.listdir(folder) if f.endswith('.pddl') and
                               not f.startswith('domain')), key=natural)
            if os.path.exists(os.path.join(folder, 'domain.pddl')):
                out.append(('ipc2023/' + d, os.path.join(folder, 'domain.pddl'),
                            [os.path.join(folder, p) for p in problems]))
            else:
                # A domain per problem (quantum-layout: domain_p01.pddl for p01.pddl)
                out.append(('ipc2023/' + d, [(os.path.join(folder, 'domain_' + p),
                                              os.path.join(folder, p)) for p in problems], None))
    for rel in CLASSICAL_OLD:
        d = potassco(rel)
        if d:
            out.append(d)
    return out


def time2processes():
    out = []
    base = os.path.join(CORPUS, 'hstairs_time2processes', 'benchmarks')
    for d in TIME2PROCESSES:
        folder = os.path.join(base, d)
        inst = os.path.join(folder, 'instances')
        if not os.path.isdir(inst):
            continue
        problems = sorted(os.listdir(inst), key=natural)
        out.append(('time2processes/' + d, os.path.join(folder, 'domain.pddl'),
                    [os.path.join(inst, p) for p in problems]))
    return out


def pddl_plus():
    """hstairs PDDL+ domains: domain + instances/, or PREFIX_domain.pddl + PREFIX.N.instance.pddl"""
    base = os.path.join(CORPUS, 'hstairs_pddl_plus_domains')
    out = []
    domain_of = {'1D-powered-descent': 'descent.pddl', 'generator_nl': 'domain_nl.pddl',
                 'hasp': 'domain_constraints.pddl'}
    for d in sorted(os.listdir(base)):
        folder = os.path.join(base, d)
        inst = os.path.join(folder, 'instances')
        if os.path.isdir(inst):
            problems = sorted((p for p in os.listdir(inst) if p.endswith('.pddl')), key=natural)
            out.append(('pddlplus/' + d, os.path.join(folder, domain_of.get(d, 'domain.pddl')),
                        [os.path.join(inst, p) for p in problems]))
            continue
        if not os.path.isdir(folder):
            continue
        for dom in sorted(glob.glob(os.path.join(folder, '*_domain.pddl'))):
            prefix = os.path.basename(dom)[:-len('_domain.pddl')]
            problems = sorted(glob.glob(os.path.join(folder, prefix + '.*.instance.pddl')),
                              key=lambda x: natural(os.path.basename(x)))
            if problems:
                out.append(('pddlplus/%s/%s' % (d, prefix), dom, problems))
    # SMTPlan's benchmarks (PDDL+ and PDDL 2.1 with non-linear continuous effects)
    smt = os.path.expanduser('~/.cache/kairos/sota/KCL-Planning_SMTPlan/benchmarks')
    if os.path.isdir(smt):
        for d in sorted(os.listdir(smt)):
            folder = os.path.join(smt, d)
            files = sorted(os.listdir(folder), key=natural)
            doms = [f for f in files if 'domain' in f]
            if doms:
                out.append(('pddlplus/smtplan/' + d, os.path.join(folder, doms[0]),
                            [os.path.join(folder, f) for f in files if f not in doms]))
    return out


def pick(items, count):
    # 1, 3, 5... of a 20-instance domain: easy to hard
    if len(items) <= count:
        return items
    step = len(items) / count
    return [items[int(i * step)] for i in range(count)]


# docs/examples: robotics domains (resources that run out, costs, concurrency)
EXAMPLES = [
    ('cooking_domain.pddl', 'cooking_problem_simple.pddl'),
    ('cooking_domain.pddl', 'cooking_problem_long.pddl'),
    ('cooking_domain.pddl', 'cooking_problem_huge.pddl'),
    ('cooking_cost_domain.pddl', 'cooking_cost_problem_simple.pddl'),
    ('cooking_cost_domain.pddl', 'cooking_cost_problem_medium.pddl'),
    ('cooking_cost_domain.pddl', 'cooking_cost_problem_long.pddl'),
    ('factory.pddl', 'factory_problem_1.pddl'),
    ('battery_domain.pddl', 'battery_problem_simple.pddl'),
    ('battery_domain.pddl', 'battery_problem_medium.pddl'),
    ('battery_domain.pddl', 'battery_problem_long.pddl'),
    ('elevator_domain.pddl', 'elevator_problem.pddl'),
    ('road_trip_domain.pddl', 'road_trip_problem.pddl'),
    ('suave_domain.pddl', 'suave_problem.pddl'),
    ('domain_simple.pddl', 'domain_simple_problem_1.pddl'),
]


def suite(name):
    per = 2 if name == 'quick' else (5 if name in ('b1', 'b2', 'prefs') else 10)
    tasks = []
    groups = []
    if name == 'b1':
        groups = [d for d in (potassco(r) for r in TEMPORAL) if d]
    if name == 'b2':
        groups = [d for d in (potassco(r) for r in CONCURRENCY) if d] + time2processes()
    if name == 'prefs':
        root = os.path.join(CORPUS, POTASSCO, 'ipc-2006', 'domains')
        rels = sorted(d for d in os.listdir(root) if 'preferences' in d or 'constraints' in d)
        groups = [d for d in (potassco('ipc-2006/domains/' + r) for r in rels) if d]
    for label, a, b in groups:
        if b is None:
            tasks += [(label, d, p) for d, p in pick(a, per)]
        else:
            tasks += [(label, a, p) for p in pick(b, per)]
    if name == 'probes':
        # One trivial task per PDDL feature (bench/probes), for the support table
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probes')
        tasks += [('probes/' + f, os.path.join(root, f, 'domain.pddl'),
                   os.path.join(root, f, 'problem.pddl')) for f in sorted(os.listdir(root))]
    if name == 'htg':
        # Hard-to-ground domains (github.com/abcorrea/htg-domains): 5 per folder with a domain
        root = os.path.expanduser('~/.cache/kairos/sota/htg-domains')
        for folder, _dirs, files in sorted(os.walk(root)):
            if 'domain.pddl' not in files:
                continue
            problems = sorted((f for f in files if f.endswith('.pddl') and f != 'domain.pddl'),
                              key=natural)
            label = 'htg/' + os.path.relpath(folder, root)
            tasks += [(label, os.path.join(folder, 'domain.pddl'), os.path.join(folder, f))
                      for f in pick(problems, 5)]
    if name == 'features':
        # The feature bank: per feature, families of the corpus and generated ones
        bank = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'featurebank')
        with open(os.path.join(bank, 'corpus_bank.json')) as fh:
            for feature, fams in json.load(fh).items():
                for f in fams:
                    tasks += [('features/%s/%s' % (feature, os.path.basename(f['family'])), d, p)
                              for d, p in f['tasks']]
        with open(os.path.join(bank, 'generated', 'manifest.json')) as fh:
            for t in json.load(fh):
                tasks.append(('features/%s/%s' % (t['feature'], t['family']),
                              os.path.join(bank, t['domain']), os.path.join(bank, t['problem'])))
        # Each problem once (a family serves several features: featurebank/report.py splits)
        seen = set()
        tasks = [x for x in tasks if (x[1], x[2]) not in seen and not seen.add((x[1], x[2]))]
    if name == 'durations':
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'durations', 'problems')
        for d in sorted(os.listdir(root)):
            for p in sorted(glob.glob(os.path.join(root, d, 'p*.pddl'))):
                tasks.append(('durations/' + d, os.path.join(root, d, 'domain.pddl'), p))
    if name == 'pddlplus':
        tasks += [(label, a, p) for label, a, b in pddl_plus() for p in pick(b, per)]
    if name in ('b3', 'quick'):
        for label, a, b in numeric_domains():
            if b is None:
                tasks += [(label, d, p) for d, p in pick(a, per)]
            else:
                tasks += [(label, a, p) for p in pick(b, per)]
    if name == 'examples':
        ex = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'kairos', 'docs',
                          'examples', 'pddls')
        for d, p in EXAMPLES:
            tasks.append(('examples/' + d.replace('.pddl', ''), os.path.join(ex, d),
                          os.path.join(ex, p)))
    if name == 'b6':
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.environ.get('KAIROS_B6', os.path.expanduser('~/.cache/kairos/b6'))
        for fam in sorted(os.listdir(root)):
            for p in sorted(glob.glob(os.path.join(root, fam, '*.pddl')),
                            key=lambda x: natural(os.path.basename(x))):
                level = os.path.basename(p).split('-')[0]
                tasks.append(('b6/%s/%s' % (fam, level),
                              os.path.join(here, 'b6', 'domains', fam + '.pddl'), p))
    if name == 'combat':
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'combat')
        for part in ('scenarios', 'mini', 'large'):
            for p in sorted(glob.glob(os.path.join(root, part, '*.pddl')),
                            key=lambda x: natural(os.path.basename(x))):
                tasks.append(('combat/' + part, os.path.join(root, 'domain.pddl'), p))
    if name in ('classical', 'quick'):
        for label, a, b in classical_domains():
            if b is None:
                tasks += [(label, d, p) for d, p in pick(a, per)]
            else:
                tasks += [(label, a, p) for p in pick(b, per)]
    return tasks


def run_popf(popf, kairos, task, timeout, memory):
    """POPF on a task; solved only if Kairos validates its plan."""
    label, domain, problem = task
    t0 = time.perf_counter()
    try:
        # The memory of a cgroup: POPF links OpenBLAS, which reserves address space at start
        # (ulimit -v kills it before it begins)
        r = subprocess.run(['systemd-run', '--user', '--scope', '-q', '-p',
                            'MemoryMax=%dM' % memory, '-p', 'MemorySwapMax=0',
                            popf, domain, problem], capture_output=True, text=True,
                           timeout=timeout)
        out, hung = r.stdout, False
    except subprocess.TimeoutExpired:
        out, hung = '', True
    wall = time.perf_counter() - t0
    row = {'domain': label, 'problem': os.path.basename(problem), 'status': 'timeout',
           'time': '%.3f' % wall, 'steps': '', 'cost': '', 'expanded': ''}
    if hung or ';;;; Solution Found' not in out:
        if not hung:
            row['status'] = 'unsolvable' if 'unsolvable' in out.lower() else 'error'
        return row
    body = out.split(';;;; Solution Found', 1)[1]
    keep(task, body)
    with tempfile.NamedTemporaryFile('w', suffix='.plan', delete=False) as f:
        f.write(body)
        plan = f.name
    v = subprocess.run([kairos, 'validate', domain, problem, plan], capture_output=True,
                       text=True)
    os.unlink(plan)
    row['status'] = 'solved' if v.returncode == 0 else 'invalid'
    row['steps'] = str(len(re.findall(r'^\s*[\d.]+:\s*\(', body, re.MULTILINE)))
    mk = re.search(r'makespan ([\d.]+)', v.stderr)
    row['cost'] = mk.group(1) if mk else ''
    return row


KEEP = None  # --keep-plans: directory where each plan is kept (label/problem.plan)


def keep(task, text):
    if KEEP and text:
        d = os.path.join(KEEP, task[0])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, os.path.basename(task[2]) + '.plan'), 'w') as f:
            f.write(text)


PLANUTILS_IMAGE = 'kairos/planutils:benchmark'

# Inside the container: the planner on copies in the working directory (Apptainer only sees
# it, $HOME and /tmp), its time, then the last plan it wrote (files of TFD, LPG-TD, Fast
# Downward) or its stdout
PLANUTILS_SCRIPT = r"""
export PATH=/root/.planutils/bin:$PATH
mkdir -p /tmp/run && cd /tmp/run && cp /in/domain.pddl /in/problem.pddl .
start=$(date +%s%N)
timeout -s KILL {timeout} {command} > stdout.txt 2>&1
code=$?
echo "@@time $(( ($(date +%s%N) - start) / 1000000 ))"
echo "@@code $code"
# The last file with steps (LPG-TD sometimes leaves lpg_plan.SOL with only its header)
last=""
for f in $(ls -1 output_plan* *.SOL sas_plan* problem.pddl.plan 2>/dev/null | sort -V -r); do
  if grep -qE '^ *([0-9.]+: *)?[(]' "$f"; then last=$f; break; fi
done
if [ -n "$last" ]; then echo "@@file $last"; cat "$last"; else cat stdout.txt; fi
"""


# Planners whose planutils wrapper hides the plan: LPG-TD runs with -noout and keeps only the
# action names, so its binary writes the plan file itself
PLANUTILS_COMMANDS = {
    'lpg-td': '/root/.planutils/packages/lpg-td/bin/lpg-td -o domain.pddl -f problem.pddl '
              '-quality -cputime {timeout} -out lpg_plan',
    # Its wrapper passes the arguments as they come: ENHSP wants -o and -f
    'enhsp-2020': 'enhsp-2020 -o domain.pddl -f problem.pddl -planner sat-hmrphj',
    # FF's search (its default, A*epsilon, needs a metric): the support probes
    'metric-ff-s0': 'metric-ff domain.pddl problem.pddl -s 0',
}
UP_IMAGE = 'kairos/up:benchmark'  # up/Dockerfile: TAMER and Aries through unified-planning
# sota/Dockerfile: IPC 2023 winners and other recent planners, built from source (sota:NAME)
SOTA_IMAGE = 'kairos/sota:benchmark'


def last_plan(lines, step):
    """The last of several plans printed one after the other, separated by other lines (TFD
    prints each plan found, then "Rescheduled Plan:" and that one, then the plan file). The
    steps of a plan need not be sorted by time: TFD prints one elevator's, then the other's."""
    blocks = [[]]
    for ln in lines:
        if step.match(ln):
            blocks[-1].append(ln)
        elif blocks[-1]:
            blocks.append([])
    return next((b for b in reversed(blocks) if b), [])


def plan_text(planner, out):
    """The last plan in what a planner printed, in a form kairos validate reads."""
    if planner == 'sota:powerlifted':
        # "1: (load-truck p t c ) ;[created objects: ]": numbered steps of a sequential plan
        return '\n'.join(re.sub(r'^\s*\d+:\s*', '', ln.split(';', 1)[0]).strip()
                         for ln in out.splitlines())
    # POPF: ";;;; Solution Found" before its plan; OPTIC: "; Plan found with metric X" before
    # each better one
    if '@@status' in out:                     # up/run_up.py: its plan follows
        return out.split('@@status', 1)[1].split('\n', 1)[-1]
    marks = [m.end() for m in re.finditer(r';;;; Solution Found|; Plan found with metric', out)]
    if marks:
        return out[marks[-1]:]
    steps = re.findall(r'^\s*step\s+\d+:\s*(.+)$', out, re.MULTILINE | re.IGNORECASE)
    if steps:                                 # Metric-FF: "step 0: MOVE A B"
        return ''.join('(%s)\n' % st.strip().lower() for st in steps)
    if 'Found Plan:' in out:                  # ENHSP
        body = out.split('Found Plan:', 1)[1]
        return '\n'.join(ln for ln in body.splitlines() if re.match(r'^\s*[\d.]+:\s*\(', ln))
    if out.lstrip().startswith('@@file'):     # a plan file: timed or sequential lines
        return out
    # Stdout without a plan marker (TFD): only timed steps, never stray "(...)" lines of a
    # planner that printed no plan (OPTIC prints facts); other lines stay as blank separators
    return '\n'.join(ln if re.match(r'^\s*\d+(\.\d+)?:\s*\(', ln) else ''
                     for ln in out.splitlines())


def run_planutils(planner, kairos, task, timeout, memory):
    """A planutils planner on a task, again (up to twice) if it fails at once: LPG-TD now and
    then writes no plan although it found one."""
    row = run_planutils_once(planner, kairos, task, timeout, memory)
    for _ in range(2):
        if row['status'] != 'error' or float(row['time']) >= 1.0:
            break
        row = run_planutils_once(planner, kairos, task, timeout, memory)
    return row


def run_planutils_once(planner, kairos, task, timeout, memory):
    """A planutils planner on a task; solved only if Kairos validates its plan."""
    label, domain, problem = task
    image = PLANUTILS_IMAGE
    if planner.startswith('up:'):
        image = UP_IMAGE
        command = 'python /run_up.py %s domain.pddl problem.pddl' % planner[3:]
    elif planner.startswith('sota:'):
        image = SOTA_IMAGE
        command = 'env KAIROS_TIMEOUT=%d KAIROS_JAVA_MEMORY=%dm /run-planner/%s domain.pddl problem.pddl' % (
            int(timeout), max(512, memory - 512), planner[5:])
    else:
        command = PLANUTILS_COMMANDS.get(planner, planner + ' domain.pddl problem.pddl').format(
            timeout=int(timeout))
    script = PLANUTILS_SCRIPT.format(timeout=int(timeout), command=command)
    if not (os.path.isfile(domain) and os.path.isfile(problem)):
        return {'domain': label, 'problem': os.path.basename(problem), 'status': 'error',
                'time': '0.000', 'steps': '', 'cost': '', 'expanded': ''}
    # --mount, not -v: -v creates a root-owned directory for a path that does not exist (it
    # turned a missing domain.pddl of the corpus into one)
    cmd = ['docker', 'run', '--rm', '--privileged', '--memory=%dm' % memory,
           '--memory-swap=%dm' % memory, '--cpus=1',
           '--mount', 'type=bind,src=%s,dst=/in/domain.pddl,readonly' % os.path.abspath(domain),
           '--mount', 'type=bind,src=%s,dst=/in/problem.pddl,readonly' % os.path.abspath(problem),
           image, 'bash', '-c', script]
    try:
        # Some planners print bytes that are not UTF-8 (Metric-FF)
        r = subprocess.run(cmd, capture_output=True, text=True, errors='replace',
                           timeout=timeout + 120)
        out = r.stdout
    except subprocess.TimeoutExpired:
        out = ''
    wall = re.search(r'^@@time (\d+)', out, re.MULTILINE)
    row = {'domain': label, 'problem': os.path.basename(problem), 'status': 'error',
           'time': '%.3f' % (int(wall.group(1)) / 1000.0 if wall else timeout), 'steps': '',
           'cost': '', 'expanded': ''}
    body = plan_text(planner, out.split('@@code', 1)[-1].split('\n', 1)[-1])
    # Only steps: anytime planners print their search progress after each plan
    step = re.compile(r'^\s*(\d+(\.\d+)?:\s*)?(\([^()]+\)|@PlanEND)\s*(\[[\d.]+\])?\s*$')
    lines = last_plan(body.splitlines(), step)
    if not lines:
        code = re.search(r'^@@code (\d+)', out, re.MULTILINE)
        killed = code and code.group(1) in ('124', '137')
        # Killed before the timeout: the memory limit of the container
        early = wall and int(wall.group(1)) / 1000.0 < timeout - 1.0
        row['status'] = ('memory' if early else 'timeout') if killed else 'error'
        # A crash (signal, or the shell's report of one), not a rejection
        crashed = code and 129 <= int(code.group(1)) <= 254 and code.group(1) != '137'
        # An uncaught exception that rejects the input (NextFLAP's parser) is not a crash
        rejected = 'terminate called after throwing' in out
        if not killed and not rejected and (crashed or re.search(
                r'Segmentation fault|core dumped|double free|Aborted', out)):
            row['status'] = 'crash'
        return row
    keep(task, '\n'.join(lines) + '\n')
    with tempfile.NamedTemporaryFile('w', suffix='.plan', delete=False) as f:
        f.write('\n'.join(lines) + '\n')
        plan = f.name
    v = subprocess.run([kairos, 'validate', domain, problem, plan], capture_output=True,
                       text=True)
    os.unlink(plan)
    row['status'] = 'solved' if v.returncode == 0 else 'invalid'
    row['steps'] = str(len(lines))
    cost = re.search(r'metric ([\d.e+-]+)', v.stderr) or re.search(r'makespan ([\d.]+)', v.stderr)
    row['cost'] = cost.group(1) if cost else row['steps']
    return row


def run_one(kairos, task, timeout, memory, extra, anytime=False):
    label, domain, problem = task
    # Kairos's own limit is not a safety net (a bug once grew one run to 43 GB): a cgroup too
    cap = ['systemd-run', '--user', '--scope', '-q', '-p', 'MemoryMax=%dM' % (memory + 512),
           '-p', 'MemorySwapMax=0']
    cmd = cap + [kairos, domain, problem] + ([] if anytime else ['--no-anytime']) + [
        '--timeout', str(timeout), '--memory', str(memory), '-v'] + extra
    t0 = time.perf_counter()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30)
        code, err, out = r.returncode, r.stderr, r.stdout
    except subprocess.TimeoutExpired:
        code, err, out = -1, '', ''
    wall = time.perf_counter() - t0
    first = re.search(r'first plan ([\d.]+) ms', err)
    if anytime and first and float(first.group(1)) >= 0:
        wall = float(first.group(1)) / 1000.0  # agile: when the first plan came
    expanded = re.search(r'(\d+) expanded', err)
    # Killed (-9, or 137 through a shell): the cgroup's memory cap came before Kairos's limit
    status = {0: 'solved', 10: 'unsolvable', 11: 'timeout', 12: 'memory', 13: 'unsupported',
              14: 'noplan', 2: 'invalid', 1: 'error', -1: 'hung', -9: 'memory',
              137: 'memory'}.get(code, 'error')
    if code == 0:
        keep(task, out)
    steps = len([ln for ln in out.splitlines() if ln.startswith('(')]) if code == 0 else ''
    costs = re.findall(r'; makespan = ([\d.e+-]+)', out) or re.findall(r'; cost = ([\d.e+-]+)', out)
    ground = re.search(r'ground ([\d.]+) ms', err)
    actions = re.search(r'kairos: \d+ atoms, (\d+) actions', err)
    peak = re.search(r'(\d+) MB peak', err)
    return {'domain': label, 'problem': os.path.basename(problem), 'status': status,
            'time': '%.3f' % wall, 'steps': steps, 'cost': costs[-1] if costs else '',
            'expanded': expanded.group(1) if expanded else '',
            'ground_ms': ground.group(1) if ground else '',
            'actions': actions.group(1) if actions else '', 'peak_mb': peak.group(1) if peak else ''}


def agile(row, timeout):
    if row['status'] != 'solved':
        return 0.0
    t = float(row['time'])
    return 1.0 if t <= 1.0 else max(0.0, 1.0 - math.log(t) / math.log(timeout))


def summary(rows, timeout):
    by = {}
    for r in rows:
        by.setdefault(r['domain'], []).append(r)
    total_s = total_n = 0
    total_a = 0.0
    print('| domain | solved | agile |')
    print('|---|---|---|')
    for d in sorted(by):
        rs = by[d]
        s = sum(1 for r in rs if r['status'] == 'solved')
        a = sum(agile(r, timeout) for r in rs)
        total_s += s
        total_n += len(rs)
        total_a += a
        print('| %s | %d/%d | %.2f |' % (d, s, len(rs), a))
    print('| **total** | **%d/%d** | **%.2f** |' % (total_s, total_n, total_a))


def cmd_run(args, extra):
    global KEEP
    KEEP = args.keep_plans and os.path.abspath(args.keep_plans)
    tasks = suite(args.suite)
    if args.only:
        tasks = [t for t in tasks if re.search(args.only, t[0])]
    kairos = os.path.abspath(args.kairos)
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        if args.planutils:
            futures = [pool.submit(run_planutils, args.planutils, kairos, t, args.timeout,
                                   args.memory) for t in tasks]
        elif args.popf:
            popf = os.path.abspath(args.popf)
            futures = [pool.submit(run_popf, popf, kairos, t, args.timeout, args.memory)
                       for t in tasks]
        else:
            futures = [pool.submit(run_one, kairos, t, args.timeout, args.memory, extra,
                                   args.anytime) for t in tasks]
        for i, f in enumerate(concurrent.futures.as_completed(futures)):
            rows.append(f.result())
            if (i + 1) % 20 == 0:
                print('%d/%d' % (i + 1, len(tasks)), file=sys.stderr, flush=True)
    rows.sort(key=lambda r: (r['domain'], natural(r['problem'])))
    with open(args.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print('# timeout %g s, extra args: %s' % (args.timeout, ' '.join(extra) or '(none)'))
    summary(rows, args.timeout)


def cmd_compare(args):
    def load(path):
        with open(path) as f:
            return {(r['domain'], r['problem']): r for r in csv.DictReader(f)}
    a, b = load(args.base), load(args.new)
    keys = sorted(set(a) & set(b), key=lambda k: (k[0], natural(k[1])))
    by = {}
    for k in keys:
        by.setdefault(k[0], []).append(k)
    t = args.timeout
    def quality(k, mine, other):
        # IPC quality: the best cost of the two over this one's (minimizing; 0 if unsolved)
        if mine[k]['status'] != 'solved' or not mine[k]['cost']:
            return 0.0
        costs = [float(r[k]['cost']) for r in (mine, other)
                 if r[k]['status'] == 'solved' and r[k]['cost']]
        c = float(mine[k]['cost'])
        return 1.0 if c <= 0 else min(costs) / c
    print('| domain | solved base | solved new | agile base | agile new | quality base | '
          'quality new | expanded (both solved) |')
    print('|---|---|---|---|---|---|---|---|')
    tot = [0, 0, 0.0, 0.0, 0.0, 0.0]
    for d in sorted(by):
        ks = by[d]
        sa = sum(1 for k in ks if a[k]['status'] == 'solved')
        sb = sum(1 for k in ks if b[k]['status'] == 'solved')
        aa = sum(agile(a[k], t) for k in ks)
        ab = sum(agile(b[k], t) for k in ks)
        both = [k for k in ks if a[k]['status'] == b[k]['status'] == 'solved' and
                a[k]['expanded'] and b[k]['expanded']]
        ea = sum(int(a[k]['expanded']) for k in both)
        eb = sum(int(b[k]['expanded']) for k in both)
        ratio = '%.2fx' % (eb / ea) if ea else '-'
        qa = sum(quality(k, a, b) for k in ks)
        qb = sum(quality(k, b, a) for k in ks)
        tot = [tot[0] + sa, tot[1] + sb, tot[2] + aa, tot[3] + ab, tot[4] + qa, tot[5] + qb]
        mark = ' (+)' if sb > sa else ' (-)' if sb < sa else ''
        print('| %s | %d | %d%s | %.2f | %.2f | %.2f | %.2f | %s |' % (
            d, sa, sb, mark, aa, ab, qa, qb, ratio))
    print('| **total** | **%d** | **%d** | **%.2f** | **%.2f** | **%.2f** | **%.2f** | |' %
          tuple(tot))


def main():
    argv = sys.argv[1:]
    extra = []
    if '--' in argv:
        extra = argv[argv.index('--') + 1:]
        argv = argv[:argv.index('--')]
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run')
    r.add_argument('kairos')
    r.add_argument('suite', choices=['b1', 'b2', 'b3', 'classical', 'quick', 'examples', 'b6', 'combat', 'pddlplus', 'probes',
                            'durations', 'htg', 'features',
                                            'prefs'])
    r.add_argument('--popf', help='run this POPF binary instead (plans validated by KAIROS)')
    r.add_argument('--planutils', help='run this planutils planner instead, in a container '
                   '(plans validated by KAIROS); up:tamer and up:aries run TAMER and Aries of '
                   'unified-planning (image of up/Dockerfile)')
    r.add_argument('--anytime', action='store_true',
                   help='let Kairos improve until the timeout (cost: the last plan)')
    r.add_argument('--out', required=True)
    r.add_argument('--only', help='only the domains whose label matches this regular expression')
    r.add_argument('--timeout', type=float, default=30.0)
    r.add_argument('--memory', type=int, default=2048)
    r.add_argument('--jobs', type=int, default=6)
    r.add_argument('--keep-plans', help='keep each plan in this directory (label/problem.plan)')
    c = sub.add_parser('compare')
    c.add_argument('base')
    c.add_argument('new')
    c.add_argument('--timeout', type=float, default=30.0)
    args = ap.parse_args(argv)
    if args.command == 'run':
        cmd_run(args, extra)
    else:
        cmd_compare(args)


if __name__ == '__main__':
    main()
