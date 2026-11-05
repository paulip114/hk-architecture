#!/usr/bin/env python3
"""Fire resisting construction (Part C) and means of access (Part D) checker.
Code of Practice for Fire Safety in Buildings 2011 (2024 Edition).

Usage:  python3 fire_cd_check.py project.json [-o report.md]
Reads the `fire_construction` and `means_of_access` blocks of the project file.

Part C: compartment size and FRR (Table C1), separation of use classes (C7),
liftwells (C9.1), special hazards and kitchens (C13), basements (C14),
spandrels (C11), boundary and same-site separation (C5), staircase external
walls (C9.7), voids and atria (C10), compartment door insulation (C8.1).
Part D: number of access staircases, fireman's lifts and firefighting and
rescue stairways (Table D1), fireman's lift and FRS dimensions (D7-D19),
and emergency vehicular access (D22-D23).

Draft for review by an Authorized Person.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
T = json.loads((HERE.parent / "fs-code" / "cd_tables.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"


def c1(uc, area, volume=None):
    """Return (required FRR, within-limit bool, limit text) from Table C1."""
    key = uc if uc in T["table_C1"] else uc[0]
    rows = T["table_C1"].get(key)
    if rows is None:
        return None, None, "BA to determine (Note 4)"
    for max_a, frr in rows:
        if max_a is None or area <= max_a:
            ok = True
            vlim = T["table_C1_volume_limits_m3"].get(key)
            if vlim and volume is not None and volume > vlim:
                ok = False
            lim = "not limited" if max_a is None else f"≤ {max_a:,} m²"
            if vlim:
                lim += f" and ≤ {vlim:,} m³"
            return frr, ok, lim
    return rows[-1][1], False, f"≤ {rows[-1][0]:,} m²"


def part_c(p, add):
    fc = p.get("fire_construction")
    if not fc:
        return
    spr = fc.get("sprinklered", False)
    use_frr = {}
    for c in fc.get("compartments", []):
        uc = c["use_class"]
        frr, ok, lim = c1(uc, c["area_m2"], c.get("volume_m3"))
        use_frr[uc] = max(use_frr.get(uc, 0), frr or 0)
        name = c["name"]
        add("C3.1 / Table C1", f"{name} compartment size", f"{c['area_m2']:,} m²" +
            (f", {c['volume_m3']:,} m³" if c.get("volume_m3") else ""), lim,
            PASS if ok else WARN,
            "" if ok else "exceeds Table C1: BA on individual merits, enhanced provisions needed")
        if frr is not None and c.get("frr_min") is not None:
            need = frr
            if c.get("basement"):
                need = max(need, T["basement"]["elements_frr"])
            add("C4.1", f"{name} FRR of elements and fire barriers", f"{c['frr_min']} min", f"≥ {need} min",
                PASS if c["frr_min"] >= need else FAIL, "basement: 240/240/240 (C14.1)" if c.get("basement") else "")
        if c.get("openings_fraction_of_wall") is not None and c["openings_fraction_of_wall"] > T["compartment_door_insulation_if_openings_gt_fraction"]:
            ins = c.get("door_insulation_min", 0)
            need = 30 if c.get("sprinklers_both_sides") else (frr or 0)
            add("C8.1", f"{name} compartment door/shutter insulation", f"{ins} min",
                f"≥ {need} min (openings > 25% of wall)", PASS if ins >= need else FAIL)

    if len(use_frr) > 1:
        need = max(use_frr.values())
        prov = fc.get("use_separation_frr_min")
        add("C7.1", "Separation between use classifications " + ", ".join(sorted(use_frr)),
            f"{prov} min" if prov is not None else "not stated", f"≥ {need} min (longer FRR)",
            (PASS if prov >= need else FAIL) if prov is not None else WARN,
            "Not needed between 4a occupancies or 4b retail shops within Table C1 limits (C7.3)")

    if fc.get("liftwell_frr_min") is not None:
        v = fc["liftwell_frr_min"]
        add("C9.1(a)", "Liftwell fire barriers", f"{v} min", "≥ 120/120/120", PASS if v >= 120 else FAIL,
            "Lift doors -/120/-; smoke seal lobby at basement if lift also serves upper floors")

    for h in fc.get("special_hazards", []):
        need = T["special_hazard_to_protected_exit_frr"] if h.get("opens_to_protected_exit") else T["special_hazard_frr"]
        add("C13.1", f"Special hazard: {h['name']}", f"{h.get('frr_min')} min", f"≥ -/{need}/{need}",
            PASS if (h.get("frr_min") or 0) >= need else FAIL)

    for k in fc.get("restaurant_kitchens", []):
        add("C13.2(a)", f"Restaurant kitchen {k['name']} enclosure", f"{k.get('frr_min')} min", "≥ -/60/60",
            PASS if (k.get("frr_min") or 0) >= 60 else FAIL)
        if k.get("ufa_m2", 0) > T["restaurant_kitchen_lobby_ufa_m2"] or k.get("opens_to_building_exit_route"):
            add("C13.2(b)", f"Restaurant kitchen {k['name']} protected lobby", "yes" if k.get("protected_lobby") else "no",
                "required (UFA > 45 m² onto dining exit route, or onto building exit route)",
                PASS if k.get("protected_lobby") else FAIL)

    ok_ = fc.get("open_kitchen_flats")
    if ok_:
        need = ["smoke detector in flat", "smoke detector at common area", "sprinkler over notional kitchen",
                "600 mm -/30/30 wall by flat door"]
        miss = [x for x in need if x not in ok_.get("provisions", [])]
        add("C13.4", "Open kitchen in flats", "missing: " + "; ".join(miss) if miss else "all provided",
            "4 provisions (5 with internal stair: 450 mm downstand)", FAIL if miss else PASS)

    b = fc.get("basement")
    if b:
        if b.get("barrier_to_ground_frr_min") is not None:
            v = b["barrier_to_ground_frr_min"]
            add("C14.1(a)", "Basement / ground storey fire barrier", f"{v} min", "≥ -/240/240", PASS if v >= 240 else FAIL)
        if b.get("floor_area_m2") and b.get("smoke_outlet_area_m2") is not None:
            frac = T["basement"]["smoke_outlet_area_fraction_storage" if b.get("storage") else "smoke_outlet_area_fraction"]
            need = frac * b["floor_area_m2"]
            add("C14.2(d)", "Basement smoke outlets area", f"{b['smoke_outlet_area_m2']} m²", f"≥ {need:.2f} m² ({frac*100:g}%)",
                PASS if b["smoke_outlet_area_m2"] >= need else FAIL, "if enclosed on four sides")
        if b.get("smoke_outlet_max_spacing_m") is not None:
            v = b["smoke_outlet_max_spacing_m"]
            add("C14.2(a)", "Basement smoke outlet spacing", f"{v} m", "≤ 30 m", PASS if v <= 30 else FAIL)
        if b.get("smoke_outlet_min_dim_m") is not None:
            v = b["smoke_outlet_min_dim_m"]
            add("C14.2(e)", "Basement smoke outlet least dimension", f"{v} m", "≥ 1 m", PASS if v >= 1 else FAIL)

    if not spr and not fc.get("single_family_house"):
        e = fc.get("external_wall", {})
        sp, pr = e.get("spandrel_m", 0), e.get("projection_m", 0)
        ok = sp >= T["spandrel_m"] or pr >= T["horizontal_projection_m"]
        add("C11.1", "Spandrel / projection between floors", f"spandrel {sp} m, projection {pr} m",
            "900 mm spandrel or 500 mm projection, FRR of storey", PASS if ok else FAIL)
    else:
        add("C11.1", "Spandrel / projection between floors", "sprinklered" if spr else "single family house",
            "not required", PASS)

    for s in fc.get("boundary_walls", []):
        d = s["distance_to_boundary_m"]
        if d <= T["boundary_fire_wall_within_m"]:
            ok = s.get("frr_equal_internal") and s.get("openings_min_distance_m", 99) >= T["boundary_opening_min_m"]
            add("C5.3", f"{s['name']} wall {d} m from boundary", "FRR & openings as stated",
                "FRR = internal elements, imperforate; openings ≥ 450 mm from boundary with FR fixed lights",
                PASS if ok else FAIL)

    for s in fc.get("stair_external_walls", []):
        if s["distance_to_exposure_m"] < T["stair_external_wall_exposure_m"]:
            fl = s.get("fixed_light_fraction", 0)
            ok = s.get("fire_rated") and fl <= T["stair_fixed_light_max_fraction"] and not s.get("unprotected_openings")
            add("C9.7", f"{s['name']} external wall within 6 m of exposure", f"fixed lights {fl*100:.0f}%",
                "FRR of stair wall, imperforate or FR fixed lights ≤ 25%", PASS if ok else FAIL)

    for v in fc.get("floor_voids", []):
        if spr:
            ok = v.get("downstand_mm", 0) >= T["void_downstand_mm"] or v.get("smoke_curtain")
            add("C10.1", f"Void {v['name']}", f"downstand {v.get('downstand_mm', 0)} mm", "≥ 450 mm -/30/- or smoke curtain",
                PASS if ok else FAIL)
        else:
            add("C10.1", f"Void {v['name']}", "non-sprinklered", "unprotected floor openings only allowed when sprinklered", FAIL)

    for a in fc.get("atria", []):
        at = T["atrium"]
        ok = spr and a["volume_m3"] <= at["max_volume_m3"] and a["height_m"] <= at["max_height_m"] and a["floors"] <= at["max_floors"]
        add("C10.3", f"Atrium {a['name']}", f"{a['volume_m3']:,} m³, {a['height_m']} m, {a['floors']} floors",
            "sprinklered, ≤ 28,000 m³, ≤ 15 m, ≤ 3 floors, separated", PASS if ok else FAIL)


def d1_required(m):
    """Return (fireman_lift, frs, row) from Table D1."""
    kind = m["building_kind"]  # single_family | small_dom_office | domestic | non_domestic | special | industrial
    h = m.get("height_above_lowest_street_m", 0)
    n = m.get("storeys", 1)
    vol = m.get("cubical_extent_m3", 0)
    fl = frs = False
    row = ""
    if n <= 1:
        return False, False, "(1) ≤ 1 storey"
    if kind == "single_family":
        return False, False, "(2)"
    if kind == "small_dom_office":
        return False, False, "(3) one access staircase"
    if kind == "domestic":
        fl = n > 2 and h > 30
        row = "(4)(b)" if fl else "(4)(a)"
    elif kind == "non_domestic":
        fl = n > 2 and (h > 30 or (h > 15 and vol > 7000))
        row = "(5)(c)/(d)" if fl else "(5)(a)/(b)"
    elif kind == "special":  # 5a, hotels, hospitals
        fl = n > 2
        row = "(6)(b)" if fl else "(6)(a)"
    elif kind == "industrial":
        if h > 30 or vol > 7000:
            fl = frs = True
            row = "(7)(b)-(d)"
        else:
            fl = n > 2
            row = "(7)(a)"
    return fl, frs, row


def part_d(p, add):
    m = p.get("means_of_access")
    if not m:
        return
    parts = m.get("parts", [m])
    need_fl = need_frs = False
    rows = []
    for part in parts:
        a, b, r = d1_required(part)
        need_fl |= a
        need_frs |= b
        rows.append(f"{part.get('name', part['building_kind'])} {r}")
    bm = m.get("basement")
    if bm and bm.get("cubical_extent_m3", 0) > 7000 and (bm.get("storeys", 0) > 2 or bm.get("depth_m", 0) > 9):
        need_fl = need_frs = True
        rows.append("basement (8)")
    add("Table D1", "Fireman's lift required", "yes" if need_fl else "no", "; ".join(rows), INFO)
    add("Table D1", "Firefighting and rescue stairway required", "yes" if need_frs else "no", "", INFO)
    prov_fl = m.get("firemans_lifts", 0)
    prov_frs = m.get("frs", 0)
    if need_fl:
        add("B(P)R 41B / D8", "Fireman's lifts provided", f"{prov_fl}", "≥ 1, every part within 60 m of lift lobby",
            PASS if prov_fl >= 1 else FAIL)
    if need_frs:
        add("B(P)R 41C / D15", "Firefighting and rescue stairways", f"{prov_frs}", "≥ 1, every part within 60 m",
            PASS if prov_frs >= 1 else FAIL)
    add("B(P)R 41A / D4", "Access staircases", "required staircases", "as many as escape staircases", INFO)

    F = T["fireman_lift"]
    if (need_fl or need_frs) and m.get("max_distance_to_lobby_m") is not None:
        v = m["max_distance_to_lobby_m"]
        lim = F["max_distance_m"] if m.get("layout_known", True) else F["design_direct_line_m"]
        add("D8.4 / D15.6", "Furthest point to fireman's lift / FRS lobby", f"{v} m",
            f"≤ {lim} m ({'actual passage' if lim == 60 else 'direct line, layout unknown'})", PASS if v <= lim else FAIL)
    if m.get("fsap_distance_m") is not None:
        v = m["fsap_distance_m"]
        add("D7.2 / D14.2", "Fire service access point to lift / stair", f"{v} m", "≤ 18 m", PASS if v <= 18 else FAIL)
    if m.get("fsap_passage_width_mm") is not None:
        v = m["fsap_passage_width_mm"]
        add("D7.3 / D14.4", "Passage from fire service access point", f"{v} mm", "≥ 1500 mm wide, 2000 mm headroom",
            PASS if v >= 1500 else FAIL)
    car = m.get("lift_car")
    if car:
        ok = car["min_dim_m"] >= F["car_min_dim_m"] and car["area_m2"] >= F["car_min_area_m2"] and car["load_kg"] >= F["car_min_load_kg"]
        add("D10.1", "Fireman's lift car", f"{car['min_dim_m']} m, {car['area_m2']} m², {car['load_kg']} kg",
            "≥ 1.1 m, ≥ 1.35 m², ≥ 680 kg", PASS if ok else FAIL)
    if m.get("lift_door_mm"):
        w, h = m["lift_door_mm"]
        add("D12.1", "Fireman's lift door", f"{w} × {h} mm", "≥ 800 × 2000 mm", PASS if w >= 800 and h >= 2000 else FAIL)
    lob = m.get("fl_lobby")
    if lob:
        ok = lob["area_m2"] >= F["lobby_min_area_m2"] and lob["min_dim_m"] >= F["lobby_min_dim_m"]
        add("D11.1", "Fireman's lift lobby", f"{lob['area_m2']} m², min {lob['min_dim_m']} m", "≥ 2.25 m², ≥ 1.5 m",
            PASS if ok else FAIL)
    fl_ = m.get("frs_lobby")
    if fl_:
        R = T["frs"]
        ok = R["lobby_area_m2"][0] <= fl_["area_m2"] <= R["lobby_area_m2"][1] and fl_["min_dim_m"] >= R["lobby_min_dim_m"]
        add("D16.1(a)", "FRS lobby size", f"{fl_['area_m2']} m², min {fl_['min_dim_m']} m", "5–10 m², ≥ 1.5 m", PASS if ok else FAIL)
        if fl_.get("vent_area_m2") is not None and not fl_.get("pressurised"):
            need = R["lobby_vent_fraction"] * fl_["area_m2"]
            add("D16.1(c)", "FRS lobby natural ventilation", f"{fl_['vent_area_m2']} m²", f"≥ {need:.2f} m² (25%), top ≥ 1.9 m, on external wall",
                PASS if fl_["vent_area_m2"] >= need else FAIL)

    e = m.get("eva")
    if e:
        E = T["eva"]
        virgin = e.get("site") == "virgin"
        cls6 = e.get("industrial")
        if virgin:
            need = E["virgin_carriageway_width_m"] if e.get("carriageway", True) else E["virgin_non_carriageway_width_m"]
            if cls6:
                need = E["class6_two_way_no_divider_m"]
        else:
            need = E["redevelopment_class6_width_m"] if cls6 else E["redevelopment_width_m"]
        add("D22.2(a) / D23.3", "EVA width", f"{e['width_m']} m", f"≥ {need} m ({'virgin' if virgin else 'redevelopment'} site)",
            PASS if e["width_m"] >= need else FAIL)
        if e.get("headroom_m") is not None:
            add("D22.2(b)", "EVA headroom", f"{e['headroom_m']} m", "≥ 4.5 m", PASS if e["headroom_m"] >= 4.5 else FAIL)
        if e.get("gradient") is not None:
            lim = E["max_gradient"]
            add("D22.2(c)", "EVA gradient (serving major facade)", f"1:{1/e['gradient']:.1f}", "≤ 1:10",
                PASS if e["gradient"] <= lim + 1e-9 else FAIL)
        if e.get("facade_served_fraction") is not None:
            v = e["facade_served_fraction"]
            add("D22.2(e)", "Facade length served (within 10 m of EVA)", f"{v*100:.0f}% of perimeter", "≥ 25% incl. the major facade",
                PASS if v >= E["facade_fraction"] else FAIL, "two opposite facades for Use Class 6 on virgin sites" if cls6 else "")
        if e.get("deadend") and not e.get("turning_space"):
            add("D22.2(d)", "Turning space at deadend EVA", "none", "required (26 m turning circle, 12 m vehicle)", FAIL)
        if e.get("not_normally_used") and not e.get("crash_gate"):
            add("D22.4", "Emergency crash gate", "none", "required where EVA not normally used by vehicles", FAIL)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    part_c(p, add)
    part_d(p, add)
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out = [f"# Fire resisting construction and means of access – {p.get('project', 'Untitled')}", "",
           f"**Result: the scheme {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).", "",
           "> Draft for review and signature by an Authorized Person. Code of Practice for Fire Safety in Buildings 2011 "
           "(2024 Edition), Parts C and D. FSI requirements (FSD) and fire engineering (Part G) are not checked.", "",
           "| Clause | Item | Proposed | Limit | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
