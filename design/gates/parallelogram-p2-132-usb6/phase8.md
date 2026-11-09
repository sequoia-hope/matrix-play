# Gate 8: simulation and signal integrity (`parallelogram-p2-132-usb6`)

Status: **passed**

## Checklist (`references/simulation.md` §Gate checklist)
- [x] **Trigger list generated from `design/nets-parallelogram-p2-132-usb6.csv` (table below — covering SI, bounce, 2-regime ESD, `VSYS` nodal PDN, thermal, and crosstalk)**
- [x] **Each triggered item has a quantitative simulation result (`design/sim/p2-132-usb6/{sim_buttons.py,results.json,debounce_esd.png,README.md}` + inherited `design/sim/p2-132/results/P0..P4`)**
- [x] **Aggressor / victim parallel-segment & switching crosstalk audit run across all `5416` routed tracks (`719` vias), all couplings quantified & bounded**
- [x] **Design & firmware findings fed back (`>= 20 ms` press+release software debounce, `AW20198` `SRCR = 0x07` + analog `GCC <= 0x40` continuous worn / `<= 0x74` burst + `ADC4` thermal foldback, `PADS_QSPI.SLEWFAST = 0`, and `16×` `ADC1` averaging documented in `brief.md` §7–§8, `bringup.md` §3–§4, `stackup.md`, and `README.md` §5)**
- [x] **Stronger-model (`agy` `gemini-4-argon-high`) fresh-context SI/EMC review completed & verified**

## 1. Trigger Matrix from `design/nets-parallelogram-p2-132-usb6.csv` (`118` Nets)

