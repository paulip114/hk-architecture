#!/usr/bin/env python3
"""Places of public entertainment (Use Classification 5a) checker.
FS Code 2011 (2024 Ed.) Part B Section 3 (B19-B28) and Part C Subsection C18.

Usage:  python3 ppe_check.py project.json [-o report.md]   (reads the `ppe` block)

Checks: B19.2 small-premises exemption, B20 thoroughfares, B21 exits (Table B2
below 12 m / Table B5 at 12 m or more), tier gradient and headroom, B23
staircases, B27.6 seat rows (Table B6) and gangways (Table B7), B27.8 / B27.3
foyer, B27.2 / B27.3 cinemas in multi-storey buildings and basements, C18
cinema and theatre fire separation.
Draft for review by an Authorized Person.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOE = json.loads((HERE.parent / "fs-code" / "moe_tables.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"

TABLE_B5 = [(200, 2, 2400), (300, 2, 2600), (500, 2, 4300), (750, 3, 6400), (1000, 4, 8500),
            (1250, 5, 10400), (1500, 6, 12500), (1750, 7, 14600), (2000, 8, 16700),
            (2500, 10, 20800), (3000, 12, 24900)]
# Table B6: (min seatway mm, max seats one side, max seats two sides); >= 500 mm limited by 12 m / 24 m row length
TABLE_B6 = [(300, 7, 14), (325, 8, 15), (350, 9, 18), (375, 10, 20), (400, 11, 22),
            (425, 12, 24), (450, 12, 26), (475, 12, 28), (500, None, None)]
TABLE_B7 = [(500, 1100), (1000, 1200), (1500, 1350), (10 ** 9, 1500)]


def b2(n):
    for row in MOE["table_B2"]:
        if n <= row[0]:
            return row[1], row[3], row[5]
    return None


def b5(n):
    for mx, no, w in TABLE_B5:
        if n <= mx:
            return no, w, 1050
    return None


def run(q):
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    occ = int(q["occupant_capacity"])
    seats = q.get("seats", 0)
    add("B21.5", "Occupant capacity (incl. standing, waiting, foyer, café)", f"{occ}", "-", INFO)

    if occ <= 50 and q.get("building_total_small_ppe", occ) <= 150 and not q.get("basement"):
        add("B19.2", "Small premises exemption", f"{occ} persons", "≤ 50 (≤ 150 total in building), not basement",
            PASS, "Section 3 does not apply; may share exits with other non-domestic uses")

    # B20 thoroughfares
    th = sorted(q.get("thoroughfares_m", []), reverse=True)
    if th:
        if occ <= 500:
            if len(th) == 1:
                ok = q.get("single_thoroughfare_is_eva_and_fsd_ok", False)
                add("B20.9", "Single thoroughfare", f"{th[0]} m", "acceptable EVA, no FSD objection (≤ 500 persons)",
                    PASS if ok else WARN)
            else:
                add("B20.8", "Widest thoroughfare", f"{th[0]} m", "≥ 7.3 m", PASS if th[0] >= 7.3 else FAIL)
        elif occ <= 2000:
            add("B20.4", "Widest thoroughfare", f"{th[0]} m", "≥ 12 m", PASS if th[0] >= 12 else FAIL)
        elif occ <= 3000:
            second = th[1] if len(th) > 1 else 0
            need2 = 6 if q.get("second_is_footway") else 9
            ok = th[0] >= 12 and second >= need2
            add("B20.5", "Thoroughfares", f"{th[0]} m + {second} m", f"≥ 12 m and ≥ {need2} m", PASS if ok else FAIL)
        elif occ <= 5000:
            second = th[1] if len(th) > 1 else 0
            ok = th[0] >= 15 and second >= 9
            add("B20.6", "Thoroughfares", f"{th[0]} m + {second} m", "≥ 15 m and ≥ 9 m", PASS if ok else FAIL)
        else:
            add("B20.7", "Thoroughfares", "-", "further frontage as BA requires", WARN)
        if len(th) < 2 and occ > 500:
            add("B20.1", "Number of thoroughfares", f"{len(th)}", "≥ 2", FAIL)
    if q.get("frontage_fraction") is not None:
        v = q["frontage_fraction"]
        add("B20.2", "Frontage to thoroughfares", f"{v*100:.0f}% of perimeter", "≥ 50%", PASS if v >= 0.5 else FAIL)

    # B21 exits
    routes = q.get("exit_routes_mm")
    if routes is not None:
        high = q.get("floor_level_m", 0) >= 12
        req = b5(occ) if high else b2(occ)
        tab = "Table B5 (≥ 12 m)" if high else "Table B2 (< 12 m)"
        if req is None:
            add("B21.1", "Exits", f"{occ} persons", "> 3000: BA to determine", WARN)
        else:
            no, tot, each = req
            no = max(no, 2)
            add("B21.1", f"Number of exits – {tab}", f"{len(routes)}", f"≥ {no}", PASS if len(routes) >= no else FAIL)
            cap = 1.5 * min(routes)
            eff = sum(min(w, cap) for w in routes)
            add("B21.1", f"Total exit width – {tab}", f"{eff:.0f} mm", f"≥ {tot} mm", PASS if eff >= tot else FAIL)
            add("B21.1", "Narrowest exit", f"{min(routes)} mm", f"≥ {each} mm", PASS if min(routes) >= each else FAIL)
        if q.get("exits_to_different_thoroughfares") is not None:
            add("B21.3", "Two exits open into different thoroughfares", "yes" if q["exits_to_different_thoroughfares"] else "no",
                "required", PASS if q["exits_to_different_thoroughfares"] else FAIL)
    if q.get("tier_gradient_deg") is not None:
        v = q["tier_gradient_deg"]
        add("B21.4", "Tier gradient", f"{v}°", "≤ 35°", PASS if v <= 35 else FAIL)
    if q.get("min_headroom_m") is not None:
        v = q["min_headroom_m"]
        add("B21.4", "Headroom over tiers / floor", f"{v} m", "≥ 3 m", PASS if v >= 3 else FAIL)

    # B23 stairs
    for st in q.get("staircases", []):
        n = st["name"]
        if st.get("tread_mm") is not None:
            add("B23.1(e)", f"{n} tread / riser", f"{st['tread_mm']} / {st['riser_mm']} mm", "≥ 280 / ≤ 150 mm",
                PASS if st["tread_mm"] >= 280 and st["riser_mm"] <= 150 else FAIL)
        if st.get("max_steps_per_flight") is not None:
            v = st["max_steps_per_flight"]
            add("B23.1(b)", f"{n} steps per flight", f"{st.get('min_steps_per_flight', v)}–{v}", "3 to 16",
                PASS if 3 <= st.get("min_steps_per_flight", v) and v <= 16 else FAIL)
            if v > 12 and not st.get("turn_between_flights"):
                add("B23.1(d)", f"{n} turn between flights", "no", "required where a flight has > 12 steps", FAIL)
        if st.get("successive_flights_without_turn") is not None:
            v = st["successive_flights_without_turn"]
            add("B23.1(c)", f"{n} successive flights without a turn", f"{v}", "≤ 2", PASS if v <= 2 else FAIL)

    # B27.6 seating
    for r in q.get("seat_rows", []):
        sw, n_seats, both = r["seatway_mm"], r["seats"], r.get("gangway_both_sides", True)
        maxlen = 24 if both else 12
        lim = None
        for mn, one, two in TABLE_B6:
            if sw >= mn:
                lim = two if both else one
        if sw < 300:
            add("B27.6(b)", f"Row {r['name']} seatway", f"{sw} mm", "≥ 300 mm", FAIL)
            continue
        if lim is not None:
            add("Table B6", f"Row {r['name']} seats ({'gangways both sides' if both else 'one side'})",
                f"{n_seats} seats, seatway {sw} mm", f"≤ {lim}", PASS if n_seats <= lim else FAIL)
        if r.get("length_m") is not None:
            add("B27.6(a)", f"Row {r['name']} length", f"{r['length_m']} m", f"≤ {maxlen} m",
                PASS if r["length_m"] <= maxlen else FAIL)
    for g in q.get("gangways", []):
        need = next(w for mx, w in TABLE_B7 if g["persons_served"] <= mx)
        add("Table B7", f"Gangway {g['name']}", f"{g['width_mm']} mm for {g['persons_served']} persons", f"≥ {need} mm",
            PASS if g["width_mm"] >= need else FAIL)

    # foyer
    if seats and q.get("foyer_m2") is not None:
        if q.get("basement"):
            need = 0.5 * seats / 3
            ref, note = "B27.3(f)", "basement cinema: foyer on G/F, 1 in 3 seats"
        else:
            need = 0.5 * seats / 6
            ref, note = "B27.8 / B(P)R 49E", "1 in 6 seats at 0.5 m²"
        add(ref, "Foyer / waiting space", f"{q['foyer_m2']} m²", f"≥ {need:.1f} m²", PASS if q["foyer_m2"] >= need else FAIL, note)

    # cinemas in multi-storey buildings
    c = q.get("cinema_in_building")
    if c:
        if q.get("basement") and c.get("basement_level", 1) > 1:
            add("B27.3", "Cinema in basement", f"B{c['basement_level']}", "first basement only", FAIL)
        if c.get("aggregate_cinema_occupancy") is not None:
            v = c["aggregate_cinema_occupancy"]
            add("B27.1", "Cinemas in one building", f"{v} persons", "≤ 2,000", PASS if v <= 2000 else FAIL)
        if c.get("shares_exits"):
            need = ["dedicated smoke extraction", "auditorium fire compartment", "FR doors to auditorium",
                    "exits discharge to streets ≥ 4.5 m", "separate from domestic exit routes"]
            miss = [x for x in need if x not in c.get("provisions", [])]
            add("B27.2 / C18.1", "Shared protected exits conditions", "missing: " + "; ".join(miss) if miss else "all provided",
                "B27.2(a)-(j)", FAIL if miss else PASS)
            if c.get("exit_width_through_other_accommodation_mm") is not None and routes:
                v = c["exit_width_through_other_accommodation_mm"]
                tot_req = (b5(occ) if q.get("floor_level_m", 0) >= 12 else b2(occ))[1]
                add("B27.5(a)", "Exit width discharging through adjoining accommodation", f"{v} mm", f"≤ {tot_req/2:.0f} mm (half)",
                    PASS if v <= tot_req / 2 else FAIL)
        if c.get("projection_room_frr_min") is not None:
            v = c["projection_room_frr_min"]
            add("C18.1(d)", "Projection room enclosure", f"{v} min", "≥ -/60/60, door with smoke seal",
                PASS if v >= 60 else FAIL)

    t = q.get("theatre")
    if t:
        ok = t.get("sprinklered") and t.get("proscenium_frr_min", 0) >= 60 and t.get("fire_curtain_frr_min", 0) >= 30
        add("C18.2", "Theatre stage separation",
            f"sprinklered={t.get('sprinklered')}, proscenium {t.get('proscenium_frr_min')} min, curtain {t.get('fire_curtain_frr_min')} min",
            "fully sprinklered, proscenium -/60/60, fire/water curtain -/30/-", PASS if ok else FAIL)

    if q.get("lining_class"):
        order = ["A1", "A2", "B", "C", "D", "E", "F"]
        v = q["lining_class"]
        add("E13.1(c) / E14.1(c)", "Wall, ceiling and floor linings in auditorium", f"Class {v}", "Class C or better",
            PASS if order.index(v) <= order.index("C") else FAIL)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    q = p["ppe"]
    rows = run(q)
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out = [f"# Place of public entertainment check – {q.get('name', p.get('project', 'Untitled'))}", "",
           f"**Result: the scheme {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).", "",
           "> Draft for review and signature by an Authorized Person. FS Code 2011 (2024 Ed.) B19-B28 and C18; "
           "the Places of Public Entertainment Ordinance (Cap. 172) licensing requirements are separate.", "",
           "| Clause | Item | Proposed | Limit | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")  # reports contain Chinese and symbols
    main()
