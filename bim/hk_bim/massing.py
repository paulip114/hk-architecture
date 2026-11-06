# -*- coding: utf-8 -*-
"""Pure helpers for massing studies (Grasshopper / Dynamo).

Geometry is done in the host; these functions take plain numbers so they
can be tested here and reused by any host.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from .areas import make_record


def floor_levels(base_z, floor_heights, top_z):
    """Floor levels from base_z upward while below top_z.

    floor_heights: list of floor-to-floor heights; the last value repeats.
    Returns a list of (index, z). A slab exactly at top_z (the roof) is not a floor.
    """
    if not floor_heights:
        raise ValueError("floor_heights is empty")
    if any(h <= 0 for h in floor_heights):
        raise ValueError("floor heights must be positive")
    levels, z, i = [], float(base_z), 0
    while z < top_z - 1e-6:
        levels.append((i, z))
        z += floor_heights[min(i, len(floor_heights) - 1)]
        i += 1
        if i > 500:
            raise ValueError("more than 500 floors: check units / floor heights")
    return levels


def hk_floor_name(index, basement_count=0):
    """0 -> 'G/F', 1 -> '1/F'; with basements, indices below basement_count are B<n>/F."""
    if index < basement_count:
        return "B%d/F" % (basement_count - index)
    n = index - basement_count
    return "G/F" if n == 0 else "%d/F" % n


def massing_records(plates, podium_floors=0, building_type="composite",
                    mandatory_plant_pct=0.0, non_mandatory_pct=0.0, green_pct=0.0,
                    basement_count=0, base_z=0.0, ground_z=None):
    """Turn sliced floor plates into area records.

    plates           list of (index, z, area_m2) from the host's slicing
    podium_floors    floors above ground counted non-domestic (composite only)
    *_pct            share of each plate assumed exempt (e.g. 0.03 = 3%), a
                     placeholder until real plant rooms are drawn
    ground_z         z of G/F (default: base_z, or the first plate above basements)
    Returns (records, footprints {level: area}).
    """
    if ground_z is None:
        ground_z = base_z
        for idx, z, _ in plates:
            if idx == basement_count:
                ground_z = z
                break
    recs, fp = [], {}
    for idx, z, area in plates:
        name = hk_floor_name(idx, basement_count)
        above = idx - basement_count
        if building_type == "domestic":
            use = "domestic"
        elif building_type == "non_domestic":
            use = "non_domestic"
        else:
            use = "non_domestic" if (above < podium_floors or idx < basement_count) else "domestic"
        elev = z - ground_z
        if idx < basement_count:  # assumed basement car park, 100% disregarded (APP-2)
            recs.append(make_record("Basement car park (assumed)", name, area,
                                    category="car_park_underground", use=use, elevation_m=elev))
            continue
        split = [("mandatory_plant", mandatory_plant_pct), ("non_mandatory_plant", non_mandatory_pct),
                 ("green_feature", green_pct)]
        rest = area
        for cat, pct in split:
            if pct:
                a = area * pct
                rest -= a
                recs.append(make_record("%s allowance" % cat.replace("_", " "), name, a, category=cat,
                                        use=use, elevation_m=elev))
        recs.append(make_record("Floor plate", name, rest, category="accountable", use=use, elevation_m=elev))
        fp[name] = area
    return recs, fp
