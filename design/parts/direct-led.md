# D67 + R80/R81/R82 (pn-dense-1d): centre LED driven directly from RP2350 GPIOs

pn-dense has 67 LEDs, one more than a single AW20198 can drive (18 CS × 11 SW = 66). The user's choice: keep all 67,
drop U2, and drive the centre LED (the Penrose sun's centre vertex at 0, 0) straight from three RP2350 GPIOs, one per
cathode, each through a series resistor, with PWM in firmware.

Datasheets read for this: `datasheets/rp2350.pdf` (§14.8.2 pin types and pin list, §14.9.1 absolute maximum ratings,
§14.9.4 IO electrical characteristics), `datasheets/xl-1615rgbc-rf.pdf` (p. 3 absolute maximum, p. 4 electrical,
p. 5 voltage bins, p. 6 typical curves, p. 8 pinout), `datasheets/aw20198qnr.pdf` (p. 18 scanning timing, DUTY and
I_LED equations), `datasheets/tps7a02.pdf` (p. 6 output accuracy), and the existing audits `leds-xl1615.md`,
`drivers-aw20198.md` and `ldo.md`. Page numbers below are the PDF's page numbers. For rp2350.pdf, the number printed on
the page is one less.

## Parts

| Ref | Part | Value | LCSC | JLC (checked 2026-11-07) |
|---|---|---|---|---|
| D67 | XINGLIGHT XL-1615RGBC-RF | RGB, common anode | C965840 | same part as the matrix LEDs (`leds-xl1615.md`) |
| R80 | UNI-ROYAL 0402WGF1500TCE | 150 Ω 1 % 0402 (red) | C25082 | preferred, stock 749,103, normal |
| R81 | UNI-ROYAL 0402WGF5100TCE | 510 Ω 1 % 0402 (green) | C25123 | basic, stock 2,716,759, normal |
| R82 | UNI-ROYAL 0402WGF5100TCE | 510 Ω 1 % 0402 (blue) | C25123 | basic, stock 2,716,759, normal |

`jlc_parts.py show C25082 C25123`. All values are E24. Green uses 510 Ω, the same part as blue, rather than 560 Ω,
because the 560 Ω 0402 at JLC (C25126) is an extended part. Green is 3.5–4.5× brighter than red and blue (p. 4) and is
scaled down in PWM for white anyway, so the 10 % extra current doesn't matter.

## GPIO choice: GPIO7 (R), GPIO8 (G), GPIO9 (B)

These are QFN-60 pins 10, 12 and 13, on the west side of U3.

- **What's taken:** I2C/ACC/light sensor/LED_SDB on 1–6, ACC_INT 10, BTN 11, CHG/PGOOD 12–13, board-ID straps 19–21,
  UART1 test pads 24/25, VBAT_SENSE 26, LIGHT 27, VBAT_EN 28 and GPIO29 test pad (`sch_gen.py`).
- **What's free:** 0, 7, 8, 9, 14–18, 22 and 23.
- **Why these three:** they are the only three free GPIOs on consecutive pins on one side. Their pads are 8.8–9.9 mm
  from the centre LED. GPIO0 is closer (6.4 mm), but it sits alone on the other end of that side, and GPIO22/23 are on
  the east side.
- **Pin type:** all three are "Digital IO (FT)", reset state pull-down (Table 1427, p. 1336).

## Anode supply: +3V3 (chosen) vs VSYS

### What the RP2350 datasheet allows

| Item | Value | Where |
|---|---|---|
| Voltage at a FT pin, IOVDD = 3.3 V | −0.5 to 5.5 V ("IOVDD must be present") | Table 1433, p. 1340 |
| Voltage at a FT pin, IOVDD = 0 V | −0.5 to 3.63 V | Table 1433, p. 1340 |
| Voltage at a standard pin (incl. GPIO26–29 ADC pins on QFN-60) | −0.5 to IOVDD + 0.5 V | Table 1433, p. 1340 |
| FT pin type | "very little current flows into the pin whilst it is below 3.63 V and IOVDD is 0 V" | Table 1426, p. 1336 |
| Output low voltage, IOVDD = 3.3 V | VOL ≤ 0.5 V at IOL = 2, 4, 8 or 12 mA "depending on setting" (drive strength) | Table 1436, p. 1341 |
| Output high voltage, IOVDD = 3.3 V | VOH ≥ 2.62 V | Table 1436, p. 1341 |
| Pull-down (reset state of every GPIO) | 36–113 kΩ | Table 1436, p. 1341 |
| Total current sunk into GPIO pins | 100 mA max | Table 1436, p. 1341 |
| Default drive strength | 4 mA | Table 1426, p. 1336 |

### Anode on VSYS (3.0–4.5 V, `drivers-aw20198.md`)

- **Pin driven high (3.3 V):** the LED sees VSYS − 3.3 V ≤ 1.2 V. Every die is dark: red conducts from about 1.65 V,
  green and blue from about 2.5 V (I–V curve, p. 6).
- **Pin floating (input, pulls disabled):** the pin rises to VSYS − VF(leakage). The datasheet gives no LED I–V below
  its curve's ~0 mA point, so it gives nothing to bound VF(leakage). Red is the worst die. "No pin ever above IOVDD +
  0.3 V" can't be shown from the datasheet in this state.
- **3V3 off while VSYS is on:** U6's EN is tied to IN (`ldo.md`), so 3V3 follows VSYS. Still, during power-up and
  soft-start, IOVDD lags VSYS, and the FT limit drops to 3.63 V with IOVDD = 0 V.
- **Verdict:** each case is probably fine, but none is provable from the datasheets.

### Anode on +3V3 (chosen)

- **Why it's safe:** the anode and IOVDD are the same rail. With a diode between them, the cathode, and so the pin, can
  never rise above +3V3 = IOVDD. This holds in every state: driven, floating, reset pull-down, and while the rail ramps
  (the LED is then unpowered too). It holds for every pin type, so it would hold even on a non-FT pin.
- **Pin high (VOH ≥ 2.62 V):** the LED sees at most 3.35 − 2.62 = 0.73 V, below every die's turn-on (p. 6), so it's
  off. When driven high with IOVDD = 3V3, it's ~0 V.
- **Reset and boot glow:** the reset pull-down (36–113 kΩ) lets a few tens of µA flow until firmware drives the pins
  high. Green/blue: (3.3 − 2.5) / 36.5 kΩ ≈ 22 µA at most, a faint glow during boot. Red emits nothing below 5 mA by the
  p. 6 luminous curve. Firmware should set GPIO7–9 high early in boot.
- **Cost:** less headroom for green/blue. 3V3 is 3.30 V ±1.5 % (tps7a02.pdf p. 6), and green/blue VF at ~1 mA is about
  2.7–2.8 V typical (p. 6 I–V). Brightness therefore depends on the VF bin. It also falls below VSYS ≈ 3.5 V, where U6
  is in dropout and 3V3 follows VSYS (`ldo.md`). Nothing is ever overstressed, and firmware can trim the PWM per board
  and with VBAT (VBAT_SENSE is on GPIO26).

## Brightness math

**Matrix LED, AW20198 (aw20198qnr.pdf p. 18):**

- I_LED = K / R_EXT × GCC/255 × SL/255 × PWM/256 × DUTY, with K = 400 V and R_EXT = 30 kΩ (R30).
- DUTY is 0.0805: SWSEL = 0000 (all 11 SW active, as on this board), 15.9375 µs PWM period ÷ (0.25 + 5×0.125 + 16 +
  0.125 + 1) µs × 1/11.
- At full scale (GCC = SL = PWM = 255): peak 400 / 30 k = 13.33 mA. The PWM step 255/256 makes it 13.28 mA.
- **Average per die = 13.28 mA × 0.0805 = 1.069 mA.**

**Direct LED:** I = (3V3 − VF − VOL) / R. The 12 mA drive setting is assumed: VOL ≤ 0.5 V at 12 mA, which bounds the
pin at ≤ 42 Ω.

| Die | R | VF (p. 6 I–V, typ) | I at 100 % PWM, typ | Worst low / high (VF bins p. 5 ±0.1 V, 3V3 ±1.5 %, pin 0–42 Ω) | Abs max (p. 3) |
|---|---|---|---|---|---|
| Red | 150 Ω | ~1.95 V at 8 mA | 7.0–9.0 mA | ~5 mA / 11.3 mA | 20 mA DC |
| Green | 510 Ω | ~2.72 V at 1 mA | 1.05–1.14 mA | ~0.4 mA / 2.0 mA | 20 mA DC |
| Blue | 510 Ω | ~2.78 V at 1 mA | 0.94–1.02 mA | ~0.4 mA / 2.0 mA | 20 mA DC |

- **Green and blue:** 100 % PWM gives about the matrix LED's 1.07 mA average. Their luminous curve starts at 0 mA and
  is concave (p. 6), so equal average current gives at least equal brightness. Firmware maps matrix level 255 to
  ~100 %.
- **Red:** p. 6 shows red giving no light below about 5 mA ("Relative Luminous vs Forward Current"). A resistor sized for
  1.07 mA DC would leave it dark. R80 = 150 Ω instead runs red at a matrix-like peak (~8 mA, ≤ 11.3 mA worst case, under
  the 12 mA drive rating). The average is set by PWM duty:
  - Average-current match: 1.069 / 8 ≈ 13 %.
  - Luminance match from the p. 6 curve: about 20 %. The matrix gives ~0.6 relative × 0.0805 = 0.050 (×20 mA-DC
    intensity); this LED gives ~0.25 relative at 8 mA × duty.
  - Firmware should start at 13 % and trim by eye at bring-up.
- **GPIO budget:** at most 11.3 + 2 + 2 ≈ 15 mA sunk, well under the 100 mA total (Table 1436). Each pin stays within
  its 12 mA drive setting.

## Firmware notes

- Set the GPIO7–9 pads to 12 mA drive. Drive them high as early in boot as possible to end the pull-down glow.
- PWM with a slice per pin; low = on.
- Scale: green/blue 100 % ↔ matrix 255; red 13–20 % ↔ matrix 255. Optionally compensate green/blue below VBAT ≈ 3.5 V.
