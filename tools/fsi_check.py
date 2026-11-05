#!/usr/bin/env python3
"""FSI checker – minimum fire service installations by premises type, FSD Codes of Practice
for Minimum Fire Service Installations and Equipment (Sept 2022), Part IV.

Usage:  python3 fsi_check.py project.json [-o report.md]   (reads the `fsi` block)

`fsi`:
  uppermost_floor_above_staircase_discharge_m   (decides low / high rise, > 30 m = high rise)
  storeys (domestic only, for the ≤ 3 storey case)
  street_hydrant_distance_m, hose_reel_max_hose_m, fs_tank_litres, largest_floor_m2
  parts[]: {name, use: domestic | commercial | hotel | industrial | institutional | basement | garage | car_port
            (or an exact key of fsi/fsi_schedule.json `premises`),
            total_floor_area_m2, max_single_occupancy_floor_m2, compartment_volume_m3,
            openable_window_pct, fire_load_mj_m2, atrium_volume_m3, natural_stair_venting (bool),
            cubical_extent_m3, basement_levels, ev_charging (bool),
            provided: [installation keys]}
Required and missing = FAIL; conditional and not decidable from the inputs = CHECK.
The schedule data is a working extract (verified: false): every report says so.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = json.loads((HERE.parent / "fsi" / "fsi_schedule.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"
NAMES = S["installations"]


def premises_key(part, q):
    u = part["use"]
    if u in S["premises"]:
        return u
    high = q.get("uppermost_floor_above_staircase_discharge_m", 0) > S["high_rise_m"]
    if u == "domestic":
        if q.get("storeys", 99) <= 3:
            return "domestic_le3"
        return "domestic_high" if high else "domestic_low"
    if u == "basement":
        return "basement_gt230" if part.get("total_floor_area_m2", 0) > 230 else "basement_le230"
    if u in ("garage", "car_port"):
        return u
    return f"{u}_{'high' if high else 'low'}"


def decide(cond, part):
    """True = required, False = not required, None = cannot tell from inputs."""
    if cond == "yes":
        return True, ""
    c = S["conditions"][cond]
    if "field" in c:
        v = part.get(c["field"])
        return (None if v is None else v > c["gt"]), c["text"]
    t = c["test"]
    if t == "smoke":
        if part.get("atrium_volume_m3", 0) > 28000:
            return True, c["text"]
        keys = ("compartment_volume_m3", "openable_window_pct", "fire_load_mj_m2")
        if any(part.get(k) is None for k in keys):
            return None, c["text"]
        return (part["compartment_volume_m3"] > 7000 and part["openable_window_pct"] <= 6.25
                and part["fire_load_mj_m2"] > 1135), c["text"]
    if t == "press":
        keys = ("cubical_extent_m3", "fire_load_mj_m2")
        if part.get("natural_stair_venting") is True and part.get("openable_window_pct", 0) > 6.25:
            return False, c["text"]
        if any(part.get(k) is None for k in keys):
            return None, c["text"]
        # only the "required" branch is certain from these fields; otherwise leave it to the AP (CHECK)
        return (part["cubical_extent_m3"] > 28000 and part["fire_load_mj_m2"] > 1135) or None, c["text"]
    if t == "press_bsmt":
        if part.get("basement_levels") is None:
            return None, c["text"]
        if part["basement_levels"] < 3:
            return False, c["text"]
        if part.get("cubical_extent_m3") is None or part.get("fire_load_mj_m2") is None:
            return None, c["text"]
        return part["cubical_extent_m3"] > 7000 and part["fire_load_mj_m2"] > 1135, c["text"]
    if cond == "ev_heat_detect":
        if part.get("total_floor_area_m2", 999) <= 230 and part.get("ev_charging") and "sprinkler" not in part.get("provided", []):
            return True, c["text"]
        return None, c["text"]
    return None, c["text"]


def run(q):
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    h = q.get("uppermost_floor_above_staircase_discharge_m")
    if h is not None:
        add("Part III", "Uppermost floor above staircase discharge", f"{h} m",
            f"> {S['high_rise_m']} m = high rise", INFO, "high rise" if h > S["high_rise_m"] else "low rise")
    sprinklered_nd = False
    domestic_parts = []
    for part in q.get("parts", []):
        key = premises_key(part, q)
        spec = S["premises"].get(key)
        if spec is None:
            add("Part IV", part["name"], part["use"], "premises type", WARN, "not encoded: read the Code")
            continue
        if key.startswith("domestic"):
            domestic_parts.append(part["name"])
        elif "sprinkler" in part.get("provided", []):
            sprinklered_nd = True
        prov = set(part.get("provided", []))
        ref = f"para {spec['para']}"
        add(ref, f"{part['name']}: premises type", spec["name"], "-", INFO, spec.get("note", ""))
        for inst, cond in spec["req"].items():
            need, why = decide(cond, part)
            have = inst in prov
            label = f"{part['name']}: {NAMES[inst]}"
            if need is True:
                add(ref, label, "provided" if have else "not provided", "required" + (f" ({why})" if why else ""),
                    PASS if have else FAIL)
            elif need is None:
                add(ref, label, "provided" if have else "not provided", f"required if {why}",
                    PASS if have else WARN, "" if have else "confirm whether the condition applies")
            elif have:
                add(ref, label, "provided", f"not required ({why})", INFO)
        extra = prov - set(spec["req"]) - set(NAMES)
        if extra:
            add(ref, f"{part['name']}: unknown installation keys", ", ".join(sorted(extra)), "-", WARN)

    if domestic_parts and sprinklered_nd:
        add("para 4.16", "Composite: sprinklers in domestic staircases", ", ".join(domestic_parts),
            "extend 2 floors above the sprinklered non-domestic part, fast-response heads", WARN,
            "show on FSI plans")
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
        need = next(l for lim, l in S["fs_tank_unverified"]["hydrant_hose_reel_litres_by_largest_floor_m2"] if lim is None or a <= lim)
        add("Part V (unverified)", "FH/HR fire service water tank", f"{q['fs_tank_litres']} L",
            f"≥ {need} L for largest floor {a} m² (unverified)", WARN,
            ("meets the unverified table" if q["fs_tank_litres"] >= need else "SHORT of the unverified table")
            + ": confirm against Part V of the 2022 Code")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows = run(p["fsi"])
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out = [f"# Minimum FSI check – {p.get('project', 'Untitled')}", "",
           f"**Result: {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).", "",
           "> Draft for review by an Authorized Person and the FSI engineer / registered FSI contractor. Schedule from the "
           "FSD Codes of Practice for Minimum FSI (Sept 2022) Part IV, read through a web summary and **not yet verified "
           "against the PDF**. FSD may vary requirements (para 1.3). Design details (Part V) are not checked.", "",
           "| Clause | Item | Proposed | Requirement | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
