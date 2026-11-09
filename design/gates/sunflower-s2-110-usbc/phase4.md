# Gate 4: Mechanical and Layout Brief — Sunflower `s2-110-usbc`

Status: **`awaiting_signoff`** (Gate 4 requires explicit user sign-off per [SKILL.md](../../../.claude/skills/pcb-design/SKILL.md) and [intent-and-brief.md](../../../.claude/skills/pcb-design/references/intent-and-brief.md)).

## Checklist ([intent-and-brief.md](../../../.claude/skills/pcb-design/references/intent-and-brief.md), Phase 4 Items 1–12)

| # | Item | Where in [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md) & [floorplan.png](../../renders/sunflower-s2-110-usbc/floorplan.png) | State |
|---|---|---|---|
| 1 | Board outline and size (`Ø38.000 mm`) | §1 (`0.250 mm` min copper-to-edge) | done |
| 2 | Mounting holes (`0`) & rim bezel notches | §2 (`J1`, `SW1/SW2`, and `Q2` 12-o'clock optical window) | done |
| 3 | Connector & rim-part placement (`J1`, `BT1`, `SW1`, `SW2`, `Q2`) | §3 + exact `pcbnew` `B.Fab` outlines in [floorplan.png](../../renders/sunflower-s2-110-usbc/floorplan.png) | awaiting user sign-off (`BT1` `4.04 mm` corridor & `SW1/2` `+0.40 mm` projection) |
| 4 | Assembly sides & reflow order | §4 (**`Pass 1 = B.Cu`, `Pass 2 = F.Cu ≤ 245 °C`** for `Q2` 1× reflow limit) | done |
| 5 | Layer count (`4L`) & stackup role | §5 (`In1.Cu` `GND` vs `In2.Cu` adjacent-plane note for `Rev S3C` vs `Rev S3D`) | awaiting user sign-off |
| 6 | Density philosophy (`0402`, no via in signal pads) | §6 | done |
| 7 | Block floorplan & signal/power flow | §7 (`U8` `29.1 mm` SE placement noted for `Rev S3C` vs `Rev S3D`) | awaiting user sign-off |
| 8 | Thermal management | §8 (`ADC4` firmware `GCC` cap keeping board `≤ 48–50 °C` / `≤ 45 °C` charging) | done |
| 9 | Art zone (`F.SilkS` `1,027`-segment Voronoi sunflower web) | §9 (`0` silk-over-pad; tented-via dimples noted) | awaiting user sign-off |
| 10 | Silkscreen policy (`designators = "none"`, `23` `B.SilkS` callouts) | §10 + [bringup-map-bottom.png](../../renders/sunflower-s2-110-usbc/bringup-map-bottom.png) | awaiting user sign-off |
| 11 | Keepouts, rule areas & rear `403535` LiPo spacer | §11 (`Kapton + ≥ 2.4 mm` rear foam/carrier spacer) | awaiting user sign-off |
| 12 | Test, debug & bring-up provisions (`14` test pads, `NT1`) | §12 + [bringup-s2-110-usbc.md](../../study/sunflower/bringup-s2-110-usbc.md) | done |

## Exact Mechanical Clearance Verification (`pcbnew` `B.Fab` + Pad Geometry, `2026-11-08`)

```text
BT1 @ (88.600, 89.800) rot=-110.0 deg vs SW2 @ (83.849, 93.800) rot=+69.0 deg:
  Minimum exact B.Fab polygon-to-polygon clearance (BT1 <-> SW2): 1.017 mm
  Minimum BT1 housing to SW2 SMD pad clearance:                   0.898 mm
  BT1 inward mouth normal (+20.0 deg) to C9 (0402):               3.020 mm
  BT1 inward mouth normal (+20.0 deg) to U3 NW corner / axis:     4.040 mm / 4.820 mm
```

## Independent Review (`2026-11-08`, fresh-context `agy` reviewer)

Reviewer inspected [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md), [intent-s2-110-usbc.md](../../study/sunflower/intent-s2-110-usbc.md), [floorplan.png](../../renders/sunflower-s2-110-usbc/floorplan.png), [rp2350.md](../../../.claude/skills/pcb-design/chips/rp2350.md), and connector/switch/sensor datasheets.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| `BLOCKER-1` | BLOCKER | Synthetic rectangle in initial `floorplan-s2-110-usbc.svg` swapped `(w, h)` on `BT1`, making `BT1` appear to collide (`0.027 mm`) with `SW2` | **Fixed & disproved on PCB ([decisions.md](../../decisions.md)):** Regenerated [floorplan-s2-110-usbc.svg](../../study/sunflower/floorplan-s2-110-usbc.svg) and [floorplan.png](../../renders/sunflower-s2-110-usbc/floorplan.png) directly from `pcbnew` `B.Fab` vertices; true `BT1 ↔ SW2` clearance is **`1.017 mm`** (`0.898 mm` to `SW2` pad) |
| `BLOCKER-2` | BLOCKER | `BT1` inward mouth (`+20°`) has `3.02 mm` to `C9` and `4.04–4.82 mm` to `U3` (not `~8 mm`), requiring upward-angled pre-mating of the `4.2 mm` `51021-0200` plug before battery install | Fixed false `~8 mm` claim in [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md) §3; put `Rev S3C` pre-mating acceptance vs `Rev S3D` `BT1` re-angling to user below |
| `BLOCKER-3` | BLOCKER | `U3` & `L1` sit on `B.Cu` (L4), so adjacent `0.21 mm` plane is `In2.Cu` (L3), whereas `plane GND` and `LX cutout L2` are on `In1.Cu` (`1.29 mm` away) | Documented in [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md) §5/§11, quantified in Phase 8 (`~2.3 mVpk` HF glitch), and held in Gates 5/6/7 pending user `Rev S3C` waiver vs `Rev S3D` layer swap |
| `MAJOR-1` | MAJOR | `SW1`/`SW2` physical plunger projects `+0.400 mm` nominally (`+0.200 mm` pressed; `0.00 to −0.20 mm` worst-case tolerance), not `+1.011 mm` courtyard | Corrected in [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md) §3 and listed for user sign-off |
| `MAJOR-2` | MAJOR | `Q2` 1× reflow limit (`xyc-pt19c-l1.pdf` p. 11) forbids reflowing `F.Cu` first | Fixed in [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md) §4: **`Pass 1 = B.Cu`, `Pass 2 = F.Cu` (`≤ 245 °C`)** |
| `MAJOR-3` | MAJOR | `BT1` is `3.20–3.40 mm` tall (not `2.70 mm`), and `Ø35 mm` `403535` overlaps both `J1` and `BT1` | Fixed in [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md) §3/§11.6: specified `0.05 mm` Kapton + `≥ 2.4 mm` rear foam/carrier spacer |
| `MAJOR-4` | MAJOR | Uncapped `1.26 W` thermal rise exceeds `SW1/SW2` `70 °C` and LiPo `45/60 °C` | Fixed in §8 via firmware `ADC4` `GCC` cap |
| `MAJOR-5` | MAJOR | `U8` (`XB9901A`) sits `29.1 mm` across disc at SE rim instead of beside `BT1` | Documented in §7 and held in Gate 6 pending user `Rev S3C` waiver vs `Rev S3D` |
| `MAJOR-6` | MAJOR | `U3.61` and `U2.41` have `1` in-pad + `1` perimeter `GND` via; `U5.17` has `2` non-POFV vias | Reconciled in §6 and held in Gate 7 pending user `Rev S3C` waiver vs `Rev S3D` |
| `MINOR-1..4` | MINOR | `Q2` optical window/baffle (`2.66 mm` from `D65`), `J1` `B.Cu` THR pin-in-paste requirement, Kapton over `13` bare test pads, `0.626 mm` rotated LED pad-to-edge | Updated across §1, §2, §3, §10, §11, and §12 |

## Decisions Required From User for Gate 4 Sign-Off

1. **Accept `Rev S3C` floorplan as-routed for `5–10` prototype boards OR authorize `Rev S3D` layout respin:**
   - **`BT1` inward mating (`4.04 mm` to `U3`, `3.02 mm` to `C9`):** Angle and pre-mate the `51021-0200` plug before applying Kapton + `≥ 2.4 mm` foam standoff + `403535` LiPo (`Rev S3C`), **or** shift/rotate `BT1` (`~−128°`) and co-locate `U8` beside `BT1` (`Rev S3D`).
   - **Inner-layer stackup role (`In1.Cu` vs `In2.Cu`):** Accept `In1.Cu` `GND` + `In1.Cu` `LX` cutout for bench prototype (`0` DRC, Phase 8 verified functional), **or** swap `In2.Cu` = `GND` + `LX` cutout adjacent to `B.Cu` (`Rev S3D`).
2. **`SW1`/`SW2` `+0.400 mm` nominal plunger projection:** Accept fingernail rim actuation (`0.00 to −0.20 mm` worst-case tolerance) on the un-scalloped `Ø38.0 mm` rim.
3. **Front `F.SilkS` Voronoi seed-web art (`1,027` segments):** Confirm keeping the clipped white Voronoi sunflower web on `F.SilkS` (or specify bare dark mask for future runs).
4. **PCBA order instruction:** Confirm instructing JLCPCB PCBA to reflow **`B.Cu` in Pass 1 and `F.Cu` (`Q2` + `110` LEDs) in Pass 2 (`≤ 245 °C`)** with **NO `F.Cu` wave/hand-soldering on `J1`'s 4 PTH shield slots** (`sunflower-B_Paste.gbp` omits paste on `J1`'s PTH slots and `F.Cu` LEDs sit `0.18–0.29 mm` away; tack outer `B.Cu` slot edges only on `Rev S3C`, or switch to full-SMT `TYPE-C-31-M-22` `C530612` / add `B.Paste` in `Rev S3D`).
