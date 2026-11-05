---
name: "hk-minor-works-ubw-mbis"
description: "Hong Kong existing-building procedures: Minor Works Control System (Class I/II/III, MW forms), unauthorised building works orders, and mandatory building / window inspection (MBIS / MWIS)."
---

# HK minor works, UBW and MBIS / MWIS

Use when the user asks whether small works need BD approval, which minor works class applies, the MW forms and notice periods, how to deal with an unauthorised building works order or a suspected UBW, or what an owner must do under MBIS / MWIS. Also for PA exam questions on these schemes.

## Before starting
Read `/mnt/project-files/architect-kb/submission/minor-works.md`, `submission/ubw-enforcement.md` and `submission/mbis-mwis.md`. Facts are marked ✅ (read on bd.gov.hk) or ⚠️ (unverified). Say so when an answer rests on a ⚠️ item (e.g. penalties under s.40, MBIS 10-year / MWIS 5-year cycle, details of the validation schemes).

## Minor works
1. Decide: building works at all? Designated exempted works? On the minor works list? Which class? (flow in section 5 of `minor-works.md`). The Schedule 1 item list in Cap. 123N is not in the knowledge base: if the class depends on the exact item, say so and ask for the item number or the regulation.
2. State appointments (Class I: PBP + PRC; II and III: PRC), forms (MW01/02, MW03/04, MW05) and timing (7 days before commencement for I and II; 14 days after completion for all).
3. To check dates, add a `minor_works` list to the `submission` block and run `python3 /mnt/project-files/architect-kb/tools/submission_timeline.py <file>.json`.

## UBW
1. Classify each item against BD's actionable categories (section 2 of `ubw-enforcement.md`).
2. For each: remove, regularise by A&A submission or minor works, or validate under a validation scheme.
3. Fill `submission/templates/ubw-order-response-plan.md`.

## MBIS / MWIS
1. Check liability (age 30+ / 10+; domestic buildings of 3 storeys or less excluded).
2. Lay out the sequence and forms (MBI1 to MBI5) with `submission/templates/mbis-inspection-programme.md`.
3. The RI's report is due 7 days after inspection; add an `mbis` block to run the date check.

## Report back
Lead with the answer (needs approval or not; which class; what to submit by when). State that it is a draft for review by the PBP / RI / AP, and list ⚠️ items. Do not submit anything to BD.
