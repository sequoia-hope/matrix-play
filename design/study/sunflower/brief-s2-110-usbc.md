# Mechanical and layout brief: Sunflower `s2-110-usbc` (Rev S3C)

Phase 4 layout brief for `hw/sunflower/s2-110-usbc/sunflower.kicad_pcb`.
Floorplan drawing: [floorplan-s2-110-usbc.svg](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/floorplan-s2-110-usbc.svg) (rendered PNG: [floorplan.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/floorplan.png)).
Generator geometry: [config.py](file:///home/sequoia/pcb/round-pendant/scripts/sunflower/config.py) (`VARIANTS["s2-110-usbc"]`).

All coordinates `(x, y)` below are in millimetres relative to the board centre `(100.000, 100.000)` (`+x` East, `+y` South, `−y` North / 12-o'clock top rim when worn).

## 1. Board outline and size
- **Outline:** Exact circle on `Edge.Cuts`, diameter **`38.000 mm`** (`R = 19.000 mm`, area `1,134.1 mm²`).
- **Bezel / copper clearance:** Minimum copper-to-edge rule `0.250 mm` (`sunflower.kicad_pro`). Outermost LED centre (`D110`) sits at `r = 17.211 mm`; rotated pad-corner minimum clearance across `D1..D110` is `0.626 mm` to `Edge.Cuts`. Tightest copper-to-edge clearances on the board are `SW1`/`SW2` side pads at `0.282 mm`, `Q2` top-rim light sensor pads at `0.364 mm`, `BT1` mechanical solder tabs at `0.408 mm`, and `J1` front shell legs at `1.012 mm`.

## 2. Mounting holes
- **Count:** **None (`0` mounting holes).** No screw standoffs or conductive chassis contacts exist in this revision; wearable retention/enclosure (if used) grips the rim outside `r > 18.0 mm` with cutouts at `J1` (`≥ 12.5 × 6.7 mm` USB-C overmold recess), `SW1`/`SW2`, and a clear optical aperture over `Q2` at 12 o'clock `(0, −18.20)` (plus an optical baffle between `Q2` and `D65` `2.66 mm` away if covered by a shared front diffuser).

## 3. Connector and rim-part placement

| Ref | Part | Side | Centre `(x, y)` mm | Rot (KiCad) | Facing / Overhang / Mating & Strain Notes |
|---|---|---|---|---|---|
| `J1` | HRO `TYPE-C-31-M-12` 16-pin USB-C | `B.Cu` | `(+0.000, +15.600)` | `180.0°` | South rim (`6 o'clock`), mouth facing **outward (`+y`)**, height **`3.26 ± 0.10 mm`**. Shell front reaches `y = +19.25..+19.30 mm` (`+0.25–0.30 mm` overhang on axis). Four plated shell-leg slots (`±4.32, +12.47` and `±4.32, +16.65`) and two `0.65 mm` NPTH pegs (`±2.89, +13.00`) pass through the board (`F.Cu` annular rings `0.18–0.29 mm` from `D104`/`D10`/`D110`, and `sunflower-B_Paste.gbp` omits paste on the 4 PTH slots: **forbid `F.Cu` wave/hand soldering**; tack outer `B.Cu` slot edges only on `Rev S3C`, and switch to full-SMT `TYPE-C-31-M-22` `C530612` or add `B.Paste` in `Rev S3D`). |
| `BT1` | Molex `53261-0271` 2P PicoBlade 1.25 mm RA | `B.Cu` | `(−11.400, −10.200)` | `−110.0°` (`250°`) | North-West rim (`~10:30`), height **`3.20 +0.20/−0.05 mm` (`3.40 mm` mated)**, body entirely inside board outline (`r_max = 18.731 mm`, `0.269 mm` inside `Edge.Cuts`, pad-to-edge `0.408 mm`, actual `pcbnew` `B.Fab` clearance to `SW2` = **`1.017 mm`**). Mating mouth points inward (`+20.0°` toward `U3`, `3.02 mm` to `0402` `C9`, `4.04 mm` to `U3` NW corner): plug (`51021-0200`, `4.2 mm` long) must be angled in and mated **before** bonding the rear battery, with wires strain-relieved by Kapton tape onto the rear foam spacer (**open — user sign-off at Gate 4**). |
| `SW1` | Panasonic `EVQP7J01P` side-actuated switch (`USER / WAKE`) | `B.Cu` | `(+16.151, −6.200)` | `−69.0°` (`291°`) | North-East rim (`~2 o'clock`, `r = 17.300 mm`), peg-less SMD (`0` through-holes, `0` front LED sites lost). Physical plunger reaches `r = 19.400 mm` (**`+0.400 mm` nominal projection** past `Edge.Cuts`, `+0.200 mm` at `0.2 mm` full travel; `0.00 to −0.20 mm` worst-case tolerance stackup — fingernail-actuated on curved rim; **open — user sign-off**). |
| `SW2` | Panasonic `EVQP7J01P` side-actuated switch (`BOOTSEL`) | `B.Cu` | `(−16.151, −6.200)` | `+69.0°` | North-West rim (`~10 o'clock`, `r = 17.300 mm`), symmetric mirror of `SW1` (`+0.400 mm` nominal plunger projection; pad-to-edge `0.282 mm`). |
| `Q2` | Newopto `XYC-PT19C-L1` phototransistor (0603) | `F.Cu` | `(+0.000, −18.200)` | `0.0°` | North rim (`12 o'clock` top bezel, height `0.80 ± 0.15 mm`) on the LED face so ambient illumination is unoccluded (`r_max = 18.646 mm`, `0.364 mm` pad-to-edge; `2.50 mm` front LED keepout disc). |

## 4. Assembly sides & mandatory reflow sequence
- **Double-sided SMT assembly at JLCPCB:**
  - **Pass 1 — Back (`B.Cu`):** Reflow all `80` `B.Cu` parts first (`U1..U9`, `Q1`, `L1`, `Y1`, THR `J1`, `BT1`, `SW1`, `SW2`, `38` MLCCs, `26` resistors; max height `3.26 mm` at `J1`, `3.20 mm` at `BT1`).
  - **Pass 2 — Front (`F.Cu`, `≤ 245 °C` peak):** Reflow `110 × XL-1615RGBC-RF` (`0.60 mm`, MSL Level 3) and `Q2` (`XYC-PT19C-L1`, `0.80 mm`) in Pass 2 (with pallet/glue support for `J1`/`BT1` on the underside) because `xyc-pt19c-l1.pdf` p. 11 specifies **`Q2` must not be reflowed more than once**.

## 5. Layer count and implemented stackup role (Rev S3C note)
- **4 layers, `1.6 mm` nominal thickness (`JLC04161H-7628`), standard `0.30/0.15 mm` (`0.35/0.15 mm` power) through vias, zero blind/buried vias, zero vias in SMD signal pads (`no POFV`).**
  - **`F.Cu` (`1 oz`):** `110` RGB LEDs + `Q2` pads; radial `CS` cathode triplet tracks along spiral wedges and outer `SW` arcs.
  - **`In1.Cu` (`0.5 oz`):** **Unbroken solid `GND` plane** (`928.8 mm²`, `1` piece) across the entire disc, perforated by via antipads, `J1` through-holes, and `LX cutout L2` (`5.4 mm²`). *(Audit note for Gate 4/5/6/7: because `U3` and `L1` sit on `B.Cu`, `In2.Cu` is the `0.21 mm` adjacent plane while `In1.Cu` is `1.29 mm` away across the core; swapping `In1.Cu ↔ In2.Cu` is recommended if `Rev S3D` is spun.)*
  - **`In2.Cu` (`0.5 oz`):** Inner routing layer — circumferential `SW` scan arcs, cross-wedge `CS` jumps, `VSYS`/`+3V3`/`VBAT` distribution trunks, `I2C0` bus, and `U3` East `+1V1` spoke.
  - **`B.Cu` (`1 oz`):** All logic/power/driver ICs, connectors, buttons, passives, test pads, `RP2350A` (`U3`) regulator zones (`RP2350 ring` `+1V1`, `RP2350 band` `+3V3`, `vendor *` pours), short crystal/USB/QSPI escapes, and solid `GND` exposed pads (`U1.41`, `U2.41`, `U3.61`, `U5.17`).

## 6. Density philosophy
- **Compact wearable density (`0402` standard passives, `0603` only for `10 µF` / `22 µF` bulk MLCCs and `0806` `2.0 × 1.6 mm` `L1`).**
- **No-POFV / signal-pad DFM discipline:** `.kicad_dru` forbids via holes in all `793` SMD signal pads (`no POFV`), allowing standard `0.30/0.15 mm` non-filled through vias only inside the `4` exposed `GND` thermal pads (`U5.17`: `2` in-pad, `U3.61`: `1` in-pad, `U2.41`: `1` in-pad, `U1.41`: `0` in-pad + `5` perimeter). *(Gate 7 audit notes `U5.17` `B.Paste` overlaps its `2` open vias and `U3.61` has `2` total `GND` vias vs `9` on the RPi reference.)*

## 7. Block floorplan and signal/power flow
Ordered from the South/North-West power connectors inward ([floorplan.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/floorplan.png)):
1. **USB-C input & ESD (`South`, `(0, +15.6)` → `(+7.0, +10.7)`):** `J1` at `(0.0, +15.6)` feeds `VBUS` (`C1`, `R1/R2` `5.1 kΩ` `CC1/CC2`) and `USB_D±` into `U7` (`USBLC6-2P6` at `(+7.03, +10.68)`), then north-west through `27 Ω` series resistors (`R14/R15`) into `U3`'s south-facing USB pins (`51/52`, `34.55 / 35.87 mm` total routed copper).
2. **Cell protection & switched `VBAT` divider (`SE / SW`, `(+6.5, +12.8)` & `(−8.2, +12.4)`):** `BT1` at `(−11.4, −10.2)` routes `VBAT` and isolated `BAT_N` (`0.25 mm` `BATTERY` class) across the disc (`29.1 mm` Euclidean) to `U8` (`XB9901A` at `(+6.45, +12.79)`, `R8`, `C6`) and `Q1` (`NTZD3155C` at `(−8.20, +12.40)`, `R9..R12`, `C7`). *(Audit note: co-locating `U8` beside `BT1` in NW is flagged as a `Rev S3D` improvement at Gates 4/6.)*
3. **Power-path charger & `+3V3` LDO (`South-Centre`, `(+3.4, +6.0)` & `(−6.1, +0.4)`):** `U5` (`BQ24073` at `(+3.40, +6.00)`) sits north of `J1`, regulating `VSYS` (`3.55–4.4 V`) to feed both LED drivers east/west and `U6` (`TPS7A0233` LDO at `(−6.10, +0.40)`).
4. **MCU, QSPI flash, `1.1 V` switcher, crystal, accelerometer (`Centre-North`):**
   - `U3` (`RP2350A` at `(−1.40, −6.60)`, `0°`) faces its regulator (`46–50`), USB (`51/52`), and QSPI (`55–60`) edge **South (`+y`)**:
     - `L1` (`3.3 µH` at `(+0.60, +0.60)`) + `C16..C19`/`R13` sit immediately south-east of `U3`.
     - `U4` (`W25Q128JVPIQ` QSPI flash at `(−2.80, +5.40)`, `90°`) sits south of `U3` (`QSPI` routed copper `5.51–13.85 mm ≪ 25 mm`).
     - `Y1` (`12 MHz` crystal at `(−2.70, −14.80)`, `0°`) + `C23/C24/R17` sit north of `U3` pins `21/22` (`XIN = 1.68 mm`, `XOUT = 9.77 mm`, `0` vias, `15.8 mm` from `L1`).
     - `U9` (`LIS2DW12` at `(+4.40, −13.80)`, `180°`) sits north-east of `U3` on dedicated `I2C1`.
5. **East/West LED matrix drivers (`U1` at `(−12.60, +3.00)`, `U2` at `(+12.60, +3.00)`, both `90°`):** Symmetric `25.2 mm` separation across the horizontal chord driving `D1..D55` (West) and `D56..D110` (East).

## 8. Thermal management
- **Heat sources & firmware `ADC4` ceiling:** Continuous pouch-backed battery operation is capped by firmware (`intent` `R19`, `35 K/W`) at `GCC ≤ 105` (`~0.68 W` total → `ΔT ≈ 23 K`, board `≤ 48 °C` at `25 °C` ambient) and `GCC ≤ 9` CC / `≤ 24` CV gated on `~{PGOOD} == 0 || ~{CHG} == 0` during USB charging (`≤ 45 °C` LiPo charge limit with fixed `TS` `R3 = 10 kΩ`), keeping `SW1`/`SW2` (`+70 °C`), `J1` (`+80 °C`), the `403535` LiPo, and skin contact within safe limits.
- **Heat sinking path:** `In1.Cu` continuous `928.8 mm²` `GND` plane + `F.Cu`/`B.Cu` pours spread heat laterally across the `38 mm` disc.

## 9. Art zone
- **Front sunflower seed web (`F.SilkS`, `1,027` graphical segments):** Clipped Voronoi sunflower seed-cell web (`0.153 mm` stroke width, clipped `≥ 0.15 mm` clear of exposed `F.Cu` pads and `Edge.Cuts`) plus concentric rim ring (`0` silk-over-pad violations; minor ink dimples over tented vias accepted).
- **Back (`B.SilkS`):** Functional callouts only (`0` decorative art zones).

## 10. Silkscreen policy
- **Hobby / wearable prototype policy (`design/checks.toml`):** Footprint reference designators hidden on both sides; `28` `B.SilkS` primitives (`5` pin-1 dots + `23` callouts for `PWR`, `BOOT`, `BATT +/-`, `USB 5V`, `LIPO 403535`, `8` ICs, and `8` test pads), supplemented by [bringup-map-bottom.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/bringup-map-bottom.png) (`BOARD_ID = 6` via `NT1`; back board-title omission flagged for user sign-off).

## 11. Keepouts and rule areas
1. **Front LED keepouts (`config.py` `front_keepouts`):** `6` discs (`r = 1.75–2.35 mm`) around `J1`'s `6` holes + `r = 2.50 mm` around `Q2`.
2. **`LX cutout L2`:** `5.4 mm²` plane cutout under `U3.48`/`L1.2` (currently on `In1.Cu`; flagged for `In2.Cu` swap in `Rev S3D`).
3. **`B.Cu` inductor window (`L1 window`):** Disallows non-`LX`/`+1V1` copper under `L1`.
4. **Solid exposed-pad rule areas (`U1/U2/U3/U5 solid EP`):** Disallow non-`GND` copper/vias inside exposed pads.
5. **RP2350 ring rule areas (`U3 ring`, `U3 ring vias`):** Keep `+1V1` `RP2350 ring` `1` whole piece (`6.06 mm²`; outer `+3V3` `RP2350 band` splits into `4` pieces — audited at Gate 7/10).
6. **Rear `Ø35.0 mm` `403535` battery stack:** Overlaps both `J1` (`3.26 mm` tall) and `BT1` (`3.40 mm` mated) as well as `13` of `14` bare `B.Cu` test pads — requires **`0.05 mm` Kapton tape** over test pads plus a **`≥ 2.4 mm` insulating foam/carrier spacer** over the central `0.75–1.00 mm` ICs so the pouch is supported flat without cantilevering onto `J1`/`BT1` (**open — user sign-off**).

## 12. Test, debug, and bring-up provisions
- **`14` bare `1.0 mm` `B.Cu` test pads (`0` `B.Paste`):** `TP1` (`VSYS`), `TP2` (`+3V3`), `TP3` (`VBAT`), `TP4` (`+1V1`), `TP5` (`RUN`), `TP6` (`SWCLK`), `TP7` (`SWDIO`), `TP8` (`GND` — clip `J1` shield shell as South `GND` return during SWD/rail probing), `TP11` (`I2C_SDA`), `TP12` (`I2C_SCL`), `TP13` (`VBUS`), `TP14` (`UART_TX`), `TP15` (`UART_RX`), `TP16` (`GPIO29_TP`), all probed **before** bonding the LiPo (`bringup-s2-110-usbc.md`).
- **Hardware board-ID strap (`NT1`):** Ties `GPIO19` to `GND` (`ID = 6`).
- **Isolation jumpers:** Explicitly omitted on `38 mm` wearable disc; all load blocks boot disabled (`LED_SDB = 0`, `VBAT_EN = 0`, `LIGHT_PWR` high-Z).
