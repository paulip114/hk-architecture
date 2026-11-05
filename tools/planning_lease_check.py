#!/usr/bin/env python3
"""OZP + lease constraint checker (Town Planning Ordinance Cap. 131, JPN 4/5/9,
LAO PN 2/2018, 2/2023, 4/2021).

Usage:
  python3 planning_lease_check.py project.json [--block planning.json] [-o report.md]

GFA (domestic / non-domestic) is computed from the project's `floors[]` the same
way as bpr_check.py (B(P)R accountable GFA), as JPN 4 makes BD's GFA the figure
PlanD and LandsD use. The `planning_lease` block is read from the project file or
from --block. Fields (all optional except ozp.zone):

ozp:   plan_no, zone, max_pr_domestic, max_pr_non_domestic, max_pr_total,
       existing_pr (the "or existing building, whichever is greater" clause),
       max_bh_mpd, max_bh_storeys, max_sc_pct, minor_relaxation (bool),
       column1_uses[], column2_uses[], nba_m2 (non-building area shown on plan)
proposal: uses[], site_formation_level_mpd, main_roof_mpd, storeys, sc_pct,
       building_kind ("residential" / "composite" / "other"), roof_area_m2,
       nba_built_over_m2,
       rooftop[] of {name, type: ancillary|lift|feature|spire|signboard,
                     height_above_roof_m, enclosed_covered_m2}
lease: lot, user_allows[] (uses the user clause permits), max_gfa_m2, min_gfa_m2,
       max_sc_pct, max_height_mpd, gfa_exemption_clause (bool), sc_discretion_clause (bool),
       ddh_clause (bool), building_covenant_months
lease_gfa_concessions[]: {item, area_m2, group: I | II_nil | II_premium | III}
bonus_pr:  district, oldest_op_year, residential_share, application_year
premium_estimate: before_rate_hkd_m2, after_rate_hkd_m2, before_gfa_m2 (indicative only)

Exit code 1 when any item fails. Output is a draft for an AP / planning consultant.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bpr_check import EXEMPT_FRACTION  # noqa: E402  same GFA rules as the B(P)R checker

D = json.loads((HERE.parent / "planning" / "planning_lands.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"
EPS = 1e-9


def fmt(x, nd=2):
    return f"{x:,.{nd}f}"


def gfa_split(p):
    g = {"domestic": 0.0, "non_domestic": 0.0}
    for f in p.get("floors", []):
        n = int(f.get("count", 1))
        acc = float(f["gross_area_m2"]) * n
        for e in f.get("exempt", []):
            acc -= float(e["area_m2"]) * EXEMPT_FRACTION[e["category"]] * n
        g[f["use"]] += acc
    return g


def rooftop_cap(kind, typ, h):
    """JPN 5 para 10: height above main roof beyond which a roof-top structure counts."""
    r = D["jpn5_rooftop"]
    if typ in ("ancillary", "lift", "signboard"):
        a = r["ancillary"]
        if h <= a["low_rise_limit_m"]:
            return a["low_rise_lift_cap_m"] if typ == "lift" else a["low_rise_cap_m"]
        return min(a["tall_pct"] * h, a["tall_cap_m"])
    if typ in ("feature", "spire"):
        if kind in ("residential", "composite"):
            f = r["feature_resi_composite"]
            return min(f["pct"] * h, f["cap_m"])
        f = r["feature_other"]
        if h <= f["low_rise_limit_m"]:
            return f["low_rise_cap_m"]
        return f["tall_pct"] * h + (f["spire_extra_pct"] * h if typ == "spire" else 0)
    raise SystemExit(f"Unknown roof-top type '{typ}'")


def run(p, q):
    rows, notes = [], []
    needs = {"s16": [], "s12A": [], "lease_mod": [], "consent_premium": [], "nil_premium": []}

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    area = float(p["site"]["area_m2"])
    g = gfa_split(p)
    total = g["domestic"] + g["non_domestic"]
    pr_d, pr_n = g["domestic"] / area, g["non_domestic"] / area
    ozp, prop, lease = q.get("ozp", {}), q.get("proposal", {}), q.get("lease", {})
    relax = bool(ozp.get("minor_relaxation"))
    add("JPN 4", "GFA used (BD basis)", f"{fmt(total)} m²", "-", INFO,
        f"domestic {fmt(g['domestic'])}, non-domestic {fmt(g['non_domestic'])}; site {fmt(area)} m²")

    # ---------- OZP: uses
    zone = ozp.get("zone", "?")
    add("OZP", "Plan / zone", f"{ozp.get('plan_no', '-')} / {zone}", "-", INFO)
    c1 = [u.lower() for u in ozp.get("column1_uses", [])]
    c2 = [u.lower() for u in ozp.get("column2_uses", [])]
    for u in prop.get("uses", []):
        ul = u.lower()
        if not c1 and not c2:
            add("Notes", f"Use: {u}", "-", "Column 1 / 2 not given", WARN, "Read the zone's Notes")
        elif ul in c1:
            add("Notes", f"Use: {u}", "Column 1", "always permitted", PASS)
        elif ul in c2:
            add("Notes", f"Use: {u}", "Column 2", "needs s16 permission", WARN)
            needs["s16"].append(f"Column 2 use '{u}'")
        else:
            add("Notes", f"Use: {u}", "not in Column 1 or 2", "not permitted", FAIL, "s12A rezoning, or redesign")
            needs["s12A"].append(f"use '{u}' not provided for in {zone}")

    # ---------- OZP: PR
    def pr_check(label, actual, lim):
        if lim is None:
            return
        lim = max(float(lim), float(ozp.get("existing_pr") or 0)) if label == "Total PR" else float(lim)
        if actual <= lim + EPS:
            add("Remarks", label, fmt(actual, 3), f"≤ {lim}", PASS)
            return
        over = (actual / lim - 1) * 100
        if relax:
            add("Remarks", label, fmt(actual, 3), f"≤ {lim}", WARN,
                f"+{over:.1f}%: minor relaxation under s16 (needs planning and design merits)")
            needs["s16"].append(f"minor relaxation of {label} ({fmt(actual,3)} vs {lim})")
        else:
            add("Remarks", label, fmt(actual, 3), f"≤ {lim}", FAIL, f"+{over:.1f}%, no minor relaxation clause: s12A")
            needs["s12A"].append(f"{label} above OZP")

    pr_check("Domestic PR", pr_d, ozp.get("max_pr_domestic"))
    pr_check("Non-domestic PR", pr_n, ozp.get("max_pr_non_domestic"))
    pr_check("Total PR", pr_d + pr_n, ozp.get("max_pr_total"))

    # ---------- OZP: building height (JPN 5)
    kind = prop.get("building_kind", "composite")
    if prop.get("main_roof_mpd") is not None:
        roof = float(prop["main_roof_mpd"])
        base = prop.get("site_formation_level_mpd")
        h = roof - float(base) if base is not None else None
        top = roof
        roof_area = prop.get("roof_area_m2")
        enclosed = sum(float(s.get("enclosed_covered_m2", 0)) for s in prop.get("rooftop", []))
        if roof_area and enclosed > D["jpn5_rooftop"]["enclosed_max_fraction_of_roof"] * float(roof_area):
            tallest = max((float(s["height_above_roof_m"]) for s in prop.get("rooftop", [])), default=0)
            top = roof + tallest
            add("JPN 5 p10", "Enclosed roof-top structures", f"{fmt(enclosed)} m²",
                f"≤ 50% of roof ({fmt(0.5*float(roof_area))} m²)", WARN, "Exceeds 50%: counted in building height")
        for s in prop.get("rooftop", []):
            if h is None:
                add("JPN 5 p10", f"Roof-top: {s['name']}", f"{s['height_above_roof_m']} m", "needs site level", WARN)
                continue
            cap = rooftop_cap(kind, s["type"], h)
            v = float(s["height_above_roof_m"])
            ok = v <= cap + EPS
            add("JPN 5 p10", f"Roof-top: {s['name']} ({s['type']})", f"{v} m", f"≤ {fmt(cap)} m above main roof",
                PASS if ok else WARN, "" if ok else "Counted in building height")
            if not ok:
                top = max(top, roof + v)
        if ozp.get("max_bh_mpd") is not None:
            lim = float(ozp["max_bh_mpd"])
            if top <= lim + EPS:
                add("Remarks", "Building height", f"{fmt(top)} mPD", f"≤ {lim} mPD", PASS,
                    f"main roof; building height {fmt(h)} m from mean formation level" if h is not None else "main roof")
            elif relax:
                add("Remarks", "Building height", f"{fmt(top)} mPD", f"≤ {lim} mPD", WARN, "minor relaxation under s16")
                needs["s16"].append(f"minor relaxation of BH ({fmt(top)} vs {lim} mPD)")
            else:
                add("Remarks", "Building height", f"{fmt(top)} mPD", f"≤ {lim} mPD", FAIL, "s12A")
                needs["s12A"].append("BH above OZP")
    if ozp.get("max_bh_storeys") is not None and prop.get("storeys") is not None:
        ok = int(prop["storeys"]) <= int(ozp["max_bh_storeys"])
        add("Remarks", "Storeys", prop["storeys"], f"≤ {ozp['max_bh_storeys']}", PASS if ok else WARN,
            "Basements count unless the plan says otherwise (JPN 5 p7)")
    if ozp.get("max_sc_pct") is not None and prop.get("sc_pct") is not None:
        ok = float(prop["sc_pct"]) <= float(ozp["max_sc_pct"]) + EPS
        add("Remarks", "Site coverage", f"{prop['sc_pct']}%", f"≤ {ozp['max_sc_pct']}%", PASS if ok else WARN, "JPN 7")
        if not ok:
            (needs["s16"] if relax else needs["s12A"]).append("SC above OZP")
    if ozp.get("nba_m2"):
        built = float(prop.get("nba_built_over_m2", 0))
        add("Plan", "Non-building area", f"{fmt(built)} m² built over", f"0 of {fmt(float(ozp['nba_m2']))} m²",
            PASS if built == 0 else WARN, "" if built == 0 else "minor relaxation under s16, if the Remarks allow")
        if built:
            needs["s16"].append("building over NBA")

    # ---------- Lease
    lease_gfa = total
    if lease:
        add("Lease", "Lot", lease.get("lot", "-"), "-", INFO, "Check all modification letters too")
        allows = [u.lower() for u in lease.get("user_allows", [])]
        if allows:
            for u in prop.get("uses", []):
                ok = u.lower() in allows
                add("Lease user", f"Use: {u}", "permitted" if ok else "outside user clause", "-", PASS if ok else FAIL,
                    "" if ok else "Waiver (temporary) or lease modification")
                if not ok:
                    needs["lease_mod"].append(f"user clause does not cover '{u}'")
        conc = q.get("lease_gfa_concessions", [])
        add_back = 0.0
        for c in conc:
            grp, a = c["group"], float(c["area_m2"])
            if grp == "I":
                add("JPN 4", f"Concession: {c['item']}", f"{fmt(a)} m²", "Group I", PASS, D["jpn4_groups"]["I"])
            elif grp in ("II_nil", "II_premium"):
                if lease.get("gfa_exemption_clause"):
                    add("JPN 4", f"Concession: {c['item']}", f"{fmt(a)} m²", f"Group {grp}", PASS if grp == "II_nil" else WARN,
                        "Lease has exemption clause; " + ("admin fee only" if grp == "II_nil" else "premium payable"))
                    (needs["nil_premium"] if grp == "II_nil" else needs["consent_premium"]).append(f"{c['item']} GFA concession")
                else:
                    add("JPN 4", f"Concession: {c['item']}", f"{fmt(a)} m²", f"Group {grp}", FAIL,
                        "No exemption clause in lease: counts as GFA unless the lease is modified")
                    needs["lease_mod"].append(f"add GFA exemption clause for {c['item']}")
                    add_back += a
            else:
                add("JPN 4", f"Concession: {c['item']}", f"{fmt(a)} m²", "Group III", WARN, D["jpn4_groups"]["III"])
        lease_gfa = total + add_back
        if lease.get("max_gfa_m2") is not None:
            v = float(lease["max_gfa_m2"])
            ok = lease_gfa <= v + 1e-6
            add("Lease", "Max GFA", f"{fmt(lease_gfa)} m²", f"≤ {fmt(v)} m²", PASS if ok else FAIL,
                (f"includes {fmt(add_back)} m² of concessions the lease does not exempt; " if add_back else "")
                + ("" if ok else f"over by {fmt(lease_gfa - v)} m²: lease modification + premium"))
            if not ok:
                needs["lease_mod"].append(f"GFA {fmt(lease_gfa)} m² above lease maximum {fmt(v)} m²")
        if lease.get("min_gfa_m2") is not None:
            v = float(lease["min_gfa_m2"])
            ok = total >= v - 1e-6
            add("Lease", "Min GFA (building covenant)", f"{fmt(total)} m²", f"≥ {fmt(v)} m²", PASS if ok else FAIL)
        if lease.get("max_sc_pct") is not None and prop.get("sc_pct") is not None:
            ok = float(prop["sc_pct"]) <= float(lease["max_sc_pct"]) + EPS
            note = "" if ok else ("Discretionary clause: consent + premium (PN 1/2004)" if lease.get("sc_discretion_clause")
                                  else "No discretionary clause: modification (admin fee), then premium (PN 1/2004)")
            add("Lease", "Site coverage", f"{prop['sc_pct']}%", f"≤ {lease['max_sc_pct']}%", PASS if ok else FAIL, note)
            if not ok:
                (needs["consent_premium"] if lease.get("sc_discretion_clause") else needs["lease_mod"]).append("SC above lease")
        if lease.get("max_height_mpd") is not None and prop.get("main_roof_mpd") is not None:
            ok = float(prop["main_roof_mpd"]) <= float(lease["max_height_mpd"]) + EPS
            add("Lease", "Height", f"{prop['main_roof_mpd']} mPD", f"≤ {lease['max_height_mpd']} mPD", PASS if ok else FAIL,
                "" if ok else "Lease modification to remove / relax (JPN 5 p15)")
            if not ok:
                needs["lease_mod"].append("height above lease limit")
        if lease.get("ddh_clause"):
            add("Lease", "DDH clause", "present", "Director's approval of layout", INFO, "No premium for approval (PN 4/2021 App A(I))")
            needs["nil_premium"].append("DDH approval during GBP checking")
        if lease.get("building_covenant_months"):
            add("Lease", "Building covenant", f"{lease['building_covenant_months']} months", "-", INFO,
                "Programme must reach OP and Certificate of Compliance in time; extension carries premium (PN 2/2021)")

    # ---------- Bonus PR (JPN 9)
    b = q.get("bonus_pr")
    if b:
        j = D["jpn9_bonus_pr"]
        rate = j["standard_rates_hkd_per_m2"].get(b.get("district"))
        yr = int(b.get("application_year", 2026))
        checks = [
            (rate is not None, f"district '{b.get('district')}' in the seven designated areas"),
            (area >= j["min_site_m2"], f"site {fmt(area)} m² ≥ {j['min_site_m2']} m²"),
            (b.get("oldest_op_year") is not None and yr - int(b["oldest_op_year"]) >= j["min_building_age_years"],
             f"existing OP ≥ {j['min_building_age_years']} years old"),
            (float(b.get("residential_share", g["domestic"] / total if total else 0)) > j["min_residential_share"],
             "redevelopment > 50% residential GFA"),
        ]
        bad = [t for ok, t in checks if not ok]
        if bad:
            add("JPN 9", "Bonus PR pilot", "not eligible", "all criteria", INFO, "Fails: " + "; ".join(bad))
        else:
            base = float(ozp.get("max_pr_domestic") or 0) * area
            bonus = j["bonus_fraction_of_max_domestic"] * base
            add("JPN 9", "Bonus PR pilot", f"+{fmt(bonus)} m² GFA", "20% of max domestic GFA", PASS,
                f"Bonus value at PN 9/2026 rate {rate:,}/m² = HK${bonus*rate:,.0f}; in situ needs s16 first")

    # ---------- Indicative premium
    pe = q.get("premium_estimate")
    if pe:
        before = float(pe["before_rate_hkd_m2"]) * float(pe.get("before_gfa_m2", lease.get("max_gfa_m2", 0) or 0))
        after = float(pe["after_rate_hkd_m2"]) * lease_gfa
        add("Premium", "Indicative premium (After − Before)", f"HK${after - before:,.0f}", "-", INFO,
            f"After GFA {fmt(lease_gfa)} m² (lease basis). Your own rates; LandsD assesses full market value. Not a valuation.")

    return rows, notes, needs


def programme(needs):
    t, l = D["tpb"], D["lands"]["pn2_2023_weeks"]
    lines = []
    if needs["s12A"]:
        lines.append(f"- **s12A rezoning** first: TPB decision within {t['s12A_decision_months']} months of receipt, "
                     "then plan-making (exhibition, representations, up to 5 months + extensions before CE in C). Budget 12–18 months.")
    if needs["s16"]:
        lines.append(f"- **s16 application**: comments in the first {t['s16_comment_weeks']} weeks; decision within "
                     f"{t['s16_decision_months']} months; notice about {t['decision_notice_weeks']} weeks later. "
                     f"Further information only within {t['fi_window_months']} months. Refusal: s17 review within "
                     f"{t['s17_lodge_days']} days (decided within {t['s17_decision_months']} months), then appeal within "
                     f"{t['appeal_lodge_days']} days. Permission typically valid {t['s16_validity_years']} years to commence.")
    if needs["lease_mod"]:
        lo, hi = D["lands"]["premium_assessment_months"]
        weeks = l["preliminary_reply"] + l["decision_after_reply"] + l["pbto_accept"] + l["bbto_accept"] + l["execution_after_contract"]
        lines.append(f"- **Lease modification / land exchange (PN 2/2023)**, after planning permission: preliminary reply "
                     f"{l['preliminary_reply']} wk, DLC decision / PBTO {l['decision_after_reply']} wk later, premium "
                     f"assessment ~{lo}–{hi} months (2022–24 average), BBTO acceptance {l['bbto_accept']} wk with 10% deposit, "
                     f"execution within {l['execution_after_contract']} wk. About {weeks} weeks + premium time "
                     f"≈ {weeks/4.33 + lo:.0f}–{weeks/4.33 + hi:.0f} months without appeal.")
    if needs["consent_premium"]:
        lines.append(f"- **Approval / consent with premium (PN 4/2021 fast track)**: premium advised within "
                     f"{D['lands']['pn4_2021_fast_track_weeks']} weeks of a valid application, during GBP checking.")
    if needs["nil_premium"]:
        lines.append("- **Nil-premium approvals** handled during GBP checking (PN 4/2021 App A).")
    if not lines:
        lines.append("- No planning application or lease modification identified on the items checked.")
    return lines


def report(p, q, rows, notes, needs):
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    out = [f"# OZP and lease check – {p.get('project', 'Untitled')}", ""]
    route = []
    if needs["s12A"]:
        route.append("s12A rezoning")
    if needs["s16"]:
        route.append("s16 planning permission")
    if needs["lease_mod"]:
        route.append("lease modification with premium")
    if needs["consent_premium"]:
        route.append("lease consent with premium")
    out.append(f"**Result: {fails} fail, {checks} to check, {len(rows)} items. Route: "
               f"{', then '.join(route) if route else 'as of right on the items checked'}.**")
    out += ["", "> Draft for review by an Authorized Person and planning / land consultants. Lease and OZP figures "
            "come from the input; read the actual Notes, ES and lease. Sources and unverified items: "
            "planning/planning-rules.md, lands/lands-rules.md.", "",
            "| Ref | Item | Proposed | Limit | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    out += ["", "## Why each application is needed", ""]
    labels = {"s12A": "s12A", "s16": "s16", "lease_mod": "Lease modification",
              "consent_premium": "Consent with premium", "nil_premium": "Nil-premium approval"}
    any_need = False
    for k, v in needs.items():
        for item in v:
            out.append(f"- {labels[k]}: {item}")
            any_need = True
    if not any_need:
        out.append("- None.")
    out += ["", "## Indicative programme", ""] + programme(needs)
    if notes:
        out += ["", "## Notes", ""] + [f"- {n}" for n in notes]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--block", help="JSON file holding the planning_lease block")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    if a.block:
        q = json.loads(Path(a.block).read_text(encoding="utf-8"))
        q = q.get("planning_lease", q)
    else:
        q = p.get("planning_lease")
    if not q:
        raise SystemExit("No planning_lease block (give it in the project file or with --block)")
    rows, notes, needs = run(p, q)
    md = report(p, q, rows, notes, needs)
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if any(r[4] == FAIL for r in rows) else 0)


if __name__ == "__main__":
    main()