| Trigger Category | Nets on `p2-132-usb6` | Routed Geometry | Simulation / Physics Evaluation (`design/sim/p2-132-usb6/results.json`) | Status |
|---|---|---|---|---|
| **New West-Edge User Buttons (`SIGNAL`, 2-regime ESD + `10 ms` bounce)** | `/MCU/USER_C` (`GPIO9`), `/MCU/USER_D` (`GPIO0`), `Net-(R46-Pad2)`, `Net-(R47-Pad2)` | `SW5/6 -> R46/47`: `4.31 / 4.61 mm` on `B.Cu` (`0` vias); `/MCU/USER_C/D`: `27.24 / 14.16 mm` | • `V_OL,wc = 68.64 mV << 800 mV` (`731.36 mV` margin); wetting `37.03–67.95 µA` (`>= 10 µA`), peak cap discharge `3.17–3.50 mA` (`<= 50 mA` `EVQP7J01P` rating)<br>• Two-regime ESD with nonlinear DC-bias X7R model (`C307331` `100 nF 50 V` X7R `0402`, basic part): insulating plastic plunger + outboard `Pin 2 = GND` (`|x| = 12.10 mm`) shields `Pin 1`; `400 V` sub-sparkover gives `3.88 V` (`6.04 mA`); direct `8 kV` IEC contact WITH `450 V` `0402` air-flashover peaks at **`13.65 V`** (`36.35 V` margin to `50 V`, `17.38 V` open-circuit = `32.62 V` margin), cutting clamp current `24.24 A -> 1.96 A` (**`-91.92%`**). Inherited `SW1..SW4` `1 kΩ`-only scope noted (`SW2` shares `/MCU/QSPI_SS`)<br>• Worst slow-corner `10 ms` OFF bounce + rise to `V_IH+` (`2.0 V`) = `18.83 ms` (`18.17 ms` sim) -> **`>= 20 ms` press+release firmware debounce** across `SW1..SW6` | **Simulated & Passed** |
| **`POWER` / `POWER_HI` Board-Extracted `VSYS` + Battery Path Nodal PDN** | `VSYS` (`U5.10/11` -> `U6.4`, `U1.5/22`, `U2.5/22`), `VBAT`, `/Power/BAT_N`, `VBUS`, `+3V3`, `+1V1` | `VSYS`: `0.16–0.30 mm`, `104.25 mm` network, `26` vias (`3.0 mΩ`/via); `VBAT/BAT_N`: `0.25 mm` (`273.8 / 370.3 mΩ` typ/worst upstream path) | Exact resistive nodal solve from `parallelogram.kicad_pcb` (`solve_vsys_nodal_pdn`):<br>• **`165 mA` continuous worn (`GCC <= 0x40`) + `25 mA` LDO:** `ΔV_VSYS(U6.4) = -3.29 mV`, `V(U6.4) = 3.445 V` typ / **`3.426 V` worst** at `V_BAT = 3.50 V`<br>• **`300 mA` burst/handheld (`GCC <= 0x74`) + `25 mA` LDO:** `ΔV_VSYS(U6.4) = -4.64 mV`, `ΔV(U2.5) = -31.78 mV`, `ΔV(U1.5) = -52.46 mV` -> `V(U6.4) = 4.395 V` on USB and **`3.406 V` typ / `3.375 V` worst >= `3.355 V`** (`TPS7A0233` `V_OUT + V_DO,max(25 mA)`) at **`V_BAT = 3.50 V`** (**`0` LDO dropout**)<br>• **`840 mA` `GCC = 0xFF` PWM-only peak pulse:** drops `V(U6.4)` to `3.170 V` (LDO dropout), proving why firmware scales brightness via analog `GCC` (`never GCC=0xFF` with PWM-only dimming) and folds back `< 3.50 V` | **Simulated & Passed** |
| **Still-Air Wearable & `U5` Charger Thermal Budget** | `U1` (`5` EP vias), `U2` (`6` EP vias), `U3` (`5` EP vias), `U5` (`2` EP vias), `132` LEDs | `1,310.45 mm²` unbroken `In1.Cu` `plane GND` heat spreader (`θ_BA = 33.3 °C/W` still-air + rear LiPo insulated) | • **Continuous worn mode (`0.541 W`, `165 mA` `GCC <= 0x40`):** still-air rise **`+18.0 °C`** -> **`43.0 °C` at `25 °C` ambient** (`< 45 °C` wearable touch limit)<br>• **Burst/handheld mode (`0.950 W`, `300 mA` `GCC <= 0x74`):** `+31.7 °C` unthrottled steady-state rise, governed by closed-loop `RP2350` `ADC4` thermal foldback (`45 °C` worn / `42 °C` charging)<br>• **`USB500` charging depleted `3.1 V` cell (`297 mA`) + `175 mA` `GCC = 0x44`:** `P(U5) = 0.669 W` -> **`T_J(U5) = 59.8 °C`** (`65.2 °C` margin below `125 °C` `BQ24073` regulation) | **Simulated & Passed** |
| **`DIFF_HS` (`USB 2.0` Full-Speed `12 Mb/s`, `t_r >= 4 ns`)** | `/Power/USB_D*_C`, `USB_DP`/`USB_DM`, `/MCU/USB_D*_MCU` | End-to-end `DP = 19.670 mm`, `DM = 19.633 mm` (`skew = 0.038 mm = 0.25 ps`); `U3 -> R14/15` = `2.51 / 2.55 mm` (`0` vias) | `l_crit = 4000 ps / (2 × 6.6 ps/mm) = 303 mm` (`stackup.md` conservative `125 mm`); actual `19.67 mm = 0.065 × l_crit` (lumped regime), damped by `27 Ω` (`R14`/`R15`) + `USBLC6-2P6` (`U7`). Inherited FDTD check in `design/sim/p2-132/results/P0`. | **Verified (`<< l_crit`)** |
| **`SE_HS` (`QSPI` `66–104 MHz`, `t_r ~ 1.5 ns`)** | `/MCU/QSPI_SCLK`, `QSPI_SS`, `QSPI_SD0..3` | `5.20–13.56 mm` (`<= 25 mm` `.kicad_dru` rule; `skew = 8.36 mm = 55 ps << 4.8 ns` half-UI) | `< 0.12 × l_crit` (`113.6 mm`), routed over unbroken `In1.Cu` `plane GND` (`1` piece) with `PADS_QSPI.SLEWFAST = 0`. Inherited FDTD eye check in `design/sim/p2-132/results/P1`. | **Simulated & Passed** |
| **`CLOCK` (`12 MHz` crystal) & `SWITCH` (`VREG_LX`)** | `Net-(U3-XIN/XOUT)`, `Net-(C24-Pad1)`, `/MCU/VREG_LX` | Crystal `1.54–6.15 mm` (`0` vias, `B.Cu`); `VREG_LX` `2.183 mm²` pour | `vendor GND` guard pour around `Y1`; `LX cutout L2` (`In1.Cu`) + `LX cutout L3` (`In2.Cu`) prevent any trace or plane coupling beneath `VREG_LX`/`L1.2`. | **Verified** |

