"""Tests for rules checked against PNAP APP-151 (July 2025) and APP-152 (September 2023).

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bpr = load("bpr_check")
sbd = load("sbd_check")
bfa = load("bfa_check")
fsi = load("fsi_check")
energy = load("energy_check")


def scheme(*floors):
    return {"site": {"area_m2": 1000, "class": "B"}, "building": {"type": "composite", "height_m": 40},
            "floors": list(floors)}


def floor(use, gross, *exempt):
    return {"name": use, "use": use, "level_m": 20, "gross_area_m2": gross, "exempt": list(exempt)}


def item(category, area, **extra):
    return dict({"item": category, "area_m2": area, "category": category}, **extra)


def rows_for(project, ref):
    return [r for r in bpr.run(project)[0] if r[0] == ref]


class App151Cap(unittest.TestCase):
    def test_exactly_ten_percent_of_accountable_gfa_passes(self):
        rows = rows_for(scheme(floor("non_domestic", 1100, item("non_mandatory_plant", 100))), "APP-151")
        self.assertEqual([r[4] for r in rows], ["PASS"])

    def test_above_ten_percent_fails(self):
        rows = rows_for(scheme(floor("non_domestic", 1100, item("non_mandatory_plant", 101))), "APP-151")
        self.assertEqual([r[4] for r in rows], ["FAIL"])

    def test_each_part_of_a_composite_has_its_own_cap(self):
        # 150 m2 is 3% of the whole 5,000 m2 but 15% of the 1,000 m2 domestic part.
        rows = rows_for(scheme(floor("domestic", 1150, item("green_feature", 150)),
                               floor("non_domestic", 4000)), "APP-151")
        self.assertEqual(len(rows), 1)
        self.assertIn("domestic part", rows[0][1])
        self.assertEqual(rows[0][4], "FAIL")

    def test_parts_are_reported_separately(self):
        rows = rows_for(scheme(floor("domestic", 1150, item("green_feature", 150)),
                               floor("non_domestic", 4100, item("non_mandatory_plant", 100))), "APP-151")
        self.assertEqual([r[4] for r in rows], ["FAIL", "PASS"])

    def test_serves_charges_the_feature_to_the_other_part(self):
        rows = rows_for(scheme(floor("domestic", 1000),
                               floor("non_domestic", 4150, item("green_feature", 150, serves="domestic"))), "APP-151")
        self.assertEqual(len(rows), 1)
        self.assertIn("domestic part", rows[0][1])
        self.assertNotIn("non-domestic", rows[0][1])
        self.assertEqual(rows[0][4], "FAIL")

    def test_unknown_serves_is_refused(self):
        with self.assertRaises(SystemExit):
            bpr.run(scheme(floor("domestic", 1000, item("green_feature", 10, serves="hotel"))))

    def test_capped_feature_with_no_accountable_gfa_fails(self):
        rows = rows_for(scheme(floor("domestic", 50, item("green_feature", 50))), "APP-151")
        self.assertEqual([r[4] for r in rows], ["FAIL"])

    def test_uncapped_feature_is_not_capped_but_needs_prerequisites(self):
        project = scheme(floor("domestic", 1500, item("green_feature_uncapped", 500)))
        self.assertEqual(rows_for(project, "APP-151"), [])
        self.assertEqual([r[4] for r in rows_for(project, "APP-151 para 6")], ["CHECK"])

    def test_mandatory_plant_needs_neither(self):
        project = scheme(floor("domestic", 1500, item("mandatory_plant", 500)))
        self.assertEqual(rows_for(project, "APP-151"), [])
        self.assertEqual(rows_for(project, "APP-151 para 6"), [])


class Reg31(unittest.TestCase):
    def rows(self, use, reg_31):
        room = {"name": "R", "use": use, "floor_area_m2": 10, "glass_m2": 1, "openable_m2": 1, "reg_31": reg_31}
        return [r for r in bpr.run(dict(scheme(floor("domestic", 1000)), rooms=[room]))[0] if r[0].startswith("31")]

    def plane(self, height, distance=5.0, **extra):
        return dict({"plane_base_m": 4.2, "plane_depth_m": 5.0, "uncovered": True,
                     "obstructions": [{"name": "Tower", "distance_m": distance, "height_above_sill_m": height}]}, **extra)

    def test_street_of_4_5_m_is_enough(self):
        self.assertEqual([r[4] for r in self.rows("habitable", {"faces_street_ge_4_5m": True})], ["PASS"])

    def test_habitable_plane_rises_at_71_5_degrees_from_the_sill_line(self):
        # 5 m x tan 71.5 deg = 14.94 m
        self.assertEqual(self.rows("habitable", self.plane(14.9))[-1][4], "PASS")
        self.assertEqual(self.rows("habitable", self.plane(15.0))[-1][4], "FAIL")

    def test_kitchen_plane_rises_at_76_degrees(self):
        # 5 m x tan 76 deg = 20.05 m
        self.assertEqual(self.rows("kitchen", self.plane(20.0))[-1][4], "PASS")
        self.assertEqual(self.rows("kitchen", self.plane(20.1))[-1][4], "FAIL")

    def test_horizontal_plane_minimums(self):
        rows = self.rows("habitable", self.plane(1, plane_base_m=4.1, plane_depth_m=4.4))
        status = {r[0]: r[4] for r in rows}
        self.assertEqual(status["31(2)(a)"], "FAIL")   # 18.04 m2
        self.assertEqual(status["31(2)(b)"], "PASS")
        self.assertEqual(status["31(2)(c)"], "FAIL")

    def boundary(self, height, distance, depth=2.3, **extra):
        return dict({"plane_base_m": 9.2, "plane_depth_m": depth, "uncovered": True, "opposite": "boundary",
                     "obstructions": [{"distance_m": distance, "height_above_sill_m": height}]}, **extra)

    def test_boundary_plane_rises_at_80_5_degrees(self):
        # 2.3 m x tan 80.5 deg = 13.74 m
        self.assertEqual(self.rows("habitable", self.boundary(13.7, 2.3))[-1][4], "PASS")
        self.assertEqual(self.rows("habitable", self.boundary(13.8, 2.3))[-1][4], "FAIL")

    def test_lane_moves_the_boundary_1_5_m_for_the_inclined_plane(self):
        # (2.3 + 1.5) m x tan 80.5 deg = 22.71 m
        self.assertEqual(self.rows("habitable", self.boundary(22.7, 2.3, lane_width_m=4))[-1][4], "PASS")
        self.assertEqual(self.rows("habitable", self.boundary(22.8, 2.3, lane_width_m=4))[-1][4], "FAIL")

    def test_lane_credit_on_depth_depends_on_its_width(self):
        depth_row = lambda lane: [r for r in self.rows("habitable", self.boundary(1, 2, depth=1.2, lane_width_m=lane))
                                  if r[0] == "31(2)(d)-(e)"][0][4]
        self.assertEqual(depth_row(3.5), "PASS")   # 1.2 + 1.5
        self.assertEqual(depth_row(2.0), "FAIL")   # 1.2 + 1.0, to the centre line

    def test_unconfirmed_plane_is_a_check(self):
        rows = self.rows("habitable", {"plane_base_m": 5, "plane_depth_m": 5})
        self.assertEqual({r[4] for r in rows}, {"PASS", "CHECK"})

    def test_room_without_input_is_listed_as_a_check(self):
        room = {"name": "Bedroom", "use": "habitable", "floor_area_m2": 10, "glass_m2": 1, "openable_m2": 1}
        rows = [r for r in bpr.run(dict(scheme(floor("domestic", 1000)), rooms=[room]))[0] if r[0] == "31"]
        self.assertEqual([r[4] for r in rows], ["CHECK"])
        self.assertIn("Bedroom", rows[0][2])


class FireServiceTank(unittest.TestCase):
    def status(self, floor_m2, litres):
        rows = fsi.run({"parts": [], "largest_floor_m2": floor_m2, "fs_tank_litres": litres})
        return [r[4] for r in rows if r[0] == "para 5.26"]

    def test_table_has_four_bands(self):
        for floor_m2, need in ((230, 9000), (231, 18000), (460, 18000), (461, 27000), (920, 27000), (921, 36000)):
            self.assertEqual(self.status(floor_m2, need), ["PASS"])
            self.assertEqual(self.status(floor_m2, need - 1), ["FAIL"])

    def test_car_port_sprinklers_apply_above_230_m2(self):
        def required(area):
            part = {"name": "Car port", "use": "4.9", "total_floor_area_m2": area, "provided": []}
            rows = fsi.run({"parts": [part]})
            return [r[4] for r in rows if "prinkler" in r[1]]
        self.assertEqual(required(231), ["FAIL"])
        self.assertNotIn("FAIL", required(230))


class BuildingEnergyCode(unittest.TestCase):
    def test_lighting_and_chiller_figures_from_the_code(self):
        self.assertEqual(energy.E["bec_lpd_W_m2"]["classroom"], 9.1)
        self.assertEqual(energy.E["bec_lpd_W_m2"]["storeroom_gt15"], 6.3)
        cop = energy.E["bec_other"]["chiller_min_cop"]
        self.assertEqual(cop["water_cooled_centrifugal_gt3000_full"], 5.9)
        self.assertEqual(cop["air_cooled_vsd_screw_ge500_75pct"], 4.1)

    def test_regenerative_braking_depends_on_speed_only(self):
        self.assertEqual(set(energy.E["bec_other"]["lift_regenerative_braking"]) - {"_ref"}, {"speed_m_s"})


class App152(unittest.TestCase):
    def permeability(self, height, planes, site=25000):
        return {"site_area_m2": site, "tallest_height_m": height,
                "planes": [{"name": f"P{i}", "lp_m": 100, "zones": {"low": {"p_pct": p, "is_pct": p}}}
                           for i, p in enumerate(planes)]}

    def statuses(self, q):
        return [r[4] for r in sbd.run(q) if r[0] == "para 4(b), Table 1"]

    def test_table_1_large_site_low_building(self):
        self.assertEqual(self.statuses(self.permeability(60, [20, 25])), ["PASS", "PASS"])
        self.assertEqual(self.statuses(self.permeability(60, [19.9, 24.9])), ["FAIL", "FAIL"])

    def test_table_1_large_site_tall_building(self):
        self.assertEqual(self.statuses(self.permeability(61, [20, 33.3])), ["PASS", "PASS"])
        self.assertEqual(self.statuses(self.permeability(61, [20, 33.2])), ["PASS", "FAIL"])

    def test_table_1_smaller_site_with_long_facade(self):
        self.assertEqual(self.statuses(self.permeability(100, [20, 20], site=5000)), ["PASS", "PASS"])

    def test_lp_limit_is_five_times_street_width(self):
        q = self.permeability(61, [20, 33.3])
        q["street_canyon_width_m"] = 20
        self.assertEqual([r[4] for r in sbd.run(q) if r[0].startswith("para 4(a)")], ["PASS"])
        q["street_canyon_width_m"] = 19.9
        self.assertEqual([r[4] for r in sbd.run(q) if r[0].startswith("para 4(a)")], ["FAIL"])


class BarrierFreeDivisions15And19(unittest.TestCase):
    def status(self, q, ref):
        return [r[4] for r in bfa.run(dict(q, building_type="non_domestic")) if r[0] == ref]

    def test_lift_car_is_1100_wide_by_1200_deep(self):
        ref = "Div 19 para 78(1)"
        self.assertEqual(self.status({"lifts": [{"name": "L", "car_mm": [1100, 1200]}]}, ref), ["PASS"])
        self.assertEqual(self.status({"lifts": [{"name": "L", "car_mm": [1200, 1100]}]}, ref), ["FAIL"])

    def test_lift_entrance_is_850(self):
        ref = "Div 19 para 78(1)"
        self.assertEqual(self.status({"lifts": [{"name": "L", "door_mm": 850}]}, ref), ["PASS"])
        self.assertEqual(self.status({"lifts": [{"name": "L", "door_mm": 800}]}, ref), ["FAIL"])

    def test_other_passenger_lifts_only_need_paras_79_and_80(self):
        q = {"lifts": [{"name": "L", "accessible": False, "car_mm": [900, 900], "door_mm": 700,
                        "button_mm": [800, 1300], "detection_mm": 300}]}
        self.assertEqual(self.status(q, "Div 19 para 78(1)"), [])
        self.assertEqual(self.status(q, "Div 19 para 80(1)"), ["FAIL"])
        self.assertEqual(self.status(q, "Div 19 para 79(4)"), ["FAIL"])

    def test_more_than_three_lifts_need_a_larger_car(self):
        small = {"name": "S", "car_mm": [1100, 1200], "door_mm": 850}
        ref = "Div 19 para 78(2)"
        self.assertEqual(self.status({"lifts": [small] * 3}, ref), [])
        self.assertEqual(self.status({"lifts": [small] * 4}, ref), ["FAIL"])
        self.assertEqual(self.status({"lifts": [small], "total_passenger_lifts": 4}, ref), ["FAIL"])
        for car in ([1500, 1400], [1400, 1500]):
            big = {"name": "B", "car_mm": car, "door_mm": 850}
            self.assertEqual(self.status({"lifts": [small] * 3 + [big]}, ref), ["PASS"])
        square = {"name": "Q", "car_mm": [1450, 1450], "door_mm": 850}
        self.assertEqual(self.status({"lifts": [small] * 3 + [square]}, ref), ["FAIL"])

    def test_counter_limits(self):
        good = {"name": "C", "height_mm": 750, "width_mm": 750, "leg_depth_mm": 400, "leg_height_mm": 680}
        bad = {"name": "C", "height_mm": 751, "width_mm": 749, "leg_depth_mm": 601, "leg_height_mm": 679}
        for counter, expected in ((good, "PASS"), (bad, "FAIL")):
            q = {"building_type": "non_domestic", "counters": [counter]}
            rows = [r[4] for r in bfa.run(q) if r[0].startswith("Div 15")]
            self.assertEqual(rows, [expected] * 4)



class BarrierFreeDivisions16To20(unittest.TestCase):
    def status(self, ref, **kw):
        rows = load("bfa_check").run({"building_type": "non_domestic", **kw})
        return [r[4] for r in rows if r[0] == ref]

    def test_illumination(self):
        self.assertEqual(self.status("Div 16 paras 72-73", illumination=[{"name": "C", "lux": 84, "kind": "upper"}, {"name": "C", "lux": 85, "kind": "upper"},
                                                                         {"name": "L", "lux": 119, "kind": "ground_lobby"}, {"name": "S", "lux": 120, "kind": "sign"}]),
                         ["FAIL", "PASS", "FAIL", "PASS"])

    def test_call_button_and_escalator(self):
        self.assertEqual(self.status("Div 17 para 76", toilets=[{"name": "T", "call_bell_mm": 650}, {"name": "U", "call_bell_mm": 700}]), ["PASS", "FAIL"])
        self.assertEqual(self.status("Div 20 para 85", escalators=[{"name": "E", "tactile_both_ends": True}, {"name": "F"}]), ["PASS", "FAIL"])


if __name__ == "__main__":
    unittest.main()
