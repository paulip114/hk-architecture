"""Tests for the fire safety tools: fire_cd_check, part_e_check, part_f_check, ppe_check, fire_eng_timeline, fs_lookup.

Expected limits are written here on purpose, so a change to a limit in the data fails a test. They were compared
with the Code of Practice for Fire Safety in Buildings 2011 (2024 Edition) on 2026-11-07.

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
PASS, FAIL, CHECK, INFO = "PASS", "FAIL", "CHECK", "INFO"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cd = load("fire_cd_check")
part_e = load("part_e_check")
part_f = load("part_f_check")
ppe = load("ppe_check")
fe = load("fire_eng_timeline")
lookup = load("fs_lookup")


def cd_rows(project):
    rows = []

    def add(ref, item, value, lim, status, note=""):
        rows.append((ref, item, value, lim, status, note))

    cd.part_c(project, add)
    cd.part_d(project, add)
    return rows


def statuses(rows, ref, contains=""):
    return [r[4] for r in rows if r[0] == ref and contains in r[1]]


class TableC1(unittest.TestCase):
    def test_required_frr_and_limits(self):
        cases = (("1a", 50000, 60, True), ("2", 50000, 60, True), ("3a", 2500, 60, True), ("3a", 2501, 60, False),
                 ("4a", 10500, 60, True), ("4a", 10501, 60, False), ("4b", 2500, 60, True), ("4b", 2501, 120, True),
                 ("4b", 10501, 120, False), ("5a", 2500, 60, True), ("5a", 2501, 120, True), ("5d", 2501, 120, True),
                 ("5b", 2501, 120, True), ("5c", 10500, 120, True), ("6a", 10500, 120, True), ("7", 10500, 60, True),
                 ("7", 10501, 60, False))
        for use, area, frr, within in cases:
            with self.subTest(use=use, area=area):
                got_frr, got_within, _ = cd.c1(use, area)
                self.assertEqual((got_frr, got_within), (frr, within))

    def test_volume_limits(self):
        self.assertTrue(cd.c1("6b", 10000, 28000)[1])
        self.assertFalse(cd.c1("6b", 10000, 28001)[1])
        self.assertTrue(cd.c1("6c", 1000, 7000)[1])
        self.assertFalse(cd.c1("6c", 1000, 7001)[1])

    def test_unknown_use_goes_to_the_building_authority(self):
        self.assertEqual(cd.c1("9", 100)[0], None)

    def test_oversize_compartment_is_a_check_and_short_frr_a_fail(self):
        rows = cd_rows({"fire_construction": {"compartments": [
            {"name": "Office", "use_class": "4a", "area_m2": 10501, "frr_min": 59}], "sprinklered": True}})
        self.assertEqual(statuses(rows, "C3.1 / Table C1"), [CHECK])
        self.assertEqual(statuses(rows, "C4.1"), [FAIL])

    def test_basement_needs_240_minutes(self):
        def result(frr):
            return statuses(cd_rows({"fire_construction": {"sprinklered": True, "compartments": [
                {"name": "B1", "use_class": "7", "area_m2": 1000, "frr_min": frr, "basement": True}]}}), "C4.1")
        self.assertEqual(result(240), [PASS])
        self.assertEqual(result(239), [FAIL])


class PartCOther(unittest.TestCase):
    def rows(self, **fire):
        return cd_rows({"fire_construction": dict({"sprinklered": True}, **fire)})

    def test_use_separation_takes_the_longer_frr(self):
        spaces = [{"name": "Flats", "use_class": "1", "area_m2": 100}, {"name": "Shops", "use_class": "4b", "area_m2": 3000}]
        self.assertEqual(statuses(self.rows(compartments=spaces, use_separation_frr_min=120), "C7.1"), [PASS])
        self.assertEqual(statuses(self.rows(compartments=spaces, use_separation_frr_min=119), "C7.1"), [FAIL])
        self.assertEqual(statuses(self.rows(compartments=spaces), "C7.1"), [CHECK])

    def test_liftwell_needs_120_minutes(self):
        self.assertEqual(statuses(self.rows(liftwell_frr_min=120), "C9.1(a)"), [PASS])
        self.assertEqual(statuses(self.rows(liftwell_frr_min=119), "C9.1(a)"), [FAIL])

    def test_special_hazards(self):
        def result(frr, direct):
            return statuses(self.rows(special_hazards=[{"name": "Boiler", "frr_min": frr, "opens_to_protected_exit": direct}]), "C13.1")
        self.assertEqual(result(120, False), [PASS])
        self.assertEqual(result(119, False), [FAIL])
        self.assertEqual(result(240, True), [PASS])
        self.assertEqual(result(239, True), [FAIL])

    def test_restaurant_kitchen_lobby_applies_above_45_m2(self):
        def lobby(ufa):
            return statuses(self.rows(restaurant_kitchens=[{"name": "K", "frr_min": 60, "ufa_m2": ufa}]), "C13.2(b)")
        self.assertEqual(lobby(45), [])
        self.assertEqual(lobby(46), [FAIL])

    def test_basement_smoke_outlets(self):
        def area(size, storage=False):
            return statuses(self.rows(basement={"floor_area_m2": 1000, "smoke_outlet_area_m2": size, "storage": storage}), "C14.2(d)")
        self.assertEqual(area(5), [PASS])
        self.assertEqual(area(4.99), [FAIL])
        self.assertEqual(area(25, True), [PASS])
        self.assertEqual(area(24.99, True), [FAIL])
        self.assertEqual(statuses(self.rows(basement={"smoke_outlet_max_spacing_m": 30.1}), "C14.2(a)"), [FAIL])
        self.assertEqual(statuses(self.rows(basement={"smoke_outlet_min_dim_m": 0.99}), "C14.2(e)"), [FAIL])

    def test_spandrel_or_projection_unless_sprinklered(self):
        def result(**wall):
            return statuses(self.rows(sprinklered=False, external_wall=wall), "C11.1")
        self.assertEqual(result(spandrel_m=0.9), [PASS])
        self.assertEqual(result(projection_m=0.5), [PASS])
        self.assertEqual(result(spandrel_m=0.89, projection_m=0.49), [FAIL])
        self.assertEqual(statuses(self.rows(), "C11.1"), [PASS])

    def test_atrium_limits(self):
        good = {"name": "A", "volume_m3": 28000, "height_m": 15, "floors": 3}
        self.assertEqual(statuses(self.rows(atria=[good]), "C10.3"), [PASS])
        for key, value in (("volume_m3", 28001), ("height_m", 15.1), ("floors", 4)):
            self.assertEqual(statuses(self.rows(atria=[dict(good, **{key: value})]), "C10.3"), [FAIL], key)
        self.assertEqual(statuses(self.rows(sprinklered=False, atria=[good]), "C10.3"), [FAIL])


class TableD1(unittest.TestCase):
    def required(self, **part):
        lift, frs, _ = cd.d1_required(dict({"storeys": 10, "cubical_extent_m3": 0}, **part))
        return lift, frs

    def test_domestic_needs_a_lift_above_30_m(self):
        self.assertEqual(self.required(building_kind="domestic", height_above_lowest_street_m=30), (False, False))
        self.assertEqual(self.required(building_kind="domestic", height_above_lowest_street_m=30.1), (True, False))

    def test_non_domestic_depends_on_height_and_extent(self):
        kind = {"building_kind": "non_domestic"}
        self.assertEqual(self.required(height_above_lowest_street_m=15, cubical_extent_m3=9000, **kind), (False, False))
        self.assertEqual(self.required(height_above_lowest_street_m=16, cubical_extent_m3=7000, **kind), (False, False))
        self.assertEqual(self.required(height_above_lowest_street_m=16, cubical_extent_m3=7001, **kind), (True, False))
        self.assertEqual(self.required(height_above_lowest_street_m=31, **kind), (True, False))

    def test_industrial_above_30_m_needs_a_lift_and_frs(self):
        self.assertEqual(self.required(building_kind="industrial", height_above_lowest_street_m=31), (True, True))

    def test_single_storey_needs_neither(self):
        self.assertEqual(self.required(building_kind="domestic", storeys=1, height_above_lowest_street_m=50), (False, False))

    def test_deep_basement_needs_a_lift_and_frs(self):
        rows = cd_rows({"means_of_access": {"building_kind": "domestic", "storeys": 3,
                                            "basement": {"cubical_extent_m3": 7001, "depth_m": 9.1}}})
        self.assertEqual(statuses(rows, "B(P)R 41B / D8"), [FAIL])
        self.assertEqual(statuses(rows, "B(P)R 41C / D15"), [FAIL])


class PartD(unittest.TestCase):
    BASE = {"building_kind": "domestic", "storeys": 10, "height_above_lowest_street_m": 40}

    def rows(self, **m):
        return cd_rows({"means_of_access": dict(self.BASE, **m)})

    def test_fireman_lift_distances(self):
        self.assertEqual(statuses(self.rows(firemans_lifts=1, max_distance_to_lobby_m=60), "D8.4 / D15.6"), [PASS])
        self.assertEqual(statuses(self.rows(firemans_lifts=1, max_distance_to_lobby_m=60.1), "D8.4 / D15.6"), [FAIL])
        unknown = {"firemans_lifts": 1, "layout_known": False}
        self.assertEqual(statuses(self.rows(max_distance_to_lobby_m=45, **unknown), "D8.4 / D15.6"), [PASS])
        self.assertEqual(statuses(self.rows(max_distance_to_lobby_m=45.1, **unknown), "D8.4 / D15.6"), [FAIL])
        self.assertEqual(statuses(self.rows(fsap_distance_m=18.1), "D7.2 / D14.2"), [FAIL])
        self.assertEqual(statuses(self.rows(fsap_passage_width_mm=1499), "D7.3 / D14.4"), [FAIL])

    def test_fireman_lift_size(self):
        good = {"min_dim_m": 1.1, "area_m2": 1.35, "load_kg": 680}
        self.assertEqual(statuses(self.rows(lift_car=good), "D10.1"), [PASS])
        for key, value in (("min_dim_m", 1.09), ("area_m2", 1.34), ("load_kg", 679)):
            self.assertEqual(statuses(self.rows(lift_car=dict(good, **{key: value})), "D10.1"), [FAIL], key)
        self.assertEqual(statuses(self.rows(lift_door_mm=[800, 2000]), "D12.1"), [PASS])
        self.assertEqual(statuses(self.rows(lift_door_mm=[799, 2000]), "D12.1"), [FAIL])
        self.assertEqual(statuses(self.rows(fl_lobby={"area_m2": 2.25, "min_dim_m": 1.5}), "D11.1"), [PASS])
        self.assertEqual(statuses(self.rows(fl_lobby={"area_m2": 2.24, "min_dim_m": 1.5}), "D11.1"), [FAIL])

    def test_frs_lobby(self):
        def lobby(area, vent=None):
            return self.rows(frs_lobby={"area_m2": area, "min_dim_m": 1.5, "vent_area_m2": vent})
        self.assertEqual(statuses(lobby(5), "D16.1(a)"), [PASS])
        self.assertEqual(statuses(lobby(10), "D16.1(a)"), [PASS])
        self.assertEqual(statuses(lobby(4.9), "D16.1(a)"), [FAIL])
        self.assertEqual(statuses(lobby(10.1), "D16.1(a)"), [FAIL])
        self.assertEqual(statuses(lobby(8, 2), "D16.1(c)"), [PASS])
        self.assertEqual(statuses(lobby(8, 1.99), "D16.1(c)"), [FAIL])

    def test_eva_width_by_site(self):
        def width(**eva):
            return statuses(self.rows(eva=eva), "D22.2(a) / D23.3")
        self.assertEqual(width(site="virgin", width_m=7.3), [PASS])
        self.assertEqual(width(site="virgin", width_m=7.29), [FAIL])
        self.assertEqual(width(site="virgin", carriageway=False, width_m=6), [PASS])
        self.assertEqual(width(site="virgin", carriageway=False, width_m=5.99), [FAIL])
        self.assertEqual(width(site="redevelopment", width_m=6), [PASS])
        self.assertEqual(width(site="redevelopment", industrial=True, width_m=7.29), [FAIL])

    def test_eva_other_limits(self):
        base = {"site": "virgin", "width_m": 7.3}
        self.assertEqual(statuses(self.rows(eva=dict(base, headroom_m=4.49)), "D22.2(b)"), [FAIL])
        self.assertEqual(statuses(self.rows(eva=dict(base, gradient=0.1)), "D22.2(c)"), [PASS])
        self.assertEqual(statuses(self.rows(eva=dict(base, gradient=0.11)), "D22.2(c)"), [FAIL])
        self.assertEqual(statuses(self.rows(eva=dict(base, facade_served_fraction=0.25)), "D22.2(e)"), [PASS])
        self.assertEqual(statuses(self.rows(eva=dict(base, facade_served_fraction=0.24)), "D22.2(e)"), [FAIL])
        self.assertEqual(statuses(self.rows(eva=dict(base, deadend=True)), "D22.2(d)"), [FAIL])
        self.assertEqual(statuses(self.rows(eva=dict(base, not_normally_used=True)), "D22.4"), [FAIL])


class PartE(unittest.TestCase):
    def element(self, **el):
        return part_e.run({"elements": [dict({"name": "E"}, **el)]})

    def test_wall_thickness_from_table_e2(self):
        cases = (("wall_brick_solid", 240, 225), ("wall_brick_solid", 60, 100), ("wall_rc_ge1pct", 240, 180),
                 ("wall_rc_ge1pct", 120, 100), ("wall_rc_lt1pct", 120, 160))
        for kind, frr, need in cases:
            with self.subTest(kind=kind, frr=frr):
                self.assertEqual(self.element(type=kind, required_frr=frr, thickness_mm=need)[0][4], PASS)
                self.assertEqual(self.element(type=kind, required_frr=frr, thickness_mm=need - 1)[0][4], FAIL)

    def test_cover_depends_on_continuity(self):
        def cover(mm, continuous):
            return self.element(type="floor_rc", required_frr=120, thickness_mm=125, cover_mm=mm, continuous=continuous)[1][4]
        self.assertEqual(cover(35, False), PASS)
        self.assertEqual(cover(34, False), FAIL)
        self.assertEqual(cover(25, True), PASS)
        self.assertEqual(cover(24, True), FAIL)

    def test_no_deemed_to_satisfy_value_is_a_check(self):
        self.assertEqual(self.element(type="wall_clay_hollow_block", required_frr=240, thickness_mm=999)[0][4], CHECK)

    def test_type_outside_the_tables_needs_a_report(self):
        self.assertEqual(self.element(type="timber_wall", required_frr=60)[0][4], CHECK)
        self.assertEqual(self.element(type="wall_brick_solid", required_frr=90)[0][4], CHECK)

    def test_lining_classes(self):
        def lining(location, **cls):
            return part_e.run({"linings": [dict({"name": "L", "location": location}, **cls)]})[0][4]
        self.assertEqual(lining("protected_exit_all", euro_class="C"), PASS)
        self.assertEqual(lining("protected_exit_all", euro_class="D"), FAIL)
        self.assertEqual(lining("use_class_3_general", euro_class="B"), PASS)
        self.assertEqual(lining("use_class_3_general", euro_class="C"), FAIL)
        self.assertEqual(lining("use_class_5a_auditoria", euro_class="C"), PASS)
        self.assertEqual(lining("protected_exit_all", bs476_class="Class 1"), PASS)
        self.assertEqual(lining("protected_exit_all", bs476_class="Class 3"), FAIL)
        self.assertEqual(lining("protected_exit_all"), CHECK)

    def test_every_documented_lining_location_is_accepted(self):
        for location in part_e.E["lining_requirements"]:
            self.assertIn(location, part_e.__doc__)

    def test_product_without_an_accredited_report_is_a_check(self):
        rows = part_e.run({"products": [{"name": "Door", "test_report_lab_accredited": False}]})
        self.assertEqual(rows[0][4], CHECK)


class PartF(unittest.TestCase):
    def test_missing_plan_items_depend_on_status(self):
        advisory = [r[4] for r in part_f.run({}) if r[4] != INFO]
        condition = [r[4] for r in part_f.run({"s42_modification": True}) if r[4] != INFO]
        self.assertEqual(set(advisory), {CHECK})
        self.assertEqual(set(condition), {FAIL})

    def test_complete_plan_passes(self):
        plan = {part: list(spec["items"]) for part, spec in part_f.F["fsmp_parts"].items()}
        rows = part_f.run({"fire_engineering": True, "temporary_refuge_spaces": True, "fsmp": plan,
                           "bounding_conditions": {"in_gbp": True, "in_fsmp": True, "fsar_in_fsmp": True, "in_dmc": True}})
        self.assertEqual({r[4] for r in rows} - {INFO}, {PASS})

    def test_final_fsar_is_only_asked_for_fire_engineering(self):
        text = part_f.F["fsmp_parts"]
        key_text = next(s["items"]["final_fsar"] for s in text.values() if "final_fsar" in s["items"])
        self.assertFalse(any(key_text in r[1] for r in part_f.run({})))
        self.assertTrue(any(key_text in r[1] for r in part_f.run({"fire_engineering": True})))

    def test_bounding_conditions(self):
        rows = part_f.run({"fire_engineering": True, "bounding_conditions": {}})
        self.assertEqual([r[4] for r in rows if r[0] == "F4.3"], [FAIL, FAIL, CHECK])

    def test_school_drills_every_six_months(self):
        def result(months):
            return [r[4] for r in part_f.run({"use_classes": ["5b"], "drill_interval_months": months}) if "drill interval" in r[1]]
        self.assertEqual(result(6), [PASS])
        self.assertEqual(result(7), [FAIL])

    def test_other_drills_use_a_working_benchmark(self):
        def result(months):
            return [r[4] for r in part_f.run({"use_classes": ["4a"], "drill_interval_months": months}) if "drill interval" in r[1]]
        self.assertEqual(result(12), [PASS])
        self.assertEqual(result(13), [CHECK])

    def lift(self, **works):
        return part_f.run({"lift_works": works})

    def test_landing_doors_open(self):
        def doors(n, hot=False):
            return [r[4] for r in self.lift(doors_open_max=n, hot_work=hot) if r[0] == "F5.7(b)"]
        self.assertEqual(doors(1), [PASS])
        self.assertEqual(doors(3), [CHECK])
        self.assertEqual(doors(4), [FAIL])
        self.assertEqual([r[4] for r in self.lift(doors_open_max=2, hot_work=True) if r[0] == "F5.7(b)(ii)"], [FAIL])

    def test_hoarding_when_more_than_one_door_is_removed(self):
        self.assertEqual([r for r in self.lift(doors_removed=1) if r[0] == "F5.7(d)"], [])
        self.assertEqual([r[4] for r in self.lift(doors_removed=2, hoarding_integrity_min=120) if r[0] == "F5.7(d)"], [PASS])
        self.assertEqual([r[4] for r in self.lift(doors_removed=2, hoarding_integrity_min=119) if r[0] == "F5.7(d)"], [FAIL])

    def test_hoarding_vent_limits(self):
        def vents(items, liftways=1):
            rows = self.lift(doors_removed=2, hoarding_integrity_min=120, vent_openings=items, liftways=liftways)
            return [r[4] for r in rows if r[0] == "F5.7(f)"]
        vent = {"area_mm2": 5500}
        self.assertEqual(vents([vent, vent]), [PASS, PASS])
        self.assertEqual(vents([{"area_mm2": 5501}]), [FAIL, PASS])
        self.assertEqual(vents([vent] * 3), [PASS, FAIL])
        self.assertEqual(vents([vent] * 4, liftways=2), [PASS, PASS])
        self.assertEqual(vents([vent] * 5, liftways=3), [PASS, FAIL])

    def test_housekeeping(self):
        keys = list(part_f.F["table_F1"])
        rows = part_f.run({"housekeeping": {keys[0]: "yes", keys[1]: "no", keys[2]: "n/a"}})
        self.assertEqual([r[4] for r in rows if r[0].startswith("Table F1 ")], [PASS, FAIL, PASS])
        self.assertEqual([r[4] for r in rows if r[0] == "Table F1"], [CHECK])


class ExitTables(unittest.TestCase):
    def test_table_b5_from_the_code(self):
        cases = ((200, 2, 2400), (201, 2, 2600), (300, 2, 2600), (301, 2, 4300), (500, 2, 4300), (501, 3, 6400),
                 (750, 3, 6400), (1000, 4, 8500), (1250, 5, 10400), (1500, 6, 12500), (1750, 7, 14600),
                 (2000, 8, 16700), (2500, 10, 20800), (3000, 12, 24900))
        for occupants, exits, width in cases:
            with self.subTest(occupants=occupants):
                self.assertEqual(ppe.b5(occupants), (exits, width, 1050))
        self.assertIsNone(ppe.b5(3001))

    def test_table_b2_starts_and_ends_as_in_the_data(self):
        self.assertEqual(ppe.b2(30), (1, 1050, 1050))
        self.assertEqual(ppe.b2(200), (2, 2100, 1050))
        self.assertEqual(ppe.b2(3000), (12, 18000, 1500))
        self.assertIsNone(ppe.b2(3001))


class PlacesOfPublicEntertainment(unittest.TestCase):
    def rows(self, **q):
        return ppe.run(dict({"occupant_capacity": 800}, **q))

    def test_small_premises_exemption(self):
        self.assertEqual(statuses(ppe.run({"occupant_capacity": 50}), "B19.2"), [PASS])
        self.assertEqual(statuses(ppe.run({"occupant_capacity": 51}), "B19.2"), [])
        self.assertEqual(statuses(ppe.run({"occupant_capacity": 50, "basement": True}), "B19.2"), [])
        self.assertEqual(statuses(ppe.run({"occupant_capacity": 50, "building_total_small_ppe": 151}), "B19.2"), [])

    def test_thoroughfares(self):
        self.assertEqual(statuses(ppe.run({"occupant_capacity": 500, "thoroughfares_m": [7.3, 4]}), "B20.8"), [PASS])
        self.assertEqual(statuses(ppe.run({"occupant_capacity": 500, "thoroughfares_m": [7.2, 4]}), "B20.8"), [FAIL])
        self.assertEqual(statuses(self.rows(thoroughfares_m=[12, 6]), "B20.4"), [PASS])
        self.assertEqual(statuses(self.rows(thoroughfares_m=[11.9, 6]), "B20.4"), [FAIL])
        self.assertEqual(statuses(self.rows(thoroughfares_m=[12]), "B20.1"), [FAIL])
        three = {"occupant_capacity": 3000}
        self.assertEqual(statuses(ppe.run(dict(three, thoroughfares_m=[12, 9])), "B20.5"), [PASS])
        self.assertEqual(statuses(ppe.run(dict(three, thoroughfares_m=[12, 8.9])), "B20.5"), [FAIL])
        self.assertEqual(statuses(ppe.run(dict(three, thoroughfares_m=[12, 6], second_is_footway=True)), "B20.5"), [PASS])
        five = {"occupant_capacity": 5000}
        self.assertEqual(statuses(ppe.run(dict(five, thoroughfares_m=[15, 9])), "B20.6"), [PASS])
        self.assertEqual(statuses(ppe.run(dict(five, thoroughfares_m=[14.9, 9])), "B20.6"), [FAIL])
        self.assertEqual(statuses(ppe.run({"occupant_capacity": 5001, "thoroughfares_m": [15, 9]}), "B20.7"), [CHECK])
        self.assertEqual(statuses(self.rows(frontage_fraction=0.5), "B20.2"), [PASS])
        self.assertEqual(statuses(self.rows(frontage_fraction=0.49), "B20.2"), [FAIL])

    def test_exits_above_12_m_use_table_b5(self):
        rows = self.rows(floor_level_m=12, exit_routes_mm=[2125, 2125, 2125, 2125])
        self.assertEqual(statuses(rows, "B21.1", "Number"), [PASS])
        self.assertEqual(statuses(rows, "B21.1", "Total"), [PASS])
        rows = self.rows(floor_level_m=12, exit_routes_mm=[2124, 2125, 2125, 2125])
        self.assertEqual(statuses(rows, "B21.1", "Total"), [FAIL])
        self.assertEqual(statuses(self.rows(floor_level_m=12, exit_routes_mm=[1049, 4000, 4000, 4000]), "B21.1", "Narrowest"), [FAIL])

    def test_wide_exits_are_capped_at_1_5_times_the_narrowest(self):
        rows = self.rows(floor_level_m=12, exit_routes_mm=[1050, 9000, 9000, 9000])
        self.assertEqual(statuses(rows, "B21.1", "Total"), [FAIL])

    def test_more_than_3000_goes_to_the_building_authority(self):
        rows = ppe.run({"occupant_capacity": 3001, "exit_routes_mm": [3000, 3000]})
        self.assertEqual(statuses(rows, "B21.1"), [CHECK])

    def test_shared_exits_above_3000_do_not_crash(self):
        q = {"occupant_capacity": 3001, "exit_routes_mm": [3000, 3000], "floor_level_m": 12,
             "cinema_in_building": {"shares_exits": True, "exit_width_through_other_accommodation_mm": 1000}}
        self.assertEqual(statuses(ppe.run(q), "B27.5(a)"), [CHECK])

    def test_tiers(self):
        self.assertEqual(statuses(self.rows(tier_gradient_deg=35), "B21.4"), [PASS])
        self.assertEqual(statuses(self.rows(tier_gradient_deg=35.1), "B21.4"), [FAIL])
        self.assertEqual(statuses(self.rows(min_headroom_m=3), "B21.4"), [PASS])
        self.assertEqual(statuses(self.rows(min_headroom_m=2.99), "B21.4"), [FAIL])

    def test_stairs(self):
        def stair(**s):
            return self.rows(staircases=[dict({"name": "S"}, **s)])
        self.assertEqual(statuses(stair(tread_mm=280, riser_mm=150), "B23.1(e)"), [PASS])
        self.assertEqual(statuses(stair(tread_mm=279, riser_mm=150), "B23.1(e)"), [FAIL])
        self.assertEqual(statuses(stair(tread_mm=280, riser_mm=151), "B23.1(e)"), [FAIL])
        self.assertEqual(statuses(stair(max_steps_per_flight=16, turn_between_flights=True), "B23.1(b)"), [PASS])
        self.assertEqual(statuses(stair(max_steps_per_flight=17, turn_between_flights=True), "B23.1(b)"), [FAIL])
        self.assertEqual(statuses(stair(max_steps_per_flight=12, min_steps_per_flight=2), "B23.1(b)"), [FAIL])
        self.assertEqual(statuses(stair(max_steps_per_flight=13), "B23.1(d)"), [FAIL])
        self.assertEqual(statuses(stair(successive_flights_without_turn=3), "B23.1(c)"), [FAIL])

    def test_table_b6_seats_in_a_row(self):
        cases = ((300, 7, 14), (325, 8, 15), (350, 9, 18), (375, 10, 20), (400, 11, 22), (425, 12, 24), (450, 12, 26), (475, 12, 28))
        for seatway, one, two in cases:
            with self.subTest(seatway=seatway):
                def row(seats, both):
                    return statuses(self.rows(seat_rows=[{"name": "A", "seatway_mm": seatway, "seats": seats, "gangway_both_sides": both}]), "Table B6")
                self.assertEqual(row(one, False), [PASS])
                self.assertEqual(row(one + 1, False), [FAIL])
                self.assertEqual(row(two, True), [PASS])
                self.assertEqual(row(two + 1, True), [FAIL])

    def test_seatway_of_500_is_limited_by_row_length(self):
        def row(length, both):
            return self.rows(seat_rows=[{"name": "A", "seatway_mm": 500, "seats": 99, "length_m": length, "gangway_both_sides": both}])
        self.assertEqual(statuses(row(24, True), "B27.6(a)"), [PASS])
        self.assertEqual(statuses(row(24.1, True), "B27.6(a)"), [FAIL])
        self.assertEqual(statuses(row(12.1, False), "B27.6(a)"), [FAIL])
        self.assertEqual(statuses(self.rows(seat_rows=[{"name": "A", "seatway_mm": 299, "seats": 1}]), "B27.6(b)"), [FAIL])

    def test_table_b7_gangways(self):
        for persons, need in ((500, 1100), (501, 1200), (1000, 1200), (1001, 1350), (1500, 1350), (1501, 1500)):
            with self.subTest(persons=persons):
                def gangway(width):
                    return statuses(self.rows(gangways=[{"name": "G", "persons_served": persons, "width_mm": width}]), "Table B7")
                self.assertEqual(gangway(need), [PASS])
                self.assertEqual(gangway(need - 1), [FAIL])

    def test_foyer(self):
        self.assertEqual(statuses(self.rows(seats=600, foyer_m2=50), "B27.8 / B(P)R 49E"), [PASS])
        self.assertEqual(statuses(self.rows(seats=600, foyer_m2=49.9), "B27.8 / B(P)R 49E"), [FAIL])
        self.assertEqual(statuses(self.rows(seats=600, foyer_m2=100, basement=True), "B27.3(f)"), [PASS])
        self.assertEqual(statuses(self.rows(seats=600, foyer_m2=99.9, basement=True), "B27.3(f)"), [FAIL])

    def test_cinema_limits(self):
        def cinema(**c):
            return self.rows(cinema_in_building=c)
        self.assertEqual(statuses(cinema(aggregate_cinema_occupancy=2000), "B27.1"), [PASS])
        self.assertEqual(statuses(cinema(aggregate_cinema_occupancy=2001), "B27.1"), [FAIL])
        self.assertEqual(statuses(cinema(projection_room_frr_min=59), "C18.1(d)"), [FAIL])
        self.assertEqual(statuses(self.rows(basement=True, cinema_in_building={"basement_level": 2}), "B27.3"), [FAIL])

    def test_theatre_and_linings(self):
        good = {"sprinklered": True, "proscenium_frr_min": 60, "fire_curtain_frr_min": 30}
        self.assertEqual(statuses(self.rows(theatre=good), "C18.2"), [PASS])
        for key, value in (("sprinklered", False), ("proscenium_frr_min", 59), ("fire_curtain_frr_min", 29)):
            self.assertEqual(statuses(self.rows(theatre=dict(good, **{key: value})), "C18.2"), [FAIL], key)
        self.assertEqual(statuses(self.rows(lining_class="C"), "E13.1(c) / E14.1(c)"), [PASS])
        self.assertEqual(statuses(self.rows(lining_class="D"), "E13.1(c) / E14.1(c)"), [FAIL])


class FireEngineering(unittest.TestCase):
    ROOM = {"name": "R", "use_class": "4a", "floor_area_m2": 500, "ceiling_height_m": 6, "growth": "medium", "sprinklered": False,
            "hrr_cap_kw": 2000, "detection_s": 60, "alarm_s": 30, "pre_movement_s": 120, "occupants": 100, "travel_distance_m": 60,
            "exit_widths_mm": [2000], "walking_speed_m_s": 1.2, "specific_flow_p_s_m": 1.3}

    def time_to_layer(self, **room):
        s = dict(self.ROOM, **room)
        time = fe.aset(s, s["hrr_cap_kw"])[0]
        return float("inf") if time is None else time  # None: the layer never reaches the criterion in the simulation

    def verdict(self, **room):
        rows = fe.run({"scenarios": [dict(self.ROOM, **room)]})
        return [r for r in rows if r[0] == "G3.4 / G6.4"][0]

    def test_growth_constants(self):
        self.assertEqual(fe.G["t2_alpha_kw_s2"], {"slow": 0.00293, "medium": 0.01172, "fast": 0.0469, "ultra_fast": 0.1876})

    def test_tenability_and_default_safety_factor(self):
        self.assertEqual(fe.G["tenability_G6_8"]["smoke_layer_height_m"], 2.0)
        self.assertEqual(fe.G["safety_factor_G3_4"]["typical_min"], 1.5)

    def test_smoke_layer_behaves_as_expected(self):
        medium = self.time_to_layer()
        self.assertLess(medium, 1800)
        self.assertLess(self.time_to_layer(growth="fast"), medium)
        self.assertGreater(self.time_to_layer(growth="slow"), medium)
        self.assertGreater(self.time_to_layer(floor_area_m2=2000), medium)
        self.assertLess(self.time_to_layer(ceiling_height_m=4), medium)
        self.assertGreater(self.time_to_layer(extract_m3_s=10), medium)

    def test_rset_adds_detection_alarm_pre_movement_and_movement(self):
        rows = []
        result = fe.rset(dict(self.ROOM), lambda *a, **k: rows.append(a))
        det, alarm, pre, travel, flow, width, move, total = result
        self.assertEqual((det, alarm, pre), (60, 30, 120))
        self.assertAlmostEqual(travel, 50)
        self.assertAlmostEqual(width, 1.7)
        self.assertAlmostEqual(flow, 100 / (1.3 * 1.7))
        self.assertAlmostEqual(move, 50)
        self.assertAlmostEqual(total, 260)

    def test_movement_can_be_summed(self):
        result = fe.rset(dict(self.ROOM, movement="sum"), lambda *a, **k: None)
        self.assertAlmostEqual(result[6], 50 + 100 / (1.3 * 1.7))

    def test_no_exit_width_gives_infinite_flow_time_and_fails(self):
        self.assertEqual(self.verdict(exit_widths_mm=[])[4], FAIL)

    def test_verdict_uses_factor_or_margin(self):
        self.assertIn("1.5 × RSET = 390", self.verdict()[3])
        self.assertIn("margin 100 s = 360", self.verdict(safety_margin_s=100)[3])

    def test_tight_room_fails_and_large_room_passes(self):
        self.assertEqual(self.verdict(floor_area_m2=50, ceiling_height_m=3)[4], FAIL)
        self.assertEqual(self.verdict(floor_area_m2=5000, ceiling_height_m=15, growth="slow")[4], PASS)

    def test_co_and_visibility_are_always_a_check(self):
        rows = fe.run({"scenarios": [dict(self.ROOM, floor_area_m2=5000, ceiling_height_m=15, growth="slow")]})
        self.assertEqual([r[4] for r in rows if "CO, visibility" in r[1]], [CHECK])

    def test_design_fire_from_table_g1(self):
        rows = []
        s = {"name": "R", "use_class": "4a", "sprinklered": True, "ceiling_height_m": 2.5}
        self.assertEqual(fe.hrr_cap(s, lambda *a: rows.append(a))[0], 1500)
        self.assertEqual(rows, [])
        fe.hrr_cap(dict(s, ceiling_height_m=4), lambda *a: rows.append(a))
        self.assertEqual(rows[0][4], CHECK)
        self.assertEqual(fe.hrr_cap(dict(s, use_class="2", ceiling_height_m=3.0), lambda *a: None)[0], 1700)

    def test_unsprinklered_fire_without_a_peak_is_a_check(self):
        rows = []
        cap, _ = fe.hrr_cap({"name": "R", "sprinklered": False}, lambda *a: rows.append(a))
        self.assertIsNone(cap)
        self.assertEqual(rows[0][4], CHECK)

    def test_pre_movement_from_table_g2(self):
        rows = []
        s = {"name": "R", "occupant_category": "awake_familiar", "alarm": "standard"}
        self.assertEqual(fe.g2_pre(s, lambda *a: rows.append(a)), 120)
        self.assertEqual(fe.g2_pre(dict(s, occupant_category="nobody"), lambda *a: rows.append(a)), None)
        self.assertEqual(rows[-1][4], FAIL)

    def test_lower_bound_pre_movement_is_a_check(self):
        rows = []
        s = {"name": "R", "occupant_category": "awake_familiar", "alarm": "local"}
        self.assertEqual(fe.g2_pre(s, lambda *a: rows.append(a)), 900)
        self.assertEqual(rows[0][4], CHECK)

    def test_missing_pre_movement_fails(self):
        rows = []
        room = {k: v for k, v in self.ROOM.items() if k != "pre_movement_s"}
        fe.rset(room, lambda *a, **k: rows.append(a))
        self.assertEqual([r[4] for r in rows if "pre-movement" in r[1]], [FAIL])


class Lookup(unittest.TestCase):
    def run_tool(self, *args):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["fs_lookup.py", *args]), contextlib.redirect_stdout(out):
            lookup.main()
        return out.getvalue()

    def test_use_class(self):
        self.assertIn("Use Class 1a", self.run_tool("1a"))

    def test_performance_requirement(self):
        self.assertIn("Performance Requirement B1", self.run_tool("b1"))

    def test_definition_in_english_or_chinese(self):
        self.assertIn("Access staircase", self.run_tool("access staircase"))
        chinese = next(v["zh"] for v in lookup.A["definitions"].values() if v.get("zh"))
        self.assertIn(chinese, self.run_tool(chinese))

    def test_unknown_term(self):
        self.assertIn("No definition matches", self.run_tool("zzzz"))

    def test_clause_without_the_code_text(self):
        with mock.patch.object(lookup, "TEXT", [Path("does-not-exist.txt")]):
            self.assertIn("not found", self.run_tool("--clause", "C13.4"))

    def test_clause_from_a_code_text_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = Path(tmp) / "code.txt"
            text.write_text("Clause C13.4\nFirst line\nClause C13.5\nNext clause\n", encoding="utf-8")
            with mock.patch.object(lookup, "TEXT", [text]):
                out = self.run_tool("--clause", "C13.4")
                self.assertIn("First line", out)
                self.assertNotIn("Next clause", out)
                self.assertIn("not found", self.run_tool("--clause", "Z9.9"))


class ExampleReports(unittest.TestCase):
    CASES = (("bpr_check.py", "demo_composite.json", "demo_composite_report.md"),
             ("moe_check.py", "demo_composite.json", "demo_composite_moe_report.md"),
             ("fire_cd_check.py", "demo_composite.json", "demo_composite_fire_cd_report.md"),
             ("part_e_check.py", "demo_composite.json", "demo_composite_part_e_report.md"),
             ("part_f_check.py", "demo_composite_fsm_energy.json", "demo_composite_part_f_report.md"),
             ("fsi_check.py", "demo_composite_fsm_energy.json", "demo_composite_fsi_report.md"),
             ("energy_check.py", "demo_composite_fsm_energy.json", "demo_composite_energy_report.md"),
             ("ppe_check.py", "demo_cinema.json", "demo_cinema_report.md"),
             ("fire_eng_timeline.py", "demo_atrium_fe.json", "demo_atrium_fe_report.md"),
             ("sbd_check.py", "demo_composite_design.json", "demo_composite_app152_report.md"),
             ("bfa_check.py", "demo_composite_design.json", "demo_composite_bfa_report.md"),
             ("cost_estimate.py", "demo_practice.json", "demo_practice_cost_report.md"),
             ("supervision_plan.py", "demo_practice.json", "demo_practice_supervision_report.md"),
             ("massing_study.py", "demo_massing.json", "demo_massing_report.md"),
             ("submission_timeline.py", "demo_submission.json", "demo_submission_report.md"))

    def test_committed_reports_match_the_tools(self):
        for tool, demo, report in self.CASES:
            with self.subTest(report=report), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "report.md"
                subprocess.run([sys.executable, str(ROOT / "tools" / tool), str(ROOT / "examples" / demo), "-o", str(out)],
                               capture_output=True, cwd=ROOT)
                got = out.read_text(encoding="utf-8").replace("\r\n", "\n")
                want = (ROOT / "examples" / report).read_text(encoding="utf-8").replace("\r\n", "\n")
                self.assertEqual(got, want, f"Regenerate examples/{report}")


if __name__ == "__main__":
    unittest.main()
