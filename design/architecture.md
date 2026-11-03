# Architecture

```mermaid
flowchart LR
  J1[J1 USB-C] --> ESD[U7 USBLC6 ESD]
  J1 -- VBUS --> CH[U5 BQ24073 charger and power path]
  BT[BT1 cell 5435035] --> PROT[U8 XB9901A protection] --> CH
  CH -- VSYS 3.0-4.5 V --> LDO[U6 TPS7A0233 3V3]
  CH -- VSYS --> D1[U1 IS31FL3741A]
  CH -- VSYS --> D2[U2 IS31FL3741A]
  LDO -- 3V3 --> MCU[U3 RP2350A]
  LDO -- 3V3 --> FL[U4 W25Q128JV]
  LDO -- 3V3 --> ACC[U9 LIS2DW12]
  ESD -- USB D+/D- --> MCU
  MCU -- QSPI --> FL
  Y1[Y1 12 MHz] --> MCU
  MCU -- I2C0 1 MHz, SDB, INTB --> D1
  MCU -- I2C0 1 MHz, SDB, INTB --> D2
  MCU -- I2C1 --> ACC
  ACC -- INT1 wake --> MCU
  SW1[SW1 user/wake] --> MCU
  SW2[SW2 BOOTSEL] --> MCU
  CH -- VBAT divider, switched --> MCU
  CH -- CHG, PGOOD --> MCU
  D1 -- 9 SW, 39 CS --> M1[117 RGB LEDs, top]
  D2 -- 9 SW, 39 CS --> M2[117 RGB LEDs, top]
```

## GPIO plan (RP2350A, confirmed in the schematic)

| GPIO | Use | Note |
|---|---|---|
| 2, 3 | I2C1 SDA, SCL to U9 | 400 kHz, 4.7 kΩ pull-ups to 3V3 |
| 4, 5 | I2C0 SDA, SCL to U1, U2 | 1 MHz, 1 kΩ pull-ups to 3V3, 12 mA drive |
| 6, 7 | SDB1, SDB2 | 100 kΩ pull-down at each driver |
| 8, 9 | INTB1, INTB2 | 100 kΩ pull-ups to 3V3 |
| 10 | ACC_INT | power-up wake source |
| 11 | SW1 | power-up wake source, 1 kΩ series |
| 12, 13 | CHG, PGOOD | open drain, 100 kΩ pull-ups to 3V3 |
| 14 | VBAT_EN | Switches the divider via Q1; default pull-down keeps it off |
| 26 | VBAT_SENSE | ADC0, 100 kΩ / 100 kΩ with 100 nF |
| others | test pads where they fit | |
