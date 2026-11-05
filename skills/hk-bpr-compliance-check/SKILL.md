---
name: "hk-bpr-compliance-check"
description: "Check a Hong Kong building scheme against the Building (Planning) Regulations: site class, site coverage, plot ratio, GFA exemptions, open space, lighting and ventilation."
---

# HK B(P)R compliance check

Use when the user asks to check GFA, plot ratio, site coverage, open space, or lighting/ventilation of a Hong Kong scheme, or to test a massing option against Cap. 123F.

## Before starting
1. Read `/mnt/project-files/architect-kb/README.md` and `/mnt/project-files/architect-kb/bpr/bpr-rules.md`.
2. Note which First Schedule cells are listed under `_uncertain` in `bpr/first_schedule.json`. If the result depends on one of them, say so in the report.

## Gather inputs
Ask only for what is missing (one message, a short list):
- Site area; street widths and frontage (or the site class); dedicated/surrendered land.
- Building type (domestic / non-domestic / composite) and height from mean street level.
- OZP limits (PR, height) and lease GFA limits, if known. Lease and OZP usually govern more tightly than B(P)R.
- Floor schedule: gross area and footprint per floor (typical floors with `count`), and each GFA exemption claimed with its category.
- Domestic open space and roofed-over area.
- Rooms for lighting/ventilation: floor area, glass area, openable area, window head height, furthest point to window.
If the user gives drawings or a Revit/Excel area schedule instead, extract these figures yourself and state any you assumed.

## Run
1. Write the inputs to a JSON file following `examples/demo_composite.json` (field list in README).
2. Run `python3 /mnt/project-files/architect-kb/tools/bpr_check.py <file>.json -o <report>.md`.
3. Save input and report under `/mnt/project-files/projects/<project-name>/`.

## Report back
- Lead with the verdict and every FAIL / CHECK item with the fix (e.g. how much openable area to add, how much GFA to cut, which exemption is at risk under the APP-151 10% cap).
- For composite buildings give the remaining domestic PR headroom from the reg 21(2) result.
- Always state: draft for review and signature by an Authorized Person; First Schedule figures unverified until checked against eLegislation Cap. 123F.
- Do not present the output as a statutory submission.

## Limits
The tool does not check means of escape (FS Code 2011), staircases, EVA, barrier-free access, reg 31 inclined planes, or performance-based L&V (APP-130). Flag these as outstanding if the scheme needs them.