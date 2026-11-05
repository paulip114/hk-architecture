# -*- coding: utf-8 -*-
"""GhPython component (Rhino 7 IronPython, or Rhino 8 Python 3 Script component).
Slices massing into HK floor plates and reports GFA, plot ratio and site
coverage against B(P)R. Live draft check for massing studies, not a submission.

Inputs (set the type hints in the component):
  BimPath        str    the repo's bim folder (blank: searched from the .gh file location)
  Massing        Brep   list, closed massing solids, Z up, model units any
  SiteArea       float  site area m2 (reg 23(2)); blank -> area of Site curve
  Site           Curve  closed site boundary (optional)
  GroundZ        float  G/F level in model units (default: lowest point of massing)
  FloorHeights   float  list of floor-to-floor heights in METRES; last value repeats
  Basements      int    number of floors below GroundZ that are basements
  Podium         int    floors above ground counted non-domestic (composite)
  BuildingType   str    domestic / non_domestic / composite
  SiteClass      str    A / B / C (or give StreetWidths + perimeter via SiteClass blank)
  StreetWidths   float  list, widths of streets the site abuts (used if SiteClass blank)
  Frontage       float  length of site boundary on specified streets, m
  HeightOverride float  building height m (reg 23(1)); blank -> top of massing - GroundZ
  PlantPct       float  share of each plate assumed mandatory plant (e.g. 0.03)
  OzpPR          float  OZP max total PR (optional)
  ExportPath     str    optional .json path to save bpr_check input
Outputs:
  Plates     floor plate curves (tree-free list in floor order)
  Levels     floor names     Areas  plate areas m2
  GFA        accountable GFA m2    PR  total plot ratio
  SC         site coverage % of each floor
  Envelope   permitted figures for this site (text)
  Report     quick check (markdown text)
  Ok         True when no FAIL rows
"""
import os
import sys


def _find_bim(given):
    cands = [given, os.environ.get("HK_BIM_PATH")]
    try:
        gh_path = ghenv.Component.OnPingDocument().FilePath  # noqa: F821
        d = os.path.dirname(gh_path)
        for _ in range(5):
            cands.append(os.path.join(d, "bim"))
            cands.append(d)
            d = os.path.dirname(d)
    except Exception:
        pass
    for c in cands:
        if c and os.path.isdir(os.path.join(c, "hk_bim")):
            return c
    raise ValueError("Set BimPath to the hk-architecture/bim folder")


_bim = _find_bim(globals().get("BimPath"))
if _bim not in sys.path:
    sys.path.insert(0, _bim)

from hk_bim import areas, bpr_limits, massing, report, rhino_adapter  # noqa: E402

breps = [b for b in (globals().get("Massing") or []) if b is not None]
if not breps:
    raise ValueError("Connect Massing breps")

to_m = rhino_adapter.unit_scale_to_m()
zmin, zmax = rhino_adapter.bbox_z(breps)
ground_z = globals().get("GroundZ")
ground_z = zmin if ground_z is None else ground_z
heights_m = list(globals().get("FloorHeights") or [3.15])
basements = int(globals().get("Basements") or 0)
heights_model = [h / to_m for h in heights_m]

# Basements sit below ground: start that many floors down using the first height.
base_z = ground_z - basements * heights_model[0]
levels = massing.floor_levels(base_z, heights_model, zmax)
# Slice a little above each slab so the plate is cut cleanly.
eps = 0.01 / to_m
sliced = rhino_adapter.slice_breps(breps, [z + eps for _i, z in levels])
plates = [(i, z, s[2] * to_m * to_m) for (i, z), s in zip(levels, sliced)]

site_area = globals().get("SiteArea")
site_crv = globals().get("Site")
if not site_area and site_crv is not None:
    site_area = rhino_adapter.planar_area([site_crv])[0] * to_m * to_m
if not site_area:
    raise ValueError("Give SiteArea or a closed Site curve")

btype = globals().get("BuildingType") or "composite"
cls = globals().get("SiteClass")
if not cls:
    perim = site_crv.GetLength() * to_m if site_crv is not None else None
    cls = bpr_limits.classify_site(list(globals().get("StreetWidths") or []), perim, globals().get("Frontage"))
height = globals().get("HeightOverride") or (zmax - ground_z) * to_m

# Plates in metres, z measured from G/F, so level_m feeds reg 20(3) directly.
plates_m = [(i, (z - ground_z) * to_m, a) for i, z, a in plates]
recs, fps = massing.massing_records(plates_m, podium_floors=int(globals().get("Podium") or 0),
                                    building_type=btype,
                                    mandatory_plant_pct=globals().get("PlantPct") or 0.0,
                                    basement_count=basements, ground_z=0.0)
floors = areas.build_floors(recs, footprints=fps)

limits = {}
if globals().get("OzpPR"):
    limits["ozp_max_pr_total"] = OzpPR  # noqa: F821
res = bpr_limits.quick_check(floors, site_area, height, cls, btype, limits=limits)

Plates = [c for s in sliced for c in s[1]]
Levels = [massing.hk_floor_name(i, basements) for i, _z, _a in plates]
Areas = [round(a, 2) for _i, _z, a in plates]
GFA = round(res["totals"]["total"], 2)
PR = round(res["totals"]["pr_total"], 3)
SC = [round(a / site_area * 100, 1) for _i, _z, a in plates]
env = bpr_limits.envelope(site_area, height, cls, btype, floor_to_floor_m=heights_m[-1],
                          podium_floors=int(globals().get("Podium") or 0),
                          non_domestic_pr=res["totals"]["pr_non_domestic"], ozp_max_pr=limits.get("ozp_max_pr_total"))
Envelope = "\n".join("%s: %s" % (k, env[k]) for k in sorted(env))
Report = report.quick_md(res, "Massing check, class %s, height %.1f m" % (cls, height))
Ok = not any(r[4] == "FAIL" for r in res["rows"])

if globals().get("ExportPath"):
    site = {"area_m2": site_area}
    if cls in ("A", "B", "C"):
        site["class"] = cls
    areas.write_json(ExportPath, areas.project_json("Grasshopper massing", site,  # noqa: F821
                                                    {"type": btype, "height_m": height}, floors, limits))
