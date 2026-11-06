# PNAP APP-152 – Sustainable Building Design Guidelines

Draft working rules. Data: `app152.json`. Tool: `../tools/sbd_check.py`.

Source: BD PNAP APP-152, version September 2023 (first issued January 2011, last revised January 2016). Checked against the PDF on 2026-11-06.

## Why it matters
- Compliance with APP-152 is a prerequisite for the APP-151 GFA concessions for green and amenity features (and most non-mandatory plant rooms). If a scheme fails APP-152, the 10% APP-151 concession cap is lost as well, not just one item.
- On a s.42 modification the BA may impose conditions: greenery kept for its approved use, designated as common parts in the DMC, and an undertaking registered at the Land Registry before OP.
- Height is measured from Level Zero (mean level of the lowest street) to the mean roof height over the highest usable floor.

## 1. Building separation (paras 3–6, Appendix B)
- **Applies to:** sites of 20,000 m² or more, or any site where a building or group has a continuous projected façade length (Lp) of 60 m or more.
- **Assessment zones:** low 0–20 m, middle 20–60 m, high above 60 m. Each zone is assessed separately on two projection planes at right angles (they may be 75°–105° apart).
- **Lp limit:** Lp should not exceed 5 × U, where U is the mean width of the street canyon (use the least U where the building abuts several streets). This is required together with Table 1 permeability, not as an alternative. Low-zone parts at or below 6.67 m may be disregarded. The limit does not apply where the site does not abut a street, or where no part of the building in the zone is within 30 m of the street centreline (Appendix B para 2.5).
- **Minimum permeability P (Table 1):**

| Tallest building H | Site < 20,000 m² with Lp ≥ 60 m (each plane) | Site ≥ 20,000 m², plane 1 | Site ≥ 20,000 m², plane 2 |
| --- | --- | --- | --- |
| H ≤ 60 m | 20% | 20% | 25% |
| H > 60 m | 20% | 20% | 33.3% |

  The PNAP does not define which plane is Plane 1. `sbd_check.py` treats the first plane in the input as Plane 1.
- P = (area of intervening space IS + permeable elements PE) ÷ area of the assessment zone.
- At least 2/3 of P must be intervening space and at most 1/3 permeable elements.
- IS along a site boundary or street centreline: separating distance ≥ 7.5 m, with no part of the building within 3 m of the boundary. Additional IS between façades: ≥ 15 m.
- IS must be open to the sky or at least 2/3 of the zone height. PE needs a clear width and clear height of at least 3 m.
- Air corridors: at least 15 m wide (direction may change by up to 15°). Wind paths through subdivided sites: at least 15 m wide, with streets of mean width ≥ 7.5 m at each end.
- **Exempt:** standalone residential blocks not over 15 m high.

## 2. Building setback (paras 7–9, Appendix C)
- **Applies to:** buildings fronting a street less than 15 m wide.
- **Option (a), corridor:** keep a ventilation corridor of at least 15 m × 15 m section. No part of the building up to 15 m above street level may be within 7.5 m of the street centreline. Follow the street profile where levels vary.
- **Option (b), podium garden:** where a cross-ventilated communal podium garden has a clear height of at least 4.5 m, the building up to 15 m must stay within a 45° plane rising from street level at the boundary on the opposite side of the street.
- **Allowed in the setback:** building over it above 15 m; canopies complying with B(P)R reg 10; projections up to 600 mm and signboards at ≥ 2.5 m clear height; single-storey footbridges; columns (Fig. C2). The setback is otherwise landscaped, paved and kept open.
- **Waiver:** may be waived for a street where building height is less than 2 × the street's mean width.
- The setback area is excluded from GFA (footnote 2).

## 3. Site coverage of greenery (paras 10–12, Appendix D)
- **Applies to:** sites of 1,000 m² or more, except a single family house.
- **Minimum greenery, as a percentage of site area (Table 2):**

| Site area | Primary zone (0–15 m above street) | Overall |
| --- | --- | --- |
| 1,000 – 20,000 m² | 10% | 20% |
| ≥ 20,000 m² | 15% | 30% |

- Measure soil area on plan. Uncovered greenery counts in full. A green buffer meeting APP-151 Appendix C1 counts ×2.
- Counted at 50%: covered greenery reachable from open space in the primary zone; water features in the primary zone or on uncovered communal roofs; grass paving (not on parking or loading areas); planters on inaccessible roofs in the primary zone.
- Counted in full: vertical greening, measured as the elevational area of the panel, modular planter or frame (frame above 7.5 m not counted); greening on slopes steeper than 45°.
- Not counted: covered greenery above the primary zone, except the scenarios in Appendix D para 1; removable planters.
- The greening features above (the 50% items, vertical greening and slope greening) may make up no more than 30% of the required overall greenery.
- Recommended soil depths: trees 1.2 m, shrubs 0.6 m, grass 0.3 m. Roofs need waterproofing, irrigation and drainage, and dead load allowed for soil and trees.

## 4. Alternative approaches (Appendix E)
- Low-zone waiver: site coverage ≤ 65% with street setbacks along ≥ 50% of the boundary (≥ 10 m) and ≥ 15% of site area.
- Where the setback exceeds 15% of site area, compensatory relaxation of greenery applies. For sites ≤ 1,000 m², primary-zone greenery must cover at least 50% of the setback area.
- Performance-based: provide at least Table 1 P and an air ventilation assessment showing performance equal to or better than a compliant baseline.

## Not automated
- Drawing the projection planes and measuring IS / PE areas. The tool takes P per zone as input.
- The 45° plane in setback option (b) is a yes/no input.
- Appendix E alternatives and AVA.
