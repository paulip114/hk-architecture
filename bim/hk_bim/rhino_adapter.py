# -*- coding: utf-8 -*-
"""Rhino / Grasshopper geometry helpers (RhinoCommon). Imported lazily so the
rest of hk_bim loads outside Rhino."""
from __future__ import absolute_import, division, print_function, unicode_literals


def _rg():
    import Rhino.Geometry as rg  # noqa
    return rg


def unit_scale_to_m():
    """Factor that turns model lengths into metres (1.0 for a metre model,
    0.001 for millimetres)."""
    import Rhino
    doc = Rhino.RhinoDoc.ActiveDoc
    if doc is None:
        return 1.0
    return Rhino.RhinoMath.UnitScale(doc.ModelUnitSystem, Rhino.UnitSystem.Meters)


def tolerance():
    import Rhino
    doc = Rhino.RhinoDoc.ActiveDoc
    return doc.ModelAbsoluteTolerance if doc else 0.001


def planar_area(curves, tol=None):
    """Area of closed planar curves, holes (courtyards, light wells) subtracted.
    Returns (area in model units^2, list of planar breps)."""
    rg = _rg()
    tol = tol or tolerance()
    closed = [c for c in curves if c is not None and c.IsClosed]
    if not closed:
        return 0.0, []
    breps = rg.Brep.CreatePlanarBreps(closed, tol) or []
    total = 0.0
    for b in breps:
        amp = rg.AreaMassProperties.Compute(b)
        if amp is not None:
            total += amp.Area
    return total, list(breps)


def slice_breps(breps, z_values, tol=None):
    """Section closed breps with horizontal planes. Returns a list of
    (z, curves, area) in model units."""
    rg = _rg()
    tol = tol or tolerance()
    out = []
    for z in z_values:
        plane = rg.Plane(rg.Point3d(0, 0, z), rg.Vector3d.ZAxis)
        curves = []
        for b in breps:
            ok, crvs, _pts = rg.Intersect.Intersection.BrepPlane(b, plane, tol)
            if ok and crvs:
                joined = rg.Curve.JoinCurves(crvs, tol) or crvs
                curves.extend(joined)
        area, _ = planar_area(curves, tol)
        out.append((z, curves, area))
    return out


def bbox_z(breps):
    rg = _rg()
    bb = rg.BoundingBox.Empty
    for b in breps:
        bb.Union(b.GetBoundingBox(True))
    return bb.Min.Z, bb.Max.Z
