# Part A – Introduction, performance requirements, definitions (FS Code 2011, 2024 Ed.)

Data: `part_a.json` (42 definitions copied verbatim from Section 3, Table A1 use classes, Performance Requirements B1–F1). Lookup: `../tools/fs_lookup.py`.

## How the Code works (A1–A4)
- Hierarchy: BO goal, then Regulations (functional statements), then Performance Requirements, then either Deemed-to-Comply provisions (Parts B–E) or an Alternative Solution (Part G fire engineering).
- Compliance (A3.1): Deemed-to-Comply, an Alternative Solution, or a mix of the two.
- Parts F and G are guidelines. The FSD Code of Practice for Minimum FSI (A4.2) and the licensing authorities' codes (A4.3, Annex A) are read with this Code.
- A5.1: a change of Use Classification is a material change in use (BO s.25). A change of Bounding Conditions may also need a submission to the BA.
- A6.1: Deemed-to-Comply does not cover organised arson or terrorism.

## Use classification (Table A1)
| Class | Use | Notes |
| --- | --- | --- |
| 1a / 1b / 1c | House (≤ 3 storeys) / flats incl. service apartments / tenement houses | occupants familiar, may be asleep |
| 2 | Hotels, guesthouses, hostels, dormitories | asleep and unfamiliar |
| 3a / 3b | Health and child care, elderly homes / detention | need assistance |
| 4a / 4b | Offices / shops, restaurants, bars, banking halls | 4b unfamiliar, higher fire growth |
| 5a–5d | PPE (Cap. 172) / schools / transport / other assembly | |
| 6a / 6b / 6c | Industrial incl. commercial kitchens and labs / warehouses / dangerous goods | |
| 7 | Car parks incl. car ports | |
| 8 | Plant rooms, IT rooms, telecom rooms | |

## Performance Requirements (Section 2)
- **B1–B7** means of escape: B(P)R 41(1).
- **C1–C6** fire resisting construction: B(C)R s.35. C6 covers works in progress.
- **D1** means of access: B(P)R 41A–41D.
- **F1** fire safety management: provisions kept in working order, evacuation effectively implemented.

## Definitions most often misread
- **Travel distance** is measured along the centreline of the exit route to the centre of the fire rated door of a protected exit (or the first tread, or the discharge point to the ultimate place of safety).
- **Ultimate place of safety** is a street, or an open area connected to a street, at least 1.5 m wide or the total required width of the exit routes discharging into it, whichever is greater.
- **Basement**: every exit route runs upward. A sloping site can still have a basement open on some sides.
- **Element of construction** excludes raised floors up to 600 mm. Compartment walls start from the structural floor.
- **FRR** is written X/Y/Z: stability / integrity / insulation, in minutes.
- **Usable floor area** excludes stairs, public circulation, lift landings, lavatories, kitchens in flats and lift / A/C machinery spaces.
- **Special hazard** covers transformer rooms, central A/C plant rooms, lift machine rooms, main switch rooms, generator, boiler, DG store and fuel tank rooms.
- Chinese terms in `part_a.json` are working translations, not the official Chinese text.
