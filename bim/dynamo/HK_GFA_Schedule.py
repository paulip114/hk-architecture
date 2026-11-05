# -*- coding: utf-8 -*-
# Dynamo Python Script node (engine: CPython3, Dynamo 2.13+ / Revit 2022+).
# HK GFA / PR / SC schedule from the "HK GFA" area scheme.
#
# IN[0]  bim folder of the hk-architecture repo (Directory Path node), e.g. C:\repos\hk-architecture\bim
# IN[1]  run (Boolean toggle)
# IN[2]  output folder for CSV / JSON (Directory Path); blank = model folder
# IN[3]  GFA area scheme name (string, default "HK GFA")
# IN[4]  site class override "A"/"B"/"C" (optional; else Project Information)
# IN[5]  building type override (optional)
# OUT    [schedule rows with header, floors, report markdown, [csv path, json path], warnings]
import os
import sys

bim = IN[0]
if bim and bim not in sys.path:
    sys.path.insert(0, bim)

import clr  # noqa: E402
clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager  # noqa: E402
clr.AddReference("RevitAPI")

from hk_bim import areas, bpr_limits, report, revit_adapter  # noqa: E402

doc = DocumentManager.Instance.CurrentDBDocument
run = IN[1]
out_dir = IN[2] or (os.path.dirname(doc.PathName) if doc.PathName else None)
scheme = IN[3] or revit_adapter.GFA_SCHEME
warnings = []

if not run:
    OUT = [None, None, "Set run to True.", None, warnings]
else:
    records, skipped = revit_adapter.area_records(doc, scheme)
    for sid, why in skipped:
        warnings.append("Area %s skipped: %s" % (sid, why))
    bad = areas.unclassified(records)
    for r in bad:
        warnings.append("No GFA category: %s @ %s (id %s)" % (r["name"], r["level"], r.get("source_id")))
    inp = revit_adapter.project_inputs(doc)
    site_class = IN[4] or inp.get("site_class") or "A"
    btype = IN[5] or inp.get("building_type") or "composite"
    rows = [areas.SCHEDULE_HEADER] + areas.schedule_rows(records)
    if bad or not inp.get("site_area_m2") or not inp.get("height_m"):
        if not inp.get("site_area_m2") or not inp.get("height_m"):
            warnings.append("Fill HK_Site_Area and HK_Building_Height in Project Information.")
        OUT = [rows, None, "Fix the warnings, then run again.", None, warnings]
    else:
        floors = areas.build_floors(records, footprints=revit_adapter.footprints(doc))
        limits = {}
        if inp.get("ozp_max_pr_total"):
            limits["ozp_max_pr_total"] = inp["ozp_max_pr_total"]
        if inp.get("lease_max_gfa_m2"):
            limits["lease_max_gfa_m2"] = inp["lease_max_gfa_m2"]
        site = {"area_m2": inp["site_area_m2"]}
        if site_class in ("A", "B", "C"):
            site["class"] = site_class
        if inp.get("dedicated_area_m2"):
            site["dedicated_area_m2"] = inp["dedicated_area_m2"]
        proj = areas.project_json(doc.Title, site, {"type": btype, "height_m": inp["height_m"]}, floors, limits)
        paths = None
        if out_dir:
            stem = os.path.join(out_dir, os.path.splitext(doc.Title)[0])
            paths = [areas.write_csv(stem + "_area_schedule.csv", rows[1:], areas.SCHEDULE_HEADER),
                     areas.write_json(stem + "_bpr.json", proj)]
        md, _fails = report.run_bpr_check(proj)
        if md is None:
            md = report.quick_md(bpr_limits.quick_check(floors, inp["site_area_m2"], inp["height_m"],
                                                        site_class, btype, limits=limits))
        OUT = [rows, floors, md, paths, warnings]
