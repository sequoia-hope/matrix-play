# Gate 6: placement (`round-pendant-f-usbc-rtc`)

Status: **passed**
Parent placement baselines: [design/gates/round-pendant-f-usbc/phase6.md](../round-pendant-f-usbc/phase6.md) and [design/gates/phase6.md](../phase6.md).
Variant brief: [design/brief-f-usbc-rtc.md](../../brief-f-usbc-rtc.md).

---

## Checklist (`references/placement.md` §Gate checklist)

- [x] **Fixed items match [brief-f-usbc-rtc.md](../../brief-f-usbc-rtc.md) and are locked:** `Ø38.000 mm` `Edge.Cuts` circle, all `7` keepout rule areas (incl. **`RX8130_xtal_end`**), and all `240` fixed footprints (`D1..D235` + `Q2` at `0.0000 mm / 0.00°` delta from `f-usbc`, `SW1`, `SW2`, `J1` at `(107.787, 110.926, -156.05°)`, and `BT1` `A1251WR-S-2P` at `(89.200, 110.550, -28.00°)`) are **locked** in `round-pendant.kicad_pcb` (`U1..U7`, `U9..U12`, `L1`, `Y1` also `0.0000 mm / 0.00°` delta from `f-usbc`).
- [x] **Placement check passes (`placement_check.py`):** **`PASS: 0 errors, 0 warnings`** (verbatim output below), `0` `courtyards_overlap` in KiCad DRC, `sync_check.py` **`PASS: 0 errors, 0 warnings`**, and `kicad-cli sch erc --severity-all` **`0` violations across `8` sheets**.
- [x] **Datasheet layout guidelines followed per part:**
  - **`BT1` (`CJT A1251WR-S-2P`, `C225111`, [parallelogram-io.md](../../parts/parallelogram-io.md) §2 & `cjt-a1251.pdf`):** Seated at SW `(89.200, 110.550, -28.00°)` facing inward NNE (`+28°` E of N) with **`4.88 mm` nominal (`4.65 mm` min to `U4`, `5.85 mm` to `C22`) flat plug-insertion runway** (`> 4.00 ± 0.25 mm` `A1251H-2P` plug length), `12.60 mm²` `GND`-tied `MP` mechanical solder tabs (`1` via per tab; `13` under-body vias capped planar via `POFV = Yes` + `100%` LPI `B.Mask` tenting), and `3.20 mm` housing height matching `J1`.
  - **`U8` (`XB9901A`, [battery.md](../../parts/battery.md)) + `C6` + `R8`:** `U8` sits immediately SE of `BT1.2` at `(91.500, 114.800, -90.00°)` with `C6` (`100 nF`) at **`1.11 mm`** pad-to-pad from `U8.6` (`VDD`) and `2× 0.30/0.15 mm` parallel `GND` vias at `(92.440, 114.800)` & `(92.411, 114.428)`.
  - **`U13` (`Seiko Epson RX8130CE:BB`, `C1542426`, [rtc-rx8130ce.md](../../parts/rtc-rx8130ce.md) & `ETM50E-10`):** Seated in the vacant East pocket at `(114.750, 101.200, 0.00°)` (`0` existing parts moved; `0` `U12` WLCSP fanout vias disturbed):
    - `C75` (`100 nF` `+3V3` decoupler) sits **`1.23 mm`** straight east of `U13.8` (`VDD`).
    - `C76` (`1 µF` `RTC_VOUT` stabilization cap) sits **`1.23 mm`** straight east of `U13.9` (`VOUT`).
    - `R32` (`100 kΩ` `RTC_INT` pull-up) sits directly north at `(114.750, 98.350, 0.00°)`.
    - Locked `B.Cu` rule area **`RX8130_xtal_end`** (`[114.30..115.20, 102.30..103.05] mm`, `no_tracks, no_vias, no_pour`) keeps `B.Cu` copper strictly clear of `U13`'s Pin `1–10` `*1` crystal inspection short side (`ETM50E-10` Fig. 9 p. 11).
  - **`Q1, R9..R12, C7` (`VBAT_SENSE` divider) & `R1, R2` (`CC1/CC2` `5.1 kΩ`):** Grouped cleanly in the vacated 6-o'clock South pocket (`R1, R2` moved closer to `J1`).
  - **Unchanged northern/central/USB-C blocks (`U3 RP2350A`, `Y1`, `L1`, `U4`, `U5`, `U6`, `U7`, `U9`, `J1`, `U1/U2/U10/U11/U12`):** `100%` identical to `f-usbc` (`147/147` locked RP2350 decoupling tracks preserved verbatim).
