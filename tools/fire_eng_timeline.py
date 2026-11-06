#!/usr/bin/env python3
"""Part G timeline screening (Assessment Type 2): ASET vs RSET for each scenario.
FS Code 2011 (2024 Ed.) Part G, Clauses G3.4, G6.4-G6.8, Table G1.

SCREENING TOOL ONLY. A one-zone smoke-filling model of a single room; it does not replace
CFD / zone modelling (G9), hot smoke tests (G7.3) or the FSAR (G7.1).

Usage: python3 fire_eng_timeline.py project.json [-o report.md]   (reads `fire_engineering`)

fire_engineering.scenarios[]:
  name, use_class (key of Table G1, e.g. "4a"), floor_area_m2, ceiling_height_m,
  growth (slow|medium|fast|ultra_fast), sprinklered (bool),
  optional: hrr_cap_kw (override), fuel_load_mj_m2 + fire_area_m2 (unsprinklered 4b),
            extract_m3_s, ambient_c (default 20), radiative_fraction (default 0.3),
            layer_criterion_m (default 2.0),
  detection_s, alarm_s, and pre_movement_s OR occupant_category + alarm (voice|standard|local)
  [+ pre_movement_source pd7974_t1|pd7974_t2|sfpe|nz_origin|nz_remote|cibse, building_complexity],
  occupants, travel_distance_m, exit_widths_mm [], walking_speed_m_s, specific_flow_p_s_m,
  movement ("max" = PD 7974-6 longer of travel/flow, or "sum"),
  safety_factor (default 1.5) or safety_margin_s
"""
import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
G = json.loads((HERE.parent / "fs-code" / "part_g.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"
CP = 1.0  # kJ/kg K


def hrr_cap(s, add):
    if s.get("hrr_cap_kw"):
        return s["hrr_cap_kw"], "user value"
    g1 = G["table_G1_sprinkler_controlled_kw"].get(str(s.get("use_class")), {})
    if s.get("sprinklered"):
        if g1.get("kw"):
            hr = g1.get("headroom_m")
            if hr and abs(hr - s["ceiling_height_m"]) > 0.05:
                add("Table G1", f"{s['name']} design fire headroom", f"{s['ceiling_height_m']} m",
                    f"Table G1 value is for {hr} m", WARN,
                    "Sprinkler activation and controlled HRR change with headroom: justify or recalculate")
            return g1["kw"], f"Table G1 use {s['use_class']} sprinkler-controlled"
        add("Table G1", f"{s['name']} design fire", "-", "no Table G1 value", WARN, g1.get("note", ""))
        return None, "uncapped t-squared"
    if s.get("fuel_load_mj_m2") and s.get("fire_area_m2"):
        qu = s["fuel_load_mj_m2"] * 1000 / 1200
        return qu * s["fire_area_m2"], f"Table G1 4b: Q_U = q/1200 = {qu:.0f} kW/m² × {s['fire_area_m2']} m²"
    add("Table G1", f"{s['name']} design fire", "unsprinklered", "peak HRR needed", WARN,
        "No cap: fire grows until simulation end; give a ventilation- or fuel-controlled peak")
    return None, "uncapped t-squared"


def aset(s, cap):
    alpha = G["t2_alpha_kw_s2"][s["growth"]]
    A, H = s["floor_area_m2"], s["ceiling_height_m"]
    T0 = s.get("ambient_c", 20) + 273.15
    chi_c = 1 - s.get("radiative_fraction", 0.3)
    zc = s.get("layer_criterion_m", G["tenability_G6_8"]["smoke_layer_height_m"])
    t_rad_k = 200 + 273.15
    vex = s.get("extract_m3_s", 0.0)
    M, E = 1e-6, 0.0  # layer mass kg, layer excess energy kJ
    dt, t, t_end = 0.5, 0.0, s.get("sim_s", 1800)
    hit_z = hit_T = None
    z, T = H, T0
    while t < t_end:
        t += dt
        Q = alpha * t * t
        if cap:
            Q = min(Q, cap)
        Qc = chi_c * Q
        zz = max(z, 0.01)
        L = 0.166 * Qc ** 0.4 if Qc > 0 else 0
        m = (0.071 * Qc ** (1 / 3) * zz ** (5 / 3) + 0.0018 * Qc) if zz > L else 0.0056 * Qc * zz / max(L, 1e-6)
        M += m * dt
        E += Qc * dt
        T = T0 + E / (CP * M)
        rho = 353.0 / T
        if vex:
            out = min(rho * vex * dt, 0.95 * M)
            E -= E * out / M
            M -= out
            T = T0 + E / (CP * M)
            rho = 353.0 / T
        z = H - (M / rho) / A
        if hit_z is None and z <= zc:
            hit_z = t
        if hit_T is None and T >= t_rad_k:
            hit_T = t
        if hit_z and hit_T:
            break
    return hit_z, hit_T, z, T - 273.15, t_end


def g2_pre(s, add):
    """Pre-movement time from Table G2 (default PD 7974-6 T2, last few occupants)."""
    t = G["table_G2_pre_movement_min"]
    cat, alarm = s["occupant_category"], s.get("alarm", "standard")
    col = s.get("pre_movement_source", "pd7974_t2")
    if cat not in t or alarm not in t[cat]:
        add("Table G2", f"{s['name']} pre-movement", f"{cat} / {alarm}", "unknown category", FAIL,
            "categories: " + ", ".join(k for k in t if not k.startswith("_")))
        return None
    row = t[cat][alarm]
    raw = row[col]
    allv = ", ".join(f"{k} {v}" for k, v in row.items())
    if raw == "-" or isinstance(raw, str) and raw.startswith("<"):
        add("Table G2", f"{s['name']} pre-movement", f"{col} = {raw}", "no usable value", WARN,
            f"choose another source; row: {allv}")
        return None
    lower = isinstance(raw, str) and raw.startswith(">")
    mins = float(str(raw).lstrip(">"))
    adj, why = 0.0, ""
    notes = t[cat].get("pd_notes", "")
    cx = s.get("building_complexity")
    if col.startswith("pd7974"):
        if cx == "large_complex" and "e" in notes:
            adj, why = 1.0, "note e"
        elif cx == "large_complex" and "c" in notes:
            adj, why = 0.5, "note c"
        elif cx == "simple_multi_storey" and "d" in notes:
            adj, why = 0.5, "note d"
    total = (mins + adj) * 60
    add("Table G2", f"{s['name']} pre-movement ({t[cat]['examples']}, {alarm} alarm)",
        f"{total:.0f} s", f"{col} {raw} min" + (f" + {adj} ({why})" if adj else ""),
        WARN if lower or "f" in notes else INFO,
        ("value is a lower bound (>): justify a higher figure; " if lower else "")
        + ("depends on presence of staff (note f); " if "f" in notes else "")
        + f"row: {allv}; use one source consistently")
    return total


def rset(s, add):
    d = G["movement_defaults_not_from_code"]
    det = s.get("detection_s")
    if det is None:
        det = 60
        add("G6.7", f"{s['name']} detection time", "not given", "assumed 60 s", WARN,
            "Calculate from detector type / spacing (e.g. DETACT) and state in FSAR")
    alarm = s.get("alarm_s", 0)
    pre = s.get("pre_movement_s")
    if pre is None and s.get("occupant_category"):
        pre = g2_pre(s, add)
    if pre is None:
        pre = 0
        add("Table G2", f"{s['name']} pre-movement time", "not given", "Table G2 value", FAIL,
            "Give pre_movement_s, or occupant_category + alarm (Table G2)")
    v = s.get("walking_speed_m_s", d["walking_speed_m_s"])
    fs = s.get("specific_flow_p_s_m", d["specific_flow_p_s_m"])
    bl = d["boundary_layer_each_side_m"]
    t_trav = s.get("travel_distance_m", 0) / v
    we = sum(max(w / 1000 - 2 * bl, 0) for w in s.get("exit_widths_mm", []))
    t_flow = s.get("occupants", 0) / (fs * we) if we else float("inf")
    mv = max(t_trav, t_flow) if s.get("movement", "max") == "max" else t_trav + t_flow
    if "walking_speed_m_s" not in s or "specific_flow_p_s_m" not in s:
        add("G6.7", f"{s['name']} movement inputs", f"v = {v} m/s, Fs = {fs} p/s/m, edge {bl} m",
            "not given in FS Code", INFO, "SFPE / PD 7974-6 typical values: justify in FSAR")
    return det, alarm, pre, t_trav, t_flow, we, mv, det + alarm + pre + mv


def run(fe):
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    for s in fe.get("scenarios", []):
        cap, src = hrr_cap(s, add)
        tz, tT, z_end, T_end, t_end = aset(s, cap)
        crit = [x for x in (tz, tT) if x]
        a = min(crit) if crit else None
        add("G6.5", f"{s['name']} design fire", f"{s['growth']} t², cap {cap/1000:.2f} MW" if cap else f"{s['growth']} t², no cap",
            src, INFO)
        add("G6.8", f"{s['name']} time to smoke layer at {s.get('layer_criterion_m', 2.0)} m",
            f"{tz:.0f} s" if tz else f"> {t_end} s (layer {z_end:.2f} m)", "tenability", INFO)
        add("G6.8", f"{s['name']} time to layer 200 °C (≈2.5 kW/m²)",
            f"{tT:.0f} s" if tT else f"> {t_end} s (layer {T_end:.0f} °C)", "tenability", INFO)
        det, alarm, pre, tt, tf, we, mv, r = rset(s, add)
        add("G6.7", f"{s['name']} RSET", f"{r:.0f} s",
            f"det {det:.0f} + alarm {alarm:.0f} + pre {pre:.0f} + move {mv:.0f} (travel {tt:.0f}, flow {tf:.0f} over {we:.2f} m)",
            INFO)
        aset_v = a if a else t_end
        if "safety_margin_s" in s:
            need = r + s["safety_margin_s"]
            lim = f"RSET + margin {s['safety_margin_s']} s = {need:.0f} s"
        else:
            sf = s.get("safety_factor", G["safety_factor_G3_4"]["typical_min"])
            need = sf * r
            lim = f"{sf} × RSET = {need:.0f} s"
        ok = aset_v >= need
        add("G3.4 / G6.4", f"{s['name']} ASET vs RSET", f"ASET {'>' if not a else ''}{aset_v:.0f} s", lim,
            PASS if ok else FAIL, "safety factor / margin to be agreed with BD (G3.4)")
        add("G6.8", f"{s['name']} CO, visibility", "-", "CO ≤ 1000 ppm, OD ≤ 0.1 /m (10 m)", WARN,
            "Not modelled here: needs soot/CO yields in CFD or zone model")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows = run(p["fire_engineering"])
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "fails the screening" if fails else "passes the screening, subject to CHECK items"
    out = [f"# Part G timeline screening – {p.get('project', 'Untitled')}", "",
           f"**Result: {verdict}** ({fails} fail, {checks} to check).", "",
           "> Screening only (one-zone smoke filling, single room). Not a substitute for CFD / zone modelling, "
           "hot smoke test or the FSAR. Draft for review by an Authorized Person and the fire engineer; "
           "the Building Authority must accept design fire, pre-movement time, tenability criteria and safety factor.", "",
           "| Clause | Item | Value | Basis / limit | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
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
