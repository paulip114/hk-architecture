#!/usr/bin/env python3
"""Contract administration calculator for HK private building contracts (SFBC 2005 / 2006 forms).

Usage:  python3 contract_admin.py project.json [-o report.md] [--as-of YYYY-MM-DD]   (reads the `contract` block)

`contract` fields:
  form ("SFBCwQ.2005" / "SFBCnQ.2006"), contract_sum, possession_date, completion_date (original),
  ld_per_day (HK$, Appendix), ld_cap (optional HK$), retention_pct (default 10 if blank, cl. 32.4),
  retention_limit_pct (of contract sum), dlp_months (Appendix),
  substantial_completion_date (actual or forecast), drc_date (optional),
  certified_gross_to_date (optional HK$ gross valuation for retention held),
  eots[]: {ref, event, days, granted (bool), particulars_dates[] (ISO dates, cl. 25.2(3)(b) <= 28 days apart)},
  instructions[]: {ref, oral_date, confirmed_date}       (cl. 4.2(1) 5 days)
  claims[]: {ref, notice_date, particulars_date}         (cl. 28.2(2) 60 days)
  cispo: true when CISPO (Cap. 652) applies (contract on/after 2025-08-28, above threshold); then
  payment_claims[]: {ref, served, claimed, response_date, admitted, paid_date, paid,
                     response_days (contract, ≤ 30), payment_days (contract, ≤ 60)}
Exit code 1 when any notice check fails. Periods and clause numbers from contracts/sfbc.json.
The results are a draft for the Architect / QS to check against the signed contract and its Appendix.
"""
import argparse
import calendar
import json
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = json.loads((HERE.parent / "contracts" / "sfbc.json").read_text(encoding="utf-8"))
P = S["periods"]
FORM_NOTE = {
    "default": "Clause numbers from SFBCwQ.2005 (rev. 2023).",
    "SFBC.2025": "Periods used here are the same in the 2025 Edition, checked against a pre-launch copy; see sfbc_2025 in contracts/sfbc.json.",
}
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"


def d(s):
    return date.fromisoformat(s) if s else None


def add_months(x, m):
    y, mo = divmod(x.month - 1 + m, 12)
    y += x.year
    mo += 1
    return date(y, mo, min(x.day, calendar.monthrange(y, mo)[1]))


def money(v):
    return f"HK${v:,.0f}"


