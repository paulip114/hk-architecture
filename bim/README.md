# BIM scripts: HK area calculation and BD sheet set-up

pyRevit, Dynamo and Grasshopper tools for Hong Kong GFA, plot ratio and site coverage (B(P)R regs 20-23, PNAP APP-2 / APP-151) and for setting up the BD general building plans sheet set. They reuse the knowledge base in this repo:

- `bpr/first_schedule.json` gives the First Schedule limits (read directly).
- `tools/bpr_check.py` runs the full B(P)R check. The scripts write its input JSON, and on CPython engines they run it straight away.

Every output is a draft for review and signature by an Authorized Person.

## Layout

| Path | What it is | Engine |
| --- | --- | --- |
| `hk_bim/areas.py` | Area records, category aliases (English and Chinese), grouping into `floors[]` for bpr_check, area schedule CSV | IronPython 2.7 and CPython 3 |
| `hk_bim/bpr_limits.py` | First Schedule lookup, quick PR / SC / APP-151 check, development envelope for massing | both |
| `hk_bim/sheets.py` | BD GBP sheet template, drawing numbers (`GBP-020-05F`), title block fields, GFA colour legend | both |
| `hk_bim/massing.py` | Floor levels from floor-to-floor heights, plates to area records | both |
| `hk_bim/revit_adapter.py` | Reads Areas, levels and Project Information; creates sheets; binds shared parameters | Revit API |
| `hk_bim/rhino_adapter.py` | Slices breps, measures planar areas with holes, handles unit scale | RhinoCommon |
| `hk_bim/report.py` | Markdown output; calls `tools/bpr_check.py` on CPython 3 | both |
| `pyrevit/HKArch.extension` | pyRevit tab **HK Arch** with the buttons Setup Parameters, GFA Schedule, BD Sheets and Envelope | pyRevit 4.8+ / 5 |
| `revit/HK_shared_parameters.txt` | Shared parameters used by the tools | Revit |
| `dynamo/*.py` | Code for Python Script nodes: GFA schedule, BD sheets, envelope | Dynamo CPython3 |
| `grasshopper/*.py` | GhPython components: massing GFA check, area schedule from tagged curves, envelope | Rhino 7 / 8 |
| `tests/test_hk_bim.py` | Unit tests: `python3 -m unittest discover -s bim/tests -v` | CPython 3 |

## GFA categories

Set `HK_GFA_Category` on each Area (Revit), or use the curve's layer name or the `Category` input (Grasshopper). Blank values are matched from the space name, so "Lift machine room", "地庫停車場" and "A/C plant room" all resolve. Anything that cannot be resolved is listed and stops the run, so no area is counted by guesswork.

| Code | Treatment |
| --- | --- |
| `accountable` | Counted in GFA |
| `mandatory_plant` | 100% disregarded, reg 23(3)(b) |
| `non_mandatory_plant`, `green_feature` | 100% disregarded, subject to the APP-151 prerequisites and 10% cap |
| `green_feature_uncapped` | 100% disregarded, subject to the APP-151 prerequisites but not the cap, such as a sky garden or wider common corridor |
| `car_park_underground`, `car_park_above_100` | 100% disregarded |
| `car_park_above_50` | 50% disregarded |
| `refuge_floor`, `bicycle_parking`, `other_disregarded` | 100% disregarded (the AP must justify) |
| `not_gfa` | Voids and open areas: not floor space, left out of the schedule totals |

The fractions are the same table as `EXEMPT_FRACTION` in `tools/bpr_check.py`, and a unit test fails if the two ever differ.

## Revit (pyRevit)

1. Install pyRevit, then add this repo's `bim/pyrevit` folder under pyRevit Settings > Custom Extension Directories, and reload. The extension finds `hk_bim` two folders up. If you move it, set the environment variable `HK_BIM_PATH` to the `bim` folder.
2. Click **Setup Parameters**. It binds the shared parameters (Areas, Project Information, Sheets) and creates the area schemes **HK GFA** and **HK SC**.
3. Fill Project Information: `HK_Site_Area` (m²), `HK_Building_Height` (m, reg 23(1)), `HK_Site_Class`, `HK_Building_Type`, and optionally `HK_OZP_Max_PR`, `HK_Lease_Max_GFA` and `HK_Dedicated_Area`. These are plain numbers in metric units.
4. Draw Areas in **HK GFA** on area plans of every floor. Measure boundaries to the outer face of external walls, and include balconies with their side walls. Put each exempt room in its own Area. For typical floors, either draw every level or draw one and set `HK_Floor_Count`.
5. Optionally draw the site coverage footprint of each level in **HK SC**.
6. Click **GFA Schedule**. It writes `<model>_area_schedule.csv` and `<model>_bpr.json` next to the model and shows the report. On the CPython engine this is the full `bpr_check.py` report; on IronPython it is the quick check plus the command to run the full one. Shift+click changes the area scheme names.
7. Click **BD Sheets**. Pick a title block, the levels and the sheet groups. It creates numbered sheets, sets `HK_Sheet_Scale` and places each level's unplaced floor plan or area plan. Existing numbers are skipped, so it is safe to run again.
8. Click **Envelope** to see the permitted PR, SC, max GFA and tower floors for the site.

