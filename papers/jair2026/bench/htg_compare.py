"""Per family comparison of htg results: python3 bench/htg_compare.py NAME... (bench/results/htg/NAME.csv)."""
import collections
import csv
import sys

names = sys.argv[1:]
res = {p: list(csv.DictReader(open(f'bench/results/htg/{p}.csv'))) for p in names}
agg = collections.OrderedDict()
for p in names:
    for r in res[p]:
        d = r['domain'].split('/')[1]
        agg.setdefault(d, {q: [0, 0] for q in names})
        agg[d][p][1] += 1
        agg[d][p][0] += r['status'] == 'solved'
print(f"{'family':36s} " + ' '.join(f'{n[-10:]:>10s}' for n in names))
for d, v in sorted(agg.items()):
    print(f'{d:36s} ' + ' '.join(f'{v[n][0]:10d}' for n in names) + f'  /{v[names[0]][1]}')
for n in names:
    t = [float(r['time']) for r in res[n] if r['status'] == 'solved']
    print(f'{n:14s} total {len(t)}  1 s {sum(x <= 1 for x in t)}  100 ms {sum(x <= 0.1 for x in t)}')
