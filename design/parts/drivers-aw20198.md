# U1, U2, U10, U11: Shanghai Awinic AW20198QNR (Parallelogram 4-Layer Study)

Datasheet: `datasheets/aw20198qnr.pdf` (V1.1, Dec 2021, 40 pages). Read: all 40 pages; Figure 1–2 (pp. 1–2), Pin Configuration & Description (pp. 2–3), Typical Application & RGB Mapping (p. 5), Electrical Characteristics (pp. 6–8), I²C 16-Address Table (pp. 11–12), Current & Duty Equations (pp. 18–20), Register Map (pp. 24–34), PCB Layout Considerations (p. 35), and QFN-40 `5 × 5 mm` Package Outline & Land Pattern (pp. 37–38).
Supplier: `C5137654 AW20198QNR (AWINIC(Shanghai Awinic Tech), QFN-40L(5x5)): extended, JLC stock 6055, lifecycle normal, checked 2026-11-05` (`~$1.06` qty 1 / `~$0.78` qty 10+).
Footprint: `round_pendant:AW20198_QFN-40-1EP_5x5mm_P0.4mm_EP3.4x3.4mm`, verified against mechanical drawing & recommended land pattern pp. 37–38 (`5.00 × 5.00 × 0.75 mm` body, `40 × 0.40 mm` pitch peripheral leads, `3.40 × 3.40 mm` solid exposed ground pad `Pin 41` with `2 × 2` solder-paste stencil windows, `40 × 0.20 × 0.60 mm` lands centered at `±2.30 mm` -> inner `±2.00 mm`, outer `±2.60 mm = 5.20 mm` span, `0.30 mm` EP-to-pad gap, `0.20 mm` pad-to-pad gap).

## Why AW20198QNR is ideal for the low-cost 4-layer parallelogram family
1. **High local JLCPCB stock & lowest cost per RGB channel:** `6,055` in stock at JLCPCB (`$0.78` at qty 10+), driving **`18 CS × 11 SW = 198` dots = `66` Common-Anode RGB LEDs per chip** (`$0.012 / RGB LED` driver cost vs `$0.044 / RGB LED` global-sourced WLCSP-36).
2. **4-layer friendly `0.40 mm` QFN-40 geometry:** `0.20 mm` pad-to-pad and `0.30 mm` EP-to-pad clearances pass standard `0.10 mm` (`4 mil`) 4-layer JLCPCB trace/space rules (`JLC04161H-7628`) with standard `0.30/0.15 mm` through-vias (`0.40 mm` center-to-center pitch matching the `0.40 mm` QFN pin pitch) and zero BGA / zero blind-buried vias.
3. **Grouped pinout by side (Top View, p. 2 Fig. 2):**
   - **West (`1..10`):** `1=SW8, 2=SW6, 3=SW4, 4=SW2, 5=PVCC, 6=SW1, 7=SW3, 8=SW5, 9=SW7, 10=SW9`
   - **South (`11..20`):** `11=SW11, 12=CS18, 13=CS17, 14=CS16, 15=CS15, 16=PGND, 17=CS14, 18=CS13, 19=CS12, 20=CS11`
   - **East (`21..30`):** `21=CS10, 22=VCC, 23=GND, 24=AD1, 25=AD0, 26=EN, 27=SCL, 28=SDA, 29=ISET, 30=SYNC`
   - **North (`31..40`):** `31=CS9, 32=CS8, 33=CS7, 34=CS6, 35=CS5, 36=CS4, 37=CS3, 38=CS2, 39=CS1, 40=SW10`
   - **Exposed Thermal Pad (`41`):** `GND` (`3.40 × 3.40 mm` solid copper, stitched with `5–6 × 0.30/0.15 mm` `GND` thermal vias directly to the unbroken `In1.Cu` `GND` plane; `0` foreign vias permitted).

## Absolute max vs our worst case
| Parameter | Datasheet (pp. 6–7) | Our worst case | Margin |
|---|---|---|---|
| Supply voltage `VCC`, `PVCC` | −0.3 V to +6.0 V abs (`2.7–5.5 V` op) | `VSYS = 3.0–4.5 V` (`BQ24073` `VO(REG)`) | ≥ 1.5 V |
| Logic / address pins `SCL, SDA, EN, AD0, AD1` | −0.3 V to `VCC + 0.3 V` | `+3V3` fed from `VSYS` (`≤ VSYS`); `AD0/AD1` strapped to `GND, VCC(VSYS), SCL, SDA` | OK by construction |
| Package thermal resistance `θJA` | `33 °C/W` (`QFN-40 5×5 mm`, p. 6) | `~0.12–0.25 W` per IC (`ΔT ≈ 4–8 °C`) | > 60 °C margin |

