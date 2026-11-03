# SW1, SW2: side-actuated tactile

`C110293 SKRTLAE010 (ALPSALPINE, SMD,4.5x3.4mm): extended, JLC stock 36079, lifecycle normal, checked 2026-11-02`, right-angle, actuator past the board edge.
Rejected: `C720477 TS-1088-AR02016` (basic): drawing shows a top plunger, not a side actuator. Footprint: stock `SW_Push_1P1T-MP_NO_Horizontal_Alps_SKRTLAE010`; it has NPTH pegs that reach the LED side, so phase 4 handles them with the USB-C holes.

- SW1: GPIO11 to GND through 1 kΩ. Internal pull-up; wake on low.
- SW2: QSPI_SS to GND through 1 kΩ, per the RP2350 reference.
