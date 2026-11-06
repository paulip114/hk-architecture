#!/usr/bin/env python3
"""Energy efficiency checker – OTTV calculator (B(EE)R Cap. 123M, OTTV Code 1995, PNAP APP-67), RTTV and
glazing limits for residential buildings (PNAP APP-156), and Building Energy Code 2024 (Cap. 610) lighting
power density, chiller COP and Major Retrofitting Works triggers.

Usage:  python3 energy_check.py project.json [-o report.md]   (reads the `energy` block)

`energy`:
  plans_submitted: "YYYY-MM-DD"  (on/after 2025-12-31 -> current limits 20/40, 12.5/3.5)
  ottv_parts[]: {name, kind: tower | podium,
     facades[]: {orientation (16-point: N, NNE, NE ... NNW),
        opaque[]: {name, area_m2, absorptivity, and either u + density_kg_m2
                   or layers[] (outside -> inside) of {material (energy.json table1) | k + density_kg_m3,
                   thickness_m} or {air_gap_mm}, plus internal_absorptivity (picks Ri, Table 2)},
        windows[]: {name, area_m2, sc, and esm, or opf (overhang A/B) and/or spf (sidefin C/D)}},
     roofs[]: {opaque[]: {...as above, slope: flat | slope_22_5 | slope_45}, skylights[]: {name, area_m2, sc}}}
  rttv: {wall_W_m2, roof_W_m2, windows[]: {name, prescribed (bool), vlt_pct, er_pct}}
  bec: {spaces[]: {name, type (key of bec_lpd_W_m2), area_m2, lighting_W},
        chillers[]: {name, type (key of chiller_min_cop), cop},
        lift_car_fans[]: {name, W_per_l_s},
        retrofit: {works_area_m2, circuit_A, ac_kW}}

OTTV Code 1995 paras 5-6 (no conduction term for glass):
  OTTVw = [Σ Aw·U·α·TDEQw + Σ Afw·SC·ESM·SF] / (Aw + Afw)     TDEQw: Table 5 (orientation x density)
  OTTVr = [Σ Ar·U·α·TDEQr + Σ Afr·SC·SF_H] / (Ar + Afr)       TDEQr: Table 9, SF_H = 264
  Tower / podium OTTV = (G + H) / (E + F), the average over all walls and roofs (para 3.2, Form OTTV 4).
Exclude refuge-floor walls, car park walls/roofs, lightwells ≤ 21 m² and walls on roofs (para 4.1).
`python3 energy_check.py --selftest` re-runs the Code's Appendix A East-tower sample (41.61 W/m²).
"""
import argparse
import bisect
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
E = json.loads((HERE.parent / "energy" / "energy.json").read_text(encoding="utf-8"))
O = E["ottv_code"]
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"
T6_COL = {"N": "N", "NE": "NE/NW", "NW": "NE/NW", "S": "S/E/W", "E": "S/E/W", "W": "S/E/W", "SE": "SE/SW", "SW": "SE/SW"}


def density_band(rho):
    # Table 5 / 9 bands: <22 | 23-199 | 200-379 | 380-569 | >=570 kg/m²
    return bisect.bisect_right(O["table5_density_bands_kg_m2"], rho)


def tdeq_wall(orient, rho):
    return O["table5_tdeq_wall"][orient][density_band(rho)]


def tdeq_roof(rho):
    return O["table9_tdeq_roof"][density_band(rho)]


def esm_lookup(table, col, factor, notes):
    cols = table["columns"]
    if col not in cols:
        notes.append(f"no ESM column for {col}: give esm directly")
        return 1.0
    rows = table["rows"]
    if factor > rows[-1][0] + 1e-9:
        notes.append(f"factor {factor} above table limit {rows[-1][0]}: capped")
        factor = rows[-1][0]
    for r in rows:  # "adopt the multiplier related to the next larger value"
        if r[0] >= factor - 1e-9:
            return r[1 + cols.index(col)]


