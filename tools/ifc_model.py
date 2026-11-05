#!/usr/bin/env python3
"""Parametric IFC4 massing model from the same `drawing` block used by dxf_plan.py.

Usage:  python3 ifc_model.py project.json -o model.ifc   (reads the `drawing` block)

Per floor (repeated `count` times, floor_to_floor_m default 3.15 or `floor_to_floor_m` on the floor):
  IfcBuildingStorey at level_m, IfcSlab from the footprint (slab_mm, default 200), IfcWall per footprint
  edge (wall_mm thick, storey height), IfcSpace per room with LongName = use and NetFloorArea quantity.
Opens in Revit (IFC import), ArchiCAD, BlenderBIM / Bonsai, Solibri. It is a massing / area model for
coordination and quantity checks, not a design or submission model.
"""
import argparse
import json
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.root
import ifcopenshell.api.unit
import ifcopenshell.api.context
import ifcopenshell.api.project
import ifcopenshell.api.aggregate
import ifcopenshell.api.spatial
import ifcopenshell.api.geometry
import ifcopenshell.api.pset
from shapely.geometry import Polygon


def run(dw, name):
    f = ifcopenshell.api.project.create_file(version="IFC4")
    proj = ifcopenshell.api.root.create_entity(f, ifc_class="IfcProject", name=name)
    ifcopenshell.api.unit.assign_unit(f)  # metres
    model = ifcopenshell.api.context.add_context(f, context_type="Model")
    body = ifcopenshell.api.context.add_context(f, context_type="Model", context_identifier="Body",
                                                target_view="MODEL_VIEW", parent=model)
    site = ifcopenshell.api.root.create_entity(f, ifc_class="IfcSite", name="Site")
    bldg = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuilding", name=dw.get("title", name))
    ifcopenshell.api.aggregate.assign_object(f, relating_object=proj, products=[site])
    ifcopenshell.api.aggregate.assign_object(f, relating_object=site, products=[bldg])

    slab_t = dw.get("slab_mm", 200) / 1000
    wall_t = dw.get("wall_mm", 200) / 1000
    stats = {"storeys": 0, "walls": 0, "slabs": 0, "spaces": 0}

    def place(el, z, x=0.0, y=0.0, angle=0.0):
        c, s = math.cos(angle), math.sin(angle)
        m = [[c, -s, 0, x], [s, c, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]
        ifcopenshell.api.geometry.edit_object_placement(f, product=el, matrix=m)

    for fl in dw["floors"]:
        h = fl.get("floor_to_floor_m", dw.get("floor_to_floor_m", 3.15))
        fp = Polygon(fl["footprint"])
        for k in range(fl.get("count", 1)):
            z = fl["level_m"] + k * h
            nm = fl["name"] if fl.get("count", 1) == 1 else f"{fl['name']} #{k + 1}"
            st = ifcopenshell.api.root.create_entity(f, ifc_class="IfcBuildingStorey", name=nm)
            st.Elevation = z
            ifcopenshell.api.aggregate.assign_object(f, relating_object=bldg, products=[st])
            place(st, z)
            stats["storeys"] += 1

            slab = ifcopenshell.api.root.create_entity(f, ifc_class="IfcSlab", name=f"{nm} slab", predefined_type="FLOOR")
            pts = [tuple(p) for p in fl["footprint"]]
            rep = ifcopenshell.api.geometry.add_slab_representation(f, context=body, depth=slab_t, polyline=pts)
            ifcopenshell.api.geometry.assign_representation(f, product=slab, representation=rep)
            place(slab, z)
            ifcopenshell.api.spatial.assign_container(f, relating_structure=st, products=[slab])
            stats["slabs"] += 1

            ring = list(fp.exterior.coords)
            for i, (a, b) in enumerate(zip(ring, ring[1:])):
                L = math.dist(a, b)
                if L < 1e-6:
                    continue
                wall = ifcopenshell.api.root.create_entity(f, ifc_class="IfcWall", name=f"{nm} EW{i + 1}")
                rep = ifcopenshell.api.geometry.add_wall_representation(f, context=body, length=L, height=h - slab_t,
                                                                        thickness=wall_t)
                ifcopenshell.api.geometry.assign_representation(f, product=wall, representation=rep)
                place(wall, z + slab_t, a[0], a[1], math.atan2(b[1] - a[1], b[0] - a[0]))
                ifcopenshell.api.spatial.assign_container(f, relating_structure=st, products=[wall])
                stats["walls"] += 1

            for r in fl.get("rooms", []):
                sp = ifcopenshell.api.root.create_entity(f, ifc_class="IfcSpace", name=r["name"])
                sp.LongName = r.get("use", "")
                ifcopenshell.api.aggregate.assign_object(f, relating_object=st, products=[sp])
                rep = ifcopenshell.api.geometry.add_slab_representation(f, context=body, depth=h - slab_t,
                                                                        polyline=[tuple(p) for p in r["polygon"]])
                ifcopenshell.api.geometry.assign_representation(f, product=sp, representation=rep)
                place(sp, z + slab_t)
                q = ifcopenshell.api.pset.add_qto(f, product=sp, name="Qto_SpaceBaseQuantities")
                ifcopenshell.api.pset.edit_qto(f, qto=q, properties={"NetFloorArea": round(Polygon(r["polygon"]).area, 3),
                                                                     "Height": h - slab_t})
                stats["spaces"] += 1
    return f, stats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    p = json.loads(Path(a.project).read_text(encoding="utf-8"))
    f, stats = run(p["drawing"], p.get("project", "Untitled"))
    f.write(a.output)
    print(f"Wrote {a.output}: " + ", ".join(f"{v} {k}" for k, v in stats.items()))


if __name__ == "__main__":
    main()
