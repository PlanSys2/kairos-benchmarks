# combat: PlanSys2's two-army robot battle (snapshot)

A copy, taken on 2026-10-12, of the combat example of PlanSys2 (Francisco Martín Rico): one
domain (`domain.pddl`, from plansys2_combat_example/pddl/combat.pddl), the scenarios s1-s7 and their
`_mixed` variants (`scenarios/`, written by `gen.py`), the minimal problems m1-m12 that isolate
planner failures (`mini/`, with a hand-written plan for m6), and hand-written plans of s1/s2
(`plans/`). A copy so that changes to the example do not move the reference silently.

What it exercises: required concurrency (artillery bombards only while a drone spots), a cost
metric in euros (and euros + time in `_mixed`), numeric resources (battery, ammunition), over all
conditions with a negated existential ("no known enemy in the zone"), and replanning scenarios.
