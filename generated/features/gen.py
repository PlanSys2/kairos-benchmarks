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

"""Generated part of the feature bank: families for features the public corpora lack (object
fluents, timed initial fluents) and a robotic warehouse with up to hundreds of robots.

  gen.py OUT_DIR
Writes OUT_DIR/FEATURE/FAMILY/{domain.pddl, pNN.pddl} and OUT_DIR/manifest.json, which says
for each problem whether it has a plan (each family has unsolvable problems too: a planner
that says "unsolvable" on a solvable one, or prints a plan for an unsolvable one, is wrong).
"""

import json
import os
import random
import sys

MANIFEST = []


def write(out, feature, family, domain, problems):
    folder = os.path.join(out, feature, family)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, 'domain.pddl'), 'w') as fh:
        fh.write(domain)
    for i, (text, solvable) in enumerate(problems, 1):
        name = 'p%02d.pddl' % i
        with open(os.path.join(folder, name), 'w') as fh:
            fh.write(text)
        MANIFEST.append({'feature': feature, 'family': family,
                         'domain': os.path.join(folder, 'domain.pddl'),
                         'problem': os.path.join(folder, name), 'solvable': solvable})


def line(names, rel):
    """rel facts linking consecutive names both ways."""
    return ' '.join('(%s %s %s) (%s %s %s)' % (rel, a, b, rel, b, a)
                    for a, b in zip(names, names[1:]))


# --- Object fluents -------------------------------------------------------------------------

DELIVERY = '''(define (domain delivery-of)
  (:requirements :typing :object-fluents :negative-preconditions)
  (:types robot location package)
  (:predicates (connected ?a ?b - location))
  (:functions (loc ?r - robot) - location (pos ?p - package) - location
              (carrying ?r - robot) - package)
  (:action move
    :parameters (?r - robot ?from ?to - location)
    :precondition (and (= (loc ?r) ?from) (connected ?from ?to))
    :effect (assign (loc ?r) ?to))
  (:action pick
    :parameters (?r - robot ?p - package ?l - location)
    :precondition (and (= (loc ?r) ?l) (= (pos ?p) ?l) (not (= (carrying ?r) ?p)))
    :effect (and (assign (carrying ?r) ?p) (assign (pos ?p) undefined)))
  (:action drop
    :parameters (?r - robot ?p - package ?l - location)
    :precondition (and (= (loc ?r) ?l) (= (carrying ?r) ?p))
    :effect (and (assign (carrying ?r) undefined) (assign (pos ?p) ?l))))
'''


def delivery(rng, robots, packages, locs, solvable):
    L = ['l%d' % i for i in range(locs)]
    island = [] if solvable else ['island']  # a package where no road goes
    init = [line(L, 'connected')]
    init += ['(= (loc r%d) %s)' % (i, rng.choice(L)) for i in range(robots)]
    goal = []
    for p in range(packages):
        a, b = rng.sample(L, 2)
        if not solvable and p == 0:
            a = 'island'
        init.append('(= (pos p%d) %s)' % (p, a))
        goal.append('(= (pos p%d) %s)' % (p, b))
    return '''(define (problem delivery-%d-%d-%d) (:domain delivery-of)
  (:objects %s - robot %s - location %s - package)
  (:init %s)
  (:goal (and %s)))
''' % (robots, packages, locs, ' '.join('r%d' % i for i in range(robots)), ' '.join(L + island),
       ' '.join('p%d' % i for i in range(packages)), '\n    '.join(init), ' '.join(goal))


