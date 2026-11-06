# -*- coding: utf-8 -*-
"""Sheet set, title block fields and GFA colour legend for BD submissions.

The sheet list follows what Building Authority general building plans
normally carry (Building (Administration) Regulations, Cap. 123A, reg 8, and
the BD's plan-submission practice). Items marked [verify] are office
practice, not statute: check them against the current Cap. 123A text, the
relevant PNAP ADM / APP notes and the BD e-submission requirements before
issue. Every sheet is a draft for the Authorized Person to sign.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import re

from .areas import ACCOUNTABLE, NOT_GFA, EXEMPT_FRACTION

# Minimum scales as commonly applied to general building plans [verify reg 8].
SCALE_BLOCK_PLAN = 1000      # location / block plan, not less than 1:1000
SCALE_SITE_PLAN = 500        # site plan, not less than 1:500
SCALE_GBP = 100              # floor plans, sections, elevations, not less than 1:100
SCALE_GBP_LARGE_SITE = 200   # [verify] larger sites with BD agreement

# Title block parameter names created by the pyRevit / Dynamo sheet tools.
TITLEBLOCK_FIELDS = [
    ("HK_Project_Title", "工程名稱 Project"),
    ("HK_Lot_No", "地段編號 Lot No."),
    ("HK_Address", "地址 Address"),
    ("HK_AP_Name", "認可人士 Authorized Person"),
    ("HK_AP_Reg_No", "認可人士註冊編號 AP Reg. No."),
    ("HK_RSE_Name", "註冊結構工程師 RSE"),
    ("HK_BD_Ref", "屋宇署檔案編號 BD Ref. (BD 2/xxxx/yy)"),
    ("HK_Submission_Type", "呈交類別 Submission (e.g. GBP first submission / amendment)"),
    ("HK_Drawing_Status", "狀態 Status"),
]

# (code, English name, Chinese name, scale, view kind, per-level?)
# view kind: site | plan | section | elevation | calc | schedule | detail
BD_GBP_TEMPLATE = [
    ("000", "Drawing list and general notes", "圖則目錄及一般附註", None, "schedule", False),
    ("001", "Location and block plan", "位置圖及地段圖", SCALE_BLOCK_PLAN, "site", False),
    ("002", "Site plan (site boundary, street widths, levels)", "地盤平面圖", SCALE_SITE_PLAN, "site", False),
    ("003", "Site formation / EVA and street levels", "地盤平整及緊急車輛通道", SCALE_SITE_PLAN, "site", False),
    ("010", "Site coverage calculation plan", "上蓋面積計算圖", SCALE_SITE_PLAN, "calc", False),
    ("011", "Plot ratio and GFA calculation summary", "地積比率及總樓面面積計算", None, "calc", False),
    ("012", "GFA calculation plan", "總樓面面積計算圖", SCALE_GBP, "calc", True),
    ("013", "Open space calculation plan (reg 25)", "休憩用地計算圖", SCALE_SITE_PLAN, "calc", False),
    ("020", "Floor plan", "樓層平面圖", SCALE_GBP, "plan", True),
    ("030", "Roof plan", "天台平面圖", SCALE_GBP, "plan", False),
    ("040", "Section", "剖面圖", SCALE_GBP, "section", False),
    ("050", "Elevation", "立面圖", SCALE_GBP, "elevation", False),
    ("060", "Means of escape plan (FS Code Part B)", "逃生途徑平面圖", SCALE_GBP, "plan", True),
    ("070", "Fire resisting construction plan (FS Code Part C)", "耐火結構平面圖", SCALE_GBP, "plan", True),
    ("080", "Barrier free access plan (DM 2008)", "無障礙通道平面圖", SCALE_GBP, "plan", True),
    ("090", "Lighting and ventilation calculation (regs 30-36)", "採光及通風計算", None, "calc", False),
    ("095", "Sustainable building design / APP-151 GFA concession schedule", "可持續建築設計及樓面面積寬免表", None, "calc", False),
]

# Colours for GFA calculation plans (RGB). Keep accountable areas plain
# hatch-free and give each exemption type its own colour so the BD officer
# can trace each figure in the calculation table to the plan. [verify office standard]
GFA_COLOURS = {
    ACCOUNTABLE: ((255, 236, 179), "計入總樓面面積 Accountable GFA"),
    NOT_GFA: ((235, 235, 235), "不屬樓面面積 Not floor space (void / open)"),
    "mandatory_plant": ((144, 202, 249), "強制機房 Mandatory plant room (reg 23(3)(b))"),
    "non_mandatory_plant": ((129, 212, 250), "非強制機房 Non-mandatory plant (APP-151 cap)"),
    "green_feature": ((165, 214, 167), "綠化及康樂設施 Green / amenity feature (APP-151 cap)"),
    "green_feature_uncapped": ((129, 199, 132), "不計上限綠化設施 Green / amenity feature (no APP-151 cap)"),
    "car_park_underground": ((206, 147, 216), "地庫停車場 Underground car park"),
    "car_park_above_100": ((225, 190, 231), "地面以上停車場 100% Car park above ground (100%)"),
    "car_park_above_50": ((243, 229, 245), "地面以上停車場 50% Car park above ground (50%)"),
    "refuge_floor": ((255, 171, 145), "庇護層 Refuge floor"),
    "bicycle_parking": ((200, 230, 201), "單車停泊處 Bicycle parking"),
    "other_disregarded": ((207, 216, 220), "其他豁免 Other disregarded (justify)"),
}
assert set(GFA_COLOURS) == set(EXEMPT_FRACTION) | {ACCOUNTABLE, NOT_GFA}


def scale_text(scale):
    return "" if not scale else "1:%d" % scale


def drawing_number(prefix, code, seq=0, level_tag=None):
    """e.g. drawing_number('GBP', '020', level_tag='05F') -> 'GBP-020-05F'."""
    parts = [prefix, code]
    if level_tag:
        parts.append(level_tag)
    elif seq:
        parts.append("%02d" % seq)
    return "-".join(parts)


def level_tag(level_name):
    """Short, sortable tag from a level name: 'B1/F' -> 'B1F', '5/F' -> '05F',
    'G/F' -> 'GF', 'LG1' -> 'LG1F', 'R/F' or 'Roof' -> 'RF', 'Level 12' -> '12F'."""
    t = re.sub(r"[\s/_.-]", "", ("%s" % level_name).upper())
    if t in ("GF", "G", "GROUND", "GROUNDFLOOR", "LEVELG", "LEVEL0", "0F"):
        return "GF"
    if t.startswith("ROOF") or t in ("RF", "R", "MAINROOF", "UPPERROOF"):
        return "UR" if t.startswith("UPPER") else "RF"
    m = re.match(r"^(LG|UG)(\d*)", t)
    if m:
        return "%s%sF" % (m.group(1), m.group(2))
    t = re.sub(r"^(LEVEL|LVL|L)(?=\d)", "", t)
    m = re.match(r"^(B?)(\d+)", t)
    if m:
        n = int(m.group(2))
        return ("B%dF" % n) if m.group(1) else ("%02dF" % n)
    return re.sub(r"[^A-Z0-9]", "", t)[:6] or "XX"


def sheet_list(levels, prefix="GBP", plan_scale=SCALE_GBP, sections=2, elevations=4,
               include=None):
    """Expand the template into concrete sheets.

    levels      ordered list of level names that need per-level sheets
    include     optional set of template codes to keep (default: all)
    Returns dicts: number, name, name_zh, scale, kind, level (or None).
    """
    out = []
    for code, name, zh, scale, kind, per_level in BD_GBP_TEMPLATE:
        if include and code not in include:
            continue
        if scale == SCALE_GBP:
            scale = plan_scale
        if per_level:
            for lv in levels:
                out.append({"number": drawing_number(prefix, code, level_tag=level_tag(lv)),
                            "name": "%s - %s" % (name, lv), "name_zh": "%s - %s" % (zh, lv),
                            "scale": scale_text(scale), "kind": kind, "level": lv})
        elif kind in ("section", "elevation"):
            n = sections if kind == "section" else elevations
            for i in range(1, n + 1):
                suffix = chr(64 + i) if kind == "section" else "%d" % i
                label = ("Section %s-%s" % (suffix, suffix)) if kind == "section" else ("Elevation %s" % suffix)
                out.append({"number": drawing_number(prefix, code, seq=i),
                            "name": label, "name_zh": "%s %s" % (zh, suffix),
                            "scale": scale_text(scale), "kind": kind, "level": None})
        else:
            out.append({"number": drawing_number(prefix, code), "name": name, "name_zh": zh,
                        "scale": scale_text(scale), "kind": kind, "level": None})
    seen = set()
    for s in out:
        if s["number"] in seen:
            raise ValueError("Duplicate drawing number %s (two levels give the same tag?)" % s["number"])
        seen.add(s["number"])
    return out


def legend_rows():
    """[(category, (r, g, b), label, fraction disregarded)] for a colour legend."""
    rows = []
    for cat in (ACCOUNTABLE,) + tuple(sorted(EXEMPT_FRACTION)) + (NOT_GFA,):
        rgb, label = GFA_COLOURS[cat]
        frac = 0.0 if cat == ACCOUNTABLE else (EXEMPT_FRACTION.get(cat, 1.0) if cat != NOT_GFA else None)
        rows.append((cat, rgb, label, frac))
    return rows