def run(c, as_of=None):
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    as_of = as_of or date.today()
    total = c.get("contract_sum")
    comp0 = d(c["completion_date"])
    poss = d(c.get("possession_date"))
    if poss:
        add("23", "Contract period", f"{(comp0 - poss).days} days", f"{poss} to {comp0}", INFO)

    granted = sum(e["days"] for e in c.get("eots", []) if e.get("granted"))
    pending = sum(e["days"] for e in c.get("eots", []) if not e.get("granted"))
    comp = comp0 + timedelta(days=granted)
    add("25", "Extended Completion Date", str(comp), f"{granted} days granted", INFO,
        f"{pending} days claimed, not yet granted" if pending else "")

    gap = timedelta(days=P["eot_further_particulars_interval_days"]["days"])
    for e in c.get("eots", []):
        ds = sorted(d(x) for x in e.get("particulars_dates", []))
        worst = max(((b - a).days for a, b in zip(ds, ds[1:])), default=0)
        if len(ds) > 1:
            add("25.2(3)(b)", f"{e['ref']} particulars interval ({e.get('event', '')})", f"max {worst} days",
                f"≤ {gap.days} days", PASS if worst <= gap.days else FAIL)

    sc = d(c.get("substantial_completion_date"))
    ld = 0
    if sc:
        late = max(0, (sc - comp).days)
        ld = late * c.get("ld_per_day", 0)
        cap = c.get("ld_cap")
        note = ""
        if cap is not None and ld > cap:
            ld, note = cap, "capped at Appendix limit"
        add("24", "Delay beyond extended Completion Date", f"{late} days", f"SC {sc}", WARN if late else PASS,
            "Architect issues certificate of non-completion; check pending EOT claims first" if late else "")
        if late:
            add("24", "Liquidated damages", money(ld), f"{money(c.get('ld_per_day', 0))}/day", INFO,
                note or "deduct only after the non-completion certificate; recompute if further EOT is granted")
        if pending and late:
            add("25", "Pending EOT", f"{pending} days", "assess before deducting LD", WARN,
                f"if all granted, LD falls to {money(max(0, late - pending) * c.get('ld_per_day', 0))}")

    pct = c.get("retention_pct") or P["retention_default_pct"]["value"]
    if not c.get("retention_pct"):
        add("32.4", "Retention rate", "not stated", "default 10%", WARN, "Appendix blank: 10% applies by default")
    if total:
        limit = total * c["retention_limit_pct"] / 100 if c.get("retention_limit_pct") else None
        gross = c.get("certified_gross_to_date", total)
        held = gross * pct / 100
        if limit is not None:
            held = min(held, limit)
        add("32.4", "Retention held", money(held), f"{pct}% of {money(gross)}" + (f", limit {money(limit)}" if limit else ""), INFO)
        if sc:
            r1 = sc + timedelta(days=P["half_retention_release_days"]["days"])
            add("32.5(2)", "Release ½ retention", f"{money(held / 2)} by {r1}", "≤ 14 days after SC Certificate", INFO)
    if sc and c.get("dlp_months"):
        dlp_end = add_months(sc, c["dlp_months"])
        add("17", "Defects Liability Period ends", str(dlp_end), f"{c['dlp_months']} months from SC", INFO,
            "issue schedule of defects at the end of DLP")
        drc = d(c.get("drc_date"))
        if drc and total:
            add("32.5(4)", "Release balance of retention", f"{money(held / 2)} by {drc + timedelta(days=14)}",
                "≤ 14 days after DRC", INFO)
        add("32.8(1)", "Final Certificate", "after DRC", "as soon as practicable", INFO)

    lim5 = P["oral_instruction_confirm_days"]["days"]
    for i in c.get("instructions", []):
        o, cf = d(i["oral_date"]), d(i.get("confirmed_date"))
        if cf is None:
            late = (as_of - o).days > lim5
            add("4.2(1)", f"{i['ref']} oral instruction confirmed", "not yet", f"≤ {lim5} days", FAIL if late else WARN)
        else:
            n = (cf - o).days
            add("4.2(1)", f"{i['ref']} oral instruction confirmed", f"{n} days", f"≤ {lim5} days", PASS if n <= lim5 else FAIL)

    lim60 = P["claim_particulars_days"]["days"]
    for cl in c.get("claims", []):
        nd, pd = d(cl["notice_date"]), d(cl.get("particulars_date"))
        due = nd + timedelta(days=lim60)
        if pd is None:
            add("28.2(2)", f"{cl['ref']} claim particulars", "not yet", f"due {due}", FAIL if as_of > due else WARN)
        else:
            add("28.2(2)", f"{cl['ref']} claim particulars", f"{(pd - nd).days} days", f"≤ {lim60} days",
                PASS if pd <= due else FAIL, "late particulars may bar the claim (check wording)" if pd > due else "")
    sop = S["cispo"]
    if c.get("cispo"):
        if d(c.get("contract_date")) and d(c["contract_date"]) < date(2025, 8, 28):
            add("Cap. 652", "CISPO applicability", c["contract_date"], "contracts from 2025-08-28", WARN,
                "contract predates CISPO: payment checks shown for reference only")
        for pc in c.get("payment_claims", []):
            sv = d(pc["served"])
            rd = min(pc.get("response_days", 30), sop["payment_response_max_days"])
            pdays = min(pc.get("payment_days", 60), sop["payment_deadline_max_days"])
            r_due, p_due = sv + timedelta(days=rd), sv + timedelta(days=pdays)
            resp = d(pc.get("response_date"))
            if resp is None:
                st = FAIL if as_of > r_due else WARN
                add("Cap. 652", f"{pc['ref']} payment response", "none", f"by {r_due}", st,
                    "no response: set-off (e.g. LD) cannot be raised in adjudication" if st == FAIL else "")
            else:
                add("Cap. 652", f"{pc['ref']} payment response", str(resp), f"by {r_due} (≤ {rd} days)",
                    PASS if resp <= r_due else FAIL, "" if resp <= r_due else "late: set-off cannot be raised in adjudication")
            due = pc.get("admitted", pc.get("claimed"))
            paid = pc.get("paid", 0)
            pd = d(pc.get("paid_date"))
            if due is not None:
                short = due - paid if (pd and pd <= p_due) else (due if as_of > p_due else 0)
                if short > 0:
                    add("Cap. 652", f"{pc['ref']} admitted amount paid", money(paid), f"{money(due)} by {p_due}", FAIL,
                        f"claimant may refer to adjudication within {sop['adjudication_referral_days']} days and may suspend "
                        f"on {sop['suspension_notice_working_days']} working days' notice")
                elif pd or as_of > p_due:
                    add("Cap. 652", f"{pc['ref']} admitted amount paid", money(paid), f"by {p_due}", PASS)
                else:
                    add("Cap. 652", f"{pc['ref']} payment deadline", "-", str(p_due), INFO)
            if pc.get("claimed") is not None and pc.get("admitted") is not None and pc["admitted"] < pc["claimed"]:
                add("Cap. 652", f"{pc['ref']} disputed amount", money(pc["claimed"] - pc["admitted"]), "claimed − admitted", INFO,
                    f"adjudication referral window {sop['adjudication_referral_days']} days (CIC timeline: days 61-88 after the claim); "
                    "pay-when-paid terms are void")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    ap.add_argument("--as-of", help="date for outstanding-notice checks (default today)")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    rows = run(p["contract"], d(a.as_of))
    fails = sum(1 for r in rows if r[4] == FAIL)
    checks = sum(1 for r in rows if r[4] == WARN)
    out = [f"# Contract administration – {p.get('project', 'Untitled')}", "",
           f"**{fails} notice failures, {checks} items to check** ({len(rows)} items, form {p['contract'].get('form', 'SFBCwQ.2005')}).", "",
           "> Draft for the Architect / QS. " + FORM_NOTE.get(p["contract"].get("form"), FORM_NOTE["default"]) +
           " Check against the signed contract, its Appendix and any special conditions. Not legal advice.", "",
           "| Clause | Item | Value | Basis | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
