# Site supervision (Buildings Ordinance) and the architect on site

Draft working rules. Data: `supervision.json`. Tool: `../tools/supervision_plan.py`.

**[V]** checked on 2026-11-05 against the Code of Practice for Site Supervision 2009 (2024 Ed., rev. Aug 2024) and the Technical Memorandum for Supervision Plans 2009 (TM), read by automated extraction. **[U]** unverified.

## 1. Statutory site supervision (BO s.4, s.9, s.14A, s.39A; B(A)R reg 41) **[V, Cap. 123 version 1.3.2026 and Cap. 123A version 30.6.2024]**
- Every building works project needs a **supervision plan** in the BD standard form (CoP Appendix I). It names each Technically Competent Person (TCP) and the frequency or extent of supervision. **[V]**
- Lodge it before or with the first consent application. For minor works under the simplified requirements, at least 7 days before commencement. **[V]**
- Confirm TCP appointments as an annex to the plan or within 7 days of commencement. Notify the BA of any later change of TCP. **[V]**
- Four streams: AS (registered contractor's Authorized Signatory), AP, RSE, RGE. Each stream appoints its own TCPs. **[V]**

## 2. TCP grades (TM Table 2) **[V]**
| Grade | Role | Minimum |
| --- | --- | --- |
| T1 | routine safety supervision | certificate / diploma + 2 years |
| T2 | routine safety supervision | higher certificate / HD + 3 years |
| T3 | routine safety supervision | HC/HD + 5 years, or degree + 2 years |
| T4 | engineering safety supervision | degree + 4 years, or registered professional |
| T5 | engineering safety supervision | registered professional + 5 years |
The AP, RSE and RGE are deemed to meet these minimums in their own streams (CoP 4.6). **[V]**

## 3. TM Table 1: minimum grade and frequency **[V, rendered PDF pages 28-29, 2026-11-06]**
Levels: 1 as and when required · 2 monthly · 3 fortnightly · 4 weekly · 5 full-time. Each principal (AS, AP, RSE, RGE) is at level 1 personally.

| Works (TM row) | RC / AS stream | AP stream | RSE stream | RGE stream |
| --- | --- | --- | --- | --- |
| Ground investigation field works | T1 L5, T4 L4 | T3 L3 | – | T3 L5, T5 L4 |
| Significant geotechnical: foundation | T1 L5, T2 L5, T4 L4 | T3 L4, T4 L2 | T3 L5, T5 L4 | T3 L5, T5 L4 |
| Significant geotechnical: others | T1 L5, T2 L4, T4 L4 | T3 L4, T4 L2 | T3 L4, T5 L3 | T3 L5, T5 L4 |
| Foundation (other) | T1 L5, T2 L5, T4 L4 | T3 L4, T4 L2 | T3 L5, T5 L4 | – |
| All other building works / street works | T1 L5, T3 L4, T4 L4 | T3 L4, T4 L2 | T3 L4, T5 L3 | – |
| Class I minor works (AP only) | T1 L5, T3 L4 | T3 L4 | – | – |
| Class I minor works, + RSE | – | – | T3 L4 | – |
| Class I minor works, + RGE | – | – | – | T2 L5 |

Notes: higher grade or more frequent inspection may be required at critical stages (Note 2); CoP defines "significant geotechnical content" (Notes 4, 5).
The tool maps Table 8.1 work types to these rows (`work_type_to_tm_row`: piles, pile walls and cap/footing/basement → foundation; the rest → all other). Override with `tm_row` where the mapping is wrong. A higher grade is assumed to satisfy a lower one **[U]**.

## 4. Scale of works (CoP section 8, Table 8.1) **[V]**
- Scale factor = estimated value ÷ basic value of the measurable item, capped at 2.
- Factor 1 means a full-day inspection on each occasion. Below 1, each visit may be shorter, but the frequency never drops below TM Table 1.
- Basic values: superstructure 20,000 m² CFA; curtain wall 10,000 m²; demolition 750 m² per storey; cap/footing/basement HK$47M; A&A HK$17.5M; large-diameter bored piles HK$19M/month; other piles HK$9.5M/month; ELS HK$8M/month; site formation HK$40M; minor works HK$11M. Full list in the JSON.
- Costs follow the Estimated Total Value of Construction Operations reported to the CIC. Contingency, fluctuation, non-BO E&M and exempted fitting-out can be deducted. A revised contract sum that changes the factor needs a revised plan.

## 5. Specific requirements **[V]**
- Full-time TCPs stay on site; the RC resources continuous supervision (8.8).
- Tower crane supporting temporary works: designer and independent checker each a registered professional engineer (civil/structural) with ≥ 5 years experience (4.12).
- Soil nailing: one TCP T3 (RGE) and one TCP T1 (RSC) resident full-time at every stage (6.15).
- Significant geotechnical works: RGE normally provides TCP T3 and T5; a Directorate Site Supervisor may be needed on difficult sites (7.3).
- Foundations in Scheduled Areas and the Northshore Lantau Designated Area need extra RGE supervision (8.3).

## 6. AP's site duties (statutory) **[U wording]**
- Periodic inspection of the works by the AP or AP's TCPs at the stated frequency; record in the site supervision log book.
- Notify the BA of contraventions and of dangerous conditions; stop works where needed.
- Certify completion, with the RSE and RC: Form BA13 for an occupation permit, BA12 for a temporary occupation permit, BA14 for works not creating a new building (see `../submission/forms.json`). Superstructure supervision covers fire safety construction, means of escape, drainage and finishes affecting B(P)R compliance.

## 7. Architect's contractual site role (SFBC) **[V clause numbers]**
- Access to the works (cl. 11), Architect's representative / clerk of works (cl. 12), instructions (cl. 4), materials testing and opening up (cl. 8), Substantial Completion inspection (cl. 17).
- Site meetings: minutes, instruction log, RFI log, submission log, inspection records, defects lists. Keep statutory and contractual records separate but cross-referenced.

## 8. Safety
- Construction Sites (Safety) Regulations (Cap. 59I) and the Factories and Industrial Undertakings Ordinance (Cap. 59) put site safety on the contractor; the designer must still design for safe construction and maintenance. **[U]**

## Notes on sources
- BO s.37 is "Limitation of public liability", not a supervision provision. An earlier version of this document cited it wrongly.
- The BA form numbers in `../submission/forms.json` were checked against [BD's forms list](https://www.bd.gov.hk/en/resources/forms/form_nbw.html) on 2026-11-07. All 24 match.
