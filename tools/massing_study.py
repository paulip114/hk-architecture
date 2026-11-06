#!/usr/bin/env python3
"""Massing study helper (Hong Kong). Compares massing options and tests each
one against B(P)R by calling tools/bpr_check.py.

Usage:
  python3 massing_study.py options.json [-o report.md] [--write-projects DIR]
  python3 massing_study.py --envelope --site-area 1000 --site-class B \
          --use domestic --ftf 3.15 [--ground-ftf 4.5] [--max-height 110]

Options mode: each option is a stack of blocks (podium, tower, etc.). The tool
works out storeys, heights, gross area, an estimate of accountable GFA,
site coverage at each level and plot ratio, then builds a bpr_check project
for each option and runs it. --write-projects saves those project files so
the chosen option can be carried on into the full B(P)R / FS Code checks.

Envelope mode: for one use and site class, lists every First Schedule height
band with the permitted SC and PR, how many storeys fit, and the GFA that can
actually be reached (min of PR x site and SC x site x storeys). Use it on day
one to see which height band gives the most GFA before drawing anything.

Input (options.json):
  project, site (as bpr_check), limits (as bpr_check), building_type
  ("domestic"/"non_domestic"/"composite"), optional mean_street_level_mpd,
  optional ozp_height_mpd, optional open_space {provided_m2, roofed_over_area_m2}
  options[]: name, optional note, blocks[], optional basements[]
    block: name, use, storeys, ftf_m (floor-to-floor), plate_m2 (gross per
      floor), optional footprint_m2 (defaults to plate), optional
      start_level_m (defaults to the top of the previous block, so blocks
      stack; give it for side-by-side towers), optional exempt[] (bpr_check
      items, per floor) or exempt_pct (rough % of plate disregarded,
      category other_disregarded)
    basement: name, use, plate_m2, optional exempt[] / exempt_pct

Results are a design-stage screening. Exemption percentages are estimates
and every option must be re-run with the real area schedule before it is
reported to a client or used in a submission. Draft for AP review.
"""
import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpr_check  # noqa: E402

SCHED = bpr_check.SCHEDULE


def block_floors(b, start):
    """Return bpr_check floor entry for a block (typical floors, count=storeys)."""
    n = int(b["storeys"])
    plate = float(b["plate_m2"])
    if b.get("exempt") is not None:
        exempt = b["exempt"]
    elif b.get("exempt_pct"):
        exempt = [{"item": "estimated exemptions", "area_m2": plate * float(b["exempt_pct"]) / 100,
                   "category": "other_disregarded"}]
    else:
        exempt = []
    return {"name": b["name"], "use": b["use"], "level_m": round(start, 3), "count": n,
            "gross_area_m2": plate, "exempt": exempt}


def build_project(spec, opt):
    floors, segments = [], []
    top = 0.0          # running stack level
    roof = 0.0         # height of building: top of the highest usable storey
    tops = []          # (end level, storeys from ground to the top of this block)
    for b in opt["blocks"]:
        start = float(b["start_level_m"]) if b.get("start_level_m") is not None else top
        ftf = float(b["ftf_m"])
        n = int(b["storeys"])
        end = start + n * ftf
        floors.append(block_floors(b, start))
        segments.append((start, end, float(b.get("footprint_m2", b["plate_m2"])), b["use"], b["name"]))
        below = tops[-1][1] if tops and b.get("start_level_m") is None else \
            next((t[1] for t in tops if abs(t[0] - start) < 0.01), 0)
        tops.append((end, below + n))
        top = end
        roof = max(roof, end)
    for bs in opt.get("basements", []):
        f = block_floors({**bs, "storeys": 1}, -4.0)
        f["level_m"] = -4.0
        floors.insert(0, f)

    # site coverage: combine footprints of all blocks present at each level
    cuts = sorted({s[0] for s in segments})
    for c in cuts:
        live = [s for s in segments if s[0] <= c < s[1]]
        if not live:
            continue
        fp = sum(s[2] for s in live)
        use = "domestic" if any(s[3] == "domestic" for s in live) else "non_domestic"
        names = " + ".join(s[4] for s in live)
        floors.append({"name": f"SC at +{c:g} m ({names})", "use": use, "level_m": c,
                       "gross_area_m2": 0, "site_coverage_m2": fp})

    proj = {"project": f"{spec.get('project', 'Massing study')} – {opt['name']}",
            "site": spec["site"],
            "building": {"type": spec["building_type"], "height_m": round(roof, 2)},
            "limits": spec.get("limits", {}),
            "floors": floors}
    if spec.get("open_space") and spec["building_type"] in ("domestic", "composite"):
        proj["open_space"] = spec["open_space"]
    if opt.get("open_space"):
        proj["open_space"] = opt["open_space"]
    storeys = max(tops, key=lambda t: t[0])[1] if tops else 0
    return proj, roof, storeys


