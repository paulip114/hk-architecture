---
name: "hk-sketch-drawings"
description: "Generate sketch floor plans (DXF/SVG), an IFC massing model and area schedules for a Hong Kong scheme from parameters, or take off areas from an existing DXF."
---

# HK sketch drawings, IFC massing and area take-off

Use when the user asks for a plan layout, a test fit, an area schedule, a BIM / IFC massing model, or areas from a DXF.

## Before starting
1. Read `/mnt/project-files/architect-kb/drawing/drawing-rules.md`.
2. Install if needed: `pip install -r /mnt/project-files/architect-kb/requirements-drawing.txt`.
3. Say up front: these are sketch / study drawings, not BD submission drawings, which the AP prepares and signs.

## Run
- Write a `drawing` block (site boundary, grid, floors with footprint, cores, rooms; metres) following `examples/demo_practice.json`.
- `python3 .../tools/dxf_plan.py <file>.json -o plans.dxf --areas areas.json --svg plans.svg`
- `python3 .../tools/ifc_model.py <file>.json -o model.ifc`
- Existing drawing: `python3 .../tools/dxf_area_takeoff.py <file>.dxf --layers <layers> -o areas.md`
- Pass `areas.json` floors to `bpr_check.py` (add exemptions) and `cost_estimate.py`.
- Save under `/mnt/project-files/projects/<project-name>/` and attach the SVG preview for the user.

## Report back
GFA and site coverage per floor, every CHECK warning (outside site, outside footprint, overlaps, open outlines), and the next check to run (B(P)R, MOE).
