# Architect knowledge base (Hong Kong)

Working knowledge and tools Claude reads before doing architect's work in this project. Every output from here is a draft for review and signature by an Authorized Person / Registered Architect.

| Path | What it is |
| --- | --- |
| `bpr/bpr-rules.md` | Building (Planning) Regulations working rules: site class, SC, PR, GFA exemptions (PNAP APP-2, APP-151), open space, lighting & ventilation |
| `bpr/first_schedule.json` | First and Second Schedule as data, verified against official Cap. 123F (17-09-2026) |
| Cap 123F consolidated PDF (17-09-2026) | Official text, primary B(P)R source. Not in the repo: download from eLegislation |
| `fs-code/moe-rules.md` | Means of escape rules (FS Code 2011, 2024 Ed., Part B) |
| `fs-code/moe_tables.json` | Tables A1, B1-B4, travel distances, stair and refuge limits as data |
| `fs-code-2011.txt` | Full FS Code text. Not in the repo (gitignored): download the Code from the BD website and save as text here |
| `skills/` | Copies of the saved Claude skills (B(P)R check, means of escape check) |
| `tools/moe_check.py` | Means of escape checker: `python3 tools/moe_check.py project.json` (reads the `means_of_escape` block) |
| `fs-code/cd-rules.md` | Fire resisting construction (Part C) and means of access / EVA (Part D) rules |
| `fs-code/cd_tables.json` | Tables C1, D1 limits, FL / FRS / EVA dimensions as data |
| `tools/fire_cd_check.py` | Part C + D checker (reads `fire_construction` and `means_of_access` blocks) |
| `tools/bpr_check.py` | Compliance checker: `python3 tools/bpr_check.py project.json -o report.md` |
| `examples/demo_composite.json` | Input template (composite building, Class B site) |
| `examples/demo_composite_report.md` | B(P)R output |
| `examples/demo_composite_moe_report.md` | Means of escape output |
| `examples/demo_composite_fire_cd_report.md` | Part C + D output |
| `fs-code/ppe-rules.md` | Use Class 5a places of public entertainment (B19-B28, C18) rules, Tables B5-B7 |
| `tools/ppe_check.py` | 5a checker (reads the `ppe` block) |
| `fs-code/part-e-rules.md`, `fs-code/part_e.json` | Part E: FRR of elements (Tables E2-E7), linings (E13/E14, Table E1), test standards |
| `tools/part_e_check.py` | Part E checker (reads the `part_e` block) |
| `fs-code/part-g-rules.md`, `fs-code/part_g.json` | Part G fire engineering: sub-systems, assessment types, Table G1, tenability, FSAR, bounding conditions |
| `tools/fire_eng_timeline.py` | ASET/RSET timeline screening (reads `fire_engineering`); screening only, not CFD |
| `examples/demo_cinema.json`, `demo_cinema_report.md` | 5a cinema demo |
| `examples/demo_composite_part_e_report.md` | Part E output |
| `examples/demo_atrium_fe.json`, `demo_atrium_fe_report.md` | Part G demo |
| `planning/planning-rules.md` | Town planning: OZP Notes (Column 1/2, Remarks), JPN 4/5 PR and height rules, s12A / s16 / s16A / s17 / appeal procedure and time limits, TPB guidelines, Bonus PR (JPN 9) and transfer of PR (PG-43A) |
| `lands/lands-rules.md` | Land administration: lease clauses, JPN 4 GFA groups under lease, GBP under lease (LAO PN 2/2018), approval / consent (PN 4/2021), lease modification and land exchange (PN 2/2023), premium and standard rates |
| `planning/planning_lands.json` | Time limits, JPN 5 roof-top limits, JPN 9 standard rates as data |
| `tools/planning_lease_check.py` | OZP + lease checker: `python3 tools/planning_lease_check.py project.json [--block planning.json]` (reads `planning_lease`; GFA from `floors[]`) |
| `examples/demo_composite_planning.json`, `demo_composite_planning_report.md` | OZP / lease demo for the composite building (fictional plan and lot) |

