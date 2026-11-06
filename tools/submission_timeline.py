#!/usr/bin/env python3
"""BD submission timeline and procedural checks (plans, consent, amendments, OP, minor works, MBIS).

Reads the `submission` block of project.json and submission/periods.json.
Dates are ISO (YYYY-MM-DD). Periods end on start date + N, because Cap. 1 s.71(1)(a) excludes the
start day. A statutory period of days whose last day is a Sunday, a listed general holiday or a day in
`warning_days` moves to the next day that is none of these (s.71(1)(b)). PNAP and BD targets do not move,
and neither do periods in months. submission/hk_holidays.json lists general holidays; later years move for
Sundays only. No statutory period in this tool is 6 days or less, so s.71(1)(d) does not arise. Periods were checked against Cap. 123 (version
1.3.2026) and Cap. 123A (version 30.6.2024); any left unverified are marked "(unverified)".

Usage: python3 submission_timeline.py project.json [-o report.md]

submission:
  warning_days[]: gale or black rainstorm warning days that fall on a last day
  as_of: date (default today)
  submissions[]: id, kind (GBP / structural / foundation / drainage / site_formation / A&A),
      type (first | resubmission | major_revision | amendment (reg 33, works already consented) |
            fast_track_aa | fast_track_cladding | warehouse_2storey),
      date, optional wr_dates[] (withdraw-and-resubmit letters), result (approved | disapproved),
      result_date, stage ("I" / "II" / "III" for staged curtailed check)
  consents[]: id, applied, concurrent (bool, BA8A), approval_date (plans), granted,
      foundation_beyond_spread_footing (bool), spread_footing_depth_m, precautionary_works (bool),
      reg8_plans_complete (bool), supervision_plan (bool)
  commencement: date, ba10_date, tcp_notice_date (if supervision plan needs TCPs)
  completion: date, rc_cert_date, ap_cert_date
  amendments[]: id, approved (bool), works_started (bool), drainage_excavation_depth_m,
      non_ldbp_pile_increase_pct, ldbp_pile_increase_pct, site_formation_level_change_m,
      retained_height_change_m, treated_as_minor (bool)
  op: applied, wr_dates[], superstructure_consent_date, first_gbp_date,
      prereq {all_amendments_approved, plans_tally, stage_iii_done, bd106_in_plans,
              gfa_summary, consolidated_digital_file, minor_works_in_plans}
  minor_works[]: item, class (I/II/III), notice_date, commence, complete, cert_date
  mbis: building_age_years, storeys, domestic_only (bool), inspection_date, report_date
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = json.loads((HERE.parent / "submission" / "periods.json").read_text(encoding="utf-8"))
PER, LIM, NMA = P["periods"], P["limits"], P["not_minor_amendment_thresholds"]
HOLIDAYS = json.loads((HERE.parent / "submission" / "hk_holidays.json").read_text(encoding="utf-8"))
CAP123N_PERIODS = {"mw_completion_after", "mbis_report_after_inspection"}  # Cap. 123N and Cap. 123P, though the ref cites BD
WARNING_DAYS = set()
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"


def d(s):
    return dt.date.fromisoformat(s) if s else None


def add_months(day, n):
    m = day.month - 1 + n
    y, m = day.year + m // 12, m % 12 + 1
    last = [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return dt.date(y, m, min(day.day, last))


def is_statutory(key):
    """Cap. 1 s.71 applies to periods set by an Ordinance or its subsidiary legislation, not to PNAP or BD targets."""
    return PER[key].get("ref", "").startswith(("B(A)R", "BO ")) or key in CAP123N_PERIODS


def rolled(day, warning_days=()):
    """Cap. 1 s.71(1)(b): a last day on a public holiday or warning day moves to the next day that is neither."""
    while day.weekday() == 6 or day.isoformat() in HOLIDAYS["general_holidays"] or day.isoformat() in warning_days:
        day += dt.timedelta(days=1)
    return day


def plus(start, key):
    if PER[key].get("months"):
        return add_months(start, PER[key]["months"])  # s.71(1)(b) follows on from "a period of days" in (a)
    due = start + dt.timedelta(days=PER[key]["days"])
    return rolled(due, WARNING_DAYS) if is_statutory(key) else due


def tag(key):
    return "" if PER[key]["verified"] else " (unverified)"


def ref(key):
    return PER[key]["ref"] + tag(key)


def status_due(due, done, today):
    if done:
        return (PASS if done <= due else WARN), f"result {done} ({'within' if done <= due else 'after'} period)"
    if today > due:
        return WARN, f"period expired {(today - due).days} d ago with no result recorded: chase BD"
    return INFO, f"{(due - today).days} d left"


def check(sub):
    out = []
    add = lambda sec, item, st, note, r="": out.append((sec, item, st, note, r))
    today = d(sub.get("as_of")) or dt.date.today()
    WARNING_DAYS.clear()
    WARNING_DAYS.update(sub.get("warning_days", []))

    # Plans
    for s in sub.get("submissions", []):
        sec = f"Plans {s.get('id', '')} ({s.get('kind', '')})"
        typ = s.get("type", "first")
        key = {"first": "gbp_first", "resubmission": "gbp_resubmission", "major_revision": "gbp_major_revision"}.get(typ, typ)
        if key not in PER:
            add(sec, "type", WARN, f"unknown type {typ}")
            continue
        start = d(s["date"])
        wrs = [d(x) for x in s.get("wr_dates", [])]
        n = len(wrs)
        lim = LIM["wr_max_times"]["value"]
        if n:
            start = max(wrs)
            add(sec, "Withdrawal and resubmission", FAIL if n > lim else PASS,
                f"{n} W&R; period restarts from {start}; limit generally {lim}", LIM["wr_max_times"]["ref"])
        due = plus(start, key)
        st, note = status_due(due, d(s.get("result_date")), today)
        add(sec, f"Refusal due by {due} ({PER[key]['days']} d from {start})", st,
            note + ("; no refusal by then = deemed approval (BO s.15(1))" if key.startswith("gbp") and not s.get("result_date") else ""), ref(key))
        if typ == "resubmission" and not s.get("result_date"):
            add(sec, "Major revision?", INFO, f"if BA says it is a major revision (notice by {plus(start, 'major_revision_notice')}), the period is 60 d",
                ref("major_revision_notice"))
        if typ == "first" and not s.get("result_date"):
            q = plus(start, "enquiry_45th_day")
            add(sec, f"45th-day enquiry {q}", INFO if today <= q else WARN,
                "ask case officer whether fundamentally acceptable" + ("" if today <= q else " (date passed)"),
                ref("enquiry_45th_day"))
        if s.get("result") == "disapproved":
            add(sec, "Disapproved", INFO, "reply to every item (submission/templates/reply-to-bd-comments.md); new items generally not added on resubmission",
                "PNAP ADM-2")
        if s.get("kind") == "GBP" and typ == "first" and start > d(LIM["staged_check_after"]["value"]):
            add(sec, "Staged curtailed check", INFO, "Stage II before superstructure consent, Stage III before OP/TOP",
                LIM["staged_check_after"]["ref"])

    # Consent
    for c in sub.get("consents", []):
        sec = f"Consent {c.get('id', '')}"
        applied, appr = d(c.get("applied")), d(c.get("approval_date"))
        if c.get("concurrent"):
            maxd = LIM["concurrent_consent_max_footing_depth_m"]["value"]
            probs = []
            if c.get("foundation_beyond_spread_footing"):
                probs.append("foundation other than spread footings")
            if (c.get("spread_footing_depth_m") or 0) > maxd:
                probs.append(f"footing excavation {c['spread_footing_depth_m']} m > {maxd} m")
            if c.get("precautionary_works"):
                probs.append("precautionary works needed before commencement")
            if c.get("reg8_plans_complete") is False:
                probs.append("reg 8 plans not all submitted")
            if c.get("supervision_plan") is False:
                probs.append("supervision plan / hoarding plans missing")
            add(sec, "Concurrent consent (BA8A) criteria", FAIL if probs else PASS,
                "; ".join(probs) or "criteria met", LIM["concurrent_consent_max_footing_depth_m"]["ref"])
        start = max([x for x in (applied, appr) if x], default=None)
        if not start:
            add(sec, "dates", WARN, "no application / approval date")
            continue
        due = plus(start, "consent")
        st, note = status_due(due, d(c.get("granted")), today)
        add(sec, f"Consent due {due} (28 d from {start})", st, note, ref("consent"))
        g = d(c.get("granted"))
        if g:
            lapse = plus(g, "consent_lapse")
            cm_date = d((sub.get("commencement") or {}).get("date"))
            if cm_date and cm_date > lapse:
                add(sec, "Consent lapse", FAIL, f"works commenced {cm_date}, after {lapse}: consent deemed revoked, renew with BA9", ref("consent_lapse"))
            elif not cm_date:
                add(sec, f"Commence by {lapse}", FAIL if today > lapse else INFO,
                    "consent deemed revoked: renew with BA9" if today > lapse else "or consent is deemed revoked", ref("consent_lapse"))

    # Commencement
    cm = sub.get("commencement")
    if cm:
        start, ba10 = d(cm.get("date")), d(cm.get("ba10_date"))
        granted = [d(c["granted"]) for c in sub.get("consents", []) if c.get("granted")]
        if start and not granted:
            add("Commencement", "Consent before works", FAIL, "works commenced with no consent recorded", "BO s.14(1) (unverified)")
        elif start and granted and start < min(granted):
            add("Commencement", "Consent before works", FAIL, f"works {start} before consent {min(granted)}", "BO s.14(1) (unverified)")
        elif start:
            add("Commencement", "Consent before works", PASS, f"works {start}, consent {min(granted)}", "BO s.14(1) (unverified)")
        if start and ba10:
            gap = (start - ba10).days
            need = PER["ba10_before_commencement"]["days"]
            add("Commencement", "BA10 notice", PASS if gap >= need else FAIL,
                f"BA10 {gap} d before commencement (need not less than {need} d)", ref("ba10_before_commencement"))
        tcp = d(cm.get("tcp_notice_date"))
        if start and tcp:
            gap = (start - tcp).days
            need = PER["tcp_notice_before"]["days"]
            add("Commencement", "TCP appointment notice", PASS if gap >= need else FAIL,
                f"{gap} d before commencement (need not less than {need} d)", ref("tcp_notice_before"))

    # Completion certificates
    cp = sub.get("completion")
    if cp and cp.get("date"):
        done = d(cp["date"])
        for k, key, who in (("rc_cert_date", "rc_completion_cert", "RC certificate to AP"),
                            ("ap_cert_date", "ap_completion_cert", "AP certificate to BA")):
            due = plus(done, key)
            got = d(cp.get(k))
            if got:
                add("Completion", who, PASS if got <= due else FAIL, f"{got}, due {due}", ref(key))
            else:
                add("Completion", f"{who} due {due}", FAIL if today > due else INFO, "", ref(key))

    # Amendments
    for a in sub.get("amendments", []):
        sec = f"Amendment {a.get('id', '')}"
        hits = []
        for k, lim in (("drainage_excavation_depth_m", "drainage_excavation_depth_m"),
                       ("non_ldbp_pile_increase_pct", "non_ldbp_pile_increase_pct"),
                       ("ldbp_pile_increase_pct", "ldbp_pile_increase_pct"),
                       ("site_formation_level_change_m", "site_formation_level_change_m"),
                       ("retained_height_change_m", "retained_height_change_m")):
            if a.get(k) is not None and a[k] > NMA[lim]:
                hits.append(f"{k} {a[k]} > {NMA[lim]}")
        if hits:
            add(sec, "Minor amendment status", FAIL if a.get("treated_as_minor") else INFO,
                "not minor: " + "; ".join(hits) + (" (but treated as minor)" if a.get("treated_as_minor") else ": submit amendment plans"),
                NMA["_ref"])
        if a.get("works_started") and not a.get("approved") and not (a.get("treated_as_minor") and not hits):
            add(sec, "Approval before works", FAIL, "amended works started before approval", "BO s.14(1) (unverified)")

    # OP
    op = sub.get("op")
    if op:
        pre = op.get("prereq", {})
        labels = {
            "all_amendments_approved": "approval and consent for all amendments (ADM-19 para 3)",
            "plans_tally": "latest GBP / structural / drainage / site formation plans tally (ADM-19 para 3)",
            "stage_iii_done": "Stage III curtailed check done (ADM-19 para 14)",
            "bd106_in_plans": "BD106 conditions in amendment plans + checklist (ADM-2 App F1)",
            "gfa_summary": "GFA and car parking summary (ADM-2 App H)",
            "consolidated_digital_file": "consolidated digital file of approved revisions (ADM-19 para 25)",
            "minor_works_in_plans": "qualifying minor works shown in plans (ADM-19 para 41)",
        }
        sc = d(op.get("superstructure_consent_date"))
        fg = d(op.get("first_gbp_date"))
        for k, lab in labels.items():
            if k == "minor_works_in_plans" and sc and sc <= d(LIM["mw_in_plans_before_op_consent_after"]["value"]):
                continue
            if k == "stage_iii_done" and fg and fg <= d(LIM["staged_check_after"]["value"]):
                continue
            v = pre.get(k)
            add("OP / TOP", lab, PASS if v else (FAIL if v is False else WARN), "" if v else ("not done" if v is False else "not stated"))
        if op.get("applied"):
            start = d(op["applied"])
            wrs = [d(x) for x in op.get("wr_dates", [])]
            if wrs:
                start = max(wrs)
                lim = LIM["wr_max_times"]["value"]
                add("OP / TOP", "W&R", FAIL if len(wrs) > lim else PASS, f"{len(wrs)} W&R; limit generally {lim}", LIM["wr_max_times"]["ref"])
            due = plus(start, "op")
            st, note = status_due(due, d(op.get("issued")), today)
            add("OP / TOP", f"Refusal due by {due}", st,
                note + ("; no refusal served by then = permit deemed granted (s.21(7))" if not op.get("issued") else ""), ref("op"))

    # Minor works
    for m in sub.get("minor_works", []):
        sec = f"Minor works: {m.get('item', '')} (Class {m.get('class')})"
        cls = str(m.get("class", "")).upper()
        com, notice, comp, cert = (d(m.get(k)) for k in ("commence", "notice_date", "complete", "cert_date"))
        if cls in ("I", "II"):
            if com and notice:
                gap = (com - notice).days
                need = PER["mw_notice_before"]["days"]
                add(sec, f"Notice {'MW01' if cls == 'I' else 'MW03'}", PASS if gap >= need else FAIL,
                    f"{gap} d before commencement (need {need})", ref("mw_notice_before"))
            elif com:
                add(sec, "Notice", FAIL, "no commencement notice recorded", ref("mw_notice_before"))
            elif notice:
                add(sec, "Earliest commencement", INFO, str(notice + dt.timedelta(days=PER["mw_notice_before"]["days"])), ref("mw_notice_before"))
        form = {"I": "MW02", "II": "MW04", "III": "MW05"}.get(cls, "?")
        if comp:
            due = plus(comp, "mw_completion_after")
            if cert:
                add(sec, f"Completion {form}", PASS if cert <= due else FAIL, f"submitted {cert}, due {due}", ref("mw_completion_after"))
            else:
                add(sec, f"Completion {form} due {due}", FAIL if today > due else INFO,
                    "overdue" if today > due else f"{(due - today).days} d left", ref("mw_completion_after"))
        if cls == "I":
            add(sec, "Appointments", INFO, "PBP + PRC; supervision plan (SP / PR5) on site", "BD minor works procedures")

    # MBIS / MWIS
    mb = sub.get("mbis")
    if mb:
        age = mb.get("building_age_years", 0)
        exempt = mb.get("domestic_only") and mb.get("storeys", 99) <= LIM["mbis_mwis_exempt_domestic_max_storeys"]["value"]
        for name, key in (("MBIS", "mbis_building_age_years"), ("MWIS", "mwis_building_age_years")):
            lim = LIM[key]["value"]
            if exempt:
                add("MBIS / MWIS", name, INFO, "domestic building of 3 storeys or less: excluded", LIM[key]["ref"])
            else:
                add("MBIS / MWIS", name, INFO, f"age {age} >= {lim}: liable once served with statutory notice" if age >= lim else f"age {age} < {lim}: not yet liable", LIM[key]["ref"])
        ins, rep = d(mb.get("inspection_date")), d(mb.get("report_date"))
        if ins:
            due = plus(ins, "mbis_report_after_inspection")
            if rep:
                add("MBIS / MWIS", "RI report", PASS if rep <= due else FAIL, f"submitted {rep}, due {due}", ref("mbis_report_after_inspection"))
            else:
                add("MBIS / MWIS", f"RI report due {due}", FAIL if today > due else INFO, "", ref("mbis_report_after_inspection"))
    return out, today


def report(rows, today, name):
    lines = [f"# BD submission timeline: {name}", "", f"As of {today}. Draft for AP review. Statutory last days move under Cap. 1 s.71(1)(b) for Sundays, general holidays listed to {HOLIDAYS['covered_to_year']} and any warning_days given. Periods marked (unverified) are not yet checked against Cap. 123 / Cap. 123A.", ""]
    fails = [r for r in rows if r[2] == FAIL]
    checks = [r for r in rows if r[2] == WARN]
    lines.append(f"**Summary:** {len(fails)} FAIL, {len(checks)} CHECK, {len(rows)} items.")
    lines.append("")
    sec = None
    for s, item, st, note, r in rows:
        if s != sec:
            lines += ["", f"## {s}", "", "| Item | Result | Note | Source |", "| --- | --- | --- | --- |"]
            sec = s
        lines.append(f"| {item} | {st} | {note} | {r} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    data = json.loads(Path(a.project).read_text(encoding="utf-8"))
    sub = data.get("submission")
    if not sub:
        sys.exit("no `submission` block")
    rows, today = check(sub)
    md = report(rows, today, data.get("name", Path(a.project).stem))
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    else:
        print(md)
    sys.exit(1 if any(r[2] == FAIL for r in rows) else 0)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")  # reports contain Chinese and symbols
    main()
