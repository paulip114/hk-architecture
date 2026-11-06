# -*- coding: utf-8 -*-
"""Development envelope: permitted PR / SC, max GFA, tower footprint and floor
count for the site in Project Information (or values you type in)."""
from __future__ import print_function

__title__ = "Envelope"
__author__ = "hk-architecture"

import hk_bootstrap
hk_bootstrap.ensure_path()

from pyrevit import forms, revit, script  # noqa: E402

from hk_bim import bpr_limits, revit_adapter  # noqa: E402

out = script.get_output()
inp = revit_adapter.project_inputs(revit.doc)


def ask(key, prompt, default):
    v = inp.get(key)
    if v:
        return v
    s = forms.ask_for_string(default=str(default), prompt=prompt, title="HK envelope")
    if s is None:
        script.exit()
    return s


site_area = float(ask("site_area_m2", "Site area (m2, reg 23(2))", 1000))
height = float(ask("height_m", "Building height (m, reg 23(1))", 100))
cls = ask("site_class", "Site class A / B / C", "A").upper()
btype = ask("building_type", "domestic / non_domestic / composite", "domestic")
f2f = float(forms.ask_for_string(default="3.15", prompt="Typical floor-to-floor (m)", title="HK envelope") or 3.15)
podium = int(forms.ask_for_string(default="0", prompt="Podium floors (non-domestic, <= 15 m)",
                                  title="HK envelope") or 0)
nd_pr = 0.0
if btype == "composite":
    nd_pr = float(forms.ask_for_string(default="1.0", prompt="Intended non-domestic PR",
                                       title="HK envelope") or 0)
env = bpr_limits.envelope(site_area, height, cls, btype, floor_to_floor_m=f2f, podium_floors=podium,
                          non_domestic_pr=nd_pr, ozp_max_pr=inp.get("ozp_max_pr_total"),
                          lease_max_gfa_m2=inp.get("lease_max_gfa_m2"))
out.print_md("# Development envelope (draft)")
out.print_table(sorted([[k, v] for k, v in env.items()]), columns=["Item", "Value"])
