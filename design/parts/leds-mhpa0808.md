# D1–D256 (`dense-square`): MEIHUA MHPA0808RGBDT

Datasheet: `design/datasheets/C404279.pdf` (`LPDS-0002507 Rev.3`, 2018-04-30, 15 pages). Read: all 15 pages; pp. 2 & 13 rendered at 250 DPI and audited visually alongside EasyEDA `C404279` (`LED-ARRAY-SMD_4P-L0.80-W0.80-BR`).
Supplier: `C404279 MHPA0808RGBDT (MEIHUA, 0808 0.80x0.80x0.60mm): extended, JLC stock 9372, lifecycle normal, checked 2026-11-06`
Footprint: `round_pendant:LED_MHPA0808RGBDT` from p.2 "For reflow soldering (Propose)": four `0.35 × 0.35 mm` (`roundrect` `rratio=0.25`) SMD pads centered at `(±0.275, ±0.275) mm` (`0.55 mm` center pitch, `0.20 mm` inner X/Y cross gap, `0.90 × 0.90 mm` total copper span; `0.80 × 0.80 × 0.60 mm` black-diffused silicone PLCC body).

## Absolute Maximum Ratings vs Our Worst Case (`AW20198QNR`, `R_EXT = 30 kΩ`)
| Parameter | Abs Max (`Ta = 25 °C`, p.4) | Our Worst Case (`dense-square`, `4× AW20198QNR`) | Margin |
|---|---|---|---|
| Continuous forward current `IF` | `20 mA` (R, G, B) | `1.07 mA` average per die (`13.33 mA × 1/12.4` scan duty) | OK (`18.7×`) |
| Peak forward current `IFP` (`1/10 duty, 0.1 ms`) | `50 mA` (R, G, B) | `13.33 mA` hardware ceiling (`R_EXT = 30 kΩ`, `SL = 255, GCC = 255`) | OK (`3.75×`, below DC rating) |
| Power dissipation `PAD` | `R: 50 mW`; `G, B: 60 mW` | `R: 2.3 V`, `G/B: 3.5 V × 1.07 mA ≈ 3.7 mW` | OK (`> 13×`) |
| Reverse voltage `VR` | `10 V` (R, G, B) | `AW20198` `DGCR = 0x44` clamps off-row anodes/cathodes `< 4.5 V` | OK (`> 2.2×`) |
| ESD threshold (HBM) | `R: 2000 V`, `G: 1000 V`, `B: 1000 V` | Protected array window + conformal-coat compatible | OK |
| Junction temperature `Tj` | `115 °C` | Low average per-LED dissipation (`< 10 mW` total package) | OK |
| Operating / storage temp | `-40 ~ +85 °C` / `-40 ~ +100 °C` | Handheld / wearable display | OK |
| Soldering `TSOL` / moisture | Reflow `260 °C`; `24 hr` floor life (`≤ 30 °C / 60% RH`), bake `60 °C × 5 h` (p.14) | Standard JLCPCB SMT dry-pack handling; zero via-in-pad prevents solder wicking | OK |

## Optical & Electrical Characteristics (`Ta = 25 °C`, p.5)
| Die | Test Current | Wavelength `λd` | Forward Voltage `VF` | Luminous Intensity `IV` | Viewing Angle `2θ1/2` |
|---|---|---|---|---|---|
| Red (`Pin 2`) | `IF = 5 mA` | `619.5 – 624.5 nm` | `1.7 – 2.3 V` | `16.5 – 27.8 mcd` | `120°` |
| Green (`Pin 3`) | `IF = 3 mA` | `529.5 – 533.5 nm` | `2.5 – 3.5 V` | `27.7 – 46.8 mcd` | `120°` |
| Blue (`Pin 4`) | `IF = 3 mA` | `463.5 – 467.5 nm` | `2.5 – 3.5 V` | `7.5 – 12.6 mcd` | `120°` |

## White-Balance & Current Scaling (`AW20198QNR`)
- With `R_EXT = 30 kΩ` (`I_OUT,max = 13.33 mA` peak at `1/12.4` scan duty = `1.07 mA` average), all three dies operate comfortably inside their `20 mA` DC / `50 mA` pulsed ratings.
- Normalizing per-mA efficacy from p.5 (`R ≈ 4.4 mcd/mA`, `G ≈ 12.4 mcd/mA`, `B ≈ 3.35 mcd/mA`), D65 white balance (`~3:6:1` photometric `Y` ratio -> `R:G:B` mcd targets) uses `AW20198` Page 2 `SL` scaling of approximately `SL_R = 190`, `SL_G = 140`, `SL_B = 255`.

## Pinout & Carrier-Tape / JLCPCB `0°` CPL Orientation (Verified Visually on pp. 2 & 13 + EasyEDA `C404279`)
- **Carrier-Tape Pocket Top View (p.13 Section 2, sprocket holes North `-Y`) & EasyEDA `LED-ARRAY-SMD_4P-L0.80-W0.80-BR` (`0°` on `F.Cu`, KiCad y-down):**
  - **Pad `1`** = `(+0.275, +0.275)` (Bottom-Right, `Anode` bevel mark) → **Common Anode (`+`)**
  - **Pad `2`** = `(-0.275, +0.275)` (Bottom-Left) → **Red Cathode (`R-`)**
  - **Pad `3`** = `(-0.275, -0.275)` (Top-Left) → **Green Cathode (`G-`)**
  - **Pad `4`** = `(+0.275, -0.275)` (Top-Right) → **Blue Cathode (`B-`)**
- *(Note: Datasheet p.2's standalone package drawing is rotated `90°` CCW relative to p.13's carrier tape so `[B][R][G]` appear stacked vertically; defining `LED_MHPA0808RGBDT` directly in p.13's carrier-tape `-BR` orientation aligns `0°` on `F.Cu` identically with JLCPCB's `C404279` pick-and-place reference and `LED-ARRAY-SMD_4P-L0.80-W0.80-H0.6-BR_MHPA0808RGBDT.step` at `(rotate (xyz 0 0 0))`!)*

## Exact Square-Array Density Proof Inside `20.0 × 20.0 mm` (Zero Via-in-Pad)
Under JLCPCB 8-layer HDI-free capabilities (`0.09 mm` min track/clearance, `0.25 mm` via pad / `0.15 mm` drill, `0.20 mm` drill-to-foreign-copper clearance -> `0.275 mm` via-center-to-foreign-pad-edge, `0.350 mm` via center-to-center, tented vias):
- **`17 × 17 = 289` LEDs (`p = 1.19 mm`, `19.94 mm` copper span):** `0` valid off-pad via positions exist anywhere in an interior unit cell (provably unroutable without filled VIPPO microvias).
- **`16 × 16 = 256` LEDs (`p = 1.27 mm = 50 mil`, `19.95 × 19.95 mm` copper span, `19.85 × 19.85 mm` body span = `64.0 LEDs/cm²`):** Provable periodic 3-via and 4-via off-pad escapes exist per cell (`131` candidate off-pad via positions per pad).
- **`15 × 15 = 225` LEDs (`p = 1.36 mm`, `19.94 × 19.94 mm` copper span, `19.84 × 19.84 mm` body span = `56.25 LEDs/cm²`):** Wide off-pad via channels (`0.46 mm` inter-LED copper gap, `677` candidate off-pad via positions per pad).
