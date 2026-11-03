# U8 XySemi XB9901A, cell protection with FETs, DFN 1.8 × 1.4

Datasheet: datasheets/xb9901a.pdf (rev 0.3). Read: all.
Supplier: `C669687 XB9901A (XySemi, DFNFC-6(1.4x1.8)): extended, JLC stock 2947, lifecycle normal, checked 2026-11-02`

- Low-side switch: cell − → GND pins + EP; VM pins → board GND. So **BT1− is not board GND**. VDD from cell + through R1 100 Ω, with C1 100 nF from VDD to its GND pins (Fig. 1 p.1, Fig. 6 p.10), close to the chip. Pins 4, 5 and the EP are cell−, net **BAT_N**: never flood them with board GND, or protection is bypassed. Only R1/C1 return there.
- VCU 4.25–4.35 V, VCL 4.10 V; VDL 2.3–2.5 V, VDR 3.0 V. Above our 4.2 V charge (BQ24073 VBAT(REG) 4.2 V), so no nuisance trip. Blocks a charge attempt beyond 4.3 V.
- RSS(ON) 11.5 mΩ. Overcurrent ~9 A, far above the cell's 1C: covers shorts only. Normal limit is firmware.
- IOPE 3.9 µA typ at 3.5 V; power-down 2.2 µA.
- Abs: VDD 6 V; VM −6 to +10 V. θJA 250 °C/W: 1 A² × 11.5 mΩ = 11.5 mW. OK.
- Current path needs "mass metal": short, wide, on pour.
- A previous user board (rp2350-pendant) uses this part.
- Margin: BQ24073 VBAT(REG) max 4.23 V (p.5) vs VCU min 4.25 V. 20 mV, plus ≥ 90 ms detection delay.
- Below 2.4 V cell, charge flows through a FET body diode until it re-closes (p.7): 297 mA × 0.7 V = 0.21 W, +52 °C at θJA 250 °C/W, briefly. Rare; TI's detection (p.24) covers it.
- Note 3 p.7: a freshly soldered cell may not power up until USB is plugged in or VM shorted to GND. In bring-up notes.
