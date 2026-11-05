# Building (Planning) Regulations (Cap. 123F) – working rules for compliance checks

Read this before any B(P)R compliance task. Sections 1-7 were checked against the **official consolidated Cap. 123F (17-09-2026, Verified Copy)** held at `/mnt/project-files/Cap 123F Consolidated version for the Whole Chapter (17-09-2026) (English and Traditional Chinese).pdf`. Quote that file, not this summary, in any submission. Items marked **[verify]** are PNAP or practice points not in the Regulations. Every report produced from this file is a draft for review and signature by an Authorized Person.

Last compiled: 2026-11-05.

## 1. Site classification – reg 18A
| Class | Condition |
| --- | --- |
| A | Not class B or C; abuts one (or more) specified street ≥ 4.5 m wide |
| B | Corner site abutting 2 specified streets, neither < 4.5 m, and ≥ 40% of the site boundary abuts them |
| C | Corner site abutting 3 specified streets, none < 4.5 m, and ≥ 60% of the site boundary abuts them |

- "Specified street" (reg 18A(3)): Government street maintained by HyD; private street under the same lease that must be surrendered; street the lessee must build on unleased Government land; street over which the owner has a right of way at all times; or street on land held by the site owner under a Government lease (or a combination of these along its length). See PNAP APP-44 and APP-124 [verify].
- Reg 19(3): a site that is not class A, B or C → height, site coverage and plot ratio **determined by the Building Authority**.
- Reg 19A (depth ≤ 3 × frontage) was **repealed** by L.N. 406 of 1987.

## 2. Site coverage – reg 20
- Limits from First Schedule (`first_schedule.json`), by building **height**, site class and domestic/non-domestic.
- Reg 20(3): non-domestic buildings / parts may exceed the permitted % site coverage, whatever the building height, **up to 15 m above ground level**. Reg 20(4): above that level the normal limit applies and the whole-building plot ratio must still comply.
- Site coverage = area covered by the building at the level considered, measured to the outer face of external walls (curtain walls per APP-2 paras 6-10), divided by site area.

