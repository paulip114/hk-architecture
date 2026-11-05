# Part G – Fire engineering (FS Code 2011, 2024 Ed.)

Draft working rules for an Alternative Solution. The AP proposes; the Building Authority accepts case by case. Source: `../fs-code-2011.txt` lines ~5708–7802.

## When Part G is used
- An Alternative Solution to any Deemed-to-Comply provision (e.g. extended travel distance, large compartment, atrium, reduced exit width).
- Must meet the Performance Requirements of Parts A–F; evaluate against the guidance (G2.3).
- Pre-submission enquiry to BD / FSD is recommended before formal plans (G6.3).

## Six sub-systems (G5)
1. Fire initiation and development
2. Smoke development, spread and control
3. Detection, warning and automatic suppression
4. Fire spread, impact and control
5. Occupant characteristics and evacuation
6. Fire service intervention

## Assessment types (G6.4)
| Type | Scope | Notes |
| --- | --- | --- |
| 1 | One sub-system, qualitative or simple calculation | Can be an equivalence argument |
| 2 | More than one sub-system, quantitative timeline (ASET vs RSET) | Most common |
| 3 | All six sub-systems, probabilistic | Comparative only, special/complex buildings |

The Type 2 timeline is the sum of four items: detection, pre-movement, travel, and time to clear the compartment. It is compared with the fire and smoke development time, after applying a safety factor or margin.

## Safety factor (G3.4)
- For normal scenarios, the typical safety factor is 1.5–2.0.
- The factor can be reduced or omitted where a single-system-failure analysis proves the design reliable.
- Margins (time-based) suit life-safety timelines. Factors suit comparative or test methods. Agree which applies case by case.

## Design fires (G6.5, Table G1)
- t² growth: slow 0.00293, medium 0.01172, fast 0.0469, ultra-fast 0.1876 kW/s².
- Sprinkler-controlled HRR at standard-response heads:

| Use | HRR | Headroom |
| --- | --- | --- |
| Hotel, health care, plant rooms | 1.7 MW | 3.0 m |
| Detention, office, mercantile, 5a, 5d | 1.5 MW | 2.5 m |
| Industrial / warehouse | 2.0 MW | 3.5 m |

- Residential:
  - Pre-flashover, medium growth.
  - Post-flashover, ventilation-controlled (CIBSE Guide E / TM19).
- Unsprinklered mercantile: Q_U (kW/m²) = q (kJ/m²) / 1200.
- Train fire: 5–22 MW.
- Carpark: a single-vehicle fire.
- Use classes 5b and 5c have no value in the table.
- If the headroom differs from the Table G1 value, recalculate sprinkler activation.

## Tenability criteria (G6.8)
| Parameter | Criterion |
| --- | --- |
| Smoke layer height | ≥ 2 m (FSD CL 4/96) |
| Radiation | ≤ 2.5 kW/m² (layer ~200 °C) |
| CO | ≤ 1000 ppm |
| Optical density | ≤ 0.1 m⁻¹ (10 m visibility) |
| Smoke temperature below layer height | ≤ 60 °C |

## Occupant movement (G6.7, Table G2)
- Pre-movement time is a distribution: first few occupants and last few occupants.
- It is longer for sleeping occupants. Add 0.5–1.0 min for complex buildings.
- Table G2 (p.221) is stored in `part_g.json` (image: `table_G2_p221.png`). Values are in minutes.
- Sources: PD 7974-6 T1 (first few) and T2 (last few), SFPE, NZ Framework (room of origin / remote), CIBSE Guide E.
- Alarm types: voice alarm / trained staff; standard alarm throughout; local alarm / non-trained staff.

| Category (PD 7974 T2, standard alarm) | Minutes |
| --- | --- |
| Awake, familiar (office, industrial) | 2 |
| Awake, unfamiliar (retail, cinema) | 3 |
| Sleeping, dwelling | 5 |
| Serviced flats, hall of residence | 25 |
| Hotel | 20 |
| Day care, clinic | 3 |
| Hospital, nursing home | 20 |

- Notes: (c) large complex building +0.5 (awake familiar); (d) simple multi-storey +0.5 and (e) large complex +1.0 (awake unfamiliar); (f) depends on staff (assisted).
- Use one source consistently through the whole assessment.
- Walking speed (1.2 m/s), specific flow (1.3 p/s/m) and the 150 mm boundary layer are SFPE / PD 7974-6 values, not Code values. Justify them in the FSAR.

## FSAR contents (G7.1)
- (a) Introduction: problems, objectives, key parameters.
- (b) Building and use: site, form, use classes, occupancy, special features.
- (c) Code compliance: DtC items not complied with, Alternative Solutions, Performance Requirements, guidance used.
- (d) Technical justification: sub-systems, acceptance criteria, method, tools, hazards and fire loads, scenarios and design fires, interactions, safety factor.
- (e) Trial design: active and passive provisions, management, means of escape strategy, smoke control (purpose, activation, capacity, zoning), fire spread, structure, sprinklers, alarm, first-aid firefighting, facilities for firefighters.
- (f) Then: results, sensitivity, conclusions, and references.

Also cover:
- G7.2 structural performance.
- G7.3 commissioning and field testing, including hot smoke tests.
- G7.4 maintenance and management.

## Bounding conditions (G8)
- These are the limits the Alternative Solution depends on: fire load, occupancy, use, management, and system reliability.
- They are written into the approval and must be maintained for the life of the building.
- Any change outside them needs reassessment.

## Computer models (G9)
- Zone models (e.g. CFAST) and CFD (e.g. FDS) for smoke.
- Evacuation models for movement.
- State validation, grid sensitivity, inputs and limitations.

## Tool
- `../tools/fire_eng_timeline.py` gives a Type 2 screening for one room.
- Smoke filling uses a one-zone model with Heskestad / Zukoski plume entrainment and energy balance, plus optional extraction.
- RSET = detection + alarm + pre-movement + max(travel, flow).
- It is not a substitute for CFD or the FSAR.
