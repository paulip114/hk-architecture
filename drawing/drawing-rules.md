# Design drawings and BIM tooling

What Claude can and cannot produce, and the tools that close part of the gap. Tools: `../tools/dxf_plan.py`, `../tools/ifc_model.py`, `../tools/dxf_area_takeoff.py`.

**[V]** tested in this repo on 2026-11-05 (ezdxf 1.4.5, ifcopenshell 0.9.0, shapely 2.2). **[U]** unverified.

## Limits (read first)
- Claude cannot produce BD submission drawings. General building plans must follow the BD's requirements for plans (B(A)R regs 8-9 and the related PNAPs) and be prepared and signed by the AP. **[U reg numbers]**
- The tools produce sketch / study drawings, area schedules and massing models: inputs to the design team's CAD / BIM, not substitutes for it.
- Every output carries "SKETCH – NOT FOR SUBMISSION".

## Workflow
1. Describe the scheme as a `drawing` block (site boundary, grid, per-floor footprint, cores, rooms). See `examples/demo_practice.json`.
2. `python3 tools/dxf_plan.py project.json -o plans.dxf --areas areas.json --svg plans.svg`: plan per floor with grid, setback lines, wall band, room names and areas, title block, north point; prints GFA and site coverage per floor; flags footprints outside the site, rooms outside the footprint, overlapping rooms. **[V]**
3. Copy `areas.json` `floors[]` into the B(P)R project and add exemptions, then run `bpr_check.py`. Feed the same floors to `cost_estimate.py` (`from_floors`). **[V]**
4. `python3 tools/ifc_model.py project.json -o model.ifc`: IFC4 storeys, slabs, external walls, and IfcSpace with NetFloorArea. Validates clean with `ifcopenshell.validate`. Opens in BlenderBIM / Bonsai; Revit and ArchiCAD import IFC4. **[V file validity; U app import not tested here]**
5. For drawings from the design team: `python3 tools/dxf_area_takeoff.py their.dxf --layers <area layers>` takes off closed polylines, names them from text inside, subtracts holes and reports open or overlapping outlines. **[V on generated DXF; U on real Revit exports]**

## Layer convention (AIA / US National CAD Standard style)
A-SITE site boundary · A-SETB setback lines · A-GRID grid · A-WALL walls · A-CORE cores · A-ROOM room outlines · A-ROOM-IDEN names and areas · A-ANNO-* annotation, title block, north point. Map to the office standard (or BS EN ISO 13567) when exporting. **[U office mapping]**

## Other tool routes (not built here)
- **Revit**: pyRevit / Dynamo scripts to place rooms from the same JSON and push area schedules back. Needs Revit on the user's machine.
- **Rhino / Grasshopper**: massing and envelope studies (e.g. Ladybug for daylight and the APP-152 SBD permeability checks).
- **AutoCAD**: open the DXF directly; insert office title block and dimension styles.

## Drawing checklist for HK schemes (for the AP to confirm) **[U]**
- Site plan: lot boundary, street names and widths, mean street level, north point, site area, setbacks, EVA.
- Floor plans: room uses and dimensions, MOE (exits, travel distance, staircase widths), FSI, barrier-free provisions, areas for GFA and exemptions with colour coding.
- Sections: floor-to-floor heights, building height to main roof from mean street level, reg 31 lighting / ventilation planes.
- Area schedule: GFA, site coverage, exempted areas by PNAP category, open space.
