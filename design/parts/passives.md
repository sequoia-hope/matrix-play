# Passives

| Value | Part | LCSC | Status 2026-11-02 | Use |
|---|---|---|---|---|
| 100 nF X7R 16 V 0402 | CL05B104KO5NNNC | C1525 | basic, 34992305 | decoupling |
| 1 µF X5R 25 V 0402 | CL05A105KA5NQNC | C52923 | basic, 10665043 | driver VCC, LDO |
| 4.7 µF X5R 10 V 0402 | CL05A475MP5NRNC | C23733 | basic, 1253732 | RP2350 |
| 10 µF X5R 10 V 0603 | CL10A106KP8NNNC | C19702 | basic, 11481030 | BAT |
| 22 µF X5R 10 V 0603 | CL10A226MP8NUNE | C86295 | extended, 1070256 | VSYS bulk, one per driver and one at charger OUT; ~11 µF at 4.4 V |
| 15 pF C0G 0402 | 0402CG150J500NT | C1548 | basic | crystal |
| 27 Ω | 0402WGF270JTCE | C25100 | extended, 38554 | USB |
| 33 Ω | 0402WGF330JTCE | C25105 | basic | RFILT |
| 1 kΩ | 0402WGF1001TCE | C11702 | basic | I2C0, XOUT, buttons |
| 3.0 kΩ | 0402WGF3001TCE | C25784 | extended, 54984 | ISET charger |
| 3.6 kΩ | 0402WGF3601TCE | C25891 | extended, 97231 | ILIM |
| 4.7 kΩ | 0402WGF4701TCE | C25900 | basic, 14517629 | I2C1 |
| 5.1 kΩ | 0402WGF5101TCE | C25905 | basic | CC |
| 10 kΩ | 0402WGF1002TCE | C25744 | basic | TS |
| 30 kΩ | 0402WGF3002TCE | C25776 | extended, 5355041 | driver ISET |
| 100 kΩ | 0402WGF1003TCE | C25741 | basic | pull-ups, SDB |
| 100 Ω | 0402WGF1000TCE | C25076 | basic (per easy2350) | XB9901A VDD R1 |

Calculations:
- VBAT divider: 100 kΩ / 100 kΩ (C25741), switched by Q1 NTZD3155C, gate pull-up 100 kΩ. Off: FET leakage only. Thevenin 50 kΩ × 1 µA GPIO leakage max (Table 1436, with RP2350 ADC pin `PDE = 0, IE = 0` mandatory to disable the default 50–80 kΩ pull-down and E9 leakage) = 50 mV at the ADC, 100 mV at VBAT worst case. 100 nF (`C7`) filter cap gives `τ = 50 kΩ × 100 nF = 5.0 ms`; firmware must wait **`≥ 30 ms` (`6 τ`, `< 0.25%` settling error)** after switching `VBAT_EN` high before reading ADC (waiting only `5 ms = 1 τ` leaves a `36.8%` error).
- 3V3 ≤ RP2350 etc.: see parts files. MLCC derating noted per use.
