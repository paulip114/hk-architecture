# -*- coding: utf-8 -*-
"""Tests for bim/hk_bim. Run from the repo root:  python3 -m unittest discover -s bim/tests -v"""
import ast
import copy
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest

BIM = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.path.dirname(BIM)
sys.path.insert(0, BIM)

from hk_bim import areas, bpr_limits, massing, report, sheets  # noqa: E402

spec = importlib.util.spec_from_file_location("bpr_check", os.path.join(ROOT, "tools", "bpr_check.py"))
bpr_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bpr_check)

with open(os.path.join(ROOT, "examples", "demo_composite.json"), encoding="utf-8") as _fh:
    DEMO = json.load(_fh)


def demo_records():
    """The demo_composite floors written as BIM area records."""
    recs = []
    for f in DEMO["floors"]:
        n = f.get("count", 1)
        exempt_total = sum(e["area_m2"] for e in f.get("exempt", []))
        for e in f.get("exempt", []):
            recs.append(areas.make_record(e["item"], f["name"], e["area_m2"], category=e["category"],
                                          use=f["use"], elevation_m=f["level_m"], count=n))
        recs.append(areas.make_record("Floor", f["name"], f["gross_area_m2"] - exempt_total, category="accountable",
                                      use=f["use"], elevation_m=f["level_m"], count=n))
    fps = {f["name"]: f["site_coverage_m2"] for f in DEMO["floors"] if "site_coverage_m2" in f}
    return recs, fps


class TestRulesInStep(unittest.TestCase):
    def test_exempt_fraction_matches_bpr_check(self):
        self.assertEqual(areas.EXEMPT_FRACTION, bpr_check.EXEMPT_FRACTION)
        self.assertEqual(set(areas.CAPPED), bpr_check.CAPPED)
        self.assertEqual(set(areas.PREREQUISITE), bpr_check.PREREQUISITE)
        self.assertEqual(areas.APP151_CAP, bpr_check.APP151_CAP)

    def test_schedule_limits_match_bpr_check(self):
        for h in (10, 15, 15.1, 30, 61, 100):
            for cls in "ABC":
                for use in ("domestic", "non_domestic"):
                    for kind in ("plot_ratio", "site_coverage_pct"):
                        self.assertEqual(bpr_limits.limit(use, kind, cls, h), bpr_check.limit(use, kind, cls, h))

    def test_site_class_matches_bpr_check(self):
        cases = [([12, 6], 130, 60), ([12], 100, 30), ([12, 6, 5], 100, 65), ([3], 100, 30), ([12, 6], 130, 40)]
        for w, p, fr in cases:
            want = bpr_check.classify_site({"street_widths_m": w, "perimeter_m": p,
                                            "frontage_on_specified_streets_m": fr})[0]
            self.assertEqual(bpr_limits.classify_site(w, p, fr), want)


class TestCategories(unittest.TestCase):
    def test_aliases(self):
        cases = {"Lift Machine Room": "mandatory_plant", "地庫停車場": "car_park_underground",
                 "B1 basement car park": "car_park_underground", "A/C plant room": "non_mandatory_plant",
                 "庇護層": "refuge_floor", "Flat A": None, "accountable": "accountable", "Void": "not_gfa",
                 "car_park_above_50": "car_park_above_50", "": None}
        for text, want in cases.items():
            self.assertEqual(areas.normalise_category(text), want, text)

    def test_parameter_beats_name(self):
        r = areas.make_record("Lift machine room", "R/F", 10, category="accountable")
        self.assertEqual(r["category"], "accountable")
        r = areas.make_record("Lift machine room", "R/F", 10, category_hint="Lift machine room")
        self.assertEqual(r["category"], "mandatory_plant")

    def test_use(self):
        self.assertEqual(areas.normalise_use("住宅"), "domestic")
        self.assertEqual(areas.normalise_use("Non-Domestic"), "non_domestic")
        self.assertEqual(areas.normalise_use(None), "non_domestic")


