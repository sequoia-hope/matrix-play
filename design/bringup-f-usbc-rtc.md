# Bench Bring-Up & Smoke-Test Plan — Round Pendant Variant `f-usbc-rtc` (`Rev FUR`)

Board: [round-pendant.kicad_pcb](../hw/round-pendant/f-usbc-rtc/round-pendant.kicad_pcb) (`Ø38.0 mm`, 8-layer `1.0 mm` ENIG POFV, `235× XL-1010RGB-YG` + `5× IS31FL3745-CLS4-TR` WLCSP-36 + `RP2350A` + `BQ24073` + `TYPE-C-31-M-22` USB-C + inward `A1251WR-S-2P` `1.25 mm` battery socket `BT1` + `RX8130CE:BB` RTC `U13`).
Assembly drawings & renders: [assembly-top.pdf](renders/round-pendant-f-usbc-rtc/assembly-top.pdf), [assembly-bottom.pdf](renders/round-pendant-f-usbc-rtc/assembly-bottom.pdf), [schematic.pdf](renders/round-pendant-f-usbc-rtc/schematic.pdf).

> [!IMPORTANT]
> **1. Complete Steps 1–3.5 on USB-C BEFORE plugging a `1.25 mm` LiPo battery into `BT1` (`CJT A1251WR-S-2P`, `C225111`).**
> **2. MANDATORY `1.25 mm` LiPo Plug Polarity Verification:** Commercial 2-pin `1.25 mm` (`MX1.25` / PicoBlade) LiPo packs ship in **both** Red/Black orientations (`~50/50` across vendors). Although `U8` (`XB9901A`, `xb9901a.pdf` p. 1) blocks reverse battery voltage when USB is unplugged, `R8` (`100 Ω` `0402`, `62.5 mW` rated) would dissipate `~122 mW` continuously under reverse hookup (and connecting USB while reversed stresses `U8`/`U5`). Before mating the plug into `BT1`, hold the plug aligned with `BT1`'s NNE mouth and verify with a DMM that the **Red (`+`) wire aligns with `BT1.1` (`VBAT`, marked `+` on `B.SilkS`, NW rear pin at `(87.521, 112.376)`)** and the **Black (`-`) wire aligns with `BT1.2` (`BAT_N`, marked `-` on `B.SilkS`, SE rear pin at `(88.625, 112.962)`)**. If reversed, gently lift the two plastic crimp-housing lances with a needle/tweezers and swap the two contacts in `10 s` before plugging in!
> **3. Rear LiPo Mechanical Stackup & Ultrasonic Prohibition:** **NEVER ultrasonic-clean the assembled PCB** (`U13` `RX8130CE:BB` built-in `32.768 kHz` tuning-fork crystal can fracture per `ETM50E-10` §12.2.(3) p. 20!). Insulate `TP1..TP8` with **`0.05 mm` Kapton tape**, mate the `1.25 mm` plug into `BT1` **before** adhering the rear battery (`4.88 mm` flat runway to `0.80 mm`-tall `U4`), and mount the **`403535` round LiPo pouch** (`35 mm` round × `4.0 mm` thick, `~400–450 mAh`) on a **`3.3–3.5 mm` foam standoff** flush with `J1` (`3.26 mm`) and `BT1` (`3.20 mm`).

---

## 1. Test-Pad, Connector & RTC Probe Map (`B.Cu`)

Coordinates `(X, Y)` below are KiCad sheet coordinates (`board center = (100.000, 100.000) mm`). **When viewing `B.Cu` directly from the back, horizontal `X` is mirrored** (`X > 100` East `J1`/`U13` appears on the **left**, and `X < 100` West `BT1`/`TP8`/`TP5` appears on the **right**).

