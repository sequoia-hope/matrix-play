# Simulation Report: `parallelogram-p2-132-usb6` Button RC, Two-Regime ESD, `VSYS` Nodal PDN, Thermal & Crosstalk Verification

## 1. Questions Answered
1. **Button DC & Contact Wetting:** Does `1 kΩ` series protection (`R46`, `R47`) + RP2350 internal pull-up (`50–80 kΩ`) satisfy RP2350 `V_IL <= 0.80 V` and Panasonic `EVQP7J01P` contact wetting/peak limits (`10 µA 2 V DC to 50 mA 12 V DC`) across all process/supply corners?
2. **10 ms ON/OFF Bounce & Debounce Window:** Across `EVQP7J01P`'s `10 ms` max ON/OFF contact bounce (`evqp7j01p.pdf` p. 1) and slow-corner RC recovery (`80 kΩ × 110 nF = 8.80 ms`), what symmetrical press + release firmware debounce window guarantees zero double-edges?
3. **Two-Regime IEC 61000-4-2 ESD (`SW5`/`SW6` + `C307331` `50 V` X7R):** What happens under sub-sparkover `400 V` contact pulses AND direct `8 kV` contact (`150 pF`, `330 Ω`) with `0402` air-flashover at `450 V` (`0.50 mm` gap across `R46`/`R47`) including nonlinear X7R DC-bias capacitance reduction on **`C307331`** (`CL05B104KB54PNC`, `100 nF 50 V X7R 0402`)?
4. **Board-Extracted `VSYS` + Battery Path Nodal PDN:** Extracting the exact `VSYS` track/via network (`3.0 mΩ`/via) from `hw/parallelogram/p2-132-usb6/parallelogram.kicad_pcb` plus the upstream battery series path (`BT1 + BAT_N + U8 + VBAT + U5 BATFET`, `273.8 mΩ` typ / `370.3 mΩ` worst), what is `V(U6.4)` down to **`V_BAT = 3.50 V`** at `165 mA` continuous worn (`GCC <= 0x40`), `300 mA` burst (`GCC <= 0x74`), and `840 mA` `GCC = 0xFF` PWM-only peak pulses?
5. **Still-Air Wearable Thermal & Crosstalk Budgets:** Under realistic still-air convection with the rear insulated by the LiPo pouch (`θ_BA = 33.3 °C/W`, `h·A_eff = 0.030 W/K`), what is the continuous worn thermal ceiling (`< 45 °C` at `25 °C` ambient), `U5` (`BQ24073`) junction temperature during `USB500` charging (`V_BAT = 3.1 V` + `GCC = 0x44`), and switching crosstalk onto `USER_C`/`USER_D`, `I2C0`, and `ADC1` (`LIGHT`)?

*(High-speed `66.5 MHz` QSPI and `USB 2.0` FS signal integrity FDTD results are inherited from `design/sim/p2-132/results/P1`, as `U3`, `U7`, `J1`, `R1`/`R2`, and stackup geometry are unchanged.)*

## 2. Setup & Input Files
- Solver script: `design/sim/p2-132-usb6/sim_buttons.py` (Backward-Euler transient ODE solver + 2-regime IEC 61000-4-2 `450 V` flashover / nonlinear `50 V` X7R DC-bias model + `pcbnew` exact `VSYS` + battery-path resistive nodal solver + still-air thermal & crosstalk calculator).
- Output JSON: `design/sim/p2-132-usb6/results.json`
- Output multi-panel waveform & PDN plot: `design/sim/p2-132-usb6/debounce_esd.png` (`debounce_esd.svg`)

## 3. Results Summary (`results.json`)
- **DC low level (`V_OL`):** Worst-case **`68.64 mV`** vs RP2350 `V_IL_max = 800 mV` -> **`731.36 mV` noise margin**.
- **Contact current vs `EVQP7J01P` (`10 µA – 50 mA`):** Steady wetting **`37.03–67.95 µA`** (`>= 10 µA` min) and `100 nF` discharge peak **`3.167–3.500 mA`** (`<= 50 mA` max) -> **PASS across all corners**.
- **10 ms ON/OFF bounce & firmware window:**
  - Press fall to `V_IL`: `0.137–0.512 ms`; during `10 ms` severe ON chatter, `V_GPIO` peaks at `0.798–0.905 V` (`<< V_IH+ = 2.0 V`) -> **0 false rising edges**.
  - Worst slow-corner `10 ms` OFF bounce + clean rise to `V_IH+` (`2.0 V`): `10.00 + 8.83 = 18.83 ms` (`18.17 ms` simulated settled) -> **`>= 20 ms` symmetrical press + release firmware debounce window** eliminates all bounce and re-closure edges across `SW1..SW6`.
