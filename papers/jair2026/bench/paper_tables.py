#!/usr/bin/env python3
"""Tables, statistics and the cactus figure of the JAIR article, from coverage.py CSVs.

  bench/paper_tables.py OUT_DIR [--kairos-dir DIR]

Times are not corrected (the start of planutils's Apptainer images is counted); the corrected
counts of the 100 ms and 1 s columns are printed apart. --kairos-dir takes Kairos's CSVs from
another run (bench/paper_battery.sh: DIR/kairos_SUITE.csv) instead of the development runs.
"""
import collections
import csv
import json
import math
import os
import random
import sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
# Start-up of planutils's Apptainer images (s), reported apart
OFFSET = {'POPF': 0.189, 'ENHSP-2020': 0.084, 'SMTPlan+': 0.185}

# suite: (label, limit s, [(planner, csv, first-plan times)])
SUITES = collections.OrderedDict([
    ('classical', ('Classical', 30, [
        ('Kairos', 'step31/kairos2_classical.csv', True),
        ('LAMA', 'f0/lama_classical.csv', False),
        ('lama-first', 'sota/lama-first_classical.csv', True),
        ('Scorpion Maidu', 'sota/maidu_classical.csv', False),
        ('Scorpion Maidu agile', 'sota/maidu-agl_classical.csv', True),
        ('Levitron', 'sota/levitron_classical.csv', False),
        ('Levitron agile', 'sota/levitron-agl_classical.csv', True),
        ('FDSS 2023', 'sota/fdss_classical.csv', False),
        ('FDSS 2023 agile', 'sota/fdss-agl_classical.csv', True),
        ('DecStar 2023', 'sota/decstar_classical.csv', True),
        ('Dual-BFWS', 'sota/dual-bfws_classical.csv', True)])),
    ('b3', ('Numeric', 30, [
        ('Kairos', 'sota/kairos_b3.csv', True),
        ('ENHSP', 'sota/enhsp_b3.csv', True),
        ('ENHSP-2020', 'f0/enhsp-2020_b3.csv', True),
        ('LNM-Plan', 'sota/lnm_b3.csv', True),
        ('Metric-FF', 'f0/metric-ff_b3.csv', True)])),
    ('b1', ('Temporal', 30, [
        ('Kairos', 'step31/kairos2_b1.csv', True),
        ('POPF', 'f0/popf_b1.csv', True),
        ('OPTIC', 'f0/optic_b1.csv', False),
        ('TFD', 'f0/tfd_b1.csv', False),
        ('LPG-td', 'f0/lpg-td_b1.csv', False),
        ('NextFLAP', 'sota/nextflap_b1.csv', False)])),
    ('b2', ('Concurrency', 30, [
        ('Kairos', 'step31/kairos2_b2.csv', True),
        ('POPF', 'f0/popf_b2.csv', True),
        ('OPTIC', 'f0/optic_b2.csv', False),
        ('TFD', 'f0/tfd_b2.csv', False),
        ('LPG-td', 'f0/lpg-td_b2.csv', False),
        ('NextFLAP', 'sota/nextflap_b2.csv', False)])),
    ('prefs', ('PDDL3', 30, [
        ('Kairos', 'prefs/kairos_step26.csv', True),
        ('POPF', 'prefs/popf.csv', True),
        ('OPTIC', 'prefs/optic.csv', False),
        ('NextFLAP', 'sota/nextflap_prefs.csv', False)])),
    ('pddlplus', ('PDDL+', 30, [
        ('Kairos', 'pddlplus/kairos.csv', True),
        ('ENHSP', 'pddlplus/enhsp.csv', True),
        ('SMTPlan+', 'pddlplus/smtplan.csv', True)])),
    ('durations', ('Durations', 30, [
        ('Kairos', 'durations/kairos.csv', True),
        ('POPF', 'durations/popf.csv', True),
        ('OPTIC', 'durations/optic.csv', False),
        ('NextFLAP', 'durations/nextflap.csv', False)])),
    ('htg', ('Hard to ground', 30, [
        ('Kairos', 'htg/kairos_final.csv', True),
        ('Powerlifted', 'htg/powerlifted.csv', True)])),
    ('b6', ('PlanSys2 at scale', 60, [
        ('Kairos', 'step31/kairos2_b6.csv', True),
        ('POPF', 'b6/popf.csv', True),
        ('OPTIC', 'b6/optic.csv', False),
        ('TFD', 'b6/tfd.csv', False),
        ('TAMER', 'b6/up_tamer.csv', True),
        ('Aries', 'b6/up_aries.csv', False)])),
])