| Ref | Net | KiCad `(X, Y)` (`mm`) | Offset `(ΔX, ΔY)` | Expected Unpowered `R` to `GND` | Expected Powered Voltage / Signal |
|---|---|---|---|---|---|
| `TP8` | `GND` | `(84.774, 100.552)` | `(-15.23, +0.55)` W | `0.0 Ω` (`< 0.1 Ω` to `J1.S1` / `BT1.MP`) | `0.000 V` reference (`J1` shell & `BT1.MP` = `GND`) |
| `C1.1` | `VBUS` | `(102.980, 108.800)` | `(+2.98, +8.80)` SE | `> 100 kΩ` (`C1 = 1 µF` ramp) | **`4.75–5.25 V`** on USB-C (`0.0 V` on battery) |
| `TP1` | `VSYS` | `(107.400, 104.300)` | `(+7.40, +4.30)` ESE | `> 50 kΩ` (`> 50 µF` MLCC ramp) | **`4.30–4.50 V`** (`4.40 V` typ) on USB; **`VBAT - <0.06 V`** on battery |
| `TP3` | `VBAT` | `(95.250, 116.750)` | `(-4.75, +16.75)` SSW | `> 1 MΩ` (`Q1` off, `C5 = 10 µF`) | **`3.50–4.20 V`** with LiPo (`~0–4.2 V` float without cell) |
| `TP2` | `+3V3` | `(106.233, 93.450)` | `(+6.23, -6.55)` ENE | `> 50 kΩ` (`TPS7A0233` + `U13`) | **`3.250–3.350 V`** (`3.30 V ±1.5%`, always-on RTC rail) |
| `C76.1` | `/MCU/RTC_VOUT` | `(116.870, 102.050)` | `(+16.87, +2.05)` E | `> 100 kΩ` (`C76 = 1 µF`) | **`~1.5–3.3 V`** internal regulated `RX8130CE` `VOUT` (`0402` pad) |
| `R32.2` | `/MCU/RTC_INT` | `(115.260, 98.350)` | `(+15.26, -1.65)` E | `~100 kΩ` to `+3V3` (`R32`) | **`3.30 V`** idle (`0.0 V` open-drain active-low on RTC alarm/timer) |
| `TP4` | `+1V1` | `(106.252, 95.597)` | `(+6.25, -4.40)` ENE | `> 10 kΩ` (`RP2350` buck output) | **`1.067–1.133 V`** (`1.10 V ±3%`) |
| `TP5` | `/MCU/RUN` | `(85.061, 98.306)` | `(-14.94, -1.69)` W | `> 100 kΩ` | **`3.25–3.33 V`** (short to `GND` to reset `U3`) |
| `TP6` / `TP7` | `SWCLK` / `SWDIO` | `(106.900, 86.200)` / `(109.073, 85.590)` | NNE | High-Z | `RP2350A` SWD debug (`U3` Pins `24, 25`) |
| `BT1.1` | `VBAT` (`+`) | `(87.523, 112.376)` | `(-12.48, +12.38)` SW | `> 1 MΩ` to `BT1.2` | `A1251WR-S-2P` rear NW pin (`+`, `VBAT`) |
| `BT1.2` | `/Power/BAT_N` (`-`) | `(88.627, 112.963)` | `(-11.37, +12.96)` SW | Open in UVLO/ship (`0.0 Ω` awake) | `A1251WR-S-2P` rear SE pin (`-`, `BAT_N` -> `U8.4/5`) |

---

## 2. Step 1 — Unpowered Visual & Cold DMM Check