## Input fields (project.json)
- `site`: `area_m2`; either `class` ("A"/"B"/"C") or `street_widths_m` + `perimeter_m` + `frontage_on_specified_streets_m`; optional `dedicated_area_m2`.
- `building`: `type` ("domestic" / "non_domestic" / "composite"), `height_m` (from mean street level), optional `house` (true for detached/semi-detached).
- `limits` (optional): `max_height_m`, `ozp_max_pr_domestic`, `ozp_max_pr_non_domestic`, `ozp_max_pr_total`, `lease_max_gfa_m2`, `lease_min_gfa_m2`.
- `floors[]`: `name`, `use`, `level_m` (lowest level above ground), `gross_area_m2`, optional `count` (typical floors), `site_coverage_m2`, `exempt[]` of `{item, area_m2, category}`. Categories: `mandatory_plant`, `non_mandatory_plant`, `green_feature`, `car_park_underground`, `car_park_above_100`, `car_park_above_50`, `refuge_floor`, `bicycle_parking`, `other_disregarded`.
- `open_space` (domestic/composite): `provided_m2`, `roofed_over_area_m2`, optional `rear_setback_m`, `level_below_lowest_floor_mm`.
- `rooms[]`: `name`, `use` ("habitable"/"kitchen"/"office"/"bathroom"), `floor_area_m2`, `glass_m2`, `openable_m2`, optional `window_head_m`, `max_distance_to_window_m`, `ceiling_height_m`, `mechanical_ventilation_ach` (offices, reg 34), `external_air` (false to flag), `performance_based` (true to skip prescriptive test).

Exit code 1 when any item fails.

## Open items
- Planning / lands: Cap. 131 text not read (eLegislation unreachable); LAO PN 3/2020 (DDH) scanned, not read. See open items in `planning/planning-rules.md` and `lands/lands-rules.md`.
- Verify the APP-151 cap base and prerequisite list against the current PNAP.
- Not yet automated: reg 31 inclined-plane geometry, Part F (fire safety management).
- Barrier-free: Divisions 15-20 of the Design Manual not yet verified (lift and counter limits from memory, reported as CHECK).
- APP-152: Table 1 large-site columns and the Lp ≤ 5U limit to be checked against the PDF.
- B(C)R / B(A)R notes are unverified until the Cap. 123A / 123B PDFs are uploaded.
- Part G tool is a one-room screening; CO / visibility not modelled.

## Means of escape input (`means_of_escape` block)
- Top level: `sprinklered`, `storeys_above_ground`, `top_floor_level_m`, `refuge_floors` (storey numbers), `industrial`, `single_stair` {`max_storey_ufa_m2`, `domestic_or_office_only`}.
- `storeys[]`: `name`, `level` ("above"/"ground"/"basement"), `use_class`, `count`, `areas[]` of {`type` from moe_tables.json, `usable_area_m2`} or {`type`, `count`} for seats/bedspaces, or `occupants`; `exit_routes_mm[]`, `max_travel_m`, `max_deadend_m`, `max_within_flat_m`, `balcony_approach`, `stair_door_separation_m`, `max_stair_to_stair_m`, `basement_exemption`.
- `staircases[]`: `name`, `width_mm`, `storeys_served`, `serves` ("above"/"basement"), `upward`, `scissors`, `pressurised`/`protected_lobby`/`ventilated`, `tread_mm`, `riser_mm`, `risers_per_flight`, `central_handrail`, `use_class`.

## Fire construction / means of access input
- `fire_construction`: `sprinklered`, `single_family_house`, `compartments[]` {`name`, `use_class`, `area_m2`, `volume_m3`, `frr_min`, `basement`, `openings_fraction_of_wall`, `door_insulation_min`, `sprinklers_both_sides`}, `use_separation_frr_min`, `liftwell_frr_min`, `special_hazards[]` {`name`, `frr_min`, `opens_to_protected_exit`}, `restaurant_kitchens[]` {`name`, `frr_min`, `ufa_m2`, `protected_lobby`, `opens_to_building_exit_route`}, `open_kitchen_flats` {`provisions`[]}, `basement` {`barrier_to_ground_frr_min`, `floor_area_m2`, `smoke_outlet_area_m2`, `smoke_outlet_max_spacing_m`, `smoke_outlet_min_dim_m`, `storage`}, `external_wall` {`spandrel_m`, `projection_m`}, `boundary_walls[]`, `stair_external_walls[]`, `floor_voids[]`, `atria[]`.
- `means_of_access`: `parts[]` {`name`, `building_kind` = single_family / small_dom_office / domestic / non_domestic / special / industrial, `height_above_lowest_street_m`, `storeys`, `cubical_extent_m3`}, `basement` {`storeys`, `depth_m`, `cubical_extent_m3`}, `firemans_lifts`, `frs`, `max_distance_to_lobby_m`, `layout_known`, `fsap_distance_m`, `fsap_passage_width_mm`, `lift_car` {`min_dim_m`, `area_m2`, `load_kg`}, `lift_door_mm` [w, h], `fl_lobby` {`area_m2`, `min_dim_m`}, `frs_lobby` {`area_m2`, `min_dim_m`, `vent_area_m2`, `pressurised`}, `eva` {`site` virgin/redevelopment, `width_m`, `carriageway`, `industrial`, `headroom_m`, `gradient`, `facade_served_fraction`, `deadend`, `turning_space`, `not_normally_used`, `crash_gate`}.

