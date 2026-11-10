# Gate 7: routing (`round-pendant-f-usbc-rtc`)

Status: **passed**
Parent board baseline compared against: **`round-pendant-f-usbc`** ([hw/round-pendant/f-usbc/round-pendant.kicad_pcb](../../../hw/round-pendant/f-usbc/round-pendant.kicad_pcb)), with routing & keepout dispositions in [design/decisions.md](../../decisions.md) (`2026-11-09`).

---

## Checklist (`references/routing.md` §Gate checklist)

- [x] **DRC `0` errors, `0` warnings, `0` unrouted (`kicad-cli pcb drc --severity-all --schematic-parity`):** **`Found 0 violations`, `Found 0 unconnected items`** (verbatim output below).
- [x] **Schematic parity:** `0` functional differences — only the **2 inherited Variant E/F `U3` pin 42/43 `{slash}` name mismatches** on unconnected pins (`GPIO28/ADC2` vs `GPIO28{slash}ADC2`, `GPIO29/ADC3` vs `GPIO29{slash}ADC3`), explicitly named below and never hidden ([decisions.md](../../decisions.md)).
- [x] **`pad_joints_fixed.py` passes (no SMD pad joint under `0.09 mm` fab minimum):** **`PASS: 0 thin pad joints`** across all `1,433` net-assigned SMD pads (`+17` vs `f-usbc`'s `1,416`: `BT1` adds `+3` net-assigned SMD pads [`2` signal + `2` `GND` `MP` vs `1` net-assigned pad in `f-usbc`'s unpopulated `BatteryPads`], `U13` adds `+8` net-assigned SMD pads [`Pins 4 [FOUT] & 5 [~RST]` are `NC`], `C75/C76` add `+4`, and `R32` adds `+2`).
- [x] **`copper_audit.py` passes all routing & strip-zone checks:** `tracks=5883 vias=918 | dangling=0 cap_gap=0 mid_graze/stubs=0 off_via=0 morph_necks(<86um)=0 acute_slivers=0 collinear_dups=0 micro_segs(<40um)=229 strip_zones=0 zone_intrusions=2` (`0` routing/strip defects; `2` inherited `B.Cu` vendor-zone intrusions `vendor +1V1` and `vendor GND` from Variant E/F, identical to `f-usbc`).
- [x] **Current capacity, via-count & RTC crystal keepout checks pass:**
  - **`VBUS` (`500 mA` max):** **`0` vias** on the `500 mA` `J1 -> C1 -> U5.13` `0.25 mm` `1 oz` `B.Cu` charger path (`R_25C = 3.90 mΩ`, `R_60C = 4.44 mΩ`, `Vdrop = 2.22 mV @ 500 mA`, `> 900 mA` IPC-2221 1 oz outer ampacity); `2× 0.30/0.15 mm` vias sit only on the `U7.5` TVS clamp branch.
  - **`VBAT` (`340 mA` max cont / `297 mA` charge / `1.0 A` brief transient):** Routed on `0.30 mm` `1 oz` `B.Cu` + plane-cooled `0.30 mm` `0.5 oz` `In3.Cu`/`In4.Cu` with **`8` `VBAT` vias** including **`2×` parallel `0.30/0.15 mm` vias** at `(95.618, 117.089)` & `(94.518, 116.839)` near `TP3.1`/`R8.2` (`R_25C = 83.23 mΩ`, `R_60C = 94.68 mΩ`, `Vdrop = 32.19 mV @ 340 mA`; total battery loop incl. `BAT_N`, `U8 -> GND`, and `2 × 20 mΩ` CJT `A1251WR-S-2P` contact resistance = **`139.88 mΩ` @ `60 °C`** -> `47.56 mV @ 340 mA` / `41.55 mV @ 297 mA` charge). Plane-cooled `0.30 mm` `0.5 oz` `In3.Cu`/`In4.Cu` (`0.076–0.170 mm` from solid `In2.Cu GND` and `In5.Cu VSYS`) exceeds **`0.80 A` IPC-2152 internal ampacity** (`> 2.3×` continuous demand).
  - **`/Power/BAT_N` & `U8.1..3 -> GND` (`340 mA` cont):** `/Power/BAT_N` has **`0` vias** (`0.30 mm` `1 oz` `B.Cu` directly from `BT1.2` to `U8.4/5`, `R_25C = 3.82 mΩ`, `R_60C = 4.34 mΩ`, `1.48 mV @ 340 mA`), and `U8.1..3` exits into **`2×` parallel `0.30/0.15 mm` `GND` vias** (`R_25C = 0.76 mΩ`, `R_60C = 0.86 mΩ`, `0.29 mV @ 340 mA`) directly into solid `In2.Cu GND`.
  - **`U7.2 -> GND` (USB ESD return) & `/Power/USB_DM_C`:** Preserved verbatim from `f-usbc` (`2×` parallel `GND` vias `(102.470, 110.730)` inside `J1.S1` NW & `(102.126, 110.639)`, and **`0` `F.Cu` segments** on `/Power/USB_DM_C`).
  - **`U13` (`RX8130CE:BB`) `*1` crystal inspection keepout (`RX8130_xtal_end`):** **`0` `B.Cu` tracks, vias, or pours** inside `[114.30..115.20, 102.30..103.05] mm` (`no_tracks, no_vias, no_pour`), keeping `B.Cu` strictly clear of the `*1` internal-crystal inspection pads on the Pin `1–10` South short side (`rx8130ce.pdf` p. 1 & `ETM50E-10` Fig. 9 p. 11) while `/MCU/ACC_SCL` (`U13.2`), `/MCU/ACC_SDA` (`U13.3`), and `/MCU/RTC_INT` (`U13.6`) escape cleanly north/west.
  - **`VSYS` (`~340 mA` board total), `+3V3` (`~40 mA` + `1.5 µA` RTC), & `GND`:** solid unbroken `In5.Cu` (`592.880 mm²` `VSYS`, `215.625 mm²` `+3V3`) and `In2.Cu` (`840.356 mm²` `GND`) planes (`1` whole piece each).
