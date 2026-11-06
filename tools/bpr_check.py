#!/usr/bin/env python3
"""B(P)R compliance checker (Hong Kong, Cap. 123F).

Usage:  python3 bpr_check.py project.json [-o report.md]

Checks: site class (reg 18A / 19(3)), site coverage (reg 20), plot ratio incl.
composite formula (reg 21), reg 22 dedication / surrender bonus, GFA
exemptions per PNAP APP-2 and the APP-151 10% cap, storey height (reg 24),
open space (reg 25), prescriptive lighting & ventilation (regs 30-32, 34, 36),
plus OZP / lease limits when given.

The output is a draft for an Authorized Person to review. It is not a
statutory submission. First and Second Schedule figures verified against the
official consolidated Cap. 123F (17-09-2026).
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEDULE = json.loads((HERE.parent / "bpr" / "first_schedule.json").read_text(encoding="utf-8"))

PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"

# exemption categories -> fraction of the area disregarded from GFA
EXEMPT_FRACTION = {
    "mandatory_plant": 1.0,          # reg 23(3)(b), APP-2 para 11
    "non_mandatory_plant": 1.0,      # APP-2 para 13, subject to APP-151 cap
    "green_feature": 1.0,            # APP-151, subject to cap
    "car_park_underground": 1.0,     # APP-2 para 18(a)
    "car_park_above_100": 1.0,       # APP-2 para 18(b)(i)/(c)/(d)/(e)
    "car_park_above_50": 0.5,        # APP-2 para 18(b)(ii)
    "refuge_floor": 1.0,             # APP-2 para 5
    "bicycle_parking": 1.0,          # APP-2 para 21
    "other_disregarded": 1.0,        # anything else the AP justifies
}
CAPPED = {"non_mandatory_plant", "green_feature"}
APP151_CAP = 0.10


def band_index(height):
    for i, (lo, hi) in enumerate(SCHEDULE["height_bands_m"]):
        if hi is None or height <= hi:
            return i
    return len(SCHEDULE["height_bands_m"]) - 1


def band_label(i):
    lo, hi = SCHEDULE["height_bands_m"][i]
    return f"> {lo} m" if hi is None else (f"≤ {hi} m" if lo == 0 else f"> {lo} m, ≤ {hi} m")


def limit(use, kind, site_class, height):
    table = SCHEDULE["domestic" if use == "domestic" else "non_domestic"]
    return table[kind][site_class][band_index(height)]


def classify_site(site):
    """Derive class from street data if not given (reg 18A)."""
    if site.get("class"):
        return site["class"], "given"
    widths = [w for w in site.get("street_widths_m", []) if w >= 4.5]
    perim = site.get("perimeter_m")
    front = site.get("frontage_on_specified_streets_m")
    if not site.get("street_widths_m") or not widths:
        return "BA", "no street ≥ 4.5 m (reg 19(3))"
    if len(widths) >= 3 and perim and front and front / perim >= 0.60:
        return "C", "3 streets ≥ 4.5 m, frontage ≥ 60%"
    if len(widths) >= 2 and perim and front and front / perim >= 0.40:
        return "B", "2 streets ≥ 4.5 m, frontage ≥ 40%"
    return "A", "1 street ≥ 4.5 m"


def fmt(x, nd=2):
    return f"{x:,.{nd}f}"


def run(p):
    rows, notes = [], []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    site = p["site"]
    bldg = p["building"]
    lims = p.get("limits", {})
    area = float(site["area_m2"])
    height = float(bldg["height_m"])
    site_class, why = classify_site(site)

    add("18A", "Site class", site_class, "-", INFO, why)
    if site_class == "BA":
        add("19(3)", "Height / SC / PR", "-", "Determined by BA", WARN,
            "Site abuts no street ≥ 4.5 m; schedule limits do not apply")
        site_class_for_tables = "A"
        notes.append("Class A figures used below for indication only.")
    else:
        site_class_for_tables = site_class

    # reg 19A (frontage/depth) was repealed by L.N. 406 of 1987 - not checked.

    bi = band_index(height)
    add("23(1)", "Building height", f"{height} m", band_label(bi), INFO,
        "mean level of (lowest) specified street ≥ 4.5 m to mean roof height over highest usable floor")
    if lims.get("max_height_m") is not None:
        add("OZP", "Height restriction", f"{height} m", f"≤ {lims['max_height_m']} m",
            PASS if height <= lims["max_height_m"] else FAIL)

    # --- GFA & exemptions per floor
    floors = p.get("floors", [])
    gfa = {"domestic": 0.0, "non_domestic": 0.0}
    gross_total = 0.0
    capped = {"domestic": 0.0, "non_domestic": 0.0}
    exempt_lines = []
    for f in floors:
        use = f["use"]
        n = int(f.get("count", 1))  # typical floors: same plate repeated n times
        gross = float(f["gross_area_m2"]) * n
        gross_total += gross
        disregarded = 0.0
        for e in f.get("exempt", []):
            cat = e["category"]
            frac = EXEMPT_FRACTION.get(cat)
            if frac is None:
                raise SystemExit(f"Unknown exemption category '{cat}' on floor {f['name']}")
            d = float(e["area_m2"]) * frac * n
            disregarded += d
            if cat in CAPPED:
                capped[use] += d
            exempt_lines.append((f["name"], e.get("item", cat), cat, float(e["area_m2"]) * n, d))
        f["_accountable"] = gross - disregarded
        gfa[use] += f["_accountable"]

    total_gfa = gfa["domestic"] + gfa["non_domestic"]
    # APP-151 para 4 (July 2025): 10% of total GFA of the development; in a composite building or a
    # development with domestic and non-domestic buildings, each part is capped on its own GFA.
    labels = {"domestic": "domestic part", "non_domestic": "non-domestic part"}
    for part in ("domestic", "non_domestic"):
        if capped[part]:
            base = gfa[part]
            ok = capped[part] <= APP151_CAP * base
            pct = f"{capped[part] / base * 100:.1f}%" if base else "no GFA"
            who = f" – {labels[part]}" if gfa["domestic"] and gfa["non_domestic"] else ""
            add("APP-151 para 4", f"Capped concessions{who} (non-mandatory plant + green features)",
                f"{fmt(capped[part])} m² ({pct})", f"≤ 10% of GFA = {fmt(APP151_CAP * base)} m²", PASS if ok else FAIL,
                "Also needs the para 6 prerequisites: APP-152, APP-156 (domestic / composite), BEAM Plus NB registration and target rating")

    # --- Plot ratio (reg 21)
    btype = bldg["type"]
    pr_d = gfa["domestic"] / area
    pr_n = gfa["non_domestic"] / area
    Pd = limit("domestic", "plot_ratio", site_class_for_tables, height)
    Pn = limit("non_domestic", "plot_ratio", site_class_for_tables, height)
    dedicated = float(site.get("dedicated_area_m2", 0) or 0)
    if dedicated:
        notes.append("Reg 21 results below use the un-bonused limits; see the reg 22 line for the bonus ceiling.")
    if btype == "domestic":
        add("21(1)", "Domestic plot ratio", fmt(pr_d, 3), f"≤ {Pd}", PASS if pr_d <= Pd + 1e-9 else FAIL)
    elif btype == "non_domestic":
        add("21(1)", "Non-domestic plot ratio", fmt(pr_n, 3), f"≤ {Pn}", PASS if pr_n <= Pn + 1e-9 else FAIL)
    else:
        allowed_d = (1 - pr_n / Pn) * Pd
        frac = pr_d / Pd + pr_n / Pn
        add("21(2)", "Composite: Dd/Pd + Dn/Pn", fmt(frac, 3), "≤ 1.000", PASS if frac <= 1 + 1e-9 else FAIL,
            f"Dn = {fmt(pr_n,3)} (Pn {Pn}); Dd = {fmt(pr_d,3)} (Pd {Pd}); max domestic PR at this Dn = {fmt(allowed_d,3)}")
    add("21(3)", "Total accountable GFA", f"{fmt(total_gfa)} m²", "-", INFO,
        f"domestic {fmt(gfa['domestic'])} m², non-domestic {fmt(gfa['non_domestic'])} m²; gross built {fmt(gross_total)} m²")

    # OZP / lease
    if lims.get("ozp_max_pr_domestic") is not None:
        v = lims["ozp_max_pr_domestic"]
        add("OZP", "Domestic PR", fmt(pr_d, 3), f"≤ {v}", PASS if pr_d <= v + 1e-9 else FAIL)
    if lims.get("ozp_max_pr_non_domestic") is not None:
        v = lims["ozp_max_pr_non_domestic"]
        add("OZP", "Non-domestic PR", fmt(pr_n, 3), f"≤ {v}", PASS if pr_n <= v + 1e-9 else FAIL)
    if lims.get("ozp_max_pr_total") is not None:
        v = lims["ozp_max_pr_total"]
        add("OZP", "Total PR", fmt(pr_d + pr_n, 3), f"≤ {v}", PASS if pr_d + pr_n <= v + 1e-9 else FAIL)
    if lims.get("lease_max_gfa_m2") is not None:
        v = lims["lease_max_gfa_m2"]
        add("Lease", "Max GFA", f"{fmt(total_gfa)} m²", f"≤ {fmt(v)} m²", PASS if total_gfa <= v + 1e-6 else FAIL,
            "Check lease definition of GFA; it may differ from B(P)R")
    if lims.get("lease_min_gfa_m2") is not None:
        v = lims["lease_min_gfa_m2"]
        add("Lease", "Min GFA", f"{fmt(total_gfa)} m²", f"≥ {fmt(v)} m²", PASS if total_gfa >= v - 1e-6 else FAIL)

    if dedicated and site_class != "BA":
        # reg 22(1) dedication for public passage (setback from ground to >= 5.5 m, or 3.3 m)
        # reg 22(2) surrender for street widening - same formulae
        base_use = "domestic" if btype in ("domestic", "composite") else "non_domestic"
        P = Pd if base_use == "domestic" else Pn
        bonus_pr_cap = min(P * 1.20, P + 5 * dedicated / area)
        actual = pr_d if base_use == "domestic" else pr_n
        add("22", f"Bonus plot ratio ({base_use.replace('_','-')} part)", fmt(actual, 3),
            f"≤ {fmt(bonus_pr_cap,3)} (lesser of 1.2 × {P} and {P} + 5 × {fmt(dedicated)}/{fmt(area)})",
            PASS if actual <= bonus_pr_cap + 1e-9 else FAIL, "Needs Government consent to dedication / BA permission; setback from G/L to ≥ 5.5 m (or 3.3 m)")
        notes.append(f"Reg 22: site coverage may rise by 1500 × {fmt(dedicated)} / ({fmt(area)} × {height}) = "
                     f"{1500*dedicated/(area*height):.2f} percentage points on the part concerned; other parts stay at the permitted %.")
        notes.append("Reg 23(2): site area includes the dedicated area and excludes any street or service lane.")

    # --- Site coverage (reg 20)
    for f in floors:
        sc_area = f.get("site_coverage_m2")
        if sc_area is None:
            continue
        lvl = float(f.get("level_m", 0))  # for typical floors give the lowest level
        use = f["use"]
        if use == "non_domestic" and lvl <= 15:
            lim_pct = 100.0
            ref_note = "non-domestic ≤ 15 m (reg 20(3))"
        else:
            lim_pct = limit(use, "site_coverage_pct", site_class_for_tables, height)
            ref_note = f"{use.replace('_','-')} table, class {site_class_for_tables}"
        pct = float(sc_area) / area * 100
        add("20", f"Site coverage – {f['name']} (+{lvl} m)", f"{pct:.1f}%", f"≤ {lim_pct}%",
            PASS if pct <= lim_pct + 1e-9 else FAIL, ref_note)

    # --- Open space (reg 25)
    os_ = p.get("open_space")
    if os_ and btype in ("domestic", "composite") and site_class != "BA":
        req = SCHEDULE["second_schedule_open_space_fraction_of_roofed_over_area"][site_class]
        need = req * float(os_["roofed_over_area_m2"])
        got = float(os_["provided_m2"])
        add("25 / Sch 2", "Open space", f"{fmt(got)} m²", f"≥ {fmt(need)} m² ({req:.3g} × roofed-over)",
            PASS if got >= need - 1e-6 else FAIL)
        if os_.get("rear_setback_m") is not None:
            r = float(os_["rear_setback_m"])
            add("25", "Distance from rear boundary", f"{r} m", "≥ 1.5 m", PASS if r >= 1.5 else FAIL)
        if os_.get("level_below_lowest_floor_mm") is not None:
            v = float(os_["level_below_lowest_floor_mm"])
            add("25(1)(a)", "Open space level below floor of lowermost storey", f"{v:.0f} mm", "≥ 150 mm",
                PASS if v >= 150 else FAIL)

    # --- Lighting & ventilation (regs 24, 30-36)
    for r in p.get("rooms", []):
        a = float(r["floor_area_m2"])
        use = r.get("use", "habitable")
        label = f"{r['name']} ({use})"
        if r.get("ceiling_height_m") is not None and use in ("habitable", "office"):
            h = float(r["ceiling_height_m"])
            add("24", f"{label} floor-to-ceiling", f"{h} m", "≥ 2.5 m (≥ 2.3 m under beams)", PASS if h >= 2.5 else FAIL)
        if r.get("performance_based"):
            add("30-31", label, "Performance-based L&V", "APP-130", WARN, "Prescriptive test not applied")
            continue
        if use == "office" and r.get("mechanical_ventilation_ach") is not None:
            v = float(r["mechanical_ventilation_ach"])
            add("34", f"{label} mechanical ventilation", f"{v} ACH", "≥ 5 ACH + approved artificial lighting",
                PASS if v >= 5 else FAIL, "Only where reg 31 cannot be met")
            continue
        g, o = float(r["glass_m2"]), float(r["openable_m2"])
        if use in ("bathroom", "toilet"):
            add("36", f"{label} glass", f"{fmt(g)} m²", f"≥ {fmt(a/10)} m² (1/10)", PASS if g >= a / 10 - 1e-9 else FAIL)
            add("36", f"{label} openable", f"{fmt(o)} m²", f"≥ {fmt(a/10)} m² (1/10, opens to open air)", PASS if o >= a / 10 - 1e-9 else FAIL)
            if r.get("window_head_m") is not None:
                h = float(r["window_head_m"])
                add("36", f"{label} top of opening", f"{h} m", "≥ 2.0 m", PASS if h >= 2.0 else FAIL)
            continue
        add("30", f"{label} glass", f"{fmt(g)} m²", f"≥ {fmt(a/10)} m² (1/10)", PASS if g >= a / 10 - 1e-9 else FAIL)
        add("30", f"{label} openable", f"{fmt(o)} m²", f"≥ {fmt(a/16)} m² (1/16)", PASS if o >= a / 16 - 1e-9 else FAIL)
        if r.get("window_head_m") is not None:
            need = 1.9 if bldg.get("house") else 2.0
            h = float(r["window_head_m"])
            add("30", f"{label} top of opening", f"{h} m", f"≥ {need} m", PASS if h >= need else FAIL)
        if r.get("max_distance_to_window_m") is not None and r.get("use", "habitable") == "habitable":
            d = float(r["max_distance_to_window_m"])
            add("32", f"{label} furthest point to window", f"{d} m", "≤ 9 m", PASS if d <= 9 else FAIL)
        if r.get("external_air") is False:
            add("31", f"{label} external air", "not confirmed", "street ≥ 4.5 m or reg 31 planes", WARN)

    return rows, exempt_lines, notes, total_gfa


def report(p, rows, exempt_lines, notes):
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    out = [f"# B(P)R compliance check – {p.get('project','Untitled')}", ""]
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out.append(f"**Result: the scheme {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).")
    out.append("")
    out.append("> Draft for review and signature by an Authorized Person. Schedule figures from the official "
               "consolidated Cap. 123F (17-09-2026). Lease and OZP conditions must be checked separately.")
    out.append("")
    out += ["| Reg | Item | Proposed | Limit | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    for ref, item, val, lim, st, note in rows:
        out.append(f"| {ref} | {item} | {val} | {lim} | {st} | {note} |")
    if exempt_lines:
        out += ["", "## GFA exemptions claimed", "",
                "| Floor | Item | Category | Area m² | Disregarded m² |", "| --- | --- | --- | --- | --- |"]
        for fl, it, cat, a, d in exempt_lines:
            out.append(f"| {fl} | {it} | {cat} | {fmt(a)} | {fmt(d)} |")
    if notes:
        out += ["", "## Notes", ""] + [f"- {n}" for n in notes]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows, ex, notes, _ = run(p)
    md = report(p, rows, ex, notes)
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if any(r[4] == FAIL for r in rows) else 0)


if __name__ == "__main__":
    main()
