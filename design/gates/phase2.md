# Gate 2: schematic

Status: **passed**.

## Checks

`scripts/check_sch.py` (kicad-cli 9.0.8 ERC, then the netlist):
```
{}                                                 (0 ERC violations, severity all)
328 components 170 nets {'B': 1, 'C': 42, 'J': 1, 'Q': 1, 'R': 28, 'T': 8, 'U': 9, 'L': 1, 'S': 2, 'Y': 1, 'D': 234}
matrix ok: 18 SW nets of 13 LEDs + driver, 78 CS nets of 9 LEDs + driver
```

`schematic_style_check.py hw/round-pendant/a`: 2 errors, both the `grid` rule on matrix1 and matrix2, waived in `decisions.md`: a matrix drawn as a matrix. 9 warnings: 9 stacked-pin decoupler notes, placement relies on the Decouples field. FAIL exit stands because of the waived rule.

Fields: all parts have value, footprint, MPN, LCSC; test pads and BT1 have no LCSC, in_bom no.

## Review
Fable reviewers, fresh context, rendered sheets and netlist. Two rounds, 2026-11-02.

Round 1, correctness: **no blockers.** All pin maps verified against datasheets (U1/U2 all 60 pins + EP, U5, U6, U8, U9, Q1, RP2350, flash). LED R/G/B to CS triplets match Figure 2. Q1 wiring and off state verified. All passive values match the audits.

| Round | Sev | Finding | Resolution |
|---|---|---|---|
| 1 | MAJOR | Charger ISET, ILIM wires through R3, R4 | Fixed |
| 1 | MAJOR | Q1 unreadable as one box | Fixed: two units |
| 1 | MAJOR | Global labels outside the frame on matrix sheets | Fixed |
| 1 | MINOR | Matrix row labels, notes, TP text, comments overflow | Fixed |
| 1 | MINOR | CC wires cross D± | Accepted: inherent to the pin order, as on easy2350 |
| 1 | NOTE | U8 footprint pads 4, 5 swapped; both BAT_N | Accepted: harmless, user's footprint |
| 2 | MAJOR | Crystal, flash cluster text collisions | Fixed: flash and crystal moved left |
| 2 | MAJOR | TS wire through a GND label | Fixed: symbol gap |
| 2 | MINOR | Accelerometer labels, U3 ref, box edges, R32, ISET/ADDR crossing | Fixed |

Reviewed in round 2 as checked, and re-checked by ERC and netlist after fixes; final text fixes were not reviewed a third time. A short from one fix, R2's wire on USB_DP_C, was caught by ERC and corrected.

Skill version: `VENDORED_FROM`.
