#!/usr/bin/env python3
"""The @durative variant of each instantaneous support probe (bench/probes), for planners that
only plan with durative actions: every action lasts 1, its preconditions at start, its effects
at end (a conditional effect: its condition at start).

  bench/probes_durative.py
"""
import os
import re

PROBES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probes')
BASE = ['conditional-effects', 'quantified-preconditions', 'disjunctive-preconditions',
        'derived-predicates', 'numeric-fluents', 'non-linear-numeric', 'object-fluents',
        'preferences', 'trajectory-constraints']


def end(s, i):
    depth = 0
    for j in range(i, len(s)):
        depth += s[j] == '('
        depth -= s[j] == ')'
        if depth == 0:
            return j + 1
    raise ValueError(s[i:])


def items(body):
    """The top-level items of '(and ...)'."""
    inner = body.strip()
    inner = inner[4:-1] if inner.startswith('(and') else inner
    out, i = [], 0
    while i < len(inner):
        if inner[i] == '(':
            e = end(inner, i)
            out.append(inner[i:e])
            i = e
        else:
            i += 1
    return out


def effect(x):
    if x.startswith('(when'):
        cond, eff = items('(and ' + x[5:-1] + ')')
        return '(when (at start %s) (at end %s))' % (cond, eff)
    return '(at end %s)' % x


def durative(text):
    out, pos = '', 0
    for m in re.finditer(r'\(:action ', text):
        s = m.start()
        e = end(text, s)
        a = text[s:e]
        name = re.search(r'\(:action (\S+)', a).group(1)
        params = re.search(r':parameters (\([^)]*\))', a).group(1)
        pi = a.index('(', a.index(':precondition'))
        ei = a.index('(', a.index(':effect'))
        pre = ' '.join('(at start %s)' % x for x in items(a[pi:end(a, pi)]))
        eff = ' '.join(effect(x) for x in items(a[ei:end(a, ei)])
                       if 'total-cost' not in x)
        out += text[pos:s] + (
            '(:durative-action %s :parameters %s :duration (= ?duration 1)\n'
            '  :condition (and %s)\n  :effect (and %s))' % (name, params, pre, eff))
        pos = e
    out += text[pos:]
    out = out.replace(' (total-cost))', ')')
    return out.replace('(:requirements ', '(:requirements :durative-actions ', 1)


def main():
    for f in BASE:
        d = os.path.join(PROBES, f + '@durative')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(PROBES, f, 'domain.pddl')) as fh:
            dom = durative(fh.read())
        with open(os.path.join(d, 'domain.pddl'), 'w') as fh:
            fh.write(dom)
        with open(os.path.join(PROBES, f, 'problem.pddl')) as fh:
            prob = fh.read()
        prob = prob.replace(' (= (total-cost) 0)', '').replace(
            '(:metric minimize (total-cost))', '(:metric minimize (total-time))')
        with open(os.path.join(d, 'problem.pddl'), 'w') as fh:
            fh.write(prob)


if __name__ == '__main__':
    main()
