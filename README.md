# kairos-benchmarks

The PDDL benchmarks used to develop and evaluate [Kairos](https://github.com/PlanSys2/kairos),
a planner for robotics. Results of Kairos and other planners on them are in Kairos's
[benchmark page](https://github.com/PlanSys2/kairos/blob/main/docs/benchmark.md). The scripts,
raw results and plans behind the article on Kairos are in [papers/jair2026](papers/jair2026).

There are two kinds of benchmarks here:

- **Suites of public problems** (`suites/`), listed and not copied: each file names the
  problems by collection, commit, path and sha256. `fetch.py` downloads exactly those files
  and checks them. The collections declare no license, so this repository does not
  redistribute them (see [THIRD_PARTY.md](THIRD_PARTY.md)).
- **Our own problems** (`generated/`, Apache-2.0), with their generators. They cover what no
  public collection has: object fluents, timed initial fluents, durations that must lie
  between their bounds, a robotic warehouse with hundreds of robots, and PlanSys2 problems at
  scale. Each feature family also has unsolvable problems, to catch planners that claim
  "unsolvable" falsely or print plans for impossible tasks.

## Suites of public problems

| Suite | Problems | What it is |
|---|---:|---|
| `classical` | 220 | Classical domains of the IPC 1998 to 2023, 10 problems each, easy to hard |
| `b1` | 225 | Temporal domains of the IPC 2002 to 2014, 5 problems each |
| `b2` | 55 | Required concurrency (match-cellar, turn-and-open, temporal-machine-shop) and temporal numeric domains of time2processes |
| `b3` | 420 | Numeric domains of the IPC 2002, 2023 and 2026, 10 problems each |
| `prefs` | 125 | IPC 2006 domains with preferences and trajectory constraints, 5 problems each |
| `pddlplus` | 255 | PDDL+ domains of hstairs (processes, events, global constraints) and the benchmarks of SMTPlan (non-linear continuous effects) |
| `htg` | 287 | Hard-to-ground tasks of the lifted planning papers (millions of ground actions), 5 per folder |
| `features` | 726 | Per PDDL feature, up to 6 families that use it, 5 problems each, easiest to hardest |

The `features` suite was chosen by the features each domain uses, as reported by
`kairos check DOMAIN PROBLEM`: typing, negative, disjunctive, existential and universal
preconditions, equality, conditional effects, numeric fluents (linear and non-linear), action
costs, durative actions, duration inequalities, variable durations, `?duration` in effects,
continuous effects, derived predicates, timed initial literals, preferences, trajectory
constraints, processes, events, global constraints and metrics. Families come from different
collections where possible.

```console
$ ./fetch.py                      # all suites (about 190 MB), into ~/.cache/kairos-benchmarks
$ ./fetch.py htg pddlplus         # some
$ ./fetch.py --list classical     # "label domain problem" lines, absolute paths
```

Each suite file is a TSV: `label`, `source` (a collection of `sources.tsv`, or
`kairos-benchmarks` for a problem of this repository), the paths of the domain and problem
inside it, and their sha256.

## Our own problems

| Folder | Problems | What it is |
|---|---:|---|
| `generated/features/object-fluents` | 24 | Delivery with several robots, an elevator, keys and doors (a static object fluent in preconditions), and a temporal delivery: functions whose values are objects, assigned and set to `undefined` |
| `generated/features/timed-initial-fluents` | 18 | Prices that drop for a while, a power grid that gives power in windows, travel times that rise at rush hour: numeric fluents changed at given times |
| `generated/features/warehouse` | 27 | A robotic warehouse: robots bring shelves to picking stations and back, from 5 to 400 robots; levels with free zones, zones with a capacity, and one robot per cell; a temporal version with batteries and stations used one at a time |
| `generated/durations` | 25 | Five domains where neither bound of the key action's duration gives a plan, only one in between: a recharge in a closing window, an oven with `?duration` in its effect, filling a tank, a shared charger, drilling to a depth range |
| `generated/plansys2-scale` | (generator) | Domains of PlanSys2 packages with problems from ~10 to ~20 000 objects and a reference plan each (`gen.py OUT_DIR`) |
| `generated/combat` | 56 | PlanSys2's two-army robot battle: required concurrency, costs in euros, resources, and minimal problems that isolate planner failures |

`generated/features/expected.tsv` says for each generated problem whether it has a plan; in
each family the last problem is the one without (a station cut off, a key behind its own door,
money one unit short...). The warehouse problems come with a reference plan (`pNN.plan`),
built along with the problem, that proves they have one. The generators are deterministic
(seeded): running `gen.py OUT_DIR` again writes the same files.

## Using it

Any planner can run the problems; plans are best checked with an independent validator (VAL,
or `kairos validate DOMAIN PROBLEM PLAN`, which also handles PDDL+ in continuous time). The
measurements of Kairos's benchmark page use 30 s and 3 GB per problem, every plan validated.

## License

Our files are under the Apache License 2.0 ([LICENSE](LICENSE)). The suites only name
third-party files; those belong to their authors ([THIRD_PARTY.md](THIRD_PARTY.md)).
