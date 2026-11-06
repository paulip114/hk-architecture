---
name: "hk-design-guides-check"
description: "Check a Hong Kong scheme against PNAP APP-152 (building separation, setback, greenery) and the Design Manual: Barrier Free Access 2008."
---

# HK APP-152 and barrier-free access check

Use when the user asks whether a scheme meets APP-152 sustainable building design, whether APP-151 GFA concessions are safe, or whether the design meets barrier-free access requirements.

## Before starting
Read `/mnt/project-files/architect-kb/pnap/app152-rules.md` and `/mnt/project-files/architect-kb/bfa/bfa-rules.md`, and the `_unverified` lists in `pnap/app152.json` and `bfa/bfa2008.json`.

## Run
1. Write `sustainable_design` and / or `barrier_free` blocks following `examples/demo_composite_design.json`.
2. `python3 tools/sbd_check.py <file>.json -o <app152-report>.md`
3. `python3 tools/bfa_check.py <file>.json -o <bfa-report>.md`
4. Save under `/mnt/project-files/projects/<project-name>/`.

## Report back
- Lead with each FAIL and the fix (e.g. setback the lowest 15 m by another 1.5 m; add a tactile guide path; split a 17-riser flight).
- An APP-152 FAIL puts APP-151 GFA concessions at risk: say so.
- Say which results rest on unverified figures (BFA Chapter 6).
- Draft for review and signature by an Authorized Person, not a submission.
