# U3 RP2350A with crystal, inductor and decoupling

Datasheet: datasheets/rp2350.pdf (LCSC copy). Read for this project: §6.2 power states, §14.9.7 Table 1445, §5 flash-boot steps, §9.7. Values below are inherited from `examples/easy2350/design/parts/rp2350-core.md` in Boardroom, an audit that passed its own gate 1 review, and `chips/rp2350.md`. Differences for this board are listed; the phase-1 reviewer re-derives them.

| Part | Value | MPN | LCSC / stock 2026-11-02 |
|---|---|---|---|
| U3 | QFN-60 7 × 7 | RP2350A | C42411118: extended, 4738, normal |
| L1 | 3.3 µH polarity-marked 2016 | AOTA-B201610S3R3-101-T | C42411119: extended, **1**, normal. **Fails on stock until pre-ordered** |
| CIN, COUT, CFILT, DVDD 2nd | 4.7 µF X5R 10 V 0402 | CL05A475MP5NRNC | C23733: basic, 1253732 |
| RFILT | 33 Ω 0402 | 0402WGF330JTCE | C25105: basic, 1855880 |
| Decoupling | 100 nF 0402 | CL05B104KO5NNNC | C1525: basic, 34992305 |
| Y1 | 12 MHz, CL 10 pF, 3225 | ABM8-272-T3 | C20625731: extended, 9181 |
| Load caps | 15 pF C0G 0402 | 0402CG150J500NT | C1548: basic, 1318347 |
| XOUT series | 1 kΩ 0402 | 0402WGF1001TCE | C11702: basic |
| USB series | 27 Ω 0402, ×2 | 0402WGF270JTCE | C25100: extended, 38554 |
| BOOTSEL series | 1 kΩ | C11702 | as above |

## Differences from easy2350
- 3V3 comes from TPS7A0233 at ≤ 200 mA; RP2350 budget 100 mA max plus flash. Firmware stops at VBAT 3.5 V, where the LDO still regulates, because VREG_AVDD and USB_OTP_VDD need ≥ 3.135 V (Table 1441, p.1343) and BOD watches only DVDD.
- Reference power layout, zones and 2 mm-grid through vias: intent risk 1, phase 4.
- No SWD header: test pads. No RESET button; RUN on a test pad.
- USB VBUS not routed to the MCU; PGOOD reports it.

## Wake
PWRUP0–3 give 4 power-up sources from any GPIO (§6.2.3.2): GPIO10 and GPIO11. In P1.x pad state is latched (§9.7) and all GPIOs reset with pull-down on: firmware clears it on GPIO 2–5, 8, 9, 12, 13, 26, each of which otherwise costs 15–89 µA against its external pull-up.

## BOOTSEL
Bootrom samples CSn on every boot, including P1.7 wake (§5.2.2). With a soldered cell and no reset button: hold SW2, tap SW1 to wake from sleep; or short the RUN test pad to its neighbouring GND pad. Firmware also polls SW2 and reboots to BOOTSEL.

## Sleep current (Table 1445, P1.7, W25Q16JV attached, USB connected, 3.3 V)
19 + 0.5 + 11 + 22 + 1 + 3.5 = 57 µA. The 22 µA on QSPI_IOVDD includes flash standby.

Flash deep power-down: bootrom never issues ABh (§5.2.3, p.371). A warm boot via POWMAN vector needs retained RAM (P1.3: +7 µA VREG, −9 µA flash, keeps SRAM, net about −2 µA). Firmware option; the budget doesn't rely on it.
Crystal: CL 10 pF, 2 × (10 − 2.5) = 15 pF. ESR 50 Ω, DL 200 µW; 1 kΩ per RP minimal design.
Inductor (drawing p.4): 2.0 × 1.6 × 1.0 mm, Isat 2.4 A min, dot = + end. Footprint L_pol_2016 from `chips/rp2350.md`.
