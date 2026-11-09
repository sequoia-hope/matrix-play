# Bench Bring-Up Plan: `parallelogram-p2-132-usb6` (`Rev P1U6`)

All expected voltages, currents, and register values below are taken directly from the audited part specifications (`design/parts/{charger.md,rp2350-core.md,drivers-aw20198.md,buttons.md,parallelogram-io.md}`) and verified schematic/PCB coordinates (`hw/parallelogram/p2-132-usb6/`).

## 1. Probe Map (`B.Cu` Back Side, board center `(0, 0)` = KiCad `(100.0, 100.0) mm`)

| Test Pad / Probe Point | Net | Position `(x, y)` mm | Expected Unpowered `R` to `GND` (`TP8`) | Expected Powered Value |
|---|---|---|---|---|
| `TP8` | `GND` | `(-5.40, -3.55)` | `0.0 Ω` (reference) | `0.00 V` |
| `TP1` | `VSYS` (`U5.OUT`) | `(+6.25, +14.30)` | `> 50 kΩ` (cap charge ramp) | **`4.30–4.50 V`** (`4.40 V` typ on USB, no cell); `VBAT - 0.05 V` on LiPo |
| `TP2` | `+3V3` (`U6.OUT`) | `(-6.90, +11.75)` | `> 20 kΩ` | **`3.267–3.333 V`** (`3.30 V ± 1%`, `TPS7A0233PDQNR`) |
| `TP3` | `VBAT` (`BT1.1`) | `(+6.55, +12.19)` | `> 100 kΩ` (`Q1` off) | `3.0–4.20 V` with cell; floats/`~4.18 V` `I_TERM` cycle with no cell |
| `TP4` | `+1V1` (`U3` `DVDD`) | `(-7.30, +13.80)` | `> 5 kΩ` | **`1.08–1.12 V`** (`1.10 V` typ RP2350 internal buck) |
| `TP5` | `/MCU/RUN` | `(-5.50, -1.50)` | `> 40 kΩ` (internal PU) | **`3.30 V`** (`short to TP8 GND to reset U3`) |
| `TP6` | `/MCU/SWCLK` | `(+4.20, -1.20)` | High-Z / internal PD | SWD clock (`3.3 V` logic) |
| `TP7` | `/MCU/SWDIO` | `(+3.55, -3.17)` | High-Z / internal PU | SWD data (`3.3 V` logic) |
| `C1.1` (`0402` by `U7`/`J1`) | `VBUS` (`J1` `5 V`) | `(+3.13, +23.65)` | `> 50 kΩ` | **`4.75–5.25 V`** (measure on external USB-C breakout rather than probing `0402` `C1.1` live) |
| `R46.1` / `C71.1` | `/MCU/USER_C` (`GPIO9`) | `(-6.90, -21.00/-22.20)` | High-Z (unpowered) | **`3.30 V` released -> `0.04–0.07 V` pressed** (`SW5` West-North) |
| `R47.1` / `C72.1` | `/MCU/USER_D` (`GPIO0`) | `(-6.90, +21.00/+19.80)` | High-Z (unpowered) | **`3.30 V` released -> `0.04–0.07 V` pressed** (`SW6` West-South) |

*(Note: All `8/8` test points — `"VSYS"` (`TP1`), `"3V3"` (`TP2`), `"VB"` (`TP3` `VBAT`), `"1V1"` (`TP4`), `"RUN"` (`TP5`), `"CLK"` (`TP6`), `"DIO"` (`TP7`), and `"GND"` (`TP8`) — are directly labeled on `B.SilkS`, and all `98` bottom parts + `133` top parts are mapped without overlap on 4:1 `fab/assembly-bottom.pdf` & `fab/assembly-top.pdf`. Isolation jumpers: none on board — `0` `0 Ω` links per parallelogram family waiver. Always power up first from a current-limited `5.0 V` USB-C breakout supply **before** connecting a LiPo cell to `BT1`, and wear an ESD wrist strap when handling bare un-enclosed boards because `SW1..SW4` use inherited `1 kΩ`-only series resistors without shunt TVS/caps.)*

---

## 2. Unpowered Visual & Continuity Inspection (Before First Power)
1. **Microscope inspection:** Check `U3` (`RP2350A`), `U1`/`U2` (`AW20198QNR`), `U5` (`BQ24073`), `U6` (`TPS7A0233`), `U8` (`XB9901A`), `U9` (`LIS2DW12TR`), `J1` (`TYPE-C-31-M-22`), `BT1` (`A1251WR-S-2P` at `(+7.97, +23.00, 0°)` facing `-Y` North toward the LiPo pocket), and `SW1..SW6` (`SW4` bezel-aligned at `(+8.15, +30.55, 162.26°)` parallel to `J1`; `SW5`/`SW6` plungers protruding `0.45 mm` past West `x = -12.50 mm` edge, `0.20 mm` crisp tactile click without binding).
2. **Rail-to-`GND` (`TP8`) diode/resistance check (no USB, no battery):** Verify zero shorts (`> 5 kΩ` steady-state after ceramic caps charge) on `C1.1` (`VBUS`), `TP3` (`VBAT`), `TP1` (`VSYS`), `TP2` (`+3V3`), and `TP4` (`+1V1`). Also verify `BT1` `Pad 1` (`+`, West `(+7.345, +25.400)`) to `Pad 2` (`-` `BAT_N`, East `(+8.595, +25.400)`) is open/`> 100 kΩ`.

