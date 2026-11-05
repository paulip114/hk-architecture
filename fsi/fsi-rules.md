# FSD minimum fire service installations (FSD CoP, Sept 2022)

Data: `fsi_schedule.json`. Tool: `../tools/fsi_check.py` (reads `fsi`).

> **Not verified.** The FSD PDF (hkfsd.gov.hk/eng/source/safety/File2022.pdf) could not be downloaded directly. The schedule was read through a summarising web reader, and parts of Part IV and all of Part V were not seen. Check every row against the PDF before a submission, and upload the PDF to the project to replace this.

## Framework
- Formal title: *Codes of Practice for Minimum Fire Service Installations and Equipment and Inspection, Testing and Maintenance of Installations and Equipment*. FS Code A4.2 says to read it with the FS Code.
- Structure:
  - Part I: general. 1.3: the Director may vary requirements or accept fire engineering. 1.5: street hydrant within 100 m. 1.8: primary and secondary supply.
  - Part II: definitions of installations.
  - Part III: building classes. **High rise** means the floor of the uppermost storey is more than 30 m above the point of staircase discharge.
  - Part IV: schedule of minimum FSI by premises type (4.1–4.45).
  - Part V and after: design requirements, and appendices on testing and tank measurement.
- FSI plans are submitted with the building plans. FSD comments go through BD. FSD inspects and issues the FSI certificate before the OP. Maintenance follows Cap. 95B (Part F).

## Part IV, main premises types (encoded)
| Para | Premises | Core installations |
| --- | --- | --- |
| 4.21 | Domestic ≤ 3 storeys | portable appliances only |
| 4.22 | Domestic > 3 storeys, low rise | FA, FH/HR, portable |
| 4.23 | Domestic high rise | + EG, EL, exit signs, fireman's lift |
| 4.14 / 4.15 | Commercial low / high rise | AAD, EL, ES, FA, FD, FH/HR, portable, VAC control; sprinklers > 230 m² total floor area; AVAS > 2,000 m² single occupancy on a floor; smoke extraction (see below). High rise adds FCC and stair pressurization |
| 4.16 | Composite | each part to its own paragraph; if the non-domestic part is sprinklered, extend sprinklers 2 floors up the domestic staircases (fast-response) |
| 4.3 / 4.4 | Basement ≤ / > 230 m² | > 230 m²: + sprinklers (fast response), AVAS, FRS stairway, smoke extraction, pressurization for ≥ 3 basement levels |
| 4.26 / 4.9 | Garage / car port | + fireman's emergency switch; garage sprinklers > 230 m²; EV charging ≤ 230 m² without sprinklers needs heat / multi-sensor detectors |
| 4.27 / 4.28 | Hotel low / high | full list incl. sprinklers, FCC, AVAS, smoke extraction incl. guestroom corridors; smoke detection over whole floor with sleeping |
| 4.29 / 4.30 | Industrial / godown | sprinklers > 230 m²; FCC; high rise + pressurization |
| 4.31 / 4.32 | Institutional | sprinklers > 230 m²; AVAS; high rise + FCC, pressurization |

## Recurring thresholds
- Sprinklers: total floor area > 230 m² (commercial, industrial, institutional, garages), and always in basements > 230 m² and hotels.
- Smoke extraction: compartment > 7,000 m³ with openable windows ≤ 6.25% of floor area and fire load > 1,135 MJ/m², or an atrium > 28,000 m³. A hot smoke test may be required above 12 m headroom.
- Stair pressurization: no natural venting / openable windows ≤ 6.25%, cubical extent > 28,000 m³, fire load > 1,135 MJ/m² (read the full paragraph).
- Hose reels: every part reached by ≤ 30 m of hose. Hydrant outlets in staircase approach lobbies.

## Not encoded
- Part IV paragraphs 4.1, 4.2, 4.5–4.8 and 4.10–4.13: special risks such as battery / EV rooms, boiler rooms, bulk fuel, chemical plants and cold stores.
- Paragraphs 4.17–4.20, 4.24, 4.25 and 4.33–4.45: PPE, schools, petrol stations and the rest.
- All Part V design rules.
- FH/HR tank size: 9,000 / 18,000 / 27,000 L by largest floor area (≤ 230 / ≤ 460 / > 460 m²). This is a **memory value**: the tool reports it as CHECK only.