- [x] **Plane integrity & locked-PDN preservation check (`compare_with_parent.py`):**
  - **`236/236` front parts (`D1..D235` + `Q2`) at `0.0000 mm / 0.00°` delta.**
  - **`147/147` locked RP2350 decoupling/DVDD/LDO/FB tracks survived 100% intact.**
  - **`0` split pieces (`dPcs = +0`) across all 9 copper zones** vs `f-usbc` (`In2.Cu plane GND = 1 pc`, `In5.Cu plane VSYS = 1 pc`, `In5.Cu plane 3V3 = 1 pc`, `B.Cu RP2350 ring = 1 pc`, `B.Cu RP2350 band = 6 pcs`).
  - **`83.2%` (`5,362 / 6,441`)** of `f-usbc`'s copper items preserved verbatim; total vias = **`918`** (`+32` vs `f-usbc`'s `886`).
  - **`J1` NPTH 8-layer clearances:** **`≥ 0.201 mm` across all 8 layers** (`NPTH #1` min `0.201 mm` to `In2/In5` planes, `0.203 mm` on `In1.Cu`, `0.220 mm` to `D234.4`; `NPTH #2` min `0.201 mm` to `In2/In5` planes, `0.210 mm` on `F.Cu`).
- [x] **Every warning explained:** `0` DRC warnings; `nets_check.py --routed` `197` warnings (`+2` vs `f-usbc`: `RTC_INT` `1` via -> `2` vias and `RTC_VOUT` short local `1.24 mm` `B.Cu` decap link) explained in [phase5.md](phase5.md).
- [x] **Per-layer copper renders reviewed (`8` layers):** [F.Cu.png](../../renders/round-pendant-f-usbc-rtc/F.Cu.png), [In1.Cu.png](../../renders/round-pendant-f-usbc-rtc/In1.Cu.png), [In2.Cu.png](../../renders/round-pendant-f-usbc-rtc/In2.Cu.png), [In3.Cu.png](../../renders/round-pendant-f-usbc-rtc/In3.Cu.png), [In4.Cu.png](../../renders/round-pendant-f-usbc-rtc/In4.Cu.png), [In5.Cu.png](../../renders/round-pendant-f-usbc-rtc/In5.Cu.png), [In6.Cu.png](../../renders/round-pendant-f-usbc-rtc/In6.Cu.png), [B.Cu.png](../../renders/round-pendant-f-usbc-rtc/B.Cu.png).
- [x] **PCB view regenerated with copper viewer:** [viewer/round-pendant-f-usbc-rtc.html](../../../viewer/round-pendant-f-usbc-rtc.html).

---

## 1. Verbatim Routing Verification Outputs

### A. Strict KiCad DRC (`kicad-cli pcb drc --severity-all --schematic-parity`)
```text
Found 0 violations
Found 0 unconnected items
Found 2 schematic parity issues
DRC violations: 0 unconnected: 0 parity: 2
  - Pad net (unconnected-(U3-GPIO28/ADC2-Pad42)) doesn't match net given by schematic (unconnected-(U3-GPIO28{slash}ADC2-Pad42)).
  - Pad net (unconnected-(U3-GPIO29/ADC3-Pad43)) doesn't match net given by schematic (unconnected-(U3-GPIO29{slash}ADC3-Pad43)).
```

### B. `copper_audit.py` & `pad_joints_fixed.py`
```text
hw/round-pendant/f-usbc-rtc/round-pendant.kicad_pcb: tracks=5883 vias=918 | dangling=0 cap_gap=0 mid_graze/stubs=0 off_via=0 morph_necks(<86um)=0 acute_slivers=0 collinear_dups=0 micro_segs(<40um)=229 strip_zones=0 zone_intrusions=2

pad_joints: round-pendant.kicad_pcb: 1433 SMD pads, joints under 0.09 mm:

  PASS: 0 thin pad joints
```

