# Bench Bring-Up & Smoke-Test Plan — Sunflower `s2-110-usbc` (Rev S3C)

Board: [sunflower.kicad_pcb](../../../hw/sunflower/s2-110-usbc/sunflower.kicad_pcb) (`Ø38.0 mm`, 4-layer, `110× XL-1615RGBC-RF` + `2× AW20198QNR` + `RP2350A`).
Probe map: [bringup-map-bottom.png](../../renders/sunflower-s2-110-usbc/bringup-map-bottom.png) and [assembly-bottom.png](../../renders/sunflower-s2-110-usbc/assembly-bottom.png).

> [!IMPORTANT]
> **Perform all Steps 1–7 BEFORE bonding a `403535` LiPo pouch to `B.Cu`.** Thirteen of the `14` bare `Ø1.0 mm` test pads lie inside the `Ø35 mm` battery envelope; once bring-up passes, apply **`0.05 mm` Kapton tape** over `B.Cu` exposed test pads (`TP1..TP7`, `TP14..TP16`) and provide a **`≥ 2.4 mm` insulating foam/carrier standoff** so the pouch clears `J1` (`3.26 mm`) and mated `BT1` (`3.40 mm`).

---

## 1. Test-Pad & Probe Reference (`B.Cu`, Board-Centre `(0, 0)` Coordinates)

Note: `TP9` and `TP10` do not exist in this variant (`14` test pads total: `TP1..TP8`, `TP11..TP16`). Coordinates `(x, y)` below are KiCad top-view (`F.Cu`) board-centre coordinates; **when looking directly at the back (`B.Cu`) as in [bringup-map-bottom.png](../../renders/sunflower-s2-110-usbc/bringup-map-bottom.png), horizontal X is mirrored so KiCad `NW` (`BT1`, `SW2`, `TP8`) appears on the right and KiCad `NE` (`SW1`, `TP14..TP16`) appears on the left.** Because `TP8` (`GND`) sits on the `NW`/`W` rim, you may also clip/probe `GND` on **`J1`'s metal USB-C shield shell** at the South rim (`(0.0, +15.6 mm)`).

| Ref | Net | Silk Landmark | `(x, y)` (`mm`) | Expected Unpowered Resistance to `GND` | Expected Powered Voltage / Signal |
|---|---|---|---|---|---|
| `TP8` | `GND` | `GND` | `(-17.30, +1.20)` | `0.0 Ω` (`< 0.3 Ω` to `J1` shell) | `0.000 V` reference |
| `TP13` | `VBUS` | *(near `USB 5V`)* | `(+6.80, +16.95)` | `> 100 kΩ` (`R1/R2` on `CC`, `C1` `1 µF`) | **`4.75–5.25 V`** on USB-C attach (`0.0 V` battery-only) |
| `TP3` | `VBAT` | *(unlabeled)* | `(+8.15, +7.60)` | `> 1 MΩ` (`Q1` off; `C3` `1 µF`) | **`3.50–4.20 V`** with LiPo (`~0–4.2 V` charger float without LiPo) |
| `TP1` | `VSYS` | `VSYS` | `(+7.80, +4.45)` | `> 50 kΩ` (`~68 µF` MLCC charge ramp) | **`4.30–4.50 V`** (`4.40 V` typ) on USB (`BQ24073` `VO(REG)`); **`VBAT - <0.05 V`** on battery |
| `TP2` | `+3V3` | *(under `LIPO 403535`, N of `1V1`)* | `(+6.60, -6.95)` | `> 50 kΩ` (`~20 µF` MLCC ramp) | **`3.250–3.350 V`** (`TPS7A0233` `±1.5%`) |
| `TP4` | `+1V1` | `1V1` | `(+6.70, -4.70)` | `> 10 kΩ` (`~10 µF` MLCC ramp) | **`1.067–1.133 V`** (`RP2350A` internal buck `1.10 V ±3%`) |
| `TP5` | `/MCU/RUN` | *(unlabeled, N)* | `(+3.20, -17.95)` | `> 100 kΩ` (internal pull-up when powered) | **`3.25–3.33 V`** (pull to `GND` to reset `RP2350A`) |
| `TP6` | `/MCU/SWCLK` | *(unlabeled, NE)* | `(+7.25, -14.70)` | High-Z | SWD clock (`RP2350` debug) |
| `TP7` | `/MCU/SWDIO` | `DIO` | `(+9.55, -15.30)` | High-Z | SWD data (`RP2350` debug) |
| `TP11` | `I2C_SDA` | *(near `SCL`)* | `(+8.90, +16.05)` | **`~1.0 kΩ`** to `TP2` (`+3V3` via `R21`) | **`3.30 V` idle**; `1 MHz` Fm+ I2C (`0x20` `U1`, `0x25` `U2`, `0x5A` broadcast) |
| `TP12` | `I2C_SCL` | `SCL` | `(+10.75, +14.75)` | **`~1.0 kΩ`** to `TP2` (`+3V3` via `R22`) | **`3.30 V` idle**; `1 MHz` Fm+ I2C clock |
| `TP14` | `/MCU/UART_TX` | `TX` | `(+11.05, -4.85)` | High-Z | `GPIO24` UART1 TX (`3.3 V` logic) |
| `TP15` | `/MCU/UART_RX` | `RX` | `(+11.45, -7.25)` | High-Z | `GPIO25` UART1 RX (`3.3 V` logic) |
| `TP16` | `/MCU/GPIO29_TP` | `29` | `(+11.25, -10.25)` | High-Z | `GPIO29 / ADC3` spare |

