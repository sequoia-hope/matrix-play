# Mechanical and Layout Brief — Round Pendant Variant `f-usbc`

Parent board: **Variant F** ([hw/round-pendant/f/round-pendant.kicad_pcb](../hw/round-pendant/f/round-pendant.kicad_pcb), brief [design/brief.md](brief.md), stackup [design/stackup.md](stackup.md)).
Variant folder: [hw/round-pendant/f-usbc/](../hw/round-pendant/f-usbc).

This document records every Phase 4 mechanical and layout brief item ([intent-and-brief.md](../.claude/skills/pcb-design/references/intent-and-brief.md)) for `round-pendant-f-usbc`, where `J1` (`round_pendant:USB_Pads` wire pads on Variant F) is replaced by the full-SMT 16-pin USB-C receptacle **Korean Hroparts Elec `TYPE-C-31-M-22` (`C530612`)** via a local rip-up and re-route of the southern `B.Cu` I/O sector while keeping **all 235 front LEDs (`D1..D235`), `Q2`, `SW1`, `SW2`, `U1..U6`, `U9..U12`, and all 147 locked RP2350 decoupling tracks 100% untouched**.

---

## 1. Board Outline & Size
- **Outline:** Circle, **`Ø38.000 mm`** (`center = (100.000, 100.000) mm`, `radius = 19.000 mm`), unchanged from Variant F ([brief.md](brief.md) §1).
- **Copper-to-edge rule:** `0.200 mm` minimum (`round-pendant.kicad_pro`).
  - On `J1` (`(107.787, 110.926, -156.05°)`), the four `S1` SMD shell pad centers sit at `(113.330, 110.915)`, `(111.747, 107.351)`, `(104.063, 115.031)`, and `(102.480, 111.467)` (`max pad-center radius = 17.283 mm`).
  - The outermost actual copper pad corner (`East` front `S1` `2.30 × 1.80 mm` `roundrect`, `rratio = 0.12`, `(114.746, 111.271) mm`) sits at **`r = 18.560 mm` unrounded (`~18.47 mm` rounded)** — **`0.440–0.530 mm` inside `Edge.Cuts`** (`> 2.2×` the `0.200 mm` DRC floor).
  - On `BT1` (`(100.000, 117.100, 180°)`), the two `1.60 × 2.40 mm` wire pads reach `r_outer = 18.366 mm` (`0.634 mm` inside `Edge.Cuts`).

