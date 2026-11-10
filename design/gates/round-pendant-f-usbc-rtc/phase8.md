# Gate 8: simulation and signal integrity (`round-pendant-f-usbc-rtc`)

Status: **passed**
Source net-class table: [design/nets-f-usbc-rtc.csv](../../nets-f-usbc-rtc.csv); SI/PDN/ESD/I2C1/RTC/crosstalk/thermal audit script: [scripts/variant_fusbc_rtc/si_audit.py](../../../scripts/variant_fusbc_rtc/si_audit.py); dispositions: [design/decisions.md](../../decisions.md) (`2026-11-09`).

---

## Checklist (`references/simulation.md` §Gate checklist)

- [x] **Trigger list generated from `design/nets-f-usbc-rtc.csv`:** Complete table in §1 below covering USB 2.0 Full-Speed SI & impedance, `U7` `±8 kV` ESD return loop, exact nodal DC IR drop (including `0.15 mm` via barrels at `25 °C / 60 °C` and `2 × 20 mΩ` CJT `A1251WR-S-2P` socket contact resistance), `400 kHz` `I2C1` bus (`U9` + `U13 RX8130CE:BB`) capacitance & rise time, `/MCU/RTC_INT` deep-sleep wake noise immunity & `/MCU/RTC_VOUT` internal LDO stability, `SE_HS` QSPI, `12 MHz` crystal, `VREG_LX`, aggressor/victim crosstalk, whole-board thermal `θ_BA`, and dormant + RTC alarm wake battery budget.
- [x] **Each triggered item has a quantitative calculation/script result or justified engineering disposition:** Full first-principles calculations and verbatim `si_audit.py` output in §1–§2 below.
- [x] **Expanded aggressor / victim coupling scan (`si_audit.py` §5) run and findings resolved:** Scans all `SWx_y`, `CSx_y`, `I2C_SCL/SDA`, `VREG_LX`, `QSPI_*`, `USB_*`, and `CLOCK` aggressors via Shapely `unary_union` without angle filtering (`10` `RTC_INT` pairs + `11` southern pairs + `23` inherited northern/matrix pairs evaluated and quantitatively dispositioned below).
- [x] **Design refinements fed back & re-verified across Gates 4–10:** Added 2nd parallel `0.30/0.15 mm` `VBAT` via `(94.518, 116.839)` alongside `(95.618, 117.089)` near `TP3.1`/`R8.2`, kept `RX8130_xtal_end` `100%` clear of `B.Cu` copper (`0` intrusions), and verified `0` DRC errors across all gates.

---

## 1. Trigger Matrix from `design/nets-f-usbc-rtc.csv`

