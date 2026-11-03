# Q1 onsemi NTZD3155CT1G, complementary N+P FET, SOT-563

Datasheet: datasheets/ntzd3155c.pdf. Read: electrical tables.
Supplier: `C236117 NTZD3155CT1G (onsemi, SOT-563)`, extended, 7988 (searched 2026-11-02).

- Switches the VBAT divider's high side. N gate on GPIO14, 100 kΩ pull-down holds it off without 3V3 (from R-network). N drain pulls P gate low against a 100 kΩ pull-up to BAT. P source on BAT, drain to 100 kΩ / 100 kΩ to GND; midpoint to GPIO26.
- 3.3 V N gate and 3.5–4.2 V P gate are well above threshold; drain current ~20 µA. Figures from the table above at schematic capture; no power concern.
- On-state draws 42 µA + 21 µA briefly, only during a reading.
