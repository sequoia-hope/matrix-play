# Mechanical and Layout Brief — Round Pendant Variant `f-usbc-rtc` (`Rev FUR`)

Parent board: **Variant `f-usbc`** ([hw/round-pendant/f-usbc/round-pendant.kicad_pcb](../hw/round-pendant/f-usbc/round-pendant.kicad_pcb), brief [design/brief-f-usbc.md](brief-f-usbc.md), stackup [design/stackup.md](stackup.md)).
Variant folder: [hw/round-pendant/f-usbc-rtc/](../hw/round-pendant/f-usbc-rtc).

This document records every Phase 4 mechanical and layout brief item ([intent-and-brief.md](../.claude/skills/pcb-design/references/intent-and-brief.md)) for `round-pendant-f-usbc-rtc` (`Rev FUR`), which builds directly on `round-pendant-f-usbc` (`J1` full-SMT 16-pin USB-C `TYPE-C-31-M-22`) by:
1. Replacing the unpopulated `BT1` wire-solder pads (`round_pendant:BatteryPads`) with an **inward-facing right-angle SMT `1.25 mm` PicoBlade / MX1.25 battery receptacle** (**CJT `A1251WR-S-2P`**, `C225111`) in the SW sector with **`4.88 mm` nominal (`4.65 mm` min to `U4`, `5.85 mm` to `C22`) unobstructed NNE plug-insertion runway** and **`0 mm` added stack height** (`3.20 mm` housing matches `J1`'s `3.16–3.26 mm` shell).
2. Adding an ultra-low-power **Seiko Epson `RX8130CE:BB` (`C1542426`)** Real-Time Clock module (`3.2 × 2.5 × 1.0 mm` `SMD-10P`, built-in `32.768 kHz` crystal, `1.5 µA` active on always-on `+3V3`, `POWMAN` alarm/timer wake on `U3` Pin `31` `GPIO19`) in the vacant East `B.Cu` pocket (`0` existing parts displaced there), while keeping **all `235` front LEDs (`D1..D235`), `Q2`, `J1`, `SW1`, `SW2`, `U1..U7`, `U9..U12`, and all `147` locked `RP2350` decoupling tracks `100%` untouched**.

---

## 1. Board Outline & Size
- **Outline:** Circle, **`Ø38.000 mm`** (`center = (100.000, 100.000) mm`, `radius = 19.000 mm`), unchanged from `f-usbc` ([brief-f-usbc.md](brief-f-usbc.md) §1).
- **Copper-to-edge rule:** `0.200 mm` minimum (`round-pendant.kicad_pro`):
  - **`J1` (`TYPE-C-31-M-22`):** Unchanged at `(107.787, 110.926, -156.05°)`; closest `S1` SMD pad corner sits `0.440–0.530 mm` inside `Edge.Cuts`.
  - **`BT1` (`CJT A1251WR-S-2P`, `C225111`):** Seated at **`(89.200, 110.550) mm`, `KiCad B.Cu rot = -28.00°`** (`CPL = 208.00°`). Outermost `B.Cu` pad corner (`West MP` `2.10 × 3.00 mm` pad at `(86.631, 108.618) mm`) reaches `r_max = 17.345 mm` (**`1.655 mm` inside `Edge.Cuts`**); outermost rear signal pin corner (`Pin 1 VBAT` at `(87.523, 112.376) mm`) reaches `r_max = 18.210 mm` (**`0.790 mm` inside `Edge.Cuts`**); housing courtyard stays **`≥ 0.65 mm` inside `Ø38.000 mm`** (`0` rim overhang!).
  - **East RTC block (`U13`, `C75`, `C76`, `R32`):** Outermost routed copper (`CS5_1` via at `(118.493, 101.614) mm`, `0.312 mm` inside `Edge.Cuts`; `C75.2` `GND` via at `(118.504, 101.208) mm`, `0.332 mm`; `C76.2` `GND` via at `(118.376, 102.411) mm`, `0.337 mm`) maintains **`≥ 0.312 mm` margin inside `Edge.Cuts`** (`> 1.56×` the `0.200 mm` DRC minimum).

## 2. Mounting, Bezel & Inward Battery Plug Insertion Runway
- **Mounting holes:** `0` (`6` total NPTH locating holes unchanged from `f-usbc`: `2× Ø0.650 mm` for `J1`, `4× Ø0.700 mm` for `SW1/SW2`; `BT1` `A1251WR-S-2P` is pure 4-pad SMT with `0` locating pegs).
- **Rim geometry:** Identical to [brief-f-usbc.md](brief-f-usbc.md) §2 (`J1` SSE `23.95°` E of S, `SW1` NE, `SW2` NW, `Q2` N; `BT1` is completely recessed inside the SW rim with `0.00 mm` perimeter projection, so no enclosure wall cutout is needed for `BT1`).
- **Inward-facing `BT1` plug mating & withdrawal geometry (`cjt-a1251.pdf` p. 1, p. 3):**
  - Why SW `(89.200, 110.550, -28.00°)` instead of due South `(100.0, 117.1, 0°)`: at due South, WLCSP-36 driver `U2` `(96.5, 112.0)` and `U7` `(100.1, 112.4)` sit `< 0.5 mm` north of the `6.15 mm` connector depth, leaving zero room to insert or withdraw a `1.25 mm` plug.
  - At `(89.200, 110.550, -28.00°)`, `BT1`'s mating mouth center sits at **`(90.421, 108.254) mm`** facing **inward NNE (`+28.00°` East of North)** between `U1`/`C31` (to the NW) and `U4`/`U2` (to the East):
    - Per `cjt-a1251.pdf` pp. 1, 3, the `A1251H-2P` crimp housing (`width B = 4.25 ± 0.25 mm`, `length = 4.00 ± 0.25 mm`; mated wafer + plug = `5.80 mm` -> `1.60 mm` seated protrusion + `2.40–2.60 mm` unlatch withdrawal = `4.00–4.20 mm` flat clearance needed) has **`4.884 mm` nominal (`4.649 mm` at `4.50 mm` max plug width) flat runway** before its SE corner reaches `0.80 mm`-tall `U4` (`5.845 mm` to `C22`), giving **`+0.88 mm` nominal (`+0.40 mm` worst-case) flat insertion/withdrawal margin** (and unlimited `+Z` lift over `U4` when mated before adhering the rear `35 mm` LiPo).
    - Flexible `28–30 AWG` silicone LiPo leads exit the seated plug at `z ≈ 1.60 mm` above `B.Cu` (well above `0.80 mm`-tall `U4` WSON-8 and `0.55 mm` `0402` passives) and curl gently under the rear `35 mm` LiPo cell, which rests flush over `BT1`'s `3.20 mm` flat thermoplastic top (`0 mm` added stack thickness beyond `J1`'s `3.16–3.26 mm` USB-C shell).

