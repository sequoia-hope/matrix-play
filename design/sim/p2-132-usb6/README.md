# Simulation Report: `parallelogram-p2-132-usb6` Button RC, Two-Regime ESD, `VSYS` Nodal PDN, Thermal & Crosstalk Verification

## 1. Questions Answered
1. **Button DC & Contact Wetting:** Does `1 kΩ` series protection (`R46`, `R47`) + RP2350 internal pull-up (`50–80 kΩ`) satisfy RP2350 `V_IL <= 0.80 V` and Panasonic `EVQP7J01P` contact wetting/peak limits (`10 µA 2 V DC to 50 mA 12 V DC`) across all process/supply corners?
2. **10 ms ON/OFF Bounce & Debounce Window:** Across `EVQP7J01P`'s `10 ms` max ON/OFF contact bounce (`evqp7j01p.pdf` p. 1) and slow-corner RC recovery (`80 kΩ × 110 nF = 8.80 ms`), what symmetrical press + release firmware debounce window guarantees zero double-edges?
3. **Two-Regime IEC 61000-4-2 ESD (`SW5`/`SW6`):** What happens under sub-sparkover `400 V` contact pulses AND direct `8 kV` contact (`150 pF`, `330 Ω`) with `0402` air-flashover at `350 V` (`0.50 mm` gap across `R46`/`R47`)?
4. **Board-Extracted `VSYS` Nodal PDN:** Extracting the exact `VSYS` track/via network from `hw/parallelogram/p2-132-usb6/parallelogram.kicad_pcb`, what is the DC IR drop from `U5.OUT` (`Pin 10/11`) to `U6.IN` (`Pin 4`), `U1.PVCC` (`Pin 5/22`), and `U2.PVCC` (`Pin 5/22`) at the `300 mA` wearable budget (`GCC <= 0x74`, `intent.md` R19) vs unthrottled `656 mA` (`GCC = 0xFF`)?
5. **Thermal & Crosstalk Budgets:** What are the steady-state board surface rise (`300 mA` battery wearable mode), `U5` (`BQ24073`) junction temperature during `USB500` charging (`V_BAT = 3.1 V` + `GCC = 0x44`), and switching crosstalk onto `USER_C`/`USER_D`, `I2C0`, and `ADC1` (`LIGHT`)?

*(High-speed `66.5 MHz` QSPI and `USB 2.0` FS signal integrity FDTD results are inherited from `design/sim/p2-132/results/P1`, as `U3`, `U7`, `J1`, `R1`/`R2`, and stackup geometry are unchanged.)*

## 2. Setup & Input Files
- Solver script: `design/sim/p2-132-usb6/sim_buttons.py` (Backward-Euler transient ODE solver + 2-regime IEC 61000-4-2 flashover/charge-sharing model + `pcbnew` exact `VSYS` resistive nodal solver + thermal & crosstalk calculator).
- Output JSON: `design/sim/p2-132-usb6/results.json`
- Output multi-panel waveform & PDN plot: `design/sim/p2-132-usb6/debounce_esd.png` (`debounce_esd.svg`)

## 3. Results Summary (`results.json`)
- **DC low level (`V_OL`):** Worst-case **`68.64 mV`** vs RP2350 `V_IL_max = 800 mV` -> **`731.36 mV` noise margin**.
- **Contact current vs `EVQP7J01P` (`10 µA – 50 mA`):** Steady wetting **`37.03–67.95 µA`** (`>= 10 µA` min) and `100 nF` discharge peak **`3.102–3.500 mA`** (`<= 50 mA` max) -> **PASS across all corners**.
- **10 ms ON/OFF bounce & firmware window:**
  - Press fall to `V_IL`: `0.137–0.512 ms`; during `10 ms` severe ON chatter, `V_GPIO` peaks at `0.798–0.905 V` (`<< V_IH+ = 2.0 V`) -> **0 false rising edges**.
  - Worst slow-corner `10 ms` OFF bounce + clean rise to `V_IH+` (`2.0 V`): `10.00 + 8.83 = 18.83 ms` (`18.17 ms` simulated settled) -> **`>= 20 ms` symmetrical press + release firmware debounce window** eliminates all bounce and re-closure edges across `SW1..SW6`.
- **Two-regime ESD (`SW5`/`SW6`):**
  - Mechanical shielding: `EVQP7J01P` uses an insulating engineering-plastic plunger, and its outboard terminal nearest the PCB edge (`x = -12.10 mm`) is **`Pin 2 = GND`** tied directly to unbroken `In1.Cu` `plane GND`.
  - Sub-sparkover `400 V` on `Pin 1`: `V_GPIO` peaks at `3.874 V` (`I_clamp = 4.8 mA`).
  - Direct `8 kV` IEC contact on `Pin 1` WITH `0402` air-flashover (`350 V`): `150 pF` ESD body charge-shares into `100 nF` `C71`/`C72` (`50 V` X7R, `37.29 V` margin), attenuating peak clamp current from `24.24 A` to **`1.77 A`** (**`92.69%` attenuation**).
- **Board-extracted `VSYS` nodal PDN (`parallelogram.kicad_pcb`):**
  - **`300 mA` wearable budget (`GCC <= 0x74`) + `25 mA` `+3V3` LDO:** `ΔV(U6.4) = -60.72 mV`, `ΔV(U2.5) = -113.31 mV`, `ΔV(U1.5) = -114.50 mV` -> `V(U6.4) = 4.339 V` on USB and **`3.437 V >= 3.42 V`** down to `V_BAT = 3.55 V` (**zero LDO dropout**).
  - **Unthrottled `656 mA` (`GCC = 0xFF`):** `ΔV(U6.4) = -126.74 mV`, `ΔV(U1.5) = -244.88 mV` -> confirms why firmware enforces `GCC <= 0x74` (`<= 0x44` while `CHG == 0`) and low-battery brightness foldback below `V_BAT = 3.50 V`.
- **Thermal & Crosstalk:**
  - Wearable `300 mA` battery mode (`0.95 W` total): board rise **`+11.2 °C`** -> **`36.2 °C` at `25 °C` ambient** (`< 45 °C` wearable touch limit).
  - `USB500` charging depleted `3.1 V` cell (`297 mA`) + `175 mA` `GCC = 0x44`: `P(U5) = 0.669 W` -> **`T_J(U5) = 59.8 °C`** (`65.2 °C` margin below `125 °C` `BQ24073` thermal regulation).
  - Switching crosstalk: `USER_C`/`USER_D` = **`0.019 mV`** (shunted by `100 nF` `C71`/`C72`), `ADC1` (`LIGHT`) = **`0.012 mV`** (`100 nF` `C70` + `16×` averaging), `I2C0` = **`84.8 mV`** (`<< 990 mV` `V_IL` margin with `1 kΩ` pull-ups + `AW20198` `SRCR = 0x07` soft slew).

## 4. Design & Firmware Impact
- Hardware: Keep `R46`/`R47 = 1 kΩ` + `C71`/`C72 = 100 nF` (`50 V` X7R `0402`) beside `SW5`/`SW6` (`x = -7.40 mm`), `2` paste-free `GND` thermal vias in `U5` EP, and `5` paste-free `GND` thermal vias in each of `U1`, `U2`, `U3` EPs.
- Firmware (`bringup.md` §3): `>= 20 ms` press+release SW debounce on `SW1..SW6`, `AW20198` `SRCR = 0x07` + `GCC <= 0x74` (`<= 0x44` when `CHG == 0`), `PADS_QSPI.SLEWFAST = 0`, and `16×` `ADC1` averaging.
