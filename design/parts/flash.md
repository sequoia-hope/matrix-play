# U4 Winbond W25Q128JVPIQ, 128 Mbit QSPI, WSON-8 5 × 6 mm

Datasheet: datasheets/w25q128jv.pdf (2018-03-27). Read: features, power-down (§8.2.21–22), DC table.
Supplier: `C190862 W25Q128JVPIQ (Winbond, WSON-8-EP(5x6)): extended, JLC stock 8662, lifecycle normal, checked 2026-11-02`
Footprint: KiCad `WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm`. EP has no internal connection: float or GND (p.69). §10.3 says avoid exposed vias under the pad, so no LED via there unless filled and capped.

- Chosen over SOIC-8 (C97521, basic, 76735) for area: 5 × 6 mm against ~5.3 × 8 mm with leads. Costs one extended part.
- VCC 2.7–3.6 V: 3V3 tracks down to ~3.2 V. OK.
- ICC1 standby 10 µA typ, 60 max; ICC2 power-down 1 µA typ, 20 max (p. DC table). Budget uses standby.
- `/WP`, `/HOLD` are QSPI data lines SD2, SD3, per the RP2350 reference.
- 100 nF on VCC. QSPI_SS: BOOTSEL via 1 kΩ to GND through SW2; no pull-up needed, QSPI_SS has an internal pull-up (RP2350 Table 1430, pin 60).
- Length limit per `chips`: QSPI ≤ 25 mm, phase 3.
- Below VCC 3.0 V the clock limit falls to 104 MHz (p.60); fine at 75 MHz.