ELEVATOR = '''(define (domain elevator-of)
  (:requirements :typing :object-fluents :negative-preconditions)
  (:types elevator floor passenger)
  (:predicates (above ?a ?b - floor) (served ?p - passenger) (serves ?e - elevator ?f - floor))
  (:functions (floor-of ?e - elevator) - floor (dest ?p - passenger) - floor
              (waiting ?p - passenger) - floor (inside ?p - passenger) - elevator)
  (:action up
    :parameters (?e - elevator ?from ?to - floor)
    :precondition (and (= (floor-of ?e) ?from) (above ?to ?from) (serves ?e ?to))
    :effect (assign (floor-of ?e) ?to))
  (:action down
    :parameters (?e - elevator ?from ?to - floor)
    :precondition (and (= (floor-of ?e) ?from) (above ?from ?to) (serves ?e ?to))
    :effect (assign (floor-of ?e) ?to))
  (:action board
    :parameters (?p - passenger ?e - elevator ?f - floor)
    :precondition (and (= (floor-of ?e) ?f) (= (waiting ?p) ?f))
    :effect (and (assign (waiting ?p) undefined) (assign (inside ?p) ?e)))
  (:action leave
    :parameters (?p - passenger ?e - elevator ?f - floor)
    :precondition (and (= (floor-of ?e) ?f) (= (inside ?p) ?e) (= (dest ?p) ?f))
    :effect (and (assign (inside ?p) undefined) (served ?p))))
'''


def elevator(rng, elevators, floors, passengers, solvable):
    F = ['f%d' % i for i in range(floors)]
    init = ['(above %s %s)' % (F[j], F[i]) for i in range(floors) for j in range(i + 1, floors)]
    # Each elevator serves every floor but the top one, which only the first serves
    for e in range(elevators):
        for i, f in enumerate(F):
            if i < floors - 1 or (e == 0 and solvable):
                init.append('(serves e%d %s)' % (e, f))
        init.append('(= (floor-of e%d) f0)' % e)
    goal = []
    for p in range(passengers):
        a, b = rng.sample(F, 2)
        if p == 0:
            b = F[-1]  # unsolvable when no elevator serves the top floor
        init.append('(= (waiting q%d) %s) (= (dest q%d) %s)' % (p, a, p, b))
        goal.append('(served q%d)' % p)
    return '''(define (problem elevator-%d-%d-%d) (:domain elevator-of)
  (:objects %s - elevator %s - floor %s - passenger)
  (:init %s)
  (:goal (and %s)))
''' % (elevators, floors, passengers, ' '.join('e%d' % i for i in range(elevators)), ' '.join(F),
       ' '.join('q%d' % i for i in range(passengers)), '\n    '.join(init), ' '.join(goal))


KEYS = '''(define (domain keys-of)
  (:requirements :typing :object-fluents :negative-preconditions)
  (:types robot room door key)
  (:predicates (joins ?d - door ?a ?b - room) (open ?d - door))
  (:functions (in ?r - robot) - room (holding ?r - robot) - key (key-at ?k - key) - room
              (opens ?d - door) - key)
  (:action unlock
    :parameters (?r - robot ?d - door ?a ?b - room)
    :precondition (and (= (in ?r) ?a) (joins ?d ?a ?b) (= (holding ?r) (opens ?d))
                       (not (open ?d)))
    :effect (open ?d))
  (:action go
    :parameters (?r - robot ?d - door ?a ?b - room)
    :precondition (and (= (in ?r) ?a) (joins ?d ?a ?b) (open ?d))
    :effect (assign (in ?r) ?b))
  (:action take
    :parameters (?r - robot ?k - key ?a - room)
    :precondition (and (= (in ?r) ?a) (= (key-at ?k) ?a))
    :effect (and (assign (key-at ?k) undefined) (assign (holding ?r) ?k)))
  (:action put
    :parameters (?r - robot ?k - key ?a - room)
    :precondition (and (= (in ?r) ?a) (= (holding ?r) ?k))
    :effect (and (assign (holding ?r) undefined) (assign (key-at ?k) ?a))))
'''