def run_options(spec, write_dir=None):
    area = float(spec["site"]["area_m2"])
    mpd0 = spec.get("mean_street_level_mpd")
    out_rows, details = [], []
    for opt in spec["options"]:
        proj, h, nst = build_project(spec, opt)
        rows, ex, notes, gfa = bpr_check.run(json.loads(json.dumps(proj)))
        fails = [r for r in rows if r[4] == bpr_check.FAIL]
        checks = [r for r in rows if r[4] == bpr_check.WARN]
        gross = sum(float(f["gross_area_m2"]) * int(f.get("count", 1)) for f in proj["floors"])
        mpd = f"{mpd0 + h:.1f}" if mpd0 is not None else "-"
        hl = []
        if spec.get("ozp_height_mpd") is not None and mpd0 is not None:
            ok = mpd0 + h <= spec["ozp_height_mpd"]
            hl.append(f"OZP {spec['ozp_height_mpd']} mPD {'PASS' if ok else 'FAIL'}")
            if not ok:
                fails.append(("OZP", "Height (mPD)", f"{mpd0+h:.1f}", spec["ozp_height_mpd"], "FAIL", ""))
        verdict = "FAIL" if fails else ("CHECK" if checks else "PASS")
        out_rows.append((opt["name"], nst, h, mpd, gross, gfa, gfa / area, verdict, len(fails), len(checks)))
        details.append((opt, proj, rows, fails, checks, hl))
        if write_dir:
            d = Path(write_dir)
            d.mkdir(parents=True, exist_ok=True)
            safe = "".join(ch if ch.isalnum() else "_" for ch in opt["name"])[:40]
            (d / f"massing_{safe}.json").write_text(json.dumps(proj, ensure_ascii=False, indent=1), encoding="utf-8")
    return out_rows, details


