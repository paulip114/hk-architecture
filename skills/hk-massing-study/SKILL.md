---
name: "hk-massing-study"
description: "Run a Hong Kong massing study: development envelope by height band, compare podium/tower options for GFA, PR, SC and height, and test each against B(P)R."
---

# HK massing study

Use when the user asks for massing options, a development envelope, how much GFA a site can take, how many storeys, or podium/tower configurations for a Hong Kong site.

## Before starting
1. Read `/mnt/project-files/architect-kb/design/massing/massing-methods.md` and `/mnt/project-files/architect-kb/bpr/bpr-rules.md`.

## Gather inputs (ask once, short list, only what is missing)
- Site area, street widths and frontage (or site class), mean street level in mPD.
- OZP zone, max PR / GFA, height limit (mPD), NBA or setback; lease GFA and height.
- Intended uses and mix (domestic / non-domestic / composite), car parking in basement or podium.
State any assumption you make (floor-to-floor heights, exemption %).

## Run
1. Envelope first: `python3 /mnt/project-files/architect-kb/tools/massing_study.py --envelope --site-area A --site-class B --use domestic --ftf 3.15 --ground-ftf 4.5 --max-height H`.
2. Write 3 options (max-out, best design, compromise) to a JSON following `examples/demo_massing.json`.
3. `python3 /mnt/project-files/architect-kb/tools/massing_study.py options.json -o report.md --write-projects /mnt/project-files/projects/<name>/massing`.
4. Adjust storeys / plates until at least one option passes, and say what each failing option needs to change.

## Report back
- Lead with the recommended option and its GFA, PR, height (m and mPD), storeys.
- Comparison table plus qualitative scores (views, ventilation, shadow, transfer structure, efficiency, SBD facade length).
- Flag what the tool does not check: APP-152 SBD, APP-151 cap with real figures, refuge floors (B18), EVA, AVA / VIA.
- Draft for AP review; exemption percentages are estimates.
