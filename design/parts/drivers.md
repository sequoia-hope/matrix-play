# U1, U2: Lumissil IS31FL3741A-QFLS4-TR

Datasheet: datasheets/is31fl3741a.pdf (Rev. C, 2020-03-16). Read: all 23 pages; Figure 2 and land pattern as images.
Supplier: `C2940604 IS31FL3741A-QFLS4-TR (ISSI, QFN-60-EP(7x7)): extended, JLC stock 455, lifecycle normal, checked 2026-11-02`
Footprint: project footprint from p.22: pads 0.22 × 0.74 mm at 0.40 mm, inner ends 6.05 mm apart, EP 5.40 mm. Pin map from p.3.

## Absolute max vs our worst case
| Parameter | Abs max | Our worst case | Margin |
|---|---|---|---|
| VCC | 6.0 V | VSYS 4.5 V (BQ24073 VO(REG) max) | OK |
| Input pins | VCC + 0.3 V | 3V3 fed from VSYS, so ≤ VSYS; SDA, SCL, SDB, INTB | OK by construction |
| VCC operating | 2.7–5.5 V | 3.0–4.5 V; firmware stops at 3.3 V | OK |
| TJ | 150 °C | see below | OK |

## Required external parts (Figure 2, p.2)
| Datasheet | Ours |
|---|---|
| PVCC pin 15: 1 µF + 0.1 µF | C_PVCC1 1 µF, 100 nF |
| PVCC pin 25: 1 µF + 0.1 µF | C_PVCC2 1 µF, 100 nF, plus 22 µF bulk per driver |
| AVCC pin 14: 1 µF + 0.1 µF | 1 µF, 100 nF |
| I2C pull-ups 2 kΩ (figure); 1 kΩ at 1 MHz (p.7) | 1 kΩ, one pair for the bus |
| INTB pull-up 100 kΩ | 100 kΩ each to 3V3 |
| SDB 100 kΩ + 0.1 µF to GND | 100 kΩ + 100 nF each |
| ISET 10 kΩ | 30 kΩ, below |
| ADDR to GND | U1 GND = 0x30; U2 VSYS = 0x33 (Table 1, p.7: 01100 + ADDR bits) |
| 51 Ω / 20 Ω CS resistors at 5 V | Omitted: decisions.md |
| GND pins 12, 36, 55 and EP | Tied to GND |

## Calculations
- IOUT = (383 V / RISET) × (GCC/256) × (SL/256), p.17. 30.0 kΩ at GCC = SL = 255: 12.67 mA. ILED = IOUT / 10.125 = 1.25 mA.
- Full white: 702 × 1.25 = 878 mA, + 2 × 3.6 mA ICC.
- Scan peak: 39 × 12.67 = 494 mA per driver; 988 mA if both align.
- Headroom (review corrected): SW 550 mV at 800 mA scaled to 494 mA = 340 mV. CS not scaled: a sink's saturation voltage is not linear in current, so 350 mV typ, 600 mV max (p.5). VBAT for a full-white row: 2.8 + 0.34 + 0.35 + 0.16 = 3.65 V typ; top bin and max headroom ~4.2 V. Firmware lowers GCC as VBAT falls.
- Path drop: cell and leads ~100 mΩ assumed, XB9901A 11.5 mΩ, BQ24073 BAT–OUT 50 mΩ typ → ~0.16 Ω × 988 mA ≈ 160 mV on an all-on row with both drivers aligned.
- Dissipation at the 300 mA firmware limit (150 mA each): battery 4.2 V, mean LED Vf ≈ 2.53 V → 1.67 V × 150 mA = 0.25 W. Red-only on USB, 4.5 V: (4.5 − 1.95) × 150 mA = 0.38 W. θJA 33.1 °C/W is a 76 × 114 mm JEDEC board; expect about double here: +15 to +25 °C. At the 439 mA per-driver hardware max: 0.73 W on battery, +24 °C; not a sustained case.
- Bulk: 22 µF 10 V 0603 (C86295), about half its value at 4.4 V. With τ = 0.16 Ω × 11 µF ≈ 1.8 µs ≪ 32 µs it filters edges and does not hold the row. The drop above stands. Cell absent on USB: charger 475 mA max against 1 A pulses gives ~0.5 V ripple, acceptable; firmware may stagger the two drivers' scan.
- I2C at 1 MHz: 702 × 9 bits = 6.3 ms, plus page unlock and addressing ~0.4 ms = 6.7 ms. Pull-ups 3.3 V / 1 kΩ = 3.3 mA.

## Fine print
- LGC bit must be 1 (VIL 0.6 V, VIH 2.4 V, p.6, PG4 00h, p.14): RP2350 VOL max 0.5 V exceeds the default VIL 0.4 V. LGC powers up 0 and resets on 3Fh = 0xAE, so its own write is received at VIL 0.4 V. Use 12 mA drive on GPIO4/5 (~0.15 V at 3.3 mA): works in practice, not by spec; measure at bring-up, at 400 kHz first.
- ADDR strap to SCL or SDA exists (p.7); not used.
- Thermal pad needs "16 or 25" vias (p.19). 6-layer through vias land in the EP; these also carry return current.
- SDB rising edge resets I2C. "If VCC has risk drop below 1.75 V but above 0.1 V during SDB low, re-initialize all registers" (p.19): firmware always re-inits on wake.
- Ghosting: firmware sets 32 kΩ pull-ups/pull-downs (p.18).
- ICC 3.6 mA typ with PWM = 0 (p.5): hold SDB low when blank.
- Shutdown 0.5 µA typ, 1 µA max at 3.6 V (p.5). Note 1: keep away from antennas: no radio here.

## Layout
- Caps close to pins, ground side to chip GND; RISET close, ground side to chip GND (p.19). 

## Open questions
- Which CS triplet and SW line drive each LED: phase 4, with the matrix map.
- Red's Vf and driver reverse bias: off LEDs see ≤ VSYS 4.5 V reverse against VR 5 V (LED p.3). Thin margin, OK.