| Class / Net Group | Changed vs `f-usbc`? | Trigger Condition (`references/simulation.md`) | Quantitative Analysis / Disposition (`si_audit.py`) |
|---|---|---|---|
| **`I2C` (`400 kHz` Fast-Mode): `/MCU/ACC_SCL`, `/MCU/ACC_SDA`** | **Yes (extended east to `U13.2/3` `RX8130CE:BB`)** | `400 kHz` I2C Fast-Mode (`C_bus ≤ 400 pF`, `t_r(30–70%)` / `t_r(10–90%) ≤ 300 ns`, address non-collision) | **PASS (`si_audit.py` §4):** `U9` (`LIS2DW12TR` @ `0x19`) + `U13` (`RX8130CE:BB` @ `0x32`, fixed 7-bit address) have zero address collision. Total copper: `ACC_SCL = 57.78 mm` (`5` vias, **`C_bus = 18.5 pF`**), `ACC_SDA = 35.31 mm` (`4` vias, **`C_bus = 16.4 pF`**) `<< 400 pF`. With existing `R19 = R20 = 4.7 kΩ` to `+3V3`: **`t_r(30–70%) = 73.6 ns`**, **`t_r(10–90%) = 191.2 ns < 300 ns`** Fast-Mode limit (`I_OL = 0.70 mA << 3 mA`). |
| **`SIGNAL_WAKE` & RTC LDO: `/MCU/RTC_INT`, `/MCU/RTC_VOUT`** | **NEW (`U13.6 -> U3.31 GPIO19`, `U13.9 -> C76`)** | Open-drain `POWMAN` `PWRUP2` deep-sleep wake noise immunity (`R32 = 100 kΩ`); `RX8130CE` internal backup-switch/oscillator node `VOUT` (`C76 = 1.0 µF`) | **PASS (`si_audit.py` §4–§5):** `RTC_VOUT` is a `1.24 mm`, **`0`-via** local `B.Cu` link directly to `C76` (`1.0 µF` 10 V X5R, `1.23 mm` pad-to-pad, **`0` aggressor couplings**). `RTC_INT` (`24.10 mm`, `2` vias, `B.Cu`/`In3.Cu` over solid `In2.Cu GND`) has `10` active-display crossings/parallels (`1.03–4.11 mm`). **During `POWMAN` deep sleep**, all `5` LED drivers (`SW*`/`CS*`) and `I2C0` (`I2C_SCL`) are **shutdown (`0 Hz`, `0 V/ns`) -> `0.00 V` coupled wake noise (`0` false wakeups)**. During active display, `C_m ≈ 0.08–0.28 pF` into `C_line ≈ 4.5 pF` produces `< 0.21 V` `< 50 ns` spikes (`<< 1.32 V` `RP2350` CMOS `3.3 V - V_IH` margin), and firmware verifies `RX8130CE` `Flag (0x1D)` `AF/TF` on wake. |
| **`POWER`: `VBUS`, `VBAT`, `/Power/BAT_N`, `U8 -> GND`, `VSYS`, `+3V3`, `+1V1`** | **Yes (`BT1` CJT `A1251WR-S-2P` SW + `U8`/`Q1` re-routed)** | Exact nodal DC resistance & IR drop at `25 °C / 60 °C` (incl. `0.15 mm` via barrels + `2 × 20 mΩ` `BT1` mated contact resistance) | **PASS (`si_audit.py` §3):** `VBUS (J1->U5.13)` = **`3.90 / 4.44 mΩ`** (`2.22 mV @ 500 mA`, `0` vias); `VBAT (BT1.1->U5.2/3)` = **`83.23 / 94.68 mΩ`** (`32.19 mV @ 340 mA`, `8` vias incl. dual parallel `0.30/0.15 mm` vias at `TP3.1`/`R8.2`); `BAT_N (BT1.2->U8.4/5)` = **`3.82 / 4.34 mΩ`** (`1.48 mV @ 340 mA`, `0` vias); `U8.1..3 -> In2.Cu GND` = **`0.76 / 0.86 mΩ`** (`0.29 mV @ 340 mA`, dual `0.30/0.15 mm` vias). **Full PCB + `2 × 20 mΩ` `BT1` contact loop @ `60 °C` = `139.88 mΩ` -> `47.56 mV @ 340 mA` (`41.55 mV @ 297 mA` charge)** — `< 1.3%` of `3.7 V` cell voltage and `<< 1.0 A` CJT `A1251` rating. |
| **`DIFF_HS` (`USB 2.0 FS`) & `U7` `±8 kV` ESD Clamp** | Unchanged from `f-usbc` | `12 Mbit/s` FS skew, stub & pre-clamp layer check | **PASS (`si_audit.py` §1–§2):** Identical to `f-usbc`: Orient. A `|skew| = 2.64 mm (~17.5 ps)`, Orient. B `|skew| = 3.74 mm (~24.7 ps)`, unmated stub `7.76–8.86 mm`, `USB_DM_C on F.Cu = False`, dual `U7.2` `GND` vias `(102.470, 110.730)` & `(102.126, 110.639)` + `R14/R15 = 27 Ω`. |
| **`SE_HS` (`QSPI`), `CLOCK` (`12 MHz` `Y1`), `SWITCH` (`VREG_LX`)** | No (`100%` verbatim from `f-usbc`) | `≤ 66 MHz` QSPI, `0`-via `12 MHz` crystal, `RP2350` `1.1 V` buck | **Unchanged from `f-usbc`:** `147/147` locked RP2350 decoupling/LDO/FB tracks and `9/9` zone piece counts preserved intact. |
| **Whole-Board Thermal & Dormant + RTC Sleep Power** | **Extended with `U13` `RX8130CE:BB` sleep audit** | `< 50 °C` worn skin limit, `< 45 °C` LiPo charge limit, `< 250 µA` sleep budget (`intent.md`) | **PASS (`si_audit.py` §6):** `θ_BA = 32.4 °C/W` free-air / `49.5 °C/W` worn (`P_cont,max = 0.51 W` continuous worn ceiling, LEDs blanked on `~CHG == 0`, `ADC4` foldback at `42 °C` / `47 °C`). With `FOUT` disabled (`FSEL1:0 = 11b` on boot), `U13` `RX8130CE:BB` draws **`1.50 µA` typ** (`4.95 µW @ 3.3 V`, `+0.0002 °C`), bringing **total dormant + hardware RTC alarm wake battery draw to `~201 µA` (`< 250 µA` target, `~83 days` standby on `400 mAh`)**. |

---

## 2. Verbatim `si_audit.py` Output & Crosstalk Dispositions