Title block: add labels for the `HK_*` Project Information fields and `HK_Sheet_Scale` / `HK_Drawing_Status` to your title block family.

GFA colour plans: create an Area colour scheme on `HK_GFA_Category` using the colours in `hk_bim/sheets.py` (`GFA_COLOURS`). The tools do not create the colour scheme yet.

## Dynamo

Use a Python Script node set to **CPython3**, paste the file's code, and wire the inputs listed at the top of the file. `IN[0]` is always the path to this `bim` folder (use a Directory Path node). Dynamo caches imported modules, so restart Dynamo after editing `hk_bim`.

- `HK_GFA_Schedule.py`: same output as the pyRevit button, returned as lists for Watch / Data.Export nodes.
- `HK_BD_Sheets.py`: same as the BD Sheets button. Use a Boolean toggle to run it.
- `HK_Envelope.py`: does not need Revit.

## Grasshopper

Use a GhPython component (Rhino 7) or a Python 3 Script component (Rhino 8). Paste the file, add the inputs named in its docstring with the type hints shown, and add the outputs. `BimPath` can be left blank if the `.gh` file is saved inside this repo.

- `HK_Massing_GFA.py`: massing breps go in. It slices them per floor, using floor-to-floor heights in metres, and gives plates, areas, GFA, PR, SC per floor, the envelope, the quick report, and an optional bpr_check JSON export. Units are scaled from the Rhino document. Plant rooms are a percentage allowance (`PlantPct`) until real rooms are drawn.
- `HK_Area_Schedule.py`: closed plan curves tagged by layer or category go in, and an area schedule, the floors JSON and a CSV come out. Curves with no readable category come out in `Unmatched`.
- `HK_Envelope.py`: max GFA, footprint and floor count from site area, height and class.

## What was tested, and what still needs testing in Revit and Rhino

Tested here (CPython 3.13, 27 unit tests):
- Category table, First Schedule lookups and site class all match `tools/bpr_check.py`.
- Records rebuilt from `examples/demo_composite.json` give the same GFA and the same PASS/FAIL results as the original file in `bpr_check.py`.
- The quick check matches `bpr_check.py` for the composite formula and site coverage.
- Mixed-use levels, `not_gfa`, refusal of unclassified areas, the APP-151 cap, CSV output, the envelope (including OZP), massing records, drawing numbers and the sheet list.
- `revit_adapter.area_records` and `footprints` run against a fake Revit API: unit conversion ft²→m², elevation above G/F, parameters versus names, unplaced Areas.
- A syntax scan for things IronPython 2.7 cannot parse.

Not tested (no Revit or Rhino here). Try these on a copy of a model first:
- All pyRevit buttons, `forms.select_titleblocks`, and the pyRevit output window.
- `bind_shared_parameters`. The shared parameter file uses the newer column layout (with `HIDEWHENNOVALUE`); check that it loads in your Revit version.
- `AreaScheme.Create`. If it is missing from your API version, the button tells you to create the schemes by hand.
- `create_sheets`: viewport placement uses the A1 sheet centre (1.38, 0.97 ft). Adjust `sheet_centre_ft` for your title block.
- All Dynamo nodes and Grasshopper components, slicing at `GroundZ + 10 mm`, and courtyards and holes in plates.
- Real IronPython 2.7 execution. The syntax scan catches most problems but not all of them.

## Rules still to confirm

- The sheet list and minimum scales in `sheets.py` (1:1000 block plan, 1:500 site plan, 1:100 general building plans) are marked [verify]. Check them against Cap. 123A reg 8 and current BD e-submission requirements.
- The tools do not check lease GFA definitions. These can differ from B(P)R.
