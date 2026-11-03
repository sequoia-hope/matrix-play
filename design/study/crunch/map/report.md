# LED map and turns: report

Saved from crunch-map's final message, because the harness blocked it from writing this file. Numbers are the agent's and haven't been rechecked.

**Conclusion:** rewiring can't be shown to get substantially further. Cathode vias through the driver pads did the most, and ribbon turns may help a little. No board from this attack is clean, and y17's map stays. Seed noise was never measured, so one-run differences under about 10 opens prove little. A cheap predictor wasn't reached: land-tree length didn't track opens, but the sample was too small to correlate properly.

| Trial (base, limit) | Change | Open / plane / errors / vias |
|---|---|---|
| c-map-20 (6L v3, 600 s) | Rebuilt fan map | 105 / 2 / 86 / 957 |
| c-map-22 (same) | Zone map | 104 / 4 / 63 / 919 |
| c-layers-v3-8a (8L, 1200 s) | Baseline | 56 / 9 / 55 / 961 |
| c-map-30 | Zone map | 51 / 8 / 70 / 922 |
| c-map-31 | Zone + ribbon turns | 39 / 13 / 81 / 949 |
| c-map-34 | Zone + 12 EP vias + F.Cu links | 38 / 14 / 89 / 918 |
| c-map-36 | 31 + 15 EP vias + links | 39 / 15 / 93 / 923 |
| c-placement-y5 (cell 0.025) | y5 | 22 / 5 / 76 / 865 |
| c-map-y2 | y5 + ribbon, 210/234 turns, 106 stubs | 18 / 8 / 178 / 845 |
| c-map-y3 | y5 + ribbon, 145/234 turns, 58 stubs | 32 / 4 / 72 / 822 |

- **Best open count:** c-map-y2 (`pad_joints` pass), but 173 errors are track_width; the doubling is unexplained.
- **Hot spot:** on the 8-layer baseline, 22 of 46 cathode lands over the U1 and U2 exposed pads stayed open, against 0 of 295 away from the chips.
- **Gemini:** its ribbon land order is mirrored; the real order is 1, 2, 4.
- **y17:** don't remap. It's complete, and any map or turn change means rerouting. y3's gains over y5 are 5% fewer vias and 7% less CS copper, at 10 more opens; SW copper stayed flat (1134 vs 1129 mm). y17 has 898 vias and 1101 mm of SW. The annealed map's SW land tree is 17% shorter (812 vs 976 mm), but its CS tree is 9% longer and it's untested here.
- **Scoring caveat:** `new_errors` subtracts pre-route errors, hiding `items_not_allowed` (via SW2_8 at 1.90, 1.62) and `length_out_of_range` on the final board.

Scripts are in `scripts/crunch/map/`.
