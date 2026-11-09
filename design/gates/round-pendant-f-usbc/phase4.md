# Gate 4: mechanical and layout brief (`round-pendant-f-usbc`)

Status: **awaiting_signoff**
Parent gates cited for unchanged requirements & parts: [phase0.md](../phase0.md), [phase1.md](../phase1.md), [phase2.md](../phase2.md), [phase3.md](../phase3.md), [phase4.md](../phase4.md).
Variant brief: [design/brief-f-usbc.md](../../brief-f-usbc.md) (delta against [design/brief.md](../../brief.md) and [design/intent.md](../../intent.md)).

---

## Checklist (`references/intent-and-brief.md` §Phase 4)

- [x] **1. Board outline and size:** Unchanged `Ø38.000 mm` circle (`center = (100.000, 100.000) mm`, `radius = 19.000 mm`; [brief-f-usbc.md](../../brief-f-usbc.md) §1). Closest `J1` `B.Cu` SMD copper pad corner (East front `S1` outer corner at `(114.746, 111.271) mm`) sits at `r = 18.560 mm` unrounded (`~18.47 mm` rounded with `0.216 mm` fillet), giving **`0.440–0.530 mm`** edge clearance (`> 2.2×` the `0.200 mm` DRC rule).
- [x] **2. Mounting holes & bezel counterbore geometry:** `0` mounting holes (unchanged wearable pendant form factor; [brief-f-usbc.md](../../brief-f-usbc.md) §2). Two new `Ø0.650 mm` (`r = 0.325 mm`) unplated locating holes (`NPTH`) for `J1` (`TYPE-C-31-M-22`) plus the four inherited `Ø0.700 mm` `NPTH` locating holes for `SW1` and `SW2` (`6` total `NPTH` drills). Note East shell corner (`r = 19.616 mm`) overhangs by `+0.616 mm` (requiring a port cutout even in thin walls `≤ 0.65 mm`), and any future perimeter bezel wall `> 0.65 mm` thick must counterbore a `12.6 × 6.8 mm` USB-C overmold pocket inward along `23.95°` E of S down to **`u ≤ 19.0–19.4 mm`** (matching the `Ø38.000 mm` PCB rim and clearing a worst-case `u = 19.466–19.666 mm` plug overmold).
- [x] **3. Connector placement:** `J1` swapped from `round_pendant:USB_Pads` (`(100.000, 116.500, 0°)` on Variant F) to Korean Hroparts Elec **`TYPE-C-31-M-22` (`C530612`)** on `B.Cu` at **`(107.787, 110.926) mm`, `KiCad rot = -156.05°` (`203.95°`)**, facing outward **SSE (`23.95°` east of South = `156.05°` CW from North)** with an **`8.35°` non-radial skew** relative to the radial normal (`32.30°` E of S) at mouth midpoint `(109.865, 115.605) mm` (`r = 18.462 mm`, `-0.538 mm` inside `Edge.Cuts`). Asymmetric shell lip: East mouth corner `(113.951, 113.791) mm` overhangs at **`r = 19.616 mm` (`+0.616 mm`)**, while West mouth corner `(105.780, 117.420) mm` sits at **`r = 18.354 mm` (`-0.646 mm` inside `Edge.Cuts`)**; a mated USB-C plug overmold stops at `u = 20.066 mm` (**`+1.066 mm` nominal / `+0.666 mm` worst-case** outside `Ø38.0 mm`; [brief-f-usbc.md](../../brief-f-usbc.md) §3). `BT1` (`BatteryPads`, `2× 1.60 × 2.40 mm`) shifts into the vacated 6-o'clock South pocket at `(100.000, 117.100, 180°)`.
- [x] **4. Assembly sides:** Double-sided SMT (`0` PTH joints; `Pass 1 = F.Cu ≤ 250 °C` for `235× XL-1010RGB-YG` + `Q2` `ALS-PT19`, `Pass 2 = B.Cu ≤ 250 °C` for all ICs, passives, `SW1/SW2`, and `J1`; [brief-f-usbc.md](../../brief-f-usbc.md) §4).
- [x] **5. Layer count:** `8` layers (`JLC08101H-1080`, [stackup.md](../../stackup.md)), `1.0 mm` finished thickness (`0.9968 mm` nominal), `ENIG`, epoxy-filled & capped POFV via-in-pad (unchanged from Variant F; [brief-f-usbc.md](../../brief-f-usbc.md) §5).
- [x] **6. Density philosophy:** Unchanged `0402` passives, `0603` bulk MLCCs, `0.50 mm` WLCSP-36 LED drivers, `0.09/0.09 mm` trace/space, `0.25/0.15 mm` standard vias (`3× 0.20/0.10 mm` vias inside `U3` `+3V3` band; [brief-f-usbc.md](../../brief-f-usbc.md) §6).
- [x] **7. Block floorplan:** Northern, central, eastern, and western blocks (`U3` RP2350 + `147` locked decoupling tracks, `U4`, `Y1`, `L1`, `U9`, `U6`, `U5`, `U1/U2/U10/U11/U12`, `SW1/SW2`, and all `235` front LEDs + `Q2`) are **100% unchanged** from Variant F. Only `J1` and `8` southern `B.Cu` parts (`BT1, U7, U8, C1, C6, R5, R8, TP3`) move inside the southern I/O sector ([brief-f-usbc.md](../../brief-f-usbc.md) §7).
- [x] **8. Thermal:** Whole-board `Ø38.0 mm` disc `θ_BA ≈ 32.4 °C/W` free-air / `49.5 °C/W` worn -> **`≤ 0.51 W` continuous wearable ceiling** (`~100 mA` total LED avg, `< 50 °C` wear; `1.26 W` `300 mA` for `≤ 15 s` bursts only), with `BQ24073` `297 mA` linear charger into unbroken `847.497 mm²` `In2.Cu GND` plane, FW LED blanking on `~CHG == 0`, and closed-loop `ADC4` foldback (`42 °C` charge / `47 °C` wear; [brief-f-usbc.md](../../brief-f-usbc.md) §8).
- [x] **9. Art zone:** Inherited `F.SilkS` Voronoi sunflower seed web, surgically clipped outside centerline `r = 0.600 mm` around `J1`'s two `Ø0.65 mm` (`r = 0.325 mm`) NPTH holes (`0.199 mm` silk-stroke-to-hole-edge margin), `< 0.055 mm` micro-stubs pruned (`min = 0.0655 mm`), and `(subtractmaskfromsilk yes)` enabled ([brief-f-usbc.md](../../brief-f-usbc.md) §9).
- [x] **10. Silkscreen policy:** Bare `F.SilkS` display face (Voronoi web + `Q2` `OD = 0.24 mm` [`0.12 mm` stroke] pin-1 dot inherited from Variant F); selective `B.SilkS` strictly at **`0°` and `270°` (`90° CCW`) draw rotations** (`0` untented `[silk-over-via]` — `6` tented + POFV-capped flat VIPPO crossings only — `0` `[under-part]`, `9` unambiguous shown designators `TP2, TP4, TP5, TP8, SW1, SW2, U4, Q1, Y1`, `'rev FU'` + `'2026-11'` identity, `13/13` `B.Cu` `OD = 0.30 mm` pin-1 dots outside courtyards/3D bodies, `'5V'`/`'+'`/`'-'`/`'USER'`/`'BOOT'` labels with `0%` 3D occlusion) + collision-free `342/342` `4:1` A4 assembly drawings ([brief-f-usbc.md](../../brief-f-usbc.md) §10).
- [x] **11. Keepouts & rear LiPo stackup:** Inherited `RP2350` `+1V1` ring and `L1`/`VREG_LX` rule areas preserved intact (`240` fixed footprints + `Edge.Cuts` + rule areas locked); `J1` `3.16–3.26 mm` shell height accommodated by `0.05 mm` Kapton tape + `3.3–3.5 mm` foam standoff under the `35 mm` round × `4.0 mm` `403535` LiPo ([intent.md](../../intent.md) R16; [brief-f-usbc.md](../../brief-f-usbc.md) §11).
- [x] **12. Test and debug:** All `8` `Ø1.0 mm` `B.Cu` test pads (`TP1..TP8`) preserved and accessible (`TP3 VBAT` relocated to `(104.000, 117.500)`); full bench procedure in [design/bringup-f-usbc.md](../../bringup-f-usbc.md).
- [ ] **User sign-off on Phase 4 mechanical & connector brief** (see §3 below).

