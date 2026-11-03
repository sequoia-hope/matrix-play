# Task: tidy the back silkscreen of this PCB

Board: `hw/round-pendant/c-silk-gemini/round-pendant.kicad_pcb` (with its own `.kicad_pro` and `.kicad_dru`). A 38 mm round, 8-layer KiCad 9 board. All parts except the LEDs are on the back. Your folder is a private copy. You can do this: it is a dense board, but a good result exists.

Goal: every back-side reference designator is readable, unambiguous and tidy, sitting beside its own part, for major components first (U*, SW*, L1, Y1, Q1, J1, BT1, TP*), then as many passives as fit. Leave a passive's designator out rather than crowd it. Aligned, consistent, small text, as a careful human would place it.

Rules:
- JLC limits. Check them yourself, starting at https://jlcpcb.com/capabilities/Capabilities and https://jlcpcb.com/blog/character-design-specifications. Reports so far: standard 0.153 mm stroke and 1.0 mm height, 0.15 mm pad clearance; high-precision silkscreen 0.1 mm stroke and 0.8 mm height (blog only). Use the smallest text JLC allows and say which option it needs. Note the project's rules in the .kicad_pro may need matching.
- Don't change copper, zones, vias, part positions, the board outline or nets. Silk and footprint text only. Don't touch front silk: another person is doing that.
- Keep clear of exposed pads, holes and the board edge. Silk over tented vias is acceptable only where no clean spot exists; say how many. Keep pin 1 marks useful on chips.
- Read the reader's side correctly: back-side text must be mirrored as KiCad normally does for B.SilkS.

Deliver:
1. A re-runnable script `scripts/crunch/silk/back_silk.py BOARD.kicad_pcb OUT.kicad_pcb` using KiCad's `pcbnew` Python, so it can be applied to later routes of the same placement.
2. The result at `hw/round-pendant/c-silk-gemini/silk.kicad_pcb`, and rendered checks. `kicad-cli pcb render --side bottom`, then look at your own images, and `kicad-cli pcb drc` (copy the .kicad_pro and .kicad_dru to match the board's name, or DRC uses default rules). Report silk error counts before and after.
3. `design/study/crunch/silk/report.md`: JLC rules found with sources, text size used, designators kept and dropped, DRC counts, what you did not check.

Limits: write only in `hw/round-pendant/c-silk-gemini/`, `scripts/crunch/silk/` and `design/study/crunch/silk/`. No `rm -rf`, recursive or wildcard deletes: make a new folder instead. No commits or pushes. This is a shared machine: no long heavy jobs. Report exact numbers, including failures.
