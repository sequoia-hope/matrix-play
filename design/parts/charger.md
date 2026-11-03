# U5 TI BQ24073RGTR charger and power path

Datasheet: datasheets/bq24075.pdf (SLUS810I, family bq24072/3/4/5/9). Read: electrical tables, pin list, operating modes.
Supplier: `C15220 BQ24073RGTR (TI, QFN-16-EP(3x3)): extended, JLC stock 8360, lifecycle normal, checked 2026-11-02`
Footprint: VQFN-16 3 × 3, RGT; check EP against the mechanical drawing at phase 2.

## Absolute max vs our worst case
| Parameter | Abs max | Our worst case | Margin |
|---|---|---|---|
| IN | 28 V | any charger; OVP 6.6 V suspends operation | OK |
| BAT | 5 V | 4.3 V protection trip | OK |
| IN current | 1.6 A | 500 mA | OK |
| OUT current | 5 A (4.5 rec.) | ~1 A peak | OK |
| ESD HBM | 1.5 kV | Behind USBLC6 on VBUS | note |

## Setup
| Pin | Connection | Reason |
|---|---|---|
| EN1 / EN2 | HI (3V3... see note) / LO | IINmax 450–475–500 mA, USB500 mode, fixed by the chip |
| ISET | 3.0 kΩ to GND | ICHG = KISET / R = 890 / 3000 = 297 mA (797–975 → 266–325 mA) |
| ILIM | 3.6 kΩ to GND | Mandatory: open ILIM disables charging (p.6). 1525 / 3.6 k = 424 mA (369–478) if EN2 is changed |
| TS | 10 kΩ to GND | Pin note: no NTC in use; 75 µA × 10 kΩ = 0.75 V, in the window |
| TMR | floating | Default 5 h limit, 300 mA × 5 h exceeds capacity |
| TD | to GND | Termination enabled |
| CE | to GND | Always enabled |
| CHG, PGOOD | 100 kΩ to 3V3, to GPIO 12, 13 | Open drain; draw only while asserted on USB |
| IN | 1 µF to GND | ≤ 10 µF USB attach limit |
| OUT | 22 µF 10 V 0603 near pins, plus driver caps | 4.7–47 µF range |
| BAT | 10 µF 0603 | 4.7–47 µF |

**EN1 from 3V3 (reviewed):** VIH 1.4 V (p.6). EN pins are read at VIN > VBAT + VIN(DT) and monitored continuously (p.16). Flat cell: 3V3 = 0, so USB100 until OUT and 3V3 rise (~2 ms), then USB500. Works because boot load ~40 mA < 100 mA, with SDB pulled low. Verify at bring-up.

## Calculations
- VO(REG) 4.3–4.4–4.5 V on USB. Dropout 300 mV typ at 1 A. VBUS at J1 ≥ 4.5 V after cable: the DPM loop may reduce charging at a weak source; system still runs.
- Dissipation (p.31): (VIN − VOUT) IOUT + (VOUT − VBAT) IBAT. 5.5 V in, VBAT 3.0 V, 40 mA load: 1.1 × 0.337 + 1.4 × 0.297 = 0.79 W, +31 °C at 39.5 °C/W on JEDEC; thermal regulation at 125 °C protects it.
- Battery sleep: IBAT(PDWN) ≤ 6.5 µA at 85 °C. No typical is given; budget uses it.
- Supplement mode: OUT from BAT through 50 mΩ typ when load exceeds input.
- Term: 0.10 × ICHG = 30 mA (27–33, p.5). Precharge 88 / 3 k = 29 mA. CHG asserts on the first cycle only (Table 3).
- No cold-charge lockout (TS fixed). TMR float: 4–6 h fast, ~3 h needed.