---

## 3. Current-Limited USB-C First Power-Up (No LiPo Connected)
1. Set bench supply to **`5.00 V`, `100 mA` current limit**, feeding a USB-C breakout cable into `J1`.
   - *Boot note (`parts/charger.md`):* With a blank `W25Q128JVPIQ` flash (`U4`), `LED_SDB` (`GPIO6`) is held low (`0 V`) by `R31` (`100 kΩ`), keeping `U1`/`U2` disabled (`~2.6 µA`). `BQ24073` starts in `USB100` for `~2 ms` until `+3V3` rises on `EN1`, then enters `USB500` (`I_IN,max = 450–500 mA`). Expected blank-flash USB draw: **`15–35 mA`**.
2. Measure rails in order against `TP8` (`GND`):
   - `TP1` (`VSYS`): **`4.30–4.50 V`** (`4.40 V` typ `BQ24073` `VO(REG)`).
   - `TP2` (`+3V3`): **`3.27–3.33 V`**.
   - `TP4` (`+1V1`): **`1.08–1.12 V`** (`12 MHz` crystal `Y1` starts when RP2350 USB bootrom enumerates).
3. Plug `J1` into a host PC USB port (through a USB current meter): verify RP2350 enumerates immediately as **`2e8a:000f` (`RP2350 Boot`)** mass-storage / `picotool` device (`U4` blank).

---

## 4. Firmware Smoke Test (All 6 Buttons, Sensors, & 132-LED Matrix)
Flash bring-up UF2 over USB (`picotool load` or drag-and-drop) and verify:
1. **Six-button GPIO & debounce verification (enable RP2350 internal pull-ups on all user GPIOs, apply `>= 20 ms` symmetrical press + release software debounce window across `SW1..SW6`):**
   - `SW1` (East mid, `"PWR"`): `GPIO11` (`U3.15`) reads `1` idle -> `0` pressed.
   - `SW2` (West mid, `"BOOT"`): `/MCU/QSPI_SS` reads `1` idle -> `0` pressed (hold `SW2` + tap `TP5` `RUN` to `TP8` `GND` re-enters `RP2350 Boot`; configure `PADS_QSPI.SLEWFAST = 0` in boot stage).
   - `SW3` (NW wing, `"USER_A"`): `GPIO7` (`U3.10`) reads `1` idle -> `0` pressed.
   - `SW4` (SE wing, `"USER_B"`): `GPIO19` (`U3.31`) reads `1` idle -> `0` pressed.
   - **`SW5` (West North, `"USER_C"`): `GPIO9` (`U3.13`) reads `1` idle (`3.30 V` at `R46.1`) -> `0` pressed (`0.05 V` at `R46.1`), `0` bounce double-triggers on press or release with `20 ms` SW filter (`10 ms` max OFF bounce + `8.83 ms` slow-corner RC rise = `18.83 ms`).**
   - **`SW6` (West South, `"USER_D"`): `GPIO0` (`U3.2`) reads `1` idle (`3.30 V` at `R47.1`) -> `0` pressed (`0.05 V` at `R47.1`), `0` bounce double-triggers on press or release with `20 ms` SW filter.**