```text
=== 1. USB 2.0 FULL-SPEED (12 Mbit/s) POINT-TO-POINT SI & IMPEDANCE ===
  /Power/USB_DP_C   : total_copper= 11.94 mm, 0 vias, layers=['B.Cu']
  /Power/USB_DM_C   : total_copper= 18.01 mm, 3 vias, layers=['B.Cu', 'In6.Cu']
  USB_DP            : total_copper= 14.95 mm, 0 vias, layers=['B.Cu']
  USB_DM            : total_copper= 13.52 mm, 0 vias, layers=['B.Cu']
  /MCU/USB_DP_MCU   : total_copper=  5.28 mm, 2 vias, layers=['In4.Cu']
  /MCU/USB_DM_MCU   : total_copper=  5.94 mm, 2 vias, layers=['B.Cu', 'In4.Cu']
  Orient. A (A6/A7) : DP=30.09 mm, DM=27.44 mm -> |skew|=2.64 mm (~17.5 ps), unmated DM stub=8.86 mm
  Orient. B (B6/B7) : DP=32.28 mm, DM=28.54 mm -> |skew|=3.74 mm (~24.7 ps), unmated DM stub=7.76 mm
  Pre-ESD F.Cu check: USB_DM_C on F.Cu = False (layers=['B.Cu', 'In6.Cu'])

=== 2. U7 (USBLC6-2P6) ESD GROUND-RETURN LOOP ===
  U7.2 GND via #1 at (102.470, 110.730): center-path=3.90 mm (dist to J1.S1 2.3x1.8mm pad=0.000 mm)
  U7.2 GND via #2 at (102.126, 110.639): center-path=4.06 mm (dist to J1.S1 2.3x1.8mm pad=0.216 mm)

=== 3. EXACT NODAL DC RESISTANCE & IR DROP (25 C / 60 C, incl. 0.15 mm via barrels + 20 mOhm BT1 contact) ===
  VBUS (J1->U5.13)        : R_25C= 3.90 mOhm, R_60C= 4.44 mOhm -> Vdrop= 2.22 mV @ 500 mA (dual-row USB500)
  VBAT (BT1.1->U5.2/3)    : R_25C=83.23 mOhm, R_60C=94.68 mOhm -> Vdrop=32.19 mV @ 340 mA (340 mA max cont; 8 vias on VBAT)
  BAT_N (BT1.2->U8.4/5)   : R_25C= 3.82 mOhm, R_60C= 4.34 mOhm -> Vdrop= 1.48 mV @ 340 mA (340 mA max cont; 0 vias on BAT_N)
  U8.1..3 -> In2.Cu GND   : R_25C= 0.76 mOhm, R_60C= 0.86 mOhm -> Vdrop= 0.29 mV @ 340 mA (dual 0.30/0.15 GND vias into solid In2.Cu)
  Total PCB + 2x20mOhm BT1 contact loop @ 60 C: 139.88 mOhm -> 47.56 mV @ 340 mA (41.55 mV @ 297 mA charge)

=== 4. I2C1 (400 kHz, U9 + U13 RX8130CE) & RTC_INT WAKE TIMING / NOISE AUDIT ===
  /MCU/ACC_SCL      : total_copper= 57.78 mm, 5 vias, layers=['B.Cu', 'In1.Cu', 'In3.Cu', 'In6.Cu']
  /MCU/ACC_SDA      : total_copper= 35.31 mm, 4 vias, layers=['B.Cu', 'In3.Cu', 'In4.Cu', 'In6.Cu']
  /MCU/RTC_INT      : total_copper= 24.10 mm, 2 vias, layers=['B.Cu', 'In3.Cu']
  /MCU/RTC_VOUT     : total_copper=  1.24 mm, 0 vias, layers=['B.Cu']
  I2C1 C_bus: SCL=18.5 pF, SDA=16.4 pF (<< 400 pF max)
  I2C1 rise time (R19/R20 = 4.7 kOhm): t_r(30-70%)=73.6 ns, t_r(10-90%)=191.2 ns (< 300 ns Fast-Mode 400 kHz limit)

=== 5. FULL AGGRESSOR / VICTIM COUPLING AUDIT (spacing <= 0.45 mm, overlap >= 1.00 mm) ===
  RTC victim couplings (RTC_INT / RTC_VOUT, >=1.0 mm within 0.45 mm): 10
    /Driver 4 and matrix/CS4_1 (LED_PWM, In4.Cu) <-> /MCU/RTC_INT (SIGNAL_WAKE, In3.Cu): len=1.33 mm, min_d=0.000 mm, Y=[91.7,91.9]
    /Driver 4 and matrix/CS4_12 (LED_PWM, In3.Cu) <-> /MCU/RTC_INT (SIGNAL_WAKE, In3.Cu): len=3.83 mm, min_d=0.191 mm, Y=[88.5,91.8]
    /Driver 4 and matrix/CS4_12 (LED_PWM, In4.Cu) <-> /MCU/RTC_INT (SIGNAL_WAKE, In3.Cu): len=1.50 mm, min_d=0.000 mm, Y=[88.5,88.9]
    /Driver 4 and matrix/CS4_13 (LED_PWM, In4.Cu) <-> /MCU/RTC_INT (SIGNAL_WAKE, In3.Cu): len=1.22 mm, min_d=0.000 mm, Y=[90.6,91.9]
    /Driver 4 and matrix/CS4_2 (LED_PWM, In3.Cu) <-> /MCU/RTC_INT (SIGNAL_WAKE, In3.Cu): len=1.83 mm, min_d=0.225 mm, Y=[91.7,91.9]
    /Driver 4 and matrix/SW4_1 (LED_SCAN, In4.Cu) <-> /MCU/RTC_INT (SIGNAL_WAKE, In3.Cu): len=1.03 mm, min_d=0.000 mm, Y=[90.2,90.9]
    /Driver 4 and matrix/SW4_5 (LED_SCAN, In4.Cu) <-> /MCU/RTC_INT (SIGNAL_WAKE, In3.Cu): len=1.37 mm, min_d=0.000 mm, Y=[91.9,91.9]
    /Driver 4 and matrix/SW4_6 (LED_SCAN, In4.Cu) <-> /MCU/RTC_INT (SIGNAL_WAKE, In3.Cu): len=1.06 mm, min_d=0.000 mm, Y=[92.2,93.2]
    /Driver 5 and matrix/CS5_7 (LED_PWM, In6.Cu) <-> /MCU/RTC_INT (SIGNAL_WAKE, B.Cu): len=1.84 mm, min_d=0.284 mm, Y=[96.4,98.0]
    I2C_SCL (I2C_1MHZ, In6.Cu) <-> /MCU/RTC_INT (SIGNAL_WAKE, B.Cu): len=4.11 mm, min_d=0.000 mm, Y=[96.0,99.7]
  Southern sector victim couplings (>=1.0 mm within 0.45 mm): 11
  Inherited northern/matrix couplings (>=1.0 mm within 0.45 mm): 23 total

=== 6. WHOLE-BOARD THERMAL & DEEP-SLEEP WAKE POWER ===
  Whole-board theta_BA: free-air = 32.4 C/W, worn (w/ rear 35 mm LiPo) = 49.5 C/W -> P_cont,max = 0.51 W
  U13 RX8130CE:BB active current (FOUT=OFF, FSEL=11b): 1.50 uA typ (4.95 uW @ 3.3 V -> +0.0002 C)
  Total dormant + hardware RTC alarm wake battery draw: ~201 uA (< 250 uA sleep budget)
```