def report(spec, out_rows, details):
    f = bpr_check.fmt
    L = [f"# Massing study – {spec.get('project', 'Untitled')}", "",
         "> Design-stage screening. Exemptions are estimates; re-run bpr_check with the real area schedule "
         "before reporting figures. Draft for review by an Authorized Person.", "",
         f"Site area {f(float(spec['site']['area_m2']))} m², building type {spec['building_type']}.", "",
         "| Option | Storeys | Height m (above street) | mPD | Gross m² | Accountable GFA m² | PR | B(P)R | Fail | Check |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for n, s, h, mpd, g, gfa, pr, v, nf, nc in out_rows:
        L.append(f"| {n} | {s} | {h:.2f} | {mpd} | {f(g)} | {f(gfa)} | {pr:.3f} | {v} | {nf} | {nc} |")
    for opt, proj, rows, fails, checks, hl in details:
        L += ["", f"## {opt['name']}", ""]
        if opt.get("note"):
            L += [opt["note"], ""]
        L += ["| Block | Use | Storeys | F-F m | Plate m² | Footprint m² | From +m | To +m |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        top = 0.0
        for b in opt["blocks"]:
            st = float(b["start_level_m"]) if b.get("start_level_m") is not None else top
            en = st + int(b["storeys"]) * float(b["ftf_m"])
            L.append(f"| {b['name']} | {b['use']} | {b['storeys']} | {b['ftf_m']} | {f(float(b['plate_m2']))} | "
                     f"{f(float(b.get('footprint_m2', b['plate_m2'])))} | {st:g} | {en:g} |")
            top = en
        key = [r for r in rows if r[0] in ("21(1)", "21(2)", "21(3)", "20", "OZP", "Lease", "APP-151", "22", "25 / Sch 2")]
        L += ["", "| Reg | Item | Proposed | Limit | Result | Note |", "| --- | --- | --- | --- | --- | --- |"]
        for r in key:
            L.append("| " + " | ".join(str(x) for x in r) + " |")
        for x in hl:
            L.append(f"- {x}")
        if fails:
            L += ["", "**To fix:** " + "; ".join(f"{r[1]} {r[2]} vs {r[3]}" for r in fails)]
    L += ["", "## Next steps", "",
          "- Pick an option, replace `exempt_pct` with the real exemption list, run `bpr_check.py` on the saved project file.",
          "- Add `means_of_escape`, `fire_construction` and `means_of_access` blocks and run the FS Code tools.",
          "- Check SBD (PNAP APP-152) separation, setback and greenery, and the APP-151 10% cap, outside this tool."]
    return "\n".join(L) + "\n"


def envelope(area, cls, use, ftf, ground_ftf=None, max_h=None):
    bands = SCHED["height_bands_m"]
    tab = SCHED["domestic" if use == "domestic" else "non_domestic"]
    g = ground_ftf or ftf
    L = [f"# Development envelope – {use}, class {cls}, site {area:,.0f} m²", "",
         f"Storey heights: ground {g} m, typical {ftf} m." + (f" Height cap {max_h} m." if max_h else ""), "",
         "| Height band | SC % | PR | Max GFA m² (PR) | Storeys that fit | GFA reachable m² | Storeys to reach PR at max SC | Plate at max SC m² |",
         "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    best = None
    for i, (lo, hi) in enumerate(bands):
        top = hi if hi is not None else (max_h or 200)
        if max_h and lo >= max_h:
            break
        top = min(top, max_h) if max_h else top
        sc = tab["site_coverage_pct"][cls][i]
        pr = tab["plot_ratio"][cls][i]
        n = 0 if top < g else 1 + int(math.floor((top - g) / ftf + 1e-9))
        plate = area * sc / 100
        if use == "non_domestic" and lo < 15:
            plate = area  # reg 20(3): 100% up to 15 m
        reach = min(pr * area, plate * n)
        need = math.ceil(pr * area / plate - 1e-9) if plate else 0
        lab = bpr_check.band_label(i)
        L.append(f"| {lab} | {sc} | {pr} | {pr*area:,.0f} | {n} | {reach:,.0f} | {need} | {plate:,.0f} |")
        if best is None or reach > best[1]:
            best = (lab, reach)
    L += ["", f"Most GFA reachable: **{best[1]:,.0f} m²** in band {best[0]}.",
          "", "SC and PR limits are those of the band the whole building falls in (height to roof over highest usable floor). "
          "For domestic SC the limit applies to every storey; podium storeys of non-domestic use up to 15 m may cover 100%. "
          "Lower OZP / lease limits govern where they exist."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("options", nargs="?")
    ap.add_argument("-o", "--output")
    ap.add_argument("--write-projects")
    ap.add_argument("--envelope", action="store_true")
    ap.add_argument("--site-area", type=float)
    ap.add_argument("--site-class", choices=["A", "B", "C"])
    ap.add_argument("--use", choices=["domestic", "non_domestic"], default="domestic")
    ap.add_argument("--ftf", type=float, default=3.15)
    ap.add_argument("--ground-ftf", type=float)
    ap.add_argument("--max-height", type=float)
    a = ap.parse_args()
    if a.envelope:
        if not (a.site_area and a.site_class):
            ap.error("--envelope needs --site-area and --site-class")
        md = envelope(a.site_area, a.site_class, a.use, a.ftf, a.ground_ftf, a.max_height)
        code = 0
    else:
        if not a.options:
            ap.error("give an options.json or --envelope")
        spec = json.loads(Path(a.options).read_text(encoding="utf-8"))
        rows, det = run_options(spec, a.write_projects)
        md = report(spec, rows, det)
        code = 1 if all(r[7] == "FAIL" for r in rows) else 0
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(code)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")  # reports contain Chinese and symbols
    main()