- **Two-regime ESD (`SW5`/`SW6` with `C307331` `50 V` X7R):**
  - Mechanical shielding: `EVQP7J01P` uses an insulating engineering-plastic plunger, and its outboard terminal nearest the PCB edge (`x = -12.10 mm`) is **`Pin 2 = GND`** tied directly to unbroken `In1.Cu` `plane GND`.
  - Sub-sparkover `400 V` on `Pin 1`: `V_GPIO` peaks at `3.88 V` (`I_clamp = 6.04 mA`).
  - Direct `8 kV` IEC contact on `Pin 1` WITH `450 V` `0402` air-flashover & nonlinear `50 V` X7R DC-bias model: clamped peak is **`13.65 V`** (**`36.35 V` margin** below `50 V` rating; open-circuit charge-share peak is `17.38 V` = `32.62 V` margin), attenuating peak clamp current from `24.24 A` to **`1.96 A`** (**`91.92%` attenuation**).
  - Inherited `SW1..SW4` note: `SW1..SW4` retain parent `p2-132-usb` `1 kΩ` series resistors (`SW2` shares `/MCU/QSPI_SS` where `100 nF` is prohibited; `SW1/SW2` have insulating plastic plungers + outboard `Pin 2 = GND`; `SW3/SW4` ground outer metal brackets and carry a `<= 450 V` sub-sparkover bare-stem rating).
- **Board-extracted `VSYS` + battery-path nodal PDN (`parallelogram.kicad_pcb`):**
  - **`165 mA` continuous worn ceiling (`GCC <= 0x40`) + `25 mA` LDO:** `ΔV_VSYS(U6.4) = -3.29 mV`, `V(U6.4) = 3.445 V` typ / **`3.426 V` worst** at `V_BAT = 3.50 V`.
  - **`300 mA` burst/handheld budget (`GCC <= 0x74`) + `25 mA` LDO:** `ΔV_VSYS(U6.4) = -4.64 mV`, `ΔV(U2.5) = -31.78 mV`, `ΔV(U1.5) = -52.46 mV` -> `V(U6.4) = 4.395 V` on USB and **`3.406 V` typ / `3.375 V` worst >= `3.355 V`** (`TPS7A0233` `V_OUT + V_DO,max(25 mA)`) at **`V_BAT = 3.50 V`** (**zero LDO dropout**).
  - **`840 mA` `GCC = 0xFF` PWM-only peak hazard:** Leaving `GCC = 0xFF` and dimming via PWM alone draws `840 mA` row pulses (`1/6` duty), pulling `V(U6.4)` down to `3.170 V` (dropout) -> proves why firmware MUST scale brightness via analog **`GCC`** (`<= 0x40` continuous worn, `<= 0x74` burst, `<= 0x44` charging, foldback `< 3.50 V`).
- **Still-Air Wearable Thermal & Crosstalk:**
  - Continuous worn battery mode (`0.541 W`, `165 mA` `GCC <= 0x40`, `θ_BA = 33.3 °C/W` still-air + rear LiPo insulated): board rise **`+18.0 °C`** -> **`43.0 °C` at `25 °C` ambient** (`< 45 °C` wearable touch limit).
  - Burst/handheld `300 mA` mode (`0.950 W`, `GCC <= 0x74`): `+31.7 °C` unthrottled steady-state rise, governed in firmware by closed-loop `RP2350` `ADC4` thermal foldback (`45 °C` worn / `42 °C` charging).
  - `USB500` charging depleted `3.1 V` cell (`297 mA`) + `175 mA` `GCC = 0x44`: `P(U5) = 0.669 W` -> **`T_J(U5) = 59.8 °C`** (`65.2 °C` margin below `125 °C` `BQ24073` thermal regulation).
  - Switching crosstalk: `USER_C`/`USER_D` = **`0.019 mV`** (shunted by `100 nF` `C71`/`C72`), `ADC1` (`LIGHT`) = **`0.012 mV`** (`100 nF` `C70` + `16×` averaging), `I2C0` = **`84.8 mV`** (`<< 990 mV` `V_IL` margin with `1 kΩ` pull-ups + `AW20198` `SRCR = 0x07` soft slew).

## 4. Design & Firmware Impact
- Hardware: `R46`/`R47 = 1 kΩ` + `C71`/`C72 = 100 nF 50 V X7R` (`C307331` `CL05B104KB54PNC` `0402`) beside `SW5`/`SW6` (`x = -7.40 mm`), `2` `GND` thermal vias in `U5` EP, and `5 + 6 + 5` paste-free `GND` thermal vias in `U1`, `U2`, `U3` EPs (`18` total).
- Firmware (`bringup.md` §3–§4): `>= 20 ms` press+release SW debounce on `SW1..SW6`, `AW20198` `SRCR = 0x07` + analog `GCC <= 0x40` continuous worn (`<= 0x74` burst with `ADC4` `45 °C` foldback, `<= 0x44` when `CHG == 0`), `PADS_QSPI.SLEWFAST = 0`, `>= 30 ms` `VBAT_SENSE` settling (`IE=0, PDE=0`), and `16×` `ADC1` averaging.