class TestFloorsAndChecks(unittest.TestCase):
    def setUp(self):
        self.recs, self.fps = demo_records()
        self.floors = areas.build_floors(self.recs, footprints=self.fps)

    def test_round_trip_matches_bpr_check(self):
        p = areas.project_json(DEMO["project"], DEMO["site"], DEMO["building"], self.floors, DEMO["limits"])
        rows_bim, _, _, gfa_bim = bpr_check.run(copy.deepcopy(p))
        rows_demo, _, _, gfa_demo = bpr_check.run(copy.deepcopy({k: DEMO[k] for k in
                                                                ("project", "site", "building", "limits", "floors")}))
        self.assertAlmostEqual(gfa_bim, gfa_demo, places=6)
        self.assertEqual([r[4] for r in rows_bim if r[0] in ("20", "21(2)", "APP-151", "OZP")],
                         [r[4] for r in rows_demo if r[0] in ("20", "21(2)", "APP-151", "OZP")])

    def test_quick_check_matches_bpr_check(self):
        res = bpr_limits.quick_check(self.floors, DEMO["site"]["area_m2"], DEMO["building"]["height_m"], "B",
                                     "composite", limits=DEMO["limits"])
        p = areas.project_json("x", DEMO["site"], DEMO["building"], self.floors, DEMO["limits"])
        rows, _, _, gfa = bpr_check.run(copy.deepcopy(p))
        self.assertAlmostEqual(res["totals"]["total"], gfa, places=6)
        comp_full = [r for r in rows if r[0] == "21(2)"][0]
        comp_quick = [r for r in res["rows"] if r[0] == "21(2)"][0]
        self.assertEqual(comp_quick[2], float(comp_full[2]))
        self.assertEqual(comp_quick[4], comp_full[4])
        sc_full = [r[4] for r in rows if r[0] == "20"]
        sc_quick = [r[4] for r in res["rows"] if r[0] == "20"]
        self.assertEqual(sc_full, sc_quick)

    def test_full_report_via_bridge(self):
        p = areas.project_json("x", DEMO["site"], DEMO["building"], self.floors, DEMO["limits"])
        md, fails = report.run_bpr_check(p)
        self.assertIn("B(P)R compliance check", md)
        self.assertIsInstance(fails, int)
        self.assertNotIn("_accountable", json.dumps(p))  # bridge must not mutate the input

    def test_mixed_use_level_splits(self):
        recs = [areas.make_record("Shop", "1/F", 100, "accountable", "non_domestic", 5),
                areas.make_record("Flat", "1/F", 80, "accountable", "domestic", 5)]
        fl = areas.build_floors(recs, footprints={"1/F": 190})
        self.assertEqual([f["name"] for f in fl], ["1/F (domestic)", "1/F (non-domestic)"])
        self.assertEqual(fl[0]["site_coverage_m2"], 190)
        self.assertNotIn("site_coverage_m2", fl[1])

    def test_unclassified_is_refused(self):
        recs = [areas.make_record("Mystery room", "2/F", 10)]
        with self.assertRaises(ValueError):
            areas.build_floors(recs)
        self.assertEqual(areas.build_floors(recs, strict=False), [])

    def test_not_gfa_excluded(self):
        recs = [areas.make_record("Atrium void", "2/F", 50, "void", elevation_m=8),
                areas.make_record("Office", "2/F", 200, "accountable", elevation_m=8)]
        fl = areas.build_floors(recs)
        self.assertEqual(fl[0]["gross_area_m2"], 200)

    def test_schedule_and_csv(self):
        rows = areas.schedule_rows(self.recs)
        total = rows[-1]
        self.assertEqual(total[0], "TOTAL")
        self.assertAlmostEqual(total[9], areas.gfa_totals(self.floors)["total"], places=6)
        self.assertAlmostEqual(total[7], areas.gfa_totals(self.floors)["gross"], places=6)
        d = tempfile.mkdtemp()
        path = areas.write_csv(os.path.join(d, "s.csv"), rows, areas.SCHEDULE_HEADER)
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
        self.assertTrue(text.startswith("Level,"))
        self.assertIn("Transformer & switch room", text)

    def test_app151_cap_fails_when_exceeded(self):
        recs = [areas.make_record("Office", "2/F", 100, "accountable", elevation_m=20),
                areas.make_record("AHU", "2/F", 20, "non_mandatory_plant", elevation_m=20)]
        res = bpr_limits.quick_check(areas.build_floors(recs), 100, 20, "A", "non_domestic")
        cap = [r for r in res["rows"] if r[0] == "APP-151"][0]
        self.assertEqual(cap[4], "FAIL")

    def test_app151_cap_is_separate_for_each_part(self):
        recs = [areas.make_record("Flat", "20/F", 1000, "accountable", use="domestic", elevation_m=60),
                areas.make_record("Balcony", "20/F", 150, "green_feature", use="domestic", elevation_m=60),
                areas.make_record("Office", "2/F", 4000, "accountable", use="non_domestic", elevation_m=20)]
        res = bpr_limits.quick_check(areas.build_floors(recs), 1000, 70, "B", "composite")
        cap = [r for r in res["rows"] if r[0] == "APP-151"]
        self.assertEqual([r[4] for r in cap], ["FAIL"])
        self.assertIn("domestic part", cap[0][1])

    def test_uncapped_feature_needs_prerequisites_only(self):
        self.assertEqual(areas.normalise_category("Sky garden"), "green_feature_uncapped")
        recs = [areas.make_record("Office", "2/F", 100, "accountable", elevation_m=20),
                areas.make_record("Sky garden", "2/F", 50, "green_feature_uncapped", elevation_m=20)]
        rows = bpr_limits.quick_check(areas.build_floors(recs), 100, 20, "A", "non_domestic")["rows"]
        self.assertEqual([r for r in rows if r[0] == "APP-151"], [])
        self.assertEqual([r[4] for r in rows if r[0] == "APP-151 para 6"], ["CHECK"])