### C. `compare_with_parent.py` (Footprint Parity, Locked Tracks, Track/Via Delta, Zone Piece Counts, `RX8130_xtal_end` & NPTH Clearances)
```text
=== 1. FOOTPRINT PARITY (f-usbc-rtc vs f-usbc) ===
  Front parts unchanged: 236/236 (235 LEDs + Q2, max delta 0.0000 mm / 0.00 deg)
  Back parts moved/swapped: 15 (BT1, C40, C43, C6, C7, Q1, R1, R10, R11, R12, R2, R8, R9, TP3, U8)
  New back parts added: 4 (C75, C76, R32, U13)

=== 2. LOCKED RP2350 DECOUPLING TRACKS ===
  Survived intact: 147/147 (locked=147/147)

=== 3. COPPER TRACKS & VIAS (F-USBC vs F-USBC-RTC) ===
  Board F-USBC    :  886 vias, 5555 track segs ( 4465.80 mm)
  Board F-USBC-RTC:  918 vias, 5883 track segs ( 4639.94 mm)
  Delta           :  +32 vias, +328 track segs ( +174.14 mm)
  Identical copper items preserved verbatim from F-USBC: 5362/6441 (83.2%)

=== 4. ZONE PIECE COUNTS & FILLED AREAS (F-USBC vs F-USBC-RTC) ===
  Idx Zone Name          Net              Layer   | P pcs    P mm^2 | R pcs    R mm^2 | dPcs    dArea
  ------------------------------------------------------------------------------------------------
    0 vendor +1V1        +1V1             B.Cu    |     1     2.280 |     1     2.280 |   +0   +0.000
    2 vendor /MCU/VREG_LX /MCU/VREG_LX     B.Cu    |     1     2.296 |     1     2.296 |   +0   +0.000
    4 vendor +3V3        +3V3             B.Cu    |     1     0.597 |     1     0.597 |   +0   +0.000
    5 RP2350 band        +3V3             B.Cu    |     6     7.529 |     6     7.529 |   +0   +0.000
    6 RP2350 ring        +1V1             B.Cu    |     1     6.437 |     1     6.437 |   +0   +0.000
    9 vendor GND         GND              B.Cu    |     1     1.633 |     1     1.633 |   +0   +0.000
   11 plane GND          GND              In2.Cu  |     1   847.497 |     1   840.356 |   +0   -7.141
   13 plane 3V3          +3V3             In5.Cu  |     1   215.756 |     1   215.625 |   +0   -0.132
   14 plane VSYS         VSYS             In5.Cu  |     1   600.368 |     1   592.880 |   +0   -7.487

=== 5. RX8130_xtal_end B.Cu KEEPOUT AUDIT ===
  B.Cu tracks/vias intruding RX8130_xtal_end [114.30..115.20, 102.30..103.05]: 0 (MUST BE 0)

=== 6. J1 NPTH 8-LAYER CLEARANCE AUDIT ===
  NPTH #1: center=(109.953, 108.684) mm, drill=0.65 mm (r=0.325 mm)
    F.Cu  : min clearance = 0.220 mm  -> Pad D234.4 (/Driver 5 and matrix/CS5_16)
    B.Cu  : min clearance = 0.247 mm  -> Pad J1.A1B12 (GND)
    In1.Cu: min clearance = 0.203 mm  -> Track (/Driver 5 and matrix/CS5_16)
    In2.Cu: min clearance = 0.201 mm  -> Zone 'plane GND' (GND)
    In3.Cu: min clearance = 0.261 mm  -> Via (/Driver 5 and matrix/CS5_16) @(109.242,108.689) [cu]
    In4.Cu: min clearance = 0.261 mm  -> Via (/Driver 5 and matrix/CS5_16) @(109.242,108.689) [cu]
    In5.Cu: min clearance = 0.201 mm  -> Zone 'plane VSYS' (VSYS)
    In6.Cu: min clearance = 0.261 mm  -> Via (/Driver 5 and matrix/CS5_16) @(109.242,108.689) [cu]
  NPTH #2: center=(104.671, 111.030) mm, drill=0.65 mm (r=0.325 mm)
    F.Cu  : min clearance = 0.210 mm  -> Track (/Driver 2 and matrix/SW2_3)
    B.Cu  : min clearance = 0.247 mm  -> Pad J1.B1A12 (GND)
    In1.Cu: min clearance = 0.435 mm  -> Via (/Driver 2 and matrix/SW2_3) @(104.717,111.914) [cu]
    In2.Cu: min clearance = 0.201 mm  -> Zone 'plane GND' (GND)
    In3.Cu: min clearance = 0.258 mm  -> Track (/Driver 2 and matrix/CS2_7)
    In4.Cu: min clearance = 0.307 mm  -> Track (/Power/CC2)
    In5.Cu: min clearance = 0.201 mm  -> Zone 'plane VSYS' (VSYS)
    In6.Cu: min clearance = 0.297 mm  -> Track (/Power/USB_DM_C)
```