---

## 2. Unpowered Visual & Ohmmeter Inspection (Step 1)

1. **Microscope visual check (`B.Cu` & `F.Cu`):**
   - Confirm **`BT1`** (`NW` rim) has its mating mouth facing inward (`ESE` toward `U3`) and signal pins on the `NW` rim: **`BT1` Pin 1 (`VBAT +`) is the more northerly/NE pad `(-13.44, -11.61)`** and **Pin 2 (`BAT_N -`) is the more southerly/SW pad `(-13.87, -10.43)`** — verify zero solder bridge to the tented `VBAT` via `0.107 mm` from `BT1.2`!
   - Confirm **`J1`** USB-C mouth overhangs the South rim (`+0.25–0.30 mm`) with clean fillets on all `16` SMD pins and `0` solder wicking from the `4` PTH shell slots onto adjacent `F.Cu` LEDs (`D10`, `D104`, `D110`). Because `sunflower-B_Paste.gbp` omits paste on `J1`'s `4` PTH shell slots (and `F.Cu` soldering is forbidden `0.18 mm` from the LEDs), if `J1`'s shell legs were left unsoldered by SMT-only PCBA, carefully tack the **outer `B.Cu` edges** of `J1`'s `4` shell slots under a microscope with a fine tip (`≤ 320 °C`, `< 2 s`) before plugging in a USB-C cable.
   - Confirm **`U5`** (`BQ24073`) sits level (no tilt/solder balling from the `2` non-POFV thermal vias inside `U5.17`).
   - Confirm **`L1`** (`3.3 µH`) polarity mark faces **West** (`+1V1` / `C18` side, pad 1).
2. **Cold continuity & diode/resistance checks (DMM in low-voltage `< 0.5 V` resistance mode, probing `Ø1.0 mm` test pads & `0402` resistor pads only — never `0.40 mm`-pitch QFN pins):**
   - Verify **no rail shorts** between `TP8`/`J1-shell` (`GND`) and `TP13` (`VBUS`), `TP3` (`VBAT`), `TP1` (`VSYS`), `TP2` (`+3V3`), and `TP4` (`+1V1`).
   - Verify `BT1.1` ↔ `BT1.2` resistance is `> 1 MΩ` (`0` short across raw cell pins).
   - *(Note: `NT1` board-ID strap on `GPIO19` sits under solder mask and connects directly to `0.40 mm`-pitch `U3.31`; do not cold-probe `U3.31` — `NT1` is verified cleanly in firmware at Smoke-Test Step 1, `ID = 6`.)*
   - Verify USB-C `Rd` pull-downs on `J1`: probe `0402` resistor pads `R1` (`5.1 kΩ ±1%`) and `R2` (`5.1 kΩ ±1%`) to `GND`.

---

## 3. Current-Limited USB-C First Power-Up (No Battery Attached, Steps 2–4)

1. **Step 2 — Current-limited `5.0 V` apply (`100 mA` compliance via USB-C breakout):**
   - Connect bench PSU `5.00 V / 100 mA` current limit through a USB-C breakout cable to `J1` (note `U5` cold-starts in `USB100` until `+3V3` rises above `1.4 V` on `EN1`).
   - Expected input current (blank flash / ROM USB boot): **`12–28 mA`** (`RP2350A` USB boot + `BQ24073` quiescent + `AW20198` `LED_SDB` disabled via `R31 = 100 kΩ` pull-down). If compliance trips (`> 60 mA`), remove power immediately.
