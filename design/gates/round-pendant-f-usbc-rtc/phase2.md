# Gate 2: schematic (`round-pendant-f-usbc-rtc`)

Status: **passed**
Parent schematic baseline: **Variant `f-usbc`** ([hw/round-pendant/f-usbc/round-pendant.kicad_sch](../../../hw/round-pendant/f-usbc/round-pendant.kicad_sch)) and [design/gates/phase2.md](../phase2.md).
Variant schematic: [hw/round-pendant/f-usbc-rtc/round-pendant.kicad_sch](../../../hw/round-pendant/f-usbc-rtc/round-pendant.kicad_sch), rendered PDF: [schematic.pdf](../../renders/round-pendant-f-usbc-rtc/schematic.pdf).

---

## Checklist (`references/schematic-style.md`)

- [x] **ERC passes with `--severity-all` (`0` violations across all `8` sheets):**
  ```text
  Found 0 violations
  ERC sheets: 8 violations: 0
  ```
- [x] **Custom functional symbols & exact footprint pin maps (`power.kicad_sch` & `mcu.kicad_sch`):**
  - **`BT1` (`power.kicad_sch`):** Swapped from `round_pendant:BatteryPads` (`in_bom=no`) to `round_pendant:JST_1P25_2P_MP` (`A1251WR-S-2P`, `C225111`, `in_bom=yes`, footprint `round_pendant:Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal`). Pin `1` = `VBAT`, Pin `2` = `BAT_N`, mounting tabs `MP` = `GND` (matching `p2-132-usb6` and `s2-110-usbc`).
  - **`U13` (`mcu.kicad_sch`, `REAL-TIME CLOCK (WAKE)` functional block):** Custom functional symbol `round_pendant:RX8130CE` (`RX8130CE:BB`, `C1542426`, footprint `round_pendant:Seiko_Epson_RX8130CE_3.2x2.5mm_P0.7mm`):
    - Top power pins: Pin `1` (`VIO`), Pin `8` (`VDD`), and Pin `10` (`VBAT`) tied to always-on `+3V3` per Seiko Epson Application Manual `ETM50E-10` §4.2 Circuit EX7 (`VBAT` never floated; `INIEN = 0, CHGEN = 0` in firmware), decoupled by **`C75`** (`100 nF 16 V X7R`, `C1525`, `Decouples=U13.8`).
    - Left bus inputs: Pin `2` (`SCL` -> `ACC_SCL`, `U3` Pin `5` `GPIO3`) and Pin `3` (`SDA` -> `ACC_SDA`, `U3` Pin `4` `GPIO2`) on `I2C1` (`400 kHz` Fast-Mode max per `ETM50E-10` Table 7, sharing `R19/R20 = 4.7 kΩ` pull-ups with `U9` `LIS2DW12` @ `0x19`; `RX8130CE` @ `0x32`).
    - Right outputs: Pin `6` (`~{IRQ}` -> `RTC_INT` -> `U3` Pin `31` `GPIO19` `POWMAN` `PWRUP2` wake input) pulled up to `+3V3` via **`R32`** (`100 kΩ 1%`, `C25741`, immune to `RP2350-E9` with `PUE=0, PDE=0`); Pin `9` (`VOUT` -> local label `RTC_VOUT`) stabilized by **`C76`** (`1 µF 10 V X5R`, `C52923`, `Decouples=U13.9`); Pin `4` (`FOUT`) and Pin `5` (`~{RST}`) marked `no_connect` (`Open` per `ETM50E-10` Table 1 Note p. 8; firmware sets `FSEL1:0 = 11b` at init to disable the default `32.768 kHz` `FOUT` driver and drop `I_DD` from `3.5 µA` to `1.5 µA` typ).
    - Bottom ground: Pin `7` (`GND`).
- [x] **All component fields complete (`Value`, `Footprint`, `MPN`, `Manufacturer`, `LCSC`, `Decouples`):** `346` schematic symbols (`338` `in_bom=yes` assembled parts with valid LCSC codes + `TP1..TP8` `in_bom=no`).
- [x] **`schematic_style_check.py` verified (`0` new errors or warnings):** Only the `5` inherited LED matrix-sheet `grid` items (waived in [decisions.md](../../decisions.md)) and `9` stacked-pin decoupler notes (all carrying explicit `Decouples` fields, verified by `placement_check.py`).
- [x] **Visual inspection of rendered sheets (`power.kicad_sch` p. 2 & `mcu.kicad_sch` p. 3 in [schematic.pdf](../../renders/round-pendant-f-usbc-rtc/schematic.pdf)):** Clean left-to-right signal flow, power top / ground bottom, dashed functional box with `0x32` / `FSEL=11b` / `INIEN=0, CHGEN=0` bring-up note, zero overlapping text or crossed wires.
