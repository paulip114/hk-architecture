# Site supervision (Buildings Ordinance) and the architect on site

Draft working rules. Data: `supervision.json`. Tool: `../tools/supervision_plan.py`.

**[V]** checked on 2026-11-05 against the Code of Practice for Site Supervision 2009 (2024 Ed., rev. Aug 2024) and the Technical Memorandum for Supervision Plans 2009 (TM), read by automated extraction. **[U]** unverified.

## 1. Statutory site supervision (BO s.37, s.39A; B(A)R) **[U section numbers]**
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

## 3. Frequency (TM Table 1 key) **[V]**
Level 1 as and when required; 2 monthly; 3 fortnightly; 4 weekly; 5 full-time during site working hours.
The grade and level for each works type and stream are in TM Table 1. **They are not encoded here**: the extraction did not keep the table's columns. Read them from the TM for every plan. **[open item]**

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
- Certify completion (Form BA12 for the occupation permit, with RSE and RC). Superstructure supervision covers fire safety construction, means of escape, drainage and finishes affecting B(P)R compliance.

## 7. Architect's contractual site role (SFBC) **[V clause numbers]**
- Access to the works (cl. 11), Architect's representative / clerk of works (cl. 12), instructions (cl. 4), materials testing and opening up (cl. 8), Substantial Completion inspection (cl. 17).
- Site meetings: minutes, instruction log, RFI log, submission log, inspection records, defects lists. Keep statutory and contractual records separate but cross-referenced.

## 8. Safety
- Construction Sites (Safety) Regulations (Cap. 59I) and the Factories and Industrial Undertakings Ordinance (Cap. 59) put site safety on the contractor; the designer must still design for safe construction and maintenance. **[U]**

## Open items
- Encode TM Table 1 rows after a manual read of the TM PDF.
- Check BO / B(A)R section numbers and the BA forms (BA10 consent, BA12, BA14) against the current BD forms list.