def keys(rng, rooms, solvable):
    # A corridor of rooms, door i between room i and i+1 opened by key i, which lies in a room
    # before it (unsolvable: one key lies behind its own door)
    R = ['room%d' % i for i in range(rooms)]
    init = ['(= (in bot) room0)']
    for i in range(rooms - 1):
        init.append('(joins d%d %s %s) (joins d%d %s %s) (= (opens d%d) k%d)' % (
            i, R[i], R[i + 1], i, R[i + 1], R[i], i, i))
        where = rng.randint(0, i)
        if not solvable and i == rooms // 2:
            where = i + 1
        init.append('(= (key-at k%d) %s)' % (i, R[where]))
    return '''(define (problem keys-%d) (:domain keys-of)
  (:objects bot - robot %s - room %s - door %s - key)
  (:init %s)
  (:goal (= (in bot) %s)))
''' % (rooms, ' '.join(R), ' '.join('d%d' % i for i in range(rooms - 1)),
       ' '.join('k%d' % i for i in range(rooms - 1)), '\n    '.join(init), R[-1])


DELIVERY_TIME = '''(define (domain delivery-of-time)
  (:requirements :typing :object-fluents :negative-preconditions :durative-actions
                 :numeric-fluents)
  (:types robot location package)
  (:predicates (connected ?a ?b - location) (idle ?r - robot))
  (:functions (loc ?r - robot) - location (pos ?p - package) - location
              (carrying ?r - robot) - package (dist ?a ?b - location))
  (:durative-action move
    :parameters (?r - robot ?from ?to - location)
    :duration (= ?duration (dist ?from ?to))
    :condition (and (at start (= (loc ?r) ?from)) (at start (idle ?r))
                    (over all (connected ?from ?to)))
    :effect (and (at start (not (idle ?r))) (at start (assign (loc ?r) undefined))
                 (at end (assign (loc ?r) ?to)) (at end (idle ?r))))
  (:durative-action pick
    :parameters (?r - robot ?p - package ?l - location)
    :duration (= ?duration 1)
    :condition (and (at start (idle ?r)) (over all (= (loc ?r) ?l)) (at start (= (pos ?p) ?l))
                    (at start (not (= (carrying ?r) ?p))))
    :effect (and (at start (not (idle ?r))) (at start (assign (pos ?p) undefined))
                 (at end (assign (carrying ?r) ?p)) (at end (idle ?r))))
  (:durative-action drop
    :parameters (?r - robot ?p - package ?l - location)
    :duration (= ?duration 1)
    :condition (and (at start (idle ?r)) (over all (= (loc ?r) ?l))
                    (at start (= (carrying ?r) ?p)))
    :effect (and (at start (not (idle ?r))) (at end (assign (carrying ?r) undefined))
                 (at end (assign (pos ?p) ?l)) (at end (idle ?r)))))
'''


def delivery_time(rng, robots, packages, locs, solvable):
    text = delivery(rng, robots, packages, locs, solvable)
    L = ['l%d' % i for i in range(locs)]
    dist = ' '.join('(= (dist %s %s) %d) (= (dist %s %s) %d)' % (a, b, d, b, a, d)
                    for (a, b), d in zip(zip(L, L[1:]), (rng.randint(2, 9) for _ in L)))
    idle = ' '.join('(idle r%d)' % i for i in range(robots))
    text = text.replace('(:domain delivery-of)', '(:domain delivery-of-time)')
    text = text.replace('(:init ', '(:init %s %s\n    ' % (idle, dist))
    return text.replace('(:goal', '(:metric minimize (total-time))\n  (:goal')


# --- Timed initial fluents ------------------------------------------------------------------

MARKET = '''(define (domain market-tif)
  (:requirements :typing :durative-actions :numeric-fluents :timed-initial-literals)
  (:types item)
  (:predicates (owned ?i - item))
  (:functions (price ?i - item) (money))
  (:durative-action buy
    :parameters (?i - item)
    :duration (= ?duration 1)
    :condition (and (at start (<= (price ?i) (money))))
    :effect (and (at start (decrease (money) (price ?i))) (at end (owned ?i)))))
'''


