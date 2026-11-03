# Layers and power: report

Saved from crunch-layers' final message, because the harness blocked it from writing this file. Numbers are the agent's and haven't been rechecked. Checked on a copy of c-placement-y17 at `hw/round-pendant/c-layers-chk17`, zones refilled, 0.025 mm grid. y17's successors will change these figures.

**Conclusion:** y17 passes at the 300 mA limit, but a full-white row needs about 4.00 V typical. Almost all of the added drop is SW line resistance.

| Net | Load | Worst drop |
|---|---:|---:|
| VBAT (BT1 to U5) | 988 mA | 52 mV (86 on long1) |
| BAT_N | 988 mA | 3.6 mV |
| VSYS | 988 mA | 9.6 mV |
| GND (U8 to EP) | 988 mA | 9.2 mV |
| VBUS | 500 mA | 14.7 mV |
| +3V3 | 131 mA (assumed split) | 1.1 mV |
| +1V1 | 100 mA (assumed split) | 16.4 mV at U3-6 |

**SW lines (494 mA, mV)**
- Driver 1, SW1_1-9: 95, 154, 55, 110, 235, 99, 147, 271, 276
- Driver 2, SW2_1-9: 54, 66, 37, 143, 179, 124, 259, 189, 272

CS is at most 7 mV: a bound from the longest net, 48 mm.

| Battery voltage needed, typical | Earlier figure | y17 |
|---|---:|---:|
| Full-white row | 3.65 V | 4.00 V |
| Top bin, worst headroom | ~4.2 V | ~4.55 V, above a full cell |
| 300 mA limit | not given | 3.44 V, if GCC scales the peak |
| Full white on USB, top bin (VSYS 4.4 V) | not given | ~4.33 V |

If firmware limits by content instead, a full row keeps the full-white figures, and far LEDs dim first at low battery. Widening SW1_8, SW1_9, SW2_7 and SW2_9 is the biggest gain, but it hasn't been routed.

**VSYS tracks under 0.3 mm:** 35 tracks, 18.1 mm in total, all 0.2 mm. 11 carry DC, the longest 1.11 mm, and only about 0.5 A flows through any but U5's output stub. The rest are capacitor and test-point stubs with no DC. 0.2 mm is justified on B.Cu: IPC-2221 gives 0.74 A at 10 K, and the longest current-carrying B.Cu track drops about 0.4 mV per 247 mA. AC ripple in the stubs wasn't solved.

**Exception:** all VSYS current leaves U5 through one via at (5.30, 6.36). IPC-2221 gives that via about 0.46 A, which covers 0.34 A continuous but not the 1 A peak if treated as DC. Use 2-3 vias there. VBAT's U5 end is also one via.

**Locked VBAT trunk: not needed.** y17 has none and has no width errors. A 1.0 mm trunk gives about 15 mV, saving 37 mV at full white. On the y5 base at 1200 s, trunks gave 29/7/7/863 against y5's 22/5/76/865: most width errors gone, more opens. `--plane-via-reach` (33/4/9/906) didn't help.

**0.1 mm drill:** y17 has 20 vias at 0.2/0.1: 15 SW LED anodes and 5 +3V3 band, all locked. Eight are in pads: 7 LED lands and U3-11. ENIG is already specified, so the finish doesn't change, and thickness is 1.0 mm. JLC calls this drill "more costly". **Needs confirming with JLC:** its filled via-in-pad range is listed as 0.15-0.55 mm, so those 8 fall outside it.

**Stackup:** F, In1, In2 GND, In3, In4, In5 VSYS/+3V3, In6, B. GND on In6 made no clear routing difference (54 open against 56). Second-GND (`8d1`) and `power_class.py` were never routed. JLC confirms 1.0 mm, 0.09/0.09 mm and 0.15/0.25 mm vias. It publishes no 8-layer 1.0 mm table, so dielectrics are estimates; read them from the quote tool.

**Thermal (estimate on y5, hand model):** `scripts/crunch/layers/thermal.py`. Tj at 40 °C: 123 °C full white, 68 °C at the 300 mA limit, 176 °C full white at h = 6. TJMAX 150 °C. The pad reduction adds only 1-3 K; board temperature and skin contact aren't checked.

**Not checked:** AC behaviour and thermal measurement.

Tools are in `scripts/crunch/layers/`, mainly `pdn.py`, `trunk.py` and `thermal.py`.
