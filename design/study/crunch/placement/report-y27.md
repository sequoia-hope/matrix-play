# Placement attack: y27, first board with everything joined

Saved from crunch-placement's final message, because the harness blocked it from writing here. Lead's checks are marked. Not signed off. Earlier results are in `report.md`.

**Board:** `hw/round-pendant/c-placement-y27/round-pendant.kicad_pcb`. Router alone (y25): 0 signal / 1 plane. One 2.3 mm scripted track closed the plane open.

**Checked by the lead, zones refilled, on the `c-web2` copy with silk and models applied:** 235 LEDs, 861 vias, 0 unconnected. Errors: XIN length, 4 vias in the U3 ring rule (+3V3, SW1_5, SW1_8, SW2_6), 1 via in the L1 window (SW2_8). No silk, clearance, width or short errors. Ring one piece at 5.66 mm², vendor 1V1 one piece at 2.19 mm², GND, VSYS and 3V3 planes one piece each, 1V1 track 15.8 mm. Parity: 3 net-name conflicts on unused pins GPIO27-29. `pad_joints_fixed.py`: FAIL on U1.61 GND, 0.079 mm. `necks.py`: 456 of 1146 joints under 0.09 mm, 378 of them sole, 451 on LED pads, minimum 0.022 mm. Corner necks not fixed.

**What made the difference:** U1 and U2 moved 2.4 mm north with the map rebuilt; cathode vias through their pads; USB and crystal pairs uncrossed; real power net classes; via escapes laid first near the regulator; no new foreign vias inside U3's ring; finer cell and 3000 s.

**Reported as failing or unchecked, besides silk and text:**
- One F.Cu copper sliver, unexamined.
- `sync_check` fails on J1's missing LCSC, also on `c`.
- `nets_check` fails with 177 errors; 176 of them are also on `c`, and the new one is XIN.
- Driver pad copper down from about 26 to 16-17 mm²; the thermal estimate on y5 put this at 1-3 K, by hand model only.

**Rule relaxations, labelled:** U6 output neck at 0.15 mm; VSYS minimum down to 0.2 mm.

**Tool findings:** `pad_joints.py` tests back pads against F.Cu; corrected copy at `scripts/crunch/placement/pad_joints_fixed.py`. The router double-wires zone-joined nets.

**To reproduce, with `P=scripts/crunch/placement`:**
1. `CAPS3V3=1 RINGVIAS=1 PENDANT_MAP=$P/exp/x3-y1.csv $P/new_variant.sh NAME $P/exp/y22.json`
2. `powerclass.py`
3. `reserve_escapes.py DIR -1 -4.5 4.2 4`
4. `critpass.sh NAME 300 3000 "--cell 0.025"`
5. `finish.py`, `undangle.py`, `finish2.py`, `fix_open.py`, then the U6 neck rule and rule area