2. **I2C sensors & LED drivers (`12 mA` pad drive on `GPIO4`/`GPIO5`):**
   - `I2C1` (`GPIO2` `ACC_SDA`, `GPIO3` `ACC_SCL`): `U9` (`LIS2DW12TR`, `SA0 = +3V3` -> `0x19`) `WHO_AM_I (0x0F) == 0x44`; `ACC_INT` (`GPIO10`) toggles.
   - `I2C0` (`GPIO4` `I2C_SDA`, `GPIO5` `I2C_SCL`): Drive `GPIO6` (`LED_SDB`) `HIGH`, wait `2 ms`, verify `U1` (`0x20`) and `U2` (`0x25`) `RST/ID == 0xB8`, write **`SRCR = 0x07`** (soft `SW`/`CS` slew rate to minimize `dV/dt` crosstalk) and **`GCR = 0xB9`** (`SW1..SW11` enabled, `LGC = 1` `3.3 V` logic threshold, `CHIPEN = 1`). Run low-brightness (`GCC = 0x20`) R/G/B walk across all `132` LEDs (`D1..D132`). **Mandatory dimming & thermal guards (`design/sim/p2-132-usb6/`):** always scale overall brightness via the **`AW20198` analog `GCC` register** (never leave `GCC = 0xFF` with PWM-only dimming, which draws `840 mA` peak row pulses and `329 mV` battery droop): cap **`GCC <= 0x40` (`~165 mA` LEDs, `0.54 W` continuous worn ceiling -> `<= 43.0 °C < 45 °C` skin limit at `25 °C` ambient)**, allow `GCC <= 0x74` (`300 mA`) only for short handheld bursts governed by **closed-loop `RP2350` `ADC4` internal temperature sensor foldback** (`<= 45 °C` worn / `<= 42 °C` while `CHG == 0` charging with `GCC <= 0x44`), and fold back brightness below `VBAT = 3.50 V`.
   - **RP2350-E9 ADC errata setup (`GPIO26` `ADC0`, `GPIO27` `ADC1`):** Before sampling either ADC channel (and before entering sleep), explicitly clear **`PADS_BANK0: GPIO26.IE = 0, PDE = 0`** and **`GPIO27.IE = 0, PDE = 0`** so pad leakage never perturbs high-impedance dividers.
   - Ambient light sensor `Q2`: Drive `GPIO1` (`LIGHT_PWR`) `HIGH`, wait `1 ms`, average `16×` `ADC1` (`GPIO27` `LIGHT`) samples -> voltage rises under flashlight (`~0.66 V` typ at `100 lx` across `R43 = 22 kΩ`).
   - Battery divider `Q1`: Drive `GPIO14` (`VBAT_EN`) `HIGH`, **wait `>= 30 ms` (`6τ` for `R11||R12 = 50 kΩ` × `C7 = 100 nF`, `τ = 5.0 ms`, `< 0.25%` settling error per `passives.md` — waiting only `2 ms` reads `33%`!)**, read `ADC0` (`GPIO26` `VBAT_SENSE`) -> `0.50 × VBAT` (`1.80–2.10 V` on cell), then set `GPIO14 = LOW`.

---

## 5. LiPo Attachment, Charger (`297 mA`), & Deep-Sleep Current Check
1. **Verify LiPo plug polarity & wire color order with DMM BEFORE mating to `BT1` (`A1251WR-S-2P`, mouth at `y = +20.70 mm` facing `-Y` North toward board center):**
   - **CRITICAL 50/50 HARNESS POLARITY TRAP:** Commercial off-the-shelf `1.25 mm` 2-pin Molex PicoBlade / CJT `A1251H-2P` / Micro-JST 1S LiPo leads split **50/50 between `Pin 1 = Red (+)` and `Pin 1 = Black (-)`**! Although `U8` (`XB9901A`) includes battery reverse-connection protection, ALWAYS verify wire polarity with a DMM against the `B.SilkS` `"+"` (West) and `"-"` (East) marks before plugging in (re-pinning the crimp housings with tweezers if reversed):
   - **`BT1` Pin 1 (`+` `VBAT`, Red wire) = WEST rear pad (`(+7.345, +25.400) mm`, Right pin in Mirrored `B.Cu` view, marked `"+"` on `B.SilkS`, toward `J1`/`U5`).**
   - **`BT1` Pin 2 (`-` `BAT_N`, Black wire) = EAST rear pad (`(+8.595, +25.400) mm`, Left pin in Mirrored `B.Cu` view, marked `"-"` on `B.SilkS`, toward East board edge).**
   - Slide the `A1251H-2P` plug straight South (`+Y`) into `BT1`'s North-facing mouth (`6.03 mm` unobstructed runway to `0402` `R8` and `7.20 mm` to `U8` — zero IC obstruction, leads exit straight North toward the LiPo pocket!) before adhering the cell (**`<= 18.0 mm`-wide cell** such as `601835` / `501035` on `1.0 mm` foam tape, OR a `20 × 35 mm` `602035`/`802035` cell on **`>= 1.8–2.0 mm` VHB/foam standoff** clearing `1.55 mm` max `SW1`/`SW2`/`SW5` `EVQP7J01P` bodies).
2. **Charge verification (cell at `3.6–3.9 V`, USB `5.0 V` attached):**
   - `PGOOD` (`GPIO13`) = `0` (USB valid), `CHG` (`GPIO12`) = `0` (charging via `R6 = 100 kΩ` pull-up).
   - Charge current into cell (`R4 = 3.0 kΩ` on `U5.16 ISET`): **`297 mA` nominal (`266–325 mA` window)**, terminating at `4.20 V ± 1%` (`~30 mA` `I_TERM`).
3. **`POWMAN` `P1.7` deep-sleep current check (USB unplugged, DMM in series with `VBAT`):**
   - Clear default RP2350 pad pull-downs on external-pull-up GPIOs (`GPIO2..5, 12, 13` plus any enabled internal-pull-up button GPIOs), set `LED_SDB (GPIO6) = 0`, `LIGHT_PWR (GPIO1) = 0`, `VBAT_EN (GPIO14) = 0` (off), enter `P1.7` -> verify total battery sleep draw **`<= 85 µA`** (`~65 µA` typ), and wake cleanly via `SW1` (`GPIO11`).