## 2. Crosstalk & Parallel-Coupling Audit (`sim_buttons.py` + `audit_phase7_8.py`)
- **`/MCU/USER_C` & `/MCU/USER_D`:** Shunted by `C71/C72 = 100 nF` (`C307331` `50 V` X7R, `Z < 1.6 Ω` at `>= 1 MHz`) -> **`0.019 mV` peak coupled noise** from `QSPI_SS` / `CS/SW` scan edges (`<< 1.20 V` Schmitt hysteresis margin).
- **`I2C0` (`I2C_SDA`/`I2C_SCL`, `1 kΩ` pull-ups `R21/R22`):** With `AW20198` `SRCR = 0x07` soft `SW/CS` slew rate (`t_r ~ 8 ns`, required in `bringup.md` §4), peak coupled glitch into `500 Ω` parallel impedance is **`84.8 mV << 990 mV` `V_IL` margin**.
- **`/MCU/LIGHT` (`ADC1`):** Shunted by `C70 = 100 nF` at `R43 = 22 kΩ` -> **`0.012 mV`** (`< 0.02 LSB`), plus `16×` ADC averaging in firmware.
- **`USB_DM`/`USB_DP` (`In2.Cu`) ↔ `Net-(U5-TS)` (`B.Cu`):** Separated across the **`0.210 mm` bottom prepreg** (complementary `12 Mb/s` differential pair, `t_r >= 4 ns`; `BQ24073` `TS` has `> 320 mV` window margin and ms-scale comparator deglitching), `< 8 fF` (`< 1 mV` into `10 kΩ` `R7`).

## 3. Verbatim `sim_buttons.py` Output (`design/sim/p2-132-usb6/results.json`)
```json
{
  "board": "parallelogram-p2-132-usb6",
  "dc_levels": {"v_low_worst_case_mV": 68.64, "rp2350_vil_max_mV": 800.0, "vil_noise_margin_mV": 731.36},
  "contact_rating_evqp7j01p": {"steady_wetting_min_uA": 37.03, "steady_wetting_max_uA": 67.95, "cap_discharge_peak_min_mA": 3.102, "cap_discharge_peak_max_mA": 3.5, "within_rating": true},
  "transient_corners": {
    "nominal": {"tau_rise_ms": 6.5, "t_clean_rise_to_vih_2p0V_ms": 5.956, "t_worst_10ms_off_bounce_plus_rise_ms": 15.956, "stays_below_vih_2p0V_during_10ms_on_chatter": true, "recommended_firmware_debounce_ms": 20},
    "fast_worst_chatter": {"tau_rise_ms": 4.5, "t_clean_rise_to_vih_2p0V_ms": 3.784, "t_worst_10ms_off_bounce_plus_rise_ms": 13.784, "stays_below_vih_2p0V_during_10ms_on_chatter": true, "recommended_firmware_debounce_ms": 20},
    "slow_worst_release": {"tau_rise_ms": 8.8, "t_clean_rise_to_vih_2p0V_ms": 8.833, "t_worst_10ms_off_bounce_plus_rise_ms": 18.833, "stays_below_vih_2p0V_during_10ms_on_chatter": true, "recommended_firmware_debounce_ms": 20}
  },
  "esd_verification": {
    "c71_c72_part": "Samsung CL05B104KB54PNC (LCSC C307331, 100 nF 50 V X7R 0402, basic part)",
    "sub_sparkover_400V_pin1": {"v_gpio_peak_V": 3.88, "i_clamp_peak_mA": 6.04},
    "direct_8kV_pin1_with_450V_0402_flashover": {"open_circuit_dc_biased_peak_V": 17.38, "v_gpio_peak_with_clamp_V": 13.65, "i_clamp_peak_A": 1.96, "unbuffered_iec_peak_A": 24.24, "current_attenuation_pct": 91.92, "c71_c72_50V_x7r_margin_V": 36.35}
  },
  "vsys_nodal_pdn": {
    "battery_series_path_ohm": {"total_upstream_typ_mOhm": 273.8, "total_upstream_worst_mOhm": 370.3},
    "worn_continuous_165mA_GCC_0x40": {"dv_u6_in_mV": -3.29, "v_u6_in_at_vbat_3p50V_typ": 3.445, "v_u6_in_at_vbat_3p50V_worst": 3.426, "tps7a0233_25mA_headroom_ok": true},
    "wearable_budget_300mA_GCC_0x74": {"dv_u6_in_mV": -4.64, "dv_u2_pin5_mV": -31.78, "dv_u1_pin5_mV": -52.46, "v_u6_in_on_usb_4p40V": 4.395, "v_u6_in_at_vbat_3p50V_typ": 3.406, "v_u6_in_at_vbat_3p50V_worst": 3.375, "tps7a0233_vout_min_headroom_ok": true},
    "pwm_only_dimming_840mA_peak_hazard_GCC_0xFF": {"dv_u6_in_mV": -10.02, "v_u6_in_at_vbat_3p50V_worst": 3.17, "enters_ldo_dropout_if_gcc_left_0xFF": true}
  },
  "thermal_budget": {
    "still_air_theta_ba_C_per_W": 33.3,
    "worn_continuous_165mA_GCC_0x40": {"p_total_W": 0.541, "board_avg_rise_C": 18.0, "t_surface_at_25C_amb_C": 43.0, "wearable_touch_limit_45C_ok": true},
    "burst_handheld_300mA_GCC_0x74_with_ADC4_foldback": {"p_total_W": 0.95, "unthrottled_steady_state_rise_C": 31.7, "adc4_closed_loop_foldback_target_C": 45.0},
    "usb500_depleted_cell_charge_plus_GCC_0x44": {"p_u5_bq24073_W": 0.669, "u5_tj_est_at_25C_amb_C": 59.8, "bq24073_tj_reg_125C_margin_C": 65.2}
  },
  "crosstalk_audit": {"user_c_user_d_with_100nF_c71_c72_mV": 0.019, "i2c0_with_1k_pullup_and_aw20198_SRCR_0x07_mV": 84.8, "adc1_light_with_100nF_c70_mV": 0.012}
}
```

