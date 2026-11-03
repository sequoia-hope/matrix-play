# U9 ST LIS2DW12TR accelerometer, LGA-12 2 × 2

Datasheet: datasheets/lis2dw12.pdf (DocID029682 Rev 4). Read: pin table, Tables 3, 5, wake-up registers.
Supplier: `C189624 LIS2DW12TR (ST, LGA-12(2x2)): extended, JLC stock 45643, lifecycle normal, checked 2026-11-02`

- VDD 1.62–3.6 V; VDD_IO to VDD + 0.1 V: both on 3V3. 3V3 max 3.4 V. OK.
- Current: low-power mode 1 µA at 12.5 Hz, 0.38 µA at 1.6 Hz (Table 5, at 1.8 V and not guaranteed; budget 2 µA at 3.3 V). Power-down 50 nA.
- Pins: 1 SPC=SCL; 4 SDA; 2 CS tied to VDD_IO (I2C); 3 SDO/SA0 tied to VDD_IO. Internal pull-ups ~20 kΩ at 3.6 V (Table 3), so no static draw when tied high. Address 0x19. 5 NC; 6, 8 GND; 7 RES to GND; 9 VDD; 10 VDD_IO; 11 INT2 unused; 12 INT1 to GPIO10.
- Bus: I2C1, 400 kHz, 4.7 kΩ pull-ups. Accelerometer alone on it. Pull-ups draw only while bus low; firmware keeps pins released in sleep.
- Decoupling: Fig. 6 p.25 asks 100 nF + 10 µF on VDD, 100 nF on VDD_IO. We use 100 nF + 4.7 µF 0402 (≥ 1 µF per review) on VDD, 100 nF on VDD_IO; the 3V3 rail adds more.
- Wake-up: INT1 from WAKE_UP_THS/DUR in low-power mode.