def market(rng, items, solvable):
    # Each price starts high and drops for a while: money only suffices buying at the drops
    init, goal, total = ['(= (money) MONEY)'], [], 0
    for i in range(items):
        high, low = rng.randint(50, 90), rng.randint(5, 15)
        t0 = rng.randint(2, 4 * items)
        init.append('(= (price i%d) %d) (at %d (= (price i%d) %d)) (at %d (= (price i%d) %d))' % (
            i, high, t0, i, low, t0 + 3, i, high))
        goal.append('(owned i%d)' % i)
        total += low
    money = total if solvable else total - 1
    return '''(define (problem market-%d) (:domain market-tif)
  (:objects %s - item)
  (:init %s)
  (:goal (and %s)))
''' % (items, ' '.join('i%d' % i for i in range(items)),
       '\n    '.join(init).replace('MONEY', str(money)), ' '.join(goal))


CHARGER = '''(define (domain charger-tif)
  (:requirements :typing :durative-actions :numeric-fluents :timed-initial-literals)
  (:types robot task)
  (:predicates (done ?t - task) (free))
  (:functions (energy ?r - robot) (power) (need ?t - task))
  (:durative-action charge
    :parameters (?r - robot)
    :duration (= ?duration 2)
    :condition (and (at start (free)) (over all (>= (power) 5)))
    :effect (and (at start (not (free))) (at end (free)) (at end (increase (energy ?r) 10))))
  (:durative-action work
    :parameters (?r - robot ?t - task)
    :duration (= ?duration 3)
    :condition (and (at start (>= (energy ?r) (need ?t))))
    :effect (and (at start (decrease (energy ?r) (need ?t))) (at end (done ?t)))))
'''


def charger(rng, robots, tasks, solvable):
    # The grid gives power only in windows; charging needs it all along
    horizon = 6 * tasks + 20
    init = ['(free) (= (power) 0)']
    windows = horizon // 10 if solvable else 0
    for w in range(windows):
        init.append('(at %d (= (power) 8)) (at %d (= (power) 0))' % (10 * w + 1, 10 * w + 7))
    for r in range(robots):
        init.append('(= (energy r%d) 0)' % r)
    goal = []
    for t in range(tasks):
        init.append('(= (need t%d) %d)' % (t, rng.choice((5, 10))))
        goal.append('(done t%d)' % t)
    return '''(define (problem charger-%d-%d) (:domain charger-tif)
  (:objects %s - robot %s - task)
  (:init %s)
  (:goal (and %s)))
''' % (robots, tasks, ' '.join('r%d' % i for i in range(robots)),
       ' '.join('t%d' % i for i in range(tasks)), '\n    '.join(init), ' '.join(goal))


TRAFFIC = '''(define (domain traffic-tif)
  (:requirements :typing :durative-actions :numeric-fluents :timed-initial-literals)
  (:types car place)
  (:predicates (at ?c - car ?p - place) (road ?a ?b - place) (open-window))
  (:functions (travel ?a ?b - place))
  (:durative-action drive
    :parameters (?c - car ?a ?b - place)
    :duration (= ?duration (travel ?a ?b))
    :condition (and (at start (at ?c ?a)) (over all (road ?a ?b)) (over all (open-window)))
    :effect (and (at start (not (at ?c ?a))) (at end (at ?c ?b)))))
'''


def traffic(rng, places, cars, solvable):
    # Travel times rise at rush hour (fluents at timed instants); the city closes at a time
    P = ['x%d' % i for i in range(places)]
    init = ['(open-window)']
    total = 0
    for a, b in zip(P, P[1:]):
        t = rng.randint(2, 6)
        total += t
        init.append('(road %s %s) (road %s %s) (= (travel %s %s) %d) (= (travel %s %s) %d)' % (
            a, b, b, a, a, b, t, b, a, t))
        init.append('(at 5 (= (travel %s %s) %d)) (at 5 (= (travel %s %s) %d))' % (
            a, b, 3 * t, b, a, 3 * t))
    for c in range(cars):
        init.append('(at c%d %s)' % (c, P[0]))
    close = 3 * total + 10 if solvable else 3
    init.append('(at %d (not (open-window)))' % close)
    goal = ' '.join('(at c%d %s)' % (c, P[-1]) for c in range(cars))
    return '''(define (problem traffic-%d-%d) (:domain traffic-tif)
  (:objects %s - car %s - place)
  (:init %s)
  (:goal (and %s)))
''' % (places, cars, ' '.join('c%d' % i for i in range(cars)), ' '.join(P),
       '\n    '.join(init), goal)


