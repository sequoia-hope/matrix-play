# Bench Bring-Up & Smoke-Test Plan — Round Pendant Variant `f-usbc`

Board: [round-pendant.kicad_pcb](../hw/round-pendant/f-usbc/round-pendant.kicad_pcb) (`Ø38.0 mm`, 8-layer `1.0 mm` ENIG POFV, `235× XL-1010RGB-YG` + `5× IS31FL3745-CLS4-TR` WLCSP-36 + `RP2350A` + `BQ24073` + `TYPE-C-31-M-22` USB-C).
Assembly drawings & renders: [assembly-top.pdf](renders/round-pendant-f-usbc/assembly-top.pdf), [assembly-bottom.pdf](renders/round-pendant-f-usbc/assembly-bottom.pdf), [schematic.pdf](renders/round-pendant-f-usbc/schematic.pdf).

> [!IMPORTANT]
> **Complete Steps 1–4.1 BEFORE soldering a LiPo battery to `BT1` (`round_pendant:BatteryPads`).** All `8` bare `Ø1.0 mm` test pads (`TP1..TP8`) sit on `B.Cu` inside the `Ø35 mm` rear battery footprint. After bring-up passes, mask `U8` temporarily with a strip of Kapton tape while hand-soldering `BT1`, verify `BT1.2 (-)` ↔ `GND` is not bridged (`U8` `XB9901A` `U8.1..3` sits `0.300 mm` CAD / `~0.20 mm` LPI dam west of `BT1.2`), insulate `TP1..TP8` and `BT1` joints with **`0.05 mm` Kapton tape**, and mount the **`403535` round LiPo pouch** (`35 mm` round × `4.0 mm` thick, `~400–450 mAh`) on a **`3.3–3.5 mm` foam standoff** matching `J1`'s `3.16–3.26 mm` shell height (leaving `(105.8..110.0, 115.6..117.8)` ahead of `J1`'s mouth clear of tape/foam).

---

## 1. Test-Pad & Connector Probe Map (`B.Cu`)

Coordinates `(X, Y)` below are KiCad sheet coordinates (`board center = (100.000, 100.000) mm`). **When viewing `B.Cu` directly from the back, horizontal `X` is mirrored** (`X > 100` `SE` `J1` appears on the **left**, and `X < 100` `W` `TP8`/`TP5`/`U8` appears on the **right**).

| Ref | Net | KiCad `(X, Y)` (`mm`) | Offset from Center `(ΔX, ΔY)` | Expected Unpowered `R` to `GND` | Expected Powered Voltage / Signal |
|---|---|---|---|---|---|
| `TP8` | `GND` | `(84.774, 100.552)` | `(-15.23, +0.55)` W | `0.0 Ω` (`< 0.1 Ω` to `J1` shell) | `0.000 V` reference (`J1` shell also `GND`) |
| `J1.A4B9` / `C1.1` | `VBUS` | `(102.980, 108.800)` (`C1.1` `0402`) | `(+2.98, +8.80)` SE | `> 100 kΩ` (`C1 = 1 µF` ramp) | **`4.75–5.25 V`** on USB-C (`0.0 V` on battery) |
| `TP1` | `VSYS` | `(107.400, 104.300)` | `(+7.40, +4.30)` ESE | `> 50 kΩ` (`> 50 µF` MLCC ramp) | **`4.30–4.50 V`** (`4.40 V` typ, `BQ24073` `VO(REG)`) on USB; **`VBAT - <0.06 V`** on battery |
| `TP3` | `VBAT` | `(104.000, 117.500)` | `(+4.00, +17.50)` S | `> 1 MΩ` (`Q1` off, `C5 = 10 µF`) | **`3.50–4.20 V`** with LiPo (`~0–4.2 V` float without cell) |
| `TP2` | `+3V3` | `(106.233, 93.450)` | `(+6.23, -6.55)` ENE | `> 50 kΩ` (`TPS7A0233` output) | **`3.250–3.350 V`** (`3.30 V ±1.5%`) |
| `TP4` | `+1V1` | `(106.252, 95.597)` | `(+6.25, -4.40)` ENE | `> 10 kΩ` (`RP2350` buck output) | **`1.067–1.133 V`** (`1.10 V ±3%`) |
| `TP5` | `/MCU/RUN` | `(85.061, 98.306)` | `(-14.94, -1.69)` W | `> 100 kΩ` (internal pull-up on power) | **`3.25–3.33 V`** (short to `GND` to reset `U3`) |
| `TP6` | `/MCU/SWCLK` | `(106.900, 86.200)` | `(+6.90, -13.80)` NNE | High-Z | `RP2350A` SWD clock (`U3` Pin 24) |
| `TP7` | `/MCU/SWDIO` | `(109.073, 85.590)` | `(+9.07, -14.41)` NNE | High-Z | `RP2350A` SWD data (`U3` Pin 25) |
| `BT1.1` | `VBAT` (`+`) | `(101.600, 117.100)` | `(+1.60, +17.10)` S | `> 1 MΩ` to `BT1.2` | Battery `+` (`1.60 × 2.40 mm` solder pad, labeled `+`) |
| `BT1.2` | `/Power/BAT_N` (`-`) | `(98.400, 117.100)` | `(-1.60, +17.10)` S | Open in UVLO/ship (`0.0 Ω` once `U8` awake) | Cell `-` to `U8` (`XB9901A` pins `4,5`, `1.60 × 2.40 mm` pad, labeled `-`) |

