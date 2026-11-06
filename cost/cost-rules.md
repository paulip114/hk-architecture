# Cost planning (Hong Kong)

Draft working rules for feasibility and design-stage cost advice. Data: `hk_cost_rates.json`. Tool: `../tools/cost_estimate.py`.

**[V]** checked against a source on 2026-11-05. **[U]** general practice, unverified.

## Stages
| Stage | Method | Who | Accuracy (indicative) **[U]** |
| --- | --- | --- | --- |
| Feasibility | Order of cost: CFA × HK$/m² by building type | Architect / QS | ±20–25% |
| Scheme design | Elemental cost plan (substructure, frame, envelope, finishes, services, externals) | QS | ±10–15% |
| Detailed design | Cost checks per element against the plan | QS | ±5–10% |
| Tender | Pre-tender estimate from priced BQ | QS | ±5% |
| Construction | Valuation of variations, interim valuations, final account | QS, certified by Architect | – |

## Unit rates
- Source in use: Arcadis Quarterly Construction Cost Review Q2 2026, "Approximate Building Costs Hong Kong", p. 5, HK$/m² CFA at 2Q 2026 levels. **[V: two independent reads of the PDF on 2026-11-05 and 11-06 gave identical figures]**
- The page does not say whether preliminaries, contractor's margin or foundations are included. Arcadis handbooks normally include preliminaries and normal foundations in these rates **[U]**: add abnormal piling as a lump sum.
- Example ranges: average high-rise apartments 25,200–28,800; average office 25,100–28,300; basement car park 28,500–32,600. Full list in the JSON.
- The rates exclude site formation, external works, land, fees, finance and legal costs, and assume no basement, flat ground and normal soil. Add these separately. **[V]**
- Other published sources to cross-check: Rider Levett Bucknall, AECOM / Langdon & Seah, and the Arcadis Construction Cost Handbook. **[U]**

## CFA, GFA and the gap between them
- Unit rates are on CFA (construction floor area, outside face of external walls, everything built). GFA under B(P)R reg 23 excludes exempted plant, car parks and green features. **[V definition from source]**
- So a GFA-based budget understates cost. Feed CFA from the area schedule: `cost_estimate.py` can take the `floors[]` block of a `bpr_check.py` project and cost gross areas (before exemptions).

## Escalation
- Tender price indices (Arcadis TPI 2026Q2 = 1912; ArchSD BWTPI 2026Q1 = 1836; both Q1 1970 = 100). Use the ratio of forecast TPI to the base-quarter TPI, or a % per year, to the tender mid-point. **[V figures]**
- TPI has been flat to slightly down from 2025Q1 to 2026Q2. **[V]**

## Allowances (feasibility defaults in the JSON, all [U])
Design contingency 10%, construction contingency 5%, external works 3%, professional fees 10%, escalation 2% a year. Replace per project, and add ground risks (piling on reclaimed land or rock, slope works), demolition, heritage and utilities diversion as lump sums.

## Architect's role on cost
- Design to the budget: report the cost implication of design choices (façade ratio, floor-to-floor height, wall-to-floor ratio, basement depth, transfer plates). **[U]**
- Value engineering: alternatives with equal function at lower whole-life cost; record client decisions. **[U]**
- Under SFBC, the QS measures and values (cl. 13 variations, cl. 32 valuations), and the Architect certifies. **[V clause numbers]**
- Measurement standard for bills in HK: Hong Kong Standard Method of Measurement of Building Works (HKSMM4, revised). **[U edition]**

## Cash flow
Construction spend follows an S-curve. A quick check uses a cumulative spend fraction of t²(3 − 2t) for elapsed fraction t of the contract period. **[U, rule of thumb]**

## Open items
- Elemental cost plan template (by element, HK$/m² CFA) and benchmarking against completed projects.
- Refresh the rates each quarter (next: Arcadis Q3 2026).
