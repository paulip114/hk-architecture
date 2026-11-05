# Energy efficiency: OTTV, RTTV, Building Energy Code

Data: `energy.json`. Tool: `../tools/energy_check.py` (reads `energy`).

## Who controls what
| Control | Law / guidance | Applies to | Checked by |
| --- | --- | --- | --- |
| OTTV of walls and roofs | B(EE)R Cap. 123M; PNAP APP-67 (Sept 2025) | commercial and hotel buildings; residents' recreational facilities (RRF) of residential developments | BD (AP submits) |
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

## OTTV formula (OTTV Code 1995) – constants unverified
```
Wall OTTV = [Σ Aw·Uw·α·TDeq + Σ Af·Uf·ΔT + Σ Af·SC·ESM·SF] / Σ(Aw + Af)
Roof OTTV = [Σ Ar·Ur·α·TDeq + Σ As·Us·ΔT + Σ As·SC·ESM·SF] / Σ(Ar + As)
```
- Aw / Ar: opaque wall / roof area. Af / As: window / skylight area.
- α: absorptivity. TDeq: equivalent temperature difference, set by density in kg/m².
- ΔT: indoor–outdoor temperature difference. SC: shading coefficient. ESM: external shading multiplier. SF: solar factor by orientation.
- The structure follows the Code and matches the inputs on the APP-67 Appendix A sheet (U values, SC, absorptivity, density, WWR).
- **The TDeq, ΔT and SF numbers in `energy.json` are placeholders.** The OTTV Code PDF could not be reached. The tool reports OTTV results as CHECK until `ottv_constants.verified` is set true after copying the Code's tables.
- Calibration against BD's published sample sheet (NT2022007OTTV): the placeholders give 73.6 W/m² against the reported 61.9 W/m². Same order, not exact.
- Not yet confirmed whether the limit applies to the overall figure or to walls and roof separately. The tool compares the overall figure and flags walls alone if they exceed the limit.

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