def window_esm(w, orient, notes):
    if "esm" in w:
        return w["esm"]
    vals = []
    if w.get("opf") is not None:
        vals.append(esm_lookup(O["table6_esm_overhang"], T6_COL.get(orient, orient), w["opf"], notes))
    if w.get("spf") is not None:
        vals.append(esm_lookup(O["table7_esm_sidefin"], orient, w["spf"], notes))
    return min(vals) if vals else 1.0  # 7.6(c): the smaller of the two


def element_u(el, roof, notes):
    """U and density per para 7.1 (Tables 1-3), or as given."""
    if "u" in el:
        return el["u"], el["density_kg_m2"]
    T2, T3, T1 = O["table2_surface_resistance"], O["table3_air_space"], O["table1_materials"]
    hi_ext = el["absorptivity"] >= 0.5
    hi_int = el.get("internal_absorptivity", 0.3) >= 0.5
    if roof:
        ri = T2["roof_ri_alpha_ge_0_5" if hi_int else "roof_ri_alpha_lt_0_5"][el.get("slope", "flat")]
        ro = T2["roof_ro"]
    else:
        ri = T2["wall_ri_alpha_ge_0_5" if hi_int else "wall_ri_alpha_lt_0_5"]
        ro = T2["wall_ro"]
    r, rho = ri + ro, 0.0
    for L in el["layers"]:
        if "air_gap_mm" in L:
            key = ("roof_horizontal_" if roof else "wall_") + ("alpha_ge_0_5" if hi_ext else "alpha_lt_0_5")
            ws = T3["widths_mm"]
            i = min(range(len(ws)), key=lambda j: abs(ws[j] - L["air_gap_mm"]))
            if ws[i] != L["air_gap_mm"]:
                notes.append(f"air gap {L['air_gap_mm']} mm taken as {ws[i]} mm (Table 3)")
            r += T3[key][i]
            continue
        dens, k = T1[L["material"]] if "material" in L else (L["density_kg_m3"], L["k"])
        r += L["thickness_m"] / k
        rho += L["thickness_m"] * dens
    return round(1 / r, 2), round(rho, 2)


def ottv(part):
    """Returns (G, E, H, F, notes) as on Form OTTV 4."""
    notes = []
    G = Ea = H = F = 0.0
    for fa in part.get("facades", []):
        o = fa["orientation"]
        sf = O["table8_sf"][o]
        for el in fa.get("opaque", []):
            u, rho = element_u(el, False, notes)
            G += el["area_m2"] * u * el["absorptivity"] * tdeq_wall(o, rho)
            Ea += el["area_m2"]
        for w in fa.get("windows", []):
            G += w["area_m2"] * w["sc"] * window_esm(w, o, notes) * sf
            Ea += w["area_m2"]
    for rf in part.get("roofs", []):
        for el in rf.get("opaque", []):
            u, rho = element_u(el, True, notes)
            H += el["area_m2"] * u * el["absorptivity"] * tdeq_roof(rho)
            F += el["area_m2"]
        for s in rf.get("skylights", []):
            H += s["area_m2"] * s["sc"] * O["table8_sf"]["H"]
            F += s["area_m2"]
    return G, Ea, H, F, notes