# --- Robotic warehouse ----------------------------------------------------------------------
#
# Robots carry shelves (pods) from storage to picking stations, where an order takes an item,
# and back. Level "free": zones joined by aisles, any number of robots per zone. Level
# "capacity": each zone holds a few robots at once (a count). Level "cells": a grid where a cell
# holds one robot (multi-agent path finding inside planning; few robots).

WAREHOUSE_FREE = '''(define (domain warehouse-free)
  (:requirements :typing :negative-preconditions :action-costs)
  (:types robot pod item zone - object station - zone)
  (:predicates (aisle ?a ?b - zone) (at ?r - robot ?z - zone) (pod-at ?p - pod ?z - zone)
               (lifting ?r - robot ?p - pod) (empty ?r - robot) (has ?p - pod ?i - item)
               (home ?p - pod ?z - zone) (delivered ?i - item ?s - station)
               (order ?i - item ?s - station))
  (:functions (total-cost))
  (:action move
    :parameters (?r - robot ?a ?b - zone)
    :precondition (and (at ?r ?a) (aisle ?a ?b))
    :effect (and (not (at ?r ?a)) (at ?r ?b) (increase (total-cost) 1)))
  (:action lift
    :parameters (?r - robot ?p - pod ?z - zone)
    :precondition (and (at ?r ?z) (pod-at ?p ?z) (empty ?r))
    :effect (and (not (pod-at ?p ?z)) (not (empty ?r)) (lifting ?r ?p)
                 (increase (total-cost) 1)))
  (:action lower
    :parameters (?r - robot ?p - pod ?z - zone)
    :precondition (and (at ?r ?z) (lifting ?r ?p) (home ?p ?z))
    :effect (and (pod-at ?p ?z) (empty ?r) (not (lifting ?r ?p)) (increase (total-cost) 1)))
  (:action pick
    :parameters (?r - robot ?p - pod ?i - item ?s - station)
    :precondition (and (at ?r ?s) (lifting ?r ?p) (has ?p ?i) (order ?i ?s))
    :effect (and (delivered ?i ?s) (not (has ?p ?i)) (increase (total-cost) 1))))
'''

WAREHOUSE_CAPACITY = '''(define (domain warehouse-capacity)
  (:requirements :typing :negative-preconditions :numeric-fluents :action-costs)
  (:types robot pod item zone - object station - zone)
  (:predicates (aisle ?a ?b - zone) (at ?r - robot ?z - zone) (pod-at ?p - pod ?z - zone)
               (lifting ?r - robot ?p - pod) (empty ?r - robot) (has ?p - pod ?i - item)
               (home ?p - pod ?z - zone) (delivered ?i - item ?s - station)
               (order ?i - item ?s - station))
  (:functions (robots-in ?z - zone) (capacity ?z - zone) (total-cost))
  (:action move
    :parameters (?r - robot ?a ?b - zone)
    :precondition (and (at ?r ?a) (aisle ?a ?b) (< (robots-in ?b) (capacity ?b)))
    :effect (and (not (at ?r ?a)) (at ?r ?b) (decrease (robots-in ?a) 1)
                 (increase (robots-in ?b) 1) (increase (total-cost) 1)))
  (:action lift
    :parameters (?r - robot ?p - pod ?z - zone)
    :precondition (and (at ?r ?z) (pod-at ?p ?z) (empty ?r))
    :effect (and (not (pod-at ?p ?z)) (not (empty ?r)) (lifting ?r ?p)
                 (increase (total-cost) 1)))
  (:action lower
    :parameters (?r - robot ?p - pod ?z - zone)
    :precondition (and (at ?r ?z) (lifting ?r ?p) (home ?p ?z))
    :effect (and (pod-at ?p ?z) (empty ?r) (not (lifting ?r ?p)) (increase (total-cost) 1)))
  (:action pick
    :parameters (?r - robot ?p - pod ?i - item ?s - station)
    :precondition (and (at ?r ?s) (lifting ?r ?p) (has ?p ?i) (order ?i ?s))
    :effect (and (delivered ?i ?s) (not (has ?p ?i)) (increase (total-cost) 1))))
'''

