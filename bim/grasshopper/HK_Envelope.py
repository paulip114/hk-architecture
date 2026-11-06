# -*- coding: utf-8 -*-
"""GhPython component: development envelope for a site (no geometry needed).

Inputs: BimPath (str), SiteArea (float m2), Height (float m), SiteClass (str),
        BuildingType (str), FloorToFloor (float m), Podium (int),
        NonDomesticPR (float, composite), OzpPR (float), LeaseGFA (float)
Outputs: MaxGFA, PlotRatio, SiteCoverage (%), Footprint (m2), TowerFloors, Governing, Text
"""
import os
import sys

_bim = globals().get("BimPath") or os.environ.get("HK_BIM_PATH")
if not _bim or not os.path.isdir(os.path.join(_bim, "hk_bim")):
    raise ValueError("Set BimPath to the hk-architecture/bim folder")
if _bim not in sys.path:
    sys.path.insert(0, _bim)
from hk_bim import bpr_limits  # noqa: E402

env = bpr_limits.envelope(SiteArea, Height, SiteClass or "A", BuildingType or "domestic",  # noqa: F821
                          floor_to_floor_m=globals().get("FloorToFloor") or 3.15,
                          podium_floors=int(globals().get("Podium") or 0),
                          non_domestic_pr=globals().get("NonDomesticPR") or 0.0,
                          ozp_max_pr=globals().get("OzpPR"), lease_max_gfa_m2=globals().get("LeaseGFA"))
MaxGFA = env["max_gfa_m2"]
PlotRatio = env["plot_ratio"]
SiteCoverage = env["site_coverage_pct"]
Footprint = env["max_tower_footprint_m2"]
TowerFloors = env["tower_floors_at_max_footprint"]
Governing = env["governing_limit"]
Text = "\n".join("%s: %s" % (k, env[k]) for k in sorted(env))
