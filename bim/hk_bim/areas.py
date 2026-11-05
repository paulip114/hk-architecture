# -*- coding: utf-8 -*-
"""Area records -> HK GFA / site coverage / plot ratio figures.

Workflow used by every host (Revit, Dynamo, Grasshopper):

1. The host script turns each area boundary (a Revit Area, a Rhino closed
   curve, a sliced massing floor plate) into a *record* dict:
       {"name": "Lift machine room", "level": "R/F", "elevation_m": 98.0,
        "use": "domestic" | "non_domestic", "category": "mandatory_plant",
        "area_m2": 12.5, "count": 1}
2. ``build_floors`` groups records per level into the ``floors[]`` block that
   ``tools/bpr_check.py`` reads, so the full checker runs on BIM output.
3. ``quick_check`` gives live PR / SC / GFA figures for massing studies on
   engines that cannot import bpr_check.py (IronPython 2.7).

Categories match ``EXEMPT_FRACTION`` in tools/bpr_check.py (a unit test keeps
the two in step), plus ``accountable`` (counted in GFA) and ``not_gfa``
(voids, open roofs and anything that is not floor space at all).

Every figure is a draft for review by an Authorized Person.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import io
import json
import os

FT2_TO_M2 = 0.09290304
FT_TO_M = 0.3048

# Same table as tools/bpr_check.py EXEMPT_FRACTION (PNAP APP-2 / APP-151).
EXEMPT_FRACTION = {
    "mandatory_plant": 1.0,
    "non_mandatory_plant": 1.0,
    "green_feature": 1.0,
    "car_park_underground": 1.0,
    "car_park_above_100": 1.0,
    "car_park_above_50": 0.5,
    "refuge_floor": 1.0,
    "bicycle_parking": 1.0,
    "other_disregarded": 1.0,
}
CAPPED = ("non_mandatory_plant", "green_feature")  # APP-151 10% cap
APP151_CAP = 0.10
ACCOUNTABLE = "accountable"
NOT_GFA = "not_gfa"
CATEGORIES = (ACCOUNTABLE, NOT_GFA) + tuple(sorted(EXEMPT_FRACTION))

# Labels people actually type into a Revit parameter or a Rhino layer name.
# Keys are compared lower-case with spaces, hyphens and slashes removed.
_ALIASES = {
    ACCOUNTABLE: ["accountable", "gfa", "counted", "計入", "計算樓面面積", "樓面面積"],
    NOT_GFA: ["notgfa", "void", "opentosky", "uncoveredroof", "非樓面", "中空", "天井", "露天"],
    "mandatory_plant": ["mandatoryplant", "mandatory", "mpr", "強制機房", "必要機房",
                        "liftmachineroom", "transformerroom", "switchroom", "pumproom",
                        "metreroom", "meterroom", "fscontrolroom", "watertank", "telecom",
                        "refusestorage", "refusechamber", "rsmrc", "垃圾房", "升降機機房",
                        "變壓器房", "電掣房", "水泵房", "錶房"],
    "non_mandatory_plant": ["nonmandatoryplant", "nonmandatory", "acplant", "ahu",
                            "acplantroom", "非強制機房", "空調機房"],
    "green_feature": ["greenfeature", "amenityfeature", "green", "綠化設施", "環保設施",
                      "康樂設施", "sunshade", "balcony", "utilityplatform", "露台", "工作平台"],
    "car_park_underground": ["carparkunderground", "basementcarpark", "地庫停車場", "地下停車場"],
    "car_park_above_100": ["carparkabove100", "carparkabove", "地面停車場", "上蓋停車場"],
    "car_park_above_50": ["carparkabove50", "停車場50"],
    "refuge_floor": ["refugefloor", "refuge", "庇護層"],
    "bicycle_parking": ["bicycleparking", "bicycle", "單車停泊", "單車位"],
    "other_disregarded": ["otherdisregarded", "other", "exempt", "disregarded", "豁免", "其他豁免"],
}
_ALIAS_INDEX = {}
for _cat, _words in _ALIASES.items():
    for _w in _words:
        _ALIAS_INDEX[_w] = _cat
    _ALIAS_INDEX[_cat.replace("_", "")] = _cat

_USE_ALIASES = {
    "domestic": "domestic", "dom": "domestic", "d": "domestic", "住宅": "domestic",
    "residential": "domestic", "resi": "domestic",
    "nondomestic": "non_domestic", "non_domestic": "non_domestic", "nd": "non_domestic",
    "n": "non_domestic", "非住宅": "non_domestic", "commercial": "non_domestic",
    "retail": "non_domestic", "office": "non_domestic", "商業": "non_domestic",
}


def _key(text):
    t = ("%s" % (text or "")).strip().lower()
    for ch in " -_/\\().,:;":
        t = t.replace(ch, "")
    return t


def normalise_category(text, default=None):
    """Map a free-text label (English or Chinese) to a category code.

    Exact alias match first, then "label contains alias" (longest alias wins),
    so "B1 private car park (basement)" still resolves. Returns ``default``
    when nothing matches; callers should report those rather than guess.
    """
    k = _key(text)
    if not k:
        return default
    if k in _ALIAS_INDEX:
        return _ALIAS_INDEX[k]
    best = None
    for alias, cat in _ALIAS_INDEX.items():
        if len(alias) >= 3 and alias in k and (best is None or len(alias) > len(best[0])):
            best = (alias, cat)
    return best[1] if best else default


def normalise_use(text, default="non_domestic"):
    k = _key(text)
    return _USE_ALIASES.get(k, default) if k else default


def make_record(name, level, area_m2, category=None, use=None, elevation_m=None,
                count=1, category_hint=None, source_id=None):
    """Build a validated record. ``category`` wins over ``category_hint``
    (usually the area's name); unmatched records get category None."""
    cat = normalise_category(category) if category else None
    if cat is None and category_hint:
        cat = normalise_category(category_hint)
    rec = {
        "name": "%s" % (name or ""),
        "level": "%s" % (level or ""),
        "elevation_m": None if elevation_m is None else float(elevation_m),
        "use": normalise_use(use),
        "category": cat,
        "area_m2": float(area_m2),
        "count": int(count or 1),
    }
    if source_id is not None:
        rec["source_id"] = "%s" % source_id
    return rec


def unclassified(records):
    """Records whose category could not be resolved (must be fixed in the model)."""
    return [r for r in records if r.get("category") not in CATEGORIES]


def _level_sort_key(item):
    elev = item[1]["elevation_m"]
    return (elev is None, elev if elev is not None else 0.0, item[0])


def build_floors(records, footprints=None, strict=True):
    """Group records into bpr_check ``floors[]`` entries.

    records     list of record dicts (see module docstring)
    footprints  optional {level name: site-coverage area m2} (outer face of
                external walls at that level, reg 20 / APP-2)
    strict      raise ValueError on unclassified records (default) instead of
                silently counting them

    A level holding both domestic and non-domestic floor space becomes two
    entries ("5/F (domestic)", "5/F (non-domestic)"); its footprint goes to
    the domestic entry, which carries the stricter First Schedule limit.
    """
    bad = unclassified(records)
    if bad and strict:
        names = ", ".join("%s @ %s" % (r["name"], r["level"]) for r in bad[:10])
        raise ValueError("%d area(s) have no GFA category: %s" % (len(bad), names))
    footprints = footprints or {}

    levels = {}
    for r in records:
        if r.get("category") not in CATEGORIES or r["category"] == NOT_GFA:
            continue
        lv = levels.setdefault(r["level"], {"elevation_m": r.get("elevation_m"),
                                            "count": r.get("count", 1), "uses": {}})
        if lv["elevation_m"] is None and r.get("elevation_m") is not None:
            lv["elevation_m"] = r["elevation_m"]
        lv["count"] = max(lv["count"], r.get("count", 1))
        u = lv["uses"].setdefault(r["use"], {"gross": 0.0, "exempt": []})
        u["gross"] += r["area_m2"]
        if r["category"] != ACCOUNTABLE:
            u["exempt"].append({"item": r["name"] or r["category"],
                                "area_m2": round(r["area_m2"], 3),
                                "category": r["category"]})

    floors = []
    for name, lv in sorted(levels.items(), key=_level_sort_key):
        uses = sorted(lv["uses"].keys())  # "domestic" sorts before "non_domestic"
        for use in uses:
            u = lv["uses"][use]
            label = name if len(uses) == 1 else "%s (%s)" % (name, use.replace("_", "-"))
            f = {"name": label, "use": use,
                 "level_m": round(lv["elevation_m"], 3) if lv["elevation_m"] is not None else 0.0,
                 "gross_area_m2": round(u["gross"], 3), "exempt": u["exempt"]}
            if lv["count"] > 1:
                f["count"] = lv["count"]
            if name in footprints and use == uses[0]:
                f["site_coverage_m2"] = round(float(footprints[name]), 3)
            floors.append(f)
    return floors


def accountable_of(floor):
    disregarded = sum(e["area_m2"] * EXEMPT_FRACTION[e["category"]] for e in floor.get("exempt", []))
    return floor["gross_area_m2"] - disregarded


def gfa_totals(floors):
    """Return dict with domestic / non_domestic / total accountable GFA,
    gross built area, and the APP-151 capped total."""
    out = {"domestic": 0.0, "non_domestic": 0.0, "gross": 0.0, "capped": 0.0, "disregarded": 0.0}
    for f in floors:
        n = int(f.get("count", 1))
        acc = accountable_of(f) * n
        out[f["use"]] += acc
        out["gross"] += f["gross_area_m2"] * n
        out["disregarded"] += f["gross_area_m2"] * n - acc
        for e in f.get("exempt", []):
            if e["category"] in CAPPED:
                out["capped"] += e["area_m2"] * EXEMPT_FRACTION[e["category"]] * n
    out["total"] = out["domestic"] + out["non_domestic"]
    return out


def project_json(project_name, site, building, floors, limits=None, extra=None):
    """Assemble the input file for ``python3 tools/bpr_check.py``."""
    p = {"project": project_name, "site": dict(site), "building": dict(building), "floors": floors}
    if limits:
        p["limits"] = dict(limits)
    if extra:
        p.update(extra)
    p["_generated_by"] = "bim/hk_bim (draft for AP review)"
    return p


def write_json(path, data):
    text = json.dumps(data, ensure_ascii=False, indent=1)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write("%s" % text)
    return path


# ---------------------------------------------------------------- area schedule

SCHEDULE_HEADER = ["Level", "Elevation (m)", "Area name", "Use", "Category",
                   "Area (m2)", "No. of floors", "Total (m2)", "Disregarded (m2)", "Accountable GFA (m2)"]


def schedule_rows(records):
    """Flat area schedule, one row per record plus a subtotal row per level
    and grand totals. Numbers are floats; format them in the host."""
    rows = []
    by_level = {}
    for r in records:
        by_level.setdefault(r["level"], {"elevation_m": r.get("elevation_m"), "items": []})["items"].append(r)
    grand = [0.0, 0.0, 0.0]
    for lvl, data in sorted(by_level.items(), key=_level_sort_key):
        sub = [0.0, 0.0, 0.0]
        for r in sorted(data["items"], key=lambda x: (x["category"] or "", x["name"])):
            cat = r.get("category")
            n = r.get("count", 1)
            total = r["area_m2"] * n
            if cat == NOT_GFA or cat not in CATEGORIES:
                dis, acc = 0.0, 0.0
            elif cat == ACCOUNTABLE:
                dis, acc = 0.0, total
            else:
                dis = total * EXEMPT_FRACTION[cat]
                acc = total - dis
            if cat != NOT_GFA:
                sub[0] += total
                sub[1] += dis
                sub[2] += acc
            rows.append([lvl, data["elevation_m"], r["name"], r["use"], cat or "UNCLASSIFIED",
                         r["area_m2"], n, total, dis, acc])
        rows.append([lvl, data["elevation_m"], "Subtotal", "", "", None, None, sub[0], sub[1], sub[2]])
        for i in range(3):
            grand[i] += sub[i]
    rows.append(["TOTAL", None, "", "", "", None, None, grand[0], grand[1], grand[2]])
    return rows


def _csv_cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        s = "%.2f" % v
    else:
        s = "%s" % v
    if any(c in s for c in ',"\n'):
        s = '"%s"' % s.replace('"', '""')
    return s


def write_csv(path, rows, header=None):
    """UTF-8 with BOM so Excel shows Chinese names correctly."""
    lines = []
    if header:
        lines.append(",".join(_csv_cell(h) for h in header))
    for row in rows:
        lines.append(",".join(_csv_cell(c) for c in row))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write("\r\n".join(lines) + "\r\n")
    return path