## Required external parts & strapping (p. 5 Fig. 5, pp. 11–12, p. 35)
- **`PVCC` (`pin 5`) & `VCC` (`pin 22`):** Tied to `VSYS` (`Note 2` p. 2 & p. 35: `PVCC` and `VCC` connect to the same rail externally), each decoupled locally by `1 µF` (`C52923`) + `100 nF` (`C1525`) `0402` (`100 nF` closest to pin), plus shared `22 µF` `0603` bulk decoupling (`C30`, `C40`).
- **`GND` (`pin 23`), `PGND` (`pin 16`), Thermal Pad (`pin 41`):** Connected directly to the solid `In1.Cu` `GND` plane.
- **`ISET` (`pin 29`):** `R_EXT = 30.0 kΩ` 1% `0402` (`C25776`, Basic) to `GND`.
  - Per p. 18 Eq.: $I_{\max} = \frac{400}{R_{\text{EXT}}} = \frac{400}{30\text{ k}\Omega} = 13.33\text{ mA}$ peak per `CS` sink (`≤ 60 mA` rating).
  - Peak switch current (`18` active `CS` channels): $18 \times 13.33\text{ mA} = 240\text{ mA}$ (`≪ 990 mA` `SDCR = 000` rating, p. 7).
  - Duty cycle (`SWN = 1010` = `SW1..SW11` active, p. 19 Table 4): $\text{DUTY} = \frac{244}{275.5 \times 11} = 0.0805$ (`1 / 12.42`), giving $I_{\text{LED,avg}} = 13.33 \times 0.0805 = 1.07\text{ mA}$ per color at full `GCC = SL = PWM = 255` (and `1.31 mA` when scanning 9 rows `SW1..SW9`, `DUTY = 0.0984`).
- **`EN` (`pin 26`):** Shared `LED_SDB` (`GPIO6`) active-high chip enable; internal `1 MΩ` pull-down (`p. 3`) plus external `100 kΩ` (`R31`) + `100 nF` (`C35`). Sleep standby current (`EN = L`): `1.3 µA` typ per IC (`p. 7`).
- **`SCL` (`pin 27`), `SDA` (`pin 28`):** `1 MHz` Fm+ I²C (`R21 = R22 = 1 kΩ` to `+3V3`). Set `GCR.LGC = 1` (`00h` bit 7, p. 25; `VIH = 2.4 V`, `VIL = 0.6 V`, p. 7) on init.
- **`AD1` (`pin 24`), `AD0` (`pin 25`) I²C 7-bit Addresses (Table 1, p. 12):**
  - `U1`: `AD1 = GND, AD0 = GND` → `0x20` (`0100000b`)
  - `U2`: `AD1 = VCC(VSYS), AD0 = VCC(VSYS)` → `0x25` (`0100101b`)
  - `U10`: `AD1 = GND, AD0 = SCL` → `0x22` (`0100010b`)
  - `U11`: `AD1 = GND, AD0 = SDA` → `0x23` (`0100011b`)
- **`SYNC` (`pin 30`):** Unconnected (`NC`); internal `1 MΩ` pull-down (`p. 3`), defaults to internal clock oscillator (`CLKOE = 0, CLKSEL = 0`, p. 22).

## Companion Low-Cost BOM Parts Audited for Parallelogram Variants
- **Peg-less side buttons `SW1, SW2` — Panasonic `EVQP7J01P` (`C2828254`):**
  - Datasheet: `datasheets/evqp7j01p.pdf` p. 2 ("No. 1 EVQP7J: With straight terminals, Without boss", `1.6 N`, `3.5 × 2.9 × 1.35 mm`, `100,000` cycles).
  - Stock: `6,971` at JLCPCB, lifecycle `normal`, checked `2026-11-05`.
  - Land pattern (`round_pendant:SW_Panasonic_EVQP7J`): identical `4 × 1.40 × 1.05 mm` SMD pads at `(±1.80, ±0.725) mm` as `EVQP7C01P`, with **zero NPTH boss holes**, leaving the `F.Cu` skewed LED grid 100% unperforated along the East and West edges.
- **Top-bezel light sensor `Q2` — Newopto `XYC-PT19C-L1` (`C2693594`) / Everlight `ALS-PT19` (`C146233`):**
  - Datasheet: `datasheets/xyc-pt19c-l1.pdf` pp. 4, 6, 8 (`1.6 × 0.8 × 0.8 mm` `0603` phototransistor, `2 × 0.80 × 0.80 mm` lands on `1.50 mm` centers, Pin 1 Collector mark side, Pin 2 Emitter — 100% footprint- and pin-identical to `ALS-PT19` `round_pendant:SENSOR_ALS-PT19`).
  - Stock: `25,206` at JLCPCB (`~$0.015`), lifecycle `normal`, checked `2026-11-05`. (`IPH = 30 µA` typ at `100 lx`, `0.66 V` across `R43 = 22 kΩ`; `ALS-PT19` `C146233` remains a direct drop-in if photopic IR-filtered `630 nm` response is preferred.)
