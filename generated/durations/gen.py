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

"""Problems that need a duration strictly between its bounds (POPF's LP finds those).

    gen.py [OUT_DIR]        (bench/durations/problems by default)

Five domains, five instances each, from small to larger: neither the least nor the greatest
duration of the key action gives a plan, only one in between.
"""

import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'problems')

DOMAINS = {}

# A one-shot recharge inside a window that closes: charging to full does not fit, the least
# charge is too little for the mission
DOMAINS['window'] = '''(define (domain window)
(:requirements :typing :fluents :durative-actions :duration-inequalities :timed-initial-literals)
(:types robot)
(:predicates (open) (done ?r - robot) (free ?r - robot) (can_charge ?r - robot))
(:functions (battery ?r - robot) (capacity ?r - robot) (need ?r - robot))
(:durative-action recharge
  :parameters (?r - robot)
  :duration (and (>= ?duration 1) (<= ?duration (/ (- (capacity ?r) (battery ?r)) 2)))
  :condition (and (at start (free ?r)) (at start (can_charge ?r)) (over all (open)))
  :effect (and (at start (not (free ?r))) (at start (not (can_charge ?r))) (at end (free ?r))
               (increase (battery ?r) (* #t 2))))
(:durative-action mission
  :parameters (?r - robot)
  :duration (= ?duration 10)
  :condition (and (at start (free ?r)) (at start (>= (battery ?r) (need ?r))))
  :effect (and (at start (not (free ?r))) (at end (done ?r)) (at end (free ?r))
               (decrease (battery ?r) (* #t 1)))))
'''

def window(k):
    robots = ['r%d' % i for i in range(1, k + 1)]
    init = ' '.join('(free %s) (can_charge %s) (= (battery %s) 10) (= (capacity %s) 100) '
                    '(= (need %s) %d)' % (r, r, r, r, r, 26 + 2 * i) for i, r in enumerate(robots))
    goal = ' '.join('(done %s)' % r for r in robots)
    return ('(define (problem window-%d) (:domain window) (:objects %s - robot)\n'
            '(:init (open) %s (at %d (not (open))))\n(:goal (and %s)))\n'
            % (k, ' '.join(robots), init, 15 + k, goal))

# An oven heats once: ?duration in its effect, a range for the temperature
DOMAINS['oven'] = '''(define (domain oven)
(:requirements :typing :fluents :durative-actions :duration-inequalities)
(:types oven)
(:predicates (idle ?o - oven) (fresh ?o - oven) (baked ?o - oven))
(:functions (temp ?o - oven) (low ?o - oven) (high ?o - oven))
(:durative-action heat
  :parameters (?o - oven)
  :duration (and (>= ?duration 1) (<= ?duration 30))
  :condition (and (at start (idle ?o)) (at start (fresh ?o)))
  :effect (and (at start (not (idle ?o))) (at start (not (fresh ?o))) (at end (idle ?o))
               (at end (increase (temp ?o) (* 2 ?duration)))))
(:action take-out
  :parameters (?o - oven)
  :precondition (and (idle ?o) (>= (temp ?o) (low ?o)) (<= (temp ?o) (high ?o)))
  :effect (baked ?o)))
'''

def oven(k):
    ovens = ['o%d' % i for i in range(1, k + 1)]
    init = ' '.join('(idle %s) (fresh %s) (= (temp %s) 20) (= (low %s) %d) (= (high %s) %d)'
                    % (o, o, o, o, 40 + 3 * i, o, 45 + 3 * i) for i, o in enumerate(ovens))
    goal = ' '.join('(baked %s)' % o for o in ovens)
    return ('(define (problem oven-%d) (:domain oven) (:objects %s - oven)\n(:init %s)\n'
            '(:goal (and %s)))\n' % (k, ' '.join(ovens), init, goal))

# Filling a tank continuously: between a least and a greatest level, a valve opened once
DOMAINS['tank'] = '''(define (domain tank)
(:requirements :typing :fluents :durative-actions :duration-inequalities)
(:types tank)
(:predicates (closed ?t - tank) (unused ?t - tank) (ready ?t - tank))
(:functions (level ?t - tank) (flow ?t - tank) (low ?t - tank) (high ?t - tank))
(:durative-action fill
  :parameters (?t - tank)
  :duration (and (>= ?duration 1) (<= ?duration 50))
  :condition (and (at start (closed ?t)) (at start (unused ?t)))
  :effect (and (at start (not (closed ?t))) (at start (not (unused ?t))) (at end (closed ?t))
               (increase (level ?t) (* #t (flow ?t)))))
(:action seal
  :parameters (?t - tank)
  :precondition (and (closed ?t) (>= (level ?t) (low ?t)) (<= (level ?t) (high ?t)))
  :effect (ready ?t)))
'''

