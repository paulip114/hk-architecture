# Reference

Every file in the knowledge base and the input fields each tool reads. For an overview, see the [README](../README.md). Paths are relative to the repo root.

Unfinished work is tracked in [GitHub issues](https://github.com/paulip114/hk-architecture/issues), not in this file.

## Core files

| Path | What it is |
| --- | --- |
| `statutes/eia-rules.md` | EIA Ordinance (Cap. 499): how to tell whether a scheme is affected, and what is required |
| `statutes/railway-protection-rules.md` | Railway protection (PNAP APP-24, Cap. 519, Cap. 276): how to tell whether a site is affected, process and design limits |
| `statutes/building-management-rules.md` | Building Management Ordinance (Cap. 344): common parts, owners' decisions and DMCs for design and A&A work |
| `statutes/lifts-escalators-rules.md` | Lifts and Escalators Ordinance (Cap. 618): responsible person, examination and use permits |
| `statutes/small-house-rules.md` | NT Small House Policy: eligibility, grant types, Cap. 121 limits and procedure |
| `statutes/nt-land-exchange-rules.md` | NT land exchange: which arrangement applies, NDAs and the standard rate pilot |
| `statutes/land-resumption-rules.md` | Cap. 124 process, statutory compensation and ex-gratia compensation |
| `docs/document-library.md` | Source documents used to check the rules: version dates, official links and what each is used for. The documents are not in the repo |
| `docs/document-dependencies.json` | How the documents in the library depend on each other across project stages. An edge from A to B means A depends on B. Each edge records its type, evidence and whether it is documented or inferred. Draft for AP review |
| `docs/document-dependency-graph.html` | Interactive view of `docs/document-dependencies.json`. Download it and open it in a browser. It holds a copy of the data, so update both together. Draft for AP review |
| `docs/assets/document-dependencies.svg` | Overview of the document dependencies for the README. Hand-drawn, so update it if the main links change |
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
| `tools/planning_lease_check.py` | OZP + lease checker: `python3 tools/planning_lease_check.py project.json [--block planning.json]` (reads `planning_lease`; GFA from `floors[]`; with `minor_relaxation: true`, a height or PR excess up to 20% is `CHECK` (s16), a larger one `FAIL` (s12A). The 20% is a screening assumption, [#90](https://github.com/paulip114/hk-architecture/issues/90)) |
| `examples/demo_composite_planning.json`, `demo_composite_planning_report.md` | OZP / lease demo for the composite building (fictional plan and lot) |
| `design/` | Massing study methods, design statement guide and templates, architectural movements and masters (see `design/README.md`) |
| `tools/massing_study.py` | Massing options and development envelope, runs `bpr_check` on each option (`examples/demo_massing.json`) |

## Input fields (project.json)
- `site`: `area_m2`; either `class` ("A"/"B"/"C") or `street_widths_m` + `perimeter_m` + `frontage_on_specified_streets_m`; optional `dedicated_area_m2`.
- `building`: `type` ("domestic" / "non_domestic" / "composite"), `height_m` (from mean street level), optional `house` (true for detached/semi-detached).
- `limits` (optional): `max_height_m`, `ozp_max_pr_domestic`, `ozp_max_pr_non_domestic`, `ozp_max_pr_total`, `lease_max_gfa_m2`, `lease_min_gfa_m2`.
- `floors[]`: `name`, `use`, `level_m` (lowest level above ground), `gross_area_m2`, optional `count` (typical floors), `site_coverage_m2`, `exempt[]` of `{item, area_m2, category}` plus optional `serves` (`domestic` or `non_domestic`, for a capped feature serving the other part). Categories: `mandatory_plant`, `non_mandatory_plant`, `green_feature`, `green_feature_uncapped`, `car_park_underground`, `car_park_above_100`, `car_park_above_50`, `refuge_floor`, `bicycle_parking`, `other_disregarded`.
- `open_space` (domestic/composite): `provided_m2`, `roofed_over_area_m2`, optional `rear_setback_m`, `level_below_lowest_floor_mm`.
- `rooms[].reg_31`: `{faces_street_ge_4_5m: true}`, or `plane_base_m`, `plane_depth_m`, `uncovered`, `opposite` (`building` or `boundary`), optional `lane_width_m`, and `obstructions[]` of `{name, distance_m, height_above_sill_m}`. `distance_m` runs from the window wall, or from the actual boundary towards the site when `opposite` is `boundary`. The sill is deemed to be 1 m above the floor.
- `rooms[]`: `name`, `use` ("habitable"/"kitchen"/"office"/"bathroom"), `floor_area_m2`, `glass_m2`, `openable_m2`, optional `window_head_m`, `max_distance_to_window_m`, `ceiling_height_m`, `mechanical_ventilation_ach` (offices, reg 34), `reg_31` (see below), `performance_based` (true to skip prescriptive test).

Exit code 1 when any item fails.

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
| `bcr-bar/bcr-bar-rules.md` | Cap. 123A plans, scales and statutory periods (verified); Cap. 123Q B(C)R outline (unverified) |
| `examples/demo_composite_design.json` | Demo inputs for both tools (same fictional scheme as `demo_composite.json`) |
| `examples/demo_composite_app152_report.md`, `demo_composite_bfa_report.md` | Outputs |

- `sustainable_design`: `site_area_m2`, `tallest_height_m`, `street_canyon_width_m`, `planes[]` {`name`, `lp_m`, `zones` {low/middle/high: {`p_pct`, `is_pct`}}, `min_is_to_boundary_m`, `min_is_between_facades_m`}, `streets[]` {`name`, `width_m`, `building_height_m`, `option` corridor/podium_garden, `min_dist_to_centreline_m`, `podium_clear_height_m`, `within_45deg_plane`, `projection_mm`}, `greenery[]` {`name`, `type` (key of `greenery_factors`), `area_m2`, `zone` primary/other}.
- `barrier_free`: see the docstring of `tools/bfa_check.py` (car park, access route, ramps, stairs, handrails, corridors, doors, toilets, hotel, auditoria, lifts, counters, Table 2 uses and features).

## Practice: contracts, cost, site supervision, sketch drawings
| Path | What it is |
| --- | --- |
| `contracts/contract-rules.md`, `contracts/sfbc.json` | HKIA/HKIS/HKICM SFBC (2005/2006 rev. 2023; 2025 Ed. periods checked against a pre-launch copy) clause map, periods, appointment, tender, PA Paper 2 notes |
| `tools/contract_admin.py` | Extended Completion Date, LD (with cap and pending EOT), retention and release dates, DLP, notice checks (cl. 4.2, 25.2, 28.2), CISPO (Cap. 652) payment response / payment deadlines. Reads `contract` |
| `cost/cost-rules.md`, `cost/hk_cost_rates.json` | Cost planning stages, Arcadis Q2 2026 HK$/m² CFA rates, TPI |
| `tools/cost_estimate.py` | Order-of-cost estimate with low/mid/high range, allowances, escalation, fees, budget, S-curve. Reads `cost` (and `floors[]` via `from_floors`) |
| `supervision/site-supervision-rules.md`, `supervision/supervision.json` | CoP for Site Supervision 2009 (2024 Ed.): TCP T1-T5, frequency levels, Table 8.1 scale factors |
| `tools/supervision_plan.py` | Scale factors, TM Table 1 minimum TCP grade and frequency per stream, TCP schedule and effort, submission timing. Reads `supervision` |
| `drawing/drawing-rules.md` | What the drawing tools can and cannot do; workflow to B(P)R and cost |
| `tools/dxf_plan.py` | Sketch plans (DXF + SVG) with grid, rooms, areas, title block; area schedule JSON for `bpr_check.py`. Reads `drawing` |
| `tools/ifc_model.py` | IFC4 massing model (storeys, slabs, walls, spaces with areas). Reads `drawing` |
| `tools/dxf_area_takeoff.py` | Area take-off from any DXF by layer, with holes and text labels |
| `examples/demo_practice.json` | Demo for all six tools; outputs `demo_practice_*` |
| `tests/test_practice_tools.py` | `python3 -m unittest discover -s tests` |
| `tests/test_compliance_rules.py` | Tests for the APP-151 cap, B(P)R reg 31, the APP-152 figures and the barrier-free lift and counter limits, run by the same command |
| `tests/test_document_dependencies.py` | Checks the dependency data and that the interactive page holds the same data |
| `tests/test_fire_tools.py` | Boundary tests for the fire safety tools and `fs_lookup.py`, and a check that committed example reports match the tools |
| `.github/workflows/tests.yml` | Runs the tests and BIM tests with the drawing packages on Linux (Python 3.9 and 3.13) and Windows (Python 3.13) |

Drawing tools need `pip install -r requirements-drawing.txt` (ezdxf, ifcopenshell, shapely, pillow). Every output is a draft: contract results for the Architect / QS against the signed contract, cost for a QS to develop, supervision plan for the AP / RSE / AS, drawings marked "SKETCH – NOT FOR SUBMISSION".
## Fire Code Part A / Part F, FSD minimum FSI, energy efficiency
| Path | What it is |
| --- | --- |
| `fs-code/part-a-rules.md`, `fs-code/part_a.json` | Part A: framework, Table A1 use classes, Performance Requirements B1-F1, 42 definitions (verbatim) |
| `tools/fs_lookup.py` | `fs_lookup.py "travel distance"` / `fs_lookup.py 庇護` / `fs_lookup.py 4b` / `fs_lookup.py --clause C13.4` |
| `fs-code/part-f-rules.md`, `fs-code/part_f.json` | Part F: FSMP (maintenance, training, fire action plans), Bounding Conditions, open kitchens, lift works, Table F1 |
| `tools/part_f_check.py` | Part F checker (reads `fire_safety_management`) |
| `fsi/fsi-rules.md`, `fsi/fsi_schedule.json` | FSD CoP Minimum FSI (Sept 2022) Part IV, all 45 paras with the Code's own applicability wording (Chinese text) |
| `tools/fsi_check.py` | Minimum FSI checker (reads `fsi`) |
| `energy/energy-rules.md`, `energy/energy.json` | OTTV (APP-67), RTTV / VLT / ER (APP-156), both Sept 2025; BEC 2024 LPD, COP, lift, retrofit triggers |
| `tools/energy_check.py` | OTTV calculator (OTTV Code 1995 Tables 1-9, U from layers, ESM from OPF / SPF; `--selftest` reproduces the Code's sample) + RTTV / BEC checks (reads `energy`) |
| `examples/demo_composite_fsm_energy.json` | Demo inputs for the three tools (same fictional scheme) |
| `examples/demo_composite_part_f_report.md`, `demo_composite_fsi_report.md`, `demo_composite_energy_report.md` | Outputs |

Input blocks: see each tool's docstring (`python3 tools/<tool>.py -h`).
