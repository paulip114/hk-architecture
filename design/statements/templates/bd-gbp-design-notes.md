# [項目名稱] – Building Plans Submission: Design Notes and GFA Concessions

> 範本，用作一般建築圖則 (GBP) 申請嘅附函／說明。屋宇署讀者要嘅係數字同依據，唔係概念。正式文件用英文。

## 1. Particulars 基本資料
- Lot no. / address: [ ]
- Authorized Person: [ ]  Registered Structural Engineer: [ ]  Registered Geotechnical Engineer: [ ]
- Submission: [first submission / amendment no. ]
- Building type: [domestic / non-domestic / composite]; site class [A/B/C] (reg 18A)

## 2. Development Parameters 發展參數
| Item | B(P)R limit | OZP / Lease limit | Proposed |
| --- | --- | --- | --- |
| Site area (reg 23(2)) | – | – | [ ] m² |
| Plot ratio / GFA (reg 21) | [ ] | [ ] | [ ] |
| Site coverage (reg 20) | [ ] % | [ ] % | [ ] % |
| Building height (reg 23(1)) | – | [ ] mPD | [ ] m / [ ] mPD |
| Open space (reg 25) | [ ] m² | – | [ ] m² |

（由 `tools/bpr_check.py` 報告抄錄，並附報告。）

## 3. GFA Exclusions and Concessions GFA 寬免
| Item | Floor | Area m² | Basis | Within APP-151 10% cap? |
| --- | --- | --- | --- | --- |
| Mandatory plant room | [ ] | [ ] | reg 23(3)(b), APP-2 | No (outside cap) |
| Non-mandatory plant room | [ ] | [ ] | APP-2, APP-151 | Yes |
| Balcony / utility platform / green features | [ ] | [ ] | APP-151 (JPN 1/2/…) | Yes |
| Car park | [ ] | [ ] | APP-2 para 18 | No |
| Refuge floor | [ ] | [ ] | APP-2 para 5 | No |
| **Capped total** | | [ ] | ≤ 10% of total GFA = [ ] | |

Prerequisites (APP-151): SBD compliance (section 4); BEAM Plus provisional registration [ref no.]; energy efficiency [OTTV / RTTV / BEC report].

## 4. Sustainable Building Design (APP-152)
| Guideline | Requirement | Provided | Drawing |
| --- | --- | --- | --- |
| Building separation | [permeability % / gap width] | [ ] | [ ] |
| Building setback | [ ] | [ ] | [ ] |
| Site coverage of greenery | [ ] % (of site area, part at pedestrian zone) | [ ] % | [ ] |

## 5. Fire Safety 消防安全（FS Code 2011）
摘要：避火層、樓梯數目及闊度、走火距離、消防員升降機、EVA；附 `moe_check.py`、`fire_cd_check.py` 報告。任何以性能為本設計 (Part G) 要列出並附 FSAR。

## 6. Modifications / Exemptions 豁免或修改申請（如有）
| Regulation | Requirement | Proposal | Justification | Compensatory measures |
| --- | --- | --- | --- | --- |
| [ ] | [ ] | [ ] | [ ] | [ ] |

## 7. Design Intent 設計意圖（一段，最多 150 字）
只講影響審批嘅設計決定，例如點解要轉換層、平台後移、架空層。

---
Draft for review and signature by the Authorized Person. Verify every PNAP reference against the current Buildings Department version.
