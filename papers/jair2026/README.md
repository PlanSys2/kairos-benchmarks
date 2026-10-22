# Kairos article (JAIR): scripts, results and plans

This directory holds everything behind the tables and figures of the article on Kairos
submitted to the Journal of Artificial Intelligence Research: the scripts as they were run, the
raw results of every run (Kairos and the other planners), Kairos's plans, the comparison of
Kairos's validator with VAL, and the recipes of the containers in which the other planners ran.
The problems are not copied here: the public ones are named by the suites of this repository,
and ours are in `../../generated`.

The layout is the one the scripts expect, so run them from this directory (`papers/jair2026`).

## Regenerate the tables of the article

```console
python3 bench/paper_tables.py OUT_DIR --kairos-dir bench/results/paper
```

This writes `stats.tex`, `latency.tex`, `quality.tex`, `unsolvable.tex`, `ablation.tex`,
`coverage_full.tex`, `losses.tex` and `cactus.pdf` (needs matplotlib) from the CSVs in
`bench/results`. No planner or problem is needed. The output is identical to the tables of the
article.

## What is where

| Path | Content |
|---|---|
| `bench/results/paper/kairos_SUITE.csv`, `.log` | Kairos 1.0.6 on each suite (`paper_battery.sh main`) |
| `bench/results/paper/battery.out` | the summary of the runs; its "kairos 1.0.0" lines are the version printed by a shell whose `LD_LIBRARY_PATH` found an older library, which the runs did not use (they run with `LD_LIBRARY_PATH` unset and load the 1.0.6 library next to the binary; `paper_battery.sh` now prints the version the same way) |
| `bench/results/paper/{m2,m3,ff,lama,...}_SUITE.csv` | the ablation runs (`paper_battery.sh ablation`) |
| `bench/results/paper/*_probes.csv` | the support probes, every planner (`paper_battery.sh support`) |
| `bench/results/paper/plans_*` | the plans of those runs, one file per problem (anytime runs keep every plan; the last one counts) |
| `bench/results/{sota,f0,htg,pddlplus,prefs,durations,b6,features,quantum,step31}` | the other planners' runs, and Kairos's development runs that `paper_tables.py` reads |
| `bench/results/paper/val_compare.csv` | Kairos's validator and VAL on every plan of Kairos and its broken variants (Section Q4 of the article) |
| `bench/results/paper/val_compare.csv.d` | those plans: `ID.plan` as Kairos's validator read it, `ID.val.plan` as VAL read it (no `@PlanEND`), and `manifest.tsv` with the domain and problem of each ID |
| `bench/results/paper/val_compare_probes.csv` | the same on the probes |
| `bench/probes` | the 26 one-feature probes of the support table |
| `bench/planutils`, `bench/sota`, `bench/up` | Dockerfiles of the containers of the other planners (planutils, planners built from source at pinned commits, Unified Planning's TAMER and Aries) |
| `bench/*.py`, `bench/*.sh` | the scripts: `coverage.py` runs a planner on a suite, `paper_battery.sh` the runs of the article, `val_compare.py` the comparison with VAL, `paper_tables.py` the tables, `support_table.py` the support table |

## The disagreements with VAL

The IDs below index `val_compare.csv` (row number, from 0) and the files of
`val_compare.csv.d`. `manifest.tsv` gives the domain and problem of each, under the
corpus that `tools/fetch_corpus.sh` of the Kairos repository downloads.

| IDs | Problem | Plan | Kairos | VAL | Why |
|---|---|---|---|---|---|
| 2081–2102, 2682–2691 (13) | car_nodrag (SMTPlan), PDDL+ suite and feature bank | Kairos's plan | valid | invalid | Two `decelerate` steps at the same instant. Applied in order (ENHSP's convention) they are valid; VAL evaluates both on the state before and rejects them as mutex. A difference of convention. |
| 564 | sugar pfile15 (IPC 2023 numeric) | a step removed | invalid | valid | Step 11 needs `(> (in-storage brand1 mill3) 0)`, which is 0. |
| 756, 760, 762, 764 | petri-net prob08-3, prob09-3, prob10-1, prob10-3 (IPC 2026 numeric) | a step removed | invalid | valid | A later step needs `(> (value ?p1) 0)`, which is 0. |
| 1663 | tpp-metric-time-constraints instance-13 (IPC 2006) | Kairos's plan | valid | invalid | VAL reports `(sometime-before (> (stored goods2) 0) ...)` as violated at time 0, where `(stored goods2)` is 0; goods2 is first stored at 2699.013. |
| 2992, 2994 | tpp-metric-time-constraints instance-15 (IPC 2006, feature bank) | Kairos's plan, and a step moved | valid | invalid | The same, with goods1, first stored at 8053.036. |

To check one: `kairos validate DOMAIN PROBLEM ID.plan` prints the failing step and condition;
`Validate -v -t 0.001 DOMAIN PROBLEM ID.val.plan` (VAL 20210401, in the planutils image) prints
VAL's trace.

## Re-running the planners

The scripts read the third-party problems from `$KAIROS_PDDL_CORPUS` (default
`~/.cache/kairos/corpus`), in the layout of `tools/fetch_corpus.sh` of the Kairos repository,
and the other planners from the images built by the Dockerfiles above. `paper_battery.sh`
installs Kairos apart and runs every suite with the limits of the article (about 3.5
hours on the machine of the article).
