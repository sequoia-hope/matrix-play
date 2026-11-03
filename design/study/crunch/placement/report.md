# Placement attack: report

Saved from crunch-placement's final message, because the harness blocked it from writing this file. Numbers are the agent's unless marked as checked by the lead. Everything here is on 6 layers.

**Best board:** `hw/round-pendant/c-placement-x15b/route/s0.kicad_pcb`, 1200 s: 76 open / 69 plane / 66 errors / 942 vias, `pad_joints` pass. The unmodified board at 600 s scores 121 / 73 / 64 / 884.

**Checked by the lead:** the x15b board's zones still include five at 0.5 mm clearance, so its plane-open figures likely carry the known clearance bug. Compare its signal opens, not its plane opens, with other attacks.

| Trial (600 s) | Open |
|---|---:|
| Drivers 2.4 mm north, remapped (x3) | 118 |
| Cathode vias through U1/U2 pads (x10) | 105 |
| Both together (x12, three routes) | 74, 79, 81 |
| x12 plus real regulator (x15; x15b is its 1200 s run) | 89 |
| Real regulator only (x6) | 128 |
| Stub limit 2.4 mm (x1) | 152 |
| Flash and charger south (x4) | 136 |
| Fewer thermal vias (x7) | 125 |
| x12 plus 72 parts nudged (x14) | 87 |

- **Why it works:** LEDs over the drivers had 1.29 open ends each, against 0.24 far away. Cathode vias cut that to 0.39.
- **Cost:** driver pad copper falls from about 26 to 18 mm², thermally unchecked. No LED moved, and the map changed.
- **Faults in the starting point:** the LX plane cut is on In2 and should be next to U3 (In4 on 6 layers; the lead confirmed `zones_b` cuts In2 while `design/brief.md` says In4). The regulator zones and PGND vias are missing. Fixing both costs little.
- **Remaining:** about 30 opens are U3 control nets, including pin 50. x15's LX zone split, though not in x15b. In x15, 65 of 68 errors are power-net necks; x15b's weren't classified.
- **Failed or skipped:** the matrix-only bound (x9) is invalid: 90 fan-outs failed, cause unknown. The U3 flip wasn't tried.
- **Next:** route control nets first on x15.

**To reproduce:** `scripts/crunch/placement/new_variant.sh` with `exp/x15.json`, setting `PENDANT_MAP` to `exp/x3-y1.csv`.

The acceptable-layout list is `rp2350-acceptable.md` in this folder. It is written for the 6-layer stack: on 8 layers, U3's neighbouring layer is In6, not In4.
