# U6 TI TPS7A0233PDQNR, 3.3 V LDO, X2SON-4 1 × 1 mm

Datasheet: datasheets/tps7a02.pdf (Chinese edition). Read: features, electrical, recommended conditions.
Supplier: `C2860046 TPS7A0233PDQNR (TI, X2-SON-4-EP(1x1)): extended, JLC stock 1914, lifecycle normal, checked 2026-11-02`
Footprint: DQN0004A, 1.0 mm, 0.65 pitch, diamond EP 0.48 (p.41–42); 1 OUT, 2 GND, 3 EN, 4 IN (p.3).

- VIN 1.5–6.0 V recommended; we use 3.0–4.5 V. IOUT 200 mA; budget 150 mA max.
- IQ 25 nA typ. Ground current rises with load; irrelevant in sleep at ~50 µA.
- CIN, COUT ≥ 1 µF: CL05A105KA5NQNC (C52923, 25 V, basic) each. At 3.3–4.5 V derate ~10 %. RP2350 CIN 4.7 µF and decouplers add to COUT.
- Ground current ~1 % of load (p.6): ~0.6 µA in sleep, not the 25 nA quiescent.
- Dropout: 270 mV max at 200 mA, ~200 mV at 150 mA, 75–110 mV typ at 40–150 mA (p.6, p.13). Regulates above VSYS ≈ 3.5 V.
- EN tied to IN. "P" variant has active discharge; harmless, and the 3V3 rail only ever drops with VSYS.
- 3V3 ≤ VSYS always, as the driver input limit needs.