1. **Optical / microscope inspection:**
   - **`J1` (`TYPE-C-31-M-22`, SSE rim):** Confirm all `4` `S1` gull-wing SMD shell tabs (`2.30 × 1.80 mm`) and `12` rear signal fingers have uniform wetting with zero bridges, and confirm `2× Ø0.65 mm` NPTH holes on `F.Cu` (`{D234, D235, D231, D226}` and `{D76, D66, D74, D64}`) show zero peg protrusion.
   - **`BT1` (`CJT A1251WR-S-2P`, SW `(89.200, 110.550, -28°)`):** Confirm both `2.10 × 3.00 mm` `MP` mechanical tabs (`GND`) and both rear `0.80 × 1.60 mm` signal leads (`BT1.1 VBAT`, `BT1.2 BAT_N`) are cleanly reflowed at `CPL = 208.00°`, mouth facing NNE (`+28°` E of N) toward `U4` (`4.88 mm` nominal / `4.65 mm` min flat plug runway to `U4`, `5.85 mm` to `C22`).
   - **`U13` (`RX8130CE:BB`, East `(114.750, 101.200, 0°)`):** Confirm Pin-1 chamfer (`SW` corner `(113.65, 102.75)`) matches the `B.SilkS` `OD = 0.30 mm` pin-1 dot and all `10` ceramic castellated/bottom lands wet cleanly (`C75` `100 nF` at `1.23 mm` east of Pin `8`, `C76` `1 µF` at `1.23 mm` east of Pin `9`).
   - **`U1, U2, U10, U11, U12` (`IS31FL3745` WLCSP-36) & `Q2` (`ALS-PT19`):** Confirm `A1` / collector alignment against pin-1 dots.
2. **Cold DMM resistance checks (`< 0.5 V` ohmmeter, probing test/passive pads only):**
   - Rail-to-`GND` (`TP8`): confirm `> 10 kΩ` steady-state on `C1.1` (`VBUS`), `TP1` (`VSYS`), `TP3` (`VBAT`), `TP2` (`+3V3`), `TP4` (`+1V1`), and `C76.1` (`RTC_VOUT`).
   - `BT1`: confirm `BT1.1 (+)` ↔ `BT1.2 (-)` reads **`> 1 MΩ`**, `BT1.MP` ↔ `TP8` reads **`< 0.1 Ω`**, and unpowered `BT1.2 (-)` ↔ `TP8` reads **open (`> 100 kΩ`)** before `U8` wake.
   - USB-C `Rd`: probe `R1` (`(102.50, 116.24)`) and `R2` (`(104.51, 117.00)`) → confirm **`5.1 kΩ ±1%`** each to `GND`.

---

## 3. Step 2 — Current-Limited USB-C Power-Up & Enumeration (No Battery)

1. Set bench supply to **`5.00 V`, `100 mA` current limit** into `J1` (test both USB-C orientations).
2. **Expected quiescent current (blank flash / ROM boot, `LED_SDB` low):** **`14–30 mA`**.
3. **Verify rails:** `C1.1 (VBUS) = 4.90–5.05 V`, `TP1 (VSYS) = 4.30–4.50 V`, `TP2 (+3V3) = 3.250–3.350 V`, `TP4 (+1V1) = 1.067–1.133 V`, `R32.2 (RTC_INT) = 3.25–3.35 V`.
4. **USB 2.0 Full-Speed enumeration (`12 Mbit/s`):** Confirm `2e8a:000f Raspberry Pi RP2350 Boot` (`RPI-RP2`) enumerates in **both** USB-C plug orientations; verify `SW2` (`BOOTSEL`) + `TP5` (`RUN`) UF2 re-entry.

---

## 4. Step 3 — Firmware Smoke Test (`RP2350`, `RX8130CE` RTC, `LIS2DW12` & `235` LEDs)

1. **Mandatory `RP2350A` pad setup ([rp2350-core.md](parts/rp2350-core.md)):**
   - **Clear default pad pull-downs (`PDE = 0`, `PUE = 0` in `PADS_BANK0`)** on all externally pulled-up pins (**`GPIO2, GPIO3, GPIO4, GPIO5, GPIO11, GPIO12, GPIO13, GPIO19`** — `I2C1`, `I2C0`, `SW1`, `~CHG`, `~PGOOD`, **`RTC_INT`**!). Leaving `PDE = 1` on `GPIO19` creates a `100 kΩ / 50 kΩ` divider (`~1.1 V` phantom low + `22 µA` leak)!
   - Set `GPIO4, GPIO5` (`I2C0`) drive strength to **`12 mA`** (`1 kΩ` pull-ups `R21/R22`).
   - Set `OD = 1, IE = 0, PDE = 0, PUE = 0` on `GPIO26/ADC0` (`VBAT_SENSE`) and `GPIO27/ADC1` (`LIGHT`), and `IE = 0, PDE = 0` on unused GPIOs (`RP2350-E9`).
