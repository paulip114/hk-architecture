# -*- coding: utf-8 -*-
"""GFA / plot ratio / site coverage schedule from the "HK GFA" area scheme.

Reads every placed Area in the HK GFA scheme (and footprints from HK SC),
classifies each into a B(P)R / PNAP APP-2 category, and writes:
  <model folder>/<model>_area_schedule.csv   area schedule for the GFA table
  <model folder>/<model>_bpr.json           input for tools/bpr_check.py
On the CPython engine it also runs bpr_check.py and shows the full report;
on IronPython it shows the quick PR / SC check.
Draft for Authorized Person review.
"""
from __future__ import print_function

__title__ = "GFA\nSchedule"
__author__ = "hk-architecture"

import os

import hk_bootstrap
hk_bootstrap.ensure_path()

from pyrevit import forms, revit, script  # noqa: E402

from hk_bim import areas, bpr_limits, report, revit_adapter  # noqa: E402

doc = revit.doc
out = script.get_output()
cfg = script.get_config()

gfa_scheme = cfg.get_option("gfa_scheme", revit_adapter.GFA_SCHEME)
sc_scheme = cfg.get_option("sc_scheme", revit_adapter.SC_SCHEME)

records, skipped = revit_adapter.area_records(doc, gfa_scheme)
if not records:
    forms.alert('No placed Areas found in area scheme "%s".\n'
                'Create the scheme, draw Areas on each floor, or change the scheme name '
                '(Shift+click this button).' % gfa_scheme, exitscript=True)

bad = areas.unclassified(records)
if bad:
    out.print_md("## Areas without a GFA category")
    out.print_md("Fill **HK_GFA_Category** on these Areas (or rename them) and run again. "
                 "Allowed: `%s`" % "`, `".join(areas.CATEGORIES))
    out.print_table([[r.get("source_id"), r["level"], r["name"],
                      "%.2f" % r["area_m2"]] for r in bad],
                    columns=["Element id", "Level", "Name", "Area m2"])
    script.exit()

inputs = revit_adapter.project_inputs(doc)
missing = [k for k in ("site_area_m2", "height_m") if not inputs.get(k)]
for k in missing:
    val = forms.ask_for_string(prompt="Project Information has no %s. Enter it:" % k, title="HK GFA")
    if not val:
        script.exit()
    inputs[k] = float(val)
site_class = inputs.get("site_class") or forms.ask_for_one_item(
    ["A", "B", "C", "BA"], default="A", prompt="Site class (reg 18A)", title="HK GFA") or "A"
btype = inputs.get("building_type") or forms.ask_for_one_item(
    ["domestic", "non_domestic", "composite"], default="composite",
    prompt="Building type", title="HK GFA") or "composite"

fps = revit_adapter.footprints(doc, sc_scheme)
floors = areas.build_floors(records, footprints=fps)
limits = {}
if inputs.get("ozp_max_pr_total"):
    limits["ozp_max_pr_total"] = inputs["ozp_max_pr_total"]
if inputs.get("lease_max_gfa_m2"):
    limits["lease_max_gfa_m2"] = inputs["lease_max_gfa_m2"]

site = {"area_m2": inputs["site_area_m2"]}
if site_class in ("A", "B", "C"):
    site["class"] = site_class
if inputs.get("dedicated_area_m2"):
    site["dedicated_area_m2"] = inputs["dedicated_area_m2"]
proj = areas.project_json(doc.Title, site, {"type": btype, "height_m": inputs["height_m"]}, floors, limits)

folder = os.path.dirname(doc.PathName) if doc.PathName else forms.pick_folder(title="Save schedule to")
if not folder:
    script.exit()
stem = os.path.join(folder, os.path.splitext(doc.Title)[0])
areas.write_csv(stem + "_area_schedule.csv", areas.schedule_rows(records), areas.SCHEDULE_HEADER)
areas.write_json(stem + "_bpr.json", proj)

out.print_md("# HK GFA schedule: %s" % doc.Title)
out.print_md("Saved `%s_area_schedule.csv` and `%s_bpr.json`." % (stem, stem))
if skipped:
    out.print_md("Skipped %d Area(s) that are unplaced or not enclosed." % len(skipped))

md, fails = report.run_bpr_check(proj)
if md is None:
    res = bpr_limits.quick_check(floors, inputs["site_area_m2"], inputs["height_m"], site_class, btype,
                                 dedicated_area_m2=inputs.get("dedicated_area_m2") or 0.0, limits=limits)
    out.print_md(report.quick_md(res))
    out.print_md("Full check (IronPython cannot run it): `python3 tools/bpr_check.py \"%s_bpr.json\"`" % stem)
else:
    out.print_md(md)

rows = [[f["name"], f["use"], "%.2f" % f["gross_area_m2"], f.get("count", 1),
         "%.2f" % areas.accountable_of(f)] for f in floors]
out.print_table(rows, columns=["Floor", "Use", "Gross m2", "x floors", "Accountable m2 (each)"],
                title="Floors")
if skipped:
    out.print_table([[i, why] for i, why in skipped], columns=["Element id", "Reason"], title="Skipped Areas")