def run(q):
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    current = q.get("plans_submitted", "2099-01-01") >= E["ottv_limits"]["current"]["applies_from"]
    lim = E["ottv_limits"]["current" if current else "previous_2024"]
    if q.get("ottv_parts"):
        add("APP-67 para 3, 12", "OTTV limit set", "current (from 31-12-2025)" if current else "previous (before 31-12-2025)",
            f"tower {lim['tower']} / podium {lim['podium']} W/m²", INFO, "OTTV Code 1995 tables (verified)")
    for p in q.get("ottv_parts", []):
        G, Ea, H, F, notes = ottv(p)
        limit = lim[p["kind"]]
        glass = sum(w["area_m2"] for fa in p.get("facades", []) for w in fa.get("windows", []))
        if Ea:
            add("Form OTTV 4", f"{p['name']} walls OTTV (G/E)", f"{G / Ea:.2f} W/m²", "-", INFO,
                f"E = {Ea:.2f} m², G = {G:,.2f} W, WWR {glass / Ea:.2f}")
        if F:
            add("Form OTTV 4", f"{p['name']} roofs OTTV (H/F)", f"{H / F:.2f} W/m²", "-", INFO, f"F = {F:.2f} m²")
        overall = (G + H) / (Ea + F)
        ok = overall <= limit
        add("APP-67 para 3; Code 3.2", f"{p['name']} {p['kind']} OTTV (G+H)/(E+F)", f"{overall:.2f} W/m²",
            f"≤ {limit} W/m²", PASS if ok else FAIL, "; ".join(dict.fromkeys(notes)))
        if not ok:
            solar = sum(w["area_m2"] * window_esm(w, fa["orientation"], []) * O["table8_sf"][fa["orientation"]]
                        for fa in p.get("facades", []) for w in fa.get("windows", []))
            solar_now = sum(w["area_m2"] * w["sc"] * window_esm(w, fa["orientation"], []) * O["table8_sf"][fa["orientation"]]
                            for fa in p.get("facades", []) for w in fa.get("windows", []))
            if solar:
                sc_need = (limit * (Ea + F) - (G + H - solar_now)) / solar
                add("APP-67", f"{p['name']} uniform glazing SC to meet limit", "-",
                    f"SC ≤ {sc_need:.2f}" if sc_need > 0 else "not achievable by SC alone", INFO,
                    "or add overhangs / fins (ESM), cut WWR, lower wall U or α")

    r = q.get("rttv")
    if r:
        R = E["rttv_limits"]["current" if current else "previous_2024"]
        for k, key in (("wall", "wall_W_m2"), ("roof", "roof_W_m2")):
            if key in r:
                add("APP-156 para 6", f"RTTV {k}", f"{r[key]} W/m²", f"≤ {R[k]} W/m²", PASS if r[key] <= R[k] else FAIL,
                    "RTTV itself computed with BD Guidelines spreadsheet")
        for w in r.get("windows", []):
            if w.get("prescribed") and "vlt_pct" in w:
                v = E["rttv_limits"]["vlt_min_pct"]
                add("APP-156 para 6", f"{w['name']} VLT (prescribed window)", f"{w['vlt_pct']}%", f"≥ {v}%",
                    PASS if w["vlt_pct"] >= v else FAIL)
            if "er_pct" in w:
                v = E["rttv_limits"]["external_reflectance_max_pct"]
                add("APP-156 para 6", f"{w['name']} external reflectance", f"{w['er_pct']}%", f"≤ {v}%",
                    PASS if w["er_pct"] <= v else FAIL)

    b = q.get("bec", {})
    L = E["bec_lpd_W_m2"]
    for s in b.get("spaces", []):
        if s["type"] not in L:
            add("BEC 2024 Table 5.4", s["name"], s["type"], "space type", WARN, "not encoded: read the Code")
            continue
        lpd = s["lighting_W"] / s["area_m2"]
        add("BEC 2024 Table 5.4", f"{s['name']} LPD", f"{lpd:.1f} W/m²", f"≤ {L[s['type']]} W/m²",
            PASS if lpd <= L[s["type"]] else FAIL)
    O = E["bec_other"]
    for c in b.get("chillers", []):
        need = O["chiller_min_cop"].get(c["type"])
        if need is None or c["type"].startswith("_"):
            add("BEC 2024 Ch. 6", c["name"], c["type"], "chiller type", WARN, "not encoded")
            continue
        add("BEC 2024 Ch. 6", f"{c['name']} COP", c["cop"], f"≥ {need}", PASS if c["cop"] >= need else FAIL)
    for f in b.get("lift_car_fans", []):
        add("BEC 2024 Ch. 8", f"{f['name']} lift car fan", f"{f['W_per_l_s']} W/(l/s)", f"≤ {O['lift_car_fan_max_W_per_l_s']}",
            PASS if f["W_per_l_s"] <= O["lift_car_fan_max_W_per_l_s"] else FAIL)
    rt = b.get("retrofit")
    if rt:
        T = E["beeo_triggers"]["major_retrofitting"]
        hit = [n for n, k, t in (("works area", "works_area_m2", T["works_area_m2"]), ("circuit", "circuit_A", T["central_electrical_circuit_A"]),
                                 ("A/C", "ac_kW", T["ac_installation_kW"])) if rt.get(k, 0) >= t]
        add("BEEO s.9 / BEC Table 10.1", "Major retrofitting works", ", ".join(hit) or "none triggered",
            f"≥ {T['works_area_m2']} m² / {T['central_electrical_circuit_A']} A / {T['ac_installation_kW']} kW", INFO,
            "BEC compliance needed for the works; confirm forms with EMSD" if hit else "")
    return rows