class TestEnvelopeAndMassing(unittest.TestCase):
    def test_envelope_class_a_domestic_tall(self):
        e = bpr_limits.envelope(1000, 100, "A", "domestic", floor_to_floor_m=3.15)
        self.assertEqual(e["plot_ratio"], 8.0)
        self.assertEqual(e["site_coverage_pct"], 33.33)
        self.assertEqual(e["max_gfa_m2"], 8000)
        self.assertEqual(e["tower_floors_at_max_footprint"], 25)  # 8000 / 333.3

    def test_envelope_composite_formula(self):
        e = bpr_limits.envelope(1000, 100, "B", "composite", non_domestic_pr=3.0)
        self.assertAlmostEqual(e["domestic_pr"], round((1 - 3.0 / 15) * 9.0, 3))

    def test_envelope_ozp_governs(self):
        e = bpr_limits.envelope(1000, 100, "C", "domestic", ozp_max_pr=6)
        self.assertEqual(e["governing_limit"], "OZP")
        self.assertEqual(e["max_gfa_m2"], 6000)
        e = bpr_limits.envelope(1000, 100, "B", "composite", non_domestic_pr=2.7, ozp_max_pr=10)
        self.assertAlmostEqual(e["domestic_pr"], 7.3)

    def test_floor_levels(self):
        lv = massing.floor_levels(0, [5, 4, 3], 15)
        self.assertEqual([z for _i, z in lv], [0, 5, 9, 12])
        with self.assertRaises(ValueError):
            massing.floor_levels(0, [0], 10)

    def test_massing_records_feed_checks(self):
        plates = [(0, -4.0, 900), (1, 0.0, 900), (2, 5.0, 900), (3, 10.0, 300), (4, 13.15, 300)]
        recs, fps = massing.massing_records(plates, podium_floors=2, building_type="composite",
                                            mandatory_plant_pct=0.02, basement_count=1, ground_z=0.0)
        fl = areas.build_floors(recs, footprints=fps)
        self.assertEqual(fl[0]["name"], "B1/F")
        self.assertEqual(fl[0]["exempt"][0]["category"], "car_park_underground")
        self.assertNotIn("site_coverage_m2", fl[0])
        self.assertEqual(fl[1]["use"], "non_domestic")
        self.assertEqual(fl[3]["use"], "domestic")
        t = areas.gfa_totals(fl)
        self.assertAlmostEqual(t["total"], (900 * 2 + 300 * 2) * 0.98, places=6)


