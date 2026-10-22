#!/usr/bin/env python3
"""Kairos's validator against VAL on the plans kept by coverage.py --keep-plans.

For each plan: the plan itself and two broken variants (a step removed; a timed step moved
1 time unit earlier), each checked by `kairos validate` and by VAL 20210401 (planutils's, in
the kairos/planutils:benchmark image). Reports verdict agreement, what VAL cannot check
(parse errors, unsupported dynamics, crashes, time-outs) and the time per plan of each, both
run as a command.

  bench/val_compare.py KAIROS PLANS_DIR SUITE [SUITE...] --out CSV
"""
import argparse
import csv
import os
import random
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage  # noqa: E402

IMAGE = 'kairos/planutils:benchmark'
STEP = re.compile(r'^\s*(\d+(\.\d+)?:\s*)?\([^()]+\)(\s*\[[\d.]+\])?\s*$')
END = re.compile(r'^\s*\d+(\.\d+)?:\s*@PlanEND\s*$')  # PDDL+: how long the processes run

# VAL inside one container for all plans: verdict, exit code and milliseconds per plan
VAL_SCRIPT = r"""
B=/root/.planutils/packages/val/bin
while IFS=$'\t' read -r id d p plan; do
  s=$(date +%s%N)
  timeout -s KILL 60 $B/Validate -t 0.001 "$d" "$p" "$plan" > /tmp/o 2>&1
  c=$?
  ms=$(( ($(date +%s%N) - s) / 1000000 ))
  v=other
  grep -q 'Plan valid' /tmp/o && v=valid
  grep -q -E 'Plan failed|Goal not satisfied|Plan invalid|Plan Repair Advice|Failed plans' /tmp/o && [ $v != valid ] && v=invalid
  grep -q -E 'Problem in domain definition|Syntax error|Bad plan description|Bad operator' /tmp/o && v=parse
  grep -q 'not handled' /tmp/o && v=unsupported
  [ $c -ge 129 ] && [ $c -le 254 ] && v=crash
  grep -q -i 'no such file' /tmp/o && v=missing
  [ $c -eq 137 ] && v=timeout
  printf '%s\t%s\t%s\t%s\n' "$id" "$v" "$c" "$ms"
done < /m/manifest.tsv
"""


def steps(text):
    # The last plan of the file (Kairos's anytime output has several), without @PlanEND
    blocks, cur = [], []
    for ln in text.splitlines():
        if STEP.match(ln) or END.match(ln):
            cur.append(ln.strip())
        elif cur and ln.strip():  # a comment after steps (; better plan 2) starts the next plan
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    return blocks[-1] if blocks else []


def end_after(lines):
    """Whether @PlanEND comes after the last happening (processes run on after it)."""
    timed = [(float(ln.split(':', 1)[0]), bool(END.match(ln)))
             for ln in lines if re.match(r'^\s*\d', ln)]
    ends = [t for t, end in timed if end]
    last = max([t for t, end in timed if not end], default=0.0)
    return bool(ends) and ends[0] > last + 1e-9


def variants(lines, rnd):
    out = [('plan', lines)]
    real = [i for i, ln in enumerate(lines) if not END.match(ln)]  # @PlanEND is never broken
    if len(real) > 1:
        i = rnd.choice(real)
        out.append(('drop', lines[:i] + lines[i + 1:]))
    timed = [i for i in real if re.match(r'^\s*\d', lines[i])]
    if timed:
        i = rnd.choice(timed)
        t = float(lines[i].split(':', 1)[0])
        if t >= 1.0:
            moved = list(lines)
            moved[i] = '%.3f:%s' % (t - 1.0, lines[i].split(':', 1)[1])
            out.append(('shift', moved))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('kairos')
    ap.add_argument('plans')
    ap.add_argument('suites', nargs='+')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    work = os.path.abspath(args.out + '.d')
    os.makedirs(work, exist_ok=True)
    rnd = random.Random(1)
    rows = []
    for s in args.suites:
        for label, domain, problem in coverage.suite(s):
            src = os.path.join(args.plans, label, os.path.basename(problem) + '.plan')
            if not os.path.exists(src):
                continue
            lines = steps(open(src).read())
            for kind, ls in variants(lines, rnd):
                pid = len(rows)
                plan = os.path.join(work, '%d.plan' % pid)
                with open(plan, 'w') as f:
                    f.write('\n'.join(ls) + '\n')
                # VAL's format has no @PlanEND: the plan ends at its last happening, so a plan
                # whose processes run on after it cannot be written for VAL
                steps_only = [ln for ln in ls if not END.match(ln)]
                with open(os.path.join(work, '%d.val.plan' % pid), 'w') as f:
                    f.write('\n'.join(steps_only) + '\n')
                rows.append({'id': pid, 'suite': s, 'domain': label,
                             'problem': os.path.basename(problem), 'kind': kind,
                             'd': os.path.abspath(domain), 'p': os.path.abspath(problem),
                             'plan': plan, 'end_after': end_after(ls)})
    with open(os.path.join(work, 'manifest.tsv'), 'w') as f:
        for r in rows:
            f.write('%d\t%s\t%s\t/m/%d.val.plan\n' % (r['id'], r['d'], r['p'], r['id']))
    # Kairos's validator, one process per plan
    for r in rows:
        t0 = time.perf_counter()
        v = subprocess.run([args.kairos, 'validate', r['d'], r['p'], r['plan']],
                           capture_output=True, text=True, timeout=120)
        r['kairos_ms'] = '%.1f' % ((time.perf_counter() - t0) * 1000)
        r['kairos'] = {0: 'valid', 1: 'invalid'}.get(v.returncode, 'other:%d' % v.returncode)
    # VAL, in the planutils image (home mounted at the same path, read-only)
    home = os.path.expanduser('~')
    out = subprocess.run(['docker', 'run', '--rm', '-i', '--memory', '4g', '-v',
                          '%s:%s:ro' % (home, home), '-v', '%s:/m:ro' % work, IMAGE, 'bash',
                          '-c', VAL_SCRIPT], capture_output=True, text=True).stdout
    for ln in out.splitlines():
        pid, verdict, code, ms = ln.split('\t')
        rows[int(pid)].update(val=verdict, val_code=code, val_ms=ms)
    for r in rows:
        if r['end_after']:
            r['val'] = 'plan-end'  # not expressible for VAL: not compared
    keys = ['suite', 'domain', 'problem', 'kind', 'kairos', 'kairos_ms', 'val', 'val_code',
            'val_ms']
    with open(args.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    report(rows)


def report(rows):
    print('| suite | plans | agree | VAL cannot check | Kairos ms (median) | VAL ms (median) |')
    print('|---|---:|---:|---:|---:|---:|')
    for s in sorted({r['suite'] for r in rows}):
        rs = [r for r in rows if r['suite'] == s]
        both = [r for r in rs if r.get('val') in ('valid', 'invalid')]
        agree = sum(1 for r in both if r['val'] == r['kairos'])
        km = sorted(float(r['kairos_ms']) for r in rs)
        vm = sorted(float(r['val_ms']) for r in both) or [0]
        print('| %s | %d | %d/%d | %d | %.0f | %.0f |' % (
            s, len(rs), agree, len(both), len(rs) - len(both), km[len(km) // 2],
            vm[len(vm) // 2]))
    print()
    for r in rows:
        if r.get('val') in ('valid', 'invalid') and r['val'] != r['kairos']:
            print('disagree: %s %s %s kairos=%s val=%s' % (r['domain'], r['problem'], r['kind'],
                                                          r['kairos'], r['val']))


if __name__ == '__main__':
    main()
