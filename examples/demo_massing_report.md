# Massing study – 示範：堅尼地城商住地盤體量比較（虛構）

> Design-stage screening. Exemptions are estimates; re-run bpr_check with the real area schedule before reporting figures. Draft for review by an Authorized Person.

Site area 1,000.00 m², building type composite.

| Option | Storeys | Height m (above street) | mPD | Gross m² | Accountable GFA m² | PR | B(P)R | Fail | Check |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A 三層商業平台＋單塔 | 26 | 88.80 | 95.3 | 11,390.00 | 9,765.00 | 9.765 | PASS | 0 | 0 |
| B 兩層平台＋高塔（地積比用到盡） | 35 | 115.30 | 121.8 | 13,740.00 | 11,988.00 | 11.988 | FAIL | 4 | 0 |
| C 平台上雙塔 | 24 | 81.15 | 87.6 | 11,360.00 | 9,918.00 | 9.918 | PASS | 0 | 0 |

## A 三層商業平台＋單塔

最常見做法：平台做零售，轉換層上面住宅塔，塔樓貼近主街以爭取景觀。

| Block | Use | Storeys | F-F m | Plate m² | Footprint m² | From +m | To +m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Podium retail | non_domestic | 3 | 5.0 | 950.00 | 950.00 | 0 | 15 |
| Transfer + clubhouse | domestic | 1 | 4.5 | 330.00 | 330.00 | 15 | 19.5 |
| Tower flats | domestic | 22 | 3.15 | 330.00 | 330.00 | 19.5 | 88.8 |

| Reg | Item | Proposed | Limit | Result | Note |
| --- | --- | --- | --- | --- | --- |
| OZP | Height restriction | 88.8 m | ≤ 110 m | PASS |  |
| 21(2) | Composite: Dd/Pd + Dn/Pn | 0.963 | ≤ 1.000 | PASS | Dn = 2.736 (Pn 15); Dd = 7.029 (Pd 9.0); max domestic PR at this Dn = 7.358 |
| 21(3) | Total accountable GFA | 9,765.00 m² | - | INFO | domestic 7,029.00 m², non-domestic 2,736.00 m²; gross built 11,390.00 m² |
| OZP | Total PR | 9.765 | ≤ 10 | PASS |  |
| 20 | Site coverage – SC at +0 m (Podium retail) (+0.0 m) | 95.0% | ≤ 100.0% | PASS | non-domestic ≤ 15 m (reg 20(3)) |
| 20 | Site coverage – SC at +15 m (Transfer + clubhouse) (+15.0 m) | 33.0% | ≤ 37.5% | PASS | domestic table, class B |
| 20 | Site coverage – SC at +19.5 m (Tower flats) (+19.5 m) | 33.0% | ≤ 37.5% | PASS | domestic table, class B |
| 25 / Sch 2 | Open space | 120.00 m² | ≥ 109.99 m² (0.333 × roofed-over) | PASS |  |
- OZP 120 mPD PASS

## B 兩層平台＋高塔（地積比用到盡）

反面教材：以為減少商業樓面就可以加住宅，但複合地積比 (reg 21(2)) 同 OZP 總地積比同時超標，高度亦超限。

| Block | Use | Storeys | F-F m | Plate m² | Footprint m² | From +m | To +m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Podium retail | non_domestic | 2 | 5.0 | 950.00 | 950.00 | 0 | 10 |
| Transfer + clubhouse | domestic | 1 | 4.5 | 330.00 | 330.00 | 10 | 14.5 |
| Tower flats | domestic | 32 | 3.15 | 330.00 | 330.00 | 14.5 | 115.3 |

| Reg | Item | Proposed | Limit | Result | Note |
| --- | --- | --- | --- | --- | --- |
| OZP | Height restriction | 115.3 m | ≤ 110 m | FAIL |  |
| 21(2) | Composite: Dd/Pd + Dn/Pn | 1.251 | ≤ 1.000 | FAIL | Dn = 1.824 (Pn 15); Dd = 10.164 (Pd 9.0); max domestic PR at this Dn = 7.906 |
| 21(3) | Total accountable GFA | 11,988.00 m² | - | INFO | domestic 10,164.00 m², non-domestic 1,824.00 m²; gross built 13,740.00 m² |
| OZP | Total PR | 11.988 | ≤ 10 | FAIL |  |
| 20 | Site coverage – SC at +0 m (Podium retail) (+0.0 m) | 95.0% | ≤ 100.0% | PASS | non-domestic ≤ 15 m (reg 20(3)) |
| 20 | Site coverage – SC at +10 m (Transfer + clubhouse) (+10.0 m) | 33.0% | ≤ 37.5% | PASS | domestic table, class B |
| 20 | Site coverage – SC at +14.5 m (Tower flats) (+14.5 m) | 33.0% | ≤ 37.5% | PASS | domestic table, class B |
| 25 / Sch 2 | Open space | 120.00 m² | ≥ 109.99 m² (0.333 × roofed-over) | PASS |  |
- OZP 120 mPD FAIL

**To fix:** Height restriction 115.3 m vs ≤ 110 m; Composite: Dd/Pd + Dn/Pn 1.251 vs ≤ 1.000; Total PR 11.988 vs ≤ 10; Height (mPD) 121.8 vs 120

## C 平台上雙塔

兩座細塔並排（塔距要另核 APP-152 樓宇間距），通風同景觀較好，但每層核心筒重複，實用率較低。

| Block | Use | Storeys | F-F m | Plate m² | Footprint m² | From +m | To +m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Podium retail | non_domestic | 3 | 5.0 | 950.00 | 950.00 | 0 | 15 |
| Tower 1 | domestic | 21 | 3.15 | 180.00 | 180.00 | 15 | 81.15 |
| Tower 2 | domestic | 21 | 3.15 | 180.00 | 180.00 | 15 | 81.15 |

| Reg | Item | Proposed | Limit | Result | Note |
| --- | --- | --- | --- | --- | --- |
| OZP | Height restriction | 81.15 m | ≤ 110 m | PASS |  |
| 21(2) | Composite: Dd/Pd + Dn/Pn | 0.980 | ≤ 1.000 | PASS | Dn = 2.736 (Pn 15); Dd = 7.182 (Pd 9.0); max domestic PR at this Dn = 7.358 |
| 21(3) | Total accountable GFA | 9,918.00 m² | - | INFO | domestic 7,182.00 m², non-domestic 2,736.00 m²; gross built 11,360.00 m² |
| OZP | Total PR | 9.918 | ≤ 10 | PASS |  |
| 20 | Site coverage – SC at +0 m (Podium retail) (+0.0 m) | 95.0% | ≤ 100.0% | PASS | non-domestic ≤ 15 m (reg 20(3)) |
| 20 | Site coverage – SC at +15 m (Tower 1 + Tower 2) (+15.0 m) | 36.0% | ≤ 37.5% | PASS | domestic table, class B |
| 25 / Sch 2 | Open space | 120.00 m² | ≥ 109.99 m² (0.333 × roofed-over) | PASS |  |
- OZP 120 mPD PASS

## Next steps

- Pick an option, replace `exempt_pct` with the real exemption list, run `bpr_check.py` on the saved project file.
- Add `means_of_escape`, `fire_construction` and `means_of_access` blocks and run the FS Code tools.
- Check SBD (PNAP APP-152) separation, setback and greenery, and the APP-151 10% cap, outside this tool.
