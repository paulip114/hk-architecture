# -*- coding: utf-8 -*-
"""First Schedule limits and a quick GFA / PR / SC check for live feedback.

Reads ``bpr/first_schedule.json`` from this repo (verified against the
official consolidated Cap. 123F, 17-09-2026). Set the environment variable
HK_BPR_SCHEDULE, or pass ``path`` to ``load_schedule``, if the scripts are
copied somewhere without the rest of the knowledge base.

``quick_check`` covers reg 20 (site coverage), reg 21 (plot ratio, incl. the
composite formula) and the APP-151 10% cap. It mirrors tools/bpr_check.py
(tested against it) but is not the full check: for a submission draft
export the project JSON and run bpr_check.py.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import io
import json
import math
import os

from .areas import APP151_CAP, gfa_totals

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEDULE = os.path.normpath(os.path.join(_HERE, "..", "..", "bpr", "first_schedule.json"))
_CACHE = {}


def load_schedule(path=None):
    path = path or os.environ.get("HK_BPR_SCHEDULE") or DEFAULT_SCHEDULE
    if path not in _CACHE:
        with io.open(path, "r", encoding="utf-8") as fh:
            _CACHE[path] = json.load(fh)
    return _CACHE[path]


def band_index(height, schedule=None):
    s = schedule or load_schedule()
    bands = s["height_bands_m"]
    for i, band in enumerate(bands):
        hi = band[1]
        if hi is None or height <= hi:
            return i
    return len(bands) - 1


def band_label(i, schedule=None):
    lo, hi = (schedule or load_schedule())["height_bands_m"][i]
    if hi is None:
        return "> %s m" % lo
    return ("<= %s m" % hi) if lo == 0 else ("> %s m, <= %s m" % (lo, hi))


def limit(use, kind, site_class, height, schedule=None):
    """kind: 'site_coverage_pct' or 'plot_ratio'; site_class 'A' / 'B' / 'C'."""
    s = schedule or load_schedule()
    table = s["domestic" if use == "domestic" else "non_domestic"]
    return table[kind][site_class][band_index(height, s)]


def classify_site(street_widths_m, perimeter_m=None, frontage_m=None):
    """Reg 18A site class from street data (same test as bpr_check.py).
    Returns 'A', 'B', 'C' or 'BA' (no street >= 4.5 m: reg 19(3))."""
    widths = [w for w in (street_widths_m or []) if w >= 4.5]
    if not widths:
        return "BA"
    ratio = (frontage_m / perimeter_m) if (perimeter_m and frontage_m) else 0.0
    if len(widths) >= 3 and ratio >= 0.60:
        return "C"
    if len(widths) >= 2 and ratio >= 0.40:
        return "B"
    return "A"


def _status(ok):
    return "PASS" if ok else "FAIL"


def quick_check(floors, site_area_m2, height_m, site_class, building_type,
                dedicated_area_m2=0.0, limits=None, schedule=None):
    """Return {"totals": {...}, "rows": [(ref, item, value, limit, status), ...]}.

    building_type: 'domestic', 'non_domestic' or 'composite'.
    limits: optional {'ozp_max_pr_total', 'ozp_max_pr_domestic',
            'ozp_max_pr_non_domestic', 'lease_max_gfa_m2', 'max_height_m'}.
    """
    s = schedule or load_schedule()
    limits = limits or {}
    rows = []
    cls = site_class if site_class in ("A", "B", "C") else "A"
    if site_class not in ("A", "B", "C"):
        rows.append(("19(3)", "Site class", "%s" % site_class,
                     "Determined by BA (class A figures shown for indication)", "CHECK"))
    t = gfa_totals(floors)
    area = float(site_area_m2)
    pr_d, pr_n = t["domestic"] / area, t["non_domestic"] / area
    Pd = limit("domestic", "plot_ratio", cls, height_m, s)
    Pn = limit("non_domestic", "plot_ratio", cls, height_m, s)

    if building_type == "domestic":
        rows.append(("21(1)", "Domestic PR", round(pr_d, 3), "<= %s" % Pd, _status(pr_d <= Pd + 1e-9)))
    elif building_type == "non_domestic":
        rows.append(("21(1)", "Non-domestic PR", round(pr_n, 3), "<= %s" % Pn, _status(pr_n <= Pn + 1e-9)))
    else:
        frac = pr_d / Pd + pr_n / Pn
        rows.append(("21(2)", "Composite Dd/Pd + Dn/Pn", round(frac, 3), "<= 1.000", _status(frac <= 1 + 1e-9)))
    t["pr_domestic"], t["pr_non_domestic"], t["pr_total"] = pr_d, pr_n, pr_d + pr_n
    t["permitted_pr_domestic"], t["permitted_pr_non_domestic"] = Pd, Pn
    t["max_domestic_pr_at_this_non_domestic"] = (1 - pr_n / Pn) * Pd

    if dedicated_area_m2:
        base = "domestic" if building_type in ("domestic", "composite") else "non_domestic"
        P = Pd if base == "domestic" else Pn
        cap = min(P * 1.2, P + 5.0 * dedicated_area_m2 / area)
        actual = pr_d if base == "domestic" else pr_n
        rows.append(("22", "Bonus PR ceiling (%s)" % base, round(actual, 3), "<= %.3f" % cap,
                     _status(actual <= cap + 1e-9)))

    for part in ("domestic", "non_domestic"):
        amount = t["capped_" + part]
        if amount:
            rows.append(("APP-151", "Capped concessions, %s part" % part.replace("_", "-"), round(amount, 2),
                         "<= %.2f m2 (10%% of the part's GFA)" % (APP151_CAP * t[part]),
                         _status(amount <= APP151_CAP * t[part])))
    if t["needs_prerequisites"]:
        rows.append(("APP-151 para 6", "Prerequisites for these GFA concessions", "not assessed",
                     "APP-152, APP-156, BEAM Plus: see tools/bpr_check.py", "CHECK"))

    for f in floors:
        if f.get("site_coverage_m2") is None:
            continue
        lvl = float(f.get("level_m", 0))
        if f["use"] == "non_domestic" and lvl <= 15:
            lim = 100.0
        else:
            lim = limit(f["use"], "site_coverage_pct", cls, height_m, s)
        pct = float(f["site_coverage_m2"]) / area * 100
        rows.append(("20", "SC %s" % f["name"], round(pct, 1), "<= %s%%" % lim, _status(pct <= lim + 1e-9)))

    for key, label, val in (("ozp_max_pr_domestic", "OZP domestic PR", pr_d),
                            ("ozp_max_pr_non_domestic", "OZP non-domestic PR", pr_n),
                            ("ozp_max_pr_total", "OZP total PR", pr_d + pr_n)):
        if limits.get(key) is not None:
            rows.append(("OZP", label, round(val, 3), "<= %s" % limits[key], _status(val <= limits[key] + 1e-9)))
    if limits.get("lease_max_gfa_m2") is not None:
        v = limits["lease_max_gfa_m2"]
        rows.append(("Lease", "Max GFA", round(t["total"], 2), "<= %s" % v, _status(t["total"] <= v + 1e-6)))
    if limits.get("max_height_m") is not None:
        v = limits["max_height_m"]
        rows.append(("OZP", "Height", height_m, "<= %s m" % v, _status(height_m <= v)))
    return {"totals": t, "rows": rows}


def envelope(site_area_m2, height_m, site_class, building_type="domestic",
             floor_to_floor_m=3.15, podium_floors=0, podium_f2f_m=5.0,
             non_domestic_pr=0.0, ozp_max_pr=None, lease_max_gfa_m2=None, schedule=None):
    """Development envelope for a massing study.

    Returns permitted PR / SC, the governing max GFA (strictest of B(P)R,
    OZP and lease), the max tower footprint and how many floors that GFA
    fills. For composite schemes pass the intended non-domestic PR: the
    domestic allowance follows reg 21(2). Podium floors are taken as
    non-domestic below 15 m at 100% SC (reg 20(3)).
    """
    s = schedule or load_schedule()
    cls = site_class if site_class in ("A", "B", "C") else "A"
    area = float(site_area_m2)
    use = "domestic" if building_type in ("domestic", "composite") else "non_domestic"
    Pd = limit("domestic", "plot_ratio", cls, height_m, s)
    Pn = limit("non_domestic", "plot_ratio", cls, height_m, s)
    if building_type == "composite":
        dom_pr = max(0.0, (1 - non_domestic_pr / Pn) * Pd)
        pr = dom_pr + non_domestic_pr
    else:
        dom_pr = Pd if use == "domestic" else 0.0
        pr = Pd if use == "domestic" else Pn
    governing = "B(P)R First Schedule"
    if ozp_max_pr is not None and ozp_max_pr < pr:
        pr, governing = float(ozp_max_pr), "OZP"
        if building_type == "composite":  # keep the intended non-domestic PR, cut domestic
            dom_pr = max(0.0, pr - non_domestic_pr)
        elif use == "domestic":
            dom_pr = pr
    max_gfa = pr * area
    if lease_max_gfa_m2 is not None and lease_max_gfa_m2 < max_gfa:
        max_gfa, governing = float(lease_max_gfa_m2), "Lease"
        pr = max_gfa / area
        if building_type == "composite":
            dom_pr = max(0.0, pr - non_domestic_pr)
        elif use == "domestic":
            dom_pr = pr
    sc_pct = limit(use, "site_coverage_pct", cls, height_m, s)
    footprint = sc_pct / 100.0 * area
    podium_gfa = podium_floors * area  # 100% SC up to 15 m (non-domestic)
    remaining = max(0.0, max_gfa - podium_gfa)
    tower_floors = int(math.ceil(remaining / footprint)) if footprint and remaining else 0
    stack = podium_floors * podium_f2f_m + tower_floors * floor_to_floor_m
    return {
        "site_class": cls,
        "height_band": band_label(band_index(height_m, s), s),
        "permitted_pr_domestic": Pd,
        "permitted_pr_non_domestic": Pn,
        "domestic_pr": round(dom_pr, 3),
        "plot_ratio": round(pr, 3),
        "max_gfa_m2": round(max_gfa, 2),
        "governing_limit": governing,
        "site_coverage_pct": sc_pct,
        "max_tower_footprint_m2": round(footprint, 2),
        "podium_gfa_m2": round(podium_gfa, 2),
        "tower_floors_at_max_footprint": tower_floors,
        "approx_height_m": round(stack, 2),
        "height_ok": stack <= height_m + 1e-6,
        "note": "Height band assumed = %s m; re-run if the stack lands in another band." % height_m,
    }
