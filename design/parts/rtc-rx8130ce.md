# `U13` — Seiko Epson `RX8130CE:BB` Real-Time Clock Module (I²C-Bus, Built-In `32.768 kHz` Crystal)

- **Datasheets:**
  - `design/datasheets/rx8130ce.pdf` (Seiko Epson catalog datasheet, 2 pages). Read: all.
  - `design/datasheets/rx8130ce-app-manual.pdf` (`ETM50E-10`, 2026-01-30, 69 pages). Read: all hardware, pinout, external connection, land-pattern, electrical/AC, power-on sequence, register, FOUT, switchover, reflow, and I²C sections (§1–§20).
- **MPN:** `RX8130CE:BB` (`X1B000311000100` series, Grade `B` `5 ± 23 ppm` @ `+25 °C`)
- **Supplier (`jlc_parts.py show`):**
  - `C1542426 RX8130CE:BB (EPSON, SMD-10P): extended, JLC stock 2242, lifecycle normal, checked 2026-11-09` (`$0.7216` @ qty 10)
  - Supporting passives (all existing JLCPCB Basic Parts already in the board BOM — `0` extra feeder types for passives):
    - `C75` (`VDD`/`VIO`/`VBAT` bypass): `C1525 CL05B104KO5NNNC (Samsung Electro-Mechanics, 0402): basic, JLC stock 33472164, lifecycle normal, checked 2026-11-09` (`100 nF 16 V X7R`)
    - `C76` (`VOUT` smoothing cap): `C52923 CL05A105KA5NQNC (Samsung Electro-Mechanics, 0402): basic, JLC stock 11367807, lifecycle normal, checked 2026-11-09` (`1.0 µF 10 V X5R`)
    - `R32` (`/IRQ` open-drain pull-up): `C25741 0402WGF1003TCE (UNI-ROYAL, 0402): basic, JLC stock 8563379, lifecycle normal, checked 2026-11-09` (`100 kΩ 1%`)
