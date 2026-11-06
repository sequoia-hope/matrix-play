# D1–D132 (p1-66, p2-132): XINGLIGHT XL-1615RGBC-RF

Datasheet: datasheets/xl-1615rgbc-rf.pdf. Read: all 15 pages; p.8 rendered and audited visually (`/tmp/xl1615-p8-08.png`).
Supplier: `C965840 XL-1615RGBC-RF (XINGLIGHT, SMD-4P,1.6x1.5mm): extended, JLC stock 718328, lifecycle normal, checked 2026-11-05`
Footprint: `round_pendant:LED_XL-1615RGBC` from p.8 Recommended Soldering Pattern: four `0.45 × 0.65 mm` rectangular SMD pads at `(±0.625, ±0.475) mm` (`1.25 mm` X pitch, `0.80 mm` inner X gap; `0.95 mm` Y pitch, `0.30 mm` inner Y gap; `1.70 × 1.60 mm` total copper span).

## Absolute max vs our worst case (AW20198QNR, R_EXT = 30 kΩ)
| Parameter | Abs max (`Ta = 25 °C`, p.3) | Our worst case (`p1-66` / `p2-132`) | Margin |
|---|---|---|---|
| IF continuous | 20 mA (R, G, B) | 1.07 mA average per die (`13.33 mA × 1/12.4`) | OK (18.7×) |
| IFP peak (`≤ 0.1 ms, ≤ 1/10`) | 80 mA (R, G, B) | 13.33 mA peak (`SL = 255, GCC = 255`), `1/12.4` duty | OK, below even DC rating |
| Power `Pd` | R 50 mW; G, B 70 mW | R 2.4 V, G/B 3.4 V × 1.07 mA ≈ 3.6 mW | OK (> 13×) |
| Reverse voltage `VR` | 5 V | AW20198 de-ghosting clamps off channels near `PVCC ≤ 4.5 V` | OK |
| ESD (HBM) | 2000 V | Enclosed / conformal-coated front | OK |
| Operating / storage temp | `-40 °C ~ +85 °C` | Indoor wearable | OK |
| Soldering `Tsol` | Reflow `260 °C, 6 s`; manual `300 °C, 3 s` | Single-sided front LEDs + side castellations allow easy hand rework | OK |
| MSL | Level 3 | JLCPCB standard dry-pack handling | note |

## Optical & Electrical Characteristics (`IF = 20 mA, Ta = 25 °C`, p.4)
| Die | Wavelength `λd` | Forward Voltage `VF` | Luminous Intensity `IV` | Viewing Angle `2θ1/2` |
|---|---|---|---|---|
| Red (`Pin 1`) | `620 – 625 nm` | `1.8 – 2.4 V` | `100 – 180 mcd` | `120°` |
| Green (`Pin 3`) | `515 – 530 nm` | `2.6 – 3.4 V` | `350 – 800 mcd` | `120°` |
| Blue (`Pin 4`) | `460 – 475 nm` | `2.6 – 3.4 V` | `120 – 180 mcd` | `120°` |

## Calculations & Comparison vs XL-1010RGB-YG (`C965834`)
- **White-balanced brightness:** Red (`100–180 mcd`) and Blue (`120–180 mcd`, `+50%` higher minimum floor than `XL-1010RGB-YG`'s `80 mcd`) set the white-point ceiling; Green (`350–800 mcd`) is still `~3.5–4.5×` brighter than R and B and is scaled down in AW20198's per-LED `SL` registers for D65 white balance, so mixed/white brightness is unchanged.
- **Cost:** LCSC USD ladder (`C965840`, checked 2026-11-05): `50+: $0.0198`, `500+: $0.0159`, `1500+: $0.0138` (`44–49%` lower than `C965834`), saving `$0.84/board` on `p1-66` (qty 10 = 660 pcs) and `$1.47/board` on `p2-132` (qty 10 = 1,320 pcs) with `> 718k` JLCPCB stock.

## Pinout & JLCPCB CPL Rotation (CRITICAL — Differs from XL-1010RGB-YG)
- **Datasheet p.8 Top View & Schematic Diagram (`LED_XL-1615RGBC` at `0°` on `F.Cu`, KiCad y-down):**
  - **Pad `1`** = `(-0.625, -0.475)` (Top-Left) → **Red Cathode (`R`)**
  - **Pad `2`** = `(-0.625, +0.475)` (Bottom-Left, green triangle mark on `-X` edge) → **Common Anode (`+`)** *(contrast `XL-1010RGB-YG` where Pin 3 is Anode!)*
  - **Pad `3`** = `(+0.625, -0.475)` (Top-Right) → **Green Cathode (`G`)** *(contrast `XL-1010RGB-YG` where Pin 2 is Green!)*
  - **Pad `4`** = `(+0.625, +0.475)` (Bottom-Right) → **Blue Cathode (`B`)**
- **EasyEDA / JLCPCB Pick-and-Place (`C965840`) `0°` Reference:**
  - Verified via `easyeda2kicad --lcsc_id=C965840`: EasyEDA's `LED-ARRAY-SMD_4P-L1.6-W1.5-BR_XL-1615RGBC-RF` places `R-` at `(+0.75, +0.42)`, `COM+` at `(+0.75, -0.42)`, `B-` at `(-0.75, -0.42)`, and `G-` at `(-0.75, +0.42)` — an exact **`180°` rotation** of the datasheet Top View across all 4 terminals.
  - Therefore `export_and_cost.py` adds `+180.0°` (mod `360°`) to `C965840` rows in `cpl-jlcpcb.csv`, and `pcb_gen.py` / `lib_gen.py` rotate `LED-ARRAY-SMD_4P-L1.6-W1.5-BR_XL-1615RGBC-RF.step` by `180°` around Z.

## Layout
- Used on the lower-density 4-layer parallelogram boards (`p1-66` at `3.70 × 5.20 mm` pitch and `p2-132` at `3.70 × 2.60 mm` pitch), leaving `2.00 mm` horizontal copper-to-copper channel clearance between columns plus a `0.80 mm` horizontal inner channel right between left and right pads (`3×` `0.10 mm` tracks or a `0.30/0.15 mm` through-via clear of SMD pads).