def load(path):
    rows = list(csv.DictReader(open(path)))
    # quantum-layout: every problem has its own domain file, which old runs of the classical
    # suite took as problems; results/quantum has those planners' runs on the right pairs
    base = os.path.basename(path).replace('_classical.csv', '.csv')
    fix = os.path.join(R, 'quantum', base)
    if path.endswith('_classical.csv') and 'kairos' not in base and os.path.exists(fix):
        rows = [r for r in rows if 'quantum-layout' not in r['domain']] + list(
            csv.DictReader(open(fix)))
    return rows


def solved_times(rows, offset=0.0):
    return sorted(max(0.0, float(r['time']) - offset) for r in rows if r['status'] == 'solved')


def by_domain(rows):
    d = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        d[r['domain']][1] += 1
        d[r['domain']][0] += r['status'] == 'solved'
    return d


def bootstrap(kd, od, n=10000, seed=1):
    """95% interval of (Kairos - other) solved, resampling domains."""
    doms = sorted(kd)
    diffs = [kd[x][0] - od.get(x, [0, 0])[0] for x in doms]
    rnd = random.Random(seed)
    stats = sorted(sum(rnd.choice(diffs) for _ in doms) for _ in range(n))
    return sum(diffs), stats[int(0.025 * n)], stats[int(0.975 * n)], diffs


def sign_test(diffs):
    """Two-sided sign test over domains (ties dropped)."""
    pos = sum(d > 0 for d in diffs)
    neg = sum(d < 0 for d in diffs)
    n = pos + neg
    if n == 0:
        return pos, neg, 1.0
    k = min(pos, neg)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return pos, neg, min(1.0, 2 * p)


def pct(times, q):
    if not times:
        return float('nan')
    return times[min(len(times) - 1, int(math.ceil(q * len(times))) - 1)]