2. **Step 3 — Rail & clock verification:**
   - `TP13` (`VBUS`) = **`4.90–5.05 V`**
   - `TP1` (`VSYS`) = **`4.30–4.50 V`** (`4.40 V` typ, `BQ24073` regulated system output; `~{PGOOD}` low on `GPIO13`)
   - `TP2` (`+3V3`) = **`3.250–3.350 V`** (`< 10 mVpp` AC ripple)
   - `TP4` (`+1V1`) = **`1.067–1.133 V`** (`< 25 mVpp` AC ripple)
   - Scope `C24` (`Y1` `XOUT` `15 pF` cap pad `1` with `10×` `< 10 pF` probe): **`12.000 MHz` sine/clipped wave** (`~0.8–1.8 Vpp`).
3. **Step 4 — USB Full-Speed enumeration & `SW2` (`BOOTSEL`) check:**
   - Connect `J1` to host PC USB port: verify `lsusb` enumerates **`2e8a:000f Raspberry Pi RP2350 Boot`** (`RPI-RP2` mass-storage drive).
   - After flashing test firmware, hold **`SW2`** (`NW` rim `BOOT`, KiCad `(-16.15, -6.20)`) while pulsing `TP5` (`RUN`) low → confirm clean re-entry to `RP2350 Boot`.

---

## 4. Firmware Smoke-Test Sequence & Mandatory Register Rules (Steps 5–6)

> [!CAUTION]
> **Four firmware initialization rules are mandatory on `s2-110-usbc` to prevent silent bus failure, ADC `37%` error, or `SW1/SW2`/LiPo overheating:**
> 1. **`GPIO4` / `GPIO5` (`I2C0`) pad drive = `12 mA` BEFORE first `AW20198` write:** At POR (`LGC = 0`), `AW20198` requires `VIL ≤ 0.40 V` (`1 kΩ` pull-ups `R21/R22` draw `3.3 mA`, giving `0.43 V` at `4 mA` reset drive); set `PADS_BANK0: GPIO4, GPIO5` `DRIVE = 12mA` (`VOL ≈ 0.08–0.14 V`) before starting `I2C0`.
> 2. **`AW20198` `GCR` (`0x00`, Page 0) = `0xB9` (NOT `0x81`!):** Bit 3 is `LGC = 1` (`3.3 V` logic threshold: `VIL ≤ 0.60 V`, `VIH ≥ 2.40 V`, vs POR default `LGC = 0` `1.4 V / 0.4 V`), bits `[7:4] = 0b1011` (`SWSEL`) enable all `11` scan switches (`SW1–SW11`), bit 0 = `CHIPEN = 1`. (`0x81` leaves `LGC = 0` and sets `SWSEL = 1000`, disabling `SW10–SW11`!)
> 3. **Set `OD = 1, IE = 0, PDE = 0, PUE = 0` on `GPIO26` (`ADC0`) and `GPIO27` (`ADC1`) (`rp2350.pdf` p. 1068), clear `PDE = 0, IE = 0` on unused floating GPIOs (`GPIO0, 7..9, 14..18, 20..23`, erratum `RP2350-E9`), and drive `GPIO6` (`LED_SDB`) cleanly low/high (never tri-stated with `IE = 1` across `C35 = 100 nF`):** Wait **`≥ 30 ms`** (`6 τ` for `R11||R12 = 50 kΩ, C7 = 100 nF, τ = 5.0 ms`) after asserting `GPIO28 = 1` (`VBAT_EN`) before sampling `ADC0`, then set `GPIO28 = 0`.
> 4. **Active thermal cap & `U4` XIP mode on `Rev S3C`:** Cap continuous full-white **`GCC ≤ 105`** on pouch-backed battery (`R_th ≈ 35 K/W → ≤ 48 °C` skin / `< 60 °C` LiPo / `< 70 °C` `EVQP7J01P`) and **`GCC ≤ 9` (`0` at low-bat CC, `≤ 24` in CV taper)** whenever **`(GPIO13 ~{PGOOD} == 0) || (GPIO12 ~{CHG} == 0)`** (`≤ 45 °C` LiPo charge ceiling because `BQ24073` `TS` is fixed by `10 kΩ` `R3` and `~{CHG}` goes High-Z on recharge cycles!), plus cold-boot `ADC4` `ΔT ≤ +15 °C` relative throttling. Because `U4.8`'s nearest decoupling cap (`C14`) is `8.56 mm` (`4` vias) away on `Rev S3C`, configure RP2350 `QMI` XIP in **1-bit (`0x0B`) or 2-bit Dual-SPI (`0xBB`)** at `≤ 50–66 MHz` (`SR3.DRV = 25%`) to avoid 4-bit Quad-SPI read SSO droop (`Relocate C22 to U4.8 in Rev S3D`).