class TestSheets(unittest.TestCase):
    def test_level_tags(self):
        cases = {"B1/F": "B1F", "5/F": "05F", "G/F": "GF", "R/F": "RF", "Level 12": "12F", "LG1": "LG1F"}
        for k, v in cases.items():
            self.assertEqual(sheets.level_tag(k), v)

    def test_sheet_list(self):
        s = sheets.sheet_list(["B1/F", "G/F", "1/F", "R/F"], include={"002", "020", "040", "050"})
        nums = [x["number"] for x in s]
        self.assertIn("GBP-020-GF", nums)
        self.assertIn("GBP-040-02", nums)
        self.assertEqual(len([n for n in nums if n.startswith("GBP-050")]), 4)
        self.assertEqual(len(nums), len(set(nums)))
        self.assertEqual([x for x in s if x["number"] == "GBP-002"][0]["scale"], "1:500")

    def test_duplicate_tags_refused(self):
        with self.assertRaises(ValueError):
            sheets.sheet_list(["5/F", "Level 5"], include={"020"})

    def test_legend_covers_categories(self):
        self.assertEqual(set(r[0] for r in sheets.legend_rows()), set(areas.CATEGORIES))


# --------------------------------------------------------- fake Revit API

class _Id(object):
    def __init__(self, v):
        self.Value = v


class _Param(object):
    def __init__(self, value, st):
        self.value, self.StorageType, self.HasValue, self.IsReadOnly = value, st, value is not None, False

    def AsString(self):
        return self.value

    def AsInteger(self):
        return self.value

    def AsDouble(self):
        return self.value


class _Level(object):
    def __init__(self, name, elev_ft):
        self.Name, self.ProjectElevation = name, elev_ft


class _Area(object):
    def __init__(self, i, name, level, area_ft2, scheme, params=None, placed=True):
        self.Id, self.Level, self.Area = _Id(i), level, area_ft2
        self.AreaScheme = types.SimpleNamespace(Name=scheme)
        self.Location = object() if placed else None
        self._name, self._params = name, params or {}

    def get_Parameter(self, _bip):
        return _Param(self._name, "String")

    def LookupParameter(self, name):
        v = self._params.get(name)
        if v is None:
            return None
        return _Param(v, "Integer" if isinstance(v, int) else "String")


def fake_revit(elements):
    class Collector(object):
        def __init__(self, doc):
            pass

        def OfCategory(self, _c):
            self._items = [e for e in elements if isinstance(e, _Area)]
            return self

        def OfClass(self, cls):
            self._items = [e for e in elements if isinstance(e, cls)]
            return self

        def WhereElementIsNotElementType(self):
            return self

        def __iter__(self):
            return iter(self._items)

    DB = types.ModuleType("Autodesk.Revit.DB")
    DB.FilteredElementCollector = Collector
    DB.BuiltInCategory = types.SimpleNamespace(OST_Areas="areas")
    DB.BuiltInParameter = types.SimpleNamespace(ROOM_NAME="name")
    DB.StorageType = types.SimpleNamespace(String="String", Integer="Integer", Double="Double")
    DB.Level = _Level
    autodesk = types.ModuleType("Autodesk")
    revit = types.ModuleType("Autodesk.Revit")
    revit.DB = DB
    autodesk.Revit = revit
    return {"Autodesk": autodesk, "Autodesk.Revit": revit, "Autodesk.Revit.DB": DB}


