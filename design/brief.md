# Mechanical and layout brief: round-pendant

Phase 4. Drawing: `study/floorplan.svg`. Numbers: `../scripts/via_study.py`, `../scripts/floorplan.py`, `study/sites.json`. Outline board with J1, SW1, SW2, BT1 on the back: `../hw/round-pendant/a/round-pendant.kicad_pcb`.

## 1. Outline
Circle, 38.0 mm. Rim clearance from LED land corners ~1.0 mm.

## 2. Mounting
No holes. Spare rim sites allow a lanyard hole later. A housing isn't designed in this revision.

## 3. Connectors
| Part | Place | Facing | Note |
|---|---|---|---|
| J1 USB-C, HRO TYPE-C-31-M-12 | Bottom side, south edge, axis at x = −0.75 mm, origin y = +16 | Out | Shell front at +3.65: overhang 0.66 mm at the axis, 1.0–1.4 mm at the corners on the curve. West front-leg pad corner 0.32 mm from the edge; confirm JLC's edge rule in phase 5. Plug clearance: the housing needs a notch; the curved edge doesn't block a plug past the shell. Its 4 shell legs and 2 pegs pass through the board, displacing LEDs (section 11) |
| BT1 | Bottom side, near the south-east rim | — | Two 2 × 3 mm solder pads. Leads reach the cell behind |
| SW1, SW2 | Bottom side, at the rim at −28° (north-east) and −152° (north-west) in the drawing, actuators 0.4 mm past the edge | Out | SKRTLAE010's 0.9 mm NPTH pegs need 1.2 mm and can't fit a 0.75 mm channel, so they take rim sites: 2 lost, (15, −9), (−15, −9). Keep travel clear of the housing |

## 4. Assembly sides
Double-sided, by the request. LEDs top; everything else bottom. JLC reflows the LED side too, against the 255 °C limit noted in `parts/leds.md`.

## 5. Layers
Six, through vias, via-in-pad filled and capped, by the user's decision. Tentative use, finalised in phase 5:
| Layer | Use |
|---|---|
| F.Cu | LED pads; R, G, B cathode columns (plan R21) |
| In1 | SW scan rows |
| In2 | GND plane |
| In3 | CS jumps between columns; bottom-side signal escape |
| In4 | VSYS and +3V3 pours, with GND where free |
| B.Cu | Parts; short signals; pours |

JLC limits read 2026-11-02: through via 0.15/0.25 mm standard; 0.10/0.20 mm for boards ≤ 1 mm with ENIG. Filled and plated-over vias allowed in pads. Thickness 1.0 mm and ENIG make the 0.10/0.20 option available for tight places.

## 6. Density
Compact. 0402 passives; 0603 only for bulk. Designators where they fit, on the back only.

## 7. Floorplan (rough regions; see drawing)
USB-C south, charger and power just inside it, drivers east and west on the widest part of the disc, RP2350 north of centre, turned so its USB, QSPI and regulator side faces south: USB stays short, flash sits just south of it, L1 near the board centre. Crystal on U3's north edge, accelerometer north-east. Power flows north from J1; I2C runs across from U3 to both drivers.

## 8. Thermal
Drivers: exposed pad to In2 through vias. Lumissil asks 16–25; with cut-outs (section 10) use what fits, then check in phase 8. Spread east and west, so their heat doesn't stack. Charger: EP vias per TI's land pattern less the centre one.

## 9. Art, silk
No art zone. Top: bare display, no silk. Back: board name, rev, repo URL once it exists, BT1 polarity, USB, buttons.

## 10. Vias under the chips (intent risk 1)
Anode vias sit on a 2 mm grid. Each may move off pad 3 on a stub of up to 0.5 mm, in the five directions LED pads leave open: −x, +y, −x+y, −x−y, +x+y. Rotating an LED opens others (R3 allows it where needed). JLC via 0.25/0.15 mm, clearance 0.09 mm.

| Chip | Alignment | On signal pads | In exposed pad | In 1V1 ring | In 3V3 band |
|---|---|---|---|---|---|
| U1, U2 IS31FL3741A | Centre on a via | 0 | 9 | — | — |
| U3 RP2350A | Centre on a via, with stubs | 0 | 1 | **0** | 8 |

**Drivers.** 5.4 mm pad with 9 holes ~0.7 mm each at 2 mm pitch, leaving a ≥ 0.2 mm mask dam. Thermal vias and paste go between.

**RP2350: a smaller deviation from `chips/rp2350.md`.** The 1V1 ring and its four spokes stay whole. The 8 vias that would hit the ring step outward into the ±2.8 mm 3V3 band, which stays connected around them, leaving foreign nets inside the pad ring: 1 cut-out in the exposed pad, 8 in the band. These are SW scan lines, pulsing at up to 494 mA, near 3V3 only; the switcher corner keeps its reference zones. U3's own vias take what room remains. Checked at phase 6 on a real layout against the reference; if SW-to-core coupling shows up at bring-up, those LEDs can be left blank in firmware.

**L1.** "No other copper under the inductor." L1 is 2.0 × 1.6 mm with 2 mm via pitch: vias in its footprint step outward, leaving a window on B.Cu, and In4 is cut under LX.

**Other parts.** Flash: offset so 2 vias land in its floating EP, filled and capped (§10.3 of its datasheet asks not to leave exposed vias). Charger: centre on a via, 1 EP cut-out, drop TI's centre thermal via. BT1: 1–2 foreign vias in each pad, each masked over, or the pads move between grid lines at phase 6. Accelerometer: corner offset, marginal, checked at phase 6. 0402s fit anywhere. USB-C signal row: 4 anode vias of LEDs (−1, 11), (1, 11), (−3, 11), (3, 11) move off it on −x−y stubs.

**Keepouts.** B.Cu and In4 under L1 and LX; J1 shell footprint on B.Cu; button actuator travel; foreign-net rule areas per `chips/rp2350.md`, adjusted for the above.

## 11. USB-C and LED sites (intent risk 5)
All 16-pin parts read have 4 legs at x = ±4.32 mm, wider than the LED channels. At the best offset, 5 sites are lost: (−5, 13), (−5, 17), (−3, 13), (3, 13), (3, 17) mm. Three are ~13.5 mm from the centre: **dark spots in the south of the display, which the user must accept.** The other 2, and the 2 button sites, are nearer the rim. Count stays 234 from spare rim sites (15 left unused).

## 12. Matrix map
Each driver takes half the disc, split on x ≈ −0.75: 9 LED columns each, up to 18 tall. Each cell (SW, triplet) must exist exactly once.
- **Triplets, 13 per driver, 9 LEDs each:** runs along a column on F.Cu, jumping between columns on In3 where a column doesn't hold 9.
- **SW lines, 9 per driver, 13 LEDs each:** not plain row bands. A band two rows tall would put two LEDs of one column on one SW, so it can't meet "exactly once". Each SW takes 2 LEDs from each of the 3 tallest columns and 1 from the rest: 9 nested, non-crossing trees on In1.
- **Solver at phase 6:** assignment with In1 planarity, F.Cu channel capacity (2 tracks per channel), and shortest jumps. If it can't close on In1 alone, In3 shares the SW load.
- **Fan-in:** ~48 matrix vias per driver. A 0.25 mm via leaves room for 1 track per channel at 0.10/0.09, so these vias spread over columns x = ±5 to ±9 either side of each driver, with arrivals on In1 and In3. Counted again at phase 6.

Firmware reads the map from a generated table.

## 13. Test and debug
RUN, GND, SWCLK, SWDIO, VSYS, +3V3, VBAT, 1V1 test pads. No isolation jumpers: no room, single prototype run.