## 3. Connectors, Controls & New RTC Block (`B.Cu` & `F.Cu`)

| Ref | Part / MPN (`LCSC`) | KiCad `(X, Y)` (`mm`), Rot | Facing / Function | Mechanical & Datasheet Verification |
|---|---|---|---|---|
| `J1` | Hroparts `TYPE-C-31-M-22` (`C530612`) | `(107.787, 110.926)`, `-156.05°` | Outward SSE (`5 V` USB-C) | Unchanged from `f-usbc` (`4× 2.30 × 1.80 mm` `S1` SMD pads + `2× Ø0.65 mm` NPTHs). |
| `BT1` | CJT `A1251WR-S-2P` (`C225111`, `1.25 mm` 2P RA SMT) | `(89.200, 110.550)`, `-28.00°` | Inward NNE (`+28°` E of N), `3.7 V` LiPo | `Pin 1` (`VBAT`, `+`) at `(87.523, 112.376)`, `Pin 2` (`BAT_N`, `-`) at `(88.627, 112.963)`, `2× MP` (`2.10 × 3.00 mm` `GND` mechanical tabs) at `(86.631, 108.618)` & `(92.238, 111.599)` (`12.60 mm²` `MP` + `2.56 mm²` signal = `15.16 mm²` `B.Cu` solder area; `3.20 mm` height). |
| `U13` | Seiko Epson `RX8130CE:BB` (`C1542426`, `I2C` RTC) | `(114.750, 101.200)`, `0.00°` | East `B.Cu` pocket (`0x32` on `I2C1`, wake -> `GPIO19`) | `3.2 × 2.5 × 1.0 mm` ceramic `SMD-10P` (`1.00 mm` height << `3.20 mm` `J1`/`BT1`). `B.Cu` rule area **`RX8130_xtal_end`** (`X ∈ [114.30, 115.20], Y ∈ [102.30, 103.05] mm`, `no_tracks, no_vias, no_pour`) keeps `B.Cu` copper strictly clear of the Pin `1–10` `*1` crystal inspection short side ([rtc-rx8130ce.md](parts/rtc-rx8130ce.md) §4, `ETM50E-10` Fig. 9 p. 11). |
| `SW1`, `SW2` | Panasonic `EVQP7C01P` (`C388883`) | `(116.198, 93.701, -68.75°)` / `(83.858, 93.723, +68.75°)` | Outward NE (`USER`) / NW (`BOOT`) | Unchanged from Variant F / `f-usbc`. |

