# Barrier-free access – Design Manual: Barrier Free Access 2008

Draft working rules. Data: `bfa2008.json`. Tool: `../tools/bfa_check.py`.

Source: Design Manual: Barrier Free Access 2008, **2025 Edition (June 2025)**, BD. First issued December 2008; previous revision May 2024. Read through a text extractor on 2026-11-05. The extractor reached Divisions 1–14 and part of 15 only. Divisions 15–20 and Chapter 5 still need checking against the full PDF.

## Legal status
- The Obligatory Design Requirements of Divisions 1–20 are given effect through the Building (Planning) Regulations (reg 72 and the Third Schedule; the Manual's numbering follows the Schedule "as far as practicable"). *The reg 72 reference was not visible in the extracted text: check in Cap. 123F.*
- Background: Disability Discrimination Ordinance (1995) s.84.
- Mandatory Section = Performance Objectives + Obligatory Design Requirements. An alternative design is accepted only if it meets the Performance Objectives.
- Best Practice Section (Design Considerations, Recommended Design Requirements) is not mandatory. The tool does not check it.

## Extent (Chapter 2, Table 1)
- Domestic over 4 storeys: all common areas. Domestic of 4 storeys or fewer: main entrance, G/F common area and means of access.
- Non-domestic: all parts except exempt areas (2.2.2: commercial kitchens, cold rooms, projector rooms, plant rooms, hazardous stores, storage-only mezzanines, guard towers, the water of swimming pools, paths serving only these).
- Composite: the non-domestic parts plus the domestic rule above.
- Exempt (2.2.1): single-family buildings ≤ 13 m high; temporary buildings and contractor's sheds (B(P)R Part VII).

## Extra provisions by use (Table 2, Division 14)
| Use | Tactile floor plan | Tactile guide path | Visual display board | Accessible counter | Visual fire alarm | Assistive listening |
| --- | --- | --- | --- | --- | --- | --- |
| Domestic | | | | | | |
| Office common areas | | | | | Y | |
| Department store, shopping complex | Y | Y | | Y | Y | |
| Hotel, guesthouse, hostel, bank | Y | | | Y | Y | |
| Place of worship | Y | | | Y | Y | |
| Cinema, theatre, concert hall, stadium, museum, theme park | Y | Y | Y | Y | Y | Y |
| School, college, university, library | Y | Y | | Y | Y | |
| Factory, workshop, industrial | | | | | Y | |
| Sports complex, public pool | Y | Y | | Y | Y | |
| Restaurant, food court | Y | | | | Y | |
| Indoor market, supermarket | Y | | | | Y | |
| Hospital, clinic | Y | Y | Y | Y | Y | Y |
| Elderly home, welfare centre | Y | Y | | Y | Y | |
| Club house | Y | | | Y | Y | |
| Transport station, interchange, terminal | Y | Y | Y | Y | Y | Y |
| Car park | Y | | | | Y | |

## Key obligatory figures (mm unless stated)
| Division | Requirement |
| --- | --- |
| 1 Auditoria | Wheelchair spaces: 4 up to 800 fixed seats; above 800, 2 per 400 seats or part. In pairs, with sightlines. Space 800 × 1300 (800 facing stage). Passage 1500 wide. Tactile exit maps at entrances. |
| 2 Hotels | 2 accessible guest rooms per 100 rooms or part. Bathrooms to Div 12. |
| 3 Car parks | Accessible bays: 1–50 → 1; 51–150 → 2; 151–250 → 3; 251–350 → 4; 351–450 → 5; over 450 → 6. Bay ≥ 3500 wide, or ≥ 2500 beside a shared area ≥ 1200 wide. Near an accessible lift or entrance. |
| 4 Access route | From the lot boundary to at least one main entrance and an accessible lift. Clear width ≥ 1050, firm, no steps or kerbs. |
| 5 Ramps | Max 1:12. Minor rises: 1:10 up to 1500 long / 150 rise; 1:8 up to 600 long / 75 rise; may not be combined. Width ≥ 1050. Landings 1500 × 1500 at head and foot (no door swing over them). At 1:20 or steeper: 1200 landing every 10 m of run, handrails both sides, tactile strips (except ramps to lifts and ramps under 300 long). Kerb ≥ 100 or rail at 200 on open edges. |
| 6 Dropped kerbs | ≥ 1200 × 1200, ≤ 1:10, ≤ 15 level difference, tactile warning strips. |
| 7 Staircases | Tread ≥ 225, riser ≤ 175 (external: ≥ 280 / ≤ 160). No projecting nosing. ≤ 16 steps per flight. Handrails both sides. Contrasting nosing. Tactile warning strips top, bottom and landings (300 wide inside, 600 at open space or exit). |
| 8 Handrails | 850–950 high; 32–50 diameter; 30–50 clear of wall; extend ≥ 300 beyond the end nosing; 1.3 kN; Braille floor information on each floor. |
| 9 Corridors | Clear width ≥ 1050. 1500 × 1500 turning space within 3500 of every dead end. Lobby length ≥ 1200 clear of door swings. Level area 1200 × 1500 both sides of entrances. Gratings: slots ≤ 13. Projections ≤ 90 below 2000. Headroom ≤ 2000 needs a guardrail. |
| 10 Doors | Clear width ≥ 800. 330 clear beside the leading edge. Handle 950–1050. Threshold ≤ 20 bevelled. Opening force: exterior 30 N, interior 22 N, fire doors on accessible routes 30 N. Vision panel in double-action doors from ≤ 1000 to ≥ 1500. Automatic door at one main entrance of listed building types. |
| 11 Toilets | Per sex, per floor: 1 accessible cubicle where there are ≤ 20 cubicles, 2 where > 20. Not needed in domestic parts. ≥ 1 unisex accessible toilet on each floor with toilets. Cubicle ≥ 1500 × 1750 with 1500 × 1500 turning. WC seat 380–450. Basin rim ≤ 750 with 550 knee space. Flush 600–1050. Grab rails 32–40 dia, folding rail 725–750. Emergency call bell (Div 17). |
| 12 Bathrooms | Bath ≤ 380 high; shower ≥ 1500 × 900; seat 430–480 high; roll-in threshold ≤ 13. |
| 13 Signs | Letter height ≥ 60 (doors), 110 (corridors), 200 (external). Braille toilet signs 900–1500; Braille exit map 800–1200 above the lift call button. |

## Not yet verified (upload the full PDF)
- **Div 15 counters, 16 illumination, 17 call bells, 18 assistive listening, 19 lifts, 20 escalators, Chapter 5.** The tool uses values from memory for lifts (car ≥ 1100 × 1400, door ≥ 800, buttons 900–1200) and counters (≤ 900 high). A shortfall shows as CHECK, not FAIL.
