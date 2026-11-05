# Part E – Fire properties of elements and materials (FS Code 2011, 2024 Ed.)

Draft working rules. Data: `part_e.json`. Tool: `../tools/part_e_check.py`.

## FRR of elements
- Deemed-to-satisfy values are in Tables E2–E7:
  - Walls: brick, RC with ≥1% steel and with <1% steel, hollow blocks.
  - Floors: RC and prestressed.
  - Steel columns and beams with encasement.
  - RC columns: fully exposed, 50% exposed, one face exposed.
  - RC and prestressed beams; RC stairs.
- The tables give minimum thickness, size, width or waist, and cover, at 60, 120 and 240 min.
- Starred covers (high cover at 240 min, and beams at 120 min) need mesh or lath within 20 mm of the face.
- Anything outside the tables needs a test report from a HOKLAS-accredited lab (or an MRA partner lab), or an assessment by an HKCAS-accredited body (E16).

## Reaction to fire of linings (E13, E14, Table E1)
- Euroclasses run A1, A2, B, C, D, E, F.
- Table E1 maps them to BS 476 classes (Class 0, Class 1 ...).
- Minimum class by location:

| Location | Minimum class |
| --- | --- |
| Protected exits | C |
| Use class 3 general | B |
| 5a auditoria | C |

## Test standards
- The BS EN suite is primary. BS 476 parts remain acceptable until obsolete. See `test_standards` in `part_e.json`.
- Doors (BS EN 1634) must be tagged or labelled.
- Dampers must be certified by a registered specialist contractor (ventilation works).
