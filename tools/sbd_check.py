#!/usr/bin/env python3
"""Sustainable Building Design checker - PNAP APP-152 (Sept 2023 version).
Building separation (permeability), building setback, site coverage of greenery.

Usage:  python3 sbd_check.py project.json [-o report.md]   (reads the `sustainable_design` block)

`sustainable_design`:
  site_area_m2, single_family_house (bool), tallest_height_m (H, from Level Zero),
  street_canyon_width_m (U, least mean width of the abutting streets),
  planes[]: {name, lp_m (longest continuous projected facade length),
             zones: {low|middle|high: {p_pct, is_pct, pe_pct}},
             min_is_to_boundary_m, min_is_between_facades_m}
  standalone_residential_le_15m (bool)  -> separation exempt (para 6)
  streets[] (setback): {name, width_m, building_height_m, option "corridor"|"podium_garden",
             min_dist_to_centreline_m (building up to 15 m), podium_clear_height_m,
             within_45deg_plane (bool), projection_mm}
  greenery[]: {name, type (key of greenery_factors in pnap/app152.json), area_m2, zone "primary"|"other"}
Prerequisite for APP-151 GFA concessions: a FAIL here puts those concessions at risk.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = json.loads((HERE.parent / "pnap" / "app152.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"


def run(q):
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    a, sep, sb = D["applicability"], D["separation"], D["setback"]
    site = q["site_area_m2"]
    H = q.get("tallest_height_m", 0)
    planes = q.get("planes", [])
    max_lp = max([p.get("lp_m", 0) for p in planes] or [0])
    large = site >= a["building_separation_site_area_m2"]

    # --- building separation ---
    if q.get("standalone_residential_le_15m"):
        add("para 6", "Building separation", "standalone residential ≤ 15 m", "may be exempt", INFO)
    elif not large and max_lp < a["building_separation_lp_m"]:
        add("para 3", "Building separation applicability", f"site {site:g} m², Lp {max_lp:g} m",
            "applies if site ≥ 20,000 m² or Lp ≥ 60 m", INFO, "not applicable")
    else:
        U = q.get("street_canyon_width_m")
        if U:
            lim = sep["lp_max_multiple_of_street_width"] * U
            add("para 4(a), App B 2.2", "Continuous projected facade length Lp", f"{max_lp:g} m",
                f"≤ 5U = {lim:g} m", PASS if max_lp <= lim else FAIL,
                "Required with Table 1 P, not instead of it. Not applicable if no building part is within 30 m "
                "of a street centreline (App B 2.5)")
        hkey = "h_le_60" if H <= 60 else "h_gt_60"
        t1 = D["table_1_permeability_pct"]
        for i, pl in enumerate(planes):
            col = ("large_site_plane_1" if i == 0 else "large_site_plane_2") if large else "small_site_lp_ge_60"
            need = t1[col][hkey]
            if not large and pl.get("lp_m", 0) < a["building_separation_lp_m"]:
                add("App B 3.3", f"{pl['name']}", f"Lp {pl.get('lp_m', 0):g} m", "< 60 m on this plane", INFO,
                    "plane need not be assessed")
                continue
            for zname, z in pl.get("zones", {}).items():
                p = z.get("p_pct")
                add("para 4(b), Table 1", f"{pl['name']} {zname} zone permeability", f"{p}%", f"≥ {need}%",
                    PASS if p is not None and p >= need else FAIL,
                    "The first plane is taken as Plane 1. The PNAP does not say which is which: "
                    "confirm the pair chosen" if large else "")
                if p:
                    is_share = z.get("is_pct", p) / p
                    add("App B 4.2-4.3", f"{pl['name']} {zname} zone IS share of P", f"{is_share:.0%}",
                        "≥ 2/3 (PE ≤ 1/3)", PASS if is_share >= sep["is_min_share_of_p"] - 1e-6 else FAIL)
            if pl.get("min_is_to_boundary_m") is not None:
                v = pl["min_is_to_boundary_m"]
                add("para 4(b)(ii)", f"{pl['name']} IS to boundary / street centreline", f"{v:g} m",
                    "≥ 7.5 m", PASS if v >= sep["is_to_boundary_or_centreline_min_m"] else FAIL)
            if pl.get("min_is_between_facades_m") is not None:
                v = pl["min_is_between_facades_m"]
                add("para 4(b)(iii)", f"{pl['name']} IS between facades", f"{v:g} m", "≥ 15 m",
                    PASS if v >= sep["is_between_facades_min_m"] else FAIL)

    # --- building setback ---
    for st in q.get("streets", []):
        if st["width_m"] >= a["building_setback_street_width_lt_m"]:
            add("para 7", f"Setback – {st['name']}", f"street {st['width_m']:g} m", "applies to streets < 15 m", INFO,
                "not applicable")
            continue
        bh = st.get("building_height_m", H)
        if bh < sb["waiver_if_height_lt_x_street_width"] * st["width_m"]:
            add("para 9", f"Setback – {st['name']}", f"H {bh:g} m", f"< 2 × {st['width_m']:g} m", INFO,
                "setback may be waived")
            continue
        if st.get("option", "corridor") == "corridor":
            v = st.get("min_dist_to_centreline_m")
            add("para 7(a)", f"Setback – {st['name']}: building ≤ 15 m from street centreline",
                f"{v} m", "≥ 7.5 m", PASS if v is not None and v >= sb["min_from_street_centreline_m"] else FAIL)
        else:
            ch = st.get("podium_clear_height_m", 0)
            add("para 7(b)", f"Setback – {st['name']}: podium garden clear height", f"{ch:g} m", "≥ 4.5 m",
                PASS if ch >= sb["podium_garden_min_clear_height_m"] else FAIL)
            add("para 7(b)", f"Setback – {st['name']}: building ≤ 15 m within 45° plane",
                "yes" if st.get("within_45deg_plane") else "no", "within plane",
                PASS if st.get("within_45deg_plane") else FAIL)
        if st.get("projection_mm") is not None:
            add("para 8(b)", f"Setback – {st['name']}: projection into setback", f"{st['projection_mm']} mm",
                "≤ 600 mm, clear height ≥ 2.5 m", PASS if st["projection_mm"] <= sb["projection_max_mm"] else FAIL)

    # --- greenery ---
    if q.get("single_family_house") or site < a["greenery_site_area_min_m2"]:
        add("para 10-11", "Site coverage of greenery", f"site {site:g} m²", "applies to sites ≥ 1,000 m²", INFO,
            "not applicable")
    elif q.get("greenery") is not None:
        t2 = D["table_2_greenery_pct"]["ge_20000" if large else "1000_to_20000"]
        F = D["greenery_factors"]
        prim = tot = feat = 0.0
        for g in q["greenery"]:
            f = F[g["type"]]
            v = g["area_m2"] * f["factor"]
            tot += v
            if g.get("zone") == "primary":
                prim += v
            if f["feature"]:
                feat += v
        need_tot = site * t2["overall"] / 100
        need_prim = site * t2["primary"] / 100
        cap = D["greening_feature_cap_of_required"] * need_tot
        over = max(0.0, feat - cap)
        tot_c = tot - over
        add("Table 2", "Greenery in primary zone (0-15 m)", f"{prim:.0f} m² ({prim / site:.1%})",
            f"≥ {t2['primary']}% = {need_prim:.0f} m²", PASS if prim >= need_prim else FAIL)
        add("App D para 3", "Greening features (counted)", f"{feat:.0f} m²", f"≤ 30% of required = {cap:.0f} m²",
            PASS if over == 0 else WARN, f"{over:.0f} m² over the cap not counted" if over else "")
        add("Table 2", "Overall greenery", f"{tot_c:.0f} m² ({tot_c / site:.1%})",
            f"≥ {t2['overall']}% = {need_tot:.0f} m²", PASS if tot_c >= need_tot else FAIL,
            "after reduction factors (App D)")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows = run(p["sustainable_design"])
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out = [f"# PNAP APP-152 sustainable building design check – {p.get('project', 'Untitled')}", "",
           f"**Result: {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).", "",
           "> Draft for review by an Authorized Person. APP-152 compliance is a prerequisite for APP-151 GFA "
           "concessions; a FAIL here puts those concessions at risk.", "",
           "| Clause | Item | Proposed | Limit | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
