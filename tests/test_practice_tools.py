"""Tests for contract_admin, cost_estimate, supervision_plan, dxf_plan, ifc_model, dxf_area_takeoff.

Run:  python3 -m unittest discover -s tests
The drawing tests are skipped if ezdxf / ifcopenshell / shapely are missing (pip install -r requirements-drawing.txt).
Pillow is deliberately not part of that skip check, so test_svg_preview fails if it is missing from the requirements.
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
DEMO = json.loads((ROOT / "examples" / "demo_practice.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(TOOLS))

import contract_admin  # noqa: E402
import cost_estimate  # noqa: E402
import supervision_plan  # noqa: E402

HAS_DRAW = all(importlib.util.find_spec(m) for m in ("ezdxf", "ifcopenshell", "shapely"))


def by_item(rows, text):
    return [r for r in rows if text in r[1]]


class Contract(unittest.TestCase):
    def test_ld_and_extension(self):
        rows = contract_admin.run(DEMO["contract"], date(2028, 12, 1))
        self.assertEqual(by_item(rows, "Extended Completion Date")[0][2], "2028-10-30")  # +30 days granted
        self.assertEqual(by_item(rows, "Delay beyond")[0][2], "21 days")
        self.assertEqual(by_item(rows, "Liquidated damages")[0][2], "HK$2,520,000")
        self.assertIn("HK$840,000", by_item(rows, "Pending EOT")[0][5])

    def test_ld_cap_and_default_retention(self):
        c = copy.deepcopy(DEMO["contract"])
        c["ld_cap"] = 1_000_000
        c.pop("retention_pct")
        rows = contract_admin.run(c, date(2028, 12, 1))
        self.assertEqual(by_item(rows, "Liquidated damages")[0][2], "HK$1,000,000")
        self.assertEqual(by_item(rows, "Retention rate")[0][4], "CHECK")

    def test_notice_checks(self):
        rows = contract_admin.run(DEMO["contract"], date(2028, 12, 1))
        self.assertEqual(by_item(rows, "AI-061")[0][4], "PASS")
        self.assertEqual(by_item(rows, "AI-077")[0][4], "FAIL")      # 10 days > 5
        self.assertEqual(by_item(rows, "EOT-02")[0][4], "FAIL")      # 32-day gap > 28
        self.assertEqual(by_item(rows, "LE-03")[0][4], "PASS")

    def test_cispo_payment(self):
        rows = contract_admin.run(DEMO["contract"], date(2028, 12, 1))
        self.assertEqual(by_item(rows, "IPA-31 payment response")[0][4], "PASS")
        self.assertEqual(by_item(rows, "IPA-31 admitted amount paid")[0][4], "PASS")
        self.assertEqual(by_item(rows, "IPA-32 payment response")[0][4], "FAIL")   # served 31 Oct, none by 30 Nov
        c = copy.deepcopy(DEMO["contract"])
        c["payment_claims"] = [{"ref": "X", "served": "2028-01-31", "response_date": "2028-02-10", "admitted": 100,
                                "payment_days": 90}]
        rows = contract_admin.run(c, date(2028, 4, 15))
        self.assertEqual(by_item(rows, "X admitted amount paid")[0][3], "HK$100 by 2028-03-31")   # 90 capped to 60
        self.assertEqual(by_item(rows, "X admitted amount paid")[0][4], "FAIL")

    def test_dlp_month_end(self):
        self.assertEqual(contract_admin.add_months(date(2028, 1, 31), 1), date(2028, 2, 29))


class Sfbc2025(unittest.TestCase):
    PERIODS = contract_admin.S["sfbc_2025"]["periods"]

    def test_mediation_period_differs_from_2005(self):
        self.assertEqual(self.PERIODS["mediation_period_days"]["days"], 42)
        self.assertEqual(contract_admin.S["periods"]["mediation_period_days"]["days"], 28)

    def test_periods_used_by_the_tool_match_the_2005_values(self):
        for key in ("oral_instruction_confirm_days", "claim_particulars_days", "half_retention_release_days",
                    "eot_further_particulars_interval_days"):
            self.assertEqual(self.PERIODS[key]["days"], contract_admin.P[key]["days"], key)

    def test_listed_events_are_counted(self):
        self.assertEqual(contract_admin.S["sfbc_2025"]["listed_events"]["count"], 24)


class Cost(unittest.TestCase):
    def test_mid_rates_and_totals(self):
        r = cost_estimate.run(DEMO)
        flats = [x for x in r["lines"] if x[0].startswith("1/F")][0]
        self.assertEqual(flats[3], "27,000")             # (25,200 + 28,800) / 2
        self.assertAlmostEqual(flats[4], 7500 * 27000)
        self.assertEqual(r["cfa"], 8550)                 # R/F plant unmapped, not costed
        self.assertTrue(any("R/F plant" in n for n in r["notes"]))
        self.assertAlmostEqual(r["total"], r["construction"] * 1.10)

    def test_range_order(self):
        lo, mid, hi = (cost_estimate.run(DEMO, lv)["construction"] for lv in ("low", "mid", "high"))
        self.assertLess(lo, mid)
        self.assertLess(mid, hi)


class Supervision(unittest.TestCase):
    def test_scale_factor_cap(self):
        q = {"works": [{"type": "superstructure", "value": 60000}], "tcps": []}
        rows, _ = supervision_plan.run(q)
        self.assertIn("= 3.00", rows[0][2])
        self.assertEqual(rows[0][5], "capped")

    def test_demo(self):
        rows, sched = supervision_plan.run(DEMO["supervision"])
        fails = [r[1] for r in rows if r[4] == "FAIL"]
        self.assertEqual(sorted(fails), ["demolition – RSE T3", "demolition – RSE T5"])   # no RSE TCPs on demolition
        self.assertEqual(by_item(rows, "TCP appointments")[0][4], "PASS")
        self.assertEqual(len(sched), 8)

    def test_tm_table1_each_grade_needs_its_own_tcp(self):
        # all other works, AP stream needs T3 weekly + T4 monthly; one T4 weekly TCP cannot fill both
        q = {"works": [{"type": "superstructure", "value": 10000}], "streams_appointed": ["AP"],
             "tcps": [{"stream": "AP", "grade": "T4", "frequency_level": 4, "works": ["superstructure"]}]}
        rows, _ = supervision_plan.run(q)
        res = {r[1]: r[4] for r in rows if r[0].startswith("TM") and r[4] != "INFO"}
        self.assertEqual(res, {"superstructure – AP T4": "PASS", "superstructure – AP T3": "FAIL"})

    def test_tm_geotech_switch(self):
        q = {"geotechnical": True, "works": [{"type": "other_piles", "value": 5}], "tcps": []}
        rows, _ = supervision_plan.run(q)
        self.assertTrue(any("geotech_foundation" in r[0] and "RGE T5" in r[1] for r in rows))

    def test_minor_works_timing(self):
        q = {"minor_works": True, "works": [], "tcps": [],
             "dates": {"plan_submitted": "2026-01-05", "commencement": "2026-01-10"}}
        rows, _ = supervision_plan.run(q)
        self.assertEqual(rows[0][4], "FAIL")   # 5 days < 7


@unittest.skipUnless(HAS_DRAW, "ezdxf / ifcopenshell / shapely not installed")
class Drawing(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.proj = self.tmp / "p.json"
        self.proj.write_text(json.dumps(DEMO, ensure_ascii=False), encoding="utf-8")

    def test_dxf_areas_and_takeoff_round_trip(self):
        dxf, areas = self.tmp / "p.dxf", self.tmp / "a.json"
        subprocess.run([sys.executable, TOOLS / "dxf_plan.py", self.proj, "-o", dxf, "--areas", areas], check=True,
                       capture_output=True)
        a = json.loads(areas.read_text(encoding="utf-8"))
        self.assertEqual(a["site_area_m2"], 750)
        self.assertEqual([f["gross_area_m2"] for f in a["floors"]], [588, 300])
        self.assertEqual(a["warnings"], [])
        out = subprocess.run([sys.executable, TOOLS / "dxf_area_takeoff.py", dxf, "--layers", "A-ROOM", "--json",
                              self.tmp / "t.json"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout)
        t = json.loads((self.tmp / "t.json").read_text(encoding="utf-8"))
        self.assertAlmostEqual(sum(x["area_m2"] for x in t["areas"]),
                               sum(r["floor_area_m2"] for r in a["rooms"]), places=1)

    def test_dxf_flags_room_outside(self):
        d = copy.deepcopy(DEMO)
        d["drawing"]["floors"][1]["rooms"].append({"name": "Bad", "polygon": [[26, 5], [29, 5], [29, 8], [26, 8]]})
        self.proj.write_text(json.dumps(d), encoding="utf-8")
        r = subprocess.run([sys.executable, TOOLS / "dxf_plan.py", self.proj, "-o", self.tmp / "x.dxf"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("room outside footprint", r.stdout)

    def test_svg_preview(self):
        # ezdxf's drawing add-on imports PIL, but ezdxf only installs Pillow through its optional extras.
        dxf, svg = self.tmp / "p.dxf", self.tmp / "p.svg"
        r = subprocess.run([sys.executable, TOOLS / "dxf_plan.py", self.proj, "-o", dxf, "--svg", svg],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        root = ET.parse(svg).getroot()
        ns = "{http://www.w3.org/2000/svg}"
        self.assertEqual(root.tag, ns + "svg")
        self.assertTrue(any(e.get("d") for e in root.iter(ns + "path")), "SVG has no drawn geometry")

    def test_takeoff_hole(self):
        import ezdxf
        doc = ezdxf.new()
        doc.header["$INSUNITS"] = 4
        m = doc.modelspace()
        m.add_lwpolyline([(0, 0), (10000, 0), (10000, 10000), (0, 10000)], close=True, dxfattribs={"layer": "GFA"})
        m.add_lwpolyline([(2000, 2000), (4000, 2000), (4000, 4000), (2000, 4000)], close=True, dxfattribs={"layer": "GFA"})
        m.add_text("FLAT A", dxfattribs={"layer": "GFA", "insert": (8000, 8000)})
        f = self.tmp / "h.dxf"
        doc.saveas(f)
        sys.path.insert(0, str(TOOLS))
        import dxf_area_takeoff
        rows, warns, unit = dxf_area_takeoff.run(str(f), ["GFA"])
        self.assertEqual(unit, "mm")
        self.assertEqual(rows, [{"layer": "GFA", "name": "FLAT A", "area_m2": 96.0}])

    def test_ifc_valid(self):
        import ifcopenshell
        import ifcopenshell.validate
        out = self.tmp / "m.ifc"
        subprocess.run([sys.executable, TOOLS / "ifc_model.py", self.proj, "-o", out], check=True, capture_output=True)
        f = ifcopenshell.open(str(out))
        self.assertEqual(len(f.by_type("IfcBuildingStorey")), 26)
        self.assertEqual(len(f.by_type("IfcSpace")), 3 + 4 * 25)
        log = ifcopenshell.validate.json_logger()
        ifcopenshell.validate.validate(f, log)
        self.assertEqual(log.statements, [])


class CLI(unittest.TestCase):
    def test_exit_codes(self):
        demo = ROOT / "examples" / "demo_practice.json"
        run = lambda t, *a: subprocess.run([sys.executable, TOOLS / t, demo, *a], capture_output=True).returncode
        self.assertEqual(run("contract_admin.py", "--as-of", "2028-12-01"), 1)   # notice failures
        self.assertEqual(run("cost_estimate.py"), 0)                            # within budget
        self.assertEqual(run("supervision_plan.py"), 1)                         # demolition lacks RSE TCPs


if __name__ == "__main__":
    unittest.main()
