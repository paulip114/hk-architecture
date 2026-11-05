#!/usr/bin/env python3
"""Means of escape checker – Code of Practice for Fire Safety in Buildings 2011 (2024 Ed.), Part B.

Usage:  python3 moe_check.py project.json [-o report.md]

Checks: occupant capacity (Table B1), number and width of exit routes (Table B2,
B8.1 incl. the 50% rule), travel distances (B11.2, B11.3), stair separation
(B10.2, B11.3(b)), single-staircase limits (B6.1), staircase discharge value
(B12, Tables B3/B4), staircase geometry (B14), refuge floors (B18.1),
protected lobbies (B10.4) and basement exits (B17.1).

Draft for review by an Authorized Person. Fire engineering (Part G) and
Part C / Part D requirements are not checked.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
T = json.loads((HERE.parent / "fs-code" / "moe_tables.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"
OF = T["occupancy_factor_m2_per_person"]


def occupants(storey):
    if storey.get("occupants") is not None:
        return int(storey["occupants"]), "given"
    total, parts = 0.0, []
    for a in storey.get("areas", []):
        if "count" in a:  # bedspaces / seats
            total += a["count"]
            parts.append(f"{a['type']} {a['count']}")
            continue
        f = OF.get(a["type"])
        if f is None:
            raise SystemExit(f"Unknown occupancy type '{a['type']}' (see fs-code/moe_tables.json)")
        area = float(a["usable_area_m2"])
        if a["type"] == "8_plant_room" and area <= T["plant_room_zero_if_net_area_le_m2"]:
            parts.append(f"plant {area:g} m² → 0")
            continue
        n = area / f
        total += n
        parts.append(f"{area:g} m² ÷ {f:g}")
    return int(-(-total // 1)), "; ".join(parts)  # round up


def table_b2(n):
    for row in T["table_B2"]:
        if n <= row[0]:
            return row
    return None


def class_key(uc):
    return "1_2" if uc[0] in "12" else ("3" if uc[0] == "3" else "other")


def effective_widths(widths):
    """B8.1(b): width above 150% of the narrowest is not counted."""
    if not widths:
        return 0
    cap = 1.5 * min(widths)
    return sum(min(w, cap) for w in widths)


def discharge_value(width, storeys, sprinkler):
    bands = T["table_B3_width_bands_mm"]
    tab = T["table_B4_sprinkler" if sprinkler else "table_B3_non_sprinkler"]
    add = T["table_B3_B4_each_additional_storey"]

    def at(col):
        if storeys <= 10:
            return tab[storeys - 1][col]
        return tab[9][col] + (storeys - 10) * add[col]

    if width < 1050:
        return 0
    if width <= 1800:
        col = max(i for i, b in enumerate(bands) if width >= b)
        return at(col)
    # Note 1: linear projection above 1800 mm, using the 1700 and 1600 columns
    v1700, v1600 = at(5), at(4)
    return v1700 + (v1700 - v1600) * (width - 1750) / 100


def run(p):
    rows, notes = [], []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    spr = bool(p.get("sprinklered"))
    stairs = p.get("staircases", [])
    storeys = p.get("storeys", [])
    top = p.get("top_floor_level_m")
    n_above = p.get("storeys_above_ground")

    # --- per storey
    occ_above = 0
    occ_basement = 0
    for s in storeys:
        n, how = occupants(s)
        cnt = int(s.get("count", 1))
        lvl = s.get("level", "above")
        if lvl == "above":
            occ_above += n * cnt
        elif lvl == "basement":
            occ_basement += n * cnt
        name = s["name"] + (f" (×{cnt})" if cnt > 1 else "")
        uc = s["use_class"]
        add("B4 / Table B1", f"{name} occupant capacity", f"{n}", "-", INFO, how)

        routes = s.get("exit_routes_mm")
        if routes is not None and n > 3:
            row = table_b2(n)
            if row is None:
                add("Table B2", f"{name} exits", f"{n} persons", "> 3000: BA to determine", WARN)
            else:
                _, need_no, _, need_total, _, need_each = row
                single_ok = len(stairs) == 1 and s.get("single_stair_ok", False)
                if lvl != "basement" and need_no < 2 and not single_ok:
                    need_no = 2  # B8.1: at least 2 exit routes from each storey unless B6.1
                add("B8.1", f"{name} number of exit routes", f"{len(routes)}", f"≥ {need_no}",
                    PASS if len(routes) >= need_no else FAIL)
                eff = effective_widths(routes)
                add("B8.1", f"{name} total exit route width", f"{eff:.0f} mm (counted)", f"≥ {need_total} mm",
                    PASS if eff >= need_total else FAIL,
                    "width above 1.5 × narrowest not counted" if eff < sum(routes) else "")
                narrow = min(routes)
                add("B8.1", f"{name} narrowest exit route", f"{narrow} mm", f"≥ {need_each} mm",
                    PASS if narrow >= need_each else FAIL)

        ck = class_key(uc)
        bal = s.get("balcony_approach", False)
        if s.get("max_travel_m") is not None:
            k = ck + ("_balcony" if bal else "")
            lim = T["travel_distance_m"]["max_two_exits"][k]
            what = "flat/room exit door to nearest stair" if ck == "1_2" else "to nearest protected exit"
            add("B11.3(a)", f"{name} max travel distance", f"{s['max_travel_m']} m", f"≤ {lim} m ({what})",
                PASS if s["max_travel_m"] <= lim else FAIL)
        if s.get("max_deadend_m") is not None:
            if ck == "1_2":
                lim = T["travel_distance_m"]["deadend"]["1_2_flat_door_to_stair"]
                what = "flat/guestroom door to stair or point of choice"
            else:
                lim = T["travel_distance_m"]["deadend"][ck + ("_balcony" if bal else "")]
                what = "to protected exit or point of choice"
            add("B11.2", f"{name} deadend travel", f"{s['max_deadend_m']} m", f"≤ {lim} m ({what})",
                PASS if s["max_deadend_m"] <= lim else FAIL)
        if s.get("max_within_flat_m") is not None:
            lim = T["travel_distance_m"]["deadend"]["1_2_within_flat"]
            add("B11.2(a)(i)", f"{name} within flat to flat door", f"{s['max_within_flat_m']} m", f"≤ {lim} m",
                PASS if s["max_within_flat_m"] <= lim else FAIL)
        if s.get("stair_door_separation_m") is not None:
            lim = T["travel_distance_m"]["min_between_stair_doors"]
            add("B10.2(b)", f"{name} distance between stair doors", f"{s['stair_door_separation_m']} m",
                f"≥ {lim} m", PASS if s["stair_door_separation_m"] >= lim else FAIL)
        if s.get("max_stair_to_stair_m") is not None:
            lim = T["travel_distance_m"]["max_between_stairs"]
            add("B11.3(b)", f"{name} stair to stair along exit route", f"{s['max_stair_to_stair_m']} m",
                f"≤ {lim} m", PASS if s["max_stair_to_stair_m"] <= lim else FAIL)

        if lvl == "basement" and routes is not None and len(routes) < 2:
            ex = s.get("basement_exemption", {})
            ok = ex.get("depth_m", 99) <= 3 and ex.get("area_m2", 1e9) <= 150 and ex.get("lavatory_or_plant_only")
            add("B17.1", f"{name} basement exits", f"{len(routes)}", "≥ 2 unless ≤ 3 m deep, ≤ 150 m², lavatory/plant only",
                PASS if ok else FAIL)

    # --- single staircase (B6.1)
    above_stairs = [st for st in stairs if st.get("serves", "above") == "above"]
    if len(above_stairs) == 1:
        s6 = p.get("single_stair", {})
        lim_ufa = T["single_stair"]["ufa_limit_top_le_13m"] if (top or 0) <= 13 else T["single_stair"]["ufa_limit_top_gt_13m"]
        ok = ((n_above or 99) <= 6 and (top or 99) <= 17 and s6.get("max_storey_ufa_m2", 1e9) <= lim_ufa
              and s6.get("domestic_or_office_only", False))
        add("B6.1", "Single required staircase", f"{n_above} storeys, top floor {top} m, UFA {s6.get('max_storey_ufa_m2')} m²",
            f"≤ 6 storeys, ≤ 17 m, UFA ≤ {lim_ufa} m², domestic/office (shop or car park at G/F)", PASS if ok else FAIL,
            "Above 13 m also needs protected lobby, stair to roof, roof refuge 0.5 m²/person" if (top or 0) > 13 else "")

    # --- discharge value (B12)
    def total_dv(kind):
        tot, parts = 0.0, []
        for st in stairs:
            if st.get("serves", "above") != kind:
                continue
            dv = discharge_value(st["width_mm"], st["storeys_served"], spr)
            if st.get("upward"):
                dv *= T["discharge_factor_upward"]
            if st.get("scissors"):
                dv *= T["discharge_factor_scissors_no_landing"]
            tot += dv
            parts.append(f"{st['name']} {st['width_mm']} mm / {st['storeys_served']} storeys = {dv:.0f}")
        return tot, parts

    if occ_above:
        dv, parts = total_dv("above")
        add("B12.1", "Stair discharge value – storeys above G/F", f"{dv:.0f}", f"≥ {occ_above} persons",
            PASS if dv >= occ_above else FAIL, ("Table B4 (sprinklered)" if spr else "Table B3") + "; " + "; ".join(parts))
    if occ_basement:
        dv, parts = total_dv("basement")
        add("B12.2", "Stair discharge value – basements", f"{dv:.0f}", f"≥ {occ_basement} persons",
            PASS if dv >= occ_basement else FAIL, "; ".join(parts))

    # --- stair geometry (B14)
    sg = T["staircase"]
    for st in stairs:
        w = st["width_mm"]
        if w > sg["max_width_mm"] and not st.get("central_handrail"):
            add("B14.5", f"{st['name']} width", f"{w} mm", "≤ 1800 mm or divided by central handrail", FAIL)
        if st.get("tread_mm") is not None:
            uc = st.get("use_class", "")
            mt = sg["5a_min_tread_mm"] if uc == "5a" else sg["5b_min_tread_mm"] if uc == "5b" else sg["min_tread_mm"]
            mr = sg["5a_max_riser_mm"] if uc in ("5a",) else sg["5b_max_riser_mm"] if uc == "5b" else sg["max_riser_mm"]
            add("B14.2", f"{st['name']} tread", f"{st['tread_mm']} mm", f"≥ {mt} mm", PASS if st["tread_mm"] >= mt else FAIL)
            add("B14.2", f"{st['name']} riser", f"{st['riser_mm']} mm", f"≤ {mr} mm", PASS if st["riser_mm"] <= mr else FAIL)
        if st.get("risers_per_flight") is not None:
            r = st["risers_per_flight"]
            add("B14.2", f"{st['name']} risers per flight", f"{r}", "2 to 16", PASS if 2 <= r <= 16 else FAIL)

    # --- protected lobby (B10.4(b))
    if top is not None and len(above_stairs) >= 2 and top > T["protected_lobby_exempt_top_floor_m"]["two_plus_stairs"]:
        unl = [st["name"] for st in above_stairs
               if not (st.get("protected_lobby") or st.get("pressurised") or st.get("ventilated"))]
        add("B10.4(b)", "Protected lobby to each required staircase", "missing: " + ", ".join(unl) if unl else "provided",
            "needed (top floor > 20 m) unless pressurised or ventilated", FAIL if unl else PASS)

    # --- refuge floors (B18.1)
    if n_above:
        if n_above > T["refuge_floor"]["trigger_storeys"]:
            interval = T["refuge_floor"]["interval_storeys_class6"] if p.get("industrial") else T["refuge_floor"]["interval_storeys_other"]
            rf = sorted(p.get("refuge_floors", []))
            levels = [0] + rf + ([] if p.get("roof_as_refuge") else [])
            gaps = [b - a for a, b in zip(levels, levels[1:])] + [n_above - levels[-1]]
            worst = max(gaps)
            add("B18.1", "Refuge floors", f"at storeys {rf or 'none'}; largest gap {worst}",
                f"≤ {interval} storeys between refuge floors / from ground", PASS if worst <= interval else FAIL,
                "Storeys solely for plant may be excluded; main roof may count if B18.3 is met")
        else:
            add("B18.1", "Refuge floors", f"{n_above} storeys", "not required (≤ 25 storeys)", PASS)

    return rows, notes


def report(p, rows, notes):
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out = [f"# Means of escape check – {p.get('project', 'Untitled')}", "",
           f"**Result: the scheme {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).", "",
           "> Draft for review and signature by an Authorized Person. Based on the Code of Practice for Fire Safety in "
           "Buildings 2011 (2024 Edition), Part B. Parts C, D, E and fire engineering are not checked.", "",
           "| Clause | Item | Proposed | Limit | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    if notes:
        out += ["", "## Notes", ""] + [f"- {n}" for n in notes]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    p = p.get("means_of_escape", p)
    rows, notes = run(p)
    md = report(p, rows, notes)
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if any(r[4] == FAIL for r in rows) else 0)


if __name__ == "__main__":
    main()
