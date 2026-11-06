#!/usr/bin/env python3
"""Parametric DXF plan generator (sketch / study drawings) + area schedule.

Usage:  python3 dxf_plan.py project.json -o plans.dxf [--areas areas.json] [--svg plans.svg]   (reads the `drawing` block)

`drawing` fields (metres, site coordinates):
  title, drawing_no, scale (e.g. 200), north_deg (0 = up), wall_mm (external wall, default 200)
  site_boundary: [[x, y], ...]
  setbacks: [{name, line: [[x, y], [x, y]], distance_m}]   optional dimensioned setback lines
  grid: {x: [0, 8.4, ...], y: [0, 7.2, ...]}   grid offsets from the site bounding-box min corner, labelled 1.. / A..
  floors[]: {name, level_m, count, use, footprint: [[x, y], ...],
             cores: [{name, polygon}], rooms: [{name, use, polygon}]}
Output: one model-space DXF (R2018) with each floor laid out side by side, layers on an AIA-style
A-xxxx scheme, room names and areas, site boundary, grid, north point and a title block stamped
"SKETCH – NOT FOR SUBMISSION". --areas writes floor gross areas, site coverage and room areas in the
`floors[]` / `rooms[]` shape used by bpr_check.py (exemptions still to be added by hand).
Not a substitute for BD submission drawings: those must follow PNAP ADM-1 / BD drawing requirements
and be prepared and signed by the AP.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import Polygon

LAYERS = {
    "A-SITE": 1, "A-SETB": 6, "A-GRID": 8, "A-WALL": 7, "A-CORE": 5, "A-ROOM": 3,
    "A-ROOM-IDEN": 2, "A-ANNO-DIMS": 4, "A-ANNO-TTLB": 7, "A-ANNO-NPNT": 7,
}


def poly(p):
    return Polygon(p)


def area(p):
    return abs(poly(p).area)


def shift(pts, dx, dy=0.0):
    return [(x + dx, y + dy) for x, y in pts]


def label(msp, text, xy, h, layer, align=TextEntityAlignment.MIDDLE_CENTER):
    msp.add_text(text, height=h, dxfattribs={"layer": layer}).set_placement(xy, align=align)


def north_point(msp, xy, r, deg):
    a = math.radians(deg)
    tip = (xy[0] + r * math.sin(a), xy[1] + r * math.cos(a))
    msp.add_circle(xy, r, dxfattribs={"layer": "A-ANNO-NPNT"})
    msp.add_line(xy, tip, dxfattribs={"layer": "A-ANNO-NPNT"})
    label(msp, "N", (xy[0] + 1.3 * r * math.sin(a), xy[1] + 1.3 * r * math.cos(a)), r * 0.5, "A-ANNO-NPNT")


def build(dw):
    doc = ezdxf.new("R2018", setup=True)
    doc.units = ezdxf.units.M
    for n, c in LAYERS.items():
        doc.layers.add(n, color=c)
    msp = doc.modelspace()
    site = dw["site_boundary"]
    sp = poly(site)
    minx, miny, maxx, maxy = sp.bounds
    w = maxx - minx
    gap = max(10.0, 0.4 * w)
    th = max(0.25, dw.get("scale", 200) * 0.0025)  # 2.5 mm text at drawing scale
    wall = dw.get("wall_mm", 200) / 1000
    sched = {"site_area_m2": round(sp.area, 2), "floors": [], "rooms": [], "warnings": []}

    for i, f in enumerate(dw["floors"]):
        dx = i * (w + gap)
        msp.add_lwpolyline(shift(site, dx), close=True, dxfattribs={"layer": "A-SITE", "linetype": "DASHDOT"})
        for sb in dw.get("setbacks", []):
            a, b = shift(sb["line"], dx)
            msp.add_line(a, b, dxfattribs={"layer": "A-SETB", "linetype": "DASHED"})
            label(msp, f"{sb['name']} {sb['distance_m']:.1f} m", ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + th), th * 0.8, "A-SETB")
        g = dw.get("grid")
        if g:
            ext = 2.0
            for k, gx in enumerate(g["x"]):
                x = minx + gx + dx
                msp.add_line((x, miny - ext), (x, maxy + ext), dxfattribs={"layer": "A-GRID", "linetype": "CENTER"})
                msp.add_circle((x, maxy + ext + th), th, dxfattribs={"layer": "A-GRID"})
                label(msp, str(k + 1), (x, maxy + ext + th), th, "A-GRID")
            for k, gy in enumerate(g["y"]):
                y = miny + gy
                msp.add_line((minx + dx - ext, y), (maxx + dx + ext, y), dxfattribs={"layer": "A-GRID", "linetype": "CENTER"})
                msp.add_circle((minx + dx - ext - th, y), th, dxfattribs={"layer": "A-GRID"})
                label(msp, chr(65 + k), (minx + dx - ext - th, y), th, "A-GRID")

        fp = poly(f["footprint"])
        if not fp.is_valid:
            sched["warnings"].append(f"{f['name']}: footprint polygon is self-intersecting")
        if not fp.buffer(1e-6).within(sp.buffer(1e-6)):
            sched["warnings"].append(f"{f['name']}: footprint extends beyond the site boundary")
        inner = fp.buffer(-wall, join_style=2)
        msp.add_lwpolyline(shift(list(fp.exterior.coords), dx), close=True, dxfattribs={"layer": "A-WALL"})
        if not inner.is_empty:
            msp.add_lwpolyline(shift(list(inner.exterior.coords), dx), close=True, dxfattribs={"layer": "A-WALL"})
            hatch = msp.add_hatch(color=8, dxfattribs={"layer": "A-WALL"})
            hatch.paths.add_polyline_path(shift(list(fp.exterior.coords), dx), is_closed=True)
            hatch.paths.add_polyline_path(shift(list(inner.exterior.coords), dx), is_closed=True)
        for c in f.get("cores", []):
            msp.add_lwpolyline(shift(c["polygon"], dx), close=True, dxfattribs={"layer": "A-CORE"})
            ctr = poly(c["polygon"]).centroid
            label(msp, c["name"], (ctr.x + dx, ctr.y), th * 0.8, "A-CORE")
        rooms_union = None
        for r in f.get("rooms", []):
            rp = poly(r["polygon"])
            if not rp.within(fp.buffer(1e-6)):
                sched["warnings"].append(f"{f['name']} / {r['name']}: room outside footprint")
            if rooms_union is not None and rooms_union.intersection(rp).area > 0.01:
                sched["warnings"].append(f"{f['name']} / {r['name']}: overlaps another room")
            rooms_union = rp if rooms_union is None else rooms_union.union(rp)
            msp.add_lwpolyline(shift(r["polygon"], dx), close=True, dxfattribs={"layer": "A-ROOM"})
            ctr = rp.representative_point()
            label(msp, r["name"].upper(), (ctr.x + dx, ctr.y + th * 0.7), th, "A-ROOM-IDEN")
            label(msp, f"{rp.area:.1f} m²", (ctr.x + dx, ctr.y - th * 0.7), th * 0.8, "A-ROOM-IDEN")
            sched["rooms"].append({"floor": f["name"], "name": r["name"], "use": r.get("use", "habitable"),
                                   "floor_area_m2": round(rp.area, 2)})
        cnt = f.get("count", 1)
        label(msp, f"{f['name'].upper()}  (+{f['level_m']:.2f})" + (f"  x{cnt}" if cnt > 1 else ""),
              (minx + dx + w / 2, miny - 4 * th), th * 1.4, "A-ANNO-TTLB")
        label(msp, f"GROSS FLOOR AREA {fp.area:,.1f} m²   SITE COVERAGE {fp.area / sp.area * 100:.1f}%",
              (minx + dx + w / 2, miny - 6 * th), th * 0.9, "A-ANNO-TTLB")
        sched["floors"].append({"name": f["name"], "use": f.get("use", "domestic"), "level_m": f["level_m"],
                                "count": cnt, "gross_area_m2": round(fp.area, 2),
                                "site_coverage_m2": round(fp.area, 2), "exempt": []})

    n = len(dw["floors"])
    total_w = n * w + (n - 1) * gap
    # title block
    tb_y = miny - 14 * th
    north_point(msp, (minx + total_w - 3 * th, tb_y + 2.5 * th), 1.6 * th, dw.get("north_deg", 0))
    tb = [(minx, tb_y), (minx + total_w, tb_y), (minx + total_w, tb_y + 5 * th), (minx, tb_y + 5 * th)]
    msp.add_lwpolyline(tb, close=True, dxfattribs={"layer": "A-ANNO-TTLB"})
    label(msp, f"{dw.get('title', 'Untitled')}   DWG {dw.get('drawing_no', 'SK-001')}   SCALE 1:{dw.get('scale', 200)}",
          (minx + th, tb_y + 3.5 * th), th * 1.2, "A-ANNO-TTLB", TextEntityAlignment.MIDDLE_LEFT)
    label(msp, "SKETCH – NOT FOR SUBMISSION. Generated by dxf_plan.py; to be checked and redrawn for BD submission by the AP.",
          (minx + th, tb_y + 1.3 * th), th * 0.8, "A-ANNO-TTLB", TextEntityAlignment.MIDDLE_LEFT)
    return doc, sched


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--areas", help="write area schedule JSON")
    ap.add_argument("--svg", help="also render an SVG preview")
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    doc, sched = build(p["drawing"])
    doc.saveas(a.output)
    if a.areas:
        Path(a.areas).write_text(json.dumps(sched, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.svg:
        from ezdxf.addons.drawing import Frontend, RenderContext, layout, svg
        backend = svg.SVGBackend()
        Frontend(RenderContext(doc), backend).draw_layout(doc.modelspace())
        Path(a.svg).write_text(backend.get_string(layout.Page(420, 297, layout.Units.mm)), encoding="utf-8")
    for f in sched["floors"]:
        print(f"{f['name']}: GFA {f['gross_area_m2']:,.2f} m² x{f['count']}, SC {f['site_coverage_m2'] / sched['site_area_m2'] * 100:.1f}%")
    for wmsg in sched["warnings"]:
        print("CHECK:", wmsg)
    print(f"Wrote {a.output}")
    sys.exit(1 if sched["warnings"] else 0)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")  # reports contain Chinese and symbols
    main()
