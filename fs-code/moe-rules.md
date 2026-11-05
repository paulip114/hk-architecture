# Means of escape – working rules (FS Code 2011, 2024 Edition, Part B)

Source: Code of Practice for Fire Safety in Buildings 2011 (2024 Edition, amendments to Sept 2024), full text at `architect-kb/fs-code-2011.txt` (user upload). Quote the code, not this summary, in submissions. Data tables: `moe_tables.json`. Checker: `tools/moe_check.py`.

## Use classifications (Table A1)
1a houses ≤ 3 storeys · 1b flats · 1c tenement · 2 hotels/hostels/dormitories · 3a health/child care · 3b detention · 4a offices · 4b retail, restaurants, banks · 5a places of public entertainment · 5b schools · 5c transport · 5d other assembly · 6a industrial · 6b warehouses · 6c dangerous goods · 7 car parks · 8 plant rooms.

## Occupant capacity (B4, Table B1) – usable floor area ÷ factor (m²/person)
| Use | Factor |
| --- | --- |
| Flats, corridor/balcony access with ≥ 5 flats per floor per stair | 4.5 |
| Other flats | 9 |
| Offices · board/conference/function rooms · staff rooms | 9 · 10 · 9 |
| Retail B/F–2/F · 3/F and above | 3 · 4.5 |
| Markets, supermarkets, showrooms | 2 |
| Restaurants, bars | 1 |
| Banking/betting halls, public counters | 0.5 |
| Classrooms, libraries · reading rooms | 2 · 1 |
| Gymnasia, pools (water area) | 3 |
| Factories, commercial kitchens | 4.5 |
| Laundries, labs | 10 |
| Warehouses, car parks, plant rooms | 30 (plant room ≤ 100 m² net = 0) |
| Hotels, hospitals (patient areas), detention | number of bedspaces |
| Fixed seating | number of seats (bench 450 mm/person) |

## Exits (B7, B8, Table B2)
- Every storey: ≥ 2 exit routes (unless B6.1 single stair). Widths per Table B2 by occupant capacity, e.g. 31–200 persons: 2 routes, total 2100 mm, each 1050 mm; 201–300: 2500 total; 301–500: 3000 total; 501–750: 3 routes, 4500 total, each 1200 mm.
- Width above 150% of the narrowest route/door is not counted (B7.3, B8.1(b)).
- Exit doors ≥ 750 mm (double leaf ≥ 600 mm each); open in direction of escape where > 30 persons (B13).

## Single staircase (B6.1)
≤ 6 storeys, top floor ≤ 17 m, domestic/office only (G/F shop or car park allowed). Top floor ≤ 13 m: UFA per storey ≤ 250 m². Above 13 m: UFA ≤ 150 m², protected lobby, stair to roof, roof refuge 0.5 m²/person.

## Travel distance (B11)
| Use | Deadend | Max with 2 exits | Balcony approach |
| --- | --- | --- | --- |
| 1, 2 | 24 m inside flat to flat door; 15 m flat door to stair / point of choice | 24 m flat door to nearest stair | 45 m |
| 3 | 12 m | 30 m | deadend 24 m / max 45 m |
| Others | 18 m | 36 m | deadend 24 m / max 45 m |
- Stair-to-stair along exit route ≤ 48 m (B11.3(b)); stair doors ≥ 6 m apart (B10.2(b)); 30° rule for alternative directions (B11.6-7).
- Inner rooms: ≤ 30 persons, through one room only, within deadend limit, vision panel (B11.5).

## Staircases
- Discharge value (B12, Tables B3/B4) of stairs serving upper storeys ≥ total occupants above G/F; separately for basements. Sprinkler table B4 roughly doubles single-storey values. Upward escape × 0.8; scissors stair without intermediate landing × 0.7. > 1800 mm by linear projection.
- Geometry (B14): straight flights, 2–16 risers, tread ≥ 225 mm, riser ≤ 175 mm (5a: 280/150; 5b: 250/150, riser ≥ 75), width ≤ 1800 mm per section (≥ 1050), headroom ≥ 2000 mm, handrails both sides 850–1100 mm.
- Protected lobby to every required stair (B10.4(b)) unless: single stair ≤ 13 m; two+ stairs with top floor ≤ 20 m; pressurised; or ventilated (≥ 50% perimeter open).
- Stairs from upper floors must not continue directly to basement (B17.3). Ramps ≤ 1:12 (B15).

## Basements (B17)
≥ 2 exits unless ≤ 3 m deep, ≤ 150 m² and lavatory/plant only. Where all exits go upward, each basement floor needs one independent exit. Protected lobby to basement stairs unless pressurised or independent.

## Refuge floors (B18)
Buildings > 25 storeys above lowest ground storey: refuge floor at ≤ 25 storeys (≤ 20 for Use Class 6) from ground or the previous refuge floor; plant-only storeys may be excluded. Net refuge area ≥ 50% of that floor's GFA, headroom ≥ 2300 mm, open on two opposite sides, stairs discontinued across it, fireman's lift only. Main roof may count (B18.3) if flat, refuge area ≥ 50% of typical floor GFA, stairs continue to roof.

## Not yet automated
Part B Section 3 (Use Class 5a, Tables B5-B7), Part C fire resisting construction, Part D means of access (firemen's lifts, EVA), Part E, fire engineering (Part G).
