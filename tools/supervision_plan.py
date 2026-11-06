#!/usr/bin/env python3
"""Site supervision plan helper – Code of Practice for Site Supervision 2009 (2024 Ed.) and the
Technical Memorandum for Supervision Plans 2009.

Usage:  python3 supervision_plan.py project.json [-o report.md]   (reads the `supervision` block)

`supervision` fields:
  works[]: {type (key of scale_basic_values in supervision/supervision.json), value (in that key's unit),
            months (duration of that work)}
  tcps[]: {stream (AS/AP/RSE/RGE), grade (T1-T5), name, frequency_level (1-5, from TM Table 1),
           works[] (types covered), qualification (text, optional)}
  dates: {consent_application, plan_submitted, commencement, tcp_confirmed}   ISO dates, any may be blank
  minor_works: true for minor works under the simplified requirements
  geotechnical: true when the works have significant geotechnical content
Produces: scale factor per work type (capped at 2), inspection effort per TCP, submission timing checks,
TM Table 1 minimum grade and frequency per stream (supervision/supervision.json `tm_table1`), and a draft
supervision plan schedule. Each work maps to a TM row by `work_type_to_tm_row` (override with work `tm_row`:
gi_field_works / geotech_foundation / geotech_others / foundation / all_other / minor_class1 ...).
  streams_appointed: optional list, default AS, AP, RSE (+ RGE when geotechnical)
"""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = json.loads((HERE.parent / "supervision" / "supervision.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"
HOURS_PER_DAY = 8  # assumed full working day for a factor-1 visit (CoP 8.7 says "full day")


def d(s):
    return date.fromisoformat(s) if s else None


def run(q):
    rows, sched = [], []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    basic = S["scale_basic_values"]
    cap = S["scale_factor_cap"]
    factors = {}
    for w in q.get("works", []):
        b = basic.get(w["type"])
        if not b:
            add("Table 8.1", w["type"], "-", "-", WARN, "work type not in Table 8.1 list")
            continue
        raw = w["value"] / b["basic"]
        f = min(raw, cap)
        factors[w["type"]] = (f, w.get("months"))
        add("8.4-8.5 / Table 8.1", f"Scale factor – {w['type'].replace('_', ' ')}",
            f"{w['value']:,} {b['unit']} / {b['basic']:,} = {raw:.2f}", f"cap {cap}", INFO,
            "capped" if raw > cap else ("shorter visits allowed, same frequency" if f < 1 else ""))

    for t in q.get("tcps", []):
        g = S["tcp_grades"].get(t["grade"])
        lvl = S["frequency_levels"].get(str(t["frequency_level"]))
        if g is None or lvl is None:
            add("TM", t.get("name", t["grade"]), t["grade"], "T1-T5, level 1-5", FAIL, "unknown grade or level")
            continue
        ws = t.get("works", [])
        f = max((factors.get(w, (1, None))[0] for w in ws), default=1)
        if lvl["visits_per_month"] is None:
            effort = "full-time on site"
        elif lvl["visits_per_month"] == 0:
            effort = "as and when required"
        else:
            hrs = lvl["visits_per_month"] * HOURS_PER_DAY * f
            effort = f"{lvl['visits_per_month']:g} visits/month × {HOURS_PER_DAY * f:.1f} h ≈ {hrs:.0f} h/month"
        sched.append((t["stream"], t["grade"], t.get("name", "(to be named)"), ", ".join(w.replace("_", " ") for w in ws),
                      f"Level {t['frequency_level']}: {lvl['text']}", effort, t.get("qualification", g["min"])))
        if t["grade"] in ("T4", "T5") and t["frequency_level"] == 5 and t["stream"] in ("AP", "AS"):
            add("TM Table 1", f"{t.get('name', t['grade'])} {t['stream']} {t['grade']} full-time", "level 5", "check TM", WARN,
                "full-time T4/T5 is unusual in AP/AS streams; confirm against TM Table 1")

    # TM Table 1: each required (stream, grade, level) must be met by a TCP of that stream covering the work,
    # with grade >= required grade and frequency level >= required level (higher grade assumed acceptable).
    tm = S["tm_table1"]
    appointed = set(q.get("streams_appointed") or (["AS", "AP", "RSE"] + (["RGE"] if q.get("geotechnical") else [])))
    order = ["T1", "T2", "T3", "T4", "T5"]
    for w in q.get("works", []):
        wt = w["type"]
        row_key = w.get("tm_row") or S["work_type_to_tm_row"].get(wt)
        if q.get("geotechnical") and wt in S["geotech_types"] and not w.get("tm_row"):
            row_key = S["geotech_switch"].get(row_key, row_key)
        row = tm.get(row_key)
        if row is None:
            add("TM Table 1", f"Row for {wt}", "-", "-", WARN, "no TM Table 1 row mapped; give `tm_row`")
            continue
        for stream in ("AS", "AP", "RSE", "RGE"):
            req = row.get(stream)
            if not req:
                continue
            if stream not in appointed:
                add("TM Table 1", f"{wt.replace('_', ' ')} – {stream} stream", "not appointed", row["label"], INFO,
                    "stream not in streams_appointed; confirm it is not needed")
                continue
            have = [t for t in q.get("tcps", []) if t["stream"] == stream and wt in t.get("works", [])]
            free = sorted(have, key=lambda t: (order.index(t["grade"]), t["frequency_level"]))
            # each required grade needs its own TCP: fill the highest grade first, using the lowest TCP that fits
            for grade, lvl in sorted(((g, l) for g, l in req.items() if g != "principal"),
                                     key=lambda x: -order.index(x[0])):
                ok = [t for t in free if order.index(t["grade"]) >= order.index(grade) and t["frequency_level"] >= lvl]
                if ok:
                    free.remove(ok[0])
                status = PASS if ok else FAIL
                note = "" if ok else "no TCP of this grade (or higher) at this frequency"
                if row.get("uncertain"):
                    status, note = WARN, row["uncertain"]
                add(f"TM Table 1 ({row_key})", f"{wt.replace('_', ' ')} – {stream} {grade}",
                    ", ".join(f"{t['grade']} L{t['frequency_level']}" for t in have) or "none",
                    f"{grade} at level {lvl} ({S['frequency_levels'][str(lvl)]['text']})", status, note)

    dt = q.get("dates", {})
    ps, ca, cm, tc = d(dt.get("plan_submitted")), d(dt.get("consent_application")), d(dt.get("commencement")), d(dt.get("tcp_confirmed"))
    if q.get("minor_works"):
        if ps and cm:
            n = (cm - ps).days
            add("CoP 4.4", "Plan submitted before commencement (minor works)", f"{n} days", "≥ 7 days", PASS if n >= 7 else FAIL)
    elif ps and ca:
        add("CoP 4.1 / 4.4", "Plan submitted with or before consent application", str(ps), f"≤ {ca}", PASS if ps <= ca else FAIL)
    elif ca and not ps:
        add("CoP 4.1 / 4.4", "Supervision plan", "not submitted", f"by {ca}", WARN)
    if cm:
        due = cm + timedelta(days=7)
        if tc:
            add("CoP 4.5", "TCP appointments confirmed", str(tc), f"≤ {due} (7 days after commencement)", PASS if tc <= due else FAIL)
        else:
            add("CoP 4.5", "TCP appointments confirmed", "not yet", f"annex to plan or by {due}", WARN)
    if q.get("geotechnical"):
        streams = {(t["stream"], t["grade"]) for t in q.get("tcps", [])}
        ok = ("RGE", "T3") in streams and ("RGE", "T5") in streams
        add("CoP 7.3", "RGE stream T3 + T5 for geotechnical works", "yes" if ok else "no", "normally both", PASS if ok else WARN)
    return rows, sched


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows, sched = run(p["supervision"])
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    out = [f"# Site supervision plan – {p.get('project', 'Untitled')}", "",
           f"**{fails} fail, {checks} to check** ({len(rows)} items).", "",
           "> Draft for the AP / RSE / RGE / AS. Grades and frequencies must match Table 1 of the Technical Memorandum for "
           "Supervision Plans 2009 (encoded from an automated read; check against the TM). A higher grade is assumed to satisfy a lower one. Effort assumes a visit of 8 h × scale factor (CoP 8.7). Use the BD standard form of supervision plan (CoP Appendix I).", "",
           "| Ref | Item | Value | Requirement | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    out += ["", "## Draft TCP schedule", "",
            "| Stream | Grade | Name | Works | Frequency | Effort | Qualification |",
            "| --- | --- | --- | --- | --- | --- | --- |"]
    out += ["| " + " | ".join(str(x) for x in s) + " |" for s in sched]
    out += ["", "## Standing duties (CoP)", ""] + [f"- {r['ref']}: {r['text']}" for r in S["rules"]]
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