WAREHOUSE_CELLS = '''(define (domain warehouse-cells)
  (:requirements :typing :negative-preconditions :action-costs)
  (:types robot pod item zone - object station - zone)
  (:predicates (aisle ?a ?b - zone) (at ?r - robot ?z - zone) (pod-at ?p - pod ?z - zone)
               (lifting ?r - robot ?p - pod) (empty ?r - robot) (has ?p - pod ?i - item)
               (home ?p - pod ?z - zone) (delivered ?i - item ?s - station)
               (order ?i - item ?s - station) (clear ?z - zone))
  (:functions (total-cost))
  (:action move
    :parameters (?r - robot ?a ?b - zone)
    :precondition (and (at ?r ?a) (aisle ?a ?b) (clear ?b))
    :effect (and (not (at ?r ?a)) (at ?r ?b) (clear ?a) (not (clear ?b))
                 (increase (total-cost) 1)))
  (:action lift
    :parameters (?r - robot ?p - pod ?z - zone)
    :precondition (and (at ?r ?z) (pod-at ?p ?z) (empty ?r))
    :effect (and (not (pod-at ?p ?z)) (not (empty ?r)) (lifting ?r ?p)
                 (increase (total-cost) 1)))
  (:action lower
    :parameters (?r - robot ?p - pod ?z - zone)
    :precondition (and (at ?r ?z) (lifting ?r ?p) (home ?p ?z))
    :effect (and (pod-at ?p ?z) (empty ?r) (not (lifting ?r ?p)) (increase (total-cost) 1)))
  (:action pick
    :parameters (?r - robot ?p - pod ?i - item ?s - station)
    :precondition (and (at ?r ?s) (lifting ?r ?p) (has ?p ?i) (order ?i ?s))
    :effect (and (delivered ?i ?s) (not (has ?p ?i)) (increase (total-cost) 1))))
'''

WAREHOUSE_TIME = '''(define (domain warehouse-time)
  (:requirements :typing :negative-preconditions :durative-actions :numeric-fluents)
  (:types robot pod item zone - object station - zone)
  (:predicates (aisle ?a ?b - zone) (at ?r - robot ?z - zone) (pod-at ?p - pod ?z - zone)
               (lifting ?r - robot ?p - pod) (empty ?r - robot) (has ?p - pod ?i - item)
               (home ?p - pod ?z - zone) (delivered ?i - item ?s - station)
               (order ?i - item ?s - station) (idle ?r - robot) (station-free ?s - station))
  (:functions (length ?a ?b - zone) (speed ?r - robot) (battery ?r - robot))
  (:durative-action move
    :parameters (?r - robot ?a ?b - zone)
    :duration (= ?duration (/ (length ?a ?b) (speed ?r)))
    :condition (and (at start (at ?r ?a)) (at start (idle ?r)) (over all (aisle ?a ?b))
                    (at start (>= (battery ?r) (length ?a ?b))))
    :effect (and (at start (not (at ?r ?a))) (at start (not (idle ?r)))
                 (at start (decrease (battery ?r) (length ?a ?b)))
                 (at end (at ?r ?b)) (at end (idle ?r))))
  (:durative-action lift
    :parameters (?r - robot ?p - pod ?z - zone)
    :duration (= ?duration 2)
    :condition (and (at start (idle ?r)) (over all (at ?r ?z)) (at start (pod-at ?p ?z))
                    (at start (empty ?r)))
    :effect (and (at start (not (idle ?r))) (at start (not (pod-at ?p ?z)))
                 (at start (not (empty ?r))) (at end (lifting ?r ?p)) (at end (idle ?r))))
  (:durative-action lower
    :parameters (?r - robot ?p - pod ?z - zone)
    :duration (= ?duration 2)
    :condition (and (at start (idle ?r)) (over all (at ?r ?z)) (at start (lifting ?r ?p))
                    (over all (home ?p ?z)))
    :effect (and (at start (not (idle ?r))) (at end (pod-at ?p ?z)) (at end (empty ?r))
                 (at start (not (lifting ?r ?p))) (at end (idle ?r))))
  (:durative-action pick
    :parameters (?r - robot ?p - pod ?i - item ?s - station)
    :duration (= ?duration 3)
    :condition (and (at start (idle ?r)) (over all (at ?r ?s)) (over all (lifting ?r ?p))
                    (at start (has ?p ?i)) (over all (order ?i ?s)) (at start (station-free ?s)))
    :effect (and (at start (not (idle ?r))) (at start (not (station-free ?s)))
                 (at start (not (has ?p ?i))) (at end (delivered ?i ?s))
                 (at end (station-free ?s)) (at end (idle ?r)))))
'''