def main():
    out = sys.argv[1]
    kdir = os.path.abspath(sys.argv[sys.argv.index('--kairos-dir') + 1]) if '--kairos-dir' in sys.argv else None
    os.makedirs(out, exist_ok=True)
    data = collections.OrderedDict()
    for key, (label, limit, planners) in SUITES.items():
        runs = []
        for name, rel, short in planners:
            path = os.path.join(R, rel)
            if name == 'Kairos' and kdir:
                path = os.path.join(kdir, 'kairos_%s.csv' % key)
            if os.path.exists(path):
                runs.append((name, load(path), short))
        data[key] = (label, limit, runs)

    full, main_rows, stats, lat, losses = [], [], [], [], []
    for key, (label, limit, runs) in data.items():
        n = len(runs[0][1])
        others = []
        for name, rows, short in runs:
            t = solved_times(rows)
            a, b = (sum(x <= 0.1 for x in t), sum(x <= 1.0 for x in t)) if short else ('--', '--')
            note = ''
            if short and name in OFFSET:
                tc = solved_times(rows, OFFSET[name])
                note = ' (%d, %d)' % (sum(x <= 0.1 for x in tc), sum(x <= 1.0 for x in tc))
            of = '' if len(rows) == n else ' of %d' % len(rows)
            full.append((label, name, a, b, len(t), of, note))
            if name != 'Kairos':
                others.append((len(t), name, rows))
        k = runs[0]
        kt = solved_times(k[1])
        lat.append((label, len(kt), pct(kt, .5), pct(kt, .9), pct(kt, .99)))
        others.sort(key=lambda o: -o[0])
        best = others[0]
        tot, lo, hi, diffs = bootstrap(by_domain(k[1]), by_domain(best[2]))
        pos, neg, p = sign_test(diffs)
        stats.append((label, best[1], tot, lo, hi, pos, neg, p))
        kd = by_domain(k[1])
        for dom in sorted(kd):
            better = ['%s %d' % (nm, by_domain(rows)[dom][0]) for c, nm, rows in others
                      if by_domain(rows).get(dom, [0, 0])[0] > kd[dom][0]]
            if better:
                losses.append((label, dom, kd[dom][0], kd[dom][1], ', '.join(better)))

    with open(os.path.join(out, 'coverage_full.tex'), 'w') as f:
        last = None
        for label, name, a, b, c, of, note in full:
            if last and label != last:
                f.write('\\midrule\n')
            cell = label if label != last else ''
            nm = '\\sys' if name == 'Kairos' else name
            bold = (lambda x: '\\textbf{%s}' % x) if name == 'Kairos' else (lambda x: str(x))
            f.write('%s & %s & %s & %s & %s%s%s \\\\\n' % (cell, nm, bold(a), bold(b), bold(c), of, note))
            last = label
    with open(os.path.join(out, 'stats.tex'), 'w') as f:
        for label, best, tot, lo, hi, pos, neg, p in stats:
            f.write('%s & %s & %+d & [%+d, %+d] & %d / %d & %s \\\\\n' % (
                label, best, tot, lo, hi, pos, neg, ('%.3f' % p) if p >= 0.001 else '$<$0.001'))
    with open(os.path.join(out, 'latency.tex'), 'w') as f:
        for label, n, p50, p90, p99 in lat:
            f.write('%s & %d & %.3f & %.2f & %.2f \\\\\n' % (label, n, p50, p90, p99))
    with open(os.path.join(out, 'losses.tex'), 'w') as f:
        for label, dom, s, n, better in losses:
            f.write('%s & \\nolinkurl{%s} & %d/%d & %s \\\\\n' % (label, dom, s, n, better))
    cactus(data, os.path.join(out, 'cactus.pdf'))
    with open(os.path.join(out, 'quality.tex'), 'w') as f:
        for key in ('classical', 'b3'):
            label, limit, runs = data[key]
            for name, score, n in quality(runs):
                f.write('%s & %s & %.1f & %d \\\\\n' % (label, '\\sys' if name == 'Kairos' else name,
                                                      score, n))
            f.write('\\midrule\n')
    unsolvable(out, kdir)
    if kdir:
        ablation(kdir, out)
    print('\n'.join('%s %s %s %s %s%s%s' % r for r in full))
    print()
    for s in stats:
        print(s)
    for l in lat:
        print(l)
    print(len(losses), 'losses')
    for l in losses:
        print(l)


def quality(runs):
    """IPC score at the limit: best cost over the planners that solved the task / own cost."""
    costs = collections.defaultdict(dict)
    for name, rows, short in runs:
        for r in rows:
            if r['status'] == 'solved' and r['cost'] not in ('', None):
                costs[(r['domain'], r['problem'])][name] = float(r['cost'])
    out = []
    for name, rows, short in runs:
        score = 0.0
        for task, c in costs.items():
            if name in c:
                best = min(c.values())
                score += 1.0 if c[name] <= 0 else (best / c[name] if best > 0 else 0.0)
        out.append((name, score, sum(name in c for c in costs.values())))
    return out


def unsolvable(out, kdir=None):
    """Answers of each planner on the generated tasks of the feature bank that have no plan."""
    bank = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'featurebank', 'generated')
    tasks = {}
    for t in json.load(open(os.path.join(bank, 'manifest.json'))):
        if not t['solvable']:
            fam = 'features/%s/%s' % (t['feature'], t['family'])
            tasks[(fam, os.path.basename(t['problem']))] = '%s/%s' % (t['feature'], t['family'])
    kf = os.path.join(kdir, 'kairos_features.csv') if kdir else 'step31/kairos2_features.csv'
    runs = [('Kairos', kf), ('lama-first', 'features/lama-first.csv'),
            ('OPTIC', 'features/optic.csv'), ('POPF', 'features/popf.csv'),
            ('ENHSP', 'features/enhsp.csv')]
    answers = {}
    for name, rel in runs:
        for r in load(os.path.join(R, rel)):
            key = (r['domain'], r['problem'])
            if key in tasks:
                answers[(name, key)] = r['status']
    with open(os.path.join(out, 'unsolvable.tex'), 'w') as f:
        for key in sorted(tasks):
            f.write('\\texttt{%s} & ' % tasks[key] + ' & '.join(
                answers.get((n, key), '--').replace('noplan', 'no plan found') for n, _ in runs) + ' \\\\\n')
    print('unsolvable', {k: [answers.get((n, k)) for n, _ in runs] for k in tasks})