## 2. Mounting & Bezel Clearances
- **Mounting holes:** `0` (unchanged wearable pendant form factor).
- **Rim geometry & enclosure counterbore requirements:**
  1. **`J1` USB-C mouth (`(109.865, 115.606) mm` midpoint, insertion axis `23.95°` east of South / KiCad `+66.05°`):**
     - **Non-radial skew (`8.35°`):** `J1`'s mouth midpoint sits at polar bearing **`32.30°` east of South** (`r = 18.462 mm`, `-0.538 mm` inside `Ø38.000 mm`), while `J1`'s insertion axis points **`23.95°` east of South**. That intentional `8.35°` skew threads both `5.78 mm`-spaced `Ø0.65 mm` NPTH locating holes cleanly into fixed front-LED gaps (`0.220 mm` pad clearance on both holes, `0` LEDs moved).
     - **Asymmetric shell corner overhang:** East `B.Fab` shell corner `(113.951, 113.791)` sits at `r = 19.616 mm` (**`+0.616 mm` overhang** past `Ø38.000 mm`); West `B.Fab` shell corner `(105.780, 117.420)` sits at `r = 18.354 mm` (**`-0.646 mm` recessed** inside `Ø38.000 mm`).
     - **Bare-board USB-C plug overmold clearance:** Standard USB Type-C plug tongue insertion depth (`6.65 ± 0.25 mm`, USB Type-C R2.2 §3.5) into `TYPE-C-31-M-22`'s `4.85 ± 0.15 mm` cavity (`type-c-31-m-22.pdf` p. 1 `SECTION A-A`) stops the `≤ 12.35 × 6.50 mm` plug overmold shoulder `1.800 mm` nominal (`1.400 mm` worst-case) forward of `J1`'s `y_out = +5.120 mm` mouth (`y_out = +6.920 / +6.520 mm`). Across `x_local ∈ [-6.175, +6.175] mm`, the closest tangent on the `Ø38.000 mm` PCB circle reaches `y_out = +5.854 mm` (at `2.681 mm` WSW of midpoint), leaving **`+1.066 mm` nominal (`u = 20.066 mm`) / `+0.666 mm` worst-case (`u = 19.666 mm`) axial overmold clearance** on the bare pendant.
     - **Enclosure / bezel counterbore rule:** East shell corner `(113.951, 113.791)` (`r = 19.616 mm`, `+0.616 mm`) requires a port opening even in thin walls `≤ 0.65 mm`, and any future perimeter bezel wall thicker than `0.65 mm` radially **must** machine a **`≥ 12.6 × 6.8 mm` clearance pocket / counterbore aligned to `23.95°` east of South** inward to **`u ≤ 19.0–19.4 mm`** (down to the `Ø38.000 mm` PCB rim around `(105.8, 117.4)`) so the recessed west side of the plug overmold never bottoms out on the bezel.
  2. **`SW1` (`-28°` NE) & `SW2` (`-152°` NW):** Unchanged Panasonic `EVQP7C01P` (`+0.40 mm` actuator projection past `Ø38.0 mm`).
  3. **`Q2` (`ALS-PT19-315C/L177/TR8`, 12-o'clock N rim `(97.960, 81.960) mm`):** Unchanged optical window on `F.Cu`.

## 3. Connectors & Rim Controls (`B.Cu` & `F.Cu`)

| Ref | Part / MPN (`LCSC`) | KiCad `(X, Y)` (`mm`), Rot | Facing / Rim Relation | Mechanical & Datasheet Verification |
|---|---|---|---|---|
| `J1` | Hroparts `TYPE-C-31-M-22` (`C530612`, full-SMT 16P USB-C) | `(107.787, 110.926)`, `-156.05°` (`203.95°`) | Outward SSE (`23.95°` E of S); East corner `+0.616 mm`, West corner `-0.646 mm`, plug overmold `+1.066 mm` clear of rim | **4 SMD gull-wing shell tabs (`2.30 × 1.80 mm`) on `B.Cu` only** (`0` PTH shell slots through `F.Cu`). Two `Ø0.65 mm` (`r = 0.325 mm`) NPTH holes at `(109.953, 108.684)` (inside `{D234, D235, D231, D226}`) and `(104.671, 111.030)` (inside `{D76, D66, D74, D64}`) clear `F.Cu` LED pads by **`0.220 mm`** (`D234.4`) and **`0.220 mm`** (`D74.3`), `F.Cu` track `CS2_12` by **`0.214 mm`**, and all inner/bottom copper by **`≥ 0.201 mm`** (`In3.Cu > 0.30 mm`; `0` LEDs moved). |
| `BT1` | `round_pendant:Battery_Pads` (`2 × 1.60 × 2.40 mm` SMD wire pads, DNP) | `(100.000, 117.100)`, `180.00°` | South rim (`6 o'clock`, `r_outer = 18.37 mm`) | Shifted `+0.60 mm` south into former `USB_Pads` pocket (`Pin 1 VBAT` at `(101.60, 117.10)`, `Pin 2 BAT_N` at `(98.40, 117.10)`). Wire leads solder directly to rear `3.7 V` `403535` / `GRP5435035` LiPo ([battery.md](parts/battery.md)). |
| `SW1`, `SW2` | Panasonic `EVQP7C01P` (`C388883`) | `(116.198, 93.701, -68.75°)` / `(83.858, 93.723, +68.75°)` | Outward (`+0.40 mm` plunger past rim) | Unchanged from Variant F (`2 × Ø0.70 mm` NPTH pegs each). |

### `TYPE-C-31-M-22` Datasheet vs `1.0 mm` PCB Audit ([type-c-31-m-22.pdf](datasheets/type-c-31-m-22.pdf) p. 1 & [USB-C-SMD_TYPE-C-31-M-22.step](../3dmodels/USB-C-SMD_TYPE-C-31-M-22.step))
1. **Locating peg length & diameter vs `1.0 mm` board thickness:**
   - Datasheet front elevation specifies **`2-Ø0.50 mm` (`±0.05 mm`)** plastic locating pegs extending **`0.70 ± 0.05 mm`** below the `B.Cu` seating plane (`Ø0.500 × 0.680 mm` in vendor 3D STEP), matching [parallelogram-io.md](parts/parallelogram-io.md) §1.
   - On our **`1.00 mm` ±10% (`0.90–1.10 mm`)** 8-layer PCB, the pegs have **`0.10–0.20 mm` positive diametral clearance** inside `2-Ø0.65 mm` NPTH drills and terminate **`0.30 mm` nominal (`0.15–0.45 mm` worst-case) BELOW the front `F.Cu` LED surface** — zero front protrusion. Two `Ø0.65 mm` unplated apertures remain visible in the dark front mask web inside `{D234, D235, D231, D226}` and `{D76, D66, D74, D64}`.
2. **4-SMD-pad shell land size (`2.30 × 1.80 mm`) & mechanical hold-down strength:**
   - Rated mating force (`type-c-31-m-22.pdf` p. 1): **`5–20 N` insertion, `8–20 N` extraction**, `10,000` cycles.
   - We retain `parallelogram`'s verified `round_pendant:USB_C_Receptacle_Hroparts_TYPE-C-31-M-22` `S1` pad size of **`2.30 × 1.80 mm`** at `±5.07 mm` (`92.0%` of the datasheet's `2.50 × 1.80 mm` land: `16.56 mm²` total `S1` copper + `5.13 mm²` signal pads = **`21.69 mm²` total `B.Cu` `1 oz` ENIG solder area**), which provides **`+0.27 mm` heel and `+0.27 mm` toe solder fillet** beyond the physical `1.48 mm`-wide stainless gull-wing foot (`x_local = ±4.47..5.95 mm` in STEP) while preserving **`≥ 0.205 mm` `hole_clearance`** to `6` fixed front-LED escape vias (`CS5_17`, `CS5_16`, `SW2_3`, `CS2_18`, `SW2_6`, `CS2_10`). The footprint's 12 rear signal pads sit at `y_rel = +2.300 mm` (`1.14 mm` long vs `parallelogram-io.md`'s `y = 2.240 mm`, `1.15 mm` long), a benign `+0.055–0.060 mm` outboard shift over `0.40 mm`-protruding tails that widens `B.Cu` NPTH clearance to `0.247 mm`.
   - Pure axial mating shear capacity (`~330–500 N`) exceeds `16×` the `20 N` specification; out-of-plane copper foil peel resistance is `~35–55 N` (`~0.15–0.22 N·m` off-axis pry torque). Users should mate/unmate straight along the SSE axis on bare boards, or capture `J1`'s `3.16 mm` stainless shell against a rear carrier if cased.

