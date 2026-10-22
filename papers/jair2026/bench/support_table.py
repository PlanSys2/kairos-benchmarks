#!/usr/bin/env python3
"""The support table of the paper from the probes runs of bench/paper_battery.sh support.

A feature is supported if the planner solves, with a plan Kairos's validator accepts, a probe
that uses it: its own probe, the probe's @durative variant (planners that only plan with
durative actions), or another probe whose :requirements name it (durative actions and numeric
fluents appear in several). For preferences the plan must also satisfy the preference.

  bench/support_table.py KAIROS RESULTS_DIR [--latex]
"""
import csv
import os
import re
import subprocess
import sys

PLANNERS = ['lama', 'powerlifted', 'metric-ff-s0', 'enhsp', 'popf', 'optic', 'tfd', 'lpg-td',
            'nextflap', 'smtplan', 'kairos']
NAMES = ['LAMA', 'Powerlifted', 'Metric-FF', 'ENHSP', 'POPF', 'OPTIC', 'TFD', 'LPG-td',
         'NextFLAP', 'SMTPlan+', r'\sys']
FEATURES = [
    ('conditional-effects', 'conditional effects'),
    ('quantified-preconditions', 'quantified preconditions'),
    ('disjunctive-preconditions', 'disjunctive preconditions'),
    ('derived-predicates', 'derived predicates'),
    ('numeric-fluents', 'numeric fluents'),
    ('non-linear-numeric', 'non-linear numeric conditions'),
    ('object-fluents', 'object fluents'),
    ('durative-actions', 'durative actions'),
    ('required-concurrency', 'required concurrency'),
    ('duration-inequalities', 'duration inequalities'),
    ('timed-initial-literals', 'timed initial literals'),
    ('timed-initial-fluents', 'timed initial fluents'),
    ('continuous-effects', 'linear continuous effects'),
    ('processes-events', 'processes and events'),
    ('non-linear-continuous', 'non-linear continuous change'),
    ('preferences', 'preferences'),
    ('trajectory-constraints', 'trajectory constraints'),
]
PROBES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probes')
# Requirements that name a feature of the table
FLAGS = {':durative-actions': 'durative-actions', ':fluents': 'numeric-fluents'}


def uses(probe):
    """The features a probe exercises: its own and those its requirements name."""
    feats = {probe.split('@')[0]}
    with open(os.path.join(PROBES, probe, 'domain.pddl')) as f:
        req = re.search(r'\(:requirements([^)]*)\)', f.read()).group(1).split()
    return feats | {FLAGS[r] for r in req if r in FLAGS}


def metric(kairos, probe, plan):
    v = subprocess.run([kairos, 'validate', os.path.join(PROBES, probe, 'domain.pddl'),
                        os.path.join(PROBES, probe, 'problem.pddl'), plan],
                       capture_output=True, text=True)
    m = re.search(r'metric ([\d.e+-]+)', v.stderr)
    return float(m.group(1)) if v.returncode == 0 and m else None


def satisfied(kairos, res, run, probe):
    plan = os.path.join(res, 'plans_%s' % run, 'probes', probe, 'problem.pddl.plan')
    return os.path.exists(plan) and metric(kairos, probe, plan) == 0


SYMBOL = {'yes': r'\yes', 'partial': r'\half', 'no': r'\no'}
TEXT = {'yes': '✓', 'partial': '◐', 'no': '✗'}


def main():
    kairos, res = sys.argv[1], sys.argv[2]
    cells = {}
    for p in PLANNERS:
        # A planner with several configurations: the best of them for each probe
        runs = {'enhsp': ['enhsp', 'enhsp-pddlplus']}.get(p, [p])
        rows, plans = {}, {}
        for run in runs:
            for r in csv.DictReader(open(os.path.join(res, '%s_probes.csv' % run))):
                probe = r['domain'].split('/', 1)[1]
                if rows.get(probe) != 'solved':
                    rows[probe], plans[probe] = r['status'], run
        for feat, _ in FEATURES:
            # Its own probes (and their @durative variants), then any probe that uses it
            own = [q for q in rows if q.split('@')[0] == feat]
            good = [q for q in rows if rows[q] == 'solved' and feat in uses(q)]
            if feat == 'preferences':
                good = [q for q in good if satisfied(kairos, res, plans[q], q)]
            if any(q in own for q in good):
                cells[p, feat] = 'yes'
            elif good or any(rows[q] in ('invalid', 'crash') for q in own):
                cells[p, feat] = 'partial'
            else:
                cells[p, feat] = 'no'
    if '--latex' in sys.argv:
        print('Feature & ' + ' & '.join(NAMES) + r' \\')
        for feat, label in FEATURES:
            print(label + ' & ' + ' & '.join(SYMBOL[cells[p, feat]] for p in PLANNERS) + r' \\')
        print('supported & ' + ' & '.join(
            str(sum(cells[p, f] == 'yes' for f, _ in FEATURES)) for p in PLANNERS) + r' \\')
        return
    print('| feature | ' + ' | '.join(PLANNERS) + ' |')
    print('|---|' + '---|' * len(PLANNERS))
    for feat, label in FEATURES:
        print('| %s | %s |' % (label, ' | '.join(TEXT[cells[p, feat]] for p in PLANNERS)))
    print('| supported | %s |' % ' | '.join(
        str(sum(cells[p, f] == 'yes' for f, _ in FEATURES)) for p in PLANNERS))


if __name__ == '__main__':
    main()