## 4. Assembly Sides & Reflow Order
- **Double-sided SMT (`0` PTH solder joints, `100%` turnkey PCBA including `BT1` & `U13`):**
  - **`F.Cu` (Pass 1, `≤ 250 °C` peak):** `235× XL-1010RGB-YG` (`C965834`) + `1× ALS-PT19` (`Q2`, `C146233`).
  - **`B.Cu` (Pass 2, `≤ 250 °C` peak):** All `13` ICs (incl. `U13` `RX8130CE:BB`, rated `260 °C` max / `2` reflows per `ETM50E-10` §6.1 Fig. 12 p. 12), passives, `SW1/SW2`, `J1`, and `BT1` (`A1251WR-S-2P` PA9T high-temp nylon housing, `260 °C` reflow rated per `cjt-a1251.pdf` p. 1) — eliminating manual battery-lead soldering onto bare PCB pads!

## 5. Layer Count & Stackup (`8` Layers, `1.00 mm` `JLC08101H-1080`, `ENIG`, POFV)
Identical to [brief-f-usbc.md](brief-f-usbc.md) §5 and [stackup.md](stackup.md) §2 (`JLC08101H-1080`, `1.00 mm`, `1 oz` outer / `0.5 oz` inner, `In2.Cu = plane GND`, `In5.Cu = plane VSYS + plane 3V3`, `ENIG 1U"`, `POFV = Yes`).

## 6. Density Philosophy
Identical to [brief-f-usbc.md](brief-f-usbc.md) §6 (`0402` passives, `0603` bulk MLCCs, `0.09/0.09 mm` trace/space, `0.25/0.15 mm` standard vias + `0.30/0.15 mm` power vias + `3` inherited `0.20/0.10 mm` vias inside `U3` `+3V3` band, POFV).

## 7. Floorplan & Delta vs Parent `f-usbc`
All `236` front parts (`D1..D235` + `Q2`), `J1`, `U1..U7`, `U9..U12`, `SW1`, `SW2`, `L1`, `Y1`, `TP1, TP2, TP4..TP8`, and all `147` locked `RP2350` decoupling tracks are **100% unchanged** from `f-usbc`. Only `15` SW/South `B.Cu` parts shift locally to open `BT1`'s pocket + `4` new RTC parts (`U13, C75, C76, R32`) populate the vacant East `B.Cu` pocket:

