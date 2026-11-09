# Gate 7: routing (`round-pendant-f-usbc`)

Status: **passed**
Parent board baseline compared against: **Variant F** ([hw/round-pendant/f/round-pendant.kicad_pcb](../../../hw/round-pendant/f/round-pendant.kicad_pcb)), with routing dispositions in [design/decisions.md](../../decisions.md) (`2026-11-08`).

---

## Checklist (`references/routing.md` §Gate checklist)

- [x] **DRC `0` errors, `0` warnings, `0` unrouted (`kicad-cli pcb drc --severity-all --schematic-parity`):** **`Found 0 violations`, `Found 0 unconnected items`** (verbatim output below).
- [x] **Schematic parity:** `0` functional differences — only the **2 inherited Variant E/F `U3` pin 42/43 `{slash}` name mismatches** on unconnected pins (`GPIO28/ADC2` vs `GPIO28{slash}ADC2`, `GPIO29/ADC3` vs `GPIO29{slash}ADC3`), explicitly named below and never hidden ([decisions.md](../../decisions.md)).
- [x] **`pad_joints_fixed.py` passes (no SMD pad joint under `0.09 mm` fab minimum):** **`PASS: 0 thin pad joints`** across all `1,416` net-assigned SMD pads (`+8` SMD pads vs Variant F's `1,408`). *(Uses `scripts/crunch/placement/pad_joints_fixed.py`, which handles `B.Cu` mirrored pads accurately.)*
- [x] **`copper_audit.py` passes all routing & strip-zone checks:** `tracks=5555 vias=886 | dangling=0 cap_gap=0 mid_graze/stubs=0 off_via=0 morph_necks(<86um)=0 acute_slivers=0 collinear_dups=0 strip_zones=0` (`2` inherited `B.Cu` vendor-zone intrusions `vendor +1V1` and `vendor GND` from Variant E/F, identical to Variant F's `zone_intrusions=2`).
- [x] **Current capacity & via-count check passes:**
  - **`VBUS` (`500 mA` max):** **`0` vias** on the `500 mA` `J1 -> C1 -> U5.13` `0.25 mm` `1 oz` `B.Cu` charger path (`R_60C = 4.44 mΩ`, `Vdrop = 2.22 mV @ 500 mA`; `IPC-2221` 1 oz outer `0.25 mm` > `900 mA` at `ΔT = 10 °C`); `2` `0.30/0.15 mm` vias sit in series only on the `U7.5` TVS clamp branch.
  - **`VBAT` (`340 mA` max cont / `297 mA` charge / `1.0 A` brief transient):** **`2×` parallel `0.30/0.15 mm` vias** at `BT1.1` (`(100.018, 114.939)` & `(100.860, 115.700)`) feeding `0.30 mm` `In3.Cu` (`R_60C = 55.01 mΩ`, `Vdrop = 18.70 mV @ 340 mA`). Plane-cooled `0.30 mm` `0.5 oz` `In3.Cu` (`0.076–0.170 mm` from solid `In2.Cu GND` and `In5.Cu VSYS`) exceeds **`0.80 A` IPC-2152 internal ampacity** (`> 2.3×` continuous demand; widening beyond `0.30 mm` violates `0.200 mm` matrix via `hole_clearance`, justified in [decisions.md](../../decisions.md)).
  - **`/Power/BAT_N` & `U8.1..3 -> GND` (`340 mA` cont):** `/Power/BAT_N` has **`0` vias** (`4.04 mm` direct `0.30 mm` `1 oz` `B.Cu` from `BT1.2` to `U8.4/5`, `R_60C = 3.25 mΩ`), and `U8.1..3` exits via `0.25–0.30 mm` `B.Cu` segments into **`2×` `GND` vias** (`(97.263, 115.721)` [`0.25/0.15 mm`] & `(97.017, 114.689)` [`0.30/0.15 mm`], `R_60C = 1.12 mΩ` via-to-plane / `3.07 mΩ` pad-center-to-plane, `1.04 mV @ 340 mA`) directly into `In2.Cu GND`.
  - **`U7.2 -> GND` (USB ESD return) & `/Power/USB_DM_C`:** `U7.2` traverses `2.21 mm` of narrow `B.Cu` microstrip into `J1.S1` NW's `2.30 × 1.80 mm` solid copper pad (`L_shield ≈ 1.09 nH` to USB cable shield) and **`2×` parallel `GND` vias** (`(102.470, 110.730)` inside `J1.S1` & `(102.126, 110.639)`, `L_eff ≈ 1.39 nH` into `In2.Cu GND`; `0` legal 8-layer TH via pockets exist within `2.00 mm` of `U7.2`), and `/Power/USB_DM_C` stays strictly on `B.Cu`/`In6.Cu` (**`0` `F.Cu` segments**).
  - **`VSYS` (`~340 mA` board total) & `+3V3` (`~40 mA`):** solid `In5.Cu` planes (`600.368 mm²` and `215.756 mm²`, `1` whole piece each).
  - **`GND`:** solid unbroken `In2.Cu` reference plane (`847.497 mm²`, **`1` whole piece**).
- [x] **Plane integrity & Variant F locked-PDN preservation check (`compare_with_f.py`):**
  - **`147/147` locked RP2350 decoupling/DVDD/LDO/FB tracks survived 100% intact.**
  - **`0` split pieces (`dPcs = +0`) across all 9 zones** vs Variant F (`In2.Cu plane GND = 1 pc`, `In5.Cu plane VSYS = 1 pc`, `In5.Cu plane 3V3 = 1 pc`, `B.Cu RP2350 ring = 1 pc`, `B.Cu RP2350 band = 6 pcs` identical to F).
  - **`85.6%` (`5,261 / 6,144`)** of Variant F's tracks and vias preserved verbatim (primary rip-up crescent `X ∈ [91.3, 114.9], Y ∈ [105.0, 118.8] mm`, with minor route adjustments spanning `X ∈ [90.08, 117.87], Y ∈ [93.29, 118.59] mm`); total vias = **`886`** (`+10` vs Variant F's `876`).
  - **`J1` NPTH 8-layer clearances:** `NPTH #1 In3.Cu` clearance widened from `0.2002 mm` to **`0.304 mm`**; all 8 layers `≥ 0.201 mm`.
- [x] **Every warning explained:** `0` DRC warnings; `nets_check.py --routed` `195` warnings explained in [phase5.md](phase5.md).
- [x] **Per-layer copper renders reviewed (`8` layers):** [F.Cu.png](../../renders/round-pendant-f-usbc/F.Cu.png), [In1.Cu.png](../../renders/round-pendant-f-usbc/In1.Cu.png), [In2.Cu.png](../../renders/round-pendant-f-usbc/In2.Cu.png), [In3.Cu.png](../../renders/round-pendant-f-usbc/In3.Cu.png), [In4.Cu.png](../../renders/round-pendant-f-usbc/In4.Cu.png), [In5.Cu.png](../../renders/round-pendant-f-usbc/In5.Cu.png), [In6.Cu.png](../../renders/round-pendant-f-usbc/In6.Cu.png), [B.Cu.png](../../renders/round-pendant-f-usbc/B.Cu.png).
- [x] **PCB view regenerated with copper viewer:** [viewer/round-pendant-f-usbc.html](../../../viewer/round-pendant-f-usbc.html).

---

## 1. Verbatim Routing Verification Outputs

### A. Strict KiCad DRC (`kicad-cli pcb drc --severity-all --schematic-parity`, `drc_final.json`)
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
hw/round-pendant/f-usbc/round-pendant.kicad_pcb: tracks=5555 vias=886 | dangling=0 cap_gap=0 mid_graze/stubs=0 off_via=0 morph_necks(<86um)=0 acute_slivers=0 collinear_dups=0 micro_segs(<40um)=203 strip_zones=0 zone_intrusions=2

pad_joints: round-pendant.kicad_pcb: 1416 SMD pads, joints under 0.09 mm:

  PASS: 0 thin pad joints
```

### C. `compare_with_f.py` (Locked Tracks, Track/Via Delta, Zone Piece Counts & Areas, 8-Layer NPTH Clearances)
```text
=== 2. LOCKED RP2350 DECOUPLING TRACKS ===
  Survived intact: 147/147 (locked=147/147)

=== 3. COPPER TRACKS & VIAS (F vs F-USBC) ===
  Board F     :  876 vias, 5268 track segs ( 4426.68 mm)
  Board F-USBC:  886 vias, 5555 track segs ( 4465.80 mm)
  Delta       :  +10 vias, +287 track segs (  +39.12 mm)
  Identical copper items preserved verbatim from F: 5261/6144 (85.6%)

=== 4. ZONE PIECE COUNTS & FILLED AREAS (F vs F-USBC) ===
  Idx Zone Name          Net              Layer   | F pcs    F mm^2 | U pcs    U mm^2 | dPcs    dArea
  ------------------------------------------------------------------------------------------------
    0 vendor +1V1        +1V1             B.Cu    |     1     2.280 |     1     2.280 |   +0   +0.000
    1 vendor /MCU/VREG_LX /MCU/VREG_LX     B.Cu    |     1     2.296 |     1     2.296 |   +0   +0.000
    3 vendor +3V3        +3V3             B.Cu    |     1     0.597 |     1     0.597 |   +0   +0.000
    4 RP2350 band        +3V3             B.Cu    |     6     7.529 |     6     7.529 |   +0   +0.000
    5 RP2350 ring        +1V1             B.Cu    |     1     6.437 |     1     6.437 |   +0   +0.000
    8 vendor GND         GND              B.Cu    |     1     1.633 |     1     1.633 |   +0   +0.000
   10 plane GND          GND              In2.Cu  |     1   849.289 |     1   847.497 |   +0   -1.792
   12 plane 3V3          +3V3             In5.Cu  |     1   216.146 |     1   215.756 |   +0   -0.390
   13 plane VSYS         VSYS             In5.Cu  |     1   603.541 |     1   600.368 |   +0   -3.174

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
    F.Cu  : min clearance = 0.214 mm  -> Track (/Driver 2 and matrix/CS2_12)
    B.Cu  : min clearance = 0.247 mm  -> Pad J1.B1A12 (GND)
    In1.Cu: min clearance = 0.293 mm  -> Via (/Driver 2 and matrix/SW2_3) @(104.892,111.739) [cu]
    In2.Cu: min clearance = 0.201 mm  -> Zone 'plane GND' (GND)
    In3.Cu: min clearance = 0.258 mm  -> Track (/Driver 2 and matrix/CS2_7)
    In4.Cu: min clearance = 0.293 mm  -> Via (/Driver 2 and matrix/SW2_3) @(104.892,111.739) [cu]
    In5.Cu: min clearance = 0.201 mm  -> Zone 'plane VSYS' (VSYS)
    In6.Cu: min clearance = 0.211 mm  -> Track (/Power/CC2)
```

---

## 2. Independent Fresh-Context Review History (`agy` `gemini-4-argon-high`)

### Round 1 Review Summary & Dispositions
- **`[M1]` (`VBAT` single via at `BT1.1` & `0.30 mm` `In3.Cu` ampacity):** **FIXED + JUSTIFIED in [decisions.md](../../decisions.md) (`2026-11-08`)** — added a **2nd parallel `0.30/0.15 mm` `VBAT` via** at `(100.860, 115.700)` beside `BT1.1` (`R_60C = 55.01 mΩ`, `18.70 mV @ 340 mA`), and justified `0.30 mm` `In3.Cu` via IPC-2152 plane-cooled internal ampacity (`> 0.80 A` vs `0.34 A` continuous; widening violates `0.200 mm` `hole_clearance`).
- **`[M2]` (`U8.1..3 -> GND` single `0.25/0.15 mm` via & `0.20 mm` trace):** **FIXED** — widened `U8.1..3` `GND` bridge (`0.25–0.30 mm` `B.Cu`) and added a **2nd `0.30/0.15 mm` `GND` via** at `(97.017, 114.689)` alongside `(97.263, 115.721)` (`R_60C = 1.12 mΩ` via-to-plane / `3.07 mΩ` pad-center, `1.04 mV @ 340 mA`).
- **`[M3]` (`U7.2` ESD `GND` return single via):** **FIXED + JUSTIFIED** — added a **2nd parallel `GND` via** at `(102.470, 110.730)` inside `J1.S1` NW's `2.30 × 1.80 mm` copper pad (`L_shield ≈ 1.09 nH`, `L_eff ≈ 1.39 nH`; `0` legal 8-layer TH via pockets exist within `2.00 mm` of `U7.2`, and downstream `R14/R15 = 27 Ω` isolate `U3`).
- **`[m1]` (`USB_DM_C` `1.10 mm` `F.Cu` hop & `In5.Cu` split note):** **FIXED** — moved `USB_DM_C`'s `1.10 mm` segment from `F.Cu` to `In6.Cu` (`0` `F.Cu` USB copper; `7.76–8.86 mm` stub = `~117 ps << 4 ns` FS rise time).
- **`[m2]` (`0.2002 mm` `In3.Cu` NPTH #1 margin):** **FIXED** — split & nudged `CS5_16` on `In3.Cu` via `(109.450, 108.150)` so clearance to NPTH #1 rose to **`0.304 mm`**.
- **`[m4]` (`VBUS` `0`-via prose, modified copper bounding box, `.kicad_dru` header):** **FIXED** in [round-pendant.kicad_dru](../../../hw/round-pendant/f-usbc/round-pendant.kicad_dru) and this gate file.

### Round 2 Re-Review (`agy` `gemini-4-argon-high`)
- **Verdict:** **`Gate 7 Verdict: PASS (0 BLOCKER, 0 MAJOR, 1 MINOR, 3 NOTE)`** (`review_r2_phase7.txt`).
- **Summary & Minor Cleanup:** Independently verified fresh KiCad `9.0.8` DRC (`0` violations, `0` warnings, `0` unconnected, `2` inherited `U3.42/43` `{slash}` NC strings), `0` thin pad joints across all `1,416` SMD pads (`min = 0.126 mm`), `copper_audit.py` clean (`0` dangling stubs, `0` off-via grazes, `0` strip zones), `VBUS`/`VBAT`/`BAT_N`/`U8.1..3`/`U7.2` ampacity & nodal resistance, `9/9` whole planes matching Variant F (`85.63%` verbatim F copper + all `147` locked RP2350 PDN tracks intact), and all `16` (`2×8L`) `J1` NPTH clearances `≥ 0.2005 mm` (`NPTH #1 In3.Cu` = `0.3044 mm`). Clarified `MINOR-1` (`0.25–0.30 mm` `U8.1..3` segments, `3.07 mΩ` pad-center-to-plane / `1.04 mV @ 340 mA`) above.