2. **`I2C1` (`GPIO2` SDA / `GPIO3` SCL, `400 kHz` max) — `U9` (`LIS2DW12` @ `0x19`) & NEW `U13` (`RX8130CE:BB` @ `0x32`):**
   - Scan `I2C1` at `100–400 kHz`: confirm ACK from **`0x19`** (`U9`, `WHO_AM_I 0x0F == 0x44`) **and** **`0x32`** (`U13` `RX8130CE:BB`, [rtc-rx8130ce.md](parts/rtc-rx8130ce.md)).
   - **Mandatory `RX8130CE:BB` initialization sequence (`ETM50E-10` §10.1 Fig. 14 p. 17, §18.1–18.3 pp. 55–57):**
     1. Wait **`> 30 ms` (`t_CL`)** after `+3V3` POR, issue **1 dummy I2C read** of `1Dh` (ignore ACK/NACK to clear any half-clocked bus state), then read Flag Register `1Dh` (note `ETM50E-10` Table 7 p. 15's `0.95 s` I2C bus timeout).
     2. **If `VLF` (`1Dh` bit 1) == `1` (cold power-up / crystal starting):** note that `30 ms` (`t_CL`) is only the wait before *reading* `VLF`, whereas crystal start-up is **`t_str = 0.19 s` typ, `1.0 s` max** (`Table 4` p. 12, `Fig. 42` p. 55: *"VLF cannot be cleared to 0 until internal oscillation starts"*). (If `+3V3` could have been at `0 V` for `< 10 s`, first write the §18.2 Software Reset sequence p. 56.) Poll writing `1Dh = 0x00` every **`25–50 ms` (up to `1.2 s` timeout)** until reading `1Dh` returns **`VLF == 0`**.
     3. Pulse `INIEN` once and lock backup charger off (`ETM50E-10` §15.5 Table 35 Note 1 p. 42 & §18.3 Fig. 44 p. 57): write `1Fh = 0x10` (`INIEN = 1, CHGEN = 0`), then write **`1Fh = 0x00`** (**`INIEN = 0, CHGEN = 0`** — mandatory when `VBAT` Pin `10` is tied to `+3V3` per §4.2 EX7!), and write `30h = 0x00` (clear `Digital Offset`).
     4. Write Extension Register **`1Ch = 0xC0`** (`FSEL1:0 = 11b` in bits `[7:6]`, `TE = 0` in bit `4`): **disables the POR-default `32.768 kHz` `FOUT` output driver**, dropping `U13` active current from `3.5 µA` to **`1.50 µA` typ**!
     5. Set `STOP = 1` (`1Eh = 0x40`), write BCD calendar `10h..16h` (e.g., `2026-11-09 18:30:00`), clear `STOP = 0` (`1Eh = 0x00`), wait `2.000 s`, and read back `10h`: confirm seconds incremented by `+2`!
   - **Hardware RTC Wake (`POWMAN` `PWRUP2` on `GPIO19`, `U3` Pin `31` — `ETM50E-10` §13.2 Table 12 p. 22 & §18.7 Fig. 48 p. 59):**
     1. Stop timer first by writing **`1Ch = 0xC2`** (`FSEL = 11b` [`FOUT = OFF`], **`TE = 0`** [bit 4], `TSEL = 010b` [`1 Hz` source clock]).
     2. Clear `TF = 0` (`1Dh = 0x00`) and enable timer interrupt by writing **`1Eh = 0x10`** (`TIE = 1`, `STOP = 0, TEST = 0, TSTP = 0, TBKE = 0`).
     3. Load the 16-bit wakeup counter (`1Ah` = LSB weights `1..128`, `1Bh` = MSB weights `256..32768`; both reset to undefined `X`!): write **`1Ah = 0x02`** and **`1Bh = 0x00`** (`2` ticks @ `1 Hz` -> `1.0–2.0 s` first period per Fig. 20 p. 29).
     4. Arm `RP2350` `POWMAN` `PWRUP2` (`SOURCE = 19`, Offset `0x94`) for active-low wake on `GPIO19` (`U3` Pin `31`), then start the countdown by writing **`1Ch = 0xD2`** (**`TE = 1`** in bit `4`!).
     5. Put `RP2350` into `POWMAN` dormant/off (`P1.4` / `P1.7`): confirm `U13.~IRQ` (`Pin 6`) pulls `RTC_INT` (`R32.2` / `GPIO19`) to `0.0 V` (`t_RTN2 = 7.57 ms` min auto-release pulse, Table 16 p. 28) within `1.0–2.0 s` and wakes `RP2350` cleanly; read `1Dh` to confirm `TF == 1`, then write `1Ch = 0xC0` (`TE = 0`) and `1Dh = 0x00` (`TF = 0`)!
3. **`I2C0` (`1 MHz`) `5× IS31FL3745` (`0x20, 0x22, 0x25, 0x26, 0x2F`) & `235` LEDs (`D1..D235`):**
   - Set `GPIO6 (LED_SDB) = 1`, set `LGC = 1`, `SWS = 0011`, `PHC = 1` on `U2/U11`, `GCC ≤ 0x40` (`≤ 0.51 W` continuous wearable ceiling; blank LEDs while `~CHG == 0`; `ADC4` foldback at `42 °C` charge / `47 °C` wear), and verify all `705` R/G/B dies light cleanly.
4. **Rim button `SW1` (`GPIO11`) & ambient light sensor `Q2` (`GPIO1` → `ADC1`):** Verify `SW1` active-low press and `Q2` dark vs lamp response (`≥ 10 ms` settle).

---

## 5. Step 4 — `BT1` LiPo Plug-In, `XB9901A` Wake, Charge & Dormant + RTC Wake Current

1. **Dormant + RTC timed-wake current check (`< 250 µA` budget):**
   - Feed `3.80 V` (`50 mA` limit) via a `1.25 mm` test pigtail into `BT1` (`Pin 1 = +3.80 V`, `Pin 2 = Return` via µA meter), wake `U8` with a `1 s` `5 V` USB-C pulse at `J1`, remove USB-C, confirm `PDE = 0` on `GPIO2–5, 11–13, 19`, `U13` `FSEL = 11b` (`FOUT = OFF`), `LED_SDB = 0`, `LIGHT_PWR = 0`, `VBAT_EN = 0` (`GPIO14`), and enter `RP2350` dormant with `U13` wakeup timer running: confirm total battery current is **`~20–205 µA` (`< 250 µA` budget)**, and confirm `U13` wakes the pendant cleanly on schedule!
2. **`403535` LiPo plug-in & `BQ24073` charge verification (`R4 = 3.0 kΩ` → `297 mA` typ):**
   - Verify `403535` cell C-rate (`R4 = 3.0 kΩ` = `297 mA`; swap `R4` to `4.3–4.7 kΩ` if cell requires `≤ 0.5C`) and **verify plug Red (`+`) = `BT1.1 (+)` / Black (`-`) = `BT1.2 (-)` with a DMM before mating!**
   - Mate plug straight along the SSW axis (`28°` W of S) into `BT1`'s NNE mouth, wake `U8` via USB-C (`5.0 V / 500 mA` limit, `LED_SDB = 0`), verify `~PGOOD = 0`, `~CHG = 0`, `266–325 mA` CC charge, `4.20 V ±1%` CV termination, and `GPIO14 = 1` (`VBAT_EN`, `≥ 30 ms` wait) `ADC0` (`VBAT_SENSE`) `2 × V_ADC0 == V_TP3 ± 50 mV`.
