---
name: "hk-means-of-escape-check"
description: "Check a Hong Kong building's means of escape against the Code of Practice for Fire Safety in Buildings 2011 Part B: occupancy, exits, travel distance, staircases, refuge floors."
---

# HK means of escape check (FS Code 2011, Part B)

Use when the user asks about fire escape, exit widths, travel distance, staircase numbers/widths, discharge value, refuge floors or protected lobbies for a Hong Kong scheme.

## Before starting
1. Read `/mnt/project-files/architect-kb/README.md` and `/mnt/project-files/architect-kb/fs-code/moe-rules.md`.
2. For any clause the rules file does not cover, search `/mnt/project-files/architect-kb/fs-code-2011.txt` (full 2024 Edition text) and quote the clause number.

## Gather inputs
Ask only for what is missing, in one short list:
- Use classification and usable floor area of each storey (or seats / bedspaces); typical floors with `count`.
- Whether the whole building is sprinklered; storeys above ground; level of the top floor.
- Exit routes per storey with clear widths; worst travel distance and deadend distance; distance between stair doors and stair-to-stair distance.
- Each required staircase: clear width, storeys served, whether it serves basements, upward escape, scissors, pressurised / protected lobby / ventilated, tread, riser, risers per flight.
- Refuge floor storeys for buildings over 25 storeys.
If the user gives plans instead, measure these yourself and state assumptions.

## Run
1. Put the inputs in a `means_of_escape` block in the project JSON (template: `examples/demo_composite.json`).
2. Run `python3 /mnt/project-files/architect-kb/tools/moe_check.py <file>.json -o <report>.md`.
3. Save under `/mnt/project-files/projects/<project-name>/`.

## Report back
- Lead with the verdict and each FAIL with the fix (extra stair width needed for the discharge value, where to add an exit, how far to cut a deadend).
- State that the report is a draft for review and signature by an Authorized Person, and that Parts C, D, E, Use Class 5a special provisions and fire engineering are not checked.