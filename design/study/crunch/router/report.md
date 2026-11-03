# Router attack: report

Saved from crunch-router's final message, because the harness blocked it from writing this file. Numbers are the agent's and haven't been rechecked. Single runs, 420 s unless noted, as signal open / plane / errors / vias. Run rows are in `runs8.tsv` and `adopt.tsv`; the full diagnosis is `diagnosis.md`.

**Blockage is local, not a layer shortage.** No cut was counted.

| Signal opens | c-layers-v3-8a | y5 |
|---|---:|---:|
| chip fan-out | 12 | 8 |
| pad wall | 23 | 7 |
| via wall | 9 | 3 |
| LED pad | 2 | 2 |
| track wall (the only possible layer shortage) | 6 | 1 |
| free path | 4 | 1 |

On y5, inner layers are 57-62% free but only 6.2% of the disc has a legal via site. 19 of 22 opens need at least one illegal via.

**Sweep (8 layers):** default 79/3/50/933. `--cell 0.025` 49/3/61/874, the only real gain. `--cell 0.04` 72. Via cost, negotiation, `--plane-via-reach 0.6` and `--prefanout-mode same` 76-82. Ultraroute main e1c6992 (6 layers): same counts as the pin.

**Adopt on y5 (1200 s):** 22/5/76/865 became 18/7/69/853.

**Single thread:** `ps` showed 100% CPU, nlwp 1, on 4-core bookings. Thread count itself wasn't varied.

**y17 is not clean yet:**
- 5 dangling tracks.
- `pad_joints` FAIL: U1.53 at 0.069 mm, U2.28 at 0.022 mm.
- `necks.py` finds 462 of 1123 joints under 0.09 mm, 393 of them the only path to the pad, 459 on LED pads. 202 are 0.085-0.09 mm, 210 are 0.075-0.085, 50 are under 0.075. Not checked against a second tool, and whether a corner neck is a fab defect is a judgement for the owner.

**Repros for the tools:**
1. Power widths: c-layers-v3-8a has 51 `track_width` errors over 60.7 mm; router `neck:` lines cover 18.9 mm.
2. `pad_joints` misses corner necks: `hw/round-pendant/b/route/trials/t5`, D134.1, 442 router lines but PASS.
3. Zones: y5 lists +1V1 'DVDD finger 39' / 'FB finger' open. Not confirmed as a router bug.

**Not done:** 1-2 hour runs and open-against-time, two-pass, `--regions`, `failview` or any picture.