---

## 2. Step 1 — Unpowered Visual & Ohmmeter Check

1. **Optical / microscope inspection:**
   - **`J1` (`TYPE-C-31-M-22`, SE rim):** Confirm all `4` gull-wing SMD shell tabs (`S1`, `2.30 × 1.80 mm`) and all `12` rear signal/power fingers have uniform wetting with zero solder bridges across the `0.50 mm`-pitch center pins (`B8, A5, B7, A6, A7, B6, A8, B5`). On `F.Cu`, verify the two `Ø0.65 mm` NPTH holes sit cleanly in the mask web between **`{D234, D235, D231, D226}`** (`NPTH #1` at `(109.953, 108.684)`) and **`{D76, D66, D74, D64}`** (`NPTH #2` at `(104.671, 111.030)`) with zero peg protrusion (`0.15–0.45 mm` recessed below `F.Cu`).
   - **`U1, U2, U10, U11, U12` (`IS31FL3745` WLCSP-36):** Confirm coplanar seating and `A1` alignment against the `5` `B.SilkS` `OD = 0.30 mm` `A1` dots outside each courtyard.
   - **`Q2` (`ALS-PT19`, 12-o'clock `F.Cu` rim):** Confirm collector mark aligns with `Pad 1` (West, `(97.214, 82.038)`) matching the `F.SilkS` pin-1 dot.
2. **Cold DMM resistance checks (`< 0.5 V` ohmmeter mode, probing `TP1..TP8`, `BT1`, `C1`, `R1`, `R2` only — never `0.4 mm` QFN or `0.5 mm` WLCSP balls):**
   - Rail-to-`GND` (`TP8` or `J1` shell): confirm **no shorts** (`> 10 kΩ` steady-state after MLCC charge) on `C1.1` (`VBUS`), `TP1` (`VSYS`), `TP3` (`VBAT`), `TP2` (`+3V3`), and `TP4` (`+1V1`).
   - Battery pads: confirm `BT1.1 (+)` ↔ `BT1.2 (-)` reads **`> 1 MΩ`**, and confirm unpowered `BT1.2 (-)` ↔ `TP8` (`GND`) reads **open (`> 100 kΩ`)** prior to `U8` wake (verifying no solder bridge across the `0.300 mm` CAD / `~0.20 mm` LPI `B.Mask` dam to `U8.1..3`).
   - USB-C sink `Rd` resistors: probe `0402` resistors `R1` (`(93.90, 115.57)`) and `R2` (`(91.75, 115.49)`) → confirm **`5.1 kΩ ±1%`** each to `GND`.

---

## 3. Step 2 — Current-Limited USB-C First Power-Up (No Battery)

1. Set a bench supply to **`5.00 V`, `100 mA` current limit** (`BQ24073` starts in `USB100` until `+3V3 > 1.4 V` raises `EN1` into `USB500`, [charger.md](parts/charger.md)) and feed `J1` via a USB-C breakout cable (test both plug orientations!).
2. **Expected quiescent input current (blank flash / ROM boot, `LED_SDB` pulled low by `R31 = 100 kΩ`):** **`14–30 mA`**. Cut power immediately if current hits compliance (`> 60 mA`).
3. **Measure every rail against datasheet limits:**
   - `C1.1` (`VBUS`): **`4.90–5.05 V`**
   - `TP1` (`VSYS`): **`4.30–4.50 V`** (`4.40 V` typ, `BQ24073` `VO(REG)`)
   - `TP2` (`+3V3`): **`3.250–3.350 V`** (`TPS7A0233PDQNR` `±1.5%`, `< 10 mVpp` ripple)
   - `TP4` (`+1V1`): **`1.067–1.133 V`** (`RP2350A` core buck `1.10 V ±3%`, `< 25 mVpp` ripple)
4. **USB 2.0 Full-Speed enumeration (`12 Mbit/s`) in both USB-C orientations:**
   - Plug `J1` into a host PC with a standard USB-C cable (flip plug `180°` and repeat): confirm `lsusb` enumerates **`2e8a:000f Raspberry Pi RP2350 Boot`** (`RPI-RP2` UF2 drive) in **both** orientations (proving `R1` `CC1`, `R2` `CC2`, `A6/B6` `DP1/DP2`, `A7/B7` `DN1/DN2`, `U7` `USBLC6-2P6`, and **`R14/R15` (`27 Ω`)** series termination resistors).
   - Hold `SW2` (`NW` rim `BOOTSEL`) while pulsing `TP5` (`RUN`) to `GND` → confirm clean UF2 bootloader re-entry.

---

## 4. Step 3 — Firmware Smoke Test & Mandatory `IS31FL3745` / `RP2350` Init

1. **`RP2350A` errata & pad setup ([rp2350-core.md](parts/rp2350-core.md)):**
   - **Clear RP2350 default pad pull-downs (`PDE = 0` in `PADS_BANK0`)** on all externally pulled-up pins (**`GPIO2, GPIO3, GPIO4, GPIO5, GPIO11, GPIO12, GPIO13`** — `I2C1`, `I2C0`, `SW1`, `~CHG`, `~PGOOD`) immediately on boot; leaving `PDE = 1` burns `~50–150 µA` across the external pull-ups and breaks the `≤ 85 µA` sleep budget.
   - Set `PADS_BANK0: GPIO4 (SDA), GPIO5 (SCL)` drive strength to **`12 mA`** before enabling `I2C0` (`1 kΩ` pull-ups `R21/R22` draw `3.3 mA`; `IS31FL3745` POR `LGC = 0` requires `VIL ≤ 0.40 V`, [drivers-bga.md](parts/drivers-bga.md)).
   - Set `OD = 1, IE = 0, PDE = 0, PUE = 0` on analog inputs `GPIO26/ADC0` (`VBAT_SENSE`) and `GPIO27/ADC1` (`LIGHT`), and clear `IE = 0, PDE = 0` on unused GPIOs (`RP2350-E9`).
2. **`I2C1` (`GPIO2` SDA / `GPIO3` SCL, `400 kHz`) accelerometer (`U9` `LIS2DW12TR` at `0x19`):**
   - Read `WHO_AM_I (0x0F)` → expect **`0x44`**; verify `±1 g` Z-axis sign flip when inverting the pendant.
3. **`I2C0` (`GPIO4` SDA / `GPIO5` SCL, `1 MHz`) `5× IS31FL3745-CLS4-TR` LED matrix (`D1..D235`):**
   - Drive `GPIO6` (`LED_SDB`) = `1`, wait `2 ms`, and scan `I2C0`: confirm ACK from all **5** drivers ([drivers-bga.md](parts/drivers-bga.md) p. 7):
     - `U1` = **`0x20`** (`ADDR2=GND, ADDR1=GND`)
     - `U2` = **`0x22`** (`ADDR2=GND, ADDR1=SDA`)
     - `U10` = **`0x25`** (`ADDR2=SCL, ADDR1=SCL`)
     - `U11` = **`0x26`** (`ADDR2=SCL, ADDR1=SDA`)
     - `U12` = **`0x2F`** (`ADDR2=VSYS, ADDR1=VSYS`)
   - Unlock command register (`0xFD = 0xC5`), select Page 2 (`0xFE = 0x02`), and write:
     - `Configuration (0x00)`: set **`LGC = 1`** (`3.3 V` I2C thresholds), **`SWS = 0011`** (`SW1..SW8`, `1/8` scan duty), **`SSD = 1`** (normal operation), and set **`PHC = 1`** (`180°` phase shift) on `U2` and `U11` to halve `VSYS` ripple.
     - `De-Ghosting (0x02) = 0x33` (`2 kΩ` off-time discharge only).
     - `Global Current Control (0x01) = 0x40` (`25%` bring-up limit; cap continuous wearable dissipation to **`≤ 0.50 W` / `~100 mA` average total LED current** (`300 mA` / `1.26 W` for short bursts only), blank LEDs except `< 5 mA` indicator when `~CHG == 0`, and implement closed-loop `RP2350` `ADC4` thermal foldback starting at **`42 °C` while charging** and **`47 °C` while discharging**).
   - Step single R, G, and B dots across all `235` LEDs (`D1..D235`): verify `705/705` dies light with zero open/shorted channels, particularly in the re-routed southern sector (`D63..D91, D190..D235`).
4. **Rim button `SW1` (`GPIO11`) & ambient light sensor `Q2` (`ALS-PT19`, `GPIO1` → `GPIO27/ADC1`):**
   - Press `SW1` (`NE` rim) → confirm `GPIO11` (`U3` Pin 15) reads `0`.
   - Set `GPIO1 = 1` (`LIGHT_PWR`, `U3` Pin 3), wait **`≥ 10 ms`** (`4.5 τ` for `R43 = 22 kΩ, C70 = 100 nF`, [light-sensor.md](parts/light-sensor.md)), read `ADC1`: confirm `< 0.05 V` dark vs `~0.33 V @ 100 lx` / `~2.9 V` under bright lamp, then clear `GPIO1 = 0`.

---

## 5. Step 4 — Battery Attach, `XB9901A` First-Wake, Charge & Sleep Current

1. **Sleep-current check before soldering LiPo (`intent.md` `≤ 85 µA` budget):**
   - Connect a `3.80 V` source (`50 mA` limit) with series µA meter (e.g. PPK2) to **`BT1.1 (+)`** `(101.60, 117.10)` and **`BT1.2 (-)`** `(98.40, 117.10)`. Briefly attach `5 V` USB-C at `J1` (`1 s`) to wake `U8` (`XB9901A` enters `0 V`-charger lockup on initial cell attach per `xb9901a.pdf` p. 7 Note 3), remove USB-C, confirm **`PDE = 0`** is cleared on `GPIO2–5, 11, 12, 13`, and enter deep sleep (`LED_SDB = 0` [`GPIO6`], `LIGHT_PWR = 0` [`GPIO1`], **`VBAT_EN = 0` [`GPIO14`, `U3` Pin 18]**, `U9` low-power wake, `RP2350` dormant): confirm **`≤ 85 µA`** (`~18–55 µA` expected).
2. **LiPo soldering & `BQ24073` charge check (`R4 = 3.0 kΩ` → `297 mA` typ; check `403535` C-rate):**
   - *Cell C-rate check before soldering:* `R4 = 3.0 kΩ` (`C25784`) programs `ICHG = 297 mA` (`266–325 mA`, `0.66C–0.81C` on a `400–450 mAh` `403535` cell). Verify the procured `403535` cell datasheet permits `≥ 0.8C` charge; if rated `≤ 0.5C`, swap `0402` `R4` (`(99.20, 109.40)`) to **`4.3 kΩ` (`207 mA`) or `4.7 kΩ` (`189 mA`)**.
   - Temporarily mask `U8` (`X ≤ 97.3 mm`) with a strip of Kapton tape while hand-soldering cell `+` (red) to `BT1.1 (+)` and cell `-` (black) to `BT1.2 (-)` (dress wire leads northward toward the board interior and avoid iron contact south of `BT1` at `Y > 118.3 mm`, where `CC1` passes `0.114 mm` south under LPI soldermask), remove the temporary mask, inspect under magnification that no solder or wire strand bridges across the `0.300 mm` CAD (`~0.20 mm` LPI) mask dam to `U8.1..3` (and re-confirm `BT1.2 (-)` ↔ `TP8` reads open before waking `U8`), wake `U8` via USB-C (`5.0 V / 500 mA` limit, `LED_SDB = 0`), and verify `~PGOOD = 0` (`GPIO13`), `~CHG = 0` (`GPIO12`), charge current **`266–325 mA`** (`297 mA` typ with `3.0 kΩ`), and `4.20 V ±1%` CV termination.
   - Set **`GPIO14 = 1` (`VBAT_EN`, `U3` Pin 18)**, wait `≥ 30 ms` (`R9 = R10 = 100 kΩ`, `C7 = 100 nF`), sample `ADC0` (`GPIO26`, `U3` Pin 40, `VBAT_SENSE`), and confirm `2 × V_ADC0` matches `TP3` within `±50 mV`, then clear **`GPIO14 = 0`**.
