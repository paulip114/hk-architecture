# Energy efficiency: OTTV, RTTV, Building Energy Code

Data: `energy.json`. Tool: `../tools/energy_check.py` (reads `energy`).

## Who controls what
| Control | Law / guidance | Applies to | Checked by |
| --- | --- | --- | --- |
| OTTV of walls and roofs | B(EE)R Cap. 123M; OTTV Code 1995; PNAP APP-67 (Sept 2025) | commercial and hotel buildings; residents' recreational facilities (RRF) of residential developments | BD (AP submits) |
| RTTV, VLT, external reflectance | PNAP APP-156 (Sept 2025) + BD Guidelines | domestic buildings (not hotels, guesthouses, RCHEs) | BD; prerequisite for APP-151 GFA concessions |
| Building services (lighting, A/C, electrical, lift & escalator) | BEEO Cap. 610; BEC 2024 | 13 building types in Sch. 4 (new buildings); major retrofitting works | EMSD (REA / developer declarations) |
| Energy audit | BEEO; EAC 2024 | commercial buildings and commercial parts of composite buildings | EMSD, every ≤ 10 years |

## OTTV limits (APP-67 para 3, 12)
- **Tower ≤ 20 W/m², podium ≤ 40 W/m²** for plans (incl. major revisions, A&A) submitted on or after **31 Dec 2025**. Before that date the limits were 21 / 50.
- Podium notional height: 20 m (para 4).
- G/F open-front shops of ≤ 50 m² UFA with separate A/C may be disregarded. Bigger shops: notional calculation with clear-glass shopfronts (para 6).
- Sunshades of ≤ 1.5 m are not counted in GFA or SC if they genuinely reduce OTTV. A quantitative assessment is needed over 750 mm. They may not project over streets (para 10).
- Submission:
  - Nothing with the first GBP submission.
  - The Appendix A summary sheet before consent (B(A)R reg 10).
  - Before the OP: final OTTVs on the GBP and an OTTV Report with Forms OTTV1–4, record plans and test certificates (paras 7–8).

## OTTV method (OTTV Code 1995, verified)
Source: BD *Code of Practice for Overall Thermal Transfer Value in Buildings 1995*, uploaded to the project. Tables 1–9 are in `energy.json` under `ottv_code`.
```
OTTVw = [Σ Aw·U·α·TDEQw + Σ Afw·SC·ESM·SF] / (Aw + Afw)       para 5
OTTVr = [Σ Ar·U·α·TDEQr + Σ Afr·SC·SF] / (Ar + Afr)           para 6 (SF horizontal = 264, no ESM)
Tower / podium OTTV = (G + H) / (E + F)                        Form OTTV 4
```
- **No conduction term for glazing.** Solar gain through glass carries the whole window load.
- The limit applies to the **average over all walls and roofs of the tower or podium**, not to any single wall or roof (para 3.2).
- TDEQw (Table 5): set by orientation (16 points) and wall density (< 22, 23–199, 200–379, 380–569, ≥ 570 kg/m²). Heavy walls get a low TDEQ.
- TDEQr (Table 9): 18.60 / 16.88 / 13.37 / 9.75 / 7.90 across the same density bands.
- SF (Table 8):
  - N 104, NE 138, E 168, SE 197, S 191, SW 202, W 175, NW 138
  - NNE 121, ENE 153, ESE 183, SSE 194, SSW 197, WSW 189, WNW 157, NNW 121
  - horizontal 264
- ESM: overhang Table 6 by OPF = A/B; sidefin Table 7 by SPF = C/D. Use the next larger factor. Where a window has both, take the smaller ESM.
- U (para 7.1): 1 / (Ri + Σx/k + Ra + Ro), using Table 1 (k), Table 2 (Ri, Ro) and Table 3 (air gaps).
  - Ri depends on the absorptivity of the **internal** surface: walls 0.120 if α ≥ 0.5, else 0.299.
  - Ro: wall 0.044, roof 0.055.
- Excluded from the calculation (4.1):
  - refuge floor walls
  - car park walls and roofs
  - lightwells ≤ 21 m² on plan
  - walls on roofs
- Party walls are always included (4.2). Internal blinds and shading from neighbours are ignored (1.8).
- Podium (Code definition): the part within 15 m above ground, or the B(P)R 20(3) / s.42 height. APP-67 allows a notional 20 m.
- The original 1995 limits were tower 35 / podium 80. APP-67 has since cut them to 20 / 40.
- Self-test: `python3 tools/energy_check.py --selftest` re-creates the Code's Appendix A East tower facade (Form OTTV 3).
  - Result: **41.61 W/m²**, E 1,968.96 m², G 81,921.03 W, all exactly as printed.
  - W1 and W4 U-values from layers also match (1.51, 0.41).

## RTTV (APP-156 para 6)
- **Wall ≤ 12.5 W/m², roof ≤ 3.5 W/m²** from 31 Dec 2025. Earlier limits: 14 / 4.
- VLT ≥ 50% for prescribed windows (B(P)R 30, 31). External reflectance ≤ 20%.
- RRF in residential developments: OTTV 20 / 40.
- The RTTV itself is computed with the BD Guidelines spreadsheets (Appendices III–IV). The tool only compares the result.
- Submission:
  - First submission: a statement of compliance on the plans.
  - Before consent: summary sheets (Appendices A and B).
  - At the OP: an Energy Efficiency Report, including NVTC compliance.
- RTTV values are published on the BD website after the OP.

## Building Energy Code 2024 (in force 23 Aug 2025)
- Lighting power density (Table 5.4, W/m²):
  - office ≤ 15 m² 9.0, 15–200 m² 8.5, > 200 m² 7.2
  - retail 11.1, restaurant 12.0
  - corridor 6.0, public circulation 9.9, entrance lobby 10.0, lift lobby 7.5, staircase 5.6
  - car park 3.0, plant room 8.4, hotel guest room 9.9, toilet 9.0
  - laboratory 10.4, workshop 9.4
- Lighting control: one control point per ≤ 250 m². Automatic control zones ≤ 250 m².
- Minimum chiller COP (examples):
  - water-cooled screw < 500 kW: 5.1
  - water-cooled VSD centrifugal < 1,000 kW: 5.5
  - air-cooled screw < 500 kW: 3.2
  - unitary air-cooled ≤ 7.5 kW: 2.8
- Motors of 75–200 kW: IE4. Car park fans ≥ 3.7 kW: modulate to ≤ 35%.
- Lift car fan ≤ 0.53 W per l/s. Regenerative braking for lifts ≥ 2.0 m/s or ≥ 900 kg. Escalator standby speed 0.05–0.25 m/s.
- Major retrofitting works: ≥ 500 m² works area, a ≥ 400 A central circuit, ≥ 350 kW of A/C, or works to central BSI motor / mechanical drives.
- Source: EMSD's BEC 2024 briefing, not the Code text. Read the Code itself for space types, duct and pipe insulation, copper loss, power factor and the full COP tables.