## 4. Assembly Sides & Reflow Order
- **Double-sided SMT (`0` PTH solder joints):**
  - **`F.Cu` (Top):** `235× XL-1010RGB-YG` (`C965834`, MSL-3, `255 °C` peak / `2` reflows) + `1× ALS-PT19-315C/L177/TR8` (`Q2`, `C146233`, `260 °C` peak / `3` reflows).
  - **`B.Cu` (Bottom):** All active ICs (`U3` `RP2350A`, `5× IS31FL3745` WLCSP-36, `U5` `BQ24073`, `U4` QSPI, `U6` LDO, `U7` ESD, `U8` LiPo prot, `U9` accel), passives, `SW1/SW2`, and `J1`.
  - **PCBA reflow sequence:** **`Pass 1 = F.Cu` (`≤ 250 °C` peak), `Pass 2 = B.Cu` (`≤ 250 °C` peak)** (`~1.5 mg` `1010` LEDs held by surface tension during Pass 2; heavier `J1` and `U3` reflowed upright once).

## 5. Layer Count & Stackup (`8` Layers, `1.00 mm` `JLC08101H-1080`, `ENIG`, POFV)
Full dielectric/copper table in [design/stackup.md](stackup.md) §2 (`JLC08101H-1080`, `0.9968 mm` nominal, `1 oz` outer / `0.5 oz` inner, `4× 1080` prepreg `0.0764 mm` + `3× 0.170 mm` FR-4 cores, `ENIG 1U"`, POFV):
- `F.Cu` (`1 oz`): LED lands + local `R/G/B/SW` escapes (`0` USB copper).
- `In1.Cu` (`0.5 oz`): Signal routing (`SW`/`CS` matrix, `VBUS`).
- `In2.Cu` (`0.5 oz`): **Continuous `GND` reference plane** (`1` whole piece, `847.50 mm²`).
- `In3.Cu` (`0.5 oz`): Signal routing (`SW`/`CS` matrix, `VBAT` `0.30 mm` trunk).
- `In4.Cu` (`0.5 oz`): Signal routing (`SW`/`CS` matrix, `USB_D*_MCU`, `0` copper zones).
- `In5.Cu` (`0.5 oz`): **Power plane (`plane VSYS` `600.37 mm²` + `plane 3V3` `215.76 mm²`, `1` whole piece each)**.
- `In6.Cu` (`0.5 oz`): Bottom-adjacent signal escape layer (`USB_DM_C`, `CC2`, `SW`/`CS`; `0` zones).
- `B.Cu` (`1 oz`): All ICs, passives, `J1`, `BT1`, `SW1/SW2`, `TP1..TP8`, and `RP2350` pours (`+1V1` ring, `+3V3` band, `VREG_LX`, vendor `GND`/`+1V1`/`+3V3`).

