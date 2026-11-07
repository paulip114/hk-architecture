#!/usr/bin/env python3
"""Part E checker – deemed-to-satisfy FRR of elements (Tables E2-E7) and
reaction-to-fire classes of linings (E13, E14, Table E1).
FS Code 2011 (2024 Ed.).

Usage:  python3 part_e_check.py project.json [-o report.md]   (reads the `part_e` block)

`part_e.elements[]`: {name, type (key in fs-code/part_e.json), required_frr (60/120/240),
  thickness_mm | size_mm | width_mm | waist_mm | protection_mm, cover_mm, continuous (bool)}
`part_e.linings[]`: {name, location: protected_exit_all | use_class_3_general | use_class_5a_auditoria,
  euro_class (A1..F) or bs476_class ("Class 0", "Class 1", ...)}
`part_e.products[]`: {name, test_report_lab_accredited (bool), standard}
Elements outside the tables need a test or assessment report (E16) – flagged CHECK.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
E = json.loads((HERE.parent / "fs-code" / "part_e.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"
DIM_KEYS = ["thickness_mm", "size_mm", "width_mm", "waist_mm", "protection_mm"]
BS_TO_EURO = {v: k for k, v in E["table_E1_euro_to_bs476"].items()}
# elements whose cover is starred (*) in Tables E4, E6, E7 at that FRR
STAR = {240: ("floor_rc", "floor_prestressed", "rc_beam", "prestressed_beam", "stair_rc"),
        120: ("rc_beam", "prestressed_beam")}


def run(q):
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    cols = E["frr_cols"]
    for el in q.get("elements", []):
        spec = E["elements"].get(el["type"])
        frr = el["required_frr"]
        if spec is None or frr not in cols:
            add("E16", f"{el['name']}", el["type"], f"FRR {frr} min", WARN,
                "Not in Tables E2-E7: needs HOKLAS lab test report or accredited assessment")
            continue
        i = cols.index(frr)
        tab = f"Table {spec['table']}"
        for k in DIM_KEYS:
            if k in spec:
                need = spec[k][i]
                if need is None:
                    add(tab, f"{el['name']} {k.replace('_mm', '')}", "-", f"no deemed-to-satisfy value for {frr} min", WARN,
                        "use test / assessment report (E16)")
                    break
                got = el.get(k, el.get("thickness_mm"))
                add(tab, f"{el['name']} {k.replace('_mm', '')} ({frr} min)", f"{got} mm", f"≥ {need} mm",
                    PASS if got is not None and got >= need else FAIL, spec.get("note", ""))
                break
        ckey = "cover_continuous_mm" if el.get("continuous") and "cover_continuous_mm" in spec else \
               "cover_simply_supported_mm" if "cover_simply_supported_mm" in spec else \
               "cover_mm" if "cover_mm" in spec else None
        if ckey and el.get("cover_mm") is not None:
            need = spec[ckey][i]
            add(tab, f"{el['name']} cover ({frr} min{', continuous' if el.get('continuous') else ''})",
                f"{el['cover_mm']} mm", f"≥ {need} mm", PASS if el["cover_mm"] >= need else FAIL,
                "starred cover in Code: add mesh / lath within 20 mm of face" if el["type"] in STAR.get(frr, ()) else "")

    order = E["class_order"]
    for ln in q.get("linings", []):
        need = E["lining_requirements"][ln["location"]]
        cls = ln.get("euro_class") or BS_TO_EURO.get(ln.get("bs476_class"))
        if cls is None:
            add("E13 / E14", ln["name"], "class not stated", f"Class {need} or better", WARN)
            continue
        add("E13.1 / E14.1", f"{ln['name']} ({ln['location'].replace('_', ' ')})", f"Class {cls}",
            f"Class {need} or better", PASS if order.index(cls) <= order.index(need) else FAIL)

    for pr in q.get("products", []):
        ok = pr.get("test_report_lab_accredited")
        add("E16.1-16.2", f"{pr['name']} certification", pr.get("standard", "-"),
            "HOKLAS / HKCAS-accredited test or assessment report", PASS if ok else WARN)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows = run(p["part_e"])
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    verdict = "does not comply" if fails else ("complies, subject to the items marked CHECK" if checks else "complies on the items checked")
    out = [f"# Part E fire properties check – {p.get('project', 'Untitled')}", "",
           f"**Result: {verdict}** ({fails} fail, {checks} to check, {len(rows)} items).", "",
           "> Draft for review by an Authorized Person / RSE. Deemed-to-satisfy values from FS Code 2011 (2024 Ed.) "
           "Tables E2-E7; anything else needs an accredited test or assessment report.", "",
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