## 3. Plot ratio – reg 21
- PR = GFA ÷ site area (reg 21(3)).
- Composite buildings (reg 21(2)): domestic PR ≤ (1 − actual non-domestic PR ÷ permitted non-domestic PR) × permitted domestic PR. Equivalent test used by the tool: Dd/Pd + Dn/Pn ≤ 1.
- **Lease conditions and the Outline Zoning Plan usually set lower limits than B(P)R** – the tool takes optional `ozp_max_pr`, `lease_max_gfa` and applies the strictest.
- HKPSG reference densities (domestic PR): Main Urban R1 – HK Island 8/9/10 (Class A/B/C), Kowloon 7.5; R2 6; R3 3.6. New Towns R1 6.5, R2 5, R3 3.6, R4 0.8. Source: [HKPSG Ch.2](https://www.pland.gov.hk/file/tech_doc/hkpsg/full/pdf/ch2_en.pdf).

## 4. Bonus for dedication or surrender – reg 22
- 22(1) Dedication: building set back from a street boundary between ground level and ≥ 5.5 m (or 3.3 m if the BA is satisfied there is no obstruction to traffic), and with Government consent the setback area is dedicated to the public for passage.
- 22(2) Surrender: part of the lot abutting a street acquired by Government (agreement or resumption under Cap. 124) for street widening.
- Bonus site coverage (both cases): permitted % + **1500 × dedicated area ÷ (site area × building height)**.
- Bonus plot ratio (both cases): the **lesser** of (permitted PR × 1.20) and (permitted PR + **5 × dedicated area ÷ site area**). For composite buildings it applies to the domestic part.
- 22(3): other parts of the building stay at the permitted % site coverage; reg 25 open space is not reduced.

## 5. Height, site area and GFA – reg 23
- Height (reg 23(1)): from the mean level of the specified street(s) ≥ 4.5 m on which the building fronts (the **lower/lowest** if levels differ) **to the mean height of the roof over the highest usable floor space**.
- Site area (reg 23(2)): **exclude** any part of a street or service lane; **include** any area dedicated to the public for passage.
- GFA (reg 23(3)(a)): area within the external walls at each floor level (including basements), **plus balconies** (overall dimensions including side thickness), **plus the thickness of external walls**.
- Reg 23(3)(b): the BA may disregard floor space used solely for parking / loading-unloading of motor vehicles; refuse storage and material recovery chambers/rooms, refuse chutes and hopper rooms; telecom and broadcasting access facilities; or machinery for lifts, air-conditioning, heating or similar services.
- Reg 23(4): a composite building whose only domestic part is a caretaker's residence ≤ 50 m² usable floor space (and/or a top-storey residence) may be treated as non-domestic.
- Reg 23A: hotels may be treated as non-domestic; back-of-house (laundry, workshops, stores, staff facilities, pick-up/drop-off) may be disregarded. Change of use without BA approval is an offence (level 6 fine, 2 years).

### Disregarded / exempted GFA – PNAP [APP-2](https://www.bd.gov.hk/doc/en/resources/codes-and-references/practice-notes-and-circular-letters/pnap/APP/APP002.pdf) (rev. Nov 2025)
| Item | Treatment |
| --- | --- |
| Mandatory/essential plant rooms (lift machine, transformer, switch, pump, FS control, water tank, meter, telecom, CO2, sewage, smoke extraction) | Disregarded under reg 23(3)(b); enclosing walls ≤ 100 mm normally |
| Non-mandatory plant rooms (A/C, heating) | Disregarded but subject to APP-151 prerequisites and the 10% cap |
| Underground car park (private & public) | 100% disregarded; spaces must be EV charging-enabling (plans from 1 Nov 2025) |
| Above-ground car park, max two floors | 100% |
| Above-ground car park, other floors | 50% (100% if site constraints / no adverse impact) |
| Loading/unloading | 100% underground or at G/F; 50% above G/F |
| Public transport terminus | Accountable unless OZP / planning approval says otherwise |
| Covered bicycle parking required by lease | May be exempted under 23(3)(a) |
| Refuge floor complying with FS Code | May be disregarded |
| Staircases, lift shafts, ducts | Counted with floors they pass through; excluded only if solely serving non-accountable floors |
| Curtain wall | Measure to structural face if projection ≤ 200 mm (dom) / 250 mm (non-dom), 300 mm dwarf wall, reflectance ≤ 20% |
| Duplex flat void | UFS ≥ 150 m², void ≤ 10% UFS and ≤ 0.5% total domestic GFA, headroom ≤ 6.5 m |
| House void | UFS ≥ 250 m², void ≤ 5% UFS, headroom ≤ 7.0 m |

### APP-151 overall cap
- Green and amenity features and non-mandatory plant rooms granted GFA concessions are capped at **10% of total GFA** of the development, with prerequisites (APP-152 Sustainable Building Design guidelines, BEAM Plus registration, energy-efficiency). Mandatory plant rooms and underground car parks are outside the cap. [verify exact list against current APP-151]

## 6. Storey height – reg 24
- Rooms for habitation or office: floor-to-ceiling ≥ **2.5 m**, ≥ 2.3 m to underside of beams; sloping ceilings measured at mean height, no part < 2 m.

## 6A. Open space for domestic buildings – reg 25, Second Schedule
- Open space within the site, at the rear (or partly rear, partly side), at a level **not less than 150 mm below the floor of the lowermost storey** (reg 25(1)(a)). The BA may require more for equitable development of an adjacent site.
- Minimum area: Class A ½, Class B ⅓, Class C ¼ of the **roofed-over area** of the domestic building.
- Reg 25(1)(b): no part of the building bounding the open space may be within 1.5 m horizontally of the opposite boundary of that open space.
- Reg 25(2): no part of a domestic building within **1.5 m** of the rear boundary (that strip counts toward the open space).
- Reg 25(3)-(4): alterations may not reduce existing open space below the requirement. Reg 25(5): parapets/railings where open space is > 600 mm above an adjoining one.

## 7. Lighting and ventilation – regs 30-33 (see PNAP APP-130)
- Habitable rooms, offices and kitchens need a **prescribed window**:
  - glass area ≥ **1/10** of room floor area;
  - openable area ≥ **1/16** of room floor area;
  - top of opening ≥ 2 m above floor (1.9 m for detached/semi-detached houses);
  - glass faces directly into external air.
- Reg 31 external air: the prescribed window must either face a street ≥ 4.5 m wide, or face an uncovered, unobstructed **rectangular horizontal plane** at sill level (sill deemed 1 m above floor) of ≥ 21 m², base ≥ 2.3 m, and sides ≥ 4.5 m to any opposite wall within the site (or ≥ 2.3 m where the opposite side is the site boundary), and:
  - (c) within the site: no building protrudes above a plane inclined from the far edge at **71½° (habitable)** or **76° (office/kitchen)**;
  - (d) facing a site boundary: from where the horizontal plane meets the boundary, no building on the site protrudes above a plane inclined back toward the site at **80½° (habitable)** or **83° (office/kitchen)**.
  - Where a service lane or street < 4.5 m runs along that boundary, the boundary is deemed 1.5 m beyond; where the lane is < 3 m, measure to its centre line.
- Reg 32: no part of a habitable room more than **9 m** from a prescribed window (or outer edge of a verandah/balcony).
- Reg 33: window onto an enclosed verandah counts as prescribed; combine room + verandah areas for the ratios.
- Reg 34: an office that cannot meet reg 31 may use mechanical ventilation of ≥ 5 air changes per hour plus BA-approved artificial lighting.
- Reg 35: the BA may require an extra vent (≥ 0.015 m² airshaft, fanlight, etc.). Laundries count as habitation.
- Reg 35A: provision for a room-sealed gas water heater in every bathroom (unless central hot water).
- Reg 36: rooms with a soil or waste fitment need a window or lantern light with glass ≥ **1/10** of floor area and openable to the open air ≥ **1/10**, top of opening ≥ 2 m; must not open directly into a food room or into an auditorium / waiting space of a place of public entertainment.
- Reg 37: a new building may not reduce another building's light and air below what these Regulations require.
- Many developments now use Performance-based L&V under APP-130 (daylight factor / vertical daylight factor) instead of reg 30-31 prescriptive tests – the tool checks only the prescriptive ratios.

## 8. Other parts of B(P)R the checker does not yet automate
Staircases (39-40), means of escape (41 → Code of Practice for Fire Safety in Buildings 2011), firemen's access (41A-41D, EVA), storey height (24), service lanes (28), projections/canopies/balconies over streets (7-13), barrier-free access (72 → Design Manual: Barrier Free Access 2008).

## Sources read
- **Official consolidated Cap. 123F (17-09-2026), uploaded by the user** – primary source for sections 1-7.
- HKU Historical Laws, B(P)R (1956, am. to 1985): https://oelawhk.lib.hku.hk/items/show/2542
- Histsyn, B(P)R 1964 ed. First Schedule (L.N. 294/76): https://hkintexts.histsyn.com/series/histsyn-historical-laws-engine/items/1964_BUILDING_(PLANNING)_REGULATIONS?p=29
- PNAP APP-2 (rev. Nov 2025): https://www.bd.gov.hk/doc/en/resources/codes-and-references/practice-notes-and-circular-letters/pnap/APP/APP002.pdf
- HKIS short course on B(P)R (2015): https://www.hkis.org.hk/hkis/general/events/cpd-2015136a.pdf
- HKPSG Ch.2 Residential Densities: https://www.pland.gov.hk/file/tech_doc/hkpsg/full/pdf/ch2_en.pdf
