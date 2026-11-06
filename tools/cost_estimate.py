#!/usr/bin/env python3
"""Order-of-cost estimate (feasibility stage) for Hong Kong buildings, HK$ by CFA x unit rate.

Usage:  python3 cost_estimate.py project.json [-o report.md]   (reads the `cost` block)

`cost` fields:
  rate_level: "low" | "mid" | "high" (default mid)
  components[]: {name, type (key in cost/hk_cost_rates.json), cfa_m2, rate (optional HK$/m2 override)}
  from_floors: {use: type, ...}  optional: also builds components from the top-level `floors[]`
               (gross_area_m2 x count) using this map of floor `use` to rate type; floors whose use
               is not in the map are listed as CHECK
  extras[]: {name, amount}  lump sums not in the unit rates (piling on poor ground, demolition, façade upgrade ...)
  allowances: override any key of `allowances_default` (percentages)
  years_to_tender_midpoint: escalation period (default 0)
  gfa_m2: accountable GFA, for HK$/m2 GFA; budget: client budget to compare (exit 1 if over)
  contract_months: optional, adds an S-curve cash flow table
Unit rates: Arcadis Q2 2026 (see hk_cost_rates.json). They exclude site formation, external works,
land, fees and finance, and assume no basement. Output is an order-of-cost estimate for a QS to develop.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.loads((HERE.parent / "cost" / "hk_cost_rates.json").read_text(encoding="utf-8"))
PASS, FAIL, WARN, INFO = "PASS", "FAIL", "CHECK", "INFO"


def rate_for(t, level):
    r = R["rates"][t]
    lo, hi = r["low"], r["high"] or r["low"]
    return {"low": lo, "high": hi, "mid": (lo + hi) / 2}[level]


def build_components(p, c):
    comps = list(c.get("components", []))
    unmapped = []
    m = c.get("from_floors")
    if m:
        for f in p.get("floors", []):
            area = f["gross_area_m2"] * f.get("count", 1)
            t = m.get(f["use"])
            if t:
                comps.append({"name": f["name"], "type": t, "cfa_m2": area})
            else:
                unmapped.append((f["name"], f["use"], area))
    return comps, unmapped


def run(p, level=None):
    c = p["cost"]
    level = level or c.get("rate_level", "mid")
    al = {**R["allowances_default"], **c.get("allowances", {})}
    comps, unmapped = build_components(p, c)
    lines, notes = [], []
    base = 0.0
    cfa = 0.0
    for comp in comps:
        t = comp["type"]
        if t not in R["rates"]:
            notes.append(f"Unknown rate type `{t}` for {comp['name']}: give `rate`.")
            if "rate" not in comp:
                continue
        rate = comp.get("rate") or rate_for(t, level)
        amt = rate * comp["cfa_m2"]
        base += amt
        cfa += comp["cfa_m2"]
        label = R["rates"].get(t, {}).get("label", t)
        lines.append((comp["name"], label, f"{comp['cfa_m2']:,.0f}", f"{rate:,.0f}", amt))
        if t in R["rates"] and R["rates"][t]["high"] is None and level != "low":
            notes.append(f"{comp['name']}: source gives only a lower bound ({R['rates'][t]['low']:,}/m2 and up).")
    for n, u, a in unmapped:
        notes.append(f"CHECK: floor `{n}` (use `{u}`, {a:,.0f} m2) has no rate mapping; not costed.")
    for e in c.get("extras", []):
        base += e["amount"]
        lines.append((e["name"], "lump sum", "-", "-", e["amount"]))

    summary = [("Building works (CFA x rate + extras)", base)]
    sf = base * al["site_formation_pct"] / 100
    ext = base * al["external_works_pct"] / 100
    summary += [(f"Site formation ({al['site_formation_pct']}%)", sf), (f"External works ({al['external_works_pct']}%)", ext)]
    works = base + sf + ext
    dc = works * al["design_contingency_pct"] / 100
    cc = (works + dc) * al["construction_contingency_pct"] / 100
    summary += [(f"Design contingency ({al['design_contingency_pct']}%)", dc),
                (f"Construction contingency ({al['construction_contingency_pct']}%)", cc)]
    cons = works + dc + cc
    yrs = c.get("years_to_tender_midpoint", 0)
    esc = cons * ((1 + al["escalation_pct_per_year"] / 100) ** yrs - 1)
    summary.append((f"Escalation ({al['escalation_pct_per_year']}%/yr x {yrs} yr)", esc))
    cons_total = cons + esc
    summary.append(("**Construction cost**", cons_total))
    fees = cons_total * al["professional_fees_pct"] / 100
    summary.append((f"Professional fees ({al['professional_fees_pct']}%)", fees))
    total = cons_total + fees
    summary.append(("**Total development cost (excl. land, finance, legal)**", total))
    return {"level": level, "lines": lines, "summary": summary, "notes": notes, "cfa": cfa,
            "construction": cons_total, "total": total}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # default Windows consoles cannot print the reports
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    res = run(p)
    lo, hi = run(p, "low"), run(p, "high")
    c = p["cost"]
    out = [f"# Order-of-cost estimate – {p.get('project', 'Untitled')}", "",
           f"**Construction cost {res['construction'] / 1e6:,.1f} M (range {lo['construction'] / 1e6:,.1f} – "
           f"{hi['construction'] / 1e6:,.1f} M); total excl. land {res['total'] / 1e6:,.1f} M HK$** "
           f"at {res['level']} rates.", "",
           f"> Draft order-of-cost estimate. Unit rates: Arcadis Quarterly Construction Cost Review {R['base_quarter']} "
           "(HK$/m² CFA); allowances are planning assumptions. Develop with a QS before reporting to the client.", "",
           "| Component | Rate basis | CFA m² | HK$/m² | Amount HK$ |", "| --- | --- | --- | --- | --- |"]
    out += [f"| {n} | {b} | {a_} | {r} | {amt:,.0f} |" for n, b, a_, r, amt in res["lines"]]
    out += ["", "| Summary | HK$ |", "| --- | --- |"]
    out += [f"| {k} | {v:,.0f} |" for k, v in res["summary"]]
    out.append("")
    if res["cfa"]:
        out.append(f"- Construction cost per m² CFA: HK${res['construction'] / res['cfa']:,.0f} (CFA {res['cfa']:,.0f} m²).")
    if c.get("gfa_m2"):
        out.append(f"- Construction cost per m² GFA: HK${res['construction'] / c['gfa_m2']:,.0f} (GFA {c['gfa_m2']:,.0f} m²).")
    over = False
    if c.get("budget"):
        over = res["total"] > c["budget"]
        out.append(f"- Client budget HK${c['budget']:,.0f}: {'**over** by' if over else 'within, margin'} "
                   f"HK${abs(res['total'] - c['budget']):,.0f}.")
    out += [f"- {n}" for n in res["notes"]]
    months = c.get("contract_months")
    if months:
        out += ["", "## Indicative cash flow (S-curve t²(3−2t), rule of thumb)", "",
                "| Month | Cumulative % | Cumulative HK$ M |", "| --- | --- | --- |"]
        step = max(1, round(months / 8))
        for m in sorted(set(list(range(step, months, step)) + [months])):
            t = m / months
            f = t * t * (3 - 2 * t)
            out.append(f"| {m} | {f * 100:.0f}% | {res['construction'] * f / 1e6:,.1f} |")
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if over else 0)


if __name__ == "__main__":
    main()