| Ref | Function | Parent `f-usbc` `(X, Y, Rot)` | Variant `f-usbc-rtc` `(X, Y, Rot)` | Placement Rationale |
|---|---|---|---|---|
| `BT1` | `A1251WR-S-2P` (`1.25 mm` 2P RA SMT) | `(100.000, 117.100, 180°)` (`BatteryPads`) | `(89.200, 110.550, -28.00°)` | Inward NNE mouth (`+28°` E of N) with `4.88 mm` nominal (`4.65 mm` min) flat plug runway to `U4` |
| `U8` | `XB9901A` LiPo protection | `(96.400, 116.400, -90°)` | `(91.500, 114.800, -90.00°)` | Immediately SE of `BT1.2` (`BAT_N`) with `2× 0.30/0.15 mm` `GND` vias |
| `C6` | `100 nF` `U8` decoupler | `(94.500, 116.600, 180°)` | `(89.900, 114.300, -90.00°)` | `1.11 mm` pad-to-pad from `U8.6` (`VDD`) |
| `R8` | `100 Ω` `U8` `VDD` series R | `(99.700, 115.000, 180°)` | `(97.000, 115.500, 180.00°)` | Short `VBAT` feed into `U8.6`/`C6.1` |
| `C40, C43` | `U2` `VSYS` decouplers | `(93.95, 111.80) / (93.20, 109.60)` | `(93.75, 114.55, -90°) / (94.25, 112.00, -90°)` | `2.55 / 3.10 mm` from `U2.A3 / U2.F5` (`VSYS` plane vias adjacent), clearing `BT1` & `U2` fanout |
| `TP3` | `VBAT` `Ø1.0 mm` test pad | `(104.000, 117.500, 180°)` | `(95.250, 116.750, 180.00°)` | Open South-SW test pad east of `U8` |
| `Q1, R9..R12, C7` | Switched `VBAT_SENSE` divider | SW `(90.2..93.5, 112.4..115.0)` | South `(97.5..101.5, 114.5..118.0)` | Relocated cleanly into vacated 6-o'clock South pocket (`BT1`'s old `f-usbc` site) |
| `R1, R2` | `5.1 kΩ` `CC1/CC2` pull-downs | `(93.90, 115.57) / (91.75, 115.49)` | `(102.50, 116.75, -90°) / (104.00, 117.00, 180°)` | Moved closer to `J1` in South-SSE pocket |
| **`U13`** | **`RX8130CE:BB` I2C RTC (`0x32`)** | *(new)* | **`(114.750, 101.200, 0.00°)`** | Vacant East pocket between `U12` and `SW1` (`RX8130_xtal_end` `B.Cu` rule area enforced; `0` `U12` fanout vias disturbed) |
| **`C75`** | **`100 nF` `U13.8` (`+3V3`) decoupler** | *(new)* | **`(117.550, 101.050, 0.00°)`** | **`1.23 mm`** straight east of `U13.8` (`VDD`) |
| **`C76`** | **`1 µF` `U13.9` (`RTC_VOUT`) cap** | *(new)* | **`(117.550, 102.050, 0.00°)`** | **`1.23 mm`** straight east of `U13.9` (`VOUT`) |
| **`R32`** | **`100 kΩ` `RTC_INT` pull-up** | *(new)* | **`(114.750, 98.350, 0.00°)`** | Directly north of `U13.6` (`~IRQ`) feeding `U3.31` (`GPIO19`) |

## 8. Thermal Management & Deep-Sleep Wake Budget
- **Thermal envelope:** Identical to [brief-f-usbc.md](brief-f-usbc.md) §8 (`θ_BA ≈ 32.4 °C/W` free-air / `49.5 °C/W` worn -> **`≤ 0.51 W` continuous wearable ceiling**, LED blanking while `~CHG == 0`, closed-loop `ADC4` foldback at `42 °C` charge / `47 °C` wear; `U13` adds `4.95 µW`, i.e., `0.0002 °C`).
- **Dormant + RTC timed-wake current:** With `RX8130CE` `FOUT` disabled (`1Ch[7:6] = 11b`, `I_DD = 1.50 µA` typ on `+3V3` from `U6` `TPS7A0233` `I_q = 25 nA`) and `R32 = 100 kΩ` idle (`0 nA` with `GPIO19` `PUE=0, PDE=0`), total dormant pendant battery draw is **`~201 µA` (`< 250 µA` budget; `+0.75%` delta for full hardware calendar/alarm wake)**.

