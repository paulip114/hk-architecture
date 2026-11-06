#!/usr/bin/env python3
"""Barrier-free access checker - Design Manual: Barrier Free Access 2008 (2025 Ed.),
Obligatory Design Requirements (B(P)R reg 72 / Third Schedule work through this Manual).

Usage:  python3 bfa_check.py project.json [-o report.md]   (reads the `barrier_free` block)

`barrier_free` (every key optional except building_type):
  building_type domestic|non_domestic|composite, storeys, height_m, single_family (bool),
  uses[] (Table 2 keys in bfa/bfa2008.json), provided_features[] (tactile_floor_plan, tactile_guide_path,
    visual_display_board, accessible_counter, visual_fire_alarm, assistive_listening),
  car_park {total_spaces, accessible_spaces, bay_width_mm, shared_area_mm},
  access_route {width_mm, steps_or_kerbs (bool)},
  ramps[] {name, gradient (x of 1:x), rise_mm, length_mm, width_mm, landing_mm [l, w], handrails_both_sides, tactile},
  stairs[] {name, tread_mm, riser_mm, external, steps_per_flight, handrails_both_sides},
  handrails[] {name, height_mm, diameter_mm, wall_clear_mm, extension_mm},
  corridors[] {name, width_mm, dead_end_turning (bool)},
  doors[] {name, clear_mm, threshold_mm, handle_mm, force_n, kind exterior|interior|fire, leading_side_mm},
  toilets[] {name, cubicles_per_sex, accessible_per_sex, unisex (bool), size_mm [w, d], seat_mm, basin_rim_mm, flush_mm},
  hotel {guest_rooms, accessible_rooms},
  auditoria[] {name, fixed_seats, wheelchair_spaces, space_mm [w, d], passage_mm},
  lifts[] {name, accessible (bool, default true), car_mm [w, d], door_mm, button_mm [low, high], button_size_mm,
           handrail_mm [low, high], handrail_wall_clear_mm, detection_mm},
  total_passenger_lifts (defaults to the number of lifts listed),
  counters[] {name, height_mm, width_mm, leg_depth_mm, leg_height_mm}
"""
import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = json.loads((HERE.parent / "bfa" / "bfa2008.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"


def rng(v, lo_hi):
    return v is not None and lo_hi[0] <= v <= lo_hi[1]


def run(q):
    rows = []

    def add(ref, item, value, lim, ok, note=""):
        st = ok if isinstance(ok, str) else (PASS if ok else FAIL)
        rows.append((ref, item, value, lim, st, note))

    if q.get("single_family") and q.get("height_m", 99) <= 13:
        add("2.2.1", "Extent", "single-family ≤ 13 m", "exempt", INFO)
        return rows
    bt = q["building_type"]
    if bt in ("domestic", "composite"):
        dom = "all common areas" if q.get("storeys", 0) > 4 else "main entrance, G/F common area, means of access"
        add("Table 1", "Extent (domestic part)", f"{q.get('storeys', '?')} storeys", dom, INFO)
    if bt in ("non_domestic", "composite"):
        add("Table 1", "Extent (non-domestic part)", "-", "all parts except 2.2.2 exempt areas", INFO)

    have = set(q.get("provided_features", []))
    for use in q.get("uses", []):
        for f in M["table_2_uses"][use]:
            add("Table 2 / Div 14", f"{f.replace('_', ' ')} ({use})", "provided" if f in have else "not shown",
                "required", f in have)

    cp = q.get("car_park")
    if cp:
        c = M["carpark"]
        need = next(n for lim, n in c["table"] if lim is None or cp["total_spaces"] <= lim)
        add("Div 3 para 8", "Accessible parking spaces", f"{cp.get('accessible_spaces', 0)} of {cp['total_spaces']}",
            f"≥ {need}", cp.get("accessible_spaces", 0) >= need)
        if cp.get("bay_width_mm") is not None:
            add("Div 3 para 9", "Accessible bay width", f"{cp['bay_width_mm']} mm",
                "≥ 3500 mm (or ≥ 2500 mm beside a ≥ 1200 mm shared area)",
                cp["bay_width_mm"] >= c["bay_width_mm"] or (cp["bay_width_mm"] >= c["bay_beside_shared_mm"]
                                                           and cp.get("shared_area_mm", 0) >= c["shared_area_mm"]))

    ar = q.get("access_route")
    if ar:
        add("Div 4 para 12", "Access route clear width", f"{ar['width_mm']} mm", "≥ 1050 mm", ar["width_mm"] >= 1050)
        if ar.get("steps_or_kerbs"):
            add("Div 4 para 12(2)", "Access route", "steps / kerbs on route", "none (use ramp or lift)", False)

    R = M["ramp"]
    for r in q.get("ramps", []):
        g, rise, ln = r["gradient"], r.get("rise_mm", 0), r.get("length_mm", 0)
        if g >= R["max_gradient"]:
            ok = True
            lim = "≤ 1:12"
        else:
            m = next((x for x in R["minor"] if g >= x["gradient"]), None)
            ok = m is not None and ln <= m["max_length_mm"] and rise <= m["max_rise_mm"]
            lim = "≤ 1:12; 1:10 only if ≤ 1500 long / 150 rise; 1:8 only if ≤ 600 long / 75 rise"
        add("Div 5 para 17", f"{r['name']} gradient", f"1:{g:g}, rise {rise} mm, length {ln} mm", lim, ok)
        if r.get("width_mm") is not None:
            add("Div 5 para 15", f"{r['name']} width", f"{r['width_mm']} mm", "≥ 1050 mm", r["width_mm"] >= R["width_mm"])
        if r.get("landing_mm"):
            add("Div 5 para 16", f"{r['name']} head/foot landing", "×".join(map(str, r["landing_mm"])) + " mm",
                "≥ 1500×1500 mm", min(r["landing_mm"]) >= 1500)
        if g <= R["handrails_from_gradient"] and ln >= 300:
            add("Div 5 para 18", f"{r['name']} handrails both sides + tactile strips",
                "yes" if r.get("handrails_both_sides") and r.get("tactile") else "no", "required (1:20 or steeper)",
                bool(r.get("handrails_both_sides") and r.get("tactile")))
            if ln > R["per_run_m"] * 1000:
                need = math.ceil(ln / (R["per_run_m"] * 1000)) - 1
                add("Div 5 para 18", f"{r['name']} intermediate landings", f"{r.get('intermediate_landings', 0)}",
                    f"≥ {need} (1200 mm long per 10 m run)", r.get("intermediate_landings", 0) >= need)

    S = M["stair"]
    for s in q.get("stairs", []):
        ext = s.get("external")
        t, rz = (S["ext_tread_min_mm"], S["ext_riser_max_mm"]) if ext else (S["tread_min_mm"], S["riser_max_mm"])
        add("Div 7 para 25", f"{s['name']} tread / riser", f"{s['tread_mm']} / {s['riser_mm']} mm",
            f"tread ≥ {t}, riser ≤ {rz} mm", s["tread_mm"] >= t and s["riser_mm"] <= rz)
        if s.get("steps_per_flight"):
            add("Div 7 para 25(c)", f"{s['name']} steps per flight", s["steps_per_flight"], "≤ 16",
                s["steps_per_flight"] <= S["max_steps_per_flight"])
        if "handrails_both_sides" in s:
            add("Div 7 para 25(d)", f"{s['name']} handrails both sides", "yes" if s["handrails_both_sides"] else "no",
                "required", s["handrails_both_sides"])

    H = M["handrail"]
    for h in q.get("handrails", []):
        add("Div 8 para 28", f"{h['name']} height", f"{h['height_mm']} mm", "850-950 mm", rng(h["height_mm"], H["height_mm"]))
        if h.get("diameter_mm") is not None:
            add("Div 8 para 28", f"{h['name']} diameter", f"{h['diameter_mm']} mm", "32-50 mm", rng(h["diameter_mm"], H["diameter_mm"]))
        if h.get("wall_clear_mm") is not None:
            add("Div 8 para 28", f"{h['name']} clear of wall", f"{h['wall_clear_mm']} mm", "30-50 mm", rng(h["wall_clear_mm"], H["wall_clear_mm"]))
        if h.get("extension_mm") is not None:
            add("Div 8 para 28", f"{h['name']} extension past nosing", f"{h['extension_mm']} mm", "≥ 300 mm",
                h["extension_mm"] >= H["extension_mm"])

    for c in q.get("corridors", []):
        add("Div 9 para 31(a)", f"{c['name']} clear width", f"{c['width_mm']} mm", "≥ 1050 mm", c["width_mm"] >= 1050)
        if "dead_end_turning" in c:
            add("Div 9 para 31(b)", f"{c['name']} 1500×1500 turning within 3500 of dead end",
                "yes" if c["dead_end_turning"] else "no", "required", c["dead_end_turning"])

    Dr = M["door"]
    for d in q.get("doors", []):
        add("Div 10 para 38", f"{d['name']} clear width", f"{d['clear_mm']} mm", "≥ 800 mm", d["clear_mm"] >= Dr["clear_mm"])
        if d.get("leading_side_mm") is not None:
            add("Div 10 para 39", f"{d['name']} clear space beside leading edge", f"{d['leading_side_mm']} mm", "≥ 330 mm",
                d["leading_side_mm"] >= Dr["leading_side_mm"])
        if d.get("handle_mm") is not None:
            add("Div 10 para 41", f"{d['name']} handle height", f"{d['handle_mm']} mm", "950-1050 mm", rng(d["handle_mm"], Dr["handle_mm"]))
        if d.get("threshold_mm") is not None:
            add("Div 10 para 42", f"{d['name']} threshold", f"{d['threshold_mm']} mm", "≤ 20 mm, bevelled", d["threshold_mm"] <= Dr["threshold_mm"])
        if d.get("force_n") is not None:
            lim = {"exterior": Dr["force_ext_n"], "fire": Dr["force_fire_n"]}.get(d.get("kind"), Dr["force_int_n"])
            add("Div 10 para 43", f"{d['name']} opening force", f"{d['force_n']} N", f"≤ {lim} N", d["force_n"] <= lim)

    T = M["toilet"]
    for t in q.get("toilets", []):
        if bt == "domestic" or t.get("domestic"):
            add("Div 11 para 46", f"{t['name']}", "domestic", "accessible cubicles not required", INFO)
            continue
        if t.get("cubicles_per_sex") is not None:
            need = T["per_sex_le_20"] if t["cubicles_per_sex"] <= 20 else T["per_sex_gt_20"]
            add("Div 11 para 46", f"{t['name']} accessible cubicles per sex", t.get("accessible_per_sex", 0),
                f"≥ {need} ({t['cubicles_per_sex']} cubicles)", t.get("accessible_per_sex", 0) >= need)
        if "unisex" in t:
            add("Div 11 para 47", f"{t['name']} accessible unisex toilet", "yes" if t["unisex"] else "no",
                "≥ 1 per floor with toilets", t["unisex"])
        if t.get("size_mm"):
            w, dd = sorted(t["size_mm"])
            add("Div 11 para 49", f"{t['name']} cubicle size", f"{w}×{dd} mm", "≥ 1500×1750 mm", w >= 1500 and dd >= 1750)
        if t.get("seat_mm") is not None:
            add("Div 11 para 49", f"{t['name']} WC seat height", f"{t['seat_mm']} mm", "380-450 mm", rng(t["seat_mm"], T["seat_mm"]))
        if t.get("basin_rim_mm") is not None:
            add("Div 11 para 51", f"{t['name']} basin rim", f"{t['basin_rim_mm']} mm", "≤ 750 mm", t["basin_rim_mm"] <= T["basin_rim_max_mm"])
        if t.get("flush_mm") is not None:
            add("Div 11 para 50", f"{t['name']} flush control height", f"{t['flush_mm']} mm", "600-1050 mm", rng(t["flush_mm"], T["flush_mm"]))

    ho = q.get("hotel")
    if ho:
        need = 2 * math.ceil(ho["guest_rooms"] / 100)
        add("Div 2 para 7(2)", "Accessible guest rooms", ho.get("accessible_rooms", 0), f"≥ {need}", ho.get("accessible_rooms", 0) >= need)

    A = M["auditorium"]
    for au in q.get("auditoria", []):
        n = au["fixed_seats"]
        need = A["spaces_le_800"] if n <= 800 else 2 * math.ceil(n / 400)
        add("Div 1 para 4", f"{au['name']} wheelchair spaces", au.get("wheelchair_spaces", 0), f"≥ {need} ({n} seats), in pairs",
            au.get("wheelchair_spaces", 0) >= need)
        if au.get("space_mm"):
            w, dd = sorted(au["space_mm"])
            add("Div 1 para 4", f"{au['name']} space size", f"{w}×{dd} mm", "≥ 800×1300 mm", w >= 800 and dd >= 1300)
        if au.get("passage_mm") is not None:
            add("Div 1 para 4", f"{au['name']} passage to spaces", f"{au['passage_mm']} mm", "≥ 1500 mm", au["passage_mm"] >= 1500)

    L = M["lift"]
    lifts = q.get("lifts", [])
    for lf in lifts:
        accessible = lf.get("accessible", True)
        # para 78(1): paras 79 and 80 apply to every passenger lift; the rest of Div 19 to the accessible lift.
        if accessible and lf.get("car_mm"):
            w, dd = lf["car_mm"]
            add("Div 19 para 78(1)", f"{lf['name']} car internal size", f"{w} wide × {dd} deep mm", "≥ 1100 wide × 1200 deep mm",
                w >= L["car_mm"]["width"] and dd >= L["car_mm"]["depth"])
        if accessible and lf.get("door_mm") is not None:
            add("Div 19 para 78(1)", f"{lf['name']} clear entrance width", f"{lf['door_mm']} mm", "≥ 850 mm", lf["door_mm"] >= L["door_mm"])
        if accessible and lf.get("handrail_mm"):
            lo, hi = lf["handrail_mm"]
            add("Div 19 para 78(1)", f"{lf['name']} handrail height", f"{lo}-{hi} mm", "850-950 mm",
                lo >= L["handrail_mm"][0] and hi <= L["handrail_mm"][1])
        if accessible and lf.get("handrail_wall_clear_mm") is not None:
            v = lf["handrail_wall_clear_mm"]
            add("Div 19 para 78(1)", f"{lf['name']} handrail to wall", f"{v} mm", "30-50 mm",
                L["handrail_wall_clear_mm"][0] <= v <= L["handrail_wall_clear_mm"][1])
        if lf.get("detection_mm") is not None:
            v = lf["detection_mm"]
            add("Div 19 para 79(4)", f"{lf['name']} door detection device height", f"{v} mm", "500-600 mm",
                L["detection_mm"][0] <= v <= L["detection_mm"][1])
        if lf.get("button_mm"):
            lo, hi = lf["button_mm"]
            add("Div 19 para 80(1)", f"{lf['name']} control buttons", f"{lo}-{hi} mm", "900-1200 mm",
                lo >= L["button_mm"][0] and hi <= L["button_mm"][1])
        if lf.get("button_size_mm") is not None:
            add("Div 19 para 80(4)", f"{lf['name']} button size", f"{lf['button_size_mm']} mm", "≥ 20 mm",
                lf["button_size_mm"] >= L["button_size_min_mm"])
    total_lifts = q.get("total_passenger_lifts", len(lifts))
    if total_lifts > L["large_car_if_lifts_over"]:
        def large(lf):
            if not lf.get("car_mm"):
                return False
            short, long_ = sorted(lf["car_mm"])
            return short >= L["large_car_mm"][0] and long_ >= L["large_car_mm"][1] and lf.get("door_mm", 0) >= L["door_mm"]
        have = [lf["name"] for lf in lifts if large(lf)]
        add("Div 19 para 78(2)", "Lift with larger car, more than three lifts", ", ".join(have) or "none",
            "≥ 1 lift of 1500 × 1400 mm, entrance ≥ 850 mm, serving every floor", bool(have),
            "Confirm that it serves every floor")
    C = M["counter"]
    for co in q.get("counters", []):
        if co.get("height_mm") is not None:
            add("Div 15 para 70(2)(a)", f"{co['name']} accessible portion height", f"{co['height_mm']} mm", "≤ 750 mm",
                co["height_mm"] <= C["height_max_mm"])
        if co.get("width_mm") is not None:
            add("Div 15 para 70(2)(a)", f"{co['name']} accessible portion width", f"{co['width_mm']} mm", "≥ 750 mm",
                co["width_mm"] >= C["width_min_mm"])
        if co.get("leg_depth_mm") is not None:
            add("Div 15 para 71(2)", f"{co['name']} leg space depth", f"{co['leg_depth_mm']} mm", "400-600 mm",
                C["leg_depth_mm"][0] <= co["leg_depth_mm"] <= C["leg_depth_mm"][1])
        if co.get("leg_height_mm") is not None:
            add("Div 15 para 71(2)", f"{co['name']} leg space height", f"{co['leg_height_mm']} mm", "≥ 680 mm",
                co["leg_height_mm"] >= C["leg_height_min_mm"])
    return rows


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # default Windows consoles cannot print the reports
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows = run(p["barrier_free"])
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out = [f"# Barrier-free access check – {p.get('project', 'Untitled')}", "",
           f"**Result: {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).", "",
           "> Draft for review by an Authorized Person. Obligatory Design Requirements of the Design Manual: "
           "Barrier Free Access 2008 (2025 Ed.).", "",
           "| Clause | Item | Proposed | Limit | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
