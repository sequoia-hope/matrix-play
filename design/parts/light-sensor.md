# Q2 — Ambient Light Sensor (`ALS-PT19-315C/L177/TR8`)

- **Reference:** `Q2` (Variant E, front LED side at 12-o'clock top rim)
- **MPN:** `ALS-PT19-315C/L177/TR8` (Everlight Electronics)
- **Supplier:** LCSC `C146233`, extended, JLC stock `0` (global-sourced alongside `C2678907` / `L1`, or same-footprint alternate Tonyu `DYWH-ALS-PT19-315C/4T` `C47416518`), lifecycle `normal`, checked `2026-11-05`
- **Datasheet read:** `design/datasheets/als-pt19.pdf` (Everlight `DLS-0000039` Rev. 8, `2018-02-12`)
- **Package & Footprint:** `1.7 × 0.8 × 0.6 mm` miniature SMD (`0603` class), `round_pendant:SENSOR_ALS-PT19` (`2 × 0.80 × 0.80 mm` SMD lands on `1.50 mm` centres, `2.30 × 0.80 mm` overall land span)

## Pinout & Connectivity (`als-pt19.pdf` p. 2, p. 6)

| Pin | Name | Net | Connected to | Notes |
|---:|---|---|---|---|
| `1` | Collector (`C`, pin-1 mark end) | `/MCU/LIGHT_PWR` | `U3` pin `3` (`GPIO1`) | GPIO-switched `3.3 V` supply (`0 µA` sleep draw when `GPIO1` driven low / hi-Z) |
| `2` | Emitter (`E`) | `/MCU/LIGHT` | `U3` pin `41` (`GPIO27/ADC1`), `R43.1`, `C70.1` | Analog voltage node `Vout = IPH × RL` |

## Operating Conditions & Calculations (`als-pt19.pdf` pp. 3–6)

1. **Supply Voltage (`VCC`):**
   - Recommended range: `2.5 V` to `5.5 V` (abs max `-0.5 V` to `6.0 V`, p. 3).
   - Driven from RP2350 `GPIO1` (`IOVDD = +3V3 = 3.3 V`), well within `2.5–5.5 V`.
   - Maximum collector current before emitter saturates (`Vout(sat) = VCC - VCE(sat) = 3.3 - 0.4 = 2.9 V`):
     $$I_{C,\max} = \frac{3.3\text{ V}}{22\text{ k}\Omega} = 150\text{ }\mu\text{A}$$
     At `150 µA`, RP2350 GPIO output drop is `< 5 mV` (`4 mA` drive setting), and sleep current with `GPIO1 = 0` is **`0 µA`** (preserving the `< 85 µA` sleep budget in `intent.md`).

2. **Spectral Response (`λp`, `Λ`, p. 4 & Fig. 3):**
   - Peak sensitivity `λp = 630 nm`, spectral passband `390–700 nm` (human-eye photopic response with infrared rejection, unlike unfiltered `850/940 nm` silicon phototransistors).

3. **Load Resistor `R43 = 22 kΩ` (`0402`, `C25768`, Basic, 1%) & ADC Range (p. 4, p. 6):**
   - White fluorescent / LED illumination (`Note 2`, `Ev = 100 lx`): `IPH1 = 5 µA` min, `15 µA` typ (`~14.7 µA` at `3.3 V` per Fig. 4 `0.98×` curve) → `Vout(100 lx) ≈ 15 µA × 22 kΩ = 0.33 V` (`~410` counts on 12-bit `3.3 V` ADC; dim indoor `10 lx` gives `~33 mV` ≈ `41` counts).
   - Bright indoor (`1000 lx` fluorescent, `IPH2 = 50 µA` min, `150 µA` typ): saturates smoothly at `Vout(sat) ≈ 2.9 V` (`~900–1000 lx` full scale, matching indoor/dusk auto-brightness control where LED dimming matters most; outdoor daylight cleanly rails at `2.9 V` = max brightness).

4. **Filter Capacitor `C70 = 100 nF` (`0402` `X7R` `16 V`, `C1525`, Basic):**
   - Placed on `B.Cu` directly beside `R43` (`LIGHT` to `GND`).
   - RC time constant `τ = 22 kΩ × 100 nF = 2.2 ms` (`fc = 72 Hz`), attenuating `100/120 Hz` mains flicker and adjacent LED matrix scan edges while providing a low-impedance charge reservoir (`100 nF >> C_ADC`) for `RP2350` `ADC1` sampling. Firmware should set `GPIO1 = 1`, wait `≥ 10 ms` (`~4.5 τ`), sample `ADC1`, and clear `GPIO1 = 0`.

5. **Placement & Optical Cross-Talk:**
   - Placed on `F.Cu` (LED side) at the **12-o'clock top rim** (`(-1.87, -18.00 mm, 15°)`) facing outward with the LEDs, clearing adjacent LEDs `D116` (`1.90 mm`) and `D115` (`2.44 mm`). Firmware can sample `ADC1` during a brief blanking interval (or scale against known adjacent PWM duty) if self-illumination rejection is desired.
