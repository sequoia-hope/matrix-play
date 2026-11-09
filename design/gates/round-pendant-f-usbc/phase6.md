# Gate 6: placement (`round-pendant-f-usbc`)

Status: **passed**
Parent gate cited for unchanged northern/central/LED placement: [design/gates/phase6.md](../phase6.md), with `f-usbc` southern placement dispositions in [design/decisions.md](../../decisions.md) (`2026-11-08`).

---

## Checklist (`references/placement.md` §Gate checklist)

- [x] **Fixed items match [brief-f-usbc.md](../../brief-f-usbc.md) and are locked:** `Ø38.000 mm` `Edge.Cuts` circle, all `6` keepout rule areas, and all `240` fixed footprints (`D1..D235` + `Q2` at `0.0000 mm / 0.00°` delta from Variant F, `SW1`, `SW2`, `BT1` at `(100.000, 117.100, 180.00°)`, and `J1` `TYPE-C-31-M-22` at `(107.787, 110.926, -156.05°)`) are **locked** in `round-pendant.kicad_pcb` (`U1..U6` and `U9..U12` also `0.0000 mm` delta from Variant F).
- [x] **Placement check passes (`placement_check.py`):** **`PASS: 0 errors, 0 warnings`** (verbatim output below), plus `sync_check.py` **`PASS: 0 errors, 0 warnings`** and `kicad-cli sch erc --severity-all` **`0` violations across `8` sheets**.
- [x] **Datasheet layout guidelines followed per part (including displaced southern I/O block):**
  - **`J1` (`TYPE-C-31-M-22`, `C530612`, [parallelogram-io.md](../../parts/parallelogram-io.md) §1 & `type-c-31-m-22.pdf`):** Seated at SSE rim (`23.95°` E of S, `8.35°` non-radial skew from mouth midpoint `(109.865, 115.605)`) so a standard `12.35 × 6.50 mm` USB-C plug overmold clears the convex `Ø38.0 mm` rim by **`+1.066 mm` nominal (`+0.666 mm` worst-case)**; closest `S1` SMD shell pad corner sits **`0.440–0.530 mm`** inside `Edge.Cuts`; both `Ø0.65 mm` NPTH locating holes clear `F.Cu` LED pads by **`0.220 mm`** (`D234.4`, `D74.3`).
  - **`U7` (`USBLC6-2P6`, `C15999`, [usb.md](../../parts/usb.md)):** Placed at `(100.100, 112.400, 113.95°)` inline behind the fixed `2.0 mm`-pitch front LED escape-via array between `J1` (`USB_DP_C` `11.94 mm` `0`-via `B.Cu`; `USB_DM_C` `18.01 mm` on `B.Cu`/`In6.Cu` with **`0` `F.Cu` copper**) and `R14, R15` (`27 Ω` at `U3`; `USB_DP` `14.95 mm` `0`-via `B.Cu`, `USB_DM` `13.52 mm` `0`-via `B.Cu`), entering `J1.S1` NW's `2.30 × 1.80 mm` solid copper pad (`L_shield ≈ 1.09 nH`) with **`2×` parallel `GND` vias** (`(102.470, 110.730)` & `(102.126, 110.639)`, `L_eff ≈ 1.39 nH` to `In2.Cu`) and `C1 = 1 µF` clamping `VBUS` `1.78 mm` from `U5.13` ([decisions.md](../../decisions.md)).
  - **`U5` (`BQ24073RGTR`, [charger.md](../../parts/charger.md)) + `C1` + `R5`:** `U5` unchanged at `(103.400, 106.000, 0°)` with solid `2.89 mm²` `GND` EP (`2` thermal vias, `0` foreign vias); relocated `C1` (`1 µF VBUS`) sits **`1.78 mm`** pad-center-to-pad-center from `U5.13` (`IN`, improved over F's `4.31 mm`), and `R5` (`3.6 kΩ ILIM`) sits immediately east of `U5.12` at `(107.500, 106.400, 90°)`.
  - **`BT1` (`BatteryPads`, `1.60 × 2.40 mm`) + `U8` (`XB9901A`, [battery.md](../../parts/battery.md)) + `C6` + `R8` + `TP3`:** `BT1.1` (`VBAT`) connects via **`2×` parallel `0.30/0.15 mm` vias**; `U8` sits at `(96.400, 116.400, -90°)` west of `BT1.2` (`0.300 mm` CAD copper/`B.Mask` gap = `3.0×` JLCPCB's `0.10 mm` ENIG dam capability, `~0.20–0.22 mm` physical LPI web + temporary Kapton masking during wire attach & mandatory pre-power ohmmeter check in [bringup-f-usbc.md](../../bringup-f-usbc.md) §2/§5), giving a **`4.04 mm`, `0`-via `0.30 mm` `B.Cu`** `BAT_N` path (`R_60C = 3.25 mΩ`) and **`2×` parallel `GND` vias** (`R_60C = 1.12 mΩ` via-to-plane / `3.07 mΩ` pad-center), with `C6` (`100 nF`) at **`1.08 mm`** from `U8.6` (`VDD`) and `R8` (`100 Ω`) beside `BT1.1`. `R1, R2` (`5.1 kΩ` `0 Hz` DC `CC1/CC2` pull-downs) remain at Variant F's SSW sites per minimum-displacement rule ([decisions.md](../../decisions.md)).
  - **Unchanged northern/central blocks (`U3 RP2350A`, `Y1`, `L1`, `U4`, `U6`, `U9`, `U1/U2/U10/U11/U12`):** Identical to Variant F (`147/147` locked RP2350 decoupling/LDO/FB tracks and all rule areas preserved verbatim).
- [x] **Rule areas & solid EPs verified (`verify_solid_ep_and_netclasses.py`):** `U3.61` (`11.56 mm²`, `9` GND vias, `0` foreign vias), `U5.17` (`2.89 mm²`, `2` GND vias, `0` foreign vias), `U3` `+1V1` ring whole (`1` piece, `6.437 mm²`), `L1`/`VREG_LX` cutouts preserved.
- [x] **Visual review on 2D/3D renders & PCB viewer regenerated:** [top.png](../../renders/round-pendant-f-usbc/top.png), [bottom.png](../../renders/round-pendant-f-usbc/bottom.png), [3d-top.png](../../renders/round-pendant-f-usbc/3d-top.png), [3d-bottom.png](../../renders/round-pendant-f-usbc/3d-bottom.png), [assembly-bottom.png](../../renders/round-pendant-f-usbc/assembly-bottom.png), and `viewer/round-pendant-f-usbc.html`.

---

## 1. Verbatim Placement, Sync & ERC Check Outputs

### A. `placement_check.py hw/round-pendant/f-usbc`
```text
placement_check: hw/round-pendant/f-usbc/round-pendant.kicad_pcb
  Y1 pad 1 (Net-(U3-XIN)) is 5.8 mm from its IC pin
  Y1 pad 3 (Net-(C24-Pad1)) is 3.9 mm from its IC pin
  ratsnest (MST, all nets except GND): 3109 mm over 212 nets

  decoupler -> pin, pad centre to pad centre
    C1    -> U5.13   VBUS        1.78 mm
    C10   -> U3.20   +3V3        2.40 mm
    C11   -> U3.30   +3V3        1.60 mm
    C12   -> U3.38   +3V3        1.87 mm
    C13   -> U3.53   +3V3        3.10 mm
    C14   -> U3.44   +3V3        1.69 mm
    C16   -> U3.49   +3V3        1.17 mm
    C17   -> U3.46   /MCU/VREG_AVDD  2.83 mm
    C18   -> U3.50   +1V1        2.13 mm
    C19   -> U3.23   +1V1        1.63 mm
    C2    -> U5.10   VSYS        2.82 mm
    C20   -> U3.6    +1V1        1.60 mm
    C21   -> U3.39   +1V1        1.69 mm
    C22   -> U4.8    +3V3        5.51 mm
    C25   -> U9.9    +3V3        1.72 mm
    C26   -> U9.9    +3V3        2.08 mm
    C27   -> U9.10   +3V3        3.51 mm
    C3    -> U6.4    VSYS        1.82 mm
    C30   -> U1.A3   VSYS        3.42 mm
    C31   -> U1.A3   VSYS        2.36 mm
    C32   -> U1.A3   VSYS        1.37 mm
    C33   -> U1.F5   VSYS        1.53 mm
    C34   -> U1.F5   VSYS        2.46 mm
    C4    -> U6.1    +3V3        1.08 mm
    C40   -> U2.A3   VSYS        2.40 mm
    C41   -> U2.A3   VSYS        2.22 mm
    C42   -> U2.A3   VSYS        1.26 mm
    C43   -> U2.F5   VSYS        4.67 mm
    C44   -> U2.F5   VSYS        1.23 mm
    C5    -> U5.2    VBAT        3.27 mm
    C51   -> U10.A3  VSYS        2.36 mm
    C52   -> U10.A3  VSYS        1.37 mm
    C53   -> U10.F5  VSYS        1.53 mm
    C54   -> U10.F5  VSYS        2.46 mm
    C6    -> U8.6    Net-(U8-VDD)  1.08 mm
    C61   -> U11.A3  VSYS        2.36 mm
    C62   -> U11.A3  VSYS        1.37 mm
    C63   -> U10.F5  VSYS        1.53 mm
    C64   -> U11.F5  VSYS        2.42 mm
    C71   -> U12.A3  VSYS        2.36 mm
    C72   -> U12.A3  VSYS        1.37 mm
    C73   -> U12.F5  VSYS        1.53 mm
    C74   -> U12.F5  VSYS        2.46 mm
    C8    -> U3.1    +3V3        1.60 mm
    C9    -> U3.11   +3V3        1.60 mm

  PASS: 0 errors, 0 warnings
```

### B. `sync_check.py` & `kicad-cli sch erc --severity-all`
```text
sync_check: hw/round-pendant/f-usbc
  schematic round-pendant.kicad_sch: 342 symbols (0 excluded from board)
  board round-pendant.kicad_pcb: 342 footprints (0 board-only)
  BOM bom-jlcpcb.csv: 333 designators
  CPL cpl-jlcpcb.csv: 333 placements
  333 parts to build; required fields: LCSC
  PASS: 0 errors, 0 warnings

Found 0 violations
Saved ERC Report to /tmp/fusbc_erc.json
ERC sheets: 8 violations: 0
```

---

## 2. Independent Fresh-Context Review History (`agy` `gemini-4-argon-high`)

### Round 1 Review Summary & Dispositions
- **`MAJOR-1` (`U7` `USBLC6-2P6` `F.Cu` excursion, `GND` return Y-network inductance, & 8-layer pocket proof):** **COPPER FIXED + PLACEMENT/POCKET PROVEN in [decisions.md](../../decisions.md) (`2026-11-08`)** — moved `USB_DM_C`'s `1.10 mm` `F.Cu` segment to `In6.Cu` (**`0` unclamped `F.Cu` USB copper**) and added a **2nd parallel `0.25/0.15 mm` `GND` via** at `(102.470, 110.730)` inside `J1.S1` NW's `2.30 × 1.80 mm` solid copper pad (`dist = 0.000 mm`) alongside `(102.126, 110.639)`. An exhaustive 8-layer `0.25/0.15 mm` via scan proves **zero legal TH via pockets exist anywhere within `2.00 mm` of `U7.2` `(100.475, 113.245)`** (for example, `(100.68, 112.75)` collides `-0.027 mm` with fixed `D91.3` on `F.Cu`, `-0.112 mm` with `U7.1` on `B.Cu`, `-0.034 mm` with `SW2_1` on `In1.Cu`, and `+0.031 mm < 0.090 mm` with `CS2_13` on `In3.Cu`). `U7.2` traverses **`2.21 mm` of narrow `B.Cu` microstrip** (`0.926 mm @ 0.12 mm` + `1.033 mm @ 0.15 mm` + `0.254 mm @ 0.20 mm` over `h = 0.262 mm` `In5.Cu` AC reference, `L_stem ≈ 0.89 nH`) directly into **`J1.S1`'s `2.30 × 1.80 mm` solid copper pad** (`L_shield ≈ 1.09 nH` to the USB cable shield; `L_eff ≈ 1.39 nH` through the `2×` parallel vias into `In2.Cu GND`), while downstream **`R14/R15 = 27 Ω`** form a two-stage ESD clamp limiting residual current into `U3`'s internal clamp to `~2.4 A` for `< 1 ns`, and `C1 = 1 µF` (`X5R`) clamps `VBUS` locally `1.78 mm` from `U5.13`.
- **`MAJOR-2` (`U8` `-90°` orientation & `0.300 mm` CAD copper/`B.Mask` gap to hand-soldered `BT1.2`):** **COPPER IMPROVED + JUSTIFIED in [decisions.md](../../decisions.md)** — bridged `U8.1..3` into a **2nd parallel `0.30/0.15 mm` `GND` via** at `(97.017, 114.689)` (`R_DC = 0.98 mΩ`). At `-90°`, `U8`'s `0.30 × 0.60 mm` pads extend to `x_east = 97.300 mm` vs `BT1.2` `x_west = 97.600 mm`, giving a **`0.300 mm` CAD copper/`B.Mask` gap** (**`3.0×` JLCPCB's `0.10 mm` ENIG dam min**, `~0.20–0.22 mm` physical LPI web after pullback). Rotating/shifting `U8`+`C6` west would displace `R1/R2/C41/C42` outside the minimum-displacement region; instead, [bringup-f-usbc.md](../../bringup-f-usbc.md) (§0, §2, §5) mandates temporary Kapton masking over `U8` (`X ≤ 97.3 mm`) during `BT1` wire soldering plus an unpowered `BT1.2 <-> TP8 (GND)` ohmmeter open-circuit verification before waking `U8`.
- **`MAJOR-3` (`R1, R2` `CC1/CC2` resistors kept at Variant F SSW sites):** **JUSTIFIED in [decisions.md](../../decisions.md)** — per task Step 3 (*"move the displaced back parts the minimum needed"*), undisplaced parts `R1` and `R2` were intentionally left at Variant F's coordinates (`CC1`/`CC2` are `0 Hz` DC `5.1 kΩ` pull-downs, not high-speed signals, and `CC1` clears `BT1` by `0.114 mm > 0.090 mm` under intact ENIG soldermask).
- **`MINOR-1` (Fixed footprints, `Edge.Cuts`, & keepout rule areas unlocked):** **FIXED** — locked all `240` fixed footprints (`D1..D235, Q2, SW1, SW2, BT1, J1`), `Edge.Cuts`, and all `6` keepout rule areas in `round-pendant.kicad_pcb`.
- **`MINOR-2..4` & `NOTE-1` (Prose fixes: `8.35°` non-radial skew, `R14/R15 = 27 Ω`, `R8 = 100 Ω`, `BT1 = BatteryPads 1.60 × 2.40 mm`, `In4.Cu` `0` zones, route ripple up to `Y = 93.29 mm`):** **FIXED** in [brief-f-usbc.md](../../brief-f-usbc.md) and this gate file.

### Round 2 Re-Review (`agy` `gemini-4-argon-high`)
- **Verdict:** **`Gate 6 Verdict: PASS (0 BLOCKER, 0 MAJOR, 2 MINOR, 2 NOTE)`** (`review_r2_phase6.txt`).
- **Summary & Minor Cleanups:** Independently confirmed all `240` fixed footprints (`D1..D235`, `Q2`, `SW1`, `SW2`, `BT1`, `J1`), `Edge.Cuts`, and all `6` keepouts are `locked=True`, `0` `F.CrtYd`/`B.CrtYd` overlaps, solid EPs intact, **`0` legal `0.25/0.15 mm` TH via pockets `< 1.998 mm` from `U7.2`** (`2.21 mm` stem into `J1.S1` NW `2×` `GND` vias + `R14/R15 = 27 Ω` two-stage ESD clamp), and valid justification of the `0.300 mm` CAD (`~0.20–0.22 mm` LPI) `BT1.2 ↔ U8.1..3` gap (`C6` clears `R1` courtyard by `0.007 mm`). Fixed `MINOR-1` (updated lines 14 & 16 above to `L_eff ≈ 1.39 nH` and `0.300 mm` CAD gap), `MINOR-2` (added northward `BT1` wire-dressing & `y > 118.3 mm` iron-avoidance note over `CC1` in [bringup-f-usbc.md](../../bringup-f-usbc.md) §5), and `NOTE-1` (noted exact intermediate rim projection `y_local = +5.854 mm` at `x_local = -2.68 mm` -> `+0.977 mm` nominal / `+0.577 mm` WC overmold clearance in [brief-f-usbc.md](../../brief-f-usbc.md) §2).