## 6. Density Philosophy
Unchanged from Variant F: `0402` passives, `0603` bulk MLCCs, `0.09/0.09 mm` trace/space, `0.25/0.15 mm` standard through-vias (`886` total PTH vias), plus the `3` inherited `0.20/0.10 mm` vias inside `U3`'s perimeter (`+1V1` at `(96.32, 91.60)` & `(100.88, 91.60)`, `GND` at `(98.60, 96.45)`), epoxy-filled & capped POFV via-in-pad.

## 7. Floorplan & Displaced Back Parts (Southern Sector Only)
Northern, eastern, western, and central blocks (`U3` RP2350 + `Y1` + `L1` + `U4` + `R14/R15` `27 Ω` USB series terminators, `U9`, `U6`, `U5`, `R1/R2` `5.1 kΩ` CC pull-downs, and all `5×` WLCSP-36 drivers `U1, U2, U10, U11, U12` + local passives) are **100% unchanged** from Variant F. Only `J1` and `8` southern `B.Cu` parts (`y ≥ 106.4 mm`) moved:

| Ref | Function | Variant F `(X, Y, Rot)` | Variant `f-usbc` `(X, Y, Rot)` | Placement Rationale |
|---|---|---|---|---|
| `J1` | USB-C 16P (`TYPE-C-31-M-22`) | `(100.000, 116.500, 0°)` (`USB_Pads`) | `(107.787, 110.926, -156.05°)` | Outward SSE rim (`23.95°` E of S); both NPTHs clear `F.Cu` LED pads (`0.220 / 0.220 mm`) |
| `U7` | `USBLC6-2P6` USB ESD | `(102.300, 109.400, 180°)` | `(100.100, 112.400, 113.95°)` | In-line between `J1` (`D+/D-` on pins `1,3`, `0` `F.Cu` hops) and `R14/R15` (`0`-via `B.Cu` on pins `4,6`), dual-via `GND` return |
| `C1` | `1 µF` `VBUS` decoupler (`U5.13`) | `(105.000, 110.000, 180°)` | `(102.500, 108.800, 180.00°)` | `1.78 mm` from `U5.13` (`IN`), clamping `VBUS` surges directly at charger input |
| `R5` | `3.6 kΩ` `U5` `ILIM` | `(105.000, 108.950, 180°)` | `(107.500, 106.400, 90.00°)` | Clear of `J1` NE `S1` pad, short run to `U5.12` |
| `BT1` | `Battery_Pads` (`VBAT`/`BAT_N`) | `(109.800, 112.900, 180°)` | `(100.000, 117.100, 180.00°)` | Centered at 6-o'clock South rim (`2× 0.30/0.15 mm` parallel `VBAT` vias) |
| `U8` | `XB9901A` LiPo protection | `(106.100, 112.600, 180°)` | `(96.400, 116.400, -90.00°)` | Immediately west of `BT1.2` (`0.300 mm` CAD copper/`B.Mask` gap = `3.0×` JLC min + Kapton mask during wire attach; `0`-via `B.Cu` `BAT_N`, dual-via `GND` return) |
| `C6` | `100 nF` `U8` decoupler | `(107.200, 110.600, 180°)` | `(94.500, 116.600, 180.00°)` | `1.08 mm` pad-to-pad from `U8.6` (`VDD`) |
| `R8` | `100 Ω` `U8` `VDD` series R | `(106.100, 114.600, 180°)` | `(99.700, 115.000, 180.00°)` | Directly north of `BT1.1` (`VBAT`) feeding `U8.6`/`C6.1` |
| `TP3` | `VBAT` `Ø1.0 mm` test pad | `(108.113, 108.950, 180°)` | `(104.000, 117.500, 180.00°)` | Accessible east of `BT1.1` (`+`) outside `J1` courtyard |

