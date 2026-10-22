#!/usr/bin/env python3
"""F0 baseline report: Kairos against the planners of planutils, from bench/results/f0/*.csv.

Usage: f0_report.py [RESULTS_DIR] > report.md

Per suite: solved by each planner, the IPC quality score (best cost among the planners that
solved a problem / own cost, 0 if unsolved) and, per domain, where some planner solves more
than Kairos. Costs are the metric, or the makespan, or the number of steps: all lower is better
in these suites.
"""

import csv
import glob
import os
import sys
from collections import defaultdict

SUITES = [('examples', 'docs/examples (robotics)'), ('b2', 'B2: required concurrency, temporal numeric'),
          ('b1', 'B1: temporal, IPC 2002-2014'), ('b3', 'B3: numeric, IPC 2002/2023/2026'),
          ('classical', 'classical, IPC 1998-2023')]


def load(path):
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            rows[(r['domain'], r['problem'])] = r
    return rows


def cost(r):
    if r is None or r['status'] != 'solved':
        return None
    try:
        return float(r['cost'])
    except (TypeError, ValueError):
        return None


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__),
                                                         'results', 'f0')
    runs = defaultdict(dict)  # suite -> planner -> rows
    for path in glob.glob(os.path.join(d, '*.csv')):
        name = os.path.basename(path)[:-4]
        planner, suite = name.rsplit('_', 1)
        runs[suite][planner] = load(path)
    print('# F0 baseline: Kairos and other planners\n')
    print('30 s and 3 GB per problem, one CPU, every plan validated by Kairos. Kairos anytime '
          '(its best plan within the time); the others as planutils runs them.\n')
    for suite, title in SUITES:
        if suite not in runs:
            continue
        planners = sorted(runs[suite], key=lambda p: (p != 'kairos', p))
        tasks = sorted(set().union(*[set(r) for r in runs[suite].values()]))
        best = {}
        for t in tasks:
            cs = [c for c in (cost(runs[suite][p].get(t)) for p in planners) if c is not None]
            best[t] = min(cs) if cs else None
        print('## %s (%d problems)\n' % (title, len(tasks)))
        print('| planner | solved | quality (IPC score) | invalid plans |')
        print('|---|---:|---:|---:|')
        for p in planners:
            rows = runs[suite][p]
            solved = sum(1 for t in tasks if cost(rows.get(t)) is not None or
                         (rows.get(t) or {}).get('status') == 'solved')
            q = 0.0
            for t in tasks:
                c = cost(rows.get(t))
                if c is not None and best[t] is not None:
                    q += 1.0 if c <= 0 else min(1.0, best[t] / c) if best[t] > 0 else 1.0
            invalid = sum(1 for t in tasks if (rows.get(t) or {}).get('status') == 'invalid')
            print('| %s | %d | %.1f | %d |' % (p, solved, q, invalid))
        # Domains where another planner solves more than Kairos
        if 'kairos' in runs[suite]:
            by_domain = defaultdict(lambda: defaultdict(int))
            for t in tasks:
                for p in planners:
                    if (runs[suite][p].get(t) or {}).get('status') == 'solved':
                        by_domain[t[0]][p] += 1
            worse = []
            for dom in sorted({t[0] for t in tasks}):
                k = by_domain[dom]['kairos']
                others = {p: n for p, n in by_domain[dom].items() if p != 'kairos' and n > k}
                if others:
                    worse.append((dom, k, others))
            if worse:
                print('\nDomains where another planner solves more than Kairos:\n')
                print('| domain | Kairos | better |')
                print('|---|---:|---|')
                for dom, k, others in worse:
                    print('| %s | %d | %s |' % (dom, k, ', '.join(
                        '%s %d' % (p, n) for p, n in sorted(others.items(), key=lambda x: -x[1]))))
        print()


if __name__ == '__main__':
    main()