def warehouse(rng, level, robots, solvable, temporal=False):
    """A grid of zones: a column of stations on the left, storage zones holding pods, aisles
    between neighbours. Orders ask a station for items of random pods; robots start spread."""
    if level == 'cells':
        cols, rows = max(4, robots + 2), max(3, robots // 2 + 2)
    else:
        cols = max(3, int((robots * 1.5) ** 0.5) + 2)
        rows = cols
    zones = ['z%d_%d' % (x, y) for x in range(1, cols) for y in range(rows)]
    stations = ['s%d' % y for y in range(rows) if y % 2 == 0]
    grid = {}
    for y in range(rows):
        grid[(0, y)] = 's%d' % y if y % 2 == 0 else 'w%d' % y
    for x in range(1, cols):
        for y in range(rows):
            grid[(x, y)] = 'z%d_%d' % (x, y)
    walls = ['w%d' % y for y in range(rows) if y % 2 == 1]
    names = zones + walls
    aisles = []
    for (x, y), a in grid.items():
        for dx, dy in ((1, 0), (0, 1)):
            b = grid.get((x + dx, y + dy))
            if b:
                aisles.append((a, b))
    if not solvable:
        # The first station cut off: no aisle reaches it
        aisles = [(a, b) for a, b in aisles if stations[0] not in (a, b)]
    storage = [z for z in zones if int(z.split('_')[0][1:]) >= 2]
    pods = min(len(storage), robots * 2)
    pod_zone = rng.sample(storage, pods)
    orders = max(1, robots)
    init, goal = [], []
    for a, b in aisles:
        init.append('(aisle %s %s) (aisle %s %s)' % (a, b, b, a))
        if temporal:
            d = rng.randint(1, 3)
            init.append('(= (length %s %s) %d) (= (length %s %s) %d)' % (a, b, d, b, a, d))
    for p, z in enumerate(pod_zone):
        init.append('(pod-at pod%d %s) (home pod%d %s)' % (p, z, p, z))
    free = [z for z in zones if z not in pod_zone] or zones
    start = [free[i % len(free)] for i in range(robots)]
    occupied = set()
    for r in range(robots):
        z = start[r]
        if level == 'cells':
            z = next(c for c in free if c not in occupied)
            occupied.add(z)
        init.append('(at r%d %s) (empty r%d)' % (r, z, r))
        if temporal:
            init.append('(idle r%d) (= (speed r%d) %d) (= (battery r%d) 1000)' % (
                r, r, rng.choice((1, 2)), r))
    if level == 'cells':
        init += ['(clear %s)' % c for c in list(grid.values()) if c not in occupied
                 and c not in walls]
    if level == 'capacity':
        count = {}
        for r in range(robots):
            count[start[r]] = count.get(start[r], 0) + 1
        for z in list(grid.values()):
            cap = 2 if z.startswith('z') else 4
            init.append('(= (robots-in %s) %d) (= (capacity %s) %d)' % (
                z, count.get(z, 0), z, max(cap, count.get(z, 0))))
    if temporal:
        init += ['(station-free %s)' % s for s in stations]
    for o in range(orders):
        p = rng.randrange(pods)
        s = stations[0] if o == 0 else rng.choice(stations)
        init.append('(has pod%d it%d) (order it%d %s)' % (p, o, o, s))
        goal.append('(delivered it%d %s)' % (o, s))
    # Every pod back home at the end
    goal += ['(pod-at pod%d %s)' % (p, z) for p, z in enumerate(pod_zone)]
    if not temporal:
        init.append('(= (total-cost) 0)')
    domain = 'warehouse-time' if temporal else 'warehouse-' + level
    metric = '(:metric minimize (total-time))' if temporal else '(:metric minimize (total-cost))'
    return '''(define (problem wh-%s-%d) (:domain %s)
  (:objects %s - robot %s - zone %s - station %s - pod %s - item)
  (:init %s)
  (:goal (and %s))
  %s)
''' % (level + ('-time' if temporal else ''), robots, domain,
       ' '.join('r%d' % i for i in range(robots)), ' '.join(names), ' '.join(stations),
       ' '.join('pod%d' % i for i in range(pods)), ' '.join('it%d' % i for i in range(orders)),
       '\n    '.join(init), ' '.join(goal), metric)


def main():
    out = sys.argv[1]
    rng = random.Random(2026)
    write(out, 'object-fluents', 'delivery', DELIVERY,
          [(delivery(rng, r, p, l, True), True) for r, p, l in
           ((1, 1, 3), (2, 3, 6), (3, 6, 12), (5, 12, 25), (10, 30, 60))] +
          [(delivery(rng, 2, 3, 6, False), False)])
    write(out, 'object-fluents', 'elevator', ELEVATOR,
          [(elevator(rng, e, f, p, True), True) for e, f, p in
           ((1, 3, 2), (1, 6, 5), (2, 10, 12), (3, 20, 30), (4, 30, 60))] +
          [(elevator(rng, 2, 6, 4, False), False)])
    write(out, 'object-fluents', 'keys', KEYS,
          [(keys(rng, n, True), True) for n in (3, 6, 12, 25, 50)] +
          [(keys(rng, 6, False), False)])
    write(out, 'object-fluents', 'delivery-time', DELIVERY_TIME,
          [(delivery_time(rng, r, p, l, True), True) for r, p, l in
           ((1, 1, 3), (2, 2, 5), (2, 4, 8), (3, 8, 15), (5, 15, 30))] +
          [(delivery_time(rng, 2, 2, 5, False), False)])
    write(out, 'timed-initial-fluents', 'market', MARKET,
          [(market(rng, n, True), True) for n in (1, 3, 6, 12, 25)] +
          [(market(rng, 3, False), False)])
    write(out, 'timed-initial-fluents', 'charger', CHARGER,
          [(charger(rng, r, t, True), True) for r, t in ((1, 1), (1, 3), (2, 5), (3, 10), (5, 20))]
          + [(charger(rng, 1, 3, False), False)])
    write(out, 'timed-initial-fluents', 'traffic', TRAFFIC,
          [(traffic(rng, n, c, True), True) for n, c in ((3, 1), (5, 2), (8, 3), (12, 5), (20, 8))]
          + [(traffic(rng, 5, 2, False), False)])
    for level, domain, sizes in (
            ('free', WAREHOUSE_FREE, (5, 20, 50, 100, 200, 400)),
            ('capacity', WAREHOUSE_CAPACITY, (5, 20, 50, 100, 200, 400)),
            ('cells', WAREHOUSE_CELLS, (2, 4, 8, 12, 16, 24))):
        write(out, 'warehouse', level, domain,
              [(warehouse(rng, level, n, True), True) for n in sizes] +
              [(warehouse(rng, level, sizes[1], False), False)])
    write(out, 'warehouse', 'time', WAREHOUSE_TIME,
          [(warehouse(rng, 'free', n, True, temporal=True), True)
           for n in (5, 20, 50, 100, 200)] +
          [(warehouse(rng, 'free', 20, False, temporal=True), False)])
    with open(os.path.join(out, 'manifest.json'), 'w') as fh:
        json.dump(MANIFEST, fh, indent=1)
    print('%d problems' % len(MANIFEST))


if __name__ == '__main__':
    main()
