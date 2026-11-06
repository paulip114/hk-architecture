# -*- coding: utf-8 -*-
"""Revit side of the workflow, shared by the pyRevit buttons and Dynamo nodes.

Model set-up this expects (see bim/README.md):
* Area scheme "HK GFA" (name configurable): one Area per space to be
  scheduled, on area plans of every floor. Boundaries to the outer face of
  external walls, balconies with their side walls (reg 23(3)(a)).
* Area scheme "HK SC" (optional): one or more Areas per level giving the
  site-coverage footprint (reg 20).
* Shared parameters from bim/revit/HK_shared_parameters.txt:
    Areas:     HK_GFA_Category (text), HK_Use (text), HK_Floor_Count (integer)
    Project Information: HK_Site_Area, HK_Building_Height, HK_Site_Class,
               HK_Building_Type, HK_OZP_Max_PR, HK_Lease_Max_GFA, HK_Dedicated_Area
               and the title block fields in sheets.TITLEBLOCK_FIELDS
    Sheets:    HK_Sheet_Scale, HK_Drawing_Status
  If HK_GFA_Category is blank the Area's name is matched against the aliases
  in areas.py ("Lift machine room" -> mandatory_plant); if HK_Use is blank
  the level default passed by the caller is used.

All Revit API calls are imported inside functions so the module also loads
outside Revit (unit tests use a fake ``Autodesk.Revit.DB``).
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from .areas import FT2_TO_M2, FT_TO_M, make_record

GFA_SCHEME = "HK GFA"
SC_SCHEME = "HK SC"

PROJECT_FIELDS = {
    "HK_Site_Area": "site_area_m2",
    "HK_Building_Height": "height_m",
    "HK_Site_Class": "site_class",
    "HK_Building_Type": "building_type",
    "HK_OZP_Max_PR": "ozp_max_pr_total",
    "HK_Lease_Max_GFA": "lease_max_gfa_m2",
    "HK_Dedicated_Area": "dedicated_area_m2",
}


def _db():
    from Autodesk.Revit import DB  # noqa: imported lazily on purpose
    return DB


def _id(element_id):
    """ElementId -> int. Revit 2024+ uses .Value; .IntegerValue is deprecated there."""
    v = getattr(element_id, "Value", None)
    if v is None:
        v = getattr(element_id, "IntegerValue", element_id)
    return int(v)


def param_value(element, name):
    """String / number value of a named parameter, or None if missing/empty."""
    p = element.LookupParameter(name)
    if p is None or not p.HasValue:
        return None
    DB = _db()
    st = p.StorageType
    if st == DB.StorageType.String:
        v = p.AsString()
        return v if v not in (None, "") else None
    if st == DB.StorageType.Integer:
        return p.AsInteger()
    if st == DB.StorageType.Double:
        return p.AsDouble()
    return p.AsValueString()


def element_name(element):
    DB = _db()
    p = element.get_Parameter(DB.BuiltInParameter.ROOM_NAME)
    return p.AsString() if p is not None and p.AsString() else ""


def collect_areas(doc, scheme_name):
    """Placed Areas in the named scheme. Returns (areas, skipped) where
    skipped lists (id, reason) for unplaced / zero-area / redundant Areas."""
    DB = _db()
    areas, skipped = [], []
    col = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Areas).WhereElementIsNotElementType()
    for a in col:
        scheme = getattr(a, "AreaScheme", None)
        if scheme is None or scheme.Name != scheme_name:
            continue
        if a.Location is None:
            skipped.append((_id(a.Id), "not placed"))
        elif not a.Area or a.Area <= 0:
            skipped.append((_id(a.Id),
                            "zero area (not enclosed or redundant)"))
        else:
            areas.append(a)
    return areas, skipped


def level_info(level, ground_elevation_ft=0.0):
    """(name, elevation above ground in metres)."""
    return level.Name, (level.ProjectElevation - ground_elevation_ft) * FT_TO_M


def area_records(doc, scheme_name=GFA_SCHEME, ground_level_name=None, default_use="non_domestic",
                 level_use=None):
    """Read the GFA scheme into hk_bim records.

    ground_level_name  level whose elevation is taken as ground (G/F); level_m
                       in the output is height above it (used by reg 20(3)).
    level_use          optional {level name: 'domestic'|'non_domestic'}
    Returns (records, skipped).
    """
    level_use = level_use or {}
    areas, skipped = collect_areas(doc, scheme_name)
    ground = ground_elevation_ft(doc, ground_level_name)
    recs = []
    for a in areas:
        lvl = a.Level
        lname, elev = level_info(lvl, ground)
        name = element_name(a)
        use = param_value(a, "HK_Use") or level_use.get(lname) or default_use
        count = param_value(a, "HK_Floor_Count") or 1
        recs.append(make_record(name=name, level=lname, area_m2=a.Area * FT2_TO_M2,
                                category=param_value(a, "HK_GFA_Category"), category_hint=name,
                                use=use, elevation_m=elev, count=count,
                                source_id=_id(a.Id)))
    return recs, skipped


def footprints(doc, scheme_name=SC_SCHEME):
    """{level name: site-coverage area m2} from the SC scheme."""
    areas, _ = collect_areas(doc, scheme_name)
    out = {}
    for a in areas:
        out[a.Level.Name] = out.get(a.Level.Name, 0.0) + a.Area * FT2_TO_M2
    return out


def ground_elevation_ft(doc, ground_level_name=None):
    DB = _db()
    levels = list(DB.FilteredElementCollector(doc).OfClass(DB.Level))
    if ground_level_name:
        for lv in levels:
            if lv.Name == ground_level_name:
                return lv.ProjectElevation
    for lv in levels:
        if lv.Name.replace(" ", "").upper() in ("G/F", "GF", "GROUNDFLOOR", "GROUND", "LEVEL0"):
            return lv.ProjectElevation
    return 0.0


def project_inputs(doc):
    """Site / building data from Project Information parameters (None where blank)."""
    info = doc.ProjectInformation
    out = {}
    for pname, key in PROJECT_FIELDS.items():
        v = param_value(info, pname)
        if v is None:
            out[key] = None
            continue
        if key in ("site_class", "building_type"):
            out[key] = ("%s" % v).strip()
        else:
            try:
                out[key] = float(v)
            except (TypeError, ValueError):
                out[key] = None
    if out.get("site_class"):
        out["site_class"] = out["site_class"].upper()
    if out.get("building_type"):
        bt = out["building_type"].lower().replace("-", "_").replace(" ", "_")
        out["building_type"] = {"nondomestic": "non_domestic", "住宅": "domestic",
                                "非住宅": "non_domestic", "綜合": "composite"}.get(bt, bt)
    return out


# ------------------------------------------------------------------ sheets

def existing_sheet_numbers(doc):
    DB = _db()
    return set(s.SheetNumber for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet))


def unplaced_plan_for_level(doc, level_name, plan_type="FloorPlan"):
    """First non-template floor/area plan of that level not yet on a sheet."""
    DB = _db()
    placed = set()
    for vp in DB.FilteredElementCollector(doc).OfClass(DB.Viewport):
        placed.add(_id(vp.ViewId))
    for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan):
        if v.IsTemplate or v.GenLevel is None or v.GenLevel.Name != level_name:
            continue
        if "%s" % v.ViewType != plan_type:
            continue
        if _id(v.Id) in placed:
            continue
        return v
    return None


def create_sheets(doc, sheets, titleblock_id, place_views=True, view_scale=100,
                  sheet_centre_ft=(1.38, 0.97)):
    """Create ViewSheets from sheets.sheet_list() output. Call inside a
    Transaction. Returns (created, skipped) lists of drawing numbers.

    sheet_centre_ft is the viewport centre in sheet coordinates (feet); the
    default suits an A1 landscape title block with origin at bottom left.
    """
    DB = _db()
    have = existing_sheet_numbers(doc)
    created, skipped = [], []
    for s in sheets:
        if s["number"] in have:
            skipped.append(s["number"])
            continue
        vs = DB.ViewSheet.Create(doc, titleblock_id)
        vs.SheetNumber = s["number"]
        vs.Name = s["name"]
        p = vs.LookupParameter("HK_Sheet_Scale")
        if p is not None and not p.IsReadOnly:
            p.Set(s["scale"])
        if place_views and s.get("level") and s["kind"] in ("plan", "calc"):
            plan_type = "AreaPlan" if s["kind"] == "calc" else "FloorPlan"
            v = unplaced_plan_for_level(doc, s["level"], plan_type)
            if v is not None and DB.Viewport.CanAddViewToSheet(doc, vs.Id, v.Id):
                if not v.ViewTemplateId or v.ViewTemplateId == DB.ElementId.InvalidElementId:
                    v.Scale = view_scale
                DB.Viewport.Create(doc, vs.Id, v.Id, DB.XYZ(sheet_centre_ft[0], sheet_centre_ft[1], 0))
        created.append(s["number"])
    return created, skipped


# ------------------------------------------------------- shared parameters

SHEET_PARAMS = ("HK_Sheet_Scale", "HK_Drawing_Status")


def parameter_targets(group_name, param_name):
    """Which BuiltInCategory names a shared parameter is bound to."""
    if param_name in SHEET_PARAMS:
        return ["OST_Sheets"]
    if group_name == "HK Area":
        return ["OST_Areas"]
    return ["OST_ProjectInformation"]


def bind_shared_parameters(doc, app, shared_file):
    """Bind every parameter in HK_shared_parameters.txt as an instance
    parameter. Call inside a Transaction. Restores the user's own shared
    parameter file afterwards. Returns (added, already_there)."""
    DB = _db()
    previous = app.SharedParametersFilename
    added, present = [], []
    try:
        app.SharedParametersFilename = shared_file
        spf = app.OpenSharedParameterFile()
        if spf is None:
            raise IOError("Cannot open shared parameter file %s" % shared_file)
        bindings = doc.ParameterBindings
        existing = set()
        it = bindings.ForwardIterator()
        while it.MoveNext():
            existing.add(it.Key.Name)
        for group in spf.Groups:
            for definition in group.Definitions:
                if definition.Name in existing:
                    present.append(definition.Name)
                    continue
                cats = app.Create.NewCategorySet()
                for cat_name in parameter_targets(group.Name, definition.Name):
                    bic = getattr(DB.BuiltInCategory, cat_name)
                    cats.Insert(DB.Category.GetCategory(doc, bic))
                binding = app.Create.NewInstanceBinding(cats)
                if bindings.Insert(definition, binding):
                    added.append(definition.Name)
    finally:
        if previous:
            app.SharedParametersFilename = previous
    return added, present