def ablation(kdir, out):
    """Kairos against its variants run alone (bench/paper_battery.sh ablation)."""
    rows = [('Temporal', 'b1', [('full', 'kairos'), ('M2 only', 'm2'), ('M3 only', 'm3')]),
            ('Concurrency', 'b2', [('full', 'kairos'), ('M2 only', 'm2'), ('M3 only', 'm3')]),
            ('Classical', 'classical', [('full', 'kairos'), ('LAMA, no novelty fallback', 'lama'),
                                        ('lazy FF', 'ff')]),
            ('Numeric', 'b3', [('full', 'kairos'), ('LAMA, no novelty fallback', 'lama'),
                               ('lazy FF', 'ff')]),
            ('PlanSys2 at scale', 'b6', [('full', 'kairos'), ('no incremental goals', 'lama')])]
    with open(os.path.join(out, 'ablation.tex'), 'w') as f:
        for label, suite, variants in rows:
            for i, (name, prefix) in enumerate(variants):
                path = os.path.join(kdir, '%s_%s.csv' % (prefix, suite))
                if not os.path.exists(path):
                    continue
                t = solved_times(load(path))
                cells = (sum(x <= 0.1 for x in t), sum(x <= 1.0 for x in t), len(t))
                f.write('%s & %s & %d & %d & %d \\\\\n' % (label if i == 0 else '', name, *cells))
            f.write('\\midrule\n')
    print(open(os.path.join(out, 'ablation.tex')).read())


def cactus(data, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 7, 'axes.linewidth': 0.5, 'font.family': 'serif'})
    ink, muted, grid = '#0b0b0b', '#52514e', '#e4e3df'
    # Kairos and the two best others with first-plan times; colour, dash and a direct label
    styles = [('#2a78d6', '-'), ('#eb6834', '--'), ('#1baf7a', ':')]
    keys = list(data)
    fig, axes = plt.subplots(3, 3, figsize=(6.5, 5.6))
    for ax, key in zip(axes.flat, keys):
        label, limit, runs = data[key]
        n = len(runs[0][1])
        firsts = [(len(solved_times(r)), nm, r) for nm, r, short in runs[1:] if short]
        firsts.sort(key=lambda x: -x[0])
        shown = [('Kairos', runs[0][1])] + [(nm, r) for c, nm, r in firsts[:2]]
        # Direct labels at the curves' ends, pushed apart when they would overlap
        ends = []
        for (nm, rows), (col, ls) in zip(shown, styles):
            t = [max(x, 1e-3) for x in solved_times(rows)]
            xs = [1e-3] + t + [limit]
            ys = [0] + list(range(1, len(t) + 1)) + [len(t)]
            ax.step(xs, ys, where='post', color=col, linestyle=ls, linewidth=1.2)
            ends.append([len(t), nm])
        ends.sort(key=lambda e: -e[0])
        for i in range(1, len(ends)):
            ends[i][0] = min(ends[i][0], ends[i - 1][0] - 0.07 * n)
        for y, nm in ends:
            ax.annotate(nm, (limit, y), xytext=(2, 0), textcoords='offset points',
                        fontsize=5.5, color=ink, va='center', ha='left')
        ax.set_xscale('log')
        ax.set_xlim(1e-3, limit)
        ax.set_ylim(0, n)
        for x in (0.1, 1.0):
            ax.axvline(x, color=grid, linewidth=0.6, zorder=0)
        ax.set_title('%s (%d)' % (label, n), fontsize=7, color=ink, loc='left')
        ax.tick_params(colors=muted, length=2, width=0.5)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
        for s in ('left', 'bottom'):
            ax.spines[s].set_color(muted)
    for ax in axes[-1]:
        ax.set_xlabel('time to first plan (s)', color=muted)
    for ax in axes[:, 0]:
        ax.set_ylabel('tasks solved', color=muted)
    fig.tight_layout(w_pad=3.2)
    fig.savefig(path)


if __name__ == '__main__':
    main()
