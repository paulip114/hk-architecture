# Energy efficiency check – 示範：堅尼地城商住大廈（虛構）

**Result: does not comply** (3 fail, 2 to check, 18 items).

> Draft for review by an Authorized Person and the BS engineer (REA under BEEO). Limits from PNAP APP-67 / APP-156 (Sept 2025) and BEC 2024. OTTV constants are placeholders until loaded from the OTTV Code 1995.

| Clause | Item | Proposed | Limit | Result | Note |
| --- | --- | --- | --- | --- | --- |
| APP-67 para 3, 12 | OTTV limit set | current (from 31-12-2025) | tower 20 / podium 40 W/m² | INFO |  |
| OTTV Code 1995 | OTTV constants (TDeq, ΔT, SF) | placeholders | Code tables | CHECK | results below are indicative only; load the Code's tables into energy.json |
| APP-67 App. A | Retail podium G/F–2/F window-to-wall ratio | 0.41 | - | INFO |  |
| B(EE)R / APP-67 | Retail podium G/F–2/F wall OTTV | 39.2 W/m² | (compare ≤ 40 W/m²) | INFO |  |
| B(EE)R / APP-67 | Retail podium G/F–2/F roof OTTV | 3.4 W/m² | (reported) | INFO |  |
| APP-67 para 3 | Retail podium G/F–2/F overall OTTV (podium) | 27.6 W/m² | ≤ 40 W/m² | CHECK | indicative: placeholder constants |
| APP-156 para 6 | RTTV wall | 13.1 W/m² | ≤ 12.5 W/m² | FAIL | RTTV itself computed with BD Guidelines spreadsheet |
| APP-156 para 6 | RTTV roof | 3.2 W/m² | ≤ 3.5 W/m² | PASS | RTTV itself computed with BD Guidelines spreadsheet |
| APP-156 para 6 | Living room window VLT (prescribed window) | 52% | ≥ 50% | PASS |  |
| APP-156 para 6 | Living room window external reflectance | 15% | ≤ 20% | PASS |  |
| APP-156 para 6 | Bedroom window VLT (prescribed window) | 48% | ≥ 50% | FAIL |  |
| APP-156 para 6 | Bedroom window external reflectance | 15% | ≤ 20% | PASS |  |
| BEC 2024 Table 5.4 | G/F shop LPD | 10.4 W/m² | ≤ 11.1 W/m² | PASS |  |
| BEC 2024 Table 5.4 | Lift lobby (typical) LPD | 6.7 W/m² | ≤ 7.5 W/m² | PASS |  |
| BEC 2024 Table 5.4 | B1 car park LPD | 2.8 W/m² | ≤ 3.0 W/m² | PASS |  |
| BEC 2024 Table 5.4 | Staircase A LPD | 5.1 W/m² | ≤ 5.6 W/m² | PASS |  |
| BEC 2024 Ch. 6 | CH-1 water-cooled VSD centrifugal 900 kW COP | 5.8 | ≥ 5.5 | PASS |  |
| BEC 2024 Ch. 8 | L1-L4 lift car fan | 0.6 W/(l/s) | ≤ 0.53 | FAIL |  |