def selftest():
    """OTTV Code 1995 Appendix A, East (Tower), Forms OTTV 1 and 3: expect 41.61 W/m²."""
    el = lambda n, a, u, al, rho: {"name": n, "area_m2": a, "u": u, "absorptivity": al, "density_kg_m2": rho}
    east = {"orientation": "E",
            "opaque": [el("W1", 200.40, 1.51, 0.58, 1482), el("W2", 220.44, 1.24, 1.00, 1471), el("W3", 206.00, 2.32, 0.58, 282),
                       el("W4", 262.68, 0.41, 1.00, 39), el("W5", 43.20, 1.91, 0.58, 762), el("W5A", 86.40, 3.13, 0.58, 731),
                       el("W6", 47.52, 1.50, 1.00, 751), el("W6A", 95.04, 2.16, 1.00, 740), el("W7", 28.80, 0.69, 0.58, 7231),
                       el("W8", 31.68, 0.63, 1.00, 7220)],
            "windows": [{"name": "F1", "area_m2": 172.80, "sc": 0.70, "esm": 0.7}, {"name": "F2", "area_m2": 156.80, "sc": 0.70},
                        {"name": "F3", "area_m2": 119.68, "sc": 0.70, "esm": 0.7}, {"name": "F4", "area_m2": 206.80, "sc": 0.70},
                        {"name": "F5", "area_m2": 43.20, "sc": 0.70}, {"name": "F6", "area_m2": 47.52, "sc": 0.70}]}
    G, Ea, H, F, _ = ottv({"facades": [east]})
    got = round(G / Ea, 2)
    w1 = element_u({"absorptivity": 0.58, "internal_absorptivity": 0.30, "layers": [
        {"material": "mosaic_tile", "thickness_m": 0.005}, {"material": "cement_sand_render", "thickness_m": 0.01},
        {"material": "concrete_normal", "thickness_m": 0.60}, {"material": "gypsum_plaster", "thickness_m": 0.01}]}, False, [])
    w4 = element_u({"absorptivity": 1.0, "internal_absorptivity": 0.30, "layers": [
        {"material": "glass", "thickness_m": 0.008}, {"material": "mineral_wool_felt", "thickness_m": 0.075},
        {"air_gap_mm": 50}, {"material": "steel", "thickness_m": 0.002}]}, False, [])
    checks = [("East tower OTTV", got, 41.61), ("W1 U", w1[0], 1.51), ("W1 density", round(w1[1], 1), 1482.3),
              ("W4 U", w4[0], 0.41)]
    bad = 0
    for name, g, want in checks:
        ok = abs(g - want) <= 0.006
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {name}: {g} (Code: {want})")
    print(f"E = {Ea:.2f} m² (Code 1,968.96), G = {G:,.2f} W (Code 81,921.03)")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?")
    ap.add_argument("-o", "--output")
    ap.add_argument("--selftest", action="store_true", help="re-run the OTTV Code Appendix A sample")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows = run(p["energy"])
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out = [f"# Energy efficiency check – {p.get('project', 'Untitled')}", "",
           f"**Result: {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).", "",
           "> Draft for review by an Authorized Person and the BS engineer (REA under BEEO). Limits from PNAP APP-67 / "
           "APP-156 (Sept 2025) and BEC 2024; OTTV method and tables from the OTTV Code 1995.", "",
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