## 9. Art Zone (`F.SilkS` Clipped Voronoi Seed Web)
Identical to [brief-f-usbc.md](brief-f-usbc.md) §9 (`100%` unchanged front art, clipped inside `R ≤ 18.720 mm` and outside all `6` NPTHs, `(subtractmaskfromsilk yes)`).

## 10. Silkscreen Policy (`designators = "selective"`, `0° / 270° [90° CCW]` Only)
- **Front (`F.SilkS`):** Identical to `f-usbc` (Voronoi web + `Q2` pin-1 dot, `0` text designators).
- **Back (`B.SilkS`):** `0` `[silk-over-via]`, `0` `[under-part]`, `0` `[association]`, `0` `[rotation]`, `0` `B.Cu` `[pin1]`, `0` DRC silk errors, `0.80 × 0.80 mm` / `0.15 mm` stroke, strictly **2 reading orientations (`0°` and `270°` bottom-to-top)**:
  - **Board identity:** `'rev FUR'` + `'2026-11'` (`'round-pendant'` / URL / `'CERN-OHL-P-2.0'` waived in [decisions.md](decisions.md)).
  - **Connector & switch labels (`0%` 3D occlusion):** `'5V'` near `J1`, `'+'` near `BT1.1` (`VBAT`) and `'-'` near `BT1.2` (`BAT_N`) (with `1.25 mm` LiPo harness polarity verification highlighted in [bringup-f-usbc-rtc.md](bringup-f-usbc-rtc.md)), `'USER'` near `SW1`, `'BOOT'` near `SW2`.
  - **Pin-1 indicators (`14/14` polarized `B.Cu` ICs/transistors incl. `U13`, `OD = 0.30 mm`):** `U1..U13, Q1` placed strictly outside `B.CrtYd` & 3D bodies.
  - **Selective designators + `346/346` collision-free `4:1` A4 assembly maps** ([assembly-top.pdf](renders/round-pendant-f-usbc-rtc/assembly-top.pdf), [assembly-bottom.pdf](renders/round-pendant-f-usbc-rtc/assembly-bottom.pdf)).

## 11. Keepouts, Rule Areas & Rear LiPo Stackup
- Inherited `RP2350` `+1V1` ring and `L1`/`VREG_LX` rule areas + new **`RX8130_xtal_end`** `B.Cu` rule area (`[114.30..115.20, 102.30..103.05] mm`), `Edge.Cuts`, and fixed footprints (`D1..D235, Q2, SW1, SW2, BT1, J1`) are **locked** in `round-pendant.kicad_pcb`.
- **Rear `35 mm` LiPo (`403535` / `GRP5435035` fitted with `2P 1.25 mm` `A1251H-2P` / PicoBlade plug):** Mate the `1.25 mm` battery plug into `BT1` first (after verifying red `+` aligns with `BT1.1` `'+'`!), apply `0.05 mm` Kapton tape over `TP1..TP8`, and seat the cell on a `3.3–3.5 mm` foam ring/spacer flush with `J1` (`3.26 mm`) and `BT1` (`3.20 mm`).

## 12. Test, Debug & Bring-Up Provisions
All `8` `Ø1.0 mm` `B.Cu` test pads (`TP1..TP8`) are preserved and accessible (`TP3 VBAT` at `(95.250, 116.750)`). Full bring-up, `BT1` harness polarity check, `RX8130CE` `I2C1` (`0x32`) init, and `POWMAN` `GPIO19` alarm-wake test procedure: [design/bringup-f-usbc-rtc.md](bringup-f-usbc-rtc.md).
