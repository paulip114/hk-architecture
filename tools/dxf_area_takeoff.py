#!/usr/bin/env python3
"""Area take-off from an existing DXF (AutoCAD, or Revit / ArchiCAD DXF export).

Usage:  python3 dxf_area_takeoff.py drawing.dxf --layers A-AREA-GFA A-ROOM [--unit mm] [-o areas.md] [--json areas.json]

Reads closed LWPOLYLINE / POLYLINE entities on the given layers (all layers if omitted), takes the
area of each, and names it from the TEXT / MTEXT whose insertion point falls inside it (first match).
Holes: a closed polyline on the same layer lying fully inside another is subtracted from it.
--unit mm|m: drawing units (default: from $INSUNITS, else mm). Arcs (bulges) are flattened.
Check the result against the drawing: unclosed or overlapping outlines are reported, not fixed.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import ezdxf
from shapely.geometry import Point, Polygon

SCALE = {"mm": 1e-6, "m": 1.0, "cm": 1e-4}
INSUNITS = {4: "mm", 5: "cm", 6: "m"}


def outlines(msp, layers):
    for e in msp.query("LWPOLYLINE POLYLINE"):
        if layers and e.dxf.layer not in layers:
            continue
        closed = e.closed if e.dxftype() == "LWPOLYLINE" else e.is_closed
        pts = [tuple(v)[:2] for v in e.flattening(0.01)] if hasattr(e, "flattening") else \
              [tuple(v)[:2] for v in e.vertices()]
        yield e.dxf.layer, closed, pts


def run(path, layers, unit=None):
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    unit = unit or INSUNITS.get(doc.header.get("$INSUNITS", 4), "mm")
    k = SCALE[unit]
    texts = [(Point(t.dxf.insert[0], t.dxf.insert[1]), t.plain_text() if t.dxftype() == "MTEXT" else t.dxf.text)
             for t in msp.query("TEXT MTEXT")]
    by_layer = defaultdict(list)
    warnings = []
    for layer, closed, pts in outlines(msp, set(layers or [])):
        if not closed or len(pts) < 3:
            warnings.append(f"open polyline on {layer} ({len(pts)} vertices) skipped")
            continue
        pg = Polygon(pts)
        if not pg.is_valid:
            warnings.append(f"self-intersecting outline on {layer} skipped")
            continue
        by_layer[layer].append(pg)
    rows = []
    for layer, pgs in by_layer.items():
        pgs.sort(key=lambda g: g.area, reverse=True)
        holes = set()
        for i, a in enumerate(pgs):
            for j in range(i + 1, len(pgs)):
                if j not in holes and pgs[j].within(a):
                    holes.add(j)
        for i, a in enumerate(pgs):
            if i in holes:
                continue
            net = a
            for j in holes:
                if pgs[j].within(a):
                    net = net.difference(pgs[j])
            name = next((s for pt, s in texts if net.contains(pt)), f"(unnamed {layer} #{i + 1})")
            rows.append({"layer": layer, "name": name.strip(), "area_m2": round(net.area * k, 2)})
        for i in range(len(pgs)):
            for j in range(i + 1, len(pgs)):
                if i in holes or j in holes:
                    continue
                if pgs[i].intersection(pgs[j]).area * k > 0.01:
                    warnings.append(f"outlines overlap on {layer}")
    return rows, warnings, unit


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dxf")
    ap.add_argument("--layers", nargs="*")
    ap.add_argument("--unit", choices=list(SCALE))
    ap.add_argument("-o", "--output")
    ap.add_argument("--json")
    a = ap.parse_args()
    rows, warns, unit = run(a.dxf, a.layers, a.unit)
    out = [f"# Area take-off – {Path(a.dxf).name}", "", f"Drawing units: {unit}. {len(rows)} areas.", "",
           "| Layer | Name | Area m² |", "| --- | --- | --- |"]
    out += [f"| {r['layer']} | {r['name']} | {r['area_m2']:,.2f} |" for r in rows]
    tot = defaultdict(float)
    for r in rows:
        tot[r["layer"]] += r["area_m2"]
    out += ["", "| Layer | Total m² |", "| --- | --- |"] + [f"| {k} | {v:,.2f} |" for k, v in tot.items()]
    out += [""] + [f"- CHECK: {w}" for w in warns]
    md = "\n".join(out) + "\n"
    if a.output:
        Path(a.output).write_text(md, encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps({"areas": rows, "warnings": warns}, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.stdout.write(md)
    sys.exit(1 if warns else 0)


if __name__ == "__main__":
    main()
