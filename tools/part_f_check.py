#!/usr/bin/env python3
"""Part F checker – fire safety management plan (FSMP) completeness, fire engineering
Bounding Conditions, open kitchen conditions, lift works (F5.7) and A&A works (F5.6),
and the Table F1 housekeeping checklist. FS Code 2011 (2024 Ed.).

Usage:  python3 part_f_check.py project.json [-o report.md]   (reads `fire_safety_management`)

`fire_safety_management`:
  use_classes [list, e.g. ["1b","4b","7"]]
  fire_engineering (bool), s42_modification (bool)
  fsmp: {maintenance_plan: [item keys], training_plan: [...], fire_action_plan: [...]}
        (keys from fs-code/part_f.json `fsmp_parts`; list what the plan contains)
  temporary_refuge_spaces (bool)
  bounding_conditions: {in_gbp, in_fsmp, fsar_in_fsmp, in_dmc}   (bools)
  open_kitchens: {provided (bool), conditions: [keys], in_fsmp (bool), in_dmc (bool)}
  drill_interval_months (number)
  lift_works: {doors_open_max, hot_work (bool), doors_removed, hoarding_integrity_min,
               vent_openings: [{area_mm2, upper_portion}], liftways, hoarding_door_frr_ok,
               hoarding_door_self_closing_openable_inside, temporary_works_non_combustible,
               openings_secured_when_unattended}
  aa_works: {items: [keys of part_f.json aa_works]}
  housekeeping: {"1.1": "yes"/"no"/"n/a", ...}   (Table F1)
Part F is advisory unless fire engineering or a s.42 modification makes the FSMP a condition:
missing items are FAIL in that case, CHECK otherwise.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
F = json.loads((HERE.parent / "fs-code" / "part_f.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"


def run(q):
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    mandatory = bool(q.get("fire_engineering") or q.get("s42_modification"))
    miss = FAIL if mandatory else WARN
    add("F4.1", "Status of FSMP", "condition of approval" if mandatory else "advisory",
        "FSMP forms part of approved GBP when FE / s.42 is used", INFO,
        "fire engineering" if q.get("fire_engineering") else ("s.42 modification" if q.get("s42_modification") else ""))

    plan = q.get("fsmp", {})
    trs = q.get("temporary_refuge_spaces", False)
    for part, spec in F["fsmp_parts"].items():
        have = set(plan.get(part, []))
        for key, text in spec["items"].items():
            if key == "final_fsar" and not q.get("fire_engineering"):
                continue
            if key in ("trs_locations", "trs_communication") and not trs:
                continue
            add(spec["clause"], f"{part.replace('_', ' ')}: {text}", "included" if key in have else "missing",
                "required in FSMP (F4.5)", PASS if key in have else miss)

    if q.get("fire_engineering"):
        bc = q.get("bounding_conditions", {})
        fe = F["fire_engineering"]
        for key, ok, fail_status in (
                ("bounding_conditions_in_gbp", bc.get("in_gbp"), FAIL),
                ("bounding_conditions_and_fsar_in_fsmp", bc.get("in_fsmp") and bc.get("fsar_in_fsmp"), FAIL),
                ("bounding_conditions_in_dmc", bc.get("in_dmc"), WARN)):
            add("F4.3", fe[key], "yes" if ok else "no", "required" if fail_status == FAIL else "where applicable",
                PASS if ok else fail_status)

    ok_ = q.get("open_kitchens", {})
    if ok_.get("provided"):
        have = set(ok_.get("conditions", []))
        for key, text in F["open_kitchen_conditions"]["items"].items():
            add("F5.8", f"Open kitchen: {text}", "in FSMP / DMC" if key in have else "missing", "required", PASS if key in have else FAIL)
        for where in ("in_fsmp", "in_dmc"):
            add("F5.8", f"Open kitchen conditions {where.replace('in_', 'in ').upper()}", "yes" if ok_.get(where) else "no",
                "incorporated (DMC where applicable)", PASS if ok_.get(where) else (FAIL if where == "in_fsmp" else WARN))

    uc = set(q.get("use_classes", []))
    if "drill_interval_months" in q:
        iv = q["drill_interval_months"]
        if "5b" in uc:
            lim = F["drill_frequency_months"]["5b"]
            add("F5.4(e) / Cap 279A r.38", "Fire drill interval (school)", f"{iv} months", f"≤ {lim} months",
                PASS if iv <= lim else FAIL)
        else:
            add("F6.3", "Fire drill interval", f"{iv} months", "regular intervals (no fixed period)",
                PASS if iv <= 12 else WARN, "≤ 12 months used as working benchmark, not a Code limit")
    elif "5b" in uc:
        add("Cap 279A r.38", "Fire drill interval (school)", "not stated", "≤ 6 months", WARN)

    lw = q.get("lift_works")
    if lw:
        L = F["lift_works"]
        n = lw.get("doors_open_max", 0)
        add("F5.7(b)", "Landing doors open at one time (per liftwell)", n, f"normally ≤ {L['max_doors_open_normal']}; absolute ≤ {L['max_doors_open_absolute']}",
            PASS if n <= L["max_doors_open_normal"] else (WARN if n <= L["max_doors_open_absolute"] else FAIL),
            "more than one: openings attended by lift workers, no hot work" if n > 1 else "")
        if n > 1:
            add("F5.7(b)(ii)", "Hot work / welding while >1 door open", "yes" if lw.get("hot_work") else "no", "not allowed",
                FAIL if lw.get("hot_work") else PASS)
        rem = lw.get("doors_removed", 0)
        if rem > L["max_doors_removed_without_hoarding"]:
            frr = lw.get("hoarding_integrity_min", 0)
            add("F5.7(d)", "Temporary hoarding integrity (>1 door removed)", f"-/{frr}/-", f"≥ -/{L['hoarding_integrity_min']}/-",
                PASS if frr >= L["hoarding_integrity_min"] else FAIL)
            vents = lw.get("vent_openings", [])
            big = [v["area_mm2"] for v in vents if v["area_mm2"] > L["vent_opening_max_mm2"]]
            add("F5.7(f)", "Hoarding vent opening area", f"max {max([v['area_mm2'] for v in vents], default=0)} mm²",
                f"≤ {L['vent_opening_max_mm2']} mm² each", FAIL if big else PASS)
            lim = min(L["vent_openings_max_per_hoarding"], L["vent_openings_max_per_liftway"] * lw.get("liftways", 1))
            add("F5.7(f)", "Number of hoarding vent openings", len(vents), f"≤ 2 per liftway, max 4 (= {lim})",
                PASS if len(vents) <= lim else FAIL)
            if any(not v.get("upper_portion", True) for v in vents):
                add("F5.7(f)", "Vent openings at upper portion", "no", "upper portion of hoarding", FAIL)
            for key, ref, text in (("hoarding_door_frr_ok", "F5.7(g)", "Hoarding door FRR ≥ hoarding"),
                                   ("hoarding_door_self_closing_openable_inside", "F5.7(g)", "Hoarding door self-closing, lockable, openable from inside without key")):
                add(ref, text, "yes" if lw.get(key) else "not stated", "required", PASS if lw.get(key) else WARN)
        for key, ref, text in (("temporary_works_non_combustible", "F5.7(i)", "Temporary works in liftwell non-combustible"),
                               ("openings_secured_when_unattended", "F5.7(j)", "Openings closed / hoarded when unattended")):
            add(ref, text, "yes" if lw.get(key) else "not stated", "required", PASS if lw.get(key) else WARN)

    aa = q.get("aa_works")
    if aa:
        have = set(aa.get("items", []))
        for key, text in F["aa_works"]["items"].items():
            add("F5.6", f"A&A works: {text}", "in method statement" if key in have else "missing", "observe", PASS if key in have else WARN)

    hk = q.get("housekeeping")
    if hk:
        for key, text in F["table_F1"].items():
            if key not in hk:
                continue
            v = str(hk[key]).lower()
            add(f"Table F1 {key}", text, v, "yes", PASS if v in ("yes", "n/a") else (FAIL if v == "no" else WARN),
                "follow-up action needed" if v == "no" else "")
        todo = [k for k in F["table_F1"] if k not in hk]
        if todo:
            add("Table F1", "Housekeeping items not yet inspected", f"{len(todo)} of {len(F['table_F1'])}",
                "all items inspected", WARN, ", ".join(todo))
    return rows


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # default Windows consoles cannot print the reports
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows = run(p["fire_safety_management"])
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out = [f"# Part F fire safety management check – {p.get('project', 'Untitled')}", "",
           f"**Result: {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).", "",
           "> Draft for review by an Authorized Person. FS Code 2011 (2024 Ed.) Part F is advisory unless the FSMP is a "
           "condition of fire engineering / s.42 approval; FSI maintenance is under Cap. 95B by a registered FSI contractor.", "",
           "| Clause | Item | Proposed | Limit | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
