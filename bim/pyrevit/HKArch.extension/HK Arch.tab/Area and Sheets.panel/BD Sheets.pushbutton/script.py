# -*- coding: utf-8 -*-
"""Create the BD general building plans sheet set.

Pick a title block, the levels that need per-floor sheets and the sheet
groups; the tool creates numbered sheets (GBP-020-05F etc.), writes
HK_Sheet_Scale, and places an unplaced floor plan / area plan of that level
where one exists. Existing sheet numbers are left alone, so it is safe to
run again after adding levels. Sheet list and scales: bim/hk_bim/sheets.py
(items marked [verify] there are office practice, not statute).
"""
from __future__ import print_function

__title__ = "BD\nSheets"
__author__ = "hk-architecture"

import hk_bootstrap
hk_bootstrap.ensure_path()

from pyrevit import DB, forms, revit, script  # noqa: E402

from hk_bim import revit_adapter, sheets  # noqa: E402

doc = revit.doc
out = script.get_output()

tb_id = forms.select_titleblocks(doc=doc, title="Title block for BD sheets")
if not tb_id:
    script.exit()

levels = sorted(DB.FilteredElementCollector(doc).OfClass(DB.Level), key=lambda l: l.ProjectElevation)
picked = forms.SelectFromList.show([l.Name for l in levels], title="Levels needing per-floor sheets",
                                   multiselect=True, button_name="Use these levels")
if not picked:
    script.exit()

groups = ["%s  %s / %s" % (code, name, zh) for code, name, zh, _s, _k, _p in sheets.BD_GBP_TEMPLATE]
chosen = forms.SelectFromList.show(groups, title="Sheet groups", multiselect=True, button_name="Create sheets")
if not chosen:
    script.exit()
codes = set(c.split()[0] for c in chosen)

scale = forms.ask_for_one_item(["100", "200"], default="100", prompt="General building plan scale 1:",
                               title="BD Sheets")
plan_scale = int(scale or 100)
prefix = forms.ask_for_string(default="GBP", prompt="Drawing number prefix", title="BD Sheets") or "GBP"

order = [l.Name for l in levels if l.Name in picked]
todo = sheets.sheet_list(order, prefix=prefix, plan_scale=plan_scale, include=codes)

with revit.Transaction("HK: create BD sheets"):
    created, skipped = revit_adapter.create_sheets(doc, todo, tb_id, place_views=True, view_scale=plan_scale)

out.print_md("# BD sheet set")
out.print_md("Created **%d** sheet(s); %d number(s) already existed and were left alone." % (len(created), len(skipped)))
out.print_table([[s["number"], s["name"], s["name_zh"], s["scale"]] for s in todo if s["number"] in created],
                columns=["No.", "Title", "標題", "Scale"])
out.print_md("Fill the title block fields in Project Information: %s. "
             "Every sheet is a draft until signed by the Authorized Person."
             % ", ".join(n for n, _ in sheets.TITLEBLOCK_FIELDS))
