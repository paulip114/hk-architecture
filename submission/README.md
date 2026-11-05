# 入則程序（Building submission procedures）

Hong Kong Buildings Department procedures from plan submission to occupation permit, plus minor works, unauthorised building works and mandatory building inspection.

**Verification:** each fact is marked ✅ (read on bd.gov.hk on 2026-11-05, source given) or ⚠️ (general practice knowledge, not yet checked). The Buildings Ordinance (Cap. 123) and Building (Administration) Regulations (Cap. 123A) could not be read from this environment (eLegislation blocks automated access). Upload their consolidated PDFs to `uploads/` to verify the ⚠️ items.

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

## Open items (⚠️)
- BO s.15 resubmission period (30 days), deemed approval, s.16(1) grounds, s.21 OP period (14 days), s.24 / s.40 penalties.
- BA10 notice period, consent lapse and BA9 renewal period, BA15 notice period.
- Technical Memorandum for Supervision Plans (TCP grades, supervision streams).
- Cap. 123N Schedule 1 item list; designated exempted works; validation scheme details.
- MBIS / MWIS cycles; MWIS forms; whether the 2015 guidelines have been revised.
- Departmental certificates needed for OP (FSD, EMSD, WSD, DSD) by name and form.