## 8. Thermal Management & Wearable Power Envelope
- **Whole-board thermal resistance ([si_audit.py](../scripts/variant_fusbc/si_audit.py) §5):** On a `Ø38.0 mm` disc (`11.34 cm²` per face), natural convection + `ε = 0.9` solder-mask radiation yields **`θ_BA ≈ 32.4 °C/W` in free air** (both faces exposed) and **`θ_BA ≈ 49.5 °C/W` when worn** against clothing/skin with the rear LiPo insulating `~70%` of `B.Cu`.
- **Continuous vs burst LED power:**
  - **Continuous wearable ceiling:** **`≤ 0.51 W` total (`~100 mA` total LED average current, `GCC ≤ 0x55`)**, limiting steady-state worn board rise to `ΔT ≤ 22–25 °C` (`T_board ≤ 47–50 °C` at `25 °C` ambient, within the `50 °C` wearable skin limit).
  - **Peak `1.26 W` (`300 mA` LED total):** Short-duration animation bursts (`≤ 15 s`) or free-air bench demo only (`ΔT_free ≈ 40.8 °C`, `ΔT_worn ≈ 62.3 °C` if sustained continuously).
  - **USB charging (`BQ24073` `297 mA`, `0.48–0.79 W` peak at `3.0 V` cell):** Firmware **must** blank or cap LEDs to `< 5 mA` whenever `~CHG == 0` (`GPIO12`, `U3` Pin 16) so charger + LED power never exceeds `0.55 W` (`T_cell ≤ 42 °C < 45 °C` LiPo charge limit), backed by closed-loop `RP2350` `ADC4` die-temperature foldback ([bringup-f-usbc.md](bringup-f-usbc.md) §4 Step 3.3).