- [x] **Rule areas & solid EPs verified:** `U3.61` (`11.56 mm²`, `9` `GND` vias, `0` foreign vias), `U5.17` (`2.89 mm²`, `2` `GND` vias, `0` foreign vias), `RP2350 ring` (`1` piece), `L1` cutouts, and `RX8130_xtal_end` (`0` intrusions) verified.
- [x] **Visual review on 2D/3D renders & PCB viewer:** [top.png](../../renders/round-pendant-f-usbc-rtc/top.png), [bottom.png](../../renders/round-pendant-f-usbc-rtc/bottom.png), [3d-top.png](../../renders/round-pendant-f-usbc-rtc/3d-top.png), [3d-bottom.png](../../renders/round-pendant-f-usbc-rtc/3d-bottom.png), [assembly-bottom.png](../../renders/round-pendant-f-usbc-rtc/assembly-bottom.png), and `viewer/round-pendant-f-usbc-rtc.html`.

---

## 1. Verbatim Placement, Sync & ERC Check Outputs

### A. `placement_check.py hw/round-pendant/f-usbc-rtc`
```text
placement_check: hw/round-pendant/f-usbc-rtc/round-pendant.kicad_pcb
  Y1 pad 1 (Net-(U3-XIN)) is 5.8 mm from its IC pin
  Y1 pad 3 (Net-(C24-Pad1)) is 3.9 mm from its IC pin
  ratsnest (MST, all nets except GND): 3168 mm over 215 nets

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
    C40   -> U2.A3   VSYS        2.55 mm
    C41   -> U2.A3   VSYS        2.22 mm
    C42   -> U2.A3   VSYS        1.26 mm
    C43   -> U2.F5   VSYS        3.10 mm
    C44   -> U2.F5   VSYS        1.23 mm
    C5    -> U5.2    VBAT        3.27 mm
    C51   -> U10.A3  VSYS        2.36 mm
    C52   -> U10.A3  VSYS        1.37 mm
    C53   -> U10.F5  VSYS        1.53 mm
    C54   -> U10.F5  VSYS        2.46 mm
    C6    -> U8.6    Net-(U8-VDD)  1.11 mm
    C61   -> U11.A3  VSYS        2.36 mm
    C62   -> U11.A3  VSYS        1.37 mm
    C63   -> U11.F5  VSYS        1.53 mm
    C64   -> U11.F5  VSYS        2.42 mm
    C71   -> U12.A3  VSYS        2.36 mm
    C72   -> U12.A3  VSYS        1.37 mm
    C73   -> U12.F5  VSYS        1.53 mm
    C74   -> U12.F5  VSYS        2.46 mm
    C75   -> U13.8   +3V3        1.23 mm
    C76   -> U13.9   /MCU/RTC_VOUT  1.23 mm
    C8    -> U3.1    +3V3        1.60 mm
    C9    -> U3.11   +3V3        1.60 mm

  PASS: 0 errors, 0 warnings
```

### B. `sync_check.py` & `kicad-cli sch erc --severity-all`
```text
sync_check: hw/round-pendant/f-usbc-rtc
  schematic round-pendant.kicad_sch: 346 symbols (0 excluded from board)
  board round-pendant.kicad_pcb: 346 footprints (0 board-only)
  338 parts to build; required fields: LCSC
  PASS: 0 errors, 0 warnings

Found 0 violations
ERC sheets: 8 violations: 0
```