## 5a, Part E, Part G inputs
- `ppe`: see docstring of `tools/ppe_check.py` (auditoria with seats, level_m, exits, tiers, stairs, rows {seats, seatway_mm, gangway_sides, length_m}, gangways, foyer, projection room, linings).
- `part_e`: `elements[]` {name, type (key in part_e.json), required_frr 60/120/240, thickness_mm / size_mm / width_mm / waist_mm / protection_mm, cover_mm, continuous}; `linings[]` {name, location, euro_class or bs476_class}; `products[]` {name, standard, test_report_lab_accredited}.
- `fire_engineering.scenarios[]`: name, use_class (Table G1 key), floor_area_m2, ceiling_height_m, growth, sprinklered, optional hrr_cap_kw / fuel_load_mj_m2 + fire_area_m2, extract_m3_s, detection_s, alarm_s, pre_movement_s, or occupant_category (awake_familiar / awake_unfamiliar / sleeping_familiar_dwelling / sleeping_familiar_serviced / sleeping_unfamiliar / awake_assisted / sleeping_assisted) + alarm (voice / standard / local) + optional pre_movement_source, building_complexity (Table G2), occupants, travel_distance_m, exit_widths_mm[], walking_speed_m_s, specific_flow_p_s_m, movement (max/sum), safety_factor or safety_margin_s.

## Design guides: APP-152, barrier-free access, B(C)R / B(A)R
| Path | What it is |
| --- | --- |
| `pnap/app152-rules.md`, `pnap/app152.json` | PNAP APP-152 (Sept 2023): building separation, setback, site coverage of greenery |
| `tools/sbd_check.py` | APP-152 checker (reads `sustainable_design`) |
| `bfa/bfa-rules.md`, `bfa/bfa2008.json` | Design Manual: Barrier Free Access 2008 (2025 Ed.) obligatory requirements, Tables 1-2 |
| `tools/bfa_check.py` | Barrier-free checker (reads `barrier_free`) |
| `bcr-bar/bcr-bar-rules.md` | Cap. 123B / 123A outline. Unverified until the official PDFs are uploaded |
| `examples/demo_composite_design.json` | Demo inputs for both tools (same fictional scheme as `demo_composite.json`) |
| `examples/demo_composite_app152_report.md`, `demo_composite_bfa_report.md` | Outputs |

- `sustainable_design`: `site_area_m2`, `tallest_height_m`, `street_canyon_width_m`, `planes[]` {`name`, `lp_m`, `zones` {low/middle/high: {`p_pct`, `is_pct`}}, `min_is_to_boundary_m`, `min_is_between_facades_m`}, `streets[]` {`name`, `width_m`, `building_height_m`, `option` corridor/podium_garden, `min_dist_to_centreline_m`, `podium_clear_height_m`, `within_45deg_plane`, `projection_mm`}, `greenery[]` {`name`, `type` (key of `greenery_factors`), `area_m2`, `zone` primary/other}.
- `barrier_free`: see the docstring of `tools/bfa_check.py` (car park, access route, ramps, stairs, handrails, corridors, doors, toilets, hotel, auditoria, lifts, counters, Table 2 uses and features).

## Building submission procedures
See `submission/README.md`: BD plan submission, consent, OP, minor works, UBW, MBIS / MWIS, with `tools/submission_timeline.py` and templates.
