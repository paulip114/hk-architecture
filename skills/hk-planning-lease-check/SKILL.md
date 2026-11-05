---
name: "hk-planning-lease-check"
description: "Check a Hong Kong scheme against its Outline Zoning Plan and Government lease: permitted uses, OZP plot ratio and building height, lease GFA, user and site coverage, and whether s16, s12A, lease modification or premium is needed."
---

# HK OZP and lease check

Use when the user asks whether a scheme is permitted under the OZP, whether it needs a s16 / s12A application, whether it complies with the lease, or what lease modification, premium or programme to expect.

## Before starting
1. Read `/mnt/project-files/architect-kb/planning/planning-rules.md` and `/mnt/project-files/architect-kb/lands/lands-rules.md`.
2. Note the items marked [verify] and the open items. Say so in the report if the result depends on one.

## Gather inputs
Ask only for what is missing (one message, short list):
- OZP number and zone; the zone's Column 1 and Column 2 uses and Remarks (PR, BH in mPD, SC, NBA, minor relaxation clause). If the user cannot give them, ask for the Notes PDF or the OZP extract from the Statutory Planning Portal.
- Proposed uses (in the OZP's own terms), site formation level and main roof level in mPD, roof-top structures with heights.
- Lease: lot number, user clause, max / min GFA, SC, height, GFA exemption clause, DDH clause, building covenant. Ask for the lease and all modification letters if the user has them.
- Floor schedule for GFA (same `floors[]` as the B(P)R checker).
- For the Bonus PR pilot: district, OP year of the existing building.

## Run
1. Write the floors to a project JSON (see `examples/demo_composite.json`) and the `planning_lease` block (see `examples/demo_composite_planning.json`; field list in the tool's docstring).
2. Run `python3 /mnt/project-files/architect-kb/tools/planning_lease_check.py <project>.json --block <planning>.json -o <report>.md`.
3. Save input and report under `/mnt/project-files/projects/<project-name>/`.

## Report back
- Lead with the route: as of right, s16, s12A, lease modification, consent with premium; then each FAIL / CHECK item with the fix.
- Give the indicative programme (s16 ≈ 2 months to decision; lease modification ≈ 16–18 months without appeal).
- Premium figures from the tool are indicative only. Bonus PR values use LAO PN 9/2026 rates.
- Always state: draft for review by an Authorized Person and planning / land consultants; OZP and lease figures as given by the user.

## Limits
The tool does not read the OZP or lease itself, does not value land, and does not check rural OZP temporary-use rules, Small House policy, NBA geometry or building gaps. Flag these if relevant.
