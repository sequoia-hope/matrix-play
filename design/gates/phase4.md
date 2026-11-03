# Gate 4: mechanical and layout brief

Status: **passed**. User sign-off 2026-11-02: accepted the 3 dark spots, chose vias in the 3V3 band, signed off the rest.

Checklist from `references/intent-and-brief.md`: outline, mounting, connectors, sides, layers, density, floorplan, thermal, art, silk, keepouts, test: `brief.md` sections 1–13. Outline board saved. Drawing: `study/floorplan.svg`.

Evidence, `scripts/floorplan.py`:
```
buttons {'SW1': -28, 'SW2': -152} sites lost to buttons [(-15, -9), (15, -9)] anode vias on USB SMT row [(-1.4, 11.4), (0.6, 11.4), (-3.4, 11.4), (2.6, 11.4)]
sites 256, lost to USB 5 at [(-5, 13), (-5, 17), (-3, 13), (3, 13), (3, 17)], chosen 234, spare left 15, radius of chosen corner 17.99, vias under chips {'U3': 9, 'U1': 9, 'U2': 9}
```
RP2350 recomputed with the 5 open stub directions: centre on via, 1 EP, 0 ring, 8 band, 16 outside; offset (1, 1), 4 EP, 0 ring, 9 band, 3 outside.

## Review (Fable, fresh context, 2026-11-02)

| Sev | Finding | Resolution |
|---|---|---|
| BLOCKER | Matrix map infeasible: row bands put two LEDs of a column on one SW | Fixed: §12, nested SW trees, solver constraints |
| MAJOR | RP2350 ring cut to 8 segments, 4 unspoked; counts wrong | Fixed: §10, ring whole. Reviewer's (1, 1) offset beaten by centring with stubs; decisions.md |
| MAJOR | USB-C SMT pads missing from via model | Fixed: 4 vias stepped off, §10; drawn |
| MAJOR | Stub model too permissive | Fixed: 5 directions, §10 |
| MAJOR | No fan-in count | Added §12; recount at phase 6 |
| MAJOR | No outline board; no keepouts; no USB mating clearance | Fixed: board saved, §10, §3 |
| MINOR | Button pegs can't fall in channels | Fixed: rim sites, §3 |
| MINOR | USB front at +3.65; corner overhang; leg edge 0.32 mm | Fixed: §3; edge rule in phase 5 |
| MINOR | Charger, accelerometer, BT1 unstudied | §10, checked at phase 6 |
| MINOR | Mask dam: cut-outs 0.7 mm | Fixed: §10 |
| NOTE | Via-in-pad slide unnecessary with 0.25 mm via | Noted |
| NOTE | LED pad 3 corner must be verified on the footprint | Check at phase 6 and CPL |
| NOTE | Three dark spots must be explicitly accepted | Put to the user |

Fixes not re-reviewed yet; placement gate reviews them on a real layout.
