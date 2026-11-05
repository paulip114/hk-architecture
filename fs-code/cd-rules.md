# Fire resisting construction (Part C) and means of access (Part D) – working rules

Source: Code of Practice for Fire Safety in Buildings 2011 (2024 Edition), `architect-kb/fs-code-2011.txt`; Part C pp.76-99, Part D pp.112-133. Data: `cd_tables.json`. Checker: `tools/fire_cd_check.py`. Quote the Code, not this summary, in submissions.

## Part C – Fire resisting construction

### Table C1: compartment size and FRR (minutes)
| Use class | Max compartment | FRR |
| --- | --- | --- |
| 1 Residential, 2 Hotel | not limited (each flat / guestroom a fire barrier) | 60 |
| 3 Institutional | 2,500 m² | 60 |
| 4a Offices | 10,500 m² | 60 |
| 4b Retail, 5a/5d Assembly, 5b Schools | ≤ 2,500 m² · ≤ 10,500 m² | 60 · 120 |
| 5c Transport | 10,500 m² | 120 |
| 6a Industrial | 10,500 m² | 120 |
| 6b Warehouses | 28,000 m³ and 10,500 m² | 120 |
| 6c Dangerous goods | 7,000 m³ | 120 |
| 7 Car parks | 10,500 m² | 60 |
Larger compartments: BA on individual merits with enhanced provisions. Table C2 sets which of stability / integrity / insulation each element must meet (e.g. doors and shutters integrity only; floors all three; non-loadbearing fire barrier walls integrity + insulation).

### Key clauses
- **C4.3** Single-storey ≤ 7,000 m³ and ≤ 7.5 m high may use unprotected steel if ≥ 6 m clear of other buildings / boundary.
- **C5.2** Buildings on the same site < 1.8 m apart are "adjoining": facades at > 135° → walls within 900 mm imperforate (unprotected openings ≥ 900 mm apart); ≤ 135° → within 1.8 m imperforate, FR fixed lights ≥ 900 mm away, unprotected openings ≥ 1.8 m apart. Roof within 1.8 m imperforate.
- **C5.3** Within 900 mm of a site boundary: external walls and roof imperforate with FRR of internal elements; openings only ≥ 450 mm from the boundary with FR fixed lights.
- **C6.1** Flats/guestrooms on a common internal corridor: corridor fire barriers per Table C1, flat doors same FRR with smoke seals.
- **C7** Different use classes / occupancies separated at the longer FRR. Not needed for ancillary offices, caretaker quarters, pantries; or between 4a occupancies or 4b retail shops within C1 limits. Common corridors to different occupancies separated at the floor's FRR (except shopping arcades). Deadend balcony approach: windows in Use Class 1 fixed and -/30/30.
- **C8.1** Openings in compartment walls need FR doors/shutters of the wall's FRR; if openings > 25% of the wall length, they also need full insulation (or 30 min with sprinklers both sides). C8.2-8.6 fire stops, dampers, shaft sealing.
- **C9.1** Liftwells 120/120/120; landing doors -/120/-; smoke seal lobby at basement where a lift also serves upper floors.
- **C9.3** Protected exits and lobbies at the FRR of the compartment; no services inside except emergency services unless enclosed.
- **C9.7-9.8** Stair / lobby external wall within 6 m of the opposite side of a street, a site boundary, a lower-FRR wall or another building: FRR of the stair wall, imperforate or FR fixed lights ≤ 25% of the storey's wall area. Where in the same plane as other external walls, stair walls return 450 mm.
- **C10.1** Unprotected floor openings (escalators, voids) only in sprinklered buildings, with a 450 mm -/30/- non-combustible downstand or smoke curtain.
- **C10.2** Curtain walls over one storey non-combustible; perimeter void sealed at floor FRR (leakage ≤ 25 m³/h/m² at 25 Pa).
- **C10.3** Atrium (sprinklered): separated, ≤ 28,000 m³, ≤ 15 m high, ≤ 3 floors interconnected.
- **C11.1** Non-sprinklered (except single houses): 900 mm spandrel or 500 mm horizontal projection between floors at storey FRR. C11.2: ≤ 110 mm pipe openings allowed in Use Class 1 kitchen/bathroom spandrels.
- **C12** Roofs non-combustible; FRR of storey below if roof is a refuge, single-stair escape > 13 m, or a temporary place of safety.
- **C13** Special hazards -/120/120 (-/240/240 if opening directly to a protected exit). Restaurant kitchens -/60/60; protected lobby onto building exit routes, and onto dining exit routes where kitchen UFA > 45 m². Flat with single exit door: kitchen by the door -/30/30 with FR door, or open-kitchen package (C13.4: smoke detectors in flat and common area, sprinkler, 600 mm -/30/30 wall by the door, 450 mm downstand if internal stair).
- **C14** Basements: elements 240/240/240; barrier to ground storey -/240/240; internal compartments -/120/120. Smoke outlets if enclosed on four sides: ≤ 30 m apart, high level, ≥ 0.5% of floor area (2.5% storage), least dimension ≥ 1 m, breakable covers, away from stair discharges. With dynamic extraction: 1 outlet per 3,500 m³ (min 1 per floor).
- **C15** Bridges and tunnels between buildings: fire barriers at each end at the longest FRR, or open non-combustible bridge.
- **C16** Fire doors self-closing, bottom gap ≤ 10 mm, signage "FIRE DOOR TO BE KEPT CLOSED 防火門應常關" (≥ 10 mm text); stair and lobby doors always closed. Protected lobby: one door at full FRR (other door no FRR), or both doors at half FRR; smoke seals on both.
- **C17** Refuge floor: walls -/120/120, floors 120/120/120; open sides ≥ 6 m from street opposite side, boundary, other building or < 120 min walls.

