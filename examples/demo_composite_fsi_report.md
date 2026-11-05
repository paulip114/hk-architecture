# Minimum FSI check – 示範：堅尼地城商住大廈（虛構）

**Result: does not comply** (1 fail, 2 to check, 40 items).

> Draft for review by an Authorized Person and the FSI engineer / registered FSI contractor. Schedule from the FSD Codes of Practice for Minimum FSI (Sept 2022) Part IV, read through a web summary and **not yet verified against the PDF**. FSD may vary requirements (para 1.3). Design details (Part V) are not checked.

| Clause | Item | Proposed | Requirement | Result | Note |
| --- | --- | --- | --- | --- | --- |
| Part III | Uppermost floor above staircase discharge | 97.35 m | > 30 m = high rise | INFO | high rise |
| para 4.26 | B1 car park: premises type | Garage (enclosed car park) | - | INFO |  |
| para 4.26 | B1 car park: Automatic actuating devices | provided | required | PASS |  |
| para 4.26 | B1 car park: Emergency lighting | provided | required | PASS |  |
| para 4.26 | B1 car park: Exit sign | provided | required | PASS |  |
| para 4.26 | B1 car park: Fire alarm system | provided | required | PASS |  |
| para 4.26 | B1 car park: Fire detection system | provided | required if ≤ 230 m² with EV charging and no sprinklers (heat or multi-sensor detectors) | PASS |  |
| para 4.26 | B1 car park: Fire hydrant / hose reel system | provided | required | PASS |  |
| para 4.26 | B1 car park: Fireman's emergency switch | not provided | required | FAIL |  |
| para 4.26 | B1 car park: Fireman's lift | provided | required if B(P)R 41B / FS Code Part D calls for it (see fire_cd_check.py) | PASS |  |
| para 4.26 | B1 car park: Portable hand-operated approved appliances | provided | required | PASS |  |
| para 4.26 | B1 car park: Sprinkler system | provided | required (total floor area exceeds 230 m²) | PASS |  |
| para 4.26 | B1 car park: Ventilation / air conditioning control system | provided | required | PASS |  |
| para 4.15 | G/F–2/F retail podium: premises type | Commercial (non-domestic), high rise | - | INFO |  |
| para 4.15 | G/F–2/F retail podium: Automatic actuating devices | provided | required | PASS |  |
| para 4.15 | G/F–2/F retail podium: Automatic fixed installation other than water (special risk areas) | provided | required if special risk areas exist (e.g. transformer, switch rooms) | PASS |  |
| para 4.15 | G/F–2/F retail podium: Emergency generator | provided | required | PASS |  |
| para 4.15 | G/F–2/F retail podium: Emergency lighting | provided | required | PASS |  |
| para 4.15 | G/F–2/F retail podium: Exit sign | provided | required | PASS |  |
| para 4.15 | G/F–2/F retail podium: Fire alarm system | provided | required | PASS |  |
| para 4.15 | G/F–2/F retail podium: Fire control centre | provided | required | PASS |  |
| para 4.15 | G/F–2/F retail podium: Fire detection system | provided | required | PASS |  |
| para 4.15 | G/F–2/F retail podium: Fire hydrant / hose reel system | provided | required | PASS |  |
| para 4.15 | G/F–2/F retail podium: Fireman's lift | provided | required | PASS |  |
| para 4.15 | G/F–2/F retail podium: Portable hand-operated approved appliances | provided | required | PASS |  |
| para 4.15 | G/F–2/F retail podium: Pressurization of staircase | provided | required if no natural venting of staircase / openable window ≤ 6.25% of floor area, cubical extent > 28 000 m³ and fire load > 1 135 MJ/m² (check the full para; refers to Part II) | PASS |  |
| para 4.15 | G/F–2/F retail podium: Sprinkler system | provided | required (total floor area exceeds 230 m²) | PASS |  |
| para 4.15 | G/F–2/F retail podium: Ventilation / air conditioning control system | provided | required | PASS |  |
| para 4.23 | 3/F–30/F flats: premises type | Domestic, high rise | - | INFO |  |
| para 4.23 | 3/F–30/F flats: Emergency generator | provided | required | PASS |  |
| para 4.23 | 3/F–30/F flats: Emergency lighting | provided | required | PASS |  |
| para 4.23 | 3/F–30/F flats: Exit sign | provided | required | PASS |  |
| para 4.23 | 3/F–30/F flats: Fire alarm system | provided | required | PASS |  |
| para 4.23 | 3/F–30/F flats: Fire hydrant / hose reel system | provided | required | PASS |  |
| para 4.23 | 3/F–30/F flats: Fireman's lift | provided | required | PASS |  |
| para 4.23 | 3/F–30/F flats: Portable hand-operated approved appliances | provided | required | PASS |  |
| para 4.16 | Composite: sprinklers in domestic staircases | 3/F–30/F flats | extend 2 floors above the sprinklered non-domestic part, fast-response heads | CHECK | show on FSI plans |
| para 1.5 | Street fire hydrant distance | 60 m | ≤ 100 m | PASS |  |
| Part IV | Hose reel coverage (longest hose run) | 30 m | ≤ 30 m | PASS |  |
| Part V (unverified) | FH/HR fire service water tank | 18000 L | ≥ 27000 L for largest floor 950 m² (unverified) | CHECK | SHORT of the unverified table: confirm against Part V of the 2022 Code |
