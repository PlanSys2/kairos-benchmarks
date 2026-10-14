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

"""B6: PlanSys2 problems scaled from a handful of objects to tens of thousands.

Each family takes the domain of a PlanSys2 package (domains/, copied unchanged) and generates
problems at the levels XS (~10 objects), S (~50), M (~200), L (~1000), XL (~5000) and
XXL (~20000), with several seeds per level. Generation is deterministic (seeded), and every
problem comes with a reference plan built along with it, so it is solvable by construction
(check.py validates the reference plans with kairos validate).

    gen.py OUT_DIR [--levels XS,S,M] [--seeds 3] [--families patrol,charging]

writes OUT_DIR/FAMILY/LEVEL-SEED.pddl (problem) and .plan (reference plan); the domain is
domains/FAMILY.pddl.
"""

import argparse
import collections
import heapq
import math
import os
import random
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LEVELS = collections.OrderedDict(
    [('XS', 10), ('S', 50), ('M', 200), ('L', 1000), ('XL', 5000), ('XXL', 20000)])
EPS = 0.01  # between the end of a step and the start of the next one in a reference plan


class Grid:
    """Waypoints on a grid with 4-neighbour corridors in both directions. Without full, some
    corridors are left out, but never one of a random spanning tree (it stays connected)."""

    def __init__(self, n, rnd, prefix, full=False, weights=None):
        self.w = max(1, int(math.ceil(math.sqrt(n))))
        self.names = ['%s%d' % (prefix, i) for i in range(n)]
        self.n = n
        cells = [(i % self.w, i // self.w) for i in range(n)]
        index = {c: i for i, c in enumerate(cells)}
        edges = set()
        for i, (x, y) in enumerate(cells):
            for c in ((x + 1, y), (x, y + 1)):
                if c in index:
                    edges.add((i, index[c]))
        keep = set(edges) if full else self.tree(edges, rnd) | {
            e for e in sorted(edges) if rnd.random() < 0.6}
        self.adj = [[] for _ in range(n)]
        self.dist = {}
        for a, b in sorted(keep):
            d = rnd.randint(*weights) if weights else 1
            for u, v in ((a, b), (b, a)):
                self.adj[u].append(v)
                self.dist[(u, v)] = d
        self.cells = cells

    def tree(self, edges, rnd):
        parent = list(range(self.n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        order = sorted(edges)
        rnd.shuffle(order)
        out = set()
        for a, b in order:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
                out.add((a, b))
        return out

    def connected_facts(self, pred):
        return ['(%s %s %s)' % (pred, self.names[u], self.names[v])
                for u in range(self.n) for v in self.adj[u]]

    def dijkstra(self, src, stop=None):
        """Distances and parents from src; stops at the first node with stop(node)."""
        dist = {src: 0}
        parent = {src: None}
        heap = [(0, src)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            if stop and stop(u):
                return dist, parent, u
            for v in self.adj[u]:
                nd = d + self.dist[(u, v)]
                if nd < dist.get(v, math.inf):
                    dist[v] = nd
                    parent[v] = u
                    heapq.heappush(heap, (nd, v))
        return dist, parent, None

    def path(self, src, dst):
        _, parent, found = self.dijkstra(src, lambda u: u == dst)
        assert found is not None, 'disconnected grid'
        return unwind(parent, dst)

    def nearest(self, src, targets):
        """The nearest of targets and the path to it (src itself if it is one)."""
        _, parent, found = self.dijkstra(src, lambda u: u in targets)
        assert found is not None, 'no target reachable'
        return found, unwind(parent, found)


def unwind(parent, node):
    out = []
    while node is not None:
        out.append(node)
        node = parent[node]
    return out[::-1]


class Timeline:
    """The steps of a reference plan, each agent one after the other (agents in parallel)."""

    def __init__(self, temporal=True):
        self.steps = []
        self.clock = collections.defaultdict(float)
        self.temporal = temporal

    def add(self, agent, action, duration=0.0):
        t = self.clock[agent]
        self.steps.append((t, action, duration))
        self.clock[agent] = t + duration + EPS

    def text(self):
        if not self.temporal:
            return ''.join('(%s)\n' % a for _, a, _ in self.steps)
        return ''.join('%.3f: (%s) [%.3f]\n' % s for s in sorted(self.steps, key=lambda s: s[0]))


def problem(name, domain, objects, init, goal, metric=None):
    """A problem in the layout of the PlanSys2 problem expert."""
    obj = ''.join('    %s - %s\n' % (' '.join(names), t) for t, names in objects if names)
    out = '(define (problem %s)\n  (:domain %s)\n  (:objects\n%s  )\n  (:init\n' % (
        name, domain, obj)
    out += ''.join('    %s\n' % f for f in init)
    out += '  )\n  (:goal (and\n' + ''.join('    %s\n' % g for g in goal) + '  ))\n'
    if metric:
        out += '  (:metric %s)\n' % metric
    return out + ')\n'


def split(n, *shares):
    """n objects in parts, at least 1 each, the last one takes the rest."""
    parts = [max(1, int(n * s)) for s in shares]
    return parts + [max(1, n - sum(parts))]


# ---------------------------------------------------------------- families


def gen_patrol(n, rnd):
    robots = 1 + n // 200
    g = Grid(max(2, n - robots), rnd, 'wp')
    rob = ['r%d' % i for i in range(robots)]
    goals = sorted(rnd.sample(range(g.n), max(1, g.n // 5)))
    start = [rnd.randrange(g.n) for _ in rob]
    init = ['(robot_at %s %s)' % (r, g.names[s]) for r, s in zip(rob, start)]
    init += g.connected_facts('connected')
    plan = Timeline()
    tours(g, rob, start, goals,
          lambda r, u: plan.add(r, 'patrol %s %s' % (r, g.names[u]), 5),
          lambda r, u, v: plan.add(r, 'move %s %s %s' % (r, g.names[u], g.names[v]), 5))
    return (problem('patrol_b6', 'patrol', [('robot', rob), ('waypoint', g.names)], init,
                    ['(patrolled %s)' % g.names[u] for u in goals]), plan)


def tours(g, robots, start, goals, visit, move):
    """Each goal to the robot whose start is nearest (by grid cell), each robot visiting its
    goals greedily, nearest first."""
    mine = collections.defaultdict(set)
    for u in goals:
        cx, cy = g.cells[u]
        best = min(range(len(robots)), key=lambda i: abs(g.cells[start[i]][0] - cx) +
                   abs(g.cells[start[i]][1] - cy))
        mine[best].add(u)
    for i, r in enumerate(robots):
        at, todo = start[i], mine[i]
        while todo:
            nxt, p = g.nearest(at, todo)
            for u, v in zip(p, p[1:]):
                move(r, u, v)
            visit(r, nxt)
            todo.discard(nxt)
            at = nxt


def gen_simple(n, rnd):
    robots = 1 + n // 1000
    chargers = 1 + n // 2000
    g = Grid(max(2, n - robots), rnd, 'room')
    rob = ['r%d' % i for i in range(robots)]
    charging = set(rnd.sample(range(g.n), min(chargers, g.n)))
    start = [rnd.randrange(g.n) for _ in rob]
    target = [rnd.randrange(g.n) for _ in rob]
    full = [rnd.random() < 0.5 for _ in rob]
    init = ['(robot_at %s %s)' % (r, g.names[s]) for r, s in zip(rob, start)]
    init += ['(%s %s)' % ('battery_full' if f else 'battery_low', r) for r, f in zip(rob, full)]
    init += ['(charging_point_at %s)' % g.names[c] for c in sorted(charging)]
    init += g.connected_facts('connected')
    plan = Timeline()
    for r, s, t, f in zip(rob, start, target, full):
        if not f:
            c = min(charging)
            plan.add(r, 'askcharge %s %s %s' % (r, g.names[s], g.names[c]), 5)
            plan.add(r, 'charge %s %s' % (r, g.names[c]), 5)
            s = c
        p = g.path(s, t)
        for u, v in zip(p, p[1:]):
            plan.add(r, 'move %s %s %s' % (r, g.names[u], g.names[v]), 5)
    return (problem('simple_b6', 'simple', [('robot', rob), ('room', g.names)], init,
                    ['(robot_at %s %s)' % (r, g.names[t]) for r, t in zip(rob, target)]), plan)


class Energy:
    """A robot or car that spends energy on each corridor and refills at some waypoints. The
    walker keeps enough energy to reach the nearest refill point from wherever it is."""

    def __init__(self, g, refill, cost, low, refill_step):
        self.g, self.refill, self.cost, self.low, self.refill_step = g, refill, cost, low, \
            refill_step
        self.to_refill = multi_source(g, refill)

    def walk(self, agent, at, level, goal, move):
        for _ in range(4 * self.g.n + 10):
            if at == goal:
                return at, level
            p = self.g.path(at, goal)
            for u, v in zip(p, p[1:]):
                spend = self.cost(u, v)
                if level - spend - self.cost_to_refill(v) < self.low:
                    break
                move(agent, u, v)
                level -= spend
                at = v
            if at == goal:
                return at, level
            # Not enough to go on: to the nearest refill point, refill, and try again
            c, back = self.g.nearest(at, self.refill)
            for u, v in zip(back, back[1:]):
                move(agent, u, v)
                level -= self.cost(u, v)
            assert level >= self.low - 1e-9, 'reference walker ran out of energy'
            at = c
            level = self.refill_step(agent, at, level)
        raise AssertionError('reference walker did not reach its goal')

    def cost_to_refill(self, u):
        return self.to_refill[u]


def multi_source(g, sources):
    """Cheapest energy (distance) from each waypoint to the nearest of sources."""
    dist = {s: 0 for s in sources}
    heap = [(0, s) for s in sources]
    heapq.heapify(heap)
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v in g.adj[u]:
            nd = d + g.dist[(v, u)]
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def spaced(g, every):
    """Waypoints on a sublattice of the grid, every 'every' cells (at least one)."""
    out = {i for i, (x, y) in enumerate(g.cells) if x % every == 0 and y % every == 0}
    return out or {0}


def gen_charging(n, rnd):
    robots = 1 + n // 500
    g = Grid(max(2, n - robots), rnd, 'wp', full=True, weights=(1, 5))
    rob = ['r%d' % i for i in range(robots)]
    chargers = spaced(g, 4)
    start = [rnd.choice(sorted(chargers)) for _ in rob]
    goals = sorted(rnd.sample(range(g.n), max(1, g.n // 10)))
    init = ['(robot_at %s %s)' % (r, g.names[s]) for r, s in zip(rob, start)]
    init += ['(charger_at %s)' % g.names[c] for c in sorted(chargers)]
    init += g.connected_facts('connected')
    init += ['(= (distance %s %s) %d)' % (g.names[u], g.names[v], d)
             for (u, v), d in sorted(g.dist.items())]
    for r in rob:
        init += ['(= (speed %s) 1)' % r, '(= (max_range %s) 100)' % r,
                 '(= (state_of_charge %s) 100)' % r]
    plan = Timeline()

    def move(r, u, v):
        plan.add(r, 'move %s %s %s' % (r, g.names[u], g.names[v]), g.dist[(u, v)])

    def charge(r, u, level):
        plan.add(r, 'charge %s %s' % (r, g.names[u]), 5)
        return 100.0
    en = Energy(g, chargers, lambda u, v: float(g.dist[(u, v)]), 0.0, charge)
    level = {r: 100.0 for r in rob}
    at = dict(zip(rob, start))

    order = assign_order(g, rob, start, goals)
    for r in rob:
        for u in order[r]:
            at[r], level[r] = en.walk(r, at[r], level[r], u, move)
            plan.add(r, 'patrol %s %s' % (r, g.names[u]), 5)
    return (problem('charging_b6', 'charging', [('robot', rob), ('waypoint', g.names)], init,
                    ['(patrolled %s)' % g.names[u] for u in goals]), plan)


def assign_order(g, robots, start, goals):
    """The goals of each robot in the order a greedy nearest-first tour visits them."""
    order = collections.defaultdict(list)
    tours(g, robots, start, goals, lambda r, u: order[r].append(u), lambda r, u, v: None)
    return order


def gen_road_trip(n, rnd):
    cars = 1 + n // 1000
    g = Grid(max(2, n - cars), rnd, 'wp', full=True, weights=(1, 5))
    car = ['car%d' % i for i in range(cars)]
    stations = spaced(g, 4)
    start = [rnd.choice(sorted(stations)) for _ in car]
    goals = sorted(rnd.sample(range(g.n), max(1, g.n // 10)))
    init = ['(car_at %s %s)' % (c, g.names[s]) for c, s in zip(car, start)]
    init += ['(fuel_at %s)' % g.names[s] for s in sorted(stations)]
    init += g.connected_facts('connected')
    init += ['(= (distance %s %s) %d)' % (g.names[u], g.names[v], d)
             for (u, v), d in sorted(g.dist.items())]
    for c in car:
        init += ['(= (fuel_level %s) 1.0)' % c, '(= (min_fuel_level %s) 0.1)' % c,
                 '(= (range %s) 100)' % c, '(= (fuel_rate %s) 0.1)' % c,
                 '(= (speed %s) 1)' % c]
    plan = Timeline()

    def move(c, u, v):
        plan.add(c, 'move %s %s %s' % (c, g.names[u], g.names[v]), g.dist[(u, v)])

    def refuel(c, u, level):
        # (fuel in hundredths): duration (1 - fuel) / rate
        plan.add(c, 'refuel %s %s' % (c, g.names[u]), (100.0 - level) / 100.0 / 0.1)
        return 100.0
    # Fuel in hundredths: a move needs more than min (10) + its cost left; a margin of 1 on
    # top keeps the strict comparison and the rounding of the decreases safe
    en = Energy(g, stations, lambda u, v: float(g.dist[(u, v)]), 11.0, refuel)
    level = {c: 100.0 for c in car}
    at = dict(zip(car, start))
    order = assign_order(g, car, start, goals)
    for c in car:
        for u in order[c]:
            at[c], level[c] = en.walk(c, at[c], level[c], u, move)
            plan.add(c, 'visit %s %s' % (c, g.names[u]), 1.0)
    return (problem('road_trip_b6', 'road_trip', [('car', car), ('waypoint', g.names)], init,
                    ['(visited %s)' % g.names[u] for u in goals]), plan)


def gen_elevator(n, rnd):
    floors = max(3, int(math.sqrt(n)))
    lifts = 1 + n // 2000
    people = max(1, n - floors - lifts)
    fl = ['f%d' % i for i in range(floors)]
    li = ['e%d' % i for i in range(lifts)]
    pe = ['p%d' % i for i in range(people)]
    origin = [rnd.randrange(floors) for _ in pe]
    dest = [(o + rnd.randrange(1, floors)) % floors for o in origin]
    init = ['(lift_at %s %s)' % (e, fl[0]) for e in li]
    init += ['(passenger_at %s %s)' % (p, fl[o]) for p, o in zip(pe, origin)]
    init += ['(next %s %s)' % (fl[i], fl[i + 1]) for i in range(floors - 1)]
    init += ['(= (floor_distance %s %s) %d)' % (fl[i], fl[i + 1], 3)
             for i in range(floors - 1)]
    init += ['(= (floor_distance %s %s) %d)' % (fl[i + 1], fl[i], 3)
             for i in range(floors - 1)]
    lift_speed = {e: rnd.choice((1, 2, 3)) for e in li}
    speed = {p: rnd.choice((1, 2)) for p in pe}
    init += ['(= (elevator_speed %s) %d)' % (e, lift_speed[e]) for e in li]
    init += ['(= (person_speed %s) %d)' % (p, speed[p]) for p in pe]
    plan = Timeline()
    # Each lift sweeps up, then down: boards and leaves its passengers on the way (SCAN)
    for k, e in enumerate(li):
        mine = [i for i in range(people) if i % lifts == k]
        up = [i for i in mine if dest[i] > origin[i]]
        down = [i for i in mine if dest[i] < origin[i]]
        d = 3.0 / lift_speed[e]
        for f in range(floors):
            serve(plan, e, fl, pe, speed, up, origin, dest, f)
            if f + 1 < floors:
                plan.add(e, 'move-up %s %s %s' % (e, fl[f], fl[f + 1]), d)
        for f in range(floors - 1, -1, -1):
            serve(plan, e, fl, pe, speed, down, origin, dest, f)
            if f > 0:
                plan.add(e, 'move-down %s %s %s' % (e, fl[f], fl[f - 1]), d)
    return (problem('elevator_b6', 'temporal-elevators',
                    [('elevator', li), ('passenger', pe), ('num', fl)], init,
                    ['(passenger_at %s %s)' % (p, fl[d]) for p, d in zip(pe, dest)]), plan)


def serve(plan, e, fl, pe, speed, group, origin, dest, f):
    for i in group:
        if dest[i] == f:
            plan.add(e, 'leave %s %s %s' % (pe[i], fl[f], e), speed[pe[i]])
    for i in group:
        if origin[i] == f:
            plan.add(e, 'board %s %s %s' % (pe[i], fl[f], e), speed[pe[i]])


COOK_TYPES = ['egg', 'oil', 'salt', 'flour', 'sugar', 'pasta', 'water']
RECIPES = {'omelette': ['egg', 'oil', 'salt'], 'cake': ['flour', 'egg', 'sugar'],
           'spaghetti': ['water', 'pasta', 'oil', 'salt']}


def gen_cooking(n, rnd):
    robots = 1 + n // 5000
    per_type = 1 + n // 10000
    kitchens = 1 + n // 5000
    zones = ['kitchen%d' % i for i in range(kitchens)] + [
        'pantry', 'fridge', 'watertap', 'recharge']
    store = {'egg': 'fridge', 'oil': 'pantry', 'salt': 'pantry', 'flour': 'pantry',
             'sugar': 'pantry', 'pasta': 'pantry', 'water': 'watertap'}
    ing = [('%s%d' % (t, i), t) for t in COOK_TYPES for i in range(per_type)]
    dishes = max(1, n - robots - len(zones) - len(ing))
    kinds = sorted(RECIPES)
    di = [('%s%d' % (kinds[i % 3], i), kinds[i % 3]) for i in range(dishes)]
    rob = ['r%d' % i for i in range(robots)]
    full = [i % 2 == 0 for i in range(robots)]
    start = [rnd.choice(zones) for _ in rob]
    init = ['(robot_at %s %s)' % (r, z) for r, z in zip(rob, start)]
    init += ['(battery_full %s)' % r for r, f in zip(rob, full) if f]
    init += ['(ingredient_at %s %s)' % (i, store[t]) for i, t in ing]
    init += ['(is_%s %s)' % (t, i) for i, t in ing]
    init += ['(is_%s %s)' % (k, d) for d, k in di]
    init += ['(is_cooking_zone %s)' % z for z in zones if z.startswith('kitchen')]
    init += ['(is_pantry_zone pantry)', '(is_fridge_zone fridge)',
             '(is_watertap_zone watertap)', '(is_recharge_zone recharge)']
    plan = Timeline()
    r, at = rob[0], start[0]
    if not full[0]:
        if at != 'recharge':
            plan.add(r, 'move %s %s recharge' % (r, at), 5)
        plan.add(r, 'recharge %s recharge' % r, 5)
        at = 'recharge'
    first = {t: '%s0' % t for t in COOK_TYPES}
    for t in COOK_TYPES:
        if at != store[t]:
            plan.add(r, 'move %s %s %s' % (r, at, store[t]), 5)
        plan.add(r, 'transport %s %s %s kitchen0' % (r, first[t], store[t]), 5)
        at = 'kitchen0'
    for d, k in di:
        args = ' '.join(first[t] for t in RECIPES[k])
        plan.add(r, 'cook_%s %s kitchen0 %s %s' % (k, r, args, d), 5)
    return (problem('cooking_b6', 'cooking',
                    [('robot', rob), ('zone', zones), ('ingredient', [i for i, _ in ing]),
                     ('dish', [d for d, _ in di])], init,
                    ['(dish_prepared %s)' % d for d, _ in di]), plan)


def gen_factory(n, rnd):
    robots = 1 + n // 1000
    zones_n = 2 + n // 200
    cars = max(1, (n - robots - zones_n) // 4)
    zones = ['z%d' % i for i in range(zones_n)]
    assembly = zones[:1 + n // 2000]
    rob = ['r%d' % i for i in range(robots)]
    ca = ['car%d' % i for i in range(cars)]
    kinds = [('wheel', 'piece_is_wheel'), ('body', 'piece_is_body_car'),
             ('steering', 'piece_is_steering_wheel')]
    pieces = [('%s%d' % (k, i), pred) for i in range(cars) for k, pred in kinds]
    where = {p: rnd.choice(zones) for p, _ in pieces}
    start = [rnd.choice(zones) for _ in rob]
    init = ['(robot_at %s %s)' % (r, z) for r, z in zip(rob, start)]
    init += ['(robot_available %s)' % r for r in rob] + ['(battery_full %s)' % r for r in rob]
    init += ['(piece_at %s %s)' % (p, where[p]) for p, _ in pieces]
    init += ['(%s %s)' % (pred, p) for p, pred in pieces]
    init += ['(piece_not_used %s)' % p for p, _ in pieces]
    init += ['(is_assembly_zone %s)' % z for z in assembly]
    plan = Timeline(temporal=False)
    r, at, a = rob[0], start[0], assembly[0]
    for p, _ in pieces:
        if where[p] == a:
            continue
        if at != where[p]:
            plan.add(r, 'move %s %s %s' % (r, at, where[p]))
        plan.add(r, 'transport %s %s %s %s' % (r, p, where[p], a))
        at = a
    if at != a:
        plan.add(r, 'move %s %s %s' % (r, at, a))
    for i, c in enumerate(ca):
        plan.add(r, 'assemble %s %s wheel%d body%d steering%d %s' % (r, a, i, i, i, c))
    return (problem('factory_b6', 'factory',
                    [('robot', rob), ('zone', zones), ('piece', [p for p, _ in pieces]),
                     ('car', ca)], init, ['(car_assembled %s)' % c for c in ca]), plan)


def suave_statics():
    """The facts of the PlanSys2 suave problem that describe the robot's architecture."""
    path = os.path.join(HERE, '..', '..', 'src', 'kairos', 'tests', 'data', 'plansys2',
                        'plansys2_executor__suave_problem.pddl')
    with open(path) as f:
        text = f.read()
    text = re.sub(r';[^\n]*', '', text)
    body = text.split('(:init', 1)[1].split('(:goal', 1)[0]
    facts = re.findall(r'\([^()]*\)', body)
    return [f for f in facts if not f.startswith('(robot_not_started')]


def gen_suave(n, rnd):
    robots = 1 + n // 1000
    decimals = ['0.0_decimal', '0.25_decimal', '0.5_decimal', '0.75_decimal', '1.0_decimal',
                '1.25_decimal', '2.25_decimal', '3.25_decimal']
    pipes = max(1, n - robots - len(decimals) - 36)
    rob = ['auv%d' % i for i in range(robots)]
    pi = ['pipeline%d' % i for i in range(pipes)]
    init = ['(robot_not_started %s)' % r for r in rob] + suave_statics()
    plan = Timeline(temporal=False)
    for r in rob:
        plan.add(r, 'start_robot %s' % r)
    plan.add(rob[0], 'reconfigure1 f_maintain_motion fd_all_thrusters')
    plan.add(rob[0], 'reconfigure1 f_generate_search_path fd_spiral_high')
    for k, p in enumerate(pi):
        plan.add(rob[0], 'search_pipeline %s %s' % (p, rob[k % robots]))
    plan.add(rob[0], 'reconfigure1 f_follow_pipeline fd_follow_pipeline')
    plan.add(rob[0], 'reconfigure2 f_generate_search_path fd_spiral_high fd_unground')
    for k, p in enumerate(pi):
        plan.add(rob[0], 'inspect_pipeline %s %s' % (p, rob[k % robots]))
    goal = ['(robot_started %s)' % r for r in rob]
    goal += ['(pipeline_found %s)' % p for p in pi] + ['(pipeline_inspected %s)' % p for p in pi]
    return (problem('suave_b6', 'suave', [('pipeline', pi), ('robot', rob),
                                           ('numerical-object', decimals)], init, goal), plan)


FAMILIES = collections.OrderedDict([
    ('patrol', gen_patrol), ('simple', gen_simple), ('charging', gen_charging),
    ('road_trip', gen_road_trip), ('elevator', gen_elevator), ('cooking', gen_cooking),
    ('factory', gen_factory), ('suave', gen_suave)])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('out')
    ap.add_argument('--levels', default=','.join(LEVELS))
    ap.add_argument('--seeds', type=int, default=3)
    ap.add_argument('--families', default=','.join(FAMILIES))
    args = ap.parse_args()
    for fam in args.families.split(','):
        os.makedirs(os.path.join(args.out, fam), exist_ok=True)
        for level in args.levels.split(','):
            for seed in range(1, args.seeds + 1):
                rnd = random.Random('%s-%s-%d' % (fam, level, seed))
                text, plan = FAMILIES[fam](LEVELS[level], rnd)
                base = os.path.join(args.out, fam, '%s-%d' % (level, seed))
                with open(base + '.pddl', 'w') as f:
                    f.write(text)
                with open(base + '.plan', 'w') as f:
                    f.write(plan.text())


if __name__ == '__main__':
    main()