### Smoke-Test Checklist
1. **Board ID (`GPIO19..21` with internal pull-ups enabled):** Read `(GPIO21<<2)|(GPIO20<<1)|GPIO19` → expect **`6` (`0b110`)**, then disable pull-ups and clear `IE = 0` on `GPIO20, 21`.
2. **`I2C1` (`GPIO2` SDA / `GPIO3` SCL, `400 kHz`, `R20/R19 = 4.7 kΩ`) accelerometer (`U9` `LIS2DW12` at `0x19`):** Read `WHO_AM_I` (`0x0F`) → expect **`0x44`**; verify `1 g` gravity vector flips cleanly when turning board face-up vs face-down.
3. **`I2C0` (`GPIO4` SDA / `GPIO5` SCL, `1 MHz`, `R21/R22 = 1 kΩ`; set `GPIO6` `LED_SDB = 1`, wait `2 ms`):**
   - Scan `I2C0`: confirm ACK at **`0x20` (`U1`, West, `AD1=GND, AD0=GND`)** and **`0x25` (`U2`, East, `AD1=VCC, AD0=VCC`)** (broadcast `0x5A`).
   - Write `Page 0` (`0xF0 = 0xC0`), `GCR (0x00) = 0xB9`, `GCC (0x01) = 0x40` (`25%` safe bring-up brightness).
   - Walk single R, G, B channels across `D1` (centre `(0, 0)`) through `D110`: confirm all `330` dies illuminate with `0` dead/swapped channels and verify uniform R/G/B colour.
4. **Rim button `SW1` (`GPIO11` via `1 kΩ` `R18`, internal pull-up) & ambient light `Q2` (`GPIO1` → `GPIO27/ADC1`):**
   - Press `SW1` (`NE` rim): confirm `GPIO11` transitions `1 → 0`.
   - Set `GPIO1 = 1`, wait `15 ms` (`~6.8 τ` for `R43 = 22 kΩ, C70 = 100 nF`), sample `ADC1`: confirm `< 0.15 V` covered in dark vs `1.0–2.9 V` under desk lamp (`saturates ~293–470 lx`), then set `GPIO1 = 0`.

---

## 5. LiPo Battery Attach, `XB9901A` Wake & Charge Verification (Step 7)

1. **Verify plug polarity BEFORE mating to `BT1`:** Confirm with DMM on the `Molex 51021-0200` 2-pin plug that **`+` (red, `3.7–4.2 V`) aligns with `BT1` Pin 1 (North/NE pad)** and **`-` (black) aligns with `BT1` Pin 2 (South/SW pad)**.
2. **First-attach `XB9901A` (`U8`) `0 V` lockup wake:** After mating the LiPo to `BT1` with USB unplugged, `TP3` (`VBAT`) may initially read `0.0 V` because `XB9901A` enters power-down on first cell attach (`xb9901a.pdf` p. 7 Note 3). Plug in USB-C (`J1`) briefly (`1–2 s`): charger voltage across `VBAT`/`GND` wakes `U8` out of shipping/lockup state, after which `TP3` reads **`VBAT` (`3.7–4.2 V`)** continuously when USB is unplugged.
3. **Verify `BQ24073` charge current & `Q1` `VBAT` telemetry:**
   - With a partially discharged (`3.7–3.9 V`) `≥ 300 mAh` `403535` cell attached and USB-C at `5.0 V / 500 mA` limit (`LED_SDB = 0`), verify `GPIO13` (`~{PGOOD}`) = `0`, `GPIO12` (`~{CHG}`) = `0`, and charge current into battery (`R4 = 3.0 kΩ` `ISET`) is **`263–328 mA`** (`297 mA` typ), tapering cleanly at **`4.20 V ±1%`**.
   - Trigger `GPIO28 = 1`, wait `30 ms`, read `ADC0`: confirm `2 × V_ADC0` matches DMM voltage on `TP3` within **`±50 mV`**.
4. **Deep-sleep battery current check (`intent` `R17`, before applying Kapton & bonding LiPo):**
   - Feed `3.70 V` (`50 mA` limit) from a bench source / µA meter (e.g. Nordic PPK2 or DMM µA range) into `BT1` (`Pin 1 = +3.70 V`, `Pin 2 = -`), wake `U8` once via USB-C if needed, unplug USB-C, and command firmware into dormant/deep sleep (`GPIO6 LED_SDB = 0`, `GPIO1 = 0`, `GPIO28 = 0`, `LIS2DW12` low-power wake mode, `RP2350` `P1.7` sleep with `RP2350-E9` `IE = 0` / latched pull-downs cleared): confirm steady-state sleep current is **`≤ 85 µA` typ (`68–85 µA` expected, `≤ 135 µA` worst-case max)**.