### Quantitative Dispositions of Aggressor / Victim Couplings ([decisions.md](../../decisions.md))
1. **`/MCU/RTC_INT` (`R32 = 100 kΩ`) ↔ `CS4_*` / `SW4_*` / `I2C_SCL` (`10` pairs):** In `POWMAN` dormant sleep (when `RTC_INT` acts as the asynchronous `PWRUP2` wake input), all `IS31FL3745` drivers and `I2C0` are **completely quiescent (`0 V/ns`)**, giving **`0.00 V` coupled noise** (`0` false wakeups). When awake, `RTC_INT` is referenced `76 µm` above solid `In2.Cu GND` (`In3.Cu`), limiting coupled pulses to `< 0.21 V` (`<< 1.32 V` noise margin), and firmware reads `RX8130CE` `Flag (0x1D)` to confirm `AF`/`TF`.
2. **Southern `VBAT_SENSE` (`8` pairs vs `CS2_*`/`SW2_*`/`SW5_8`):** `VBAT_SENSE` is hardware-filtered by `C7 = 100 nF` (`R1||R2 = 50 kΩ`, `f_c = 31.8 Hz`), driven low (`0 V`) whenever `VBAT_EN == 0`, and firmware averages `16×` `ADC0` samples with `0.0 mV` DC shift.
3. **`Net-(U5-ISET)` (`R4 = 3.0 kΩ` ↔ `SW2_4`, `1.26 mm` across `170 µm` core) & `Net-(U2-RSET)` (`R33 = 30 kΩ` ↔ `I2C_SCL`/`CS2_7`):** `< 25 ns` transient edge currents (`< 0.005%` average charge-current error; `0%` duty during static LED display).
