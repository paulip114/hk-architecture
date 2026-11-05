#!/usr/bin/env python3
"""Energy efficiency checker – OTTV calculator (B(EE)R Cap. 123M / PNAP APP-67), RTTV and glazing
limits for residential buildings (PNAP APP-156), and Building Energy Code 2024 (Cap. 610) lighting
power density, chiller COP and Major Retrofitting Works triggers.

Usage:  python3 energy_check.py project.json [-o report.md]   (reads the `energy` block)

`energy`:
  plans_submitted: "YYYY-MM-DD"  (on/after 2025-12-31 -> current limits 20/40, 12.5/3.5)
  constants: optional override of energy.json `ottv_constants` (set "verified": true once copied from the OTTV Code)
  ottv_parts[]: {name, kind: tower | podium, use,
     walls[]: {orientation N/NE/E/SE/S/SW/W/NW, opaque_m2, u_wall, absorptivity, density_kg_m2,
               glass_m2, u_glass, sc, esm (external shading multiplier, default 1)},
     roofs[]: {opaque_m2, u_roof, absorptivity, density_kg_m2, skylight_m2, u_skylight, sc, esm}}
  rttv: {wall_W_m2, roof_W_m2, windows[]: {name, prescribed (bool), vlt_pct, er_pct}}
  bec: {spaces[]: {name, type (key of bec_lpd_W_m2), area_m2, lighting_W},
        chillers[]: {name, type (key of chiller_min_cop), cop},
        lift_car_fans[]: {name, W_per_l_s},
        retrofit: {works_area_m2, circuit_A, ac_kW}}

OTTV (structure of the OTTV Code 1995):
  wall OTTV = [Σ A_w·U_w·α·TDeq + Σ A_f·U_f·ΔT + Σ A_f·SC·ESM·SF] / Σ (A_w + A_f)
  roof OTTV = [Σ A_r·U_r·α·TDeq + Σ A_s·U_s·ΔT + Σ A_s·SC·ESM·SF_H] / Σ (A_r + A_s)
  overall  = area-weighted average of wall and roof
TDeq, ΔT and SF come from energy.json and are PLACEHOLDERS until verified: OTTV rows are CHECK, never PASS,
while `verified` is false.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
E = json.loads((HERE.parent / "energy" / "energy.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"


def band(table, x):
    for lim, v in table:
        if lim is None or x <= lim:
            return v


def ottv(part, C):
    sf = C["solar_factor_W_m2"]
    dt = C["delta_t_K"]
    num_w = area_w = 0.0
    for w in part.get("walls", []):
        td = band(C["tdeq_wall_by_density"], w["density_kg_m2"])
        num_w += w["opaque_m2"] * w["u_wall"] * w["absorptivity"] * td
        num_w += w.get("glass_m2", 0) * w.get("u_glass", 0) * dt
        num_w += w.get("glass_m2", 0) * w.get("sc", 0) * w.get("esm", 1) * sf[w["orientation"]]
        area_w += w["opaque_m2"] + w.get("glass_m2", 0)
    num_r = area_r = 0.0
    for r in part.get("roofs", []):
        td = band(C["tdeq_roof_by_density"], r["density_kg_m2"])
        num_r += r["opaque_m2"] * r["u_roof"] * r["absorptivity"] * td
        num_r += r.get("skylight_m2", 0) * r.get("u_skylight", 0) * dt
        num_r += r.get("skylight_m2", 0) * r.get("sc", 0) * r.get("esm", 1) * sf["H"]
        area_r += r["opaque_m2"] + r.get("skylight_m2", 0)
    wall = num_w / area_w if area_w else None
    roof = num_r / area_r if area_r else None
    overall = (num_w + num_r) / (area_w + area_r) if area_w + area_r else None
    return wall, roof, overall, area_w, area_r


def run(q):
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    current = q.get("plans_submitted", "2099-01-01") >= E["ottv_limits"]["current"]["applies_from"]
    lim = E["ottv_limits"]["current" if current else "previous_2024"]
    C = dict(E["ottv_constants"])
    C.update(q.get("constants", {}))
    verified = C.get("verified", False)
    if q.get("ottv_parts"):
        add("APP-67 para 3, 12", "OTTV limit set", "current (from 31-12-2025)" if current else "previous (before 31-12-2025)",
            f"tower {lim['tower']} / podium {lim['podium']} W/m²", INFO)
        if not verified:
            add("OTTV Code 1995", "OTTV constants (TDeq, ΔT, SF)", "placeholders", "Code tables", WARN,
                "results below are indicative only; load the Code's tables into energy.json")
    for p in q.get("ottv_parts", []):
        wall, roof, overall, aw, ar = ottv(p, C)
        limit = lim[p["kind"]]
        wwr = sum(w.get("glass_m2", 0) for w in p.get("walls", [])) / aw if aw else 0
        add("APP-67 App. A", f"{p['name']} window-to-wall ratio", f"{wwr:.2f}", "-", INFO)
        if wall is not None:
            add("B(EE)R / APP-67", f"{p['name']} wall OTTV", f"{wall:.1f} W/m²", f"(compare ≤ {limit} W/m²)",
                INFO if wall <= limit else WARN,
                "" if wall <= limit else "walls alone exceed the limit: confirm the limit applies to the overall value")
        if roof is not None:
            add("B(EE)R / APP-67", f"{p['name']} roof OTTV", f"{roof:.1f} W/m²", "(reported)", INFO)
        ok = overall <= limit
        add("APP-67 para 3", f"{p['name']} overall OTTV ({p['kind']})", f"{overall:.1f} W/m²", f"≤ {limit} W/m²",
            (PASS if ok else FAIL) if verified else (WARN if ok else FAIL),
            "" if verified else "indicative: placeholder constants")
        if not ok and aw:
            # glass solar term dominates; show the SC that would hit the limit, all else equal
            sf = C["solar_factor_W_m2"]
            fixed = overall * (aw + ar) - sum(w.get("glass_m2", 0) * w.get("sc", 0) * w.get("esm", 1) * sf[w["orientation"]]
                                               for w in p["walls"])
            solar_unit = sum(w.get("glass_m2", 0) * w.get("esm", 1) * sf[w["orientation"]] for w in p["walls"])
            if solar_unit:
                sc_need = (limit * (aw + ar) - fixed) / solar_unit
                add("APP-67", f"{p['name']} glazing SC needed to meet limit", "-",
                    f"SC ≤ {sc_need:.2f}" if sc_need > 0 else "not achievable by SC alone", INFO,
                    "or add external shading (lower ESM) / cut WWR")

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
        if need is None:
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows = run(p["energy"])
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out = [f"# Energy efficiency check – {p.get('project', 'Untitled')}", "",
           f"**Result: {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).", "",
           "> Draft for review by an Authorized Person and the BS engineer (REA under BEEO). Limits from PNAP APP-67 / "
           "APP-156 (Sept 2025) and BEC 2024. OTTV constants are placeholders until loaded from the OTTV Code 1995.", "",
           "| Clause | Item | Proposed | Limit | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
