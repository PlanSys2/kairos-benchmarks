# Third-party problems

The suites (`suites/*.tsv`) name problems of these public collections, at the commits of
`sources.tsv`. None of them declares a license, so this repository does not copy their files:
`fetch.py` downloads them from their authors' repositories. Please cite the collections and the
competitions they come from when you use them.

| Source | Repository | What it holds |
|---|---|---|
| `potassco-pddl-instances` | https://github.com/potassco/pddl-instances | The domains and problems of the International Planning Competitions 1998 to 2014, gathered by the Potassco group (University of Potsdam) |
| `ipc2023-classical` | https://github.com/ipc2023-classical/ipc2023-dataset | The classical tracks of the IPC 2023 |
| `ipc2023-numeric` | https://github.com/ipc2023-numeric/ipc2023-dataset | The numeric track of the IPC 2023 |
| `ipc2026-numeric` | https://github.com/ipc2026-numeric/ipc2026-dataset | The numeric track of the IPC 2026 |
| `hstairs-pddl-plus-domains` | https://github.com/hstairs/pddl_plus_domains | PDDL+ domains gathered by Enrico Scala and colleagues (ENHSP) |
| `hstairs-time2processes` | https://github.com/hstairs/time2processes | Temporal numeric domains of the time2processes work (Scala and colleagues) |
| `htg-domains` | https://github.com/abcorrea/htg-domains | Hard-to-ground benchmarks of the lifted planning papers (Augusto B. Corrêa and colleagues) |
| `smtplan` | https://github.com/KCL-Planning/SMTPlan | The benchmarks of SMTPlan+ (King's College London planning group) |

The domains of `generated/plansys2-scale/domains` come from the packages of PlanSys2
(https://github.com/PlanSys2, Apache-2.0); `generated/combat` is PlanSys2's combat example.
