---
name: "hk-bd-submission-workflow"
description: "Run Hong Kong Buildings Department submissions: plans (BA5), centralised processing, BD comments and resubmission, consent (BA8/BA8A), amendments, OP/TOP (BA12/BA13), with deadlines."
---

# HK BD submission workflow

Use when the user asks about getting plans approved by BD, replying to a BD disapproval or departmental comments, applying for consent to commence, amendment plans, withdrawal and resubmission, or applying for an occupation permit. Also for PA exam questions on the building approval process.

## Before starting
1. Read `/mnt/project-files/architect-kb/submission/README.md` and `submission/bd-submission-process.md`.
2. Every fact there is marked ✅ (read on bd.gov.hk) or ⚠️ (unverified). If an answer depends on a ⚠️ item (e.g. the 30-day resubmission period, the 14-day OP period, BO section numbers), say so. If the user has uploaded Cap. 123 / Cap. 123A, check the section first and update the file.

## Work out where the project is
Ask only for what is missing (one short list):
- Kind of works: new building, A&A, demolition, site formation, foundation, minor works.
- Each submission so far: type (first / resubmission / amendment / fast track), date, W&R letters, result and date.
- Consent applications: date, concurrent or not, approval date, granted date. For BA8A: foundation type and footing depth, precautionary works, reg 8 plans, supervision plan.
- Commencement date and BA10 date; amendments in progress and their size (Appendix G thresholds).
- For OP: the prerequisites in `submission/templates/op-application-checklist.md`.

## Run
1. Write a `submission` block following `examples/demo_submission.json` (fields in the docstring of `tools/submission_timeline.py`).
2. `python3 /mnt/project-files/architect-kb/tools/submission_timeline.py <file>.json -o <report>.md`
3. Save input and report under `/mnt/project-files/projects/<project-name>/`.

## Outputs by task
- **BD disapproval / comments:** fill `submission/templates/reply-to-bd-comments.md` item by item. Separate BO fundamental items (disapproval) from advisory and departmental comments (ADM-2, ADM-19). For each change, re-run the affected checkers (`bpr_check.py`, `moe_check.py`, `fire_cd_check.py`) so a fix does not open a new failure.
- **Deadline close, issue fixable soon:** consider W&R, `submission/templates/withdraw-and-resubmit-letter.md`; at most two times (ADM-22).
- **Consent:** `submission/templates/consent-application-checklist.md`.
- **OP / TOP:** `submission/templates/op-application-checklist.md`.
- **Exam answer:** explain the sequence (section 1 of the knowledge file), cite PNAP numbers, and name the forms.

## Report back
- Lead with the next deadline and anything FAIL / CHECK, with the action.
- State: draft for review and signature by the AP; ⚠️ items not checked against the Ordinance.
- Do not send anything to BD or any department. The AP signs and submits.

## Limits
Does not cover lease / LandsD procedures, s.16 planning applications, or FSD's own FSI approval process in detail. Minor works, UBW and MBIS are in the `hk-minor-works-ubw-mbis` skill.
