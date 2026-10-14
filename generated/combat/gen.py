#!/usr/bin/env python3
# Writes the combat scenarios: python3 gen.py [OUTDIR], by default into the package
import sys
from pathlib import Path

GRID = [['n_west', 'n_mid', 'n_east'],
        ['c_west', 'c_mid', 'c_east'],
        ['s_west', 's_mid', 's_east']]
ZONES = [z for row in GRID for z in row]
CPS = ['n_mid', 'c_mid', 's_mid']
BASE = 'c_west'

# type, speed, ammo, value, op_cost, shot_cost
KINDS = {
    'drone': (None, 0, 5000, 50, 0),
    'infantry': (1.0, 5, 20000, 100, 10),
    'tank': (0.5, 4, 150000, 500, 300),
    'artillery': (0.4, 3, 80000, 300, 1000),
}
ARMY = {'d1': 'drone', 'i1': 'infantry', 'i2': 'infantry', 't1': 'tank', 'a1': 'artillery'}


def edges():
    out = []
    for r in range(3):
        for c in range(3):
            for dr, dc in ((0, 1), (1, 0)):
                if r + dr < 3 and c + dc < 3:
                    a, b = GRID[r][c], GRID[r + dr][c + dc]
                    out += [(a, b), (b, a)]
    return out


def problem(name, army=None, at=None, enemies=None, explored=(BASE,), goal=None,
            battery=100, metric='(spent)', ammo=None, extra_init=()):
    army = dict(ARMY if army is None else army)
    at = at or {}
    enemies = enemies or {}
    objs = {}
    for r, k in list(army.items()) + [(e, k) for e, (k, _) in enemies.items()]:
        objs.setdefault(k, []).append(r)
    init = []
    for r, k in army.items():
        speed, a, value, op, shot = KINDS[k]
        init += [f'(mine {r})', f'(available {r})', f'(at {r} {at.get(r, BASE)})',
                 f'(= (value {r}) {value})', f'(= (op_cost {r}) {op})',
                 f'(= (shot_cost {r}) {shot})', f'(= (ammo {r}) {(ammo or {}).get(r, a)})']
        if speed:
            init.append(f'(= (speed {r}) {speed})')
        if k == 'drone':
            init.append(f'(= (battery {r}) {battery})')
    for e, (k, z) in enemies.items():
        init += [f'(hostile {e})', f'(at {e} {z})']
    init += [f'(connected {a} {b})' for a, b in edges()]
    init += [f'(= (distance {a} {b}) 10)' for a, b in edges()]
    init += [f'(explored {z})' for z in explored]
    init += [f'(control_point {z})' for z in CPS] + [f'(base {BASE})', '(= (spent) 0)']
    init += list(extra_init)
    goal = goal or [f'(owned {z})' for z in CPS]
    objects = '\n    '.join(' '.join(v) + f' - {k}' for k, v in objs.items())
    return f"""(define (problem {name})
  (:domain combat)
  (:objects
    {' '.join(ZONES)} - zone
    {objects})
  (:init
    {chr(10).join('    ' + i for i in init).strip()})
  (:goal (and {' '.join(goal)}))
  (:metric minimize {metric}))
"""


DEFENSE = {'e_inf1': ('infantry', 'c_mid'), 'e_tank1': ('tank', 'n_mid'),
           'e_art1': ('artillery', 'c_east')}

SCENARIOS = {
    # Nothing known but the base.
    's1_fog': dict(),
    # Same, optimizing time instead of euros.
    's1b_fog_time': dict(metric='(total-time)'),
    # Everything surveyed: infantry in c_mid, tank in n_mid, artillery behind in c_east.
    's2_known_defense': dict(explored=ZONES, enemies=DEFENSE),
    # Same defense, and every enemy must be destroyed.
    's3_total_victory': dict(explored=ZONES, enemies=DEFENSE,
                             goal=[f'(owned {z})' for z in CPS] +
                             [f'(destroyed {e})' for e in DEFENSE]),
    # No tank of ours: the enemy tank in n_mid only falls to artillery spotted by the drone.
    's4_no_tank': dict(explored=ZONES, enemies=DEFENSE,
                       army={k: v for k, v in ARMY.items() if k != 't1'}),
    # Drone almost empty: it has to recharge before helping.
    's5_low_battery': dict(explored=ZONES, enemies=DEFENSE, battery=12,
                           army={k: v for k, v in ARMY.items() if k != 't1'}),
    # Both infantry lost: no one can capture.
    's6_no_infantry': dict(explored=ZONES, enemies=DEFENSE,
                           army={k: v for k, v in ARMY.items() if not k.startswith('i')}),
    # Replanning after s2 started: i1 entered s_mid blind and met an enemy infantry there,
    # t1 missed in n_mid (e_tank1 still alive), c_mid already ours.
    's7_replan': dict(explored=ZONES, at={'i1': 's_mid', 'i2': 'c_mid', 't1': 'n_mid',
                                          'a1': 'c_west', 'd1': 'c_west'},
                      enemies={'e_tank1': ('tank', 'n_mid'), 'e_inf2': ('infantry', 's_mid'),
                               'e_art1': ('artillery', 'c_east')},
                      ammo={'t1': 3, 'i1': 5, 'i2': 4},
                      extra_init=['(owned c_mid)']),
}

# Euros plus 100 euros per second
MIXED = '(+ (spent) (* 100 (total-time)))'
MIXED_SCENARIOS = ['s1_fog', 's2_known_defense', 's3_total_victory', 's7_replan']
PACKAGE = (Path(__file__).resolve().parent.parent /
           'src/ros2_planning_system_examples/plansys2_combat_example/pddl/problems')

if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else PACKAGE
    out.mkdir(parents=True, exist_ok=True)
    for name, kw in SCENARIOS.items():
        (out / f'{name}.pddl').write_text(problem(name, **kw))
    for name in MIXED_SCENARIOS:
        kw = dict(SCENARIOS[name], metric=MIXED)
        (out / f'{name}_mixed.pddl').write_text(problem(f'{name}_mixed', **kw))
