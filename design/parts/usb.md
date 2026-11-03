# J1, U7: USB-C front end

J1 Hroparts TYPE-C-31-M-12: `C165948 TYPE-C-31-M-12 (Korean Hroparts Elec, SMD): extended, JLC stock 177286, lifecycle normal, checked 2026-11-02`. Stock KiCad footprint `USB_C_Receptacle_HRO_TYPE-C-31-M-12`; audited with drawing in easy2350's `parts/usb-front-end.md`.
U7 ST USBLC6-2P6, SOT-666: `C15999`, extended, 23013 (searched 2026-11-02). Datasheet: datasheets/usblc6-2p6.pdf.
CC: 5.1 kΩ ×2 (C25905, basic, 4976972). USB series: 27 Ω at the MCU (`rp2350-core.md`).

- Contact pins, 8 kV: USBLC6-2P6 on D+, D−, and its VBUS pin. No Vrwm given: VBR min 6 V, IRM 150 nA at 5.25 V (Table 2, p.2). 5.5 V is fine; a charger above 6 V can damage U7 before BQ24073's 6.6 V OVP acts. Accepted. CC lines unprotected, as in easy2350.
- D+/D− pairs joined across the connector's A and B rows per USB-C for reversible use.
- Bulk on VBUS: ≤ 10 µF; BQ24073 IN cap 1 µF serves.

## Through-hole problem (intent risk 5)
From the footprint, relative to connector centre, edge at +3.1 or so:
| Feature | x | y | Size |
|---|---|---|---|
| Shell front | ±4.32 | +1.05 | 0.6 × 1.2 slot, 1.0 × 1.6 pad |
| Shell rear | ±4.32 | −3.13 | 0.6 × 1.7 slot, 1.0 × 2.1 pad |
| Pegs | ±2.89 | −2.60 | 0.65 NPTH |

All run through to the LED side. A 1.0 mm pad does not fit a 0.75 mm channel. Other 16-pin candidates read (GT-USB-7010ASV, GT-USB-7014D sinker, USB4105, HC-TYPE-C-16P-01A, DX07S016, TYPEC-304-ACP16, XKB U262) have four legs too. Six-pin parts (M-17) have no D+/D− and are excluded. Phase 4 decides.
