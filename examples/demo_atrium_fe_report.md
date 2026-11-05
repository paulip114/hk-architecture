# Part G timeline screening – Demo – mall atrium extended travel distance

**Result: fails the screening** (1 fail, 4 to check).

> Screening only (one-zone smoke filling, single room). Not a substitute for CFD / zone modelling, hot smoke test or the FSAR. Draft for review by an Authorized Person and the fire engineer; the Building Authority must accept design fire, pre-movement time, tenability criteria and safety factor.

| Clause | Item | Value | Basis / limit | Result | Note |
| --- | --- | --- | --- | --- | --- |
| Table G1 | Atrium, sprinklered, with extraction design fire headroom | 12 m | Table G1 value is for 2.5 m | CHECK | Sprinkler activation and controlled HRR change with headroom: justify or recalculate |
| G6.5 | Atrium, sprinklered, with extraction design fire | fast t², cap 1.50 MW | Table G1 use 4b sprinkler-controlled | INFO |  |
| G6.8 | Atrium, sprinklered, with extraction time to smoke layer at 2.0 m | > 1800 s (layer 9.48 m) | tenability | INFO |  |
| G6.8 | Atrium, sprinklered, with extraction time to layer 200 °C (≈2.5 kW/m²) | > 1800 s (layer 52 °C) | tenability | INFO |  |
| Table G2 | Atrium, sprinklered, with extraction pre-movement (retail, restaurant, cinema, theatre, voice alarm) | 180 s | pd7974_t2 2 min + 1.0 (note e) | INFO | row: pd7974_t1 0.5, pd7974_t2 2, sfpe <2, nz_origin 0.5, nz_remote 1, cibse 3; use one source consistently |
| G6.7 | Atrium, sprinklered, with extraction movement inputs | v = 1.2 m/s, Fs = 1.3 p/s/m, edge 0.15 m | not given in FS Code | INFO | SFPE / PD 7974-6 typical values: justify in FSAR |
| G6.7 | Atrium, sprinklered, with extraction RSET | 394 s | det 90 + alarm 30 + pre 180 + move 94 (travel 50, flow 94 over 4.90 m) | INFO |  |
| G3.4 / G6.4 | Atrium, sprinklered, with extraction ASET vs RSET | ASET >1800 s | 1.5 × RSET = 591 s | PASS | safety factor / margin to be agreed with BD (G3.4) |
| G6.8 | Atrium, sprinklered, with extraction CO, visibility | - | CO ≤ 1000 ppm, OD ≤ 0.1 /m (10 m) | CHECK | Not modelled here: needs soot/CO yields in CFD or zone model |
| Table G1 | Shop unit, sprinklered, no extraction design fire headroom | 3.5 m | Table G1 value is for 2.5 m | CHECK | Sprinkler activation and controlled HRR change with headroom: justify or recalculate |
| G6.5 | Shop unit, sprinklered, no extraction design fire | fast t², cap 1.50 MW | Table G1 use 4b sprinkler-controlled | INFO |  |
| G6.8 | Shop unit, sprinklered, no extraction time to smoke layer at 2.0 m | 154 s | tenability | INFO |  |
| G6.8 | Shop unit, sprinklered, no extraction time to layer 200 °C (≈2.5 kW/m²) | 224 s | tenability | INFO |  |
| Table G2 | Shop unit, sprinklered, no extraction pre-movement (retail, restaurant, cinema, theatre, standard alarm) | 180 s | pd7974_t2 3 min | INFO | row: pd7974_t1 1, pd7974_t2 3, sfpe 3, nz_origin 1, nz_remote 2, cibse 3; use one source consistently |
| G6.7 | Shop unit, sprinklered, no extraction movement inputs | v = 1.2 m/s, Fs = 1.3 p/s/m, edge 0.15 m | not given in FS Code | INFO | SFPE / PD 7974-6 typical values: justify in FSAR |
| G6.7 | Shop unit, sprinklered, no extraction RSET | 291 s | det 60 + alarm 0 + pre 180 + move 51 (travel 25, flow 51 over 1.50 m) | INFO |  |
| G3.4 / G6.4 | Shop unit, sprinklered, no extraction ASET vs RSET | ASET 154 s | 1.5 × RSET = 437 s | FAIL | safety factor / margin to be agreed with BD (G3.4) |
| G6.8 | Shop unit, sprinklered, no extraction CO, visibility | - | CO ≤ 1000 ppm, OD ≤ 0.1 /m (10 m) | CHECK | Not modelled here: needs soot/CO yields in CFD or zone model |
