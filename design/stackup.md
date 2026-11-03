# Stackup and rules

Sources: JLC capabilities page https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-02. 3313 prepreg Er 4.1, 6-layer via-in-pad filled and capped.

**Thickness estimate.** Layer thicknesses below are worked out to total 1.0 mm from a JLC-style 3313 stack on the user's 6-layer `pendant-nrf52820` (which is 1.6 mm). JLC's exact table for 1.0 mm wasn't reachable by script. Read it from the quote tool before fab. Nothing here depends on impedance control: USB is full speed over a very short run, QSPI is under 25 mm.

| Layer | Copper | Dielectric below | Role |
|---|---|---|---|
| F.Cu | 1 oz finished, 0.035 | 0.0994 prepreg | LED pads, R, G, B columns |
| In1 | 0.5 oz, 0.0152 | 0.2708 core | SW scan trees |
| In2 | 0.5 oz | 0.1088 prepreg | GND plane |
| In3 | 0.5 oz | 0.2708 core | CS jumps, bottom-side signal escape |
| In4 | 0.5 oz | 0.0994 prepreg | VSYS, +3V3 pours, GND |
| B.Cu | 1 oz | — | Parts, short signals, pours |

## Fab limits used (JLC, 6-layer)

| Rule | Value | Source |
|---|---|---|
| Track / clearance | 0.09 / 0.09 mm | Capability page; floor on the user's earlier board |
| Via | 0.25 / 0.15 mm standard; 0.20 / 0.10 mm in U3's 3V3 band only; annular 0.05 mm | Capability page; the smaller one needs board ≤ 1 mm and ENIG, both set |
| Via-in-pad | Filled and capped | Capability page, standard on 6 layers |
| Hole clearance, hole to hole | 0.2 mm | Capability page |
| Copper to edge | 0.2 mm | Capability page; check J1's west front leg, 0.32 mm from the edge: passes |
| Silk | 0.8 mm height, 0.15 width | Skill defaults |

## Net classes

| Class | Track | Clearance | Via | Why |
|---|---|---|---|---|
| SIGNAL, ANALOG | 0.1 | 0.09 | 0.25/0.15 | nets.csv; R21 needs 0.1/0.09 in the LED channels |
| POWER | 0.2 | 0.09 | 0.3/0.15 | Rails, with DRU minimums below, SW lines |
| CLOCK | 0.15 | 0.15 | 0.25/0.15 | Crystal: guard by spacing |
| SE_HS | 0.1 | 0.1 | 0.25/0.15 | QSPI |
| DIFF_HS | 0.15 | 0.15 | 0.25/0.15 | USB FS; pair 0.15/0.15, not impedance controlled |
| SWITCH | 0.4 | 0.12 | 0.3/0.15 | VREG_LX in its zone |

DRU minimums: VBUS 0.25; VSYS, VBAT, BAT_N 0.3; +3V3 0.2; SW lines 0.1. Length limits and "no vias" rows from nets.csv. Rule areas for L1 and U3's ring are drawn with the parts at phase 6.

Severities: silk overlap, silk over copper, track dangling, net conflict, duplicate, extra and missing footprint set to error. Library mismatch ignored for the board-local footprint copies.
