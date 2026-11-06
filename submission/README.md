# 入則程序（Building submission procedures）

Hong Kong Buildings Department procedures from plan submission to occupation permit, plus minor works, unauthorised building works and mandatory building inspection.

**Verification:** each fact is marked ✅ (read on bd.gov.hk on 2026-11-05), 📜 (checked on 2026-11-06 against the uploaded consolidated texts: Cap. 123 version date 1.3.2026, Cap. 123A version date 30.6.2024) or ⚠️ (not yet checked).

| Path | What it is |
| --- | --- |
| `bd-submission-process.md` | Full workflow: pre-submission, BA5 / ESH, centralised processing (ADM-2), fundamental items and staged curtailed check (ADM-19), processing periods, W&R (ADM-22), minor amendments (ADM-14), consent (BA8 / BA8A), site supervision (ADM-13), amendment plans, OP / TOP |
| `minor-works.md` | Minor Works Control System: classes, appointments, MW forms, 7-day / 14-day rules, validation schemes |
| `ubw-enforcement.md` | UBW definition, BD's actionable categories, orders and warning notices, AP practice |
| `mbis-mwis.md` | Mandatory building / window inspection: scope, RI / QP, sequence, MBI forms, penalties |
| `periods.json` | Processing periods and limits as data, each with source and `verified` flag |
| `forms.json` | BA, MW and MBI forms with workflow stage |
| `templates/reply-to-bd-comments.md` | Cover letter and response schedule for BD disapproval / departmental comments |
| `templates/withdraw-and-resubmit-letter.md` | W&R letter (ADM-22) |
| `templates/consent-application-checklist.md` | Consent (BA8 / BA8A) and commencement checklist |
| `templates/op-application-checklist.md` | OP / TOP checklist |
| `templates/ubw-order-response-plan.md` | Work plan for a UBW removal order |
| `templates/mbis-inspection-programme.md` | MBIS work plan / fee scope |
| `../tools/submission_timeline.py` | Deadline and procedure checker: `python3 tools/submission_timeline.py project.json -o report.md` (reads `submission`) |
| `../examples/demo_submission.json`, `demo_submission_report.md` | Demo input and output |
| `../skills/hk-bd-submission-workflow/`, `../skills/hk-minor-works-ubw-mbis/` | Skills that use these files |

## Verified against the Ordinance (📜)
- Plans: 60 days first submission / major revision, 30 days other resubmissions, deemed approval (B(A)R reg 30(3), BO s.15); s.16(1) grounds.
- Consent: 28 days (reg 32(3)); amendments to consented works 28 days (reg 33(2)); lapse after 3 months not commenced or suspended (s.20); no deemed consent without supervision plan (s.14A).
- Notices: BA10 not less than 7 days before commencement (reg 20(1)); TCPs 7 days (reg 20(2)); AP ceasing 7 days (reg 19); change of use one month (s.25).
- Completion: RC 7 days, AP 14 days, RSE/RGE 7 days (reg 25); water certificate (reg 25A).
- OP: grounds of refusal (s.21(6)); deemed granted after 14 days (s.21(7), (8)); TOP rules (s.21(3)-(5)).
- Enforcement: s.24 orders, s.33 cost + 20% surcharge, s.40 penalties; MBIS s.30B (30 years), MWIS s.30C (10 years).

## Open items (⚠️)
- Cap. 1 s.71 day counting is checked (version 31.7.2026), but `tools/submission_timeline.py` does not move last days that fall on holidays or warning days.
- Technical Memorandum for Supervision Plans (TCP grades, supervision streams).
- Validation schemes: Cap. 123N does not mention them. See `minor-works.md`.
- Cap. 123P prescribed inspection scope and the MWIS forms have not been compared line by line with `mbis-mwis.md`.
- The FSD certificate needed for an OP application. The FSD Code names F.S. 251 as the RFSIC's certificate after maintenance or inspection, but it does not say this is the OP form.
- Fine levels in dollars (Cap. 221 Sch. 8).