---

## 1. Feasibility Study & Mechanical Verification Output

### Why SSE (`23.95°` East of South, `8.35°` Non-Radial Skew) Instead of Due South (`0°`)
At due South `(100.0, 113.5, 180°)`, `TYPE-C-31-M-22`'s two `5.78 mm`-spaced `Ø0.65 mm` (`r = 0.325 mm`) NPTH locating holes collide with Variant F's fixed golden-angle LED pads (`< 0.08 mm` clearance). Sweeping `(x, y, θ)` along the southern rim found an exact zero-LED-move window at **`(107.787, 110.926) mm`, `KiCad rot = -156.05°` (`203.95°`)** (`23.95°` E of S, an `8.35°` non-radial skew from the `32.30°` radial normal at mouth center `(109.865, 115.605) mm`):
- **`NPTH #1 (109.953, 108.684) mm`** lands inside the `{D234, D235, D231, D226}` inter-LED gap with **`0.220 mm`** hole-edge-to-pad-edge clearance (`D234.4`), **`0.304 mm`** on `In3.Cu` (`CS5_16`), and **`≥ 0.201 mm`** across all 8 copper layers.
- **`NPTH #2 (104.671, 111.030) mm`** lands inside the `{D76, D66, D74, D64}` inter-LED gap with **`0.220 mm`** hole-edge-to-pad-edge clearance (`D74.3`), **`0.214 mm`** to nearest `F.Cu` track (`CS2_12`), and **`≥ 0.201 mm`** across all inner/bottom layers.
- **Local rip-up bounding box:** Primary southern crescent `X ∈ [91.3, 114.9] mm, Y ∈ [105.0, 118.8] mm` (`~195 mm²`, `17%` of the `1,134 mm²` disc, with minor route adjustments reaching `Y = 93.29 mm`; **`85.6%`** [`5,261 / 6,144`] of Variant F's copper items preserved verbatim).

### Verbatim `compare_with_f.py` Footprint & NPTH Audit Output
```text
=== 1. FOOTPRINT PARITY ===
  Front parts unchanged: 236/236 (235 LEDs + Q2, max delta 0.0000 mm / 0.00 deg)
  Back parts moved/swapped: 9
    BT1 : (109.800, 112.900, 180.00 deg) -> (100.000, 117.100, 180.00 deg)
    C1  : (105.000, 110.000, 180.00 deg) -> (102.500, 108.800, 180.00 deg)
    C6  : (107.200, 110.600, 180.00 deg) -> ( 94.500, 116.600, 180.00 deg)
    J1  : (100.000, 116.500,   0.00 deg) -> (107.787, 110.926, -156.05 deg)
    R5  : (105.000, 108.950, 180.00 deg) -> (107.500, 106.400,  90.00 deg)
    R8  : (106.100, 114.600, 180.00 deg) -> ( 99.700, 115.000, 180.00 deg)
    TP3 : (108.113, 108.950, 180.00 deg) -> (104.000, 117.500, 180.00 deg)
    U7  : (102.300, 109.400, 180.00 deg) -> (100.100, 112.400, 113.95 deg)
    U8  : (106.100, 112.600, 180.00 deg) -> ( 96.400, 116.400, -90.00 deg)

=== 5. J1 NPTH 8-LAYER CLEARANCE AUDIT ===
  NPTH #1: center=(109.953, 108.684) mm, drill=0.65 mm (r=0.325 mm)
    F.Cu  : min clearance = 0.220 mm  -> Pad D234.4 (/Driver 5 and matrix/CS5_16)
    B.Cu  : min clearance = 0.247 mm  -> Pad J1.A1B12 (GND)
    In1.Cu: min clearance = 0.311 mm  -> Via (/Driver 5 and matrix/CS5_16) @(109.192,108.714) [cu]
    In2.Cu: min clearance = 0.201 mm  -> Zone 'plane GND' (GND)
    In3.Cu: min clearance = 0.304 mm  -> Track (/Driver 5 and matrix/CS5_16)
    In4.Cu: min clearance = 0.264 mm  -> Track (/Driver 5 and matrix/CS5_14)
    In5.Cu: min clearance = 0.201 mm  -> Zone 'plane VSYS' (VSYS)
    In6.Cu: min clearance = 0.311 mm  -> Via (/Driver 5 and matrix/CS5_16) @(109.192,108.714) [cu]
  NPTH #2: center=(104.671, 111.030) mm, drill=0.65 mm (r=0.325 mm)
    F.Cu  : min clearance = 0.214 mm  -> Track (/Driver 2 and matrix/CS2_12) [nearest F.Cu LED pad D74.3 = 0.220 mm]
    B.Cu  : min clearance = 0.247 mm  -> Pad J1.B1A12 (GND)
    In1.Cu: min clearance = 0.293 mm  -> Via (/Driver 2 and matrix/SW2_3) @(104.892,111.739) [cu]
    In2.Cu: min clearance = 0.201 mm  -> Zone 'plane GND' (GND)
    In3.Cu: min clearance = 0.258 mm  -> Track (/Driver 2 and matrix/CS2_7)
    In4.Cu: min clearance = 0.293 mm  -> Via (/Driver 2 and matrix/SW2_3) @(104.892,111.739) [cu]
    In5.Cu: min clearance = 0.201 mm  -> Zone 'plane VSYS' (VSYS)
    In6.Cu: min clearance = 0.211 mm  -> Track (/Power/CC2)
```

### Datasheet vs Audit Verification (`type-c-31-m-22.pdf` p. 1 vs `parallelogram-io.md` §1)
1. **Peg diameter & length on `1.0 mm` PCB:** Datasheet p. 1 (`Front View` & `SECTION A-A`) specifies **`2-Ø0.50 mm` pegs** (`5.78 mm` span, matching [parallelogram-io.md](../../parts/parallelogram-io.md) §1 and STEP) of **`0.70 ± 0.05 mm` length** (`0.65–0.75 mm`), terminating **`0.30 mm` nominal (`0.15 mm` worst-case min board / max peg) below `F.Cu`** on our `1.00 mm ± 10%` PCB (guaranteed zero front protrusion).
2. **4-SMD-pad shell hold-down (`2.30 × 1.80 mm` each = `16.56 mm²` `B.Cu` area) & signal-row land note:** Pure axial mating shear capacity (`~330–500 N`) is `> 16×` the `5–20 N` rated insertion/extraction force, while out-of-plane prying is foil-peel-limited (`~35–55 N` / `~0.15–0.22 N·m`). Through-hole `TYPE-C-31-M-12` cannot be used because its `1.28 mm` PTH legs would protrude `0.28 mm` through the `1.0 mm` front LED array and destroy front LED sites. As logged in [design/decisions.md](../../decisions.md) (`2026-11-08`), `S1` retains `parallelogram`'s verified `2.30 × 1.80 mm` pads (`92%` of datasheet `2.50 × 1.80 mm`, `+0.27 mm` heel/toe fillet beyond the `1.48 mm` gull-wing foot) because widening `S1` to `2.50 × 1.80 mm` reduces `hole_clearance` to `6` fixed front-LED escape vias (`CS5_17, CS5_16, SW2_3, CS2_18, SW2_6, CS2_10`) to `0.105–0.138 mm` (`< 0.200 mm` DRC rule); `J1`'s 12 rear signal pads sit at `y_rel = +2.300 mm` (`1.14 mm` long vs `parallelogram-io.md`'s `y = 2.240 mm`, `1.15 mm` long), a benign `+0.055–0.060 mm` outboard shift over `0.40 mm`-protruding tails that widens `B.Cu` NPTH clearance to `0.247 mm`.

---

## 2. Renders Inspected
- [top.png](../../renders/round-pendant-f-usbc/top.png), [bottom.png](../../renders/round-pendant-f-usbc/bottom.png)
- [3d-top.png](../../renders/round-pendant-f-usbc/3d-top.png), [3d-bottom.png](../../renders/round-pendant-f-usbc/3d-bottom.png)
- [npth-gerber-zoom.png](../../renders/round-pendant-f-usbc/npth-gerber-zoom.png)

---

## 3. Decisions Requiring User Sign-Off (Gate 4)
1. **SSE Connector Angle (`23.95°` E of S, `8.35°` Non-Radial Skew) & Two Front `Ø0.65 mm` NPTH Apertures:** Approve placing `J1` at `(107.787, 110.926, -156.05°)` so **zero** front LEDs move, accepting the `23.95°` SSE cable angle (asymmetric `+0.616 mm` East / `-0.646 mm` West shell lip, `+1.066 mm` bare-board USB-C overmold clearance; any future bezel wall `> 0.65 mm` counterbored `12.6 × 6.8 mm` along `23.95°` E of S) and two tiny `Ø0.65 mm` unplated apertures in the dark front mask web (`0.70 mm` pegs recessed `0.30 mm` below `F.Cu`).
2. **SMD-Only Shell Hold-Down (`TYPE-C-31-M-22`, `4× 2.30 × 1.80 mm` `S1` Pads):** Accept the 4-SMD-pad gull-wing shell (`16.56 mm²` `B.Cu` solder area; straight axial plug insertion/removal on bare boards, or rear housing capture / corner epoxy if cased) instead of through-hole shell stakes (`M-12` would pierce the `1.0 mm` front LED face).
3. **Rear `35 mm` `403535` LiPo Standoff (`3.3–3.5 mm`):** Confirm `0.05 mm` Kapton tape over `TP1..TP8`/`BT1` + `3.3–3.5 mm` foam ring/spacer matching `J1`'s `3.16–3.26 mm` rear shell height.

---

## 4. Independent Fresh-Context Review History (`agy` `gemini-4-argon-high`)

### Round 1 Review Summary & Dispositions
- **`BLOCKER-1` (Mouth/bezel trig, `8.35°` non-radial skew, single-corner `+0.616 mm` overhang, `0.440–0.530 mm` `S1` corner clearance):** **FIXED** in [brief-f-usbc.md](../../brief-f-usbc.md) (§1–§3) and this gate file (Checklist #1–#3, §1, §3) with exact mouth center `(109.865, 115.605) mm` (`r = 18.462 mm`), East `(113.951, 113.791)` (`r = 19.616 mm`, `+0.616 mm`) / West `(105.780, 117.420)` (`r = 18.354 mm`, `-0.646 mm`), `8.35°` non-radial skew, `u = 20.066 mm` overmold plane (`≤ 0.65 mm` bezel wall or `12.6 × 6.8 mm` counterbore), and `0.440–0.530 mm` `S1` pad-corner clearance.
- **`MAJOR-1` (`S1` pad width `2.30 × 1.80 mm` vs `2.50 × 1.80 mm`):** **DISPUTED / JUSTIFIED in [design/decisions.md](../../decisions.md) (`2026-11-08`)** — widening `S1` to `2.50 × 1.80 mm` was tested in `pcbnew` + KiCad DRC and caused `6` `hole_clearance` violations (`0.105–0.138 mm < 0.200 mm`) against `6` fixed front-LED escape vias (`CS5_17, CS5_16, SW2_3, CS2_18, SW2_6, CS2_10`); keeping `parallelogram`'s verified `2.30 × 1.80 mm` (`92%` area, `+0.27 mm` heel/toe fillet) preserves `0` LEDs moved and `0` DRC errors.
- **`MAJOR-2` (`(subtractmaskfromsilk no)`, `'5V'`/`'R4'` pad encroachment, `'-'` under `U8`):** **FIXED** in `round-pendant.kicad_pcb` via [polish_board.py](../../../scripts/variant_fusbc/polish_board.py): enabled `(subtractmaskfromsilk yes)`, hid `R4`, nudged `'5V'` to `(109.25, 106.05, 270°)` clear of `J1` pads, and moved `'-'` to `(98.00, 115.45, 0°)` directly north of `BT1.2` clear of `U8`.
- **`MINOR-1..3` (`2-Ø0.50 mm` peg callout, `403535` cell ref, `+0.065 mm` signal-row shift note):** **FIXED** in [brief-f-usbc.md](../../brief-f-usbc.md) and this gate file.

### Round 2 Re-Review (`agy` `gemini-4-argon-high`)
- **Verdict:** **`Gate 4 Verdict: AWAITING_SIGNOFF — Ready for user sign-off (0 BLOCKER, 0 MAJOR, 2 MINOR, 2 NOTE)`** (`review_r2_phase4.txt`).
- **Summary & Minor Cleanups:** Independently re-derived `J1` mouth midpoint `(109.865, 115.605) mm` (`8.35°` non-radial skew), `+1.066 mm` nominal / `+0.666 mm` WC overmold clearance (`u = 20.066 / 19.666 mm`), all `16` (`2×8L`) `J1` `Ø0.65 mm` NPTH clearances (`0.2005–0.3113 mm`, `0` LEDs moved), `0.70 ± 0.05 mm` peg recess (`0.30 mm` nom / `0.15 mm` WC below `F.Cu`), and reproduced the `6` `hole_clearance` DRC violations (`0.105–0.134 mm`) if `S1` were widened to `2.50 × 1.80 mm`. Fixed `MINOR-1` (tightened bezel counterbore floor to `u ≤ 19.0–19.4 mm` & updated intermediate `y_out` numbers in [brief-f-usbc.md](../../brief-f-usbc.md) §2), `MINOR-2` (added `y_rel = +2.300 mm` signal-row land note above and in [brief-f-usbc.md](../../brief-f-usbc.md) §3), and `NOTE-1` (tented + POFV-capped VIPPO qualification & `min = 0.0655 mm` `F.SilkS` threshold).
