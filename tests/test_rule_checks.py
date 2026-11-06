"""Regression tests for rules checked against the official PDFs: PNAP APP-151 para 4 and the Barrier Free Design Manual.

Run:  python3 -m unittest discover -s tests
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import bfa_check  # noqa: E402
import bpr_check  # noqa: E402


def composite(dom_plant, non_dom_plant):
    return {"site": {"area_m2": 1000, "class": "B"}, "building": {"type": "composite", "height_m": 70},
            "floors": [{"name": "Pod", "use": "non_domestic", "level_m": 0, "gross_area_m2": 3000,
                        "exempt": [{"item": "Plant", "area_m2": non_dom_plant, "category": "non_mandatory_plant"}]},
                       {"name": "Tower", "use": "domestic", "level_m": 15, "gross_area_m2": 1000,
                        "exempt": [{"item": "Balcony", "area_m2": dom_plant, "category": "green_feature"}]}]}


def cap_rows(p):
    return [r for r in bpr_check.run(p)[0] if r[0] == "APP-151 para 4"]


class App151(unittest.TestCase):
    def test_each_part_is_capped_on_its_own_gfa(self):
        # Domestic: 150 of 850 m² fails, although 200 of 3,800 m² across the development would pass.
        rows = cap_rows(composite(150, 50))
        self.assertEqual(len(rows), 2)
        by = {("domestic" if "– domestic" in r[1] else "non_domestic"): r[4] for r in rows}
        self.assertEqual(by, {"domestic": "FAIL", "non_domestic": "PASS"})

    def test_single_use_row_has_no_part_label(self):
        p = composite(0, 100)
        p["floors"] = p["floors"][:1]
        p["building"]["type"] = "non_domestic"
        rows = cap_rows(p)
        self.assertEqual(len(rows), 1)
        self.assertNotIn("part", rows[0][1])


def bfa(**kw):
    rows = bfa_check.run({"building_type": "non_domestic", **kw})
    return {r[0]: r[4] for r in rows}, rows


class BarrierFree(unittest.TestCase):
    def test_counter_limit_is_750_not_900(self):
        self.assertEqual(bfa(counters=[{"name": "C", "height_mm": 850, "width_mm": 900}])[0]["Div 15 para 70(2)(a)"], "FAIL")
        self.assertEqual(bfa(counters=[{"name": "C", "height_mm": 750, "width_mm": 750}])[0]["Div 15 para 70(2)(a)"], "PASS")
        self.assertEqual(bfa(counters=[{"name": "C", "height_mm": 750, "width_mm": 700}])[0]["Div 15 para 70(2)(a)"], "FAIL")
        self.assertEqual(bfa(counters=[{"name": "C", "height_mm": 750}])[0]["Div 15 para 70(2)(a)"], "CHECK")

    def test_only_one_lift_needs_the_accessible_size(self):
        small = {"name": "S", "car_mm": [1000, 1000], "door_mm": 800}
        good = {"name": "G", "car_mm": [1100, 1200], "door_mm": 850}
        self.assertEqual(bfa(lifts=[small, good])[0]["Div 19 para 78(1)"], "PASS")
        self.assertEqual(bfa(lifts=[small])[0]["Div 19 para 78(1)"], "FAIL")
        self.assertEqual(bfa(lifts=[{**good, "door_mm": 800}])[0]["Div 19 para 78(1)"], "FAIL")

    def test_more_than_three_lifts_need_one_large_lift(self):
        good = {"name": "G", "car_mm": [1100, 1200], "door_mm": 850}
        self.assertNotIn("Div 19 para 78(2)", bfa(lifts=[good] * 3)[0])
        self.assertEqual(bfa(lifts=[good] * 4)[0]["Div 19 para 78(2)"], "FAIL")
        self.assertEqual(bfa(lifts=[good] * 3 + [{"name": "B", "car_mm": [1500, 1400], "door_mm": 850}])[0]["Div 19 para 78(2)"], "PASS")

    def test_other_divisions(self):
        self.assertEqual(bfa(illumination=[{"name": "Corridor", "lux": 80, "kind": "upper"}])[0]["Div 16 paras 72-73"], "FAIL")
        self.assertEqual(bfa(illumination=[{"name": "Lobby", "lux": 120, "kind": "ground_lobby"}])[0]["Div 16 paras 72-73"], "PASS")
        self.assertEqual(bfa(escalators=[{"name": "E"}])[0]["Div 20 para 85"], "FAIL")
        self.assertEqual(bfa(toilets=[{"name": "T", "call_bell_mm": 700}])[0]["Div 17 para 76"], "FAIL")


if __name__ == "__main__":
    unittest.main()
