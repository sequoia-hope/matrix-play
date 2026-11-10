# Gate 3: net classification (`round-pendant-f-usbc-rtc`)

Status: **passed**
Parent net table: [design/nets-f-usbc.csv](../../nets-f-usbc.csv) and [design/gates/phase3.md](../phase3.md).
Variant net table: [design/nets-f-usbc-rtc.csv](../../nets-f-usbc-rtc.csv) (`187` rows = `185` inherited from `f-usbc` + `2` new RTC nets).

---

## Checklist (`references/net-classes.md`)

- [x] **Every schematic net of `≥ 2` pins classified in `design/nets-f-usbc-rtc.csv`:**
  - **`/MCU/RTC_INT`** (`U13.6 ~IRQ`, `R32.2`, `U3.31 GPIO19`): class **`SIGNAL`**, `0 Hz` idle (`< 1 Hz` open-drain active-low alarm/timer wake edge, `R32 = 100 kΩ` pull-up to `+3V3`, `0.033 mA` active sink), `0.09 mm` min width.
  - **`/MCU/RTC_VOUT`** (`U13.9 VOUT`, `C76.1`): class **`POWER`**, internal `RX8130CE` regulated logic rail (`< 0.01 mA`, `1.23 mm` direct `0.20 mm` `B.Cu` stub to `C76 = 1 µF`), `0.20 mm` width.
  - **`/MCU/ACC_SCL` & `/MCU/ACC_SDA`** (`I2C1`, `U3.5/4`, `R19/R20 = 4.7 kΩ`, `U9.1/4`, `U13.2/3`): retained in `SIGNAL` (`400 kHz` Fast-Mode max; bus capacitance `C_bus ≈ 18 pF` -> `t_r,10-90% = 2.2 · 4.7 kΩ · 18 pF = 186 ns < 300 ns` I2C Fast-Mode max).
  - **`VBAT` & `/Power/BAT_N`** (`BT1.1` / `BT1.2` on `A1251WR-S-2P`, rated `1.0 A` AC/DC vs `340 mA` max continuous wearable / `297 mA` charge): retained in `POWER` (`BATTERY` subclass in `.kicad_pro`, `≥ 0.30 mm` width in `.kicad_dru`).
- [x] **`nets_check.py` passes with `0` errors:**
  ```text
  nets_check: hw/round-pendant/f-usbc-rtc
    171 named nets in round-pendant.kicad_sch, 187 rows in nets-f-usbc-rtc.csv
    PASS: 0 errors, 187 warnings
  ```
  *(Pre-route `.kicad_pro` netlist export warnings match parent `phase3.md` / `phase5.md`.)*
