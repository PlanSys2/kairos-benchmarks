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

"""Larger combat problems: bigger maps and armies with more robots of every kind.

    gen_large.py OUT_DIR [--seeds 2]

Maps of 3x3 to 6x6 zones (4 neighbours, 10 m apart), our base in the middle of the west side,
the control points down the middle column. Our army at four sizes (drones, infantry, tanks,
artillery): small 1/3/1/1, medium 2/5/2/2, large 3/8/3/3, huge 4/12/4/4. Enemies of the three
ground kinds, about as many as our ground robots, at random zones (seeded). Variants:
  known  everything surveyed, take every control point
  total  also destroy every enemy
  fog    only the base surveyed (no enemy known yet), take every control point
  mixed  known, with the metric euros + 100 per second
Costs, speeds and ammunition are those of gen.py (the example's generator).
"""

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen import KINDS  # noqa: E402

SIZES = {'small': (1, 3, 1, 1), 'medium': (2, 5, 2, 2), 'large': (3, 8, 3, 3),
         'huge': (4, 12, 4, 4)}
MAPS = {'small': 3, 'medium': 4, 'large': 5, 'huge': 6}
MIXED = '(+ (spent) (* 100 (total-time)))'


def grid(n):
    names = [[f'z{r}_{c}' for c in range(n)] for r in range(n)]
    edges = []
    for r in range(n):
        for c in range(n):
            for dr, dc in ((0, 1), (1, 0)):
                if r + dr < n and c + dc < n:
                    a, b = names[r][c], names[r + dr][c + dc]
                    edges += [(a, b), (b, a)]
    base = names[n // 2][0]
    cps = [names[r][n // 2] for r in range(n)]
    return [z for row in names for z in row], edges, base, cps


def problem(name, size, variant, rnd):
    n = MAPS[size]
    zones, edges, base, cps = grid(n)
    drones, inf, tanks, art = SIZES[size]
    army = {}
    for kind, count, prefix in (('drone', drones, 'd'), ('infantry', inf, 'i'),
                                ('tank', tanks, 't'), ('artillery', art, 'a')):
        for k in range(count):
            army[f'{prefix}{k + 1}'] = kind
    # Enemies: as many as our ground robots, half infantry, then tanks and artillery
    ground = inf + tanks + art
    kinds = (['infantry'] * (ground // 2) + ['tank'] * (ground // 4) +
             ['artillery'] * (ground - ground // 2 - ground // 4))
    away = [z for z in zones if z != base]
    enemies = {f'e{k + 1}': (kind, rnd.choice(away)) for k, kind in enumerate(kinds)}
    known = variant != 'fog'
    objs = {}
    for r, k in army.items():
        objs.setdefault(k, []).append(r)
    if known:
        for e, (k, _) in enemies.items():
            objs.setdefault(k, []).append(e)
    init = []
    for r, k in army.items():
        speed, ammo, value, op, shot = KINDS[k]
        init += [f'(mine {r})', f'(available {r})', f'(at {r} {base})',
                 f'(= (value {r}) {value})', f'(= (op_cost {r}) {op})',
                 f'(= (shot_cost {r}) {shot})', f'(= (ammo {r}) {ammo})']
        if speed:
            init.append(f'(= (speed {r}) {speed})')
        if k == 'drone':
            init.append('(= (battery {}) 100)'.format(r))
    if known:
        for e, (k, z) in enemies.items():
            init += [f'(hostile {e})', f'(at {e} {z})']
    init += [f'(connected {a} {b})' for a, b in edges]
    init += [f'(= (distance {a} {b}) 10)' for a, b in edges]
    init += [f'(explored {z})' for z in (zones if known else [base])]
    init += [f'(control_point {z})' for z in cps] + [f'(base {base})', '(= (spent) 0)']
    goal = [f'(owned {z})' for z in cps]
    if variant == 'total':
        goal += [f'(destroyed {e})' for e in enemies]
    metric = MIXED if variant == 'mixed' else '(spent)'
    objects = '\n    '.join(' '.join(v) + f' - {k}' for k, v in objs.items())
    body = '\n    '.join(init)
    return f"""(define (problem {name})
  (:domain combat)
  (:objects
    {' '.join(zones)} - zone
    {objects})
  (:init
    {body})
  (:goal (and {' '.join(goal)}))
  (:metric minimize {metric}))
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('out')
    ap.add_argument('--seeds', type=int, default=2)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        for variant in ('known', 'total', 'fog', 'mixed'):
            for seed in range(1, args.seeds + 1):
                rnd = random.Random(f'{size}-{variant}-{seed}')
                name = f'{size}_{variant}_{seed}'
                (out / f'{name}.pddl').write_text(problem(name, size, variant, rnd))


if __name__ == '__main__':
    main()
