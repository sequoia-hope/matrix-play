# D1–D234: XINGLIGHT XL-1010RGB-YG

Datasheet: datasheets/xl-1010rgb-yg.pdf. Read: all 15 pages; pp.3–6 and 8 as images.
Supplier: `C965834 XL-1010RGB-YG (XINGLIGHT, SMD-4P,1x1mm): extended, JLC stock 12489, lifecycle normal, checked 2026-11-02`
Footprint: project footprint from p.8 recommended pattern: 0.45 × 0.45 mm pads, 0.35 mm gaps, 1.25 mm overall.

## Absolute max vs our worst case
| Parameter | Abs max | Our worst case | Margin |
|---|---|---|---|
| IF continuous | 20 mA | 1.25 mA average per die | OK |
| IF peak (≤ 0.1 ms, ≤ 1/10) | R 60, G/B 80 mA | 12.7 mA, 32 µs, duty 1/10.125 | OK, below even the continuous limit |
| Power | R 50, G/B 70 mW | R 2.4 V, G/B 3.4 V × 1.25 mA ≈ 4 mW | OK |
| VR | 5 V | Off cathode can be above anode; driver pull-ups and de-ghost hold it near VSYS. ≤ 4.5 V | OK |
| ESD | 2 kV | Not exposed behind a window | OK |
| MSL | 3 | JLC handles at assembly | note |

## Calculations
- Vf at 12.7 mA, p.6 curve: G/B ~2.8 V, R ~2.0 V. Table limits at 20 mA: G/B 2.6–3.4 V, R 1.8–2.4 V.
- Relative intensity at 12.7 mA from p.6: G/B ~0.8, R ~0.6 of the 20 mA value. Average 1.25 mA over the 20 mA rating is 1/16 duty, so G ~27–50 mcd average, R ~4–8, B ~4–10. Colour balance needs firmware scaling, since G is ~5 × R and B. Each driver has per-channel Scaling registers for this.

## Fine print
- Pad 3 is the common anode; 1 R, 2 G, 4 B cathodes (p.8). The mark is at the 3/4 side of the bottom view. Check pin 1 at the CPL step: the top and bottom drawings mirror each other.
- Reflow 255 °C peak (p.7). The LEDs are on one side only, reflowed once or twice per JLC's double-sided order; datasheet tests 2 cycles.
- Tolerance ±0.25 mm unless noted (p.8), so the 0.75 mm channel between lands is copper to copper, and the body stays inside the land.

## Layout
- 2.000 mm square grid, one orientation. Plan per LED: R and B tracks in the channels, G through the 0.35 mm centre gap, anode down a via in pad 3.

## Open questions
- Reel Vf bin not guaranteed; affects intent risk 2 only.