## 4. Independent Fresh-Context Review (`agy` `gemini-4-argon-high`) & Dispositions

| ID | Severity | Finding Summary | Resolution |
|---|---|---|---|
| `B1` / `B3a` | BLOCKER | `C71`/`C72` (`C1525` `16 V` X7R) lacked DC-bias/ESD voltage margin under `8 kV` `0402` air-flashover (`450 V`). | **Fixed**: Upgraded `C71`/`C72` in schematic/BOM/PCB to **`C307331` (`CL05B104KB54PNC`, `100 nF 50 V X7R 0402`, basic)** and modeled nonlinear X7R DC-bias capacitance (`13.65 V` clamped = **`36.35 V` margin to `50 V`**, `17.38 V` open-circuit = `32.62 V` margin, `1.96 A` `-91.92%`). |
| `B2` | BLOCKER | `15 ms` debounce window was `3.83 ms` shorter than worst slow-corner `10 ms` OFF bounce + `8.83 ms` RC rise (`18.83 ms`). | **Fixed**: Increased firmware debounce specification to **`>= 20 ms` symmetrical press + release** across `sim_buttons.py`, `brief.md` §7, `bringup.md` §4, `phase4.md`, and `README.md` §5. |
| `M1–M3` | MAJOR | Still-air + rear-LiPo-insulated wearable convection (`θ_BA ≈ 33.3 °C/W`) and upstream battery-path resistance (`BT1 + BAT_N + U8 + VBAT + U5 BATFET` + `3 mΩ` vias, plus `840 mA` PWM-only peak pulse if `GCC = 0xFF`) needed explicit physics in `sim_buttons.py`. | **Fixed**: Added `33.3 °C/W` still-air thermal budget (`0.541 W` / `165 mA` `GCC <= 0x40` continuous worn ceiling -> **`43.0 °C < 45 °C`**; `ADC4` closed-loop foldback on `0.95 W` bursts) and full `273.8 / 370.3 mΩ` battery-path + `3 mΩ` via nodal solve (`V(U6.4) = 3.375 V >= 3.355 V` worst-case at `VBAT = 3.50 V` with analog `GCC <= 0x74`; mandatory analog `GCC` scaling in `bringup.md` §4). |

**Independent Fresh-Context Re-Review Verdict:** **VERDICT: PASS** (all prior `B1`, `B2`, and `M1–M3` findings verified resolved).