def tank(k):
    tanks = ['t%d' % i for i in range(1, k + 1)]
    init = ' '.join('(closed %s) (unused %s) (= (level %s) 0) (= (flow %s) %d) (= (low %s) %d) '
                    '(= (high %s) %d)' % (t, t, t, t, 2 + i % 3, t, 30 + 4 * i, t, 34 + 4 * i)
                    for i, t in enumerate(tanks))
    goal = ' '.join('(ready %s)' % t for t in tanks)
    return ('(define (problem tank-%d) (:domain tank) (:objects %s - tank)\n(:init %s)\n'
            '(:goal (and %s)))\n' % (k, ' '.join(tanks), init, goal))

# Robots share one charger before a deadline: each must charge enough, not to full
DOMAINS['charger'] = '''(define (domain charger)
(:requirements :typing :fluents :durative-actions :duration-inequalities :timed-initial-literals)
(:types robot)
(:predicates (charger_free) (open) (done ?r - robot) (free ?r - robot) (flat ?r - robot))
(:functions (battery ?r - robot) (capacity ?r - robot) (need ?r - robot))
(:durative-action charge
  :parameters (?r - robot)
  :duration (and (>= ?duration 1) (<= ?duration (/ (- (capacity ?r) (battery ?r)) 4)))
  :condition (and (at start (free ?r)) (at start (flat ?r)) (at start (charger_free))
                  (over all (open)))
  :effect (and (at start (not (free ?r))) (at start (not (flat ?r))) (at start (not (charger_free)))
               (at end (free ?r)) (at end (charger_free))
               (increase (battery ?r) (* #t 4))))
(:action go
  :parameters (?r - robot)
  :precondition (and (free ?r) (>= (battery ?r) (need ?r)))
  :effect (done ?r)))
'''

def charger(k):
    robots = ['r%d' % i for i in range(1, k + 1)]
    init = ' '.join('(free %s) (flat %s) (= (battery %s) 0) (= (capacity %s) 100) (= (need %s) %d)'
                    % (r, r, r, r, r, 20 + 4 * i) for i, r in enumerate(robots))
    goal = ' '.join('(done %s)' % r for r in robots)
    window_close = sum(7 + i for i in range(k)) + 1
    return ('(define (problem charger-%d) (:domain charger) (:objects %s - robot)\n'
            '(:init (charger_free) (open) %s (at %d (not (open))))\n(:goal (and %s)))\n'
            % (k, ' '.join(robots), init, window_close, goal))

# Drilling: the depth grows with the time; it must end between two depths
DOMAINS['drill'] = '''(define (domain drill)
(:requirements :typing :fluents :durative-actions :duration-inequalities)
(:types hole)
(:predicates (planned ?h - hole) (drilled ?h - hole) (bit_free))
(:functions (depth ?h - hole) (rate) (min_depth ?h - hole) (max_depth ?h - hole))
(:durative-action drill
  :parameters (?h - hole)
  :duration (and (>= ?duration 1) (<= ?duration 60))
  :condition (and (at start (planned ?h)) (at start (bit_free)))
  :effect (and (at start (not (planned ?h))) (at start (not (bit_free))) (at end (bit_free))
               (increase (depth ?h) (* #t (rate)))))
(:action check
  :parameters (?h - hole)
  :precondition (and (bit_free) (>= (depth ?h) (min_depth ?h)) (<= (depth ?h) (max_depth ?h)))
  :effect (drilled ?h)))
'''

def drill(k):
    holes = ['h%d' % i for i in range(1, k + 1)]
    init = ' '.join('(planned %s) (= (depth %s) 0) (= (min_depth %s) %d) (= (max_depth %s) %d)'
                    % (h, h, h, 12 + 5 * i, h, 15 + 5 * i) for i, h in enumerate(holes))
    goal = ' '.join('(drilled %s)' % h for h in holes)
    return ('(define (problem drill-%d) (:domain drill) (:objects %s - hole)\n'
            '(:init (bit_free) (= (rate) 1.5) %s)\n(:goal (and %s)))\n'
            % (k, ' '.join(holes), init, goal))


def main():
    gens = {'window': window, 'oven': oven, 'tank': tank, 'charger': charger, 'drill': drill}
    for name, text in DOMAINS.items():
        d = os.path.join(OUT, name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'domain.pddl'), 'w') as f:
            f.write(text)
        for k in range(1, 6):
            with open(os.path.join(d, 'p%02d.pddl' % k), 'w') as f:
                f.write(gens[name](k))


if __name__ == '__main__':
    main()