## Part D – Means of access

### Table D1 (B(P)R 41A, 41B, 41C)
Access staircases = as many as escape staircases in all multi-storey buildings (single access stair only for small domestic/office buildings in row (3)). Fireman's lift (FL) and firefighting and rescue stairway (FRS):
| Building | FL required | FRS required |
| --- | --- | --- |
| Domestic (or domestic part) > 2 storeys and > 30 m above lowest street | yes | – |
| Non-domestic (not 5a, hotels, hospitals, Class 6) > 2 storeys and > 30 m; or > 15 m and > 7,000 m³ | yes | – |
| 5a, hotels, hospitals > 2 storeys | yes | – |
| Class 6 > 2 storeys ≤ 30 m and ≤ 7,000 m³ | yes | – |
| Class 6 > 1 storey and (> 30 m or > 7,000 m³) | yes | yes |
| Basements > 7,000 m³ and (> 2 storeys or > 9 m deep) | yes | yes |
Every part of every floor within 60 m (along passages; 45 m direct line at design stage) of the FL / FRS lobby door. Height measured above the mean level of the lowest street.

### Fireman's lift (D6-D13)
Fire service access point at ground perimeter, from an FSD-accessible street or via open area ≥ 1.5 m; lift ≤ 18 m from it; passage ≥ 1500 mm wide, 2000 mm headroom, separated. Serve at least alternate floors uniformly, every refuge floor, and the top floor. Up to 3 FLs per liftwell. Car ≥ 1.1 m min dimension, ≥ 1.35 m², ≥ 680 kg; door ≥ 800 × 2000 mm. Lobby on each floor ≥ 2.25 m², min 1.5 m, FRR of floor (max 120), direct access to a protected exit.

### Firefighting and rescue stairway (D14-D21)
Serves every floor, refuge floor, roof, car parks; upper-floor stair does not continue to basement. Lobby 5–10 m², min 1.5 m, on an external wall with vents ≥ 25% of lobby area (top ≥ 1.9 m); basement lobbies 1 m² smoke outlet each. Stair ≥ 1050 mm, 2-16 risers, tread ≥ 225, riser ≤ 175; natural vent 15% per storey + 5% at top, or pressurised. Non-combustible throughout; openings ≥ 450 mm from other openings.

### Emergency vehicular access (D22-D26, B(P)R 41D)
| Item | Virgin site | Redevelopment site |
| --- | --- | --- |
| Width | 7.3 m carriageway or 6 m hard-paved | 6 m (7.3 m for Class 6) |
| Class 6 | two opposite facades, 13.5 m two-way (or 2 × 7.3 m), 6 m reserve if EVA outside site | one major facade, 7.3 m |
| Headroom · gradient | 4.5 m · ≤ 1:10 at major facades (1:6 elsewhere) | same |
| Vehicle | 30 t, 26 m turning circle, 12 m long; turning space at deadends | same |
| Facades served | ≥ 1/4 of perimeter incl. the major facade, within 10 m of the EVA (not above 60 m), uncovered | same |
Crash gate where EVA is not normally used; signs every 100 m, "No Parking" every 50 m. Exemption under 41D(3) needs a fire safety assessment report (Part G) and enhanced provisions (D26).
