---
name: "hk-contract-admin"
description: "Administer a Hong Kong private building contract (HKIA/HKIS/HKICM SFBC forms) and the BD site supervision plan: EOT, liquidated damages, retention, notices, certificates, TCP schedule."
---

# HK contract administration and site supervision

Use when the user asks about the architect's role under a Hong Kong building contract (EOT, LD, variations, certificates, retention, DLP, disputes), the HKIA appointment agreement, PA Paper 2 questions, or a site supervision plan / TCP schedule under the Code of Practice for Site Supervision.

## Before starting
1. Read `/mnt/project-files/architect-kb/contracts/contract-rules.md` (and `supervision/site-supervision-rules.md` for supervision).
2. Items marked [U] are unverified. If the answer depends on one, say so.
3. Ask which form and edition applies (SFBCwQ.2005 / SFBCnQ.2006 rev. 2023, or the 2025 Edition) and for the Appendix values. Do not assume Appendix values.

## Run
- Contract: if the contract was made on or after 28 Aug 2025 and is above the CISPO threshold, set `cispo: true` and add `payment_claims[]`. Write a `contract` block following `examples/demo_practice.json`, then `python3 /mnt/project-files/architect-kb/tools/contract_admin.py <file>.json --as-of <date> -o <report>.md`.
- Supervision: write a `supervision` block, then `python3 .../tools/supervision_plan.py <file>.json -o <report>.md`. The tool checks TCPs against TM Table 1; override the TM row per work with `tm_row` where the default mapping is wrong.
- Save under `/mnt/project-files/projects/<project-name>/`.

## Report back
- Lead with the decision the Architect has to make (grant EOT? issue non-completion certificate? reject late particulars?) and the clause.
- Keep the contractual role (Architect under SFBC) separate from the statutory role (AP under the Buildings Ordinance).
- For exam answers: clause, who acts, by when, with what document.
- State: draft for the Architect / AP; check against the signed contract and its Appendix; not legal advice.
