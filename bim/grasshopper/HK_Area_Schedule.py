# -*- coding: utf-8 -*-
"""GhPython component: area schedule from tagged closed curves (Rhino plans).

Draw each space as a closed curve and give it a category, either through the
Category input (one per curve) or by putting the curves on layers named
after the category (e.g. "GFA::mandatory_plant", "GFA::地庫停車場").

Inputs:
  BimPath     str    the repo's bim folder (blank: searched from the .gh file)
  Curves      Curve  list of closed planar curves (one per space)
  Names       str    list, space names (optional)
  Category    str    list, category per curve (optional if Layers given)
  Layers      str    list, layer full path per curve (e.g. from a Human / Elefront object attributes node)
  Level       str    list or single, floor name per curve (e.g. "5/F")
  Elevation   float  list or single, level above ground, m
  Use         str    list or single, domestic / non_domestic
  Count       int    list or single, number of identical floors (typical floors)
  Footprint   Curve  list of site-coverage outlines (optional), one per Level in FootprintLevel
  FootprintLevel str list, floor name per Footprint curve
  CsvPath     str    optional .csv path to save the schedule
Outputs:
  Table       list of text rows (Level | Name | Category | Area | Accountable)
  Floors      floors JSON text for tools/bpr_check.py
  Unmatched   curves whose category could not be read (fix these first)
  TotalGFA    accountable GFA m2
"""
import json
import os
import sys


def _find_bim(given):
    cands = [given, os.environ.get("HK_BIM_PATH")]
    try:
        d = os.path.dirname(ghenv.Component.OnPingDocument().FilePath)  # noqa: F821
        for _ in range(5):
            cands += [os.path.join(d, "bim"), d]
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

from hk_bim import areas, rhino_adapter  # noqa: E402


def _pick(values, i, default=None):
    if values is None:
        return default
    if not isinstance(values, (list, tuple)):
        return values
    if not values:
        return default
    return values[i] if i < len(values) else values[-1]


to_m2 = rhino_adapter.unit_scale_to_m() ** 2
crvs = [c for c in (globals().get("Curves") or []) if c is not None]
recs, Unmatched = [], []
for i, c in enumerate(crvs):
    layer = _pick(globals().get("Layers"), i, "") or ""
    cat_text = _pick(globals().get("Category"), i) or layer.split("::")[-1]
    a = rhino_adapter.planar_area([c])[0] * to_m2
    r = areas.make_record(_pick(globals().get("Names"), i, "Space %d" % (i + 1)), _pick(globals().get("Level"), i, "G/F"),
                          a, category=cat_text, use=_pick(globals().get("Use"), i, "non_domestic"),
                          elevation_m=_pick(globals().get("Elevation"), i, 0.0), count=_pick(globals().get("Count"), i, 1))
    if r["category"] is None:
        Unmatched.append(c)
    recs.append(r)

fps = {}
for i, c in enumerate(globals().get("Footprint") or []):
    lv = _pick(globals().get("FootprintLevel"), i, "G/F")
    fps[lv] = fps.get(lv, 0.0) + rhino_adapter.planar_area([c])[0] * to_m2

rows = areas.schedule_rows(recs)
Table = ["%s | %s | %s | %.2f | %.2f" % (r[0], r[2], r[4], r[7] or 0.0, r[9] or 0.0) for r in rows]
floors = areas.build_floors(recs, footprints=fps, strict=False)
Floors = json.dumps(floors, ensure_ascii=False, indent=1)
TotalGFA = round(areas.gfa_totals(floors)["total"], 2)
if globals().get("CsvPath"):
    areas.write_csv(CsvPath, rows, areas.SCHEDULE_HEADER)  # noqa: F821
