# FSD minimum fire service installations (FSD CoP, Sept 2022)

Data: `fsi_schedule.json`. Tool: `../tools/fsi_check.py` (reads `fsi`; `--list` shows the premises types).

Source: 《最低限度之消防裝置及設備守則與裝置及設備之檢查、測試及保養守則》, September 2022 edition. The Chinese text was uploaded to the project.
- All of Part IV (paras 4.1–4.45) was parsed from that text.
- The installation lists and each installation's applicability wording (`applicability_zh`) are verbatim.
- English names are working translations.

## Framework
- FS Code A4.2 says to read this Code with the FS Code.
- Part I: 1.3, the Director may vary requirements. 1.5, a street hydrant within 100 m.
- Part II: definitions. Part III: building classes.
- **High rise** (Part III): 「最高樓層的樓面在地面層水平的樓梯出口處之上超過30米的建築物」. Low rise is ≤ 30 m.
- Part IV: minimum FSI by premises type. Part V: design specifications.
- FSI plans go with the building plans. FSD issues the FSI certificate before the OP. Maintenance under Cap. 95B (FS Code Part F).

## How the tool reads Part IV
Each installation in a paragraph is one of three kinds:
- **required** (`cond: yes`)
- a **machine-checked condition**: see the `conditions` table in the JSON and the list below
- **conditional** (`check`): the tool prints the Code's own wording so the AP can decide

## Main premises types
| Para | Premises | Notes from the text |
| --- | --- | --- |
| 4.21 | 住用 ≤ 3 層 | portable appliances only: one per floor, more for car ports |
| 4.22 | 住用 > 3 層，低層 | FA, FH/HR, portable |
| 4.23 | 高層住用 | + EG (enough for FSI and fireman's lift), EL in all stairs, passages, plant rooms and public areas incl. lift lobbies and refuge spaces, exit signs, fireman's lift per FS Code |
| 4.14 / 4.15 | 商業 低層 / 高層 | EG is **required in both**. Sprinklers when total floor area > 230 m², covering stairs, common corridors and toilets. AVAS > 2,000 m² single occupancy on a floor. High rise adds FCC and pressurization (all four conditions below) |
| 4.16 | 綜合用途 | each use to its own paragraph. If the non-domestic part is sprinklered, the staircases leading to the domestic part on the floors immediately above and below it are sprinklered too, with fast-response heads |
| 4.3 / 4.4 | 地庫 ≤ / > 230 m² | > 230 m²: fast-response sprinklers throughout; FRS stairway for ≥ 3 levels; smoke extraction where > 7,000 m³ and > 1,135 MJ/m², an industrial basement, or ≥ 3 levels (excluding parking-only areas); pressurization for ≥ 3 levels with no open-air access for firemen, > 7,000 m³ and > 1,135 MJ/m² |
| 4.26 | 車房 (garage) | sprinklers > 230 m² incl. stairs to it. **Fireman's emergency switch only where EV charging is provided.** Heat or multi-sensor detectors where EV charging is not sprinklered. An extra dry-powder or CO₂ extinguisher at each hose reel on EV floors |
| 4.9 | 停車間 (car port) | FA and FH/HR depend on risk; same EV rules as garages; sprinklers where total floor area > 230 m² (Circular Letter 1/2023) |
| 4.27 / 4.28 | 旅館 | sprinklers in all parts incl. bathrooms; smoke or multi-sensor detection over whole floors with sleeping (sounder bases in guestrooms); smoke extraction for internal escape routes serving guestrooms unless openable windows > 6.25%; pressurization where stairs are not naturally ventilated and openable windows ≤ 6.25% |
| 4.29 / 4.30 | 工業／貨倉 | low rise: sprinklers > 230 m². High rise: sprinklers throughout, FRS stairway, pressurization (four conditions) |
| 4.31 / 4.32 | 社團 (GIC, clubs, schools, hostels, hospitals, prisons, nursing homes) | low rise: sprinklers > 230 m²; EG for hospitals, nursing homes and prisons or as the risk requires. High rise: sprinklers throughout; pressurization only for hospitals and nursing homes |
| 4.33–4.45 | kitchens, lift machine rooms, plant rooms, transport terminals, refuge floors (drenchers to all external openings, with their own water supply), tunnels, substations, telecom / computer rooms | stored, with the text where the paragraph has no numbered list |

## Recurring thresholds (verbatim conditions)
- Smoke extraction (commercial, industrial): an atrium compartment > 28,000 m³ (or a basement / storey of it > 7,000 m³), or any compartment > 7,000 m³ with openable windows ≤ 6.25% of its floor area **and** a fire load likely > 1,135 MJ/m². Above 12 m headroom, or for irregular or very large compartments, FSD may require a hot smoke test.
- Stair pressurization (commercial high rise, industrial high rise), all four together:
  - stairs not naturally ventilated
  - openable windows ≤ 6.25% per floor
  - building > 28,000 m³
  - fire load > 1,135 MJ/m²
- The number of pressurized stairs follows the Part II table, and is never more than the FS Code requires.
- Hose reels: every part within 30 m of hose. Hydrants in the approach lobby or enclosure of a required staircase. One actuating point and one sounder at each hose reel, starting the pumps and the alarm.
- Linings in ducts, concealed spaces and protected exits: BS 476 Part 7 Class 1 or 2, or equivalent.

## Checked on 2026-11-07
- **Para 5.26 FH/HR supply tank:** minimum effective quantity by the gross area of the largest floor: ≤ 230 m² 9,000 L; ≤ 460 m² 18,000 L; ≤ 920 m² 27,000 L; > 920 m² 36,000 L. `fsi_check.py` reports PASS or FAIL.
- **FSD certificate:** the Fire Services Certificate is **F.S. 172**, issued after a satisfactory inspection. The Certificate of Fire Service Installations and Equipment for maintenance and inspection is **F.S. 251**.
- **Later changes to the September 2022 Codes:** Circular Letter 1/2023 adds sprinklers to para 4.9 (car ports over 230 m², effective 1 April 2023). Circular Letter 4/2024 is a corrigendum and does not change para 5.26. Circular Letter 3/2023 sets the gas extraction specification for battery rooms and charging facilities, for building plans first received on or after 1 September 2023. The copy of the English Code in the document library does not include the 1/2023 change.
- **Part V scope:** the tool checks para 5.26 tank size only. Other Part V design specifications are for manual checking against the Code.

## Still unverified
- The Part II pressurization table.