## 9. Art Zone (`F.SilkS` Clipped Voronoi Seed Web)
Unchanged from Variant E/F (`F.SilkS` Voronoi sunflower web around `235` LEDs, clipped clear of `F.Cu` pads and `Q2`'s window), plus clipped strictly inside `R ≤ 18.720 mm` (`≥ 0.203 mm` stroke-edge clearance from `Edge.Cuts`) and outside all `6` NPTH holes (`r ≥ 0.600 mm` / `≥ 0.199 mm` stroke-edge margin around `J1`'s two `Ø0.65 mm` NPTHs; `r ≥ 0.630 mm` / `≥ 0.203 mm` around `SW1/SW2`'s four `Ø0.70 mm` NPTHs), `< 0.055 mm` runt specks pruned, and `(subtractmaskfromsilk yes)` active in board setup.

## 10. Silkscreen Policy (`designators = "selective"`, `0° / 270° [90° CCW]` Only)
- **Front (`F.SilkS`):** Voronoi art + `Q2` `OD = 0.24 mm` (`0.12 mm` stroke, inherited from Variant F) pin-1 indicator dot only (`0` text designators on display face).
- **Back (`B.SilkS`):** `0` untented `[silk-over-via]` (`6` tented + POFV-capped flat VIPPO crossings only), `0` `[under-part]`, `0` `[association]`, `0` `[rotation]`, `0` `B.Cu` `[pin1]`, `0` DRC silk errors, `0.80 × 0.80 mm` / `0.15 mm` stroke, strictly **2 reading orientations (`0°` horizontal and `270°` bottom-to-top vertical)**:
  - **Board identity:** `'rev FU'` at `(105.30, 98.95, 270°)` + `'2026-11'` at `(89.40, 107.52, 0°)` (`'round-pendant'` / URL / `CERN-OHL-P-2.0` strings formally waived in [decisions.md](decisions.md) due to `886` vias across `Ø38.0 mm`).
  - **Connector & switch function/polarity/rating labels (`0%` 3D occlusion):** `'5V'` at `(109.25, 106.05, 270°)` north of `J1`, `'+'` at `(101.20, 115.05, 0°)` north of `BT1.1`, `'-'` at `(98.00, 115.45, 0°)` north of `BT1.2` (clear of `U8`; multi-char `'BAT'`/`'3V7'` beside `BT1` waived in [decisions.md](decisions.md) because `886` LED vias leave zero `≥ 2.4 mm` via-free pocket within `9.25 mm` of `BT1`), `'USER'` at `(116.45, 97.29, 0°)` beside `SW1`, and `'BOOT'` at `(82.52, 97.74, 270°)` beside `SW2`.
  - **Pin-1 indicators (`13/13` polarized `B.Cu` ICs/transistors, `OD = 0.30 mm`):** `U1, U2, U3, U4, U5, U6, U7, U8, U9, U10, U11, U12, Q1`, every single dot placed **strictly outside `B.CrtYd` & 3D bodies** (`0` embedded inside-courtyard dots; unpolarized `L1` has `0` dot).
  - **Selective unambiguous designators (`9` shown, `0°×4, 270°×5`):** `TP2, TP4, TP5, TP8, SW1, SW2, U4, Q1, Y1`; collision-free `342/342` assembly maps provided in [assembly-top.pdf](renders/round-pendant-f-usbc/assembly-top.pdf) and [assembly-bottom.pdf](renders/round-pendant-f-usbc/assembly-bottom.pdf).

## 11. Keepouts, Rule Areas & Rear LiPo Stackup
- All `240` fixed footprints (`D1..D235, Q2, SW1, SW2, BT1, J1`), `Edge.Cuts`, and `RP2350`/`L1` keepout rule areas are **locked** in `round-pendant.kicad_pcb`.
- **Rear `35 mm` LiPo (`403535` / `GRP5435035`, [battery.md](parts/battery.md)):** Apply **`0.05 mm` Kapton tape** over `TP1..TP8` and `BT1` solder joints plus a **`3.3–3.5 mm` foam ring/spacer** matching `J1`'s `3.16–3.26 mm` shell height.

## 12. Test, Debug & Bring-Up Provisions
All `8` `Ø1.0 mm` `B.Cu` test pads (`TP1` `VSYS`, `TP2` `+3V3`, `TP3` `VBAT`, `TP4` `+1V1`, `TP5` `RUN`, `TP6` `SWCLK`, `TP7` `SWDIO`, `TP8` `GND`) are preserved and accessible. Full bring-up & sleep/thermal validation plan: [design/bringup-f-usbc.md](bringup-f-usbc.md).