- **Footprint:** `round_pendant:Seiko_Epson_RX8130CE_3.2x2.5mm_P0.7mm` (`3.2 × 2.5 mm`, `1.0 mm` max height, 10-pad ceramic LCC/SON `CE` package) — matches JLCPCB/EasyEDA `C1542426` (`RTC-SMD_L3.2-W2.5-P0.7-RX8130CE`) to `0.000 mm` (`1.00 × 0.70/0.40 mm` pads at `x = ±1.100 mm, y = ±1.550/±0.700/0.000 mm`, covering `100%` of Epson `ETM50E-10` §5.1 Fig. 9's `x ∈ [±0.63, ±1.27 mm]` bottom gold lands plus `0.33 mm` outer side-castellation toe fillet), with 3D model `3dmodels/RTC-SMD_L3.2-W2.5-P0.7-RX8130CE.step`.

---

## 1. Absolute Maximum Ratings vs. Board Worst Case (`ETM50E-10` §6 Table 2, p. 12)

| Parameter | Symbol | Abs Max | Board Worst Case (`round-pendant-f-usbc-rtc`) | Margin |
|---|---|---|---|---|
| Supply voltage (`VDD`, `VIO`, `VBAT`, `VOUT`) | `VDD..VOUT` | `-0.3 V` to `+6.5 V` | `+3.30 V ± 2%` (`3.366 V` max from `TPS7A0233` `U6`) | `+3.13 V` (`1.93×`) — OK |
| Input voltage (`SCL`, `SDA`) | `VIN1` | `-0.3 V` to `+6.5 V` | `+3.366 V` (`I2C1` pulled to `+3V3` via `R19/R20`) | `+3.13 V` (`1.93×`) — OK |
| Open-drain output voltage (`/RST`, `/IRQ`, `SDA`) | `VOUT1` | `-0.3 V` to `+6.5 V` | `+3.366 V` (`/IRQ` pulled to `+3V3` via `R32`) | `+3.13 V` (`1.93×`) — OK |
| CMOS output voltage (`FOUT`) | `VOUT2` | `-0.3 V` to `VIO + 0.3 V` | Unconnected (`Open`, `0 mA` load) | OK |
| Operating temperature | `T_use` | `-40 °C` to `+85 °C` | `0 °C` to `+50 °C` worn/bench (`≤ 47 °C` thermal cap) | `≥ 35 °C` — OK |
| Storage temperature | `T_stg` | `-55 °C` to `+125 °C` | `-20 °C` to `+60 °C` | OK |
| Reflow peak package temperature | `T_reflow` | `+260 °C` max (§12.2.(1) p. 20) | `Pass 1 B.Cu ≤ 250 °C`, `Pass 2 F.Cu ≤ 245 °C` | `≥ 10 °C` — OK |

---

## 2. Pin Assignment & Required External Parts (`ETM50E-10` §3.2 Table 1 p. 8, §4.2 Circuit EX7 p. 10, §20.1 Fig. 52 p. 65)

Per user architecture selection, `U13` operates from the **always-on `+3V3` rail** (`TPS7A0233` `U6`, `I_q = 25 nA`, active whenever either the `403535` LiPo cell is plugged into `BT1` or USB-C is plugged into `J1`) without an external backup coin cell or supercapacitor:

| Pin | Name | Type | Connection on `round-pendant-f-usbc-rtc` | Datasheet Justification |
|---|---|---|---|---|
| `1` | `VIO` | Power | `+3V3` (decoupled by `C75 = 100 nF`) | Host interface supply (`1.6–5.5 V`, `ETM50E-10` Table 3 p. 12). |
| `2` | `SCL` | Input | `/MCU/ACC_SCL` (`U3.5` `GPIO3`, `I2C1`) | `400 kHz` Fast-Mode sensor I²C1 bus (`R19 = 4.7 kΩ` to `+3V3`). **Must NOT share `1 MHz` `I2C0` LED driver bus** because `RX8130CE` max `f_SCL = 400 kHz` (Table 7 p. 15). |
| `3` | `SDA` | Bi-dir (OD) | `/MCU/ACC_SDA` (`U3.4` `GPIO2`, `I2C1`) | `400 kHz` Fast-Mode sensor I²C1 bus (`R20 = 4.7 kΩ` to `+3V3`); 7-bit address `0x32` (`0110010b`, §19.4 p. 61) — zero conflict with `U9` `LIS2DW12` (`0x19`). |
| `4` | `FOUT` | CMOS Out | `NC` (`Open`) | Table 1 Note p. 8: *"Use the FOUT, /RST, /IRQ terminals as Open when not in use. Don't connected to GND or VDD."* Avoids `32.768 kHz` trace `C·V²·f` sleep current prior to `FSEL1:0 = 11b`. |
| `5` | `/RST` | OD Out | `NC` (`Open`) | Unused reset monitor output; left open per Table 1 Note p. 8. |
| `6` | `/IRQ` | OD Out | `/MCU/RTC_INT` (`U3.31` `GPIO19`) + `R32 = 100 kΩ` to `+3V3` | Active-low N-ch open-drain alarm / wakeup-timer output; wakes `RP2350A` from `POWMAN` `P1.7` deep sleep via `PWRUP2` (`0 nA` idle pull-up current). |
| `7` | `GND` | Ground | `GND` (`In2.Cu` solid plane via) | System 0 V reference. |
| `8` | `VDD` | Power | `+3V3` (decoupled by `C75 = 100 nF`) | Main logic/oscillator supply (`1.25–5.5 V` for `INIEN = 0`, clock updates down to `VCLK = 1.1 V` — Table 3 p. 12). |
| `9` | `VOUT` | Reg/SW Out | `Net-(U13-VOUT)` -> `C76 = 1.0 µF` (`C52923`) to `GND` | Internal power-switch output; Table 1 p. 8 & Fig. 52 p. 65 specify **`1.0 µF` smoothing capacitor** close to `VOUT` and `GND`. |
| `10` | `VBAT` | Backup In | `+3V3` (tied to `VDD` & `VIO`) | **Mandatory §4.2 rule (p. 10, Circuit EX5/EX7):** *"Power is always supplied from VDD, but for stable operation, do not open VBAT and connect it to VDD."* Firmware keeps default `INIEN = 0, CHGEN = 0` (`1Fh = 0x00`). |

---

## 3. Calculations

### A. Supply Current & Sleep Budget (`ETM50E-10` Table 5 p. 13 & Table 32 p. 39)
- At POR (`1Ch = 0x04`), `FSEL1:FSEL0 = 00b` enables `32.768 kHz` on `FOUT`: `I_32k = 3.5 µA` typ (`4.0 µA` max, `C_L = 15 pF`; lower here because `FOUT` is `Open` with `C_L ≈ 0.5 pF`).
- Firmware initialization sets `Extension Register (1Ch)` bits `FSEL1:FSEL0 = 11b` (`FOUT = OFF`) and keeps `Control Register1 (1Fh) = 0x00` (`INIEN = 0, CHGEN = 0`):
  $$I_{DD,\text{sleep}} = 1.50\,\mu\text{A}\text{ typ} \quad (1.60\,\mu\text{A}\text{ max across }-40\,^\circ\text{C to }+85\,^\circ\text{C})$$
- On a `400 mAh` `403535` LiPo cell, `1.50 µA` adds only **`1.08 mAh / month`** (`0.27% / month`), keeping whole-board `POWMAN` `P1.7` cold-sleep (`~79–84 µA` typ incl. `5× IS31FL3745`) inside `intent.md` R17's **`≤ 85 µA`** limit and `RP2350` `DORMANT` SRAM-retained sleep (`~201 µA`) inside the `< 250 µA` brief budget.

### B. `C75` (`VDD/VIO/VBAT`) & `C76` (`VOUT`) MLCC DC-Bias Derating
- **`C75` (`CL05B104KO5NNNC`, `100 nF`, `16 V` X7R `0402` on `+3.3 V`):** Voltage ratio `3.3 V / 16 V = 20.6%` (`4.8×` voltage margin vs `≥ 2×` rule); Samsung `CL05B104KO5NNNC` retains **`~84 nF`** effective capacitance at `3.3 V` (`ETM50E-10` Circuit EX7 requires `~0.1 µF` class ceramic filter cap).
- **`C76` (`CL05A105KA5NQNC`, `1.0 µF`, `10 V` X5R `0402` on `VOUT ≈ 3.29 V`):** Voltage ratio `3.3 V / 10 V = 33%` (`3.0×` voltage margin); Samsung `CL05A105KA5NQNC` retains **`~0.68 µF`** effective capacitance at `3.3 V` (`6.8×` Circuit EX7's `0.1 µF` single-rail requirement on p. 10, and matches Table 1 / Fig. 52's `1.0 µF` nominal part).

### C. `I2C1` (`ACC_SDA` / `ACC_SCL`, `400 kHz` Fast-Mode) Rise Time & `V_OL` Margin (`ETM50E-10` Table 6–7 pp. 14–15)
- Pull-up resistors `R19 = R20 = 4.7 kΩ` (`1%`) to `+3.30 V`:
  - Sink current when `SDA` driven low: $I_{OL} = \frac{3.30\,\text{V}}{4.7\,\text{k}\Omega} = 0.702\,\text{mA} \ll 3.0\,\text{mA}$ rated (`Table 6`: $V_{OL4} \le 0.40\,\text{V}$ at $I_{OL} = 3\,\text{mA}$ $\Rightarrow$ $V_{OL4} \approx 0.09\,\text{V} \ll V_{IL,\max}(\text{RP2350}) = 0.99\,\text{V}$).
  - Bus capacitance (`U3` RP2350 `~5 pF` + `U9` LIS2DW12 `~5 pF` + `U13` RX8130CE `~5 pF` + `~26 mm` inner/bottom trace `@ 0.11 pF/mm ≈ 3 pF`): $C_{\text{bus}} \approx 18\,\text{pF}$.
  - `10%–90%` RC rise time (`0.3 VIO` to `0.7 VIO` is `0.8473 τ`; `10%–90%` is `2.197 τ`):
    $$t_{r,30\text{–}70\%} = 0.8473 \times 4700\,\Omega \times 18\,\text{pF} = 71.7\,\text{ns}, \qquad t_{r,10\text{–}90\%} = 2.197 \times 4700\,\Omega \times 18\,\text{pF} = 185.9\,\text{ns} < 300\,\text{ns}\text{ (Fast-Mode max)}$$
  - Logic thresholds: `VIH_min(RX8130CE) = 0.8 × VIO = 2.64 V` (`+3.30 V` pull-up gives `+0.66 V` high noise margin); `VIL_max(RX8130CE) = 0.2 × VIO = 0.66 V` (`RP2350` `VOL < 0.20 V` at `0.7 mA` gives `0.46 V` low noise margin).

### D. `/IRQ` (`RTC_INT`) Open-Drain Pull-Up (`R32 = 100 kΩ`) & `RP2350-E9` Safe Wake
- Idle (`RTC_INT = 3.30 V`): external `R32 = 100 kΩ` holds `U3.31` (`GPIO19`) solidly at `+3.30 V` with **`0.00 nA` quiescent current** while `RP2350` internal pull-up/pull-down stay disabled (`PUE = 0, PDE = 0`), completely sidestepping `RP2350-E9` pad-latching leakage in `POWMAN` `P1.7` sleep.
- Active alarm/timer pulse (`t_RTN2 = 7.57 ms` at `1 Hz` / `1/60 Hz` timer): $I_{\text{IRQ}} = 3.30\,\text{V} / 100\,\text{k}\Omega = 33\,\mu\text{A}$ for `7.57 ms` (`250 nC` per wake event). Fall time to `0 V` via N-ch FET (`R_on ≈ 130 Ω`, `C_net ≈ 8 pF`) is `< 3 ns`; release rise time `2.2 × 100 kΩ × 8 pF = 1.76 µs`.

### E. Timekeeping Accuracy (`ETM50E-10` Table 4 p. 12 & §11.1 Fig. 18 p. 19)
- Factory room-temperature trim (`+25 °C`): $\Delta f / f_0 = +5 \pm 23\,\text{ppm}$ (`±60 s / month` max at `+25 °C` before digital offset).
- Parabolic tuning-fork temperature curve ($\alpha = -0.035\,\text{ppm}/^\circ\text{C}^2$, turnover $\theta_T = +25\,^\circ\text{C}$): at worn `+33 °C`, $\Delta f_T = -0.035 \times (33 - 25)^2 = -2.24\,\text{ppm}$ (partially cancelling the `+5 ppm` nominal room offset!), plus `Digital Offset Register (30h)` supports `±189 ppm` trim in `3.05 ppm` steps if sub-`5 ppm` calibration against USB host time is desired.

---

## 4. Fine Print, Gotchas & Layout Guidance (`ETM50E-10` §5.1 p. 11, §10.2 p. 17, §12 p. 20)

1. **Crystal Inspection Pads (`*1` on Pin 1–10 Short Side — §5.1 Fig. 9 p. 11):**
   - *"The metal pads on the short side of the 1st and 10th pins of the package are inspection pads for the crystal unit. For stable oscillation, make sure that leakage current due to condensation or dust does not occur between these pads."*
   - **Enforced in PCB:** A dedicated `B.Cu` rule area (`RX8130_xtal_end`, `[114.30..115.20, 102.30..103.05] mm`, `no_tracks, no_vias, no_pour`) is placed directly under the Pin 1–10 short edge so no `B.Cu` trace, pour, or via sits beneath the crystal inspection pads.
2. **Never Float `VBAT` (Pin 10) — §4.2 p. 10:** Tied directly to `VDD` (`+3V3`) right at the package pads; `CHGEN` (`1Fh[7]`) must remain `0`.
3. **Power-Supply Slew Rate (`t_R1 = 0.1–10 ms/V` — §10.4 Table 11 p. 18) & Crystal Start-Up (`t_str ≤ 1.0 s` — Table 4 p. 12, Fig. 42 p. 55):** `TPS7A0233` (`U6`) ramps `0 -> 3.3 V` in `~0.75–1.20 ms` (`~0.25–0.40 ms/V`, right inside `0.1–10 ms/V`!). Firmware waits `> 30 ms` (`t_CL`), issues 1 dummy read, and checks `VLF` (`1Dh[1]`): if `VLF == 1` (cold battery attach), poll writing `1Dh = 0x00` across `t_str` (`0.19 s` typ, **`1.0 s` max**) until `VLF` reads back `0`, pulse `INIEN` (`1Fh = 0x10 -> 0x00` with `CHGEN = 0`), set `30h = 0x00`, `1Ch = 0xC0` (`FSEL1:FSEL0 = 11b`, `FOUT = OFF`), and program BCD calendar `10h..16h` (`[bringup-f-usbc-rtc.md](../bringup-f-usbc-rtc.md)` §4).
4. **No Ultrasonic Cleaning & Keep Away From High-dV/dt Switchers (§12.1.(2) & §12.2.(3) p. 20):** Placed in the quiet East `B.Cu` pocket (`~13.5 mm` from `L1` `VREG_LX` buck inductor, shielded above by solid `In2.Cu GND`), with `C75` (`100 nF`) and `C76` (`1.0 µF`) placed `1.23 mm` from `U13.8/10` and `U13.9`. PCBA order notes must include **`DO NOT ULTRASONIC CLEAN`**.
5. **Verified Land Pattern (`ETM50E-10` Fig. 9 p. 11 & EasyEDA `C1542426`):**
   - Matches JLCPCB/EasyEDA `C1542426` (`0.000 mm` pad-center delta; vs `ETM50E-10` Fig. 9's `0.90 mm` pads at `x = ±1.000 mm`, EasyEDA's `1.00 mm` pads at `x = ±1.100 mm` overlap `100%` of the `x ∈ [±0.63..0.65, ±1.25..1.27 mm]` bottom gold lands with `+0.03–0.05 mm` inner heel and `+0.33 mm` outer side-castellation toe fillet):
     - Corner pads `1, 5, 6, 10`: `1.00 × 0.70 mm` at `x = ±1.100 mm, y = ±1.550 mm`.
     - Inner pads `2, 3, 4` (`x = -1.100 mm`) & `7, 8, 9` (`x = +1.100 mm`): `1.00 × 0.40 mm` at `y = -0.700, 0.000, +0.700 mm` (`0.30 mm` inter-pad solder-mask dam = `3.0×` JLC `0.10 mm` ENIG minimum; `1.20 mm` inner cross-row gap).

## 5. Open Questions
- None — user selected `Seiko Epson RX8130CE:BB` (`C1542426`) powered from always-on `+3V3` (`VBAT = VDD = VIO = +3V3`).
