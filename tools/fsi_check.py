#!/usr/bin/env python3
"""FSI checker – minimum fire service installations by premises type, FSD Codes of Practice
for Minimum Fire Service Installations and Equipment (Sept 2022), Part IV (paras 4.1-4.45).

Usage:  python3 fsi_check.py project.json [-o report.md]   (reads the `fsi` block)
        python3 fsi_check.py --list                          (premises types and aliases)

`fsi`:
  uppermost_floor_above_staircase_discharge_m   (> 30 m = high rise, Part III)
  storeys (domestic only, for the ≤ 3 storey case)
  street_hydrant_distance_m, hose_reel_max_hose_m, fs_tank_litres, largest_floor_m2
  parts[]: {name, use: domestic | commercial | hotel | industrial | institutional | basement | garage | car_port
            (or a para number "4.33" / alias from --list),
            total_floor_area_m2, max_single_occupancy_floor_m2, compartment_volume_m3, atrium_volume_m3,
            openable_window_pct, fire_load_mj_m2, natural_stair_venting (bool), cubical_extent_m3,
            basement_levels, industrial_basement (bool), open_air_firemen_access (bool), ev_charging (bool),
            ev_area_sprinklered (bool), hospital_nursing_prison (bool), guestroom_corridor_window_pct,
            provided: [installation keys]}
Required and missing = FAIL. Conditional and not decidable from the inputs = CHECK, with the Code's
own wording (applicability_zh) in the note.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = json.loads((HERE.parent / "fsi" / "fsi_schedule.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"
NAMES = S["installations"]
ALIAS = {v["alias"]: k for k, v in S["premises"].items() if "alias" in v}


def premises_key(part, q):
    u = part["use"]
    if u in S["premises"]:
        return u
    if u in ALIAS:
        return ALIAS[u]
    high = q.get("uppermost_floor_above_staircase_discharge_m", 0) > S["high_rise_m"]
    if u == "domestic":
        if q.get("storeys", 99) <= 3:
            return ALIAS["domestic_le3"]
        return ALIAS["domestic_high" if high else "domestic_low"]
    if u == "basement":
        return ALIAS["basement_gt230" if part.get("total_floor_area_m2", 0) > 230 else "basement_le230"]
    return ALIAS.get(f"{u}_{'high' if high else 'low'}")


def smoke_compartment(p):
    if p.get("atrium_volume_m3", 0) > 28000:
        return True
    keys = ("compartment_volume_m3", "openable_window_pct", "fire_load_mj_m2")
    if any(p.get(k) is None for k in keys):
        return None
    return p["compartment_volume_m3"] > 7000 and p["openable_window_pct"] <= 6.25 and p["fire_load_mj_m2"] > 1135


def decide(cond, p):
    """True = required, False = not required, None = cannot tell from inputs."""
    g = p.get
    if cond == "yes":
        return True
    if cond == "check":
        return None
    c = S["conditions"][cond]
    if "field" in c:
        return None if g(c["field"]) is None else g(c["field"]) > c["gt"]
    if cond == "smoke_compartment":
        return smoke_compartment(p)
    if cond == "smoke_hotel":
        if g("guestroom_corridor_window_pct") is not None and g("guestroom_corridor_window_pct") <= 6.25:
            return True
        return smoke_compartment(p) or None
    if cond == "smoke_basement":
        if g("industrial_basement") or (g("basement_levels") or 0) >= 3:
            return True
        if g("compartment_volume_m3") is None or g("fire_load_mj_m2") is None:
            return None
        return g("compartment_volume_m3") > 7000 and g("fire_load_mj_m2") > 1135
    if cond in ("press_2", "press_4", "press_hospital"):
        if cond == "press_hospital" and g("hospital_nursing_prison") is False:
            return False
        if g("natural_stair_venting") is True:
            return False
        if g("openable_window_pct") is not None and g("openable_window_pct") > 6.25:
            return False
        if g("natural_stair_venting") is None or g("openable_window_pct") is None:
            return None
        if cond == "press_4":
            if g("cubical_extent_m3") is None or g("fire_load_mj_m2") is None:
                return None
            return g("cubical_extent_m3") > 28000 and g("fire_load_mj_m2") > 1135
        return True if cond == "press_2" else (True if g("hospital_nursing_prison") else None)
    if cond == "press_basement":
        if g("basement_levels") is not None and g("basement_levels") < 3:
            return False
        keys = ("basement_levels", "open_air_firemen_access", "cubical_extent_m3", "fire_load_mj_m2")
        if any(g(k) is None for k in keys):
            return None
        return (not g("open_air_firemen_access")) and g("cubical_extent_m3") > 7000 and g("fire_load_mj_m2") > 1135
    if cond == "frs_basement":
        return True if (g("basement_levels") or 0) >= 3 else None
    if cond == "ev_charging":
        return None if g("ev_charging") is None else bool(g("ev_charging"))
    if cond == "ev_detection":
        if g("ev_charging") is False:
            return False
        if g("ev_charging") and not g("ev_area_sprinklered", "sprinkler" in g("provided", [])):
            return True
        return False if g("ev_charging") else None
    if cond == "eg_institutional":
        return True if g("hospital_nursing_prison") else None
    if cond == "fd_uncovered":
        return True  # needed wherever no automatic fixed installation covers the area
    return None


def run(q):
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    h = q.get("uppermost_floor_above_staircase_discharge_m")
    if h is not None:
        add("Part III", "Uppermost floor above staircase discharge", f"{h} m",
            f"> {S['high_rise_m']} m = high rise", INFO, "high rise" if h > S["high_rise_m"] else "low rise")
    sprinklered_nd, domestic_parts = False, []
    for part in q.get("parts", []):
        key = premises_key(part, q)
        spec = S["premises"].get(key)
        if spec is None:
            add("Part IV", part["name"], part["use"], "premises type", WARN, "unknown use: see --list")
            continue
        ref = f"para {key}"
        if spec.get("alias", "").startswith("domestic"):
            domestic_parts.append(part["name"])
        elif "sprinkler" in part.get("provided", []):
            sprinklered_nd = True
        prov = set(part.get("provided", []))
        add(ref, f"{part['name']}: premises type", spec["title_zh"], "-", INFO, spec.get("note_zh", ""))
        if not spec["installations"]:
            add(ref, f"{part['name']}: requirements", "-", "see text_zh in fsi_schedule.json", WARN,
                " ".join(spec.get("text_zh", []))[:300])
        for inst, v in spec["installations"].items():
            cond = v["cond"]
            need = decide(cond, part)
            have = inst in prov
            if inst == "fire_detection" and cond == "fd_uncovered" and "sprinkler" in prov:
                need = None
            label = f"{part['name']}: {NAMES[inst]['en']} {NAMES[inst]['zh']}"
            why = S["conditions"].get(cond, {}).get("text", "") if cond not in ("yes", "check") else ""
            if need is True:
                add(ref, label, "provided" if have else "not provided", "required" + (f" ({why})" if why else ""),
                    PASS if have else FAIL)
            elif need is None:
                add(ref, label, "provided" if have else "not provided", f"required if: {why or 'see note'}",
                    PASS if have else WARN, "" if have else v["applicability_zh"][:220])
            elif have:
                add(ref, label, "provided", f"not required ({why})", INFO)
        extra = prov - set(spec["installations"]) - set(NAMES)
        if extra:
            add(ref, f"{part['name']}: unknown installation keys", ", ".join(sorted(extra)), "-", WARN)

    if domestic_parts and sprinklered_nd:
        r = S["composite_rule"]
        add("para 4.16(ii)", "Composite: sprinklers in staircases to the domestic part", ", ".join(domestic_parts),
            "floors immediately above and below the sprinklered non-domestic part, fast-response heads", WARN,
            r["text_zh"])
    if "street_hydrant_distance_m" in q:
        d = q["street_hydrant_distance_m"]
        add("para 1.5", "Street fire hydrant distance", f"{d} m", f"≤ {S['street_hydrant_max_m']} m",
            PASS if d <= S["street_hydrant_max_m"] else FAIL)
    if "hose_reel_max_hose_m" in q:
        d = q["hose_reel_max_hose_m"]
        add("Part IV", "Hose reel coverage (longest hose run)", f"{d} m", f"≤ {S['hose_reel_max_hose_m']} m",
            PASS if d <= S["hose_reel_max_hose_m"] else FAIL)
    if "fs_tank_litres" in q and "largest_floor_m2" in q:
        a = q["largest_floor_m2"]
        tab = S["fs_tank"]["hydrant_hose_reel_litres_by_largest_floor_m2"]
        need = next(l for lim, l in tab if lim is None or a <= lim)
        add("para 5.26", "FH/HR fire service water tank", f"{q['fs_tank_litres']} L",
            f"≥ {need} L for largest floor {a} m²", PASS if q["fs_tank_litres"] >= need else FAIL,
            "Effective quantity, gross floor area of the largest floor")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?")
    ap.add_argument("-o", "--output")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for k, v in S["premises"].items():
            print(f"{k:5} {v.get('alias', ''):22} {v['title_zh']}")
        return
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows = run(p["fsi"])
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out = [f"# Minimum FSI check – {p.get('project', 'Untitled')}", "",
           f"**Result: {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).", "",
           "> Draft for review by an Authorized Person and the FSI engineer / registered FSI contractor. Schedule from "
           "the FSD Codes of Practice for Minimum FSI (Sept 2022) Part IV, Chinese text. FSD may vary requirements "
           "(para 1.3). Part V design details are not checked.", "",
           "| Clause | Item | Proposed | Requirement | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    out += ["| " + " | ".join(str(x).replace("|", "/") for x in r) + " |" for r in rows]
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")  # reports contain Chinese and symbols
    main()
