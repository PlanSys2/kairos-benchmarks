# F0 baseline: Kairos and other planners

2026-10-11. Kairos 0.3.0 (023fe98) against OPTIC, TFD, POPF, LPG-TD, ENHSP-2020, Metric-FF and
LAMA from planutils (image built from bench/planutils/Dockerfile). 30 s and 3 GB per problem,
one CPU each, 8 processes at a time on a 16-core laptop. Every plan was validated by Kairos.
Regenerate: `python3 bench/f0_report.py > bench/results/f0/report.md` (add the notes back).

## Summary

| Suite | Kairos | Best other |
|---|---:|---|
| docs/examples, robotics (11) | **11** | OPTIC 8 |
| B2, required concurrency and temporal numeric (55) | **32** | POPF 24, TFD 24 |
| B1, temporal IPC 2002-2014 (225) | **161** | LPG-TD 125, TFD 110, OPTIC 107 |
| B3, numeric IPC 2002/2023/2026 (420) | **252** | ENHSP 103, Metric-FF 57 |
| classical IPC 1998-2023 (220) | 120 | **LAMA 151** |

- Temporal and numeric: Kairos solves the most and has the best quality score everywhere.
- Classical: Fast Downward's LAMA solves 31 more (barman 10 vs 0, sokoban 9 vs 3, parking 10
  vs 7, hiking 10 vs 6, rubiks-cube 10 vs 6).
- Domains to look at (others solve more): turn-and-open and parc-printer (TFD), floor-tile and
  satellite with time windows (LPG-TD), parking (temporal and classical), depots-numeric and
  settlers (Metric-FF: 9 and 3 vs 2 and 0).

## Notes on the method

- Kairos runs anytime and its first-plan time is its agile time; the anytime planners (OPTIC,
  LPG-TD with -quality, LAMA) run until the timeout, so their agile score is not comparable.
  Solved and quality are.
- Quality: IPC score, best cost among the planners that solved the problem divided by the own
  cost (metric, or makespan, or steps).
- "invalid plans" counts plans Kairos's validator rejected; for Kairos itself the 10 in classical
  are not plans but inputs it rejects: the suite picks the per-problem domain files of
  quantum-layout (domain_pNN.pddl) as problems, a bug of the suite that affects every planner.
- ENHSP runs with -planner sat-hmrphj; it does not read some IPC 2002 domains ("Depot not found")
  and Java hits the 3 GB limit in some problems. Metric-FF does not read most IPC 2023/2026
  domains. Both numbers are below what their best configurations reach.
- LPG-TD sometimes announces a plan file it never writes: runs that fail at once are retried
  twice. POPF from planutils is not the PlanSys2 build used elsewhere in this project.

## Details

### docs/examples (robotics) (11 problems)

| planner | solved | quality (IPC score) | invalid plans |
|---|---:|---:|---:|
| kairos | 11 | 9.2 | 0 |
| lpg-td | 2 | 2.0 | 1 |
| optic | 8 | 8.0 | 0 |
| popf | 6 | 5.4 | 1 |
| tfd | 5 | 3.8 | 0 |

### B2: required concurrency, temporal numeric (55 problems)

| planner | solved | quality (IPC score) | invalid plans |
|---|---:|---:|---:|
| kairos | 32 | 30.6 | 0 |
| lpg-td | 0 | 0.0 | 0 |
| optic | 17 | 16.6 | 0 |
| popf | 24 | 23.6 | 5 |
| tfd | 24 | 22.0 | 0 |

Domains where another planner solves more than Kairos:

| domain | Kairos | better |
|---|---:|---|
| ipc-2004/airport-temporal-time-windows-compiled-strips | 2 | popf 3 |
| ipc-2011/temporal-machine-shop-temporal-satisficing | 0 | popf 1 |
| ipc-2011/turn-and-open-temporal-satisficing | 2 | tfd 5 |
| ipc-2014/turn-and-open-temporal-satisficing | 2 | tfd 3 |

### B1: temporal, IPC 2002-2014 (225 problems)

| planner | solved | quality (IPC score) | invalid plans |
|---|---:|---:|---:|
| kairos | 161 | 140.0 | 0 |
| lpg-td | 125 | 109.6 | 14 |
| optic | 107 | 99.1 | 2 |
| popf | 104 | 91.2 | 2 |
| tfd | 110 | 80.2 | 1 |

Domains where another planner solves more than Kairos:

| domain | Kairos | better |
|---|---:|---|
| ipc-2004/airport-temporal-strips | 4 | tfd 5 |
| ipc-2004/satellite-time-time-windows-strips | 1 | lpg-td 3, optic 2 |
| ipc-2006/pathways-metric-time | 2 | lpg-td 3 |
| ipc-2006/storage-time | 3 | lpg-td 4 |
| ipc-2006/trucks-time-constraints-timed-initial-literals | 1 | lpg-td 2, optic 2, popf 2 |
| ipc-2008/elevator-temporal-satisficing-strips | 4 | tfd 5 |
| ipc-2008/parc-printer-temporal-satisficing-strips | 2 | tfd 4 |
| ipc-2011/floor-tile-temporal-satisficing | 3 | lpg-td 4 |
| ipc-2011/parc-printer-temporal-satisficing | 0 | tfd 3 |
| ipc-2011/parking-temporal-satisficing | 4 | popf 5 |
| ipc-2014/floor-tile-temporal-satisficing | 0 | lpg-td 5 |
| ipc-2014/parking-temporal-satisficing | 3 | lpg-td 5, tfd 5, optic 4 |
| ipc-2014/satellite-temporal-satisficing | 4 | lpg-td 5 |

### B3: numeric, IPC 2002/2023/2026 (420 problems)

| planner | solved | quality (IPC score) | invalid plans |
|---|---:|---:|---:|
| kairos | 252 | 249.3 | 0 |
| enhsp-2020 | 103 | 89.2 | 28 |
| metric-ff | 57 | 49.5 | 10 |

Domains where another planner solves more than Kairos:

| domain | Kairos | better |
|---|---:|---|
| ipc-2002/depots-numeric-automatic | 2 | metric-ff 9 |
| ipc-2002/driverlog-numeric-automatic | 9 | enhsp-2020 10 |
| ipc-2002/settlers-numeric-automatic | 0 | metric-ff 3 |

### classical, IPC 1998-2023 (220 problems)

| planner | solved | quality (IPC score) | invalid plans |
|---|---:|---:|---:|
| kairos | 120 | 113.5 | 10 |
| lama | 151 | 148.9 | 0 |

Domains where another planner solves more than Kairos:

| domain | Kairos | better |
|---|---:|---|
| ipc-2000/blocks-strips-typed | 6 | lama 8 |
| ipc-2002/depots-strips-automatic | 8 | lama 9 |
| ipc-2008/sokoban-sequential-satisficing-strips | 3 | lama 9 |
| ipc-2011/barman-sequential-satisficing | 0 | lama 10 |
| ipc-2011/parking-sequential-satisficing | 7 | lama 10 |
| ipc-2014/hiking-sequential-satisficing | 6 | lama 10 |
| ipc2023/folding | 1 | lama 3 |
| ipc2023/recharging-robots | 0 | lama 2 |
| ipc2023/ricochet-robots | 0 | lama 1 |
| ipc2023/rubiks-cube | 6 | lama 10 |