class TestRevitAdapter(unittest.TestCase):
    def test_area_records_from_fake_model(self):
        gf, f5 = _Level("G/F", 10.0), _Level("5/F", 10.0 + 60.0)
        elems = [gf, f5,
                 _Area(1, "Shop", gf, 1000.0, "HK GFA", {"HK_GFA_Category": "accountable"}),
                 _Area(2, "Lift machine room", f5, 100.0, "HK GFA", {"HK_Use": "domestic", "HK_Floor_Count": 3}),
                 _Area(3, "Unplaced", f5, 0.0, "HK GFA", placed=False),
                 _Area(4, "Footprint", gf, 2000.0, "HK SC")]
        saved = {k: sys.modules.get(k) for k in ("Autodesk", "Autodesk.Revit", "Autodesk.Revit.DB")}
        sys.modules.update(fake_revit(elems))
        try:
            from hk_bim import revit_adapter
            recs, skipped = revit_adapter.area_records(None, "HK GFA")
            fps = revit_adapter.footprints(None, "HK SC")
        finally:
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
        self.assertEqual(len(recs), 2)
        self.assertEqual(skipped, [(3, "not placed")])
        shop = [r for r in recs if r["name"] == "Shop"][0]
        self.assertAlmostEqual(shop["area_m2"], 92.90304)
        self.assertAlmostEqual(shop["elevation_m"], 0.0)
        lmr = [r for r in recs if r["name"] != "Shop"][0]
        self.assertEqual((lmr["category"], lmr["use"], lmr["count"]), ("mandatory_plant", "domestic", 3))
        self.assertAlmostEqual(lmr["elevation_m"], 60 * 0.3048)
        self.assertAlmostEqual(fps["G/F"], 2000 * 0.09290304)


# ------------------------------------------- IronPython 2.7 compatibility

PY2_SCAN = ["hk_bim", "grasshopper", "dynamo/HK_Envelope.py", "pyrevit"]


def _py_files():
    for entry in PY2_SCAN:
        p = os.path.join(BIM, entry)
        if os.path.isfile(p):
            yield p
        for d, _dirs, files in os.walk(p):
            for f in files:
                if f.endswith(".py"):
                    yield os.path.join(d, f)


class TestIronPythonSafe(unittest.TestCase):
    """IronPython 2.7 cannot parse f-strings, annotations, keyword-only args,
    nonlocal, async or `yield from`. Catch them here since no IronPython is
    available in CI."""

    def test_no_py3_only_syntax(self):
        problems = []
        for path in _py_files():
            with open(path, encoding="utf-8") as fh:
                src = fh.read()
            tree = ast.parse(src)
            if "coding: utf-8" not in src.splitlines()[0] and any(ord(c) > 127 for c in src):
                problems.append("%s: non-ASCII without coding line" % path)
            for node in ast.walk(tree):
                bad = None
                if isinstance(node, ast.JoinedStr):
                    bad = "f-string"
                elif isinstance(node, (ast.AnnAssign, ast.Nonlocal, ast.YieldFrom, ast.AsyncFunctionDef, ast.Await)):
                    bad = type(node).__name__
                elif isinstance(node, (ast.FunctionDef, ast.Lambda)):
                    a = node.args
                    if a.kwonlyargs or getattr(a, "posonlyargs", []) or \
                            any(x.annotation for x in a.args) or getattr(node, "returns", None):
                        bad = "py3-only function signature"
                elif isinstance(node, ast.Starred) and not isinstance(getattr(node, "ctx", None), ast.Load):
                    bad = "starred assignment"
                if bad:
                    problems.append("%s:%s %s" % (os.path.relpath(path, BIM), getattr(node, "lineno", "?"), bad))
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
