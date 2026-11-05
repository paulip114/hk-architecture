# Part F – Fire safety management (FS Code 2011, 2024 Ed.)

Data: `part_f.json`. Tool: `../tools/part_f_check.py` (reads `fire_safety_management`). All clauses below were checked against the full Code text.

## Status
- Advisory (F4.1), **except** in two cases:
  - Fire engineering: the FSAR may need a fire safety management plan (FSMP), which then forms part of the approved GBP.
  - BO s.42 modification of B(P)R 41(1), 41A–41D or B(C)R s.35: compliance with the FSMP is imposed as a condition.
- The tool marks missing items FAIL in those two cases and CHECK otherwise.
- Applies to all use classes (F3.1).

## Who does what (F3 commentary)
- Passive provisions at common parts: inspected and repaired under the BO.
- Active FSI: registered FSI contractor under Cap. 95B.
- Ventilating systems: registered specialist contractor (ventilation works) under Cap. 123J.
- The owners / OC engage a competent person (for example an AP) to document provisions, inspection periods and records, and to make documents available to the authorities.
- The AP helps compile the FSMP: approved GBP with exit routes highlighted, FSI plans, documents of installed provisions (F4.2).

## FSMP contents (F4.5)
1. **Maintenance plan (F5.1)**: (a) GBP with exit routes highlighted, (b) specifications of the provisions, (c) maintenance periods, (d) method statements, (e) repair methods, (f) records, (g) housekeeping, (h) final FSAR if any.
2. **Training plan (F6)**: staff duties on routine inspection and in a fire, training programme and records, appointed fire wardens, regular drills and seminars including persons with a disability. Fire wardens stop people stopping at refuge floors.
3. **Fire action plan (F7)**: dial 999, inform and assist occupants, evacuation and contingency plan, procedures for persons with a disability, temporary refuge space locations, and management staff in contact with people waiting there.

## Fire engineering (F4.3, F4.4)
- Bounding Conditions go on the GBP.
- The Bounding Conditions and the final FSAR go into the FSMP.
- The Bounding Conditions go into the DMC where applicable.
- Review and audit the FSMP periodically. Keep records of all alterations in it.

## Open kitchens (F5.8, with C13.4)
Put these in the FSMP and DMC:
- smoke detectors in the flat and in the common lobby
- a sprinkler head over the kitchen
- a -/30/30 full height wall (≥ 600 mm wide) next to the flat exit door
- an annual check by the management's registered FSI contractor, with the certificate sent to FSD

## Works in occupied buildings
- **A&A and repair works (F5.6)**:
  - keep the means of escape, fire doors and fire barriers
  - provide alternative measures where any are temporarily removed
  - use flame-retardant scaffold sheeting
  - control combustibles (Cap. 295)
  - notify FSD of FSI shutdowns
  - keep first-aid and firefighting equipment accessible
  - have an emergency plan and train workers
- **Lift works (F5.7)**:
  - Normally one landing door open per liftwell. Up to 3 may be open, with no hot work.
  - Where more than one door is removed, hoard the openings at -/120/-.
  - Vents in the hoarding: each ≤ 5,500 mm², at the upper portion, ≤ 2 per liftway and ≤ 4 in total.
  - The hoarding door has the same FRR as the hoarding, is self-closing, lockable and openable from inside without a key.
  - Temporary works in the liftwell are non-combustible.
  - Close or hoard all openings when the work is left unattended.

## Other law cited (F5.4)
- Cap. 95F: it is an offence to obstruct or lock the means of escape. Roof doors must be openable from the staircase side without a key.
- Cap. 95B r.7(1), 9(1): only a registered contractor maintains FSI.
- Cap. 509 (OSH).
- Cap. 279A r.38: schools hold a fire drill **at least every 6 months**.

## Housekeeping (Table F1)
- 31 items, under means of escape, fire resisting construction, access and others.
- Record each as yes / no / n/a in the `housekeeping` block.
- The tool lists any items not yet inspected.
