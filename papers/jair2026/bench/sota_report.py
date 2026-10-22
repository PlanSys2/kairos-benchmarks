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

"""Kairos against every planner measured: problems solved in 100 ms, 1 s and the whole limit.

    sota_report.py [RESULTS_DIR]        (bench/results by default)

The short columns need the time of the first plan: Kairos reports it; planners that stop at
their first plan (POPF, ENHSP, Metric-FF, LNM-Plan, lama-first, the agile IPC 2023
configurations, DecStar agile, Dual-BFWS) take that long. Anytime runs (LAMA, OPTIC, TFD, LPG-td,
NextFLAP, the satisficing IPC 2023 configurations) only show when they stopped: "-" there.

Packaging is not the planner's: planutils runs POPF, ENHSP-2020 and SMTPlan+ in Apptainer,
started cold for each problem. POPF's times lose 0.189 s and SMTPlan+'s 0.185 s (their whole
time on a one-action problem, run the same way: the most favourable reading), ENHSP-2020's
0.084 s (Apptainer's cold start alone; the JVM is ENHSP's). The planners of bench/sota run without Apptainer, and times are taken inside
the container, so Docker's start does not count for anyone. Kairos's first-plan time leaves
out its process start (about 5 ms).
"""

# Seconds of packaging per planner (see above)
OFFSET = {'POPF': 0.189, 'ENHSP-2020': 0.084, 'SMTPlan+': 0.185}

import csv
import os
import sys

R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'results')

# suite: [(planner, csv relative to R, first-plan times)]
SUITES = {
    'Classical (220)': [
        ('Kairos', 'sota/kairos_classical.csv', True),
        ('LAMA (anytime)', 'f0/lama_classical.csv', False),
        ('lama-first', 'sota/lama-first_classical.csv', True),
        ('Scorpion Maidu', 'sota/maidu_classical.csv', False),
        ('Scorpion Maidu agile', 'sota/maidu-agl_classical.csv', True),
        ('Levitron', 'sota/levitron_classical.csv', False),
        ('Levitron agile', 'sota/levitron-agl_classical.csv', True),
        ('FD Stone Soup 2023', 'sota/fdss_classical.csv', False),
        ('FD Stone Soup 2023 agile', 'sota/fdss-agl_classical.csv', True),
        ('DecStar 2023 (agile)', 'sota/decstar_classical.csv', True),
        ('Dual-BFWS', 'sota/dual-bfws_classical.csv', True),
    ],
    'B3: numeric (420)': [
        ('Kairos', 'sota/kairos_b3.csv', True),
        ('ENHSP (current)', 'sota/enhsp_b3.csv', True),
        ('ENHSP-2020', 'f0/enhsp-2020_b3.csv', True),
        ('LNM-Plan', 'sota/lnm_b3.csv', True),
        ('Metric-FF', 'f0/metric-ff_b3.csv', True),
    ],
    'B1: temporal (225)': [
        ('Kairos', 'sota/kairos_b1.csv', True),
        ('POPF', 'f0/popf_b1.csv', True),
        ('OPTIC', 'f0/optic_b1.csv', False),
        ('TFD', 'f0/tfd_b1.csv', False),
        ('LPG-td', 'f0/lpg-td_b1.csv', False),
        ('NextFLAP', 'sota/nextflap_b1.csv', False),
    ],
    'B2: required concurrency, temporal numeric (55)': [
        ('Kairos', 'sota/kairos_b2.csv', True),
        ('POPF', 'f0/popf_b2.csv', True),
        ('OPTIC', 'f0/optic_b2.csv', False),
        ('TFD', 'f0/tfd_b2.csv', False),
        ('LPG-td', 'f0/lpg-td_b2.csv', False),
        ('NextFLAP', 'sota/nextflap_b2.csv', False),
    ],
    'Robotics examples': [
        ('Kairos', 'sota/kairos_examples.csv', True),
        ('POPF', 'f0/popf_examples.csv', True),
        ('OPTIC', 'f0/optic_examples.csv', False),
        ('TFD', 'f0/tfd_examples.csv', False),
        ('LPG-td', 'f0/lpg-td_examples.csv', False),
        ('NextFLAP', 'sota/nextflap_examples.csv', False),
    ],
    'PDDL3: IPC 2006 preferences and constraints (125)': [
        ('Kairos', 'prefs/kairos_step26.csv', True),
        ('POPF', 'prefs/popf.csv', True),
        ('OPTIC', 'prefs/optic.csv', False),
        ('NextFLAP', 'sota/nextflap_prefs.csv', False),
    ],
    'PDDL+: hstairs and SMTPlan benchmarks (255; 30 s, 3 GB)': [
        ('Kairos', 'pddlplus/kairos.csv', True),
        ('ENHSP (current, sat-hadd, steps of 0.1 s)', 'pddlplus/enhsp.csv', True),
        ('SMTPlan+', 'pddlplus/smtplan.csv', True),
    ],
    'B6: PlanSys2 problems at scale (144; 60 s, 2 GB)': [
        ('Kairos', 'sota/kairos_b6.csv', True),
        ('POPF', 'b6/popf.csv', True),
        ('OPTIC', 'b6/optic.csv', False),
        ('TFD', 'b6/tfd.csv', False),
        ('TAMER (unified-planning)', 'b6/up_tamer.csv', True),
        ('Aries (unified-planning)', 'b6/up_aries.csv', False),
    ],
}


def counts(path, short, offset=0.0):
    rows = [r for r in csv.DictReader(open(path)) if r['status'] == 'solved']
    times = [max(0.0, float(r['time']) - offset) for r in rows]
    if not short:
        return '-', '-', len(rows), len(list(csv.DictReader(open(path))))
    return (sum(t <= 0.1 for t in times), sum(t <= 1.0 for t in times), len(rows),
            len(list(csv.DictReader(open(path)))))


def main():
    for suite, planners in SUITES.items():
        print(f'\n### {suite}\n')
        print('| Planner | 100 ms | 1 s | whole limit |')
        print('|---|---:|---:|---:|')
        nominal = None
        for name, rel, short in planners:
            path = os.path.join(R, rel)
            if not os.path.exists(path):
                print(f'| {name} | | | not run |')
                continue
            a, b, c, n = counts(path, short, OFFSET.get(name, 0.0))
            nominal = nominal or n
            bold = '**' if name == 'Kairos' else ''
            of = f' (of {n})' if n != nominal else ''
            print(f'| {bold}{name}{bold} | {a} | {b} | {c}{of} |')


if __name__ == '__main__':
    main()
