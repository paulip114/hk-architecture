# 範本：回覆 BD 不批准 / 意見信（Response Schedule）

用法：BD 不批准信或者部門意見到咗之後，逐項填。重新遞交時附喺 cover letter 後面。
原則（PNAP ADM-2 ✅）：
- 只有《建築物條例》下嘅基本事項先係不批准理由；其他部門意見係參考，但要回應，唔好漏。
- 60 日內已列出嘅不批准項目，重交時 BD 一般唔會加新項目，所以每項都要清楚回應。
- 有爭議嘅非 BO 事項，交返有關部門處理；可要求 BD 召開會議。

所有內容係草稿，要 AP 覆核簽署。

---

**[AP 公司信頭]**

Our Ref: [ ]　　Your Ref: BD [ ]

Date: [YYYY-MM-DD]

The Building Authority
Buildings Department
[Division / Unit]
[Address]

Attn: [Building Surveyor / Structural Engineer 姓名]

Dear Sir / Madam,

**[Lot No.], [Address]: Resubmission of General Building Plans**
**Your letter of disapproval dated [ ] (BD Ref. [ ])**

We refer to your letter above and resubmit the general building plans (Drawing Nos. [ ]) under Form BA5 for your approval. Our responses to the items raised are set out in the schedule below. Amendments are clouded and annotated on the plans.

[如屬撤回並重新遞交：] We hereby withdraw and resubmit the above submission under PNAP ADM-22 for the following reasons: [理由]. This is the [first / second] withdrawal and resubmission of this submission.

Yours faithfully,

[AP 姓名]
Authorized Person (List of Architects)
for and on behalf of [公司]

c.c. [Client], [RSE], [其他顧問]

---

## Response Schedule

| BD Item | BD / Dept comment (摘要) | Regulation / PNAP | Category | Response | Drawing / doc ref |
| --- | --- | --- | --- | --- | --- |
| 1 | [例：Means of escape from 3/F exceeds travel distance] | FS Code 2011 B[ ] / B(P)R reg 41(1) | Disapproval (s.16(1)(d)?) | Additional staircase provided; travel distance now [ ] m < [ ] m. See calc. | GBP-03 Rev B; MOE calc Appx 2 |
| 2 | [例：GFA exemption for balcony not justified] | PNAP APP-2, APP-151 | Disapproval | [Areas re-calculated / exemption withdrawn / justification] | GBP-20 Rev B; Appx G table |
| 3 | [例：FSD: provide FSI drawings] | — | Advisory (FSD) | Noted. FSI proposals will be submitted to FSD under separate cover by [date]. | — |
| 4 | [例：PlanD: building height exceeds OZP] | OZP [ ] | Advisory (PlanD) | Height reduced to [ ] mPD / s.16 application No. [ ] approved on [ ]. | GBP-30 Rev B |
| 5 | [例：LandsD: lease clause [ ] non-compliance] | Lease | Advisory (LandsD) | To be resolved with DLO; no BO implications. | — |

**Category** 填：Disapproval（BO 基本事項）、Advisory（BD 非基本）、[部門] for information。

## 回覆寫法（每項）
1. **重述問題**：一句，唔好爭拗字眼。
2. **處理方式**：「已修改」、「已補交資料」、「維持原設計，理由係……」三揀一。
3. **證明**：圖號 + 版本、計算書頁碼、PNAP / 守則條文。
4. **如果唔同意**：引用條文，建議開會或者申請 s.42 豁免/變通（BA16）。語氣中性。
5. **跟進日期**：如果要另行處理（FSD、LandsD），寫預計日期。

## 重交前自查
- [ ] 每一個 BD item 都有回覆（包括非不批准項目）
- [ ] 修改有雲線及註明，圖則版本已更新
- [ ] 有冇因為修改引起新問題（例如加樓梯影響 GFA、上蓋面積、窗戶採光）——跑一次 `tools/bpr_check.py`、`tools/moe_check.py`
- [ ] 有 BD 106 條件嘅，已反映喺圖則
- [ ] 份數 / ESH 檔案符合 ADM-2
- [ ] 如屬 W&R，未超過兩次（ADM-22）
- [ ] 用 `tools/submission_timeline.py` 更新處理期限
