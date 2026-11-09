# Gate 8: simulation and signal integrity (`parallelogram-p2-132-usb6`)

Status: **passed**

## Checklist (`references/simulation.md` §Gate checklist)
- [x] **Trigger list generated from `design/nets-parallelogram-p2-132-usb6.csv` (table below — covering SI, bounce, 2-regime ESD, `VSYS` nodal PDN, thermal, and crosstalk)**
- [x] **Each triggered item has a quantitative simulation result (`design/sim/p2-132-usb6/{sim_buttons.py,results.json,debounce_esd.png,README.md}` + inherited `design/sim/p2-132/results/P0..P4`)**
- [x] **Aggressor / victim parallel-segment & switching crosstalk audit run across all `4921` routed tracks (`729` vias), all couplings quantified & bounded**
- [x] **Design & firmware findings fed back (`>= 20 ms` press+release software debounce, `AW20198` `SRCR = 0x07` + `GCC <= 0x74`, `PADS_QSPI.SLEWFAST = 0`, and `16×` `ADC1` averaging documented in `brief.md` §7, `bringup.md` §4, `stackup.md`, and `README.md` §5)**
- [x] **Stronger-model (`agy` `gemini-4-argon-high`) fresh-context SI/EMC review completed & verified**

## 1. Trigger Matrix from `design/nets-parallelogram-p2-132-usb6.csv` (`118` Nets)

| Trigger Category | Nets on `p2-132-usb6` | Routed Geometry | Simulation / Physics Evaluation (`design/sim/p2-132-usb6/results.json`) | Status |
|---|---|---|---|---|
| **New West-Edge User Buttons (`SIGNAL`, 2-regime ESD + `10 ms` bounce)** | `/MCU/USER_C` (`GPIO9`), `/MCU/USER_D` (`GPIO0`), `Net-(R46-Pad2)`, `Net-(R47-Pad2)` | `SW5/6 -> R46/47`: `4.31 / 4.61 mm` on `B.Cu` (`0` vias); `/MCU/USER_C/D`: `31.05 / 13.22 mm` | • `V_OL,wc = 68.64 mV << 800 mV` (`731.36 mV` margin); wetting `37.03–67.95 µA` (`>= 10 µA`), peak cap discharge `3.10–3.50 mA` (`<= 50 mA` `EVQP7J01P` rating)<br>• Two-regime ESD: insulating plastic plunger + outboard `Pin 2 = GND` (`|x| = 12.10 mm`) shields `Pin 1`; `400 V` sub-sparkover gives `3.87 V` (`4.8 mA`); direct `8 kV` IEC contact WITH `350 V` `0402` air-flashover charge-shares `150 pF` into `100 nF` `C71`/`C72` (`50 V` X7R, `37.29 V` margin), cutting peak clamp current `24.24 A -> 1.77 A` (**`-92.69%`**)<br>• Worst slow-corner `10 ms` OFF bounce + rise to `V_IH+` (`2.0 V`) = `18.83 ms` (`18.17 ms` sim) -> **`>= 20 ms` press+release firmware debounce** across `SW1..SW6` | **Simulated & Passed** |
| **`POWER` / `POWER_HI` Board-Extracted `VSYS` Nodal PDN** | `VSYS` (`U5.10/11` -> `U6.4`, `U1.5/22`, `U2.5/22`), `VBAT`, `VBUS`, `+3V3`, `+1V1` | `VSYS`: `0.16–0.20 mm`, `156.5 mm` network, `31` vias; `VBAT/VBUS`: `0.25 mm` | Exact resistive nodal solve from `parallelogram.kicad_pcb` (`solve_vsys_nodal_pdn`):<br>• **`300 mA` wearable budget (`GCC <= 0x74`, `intent.md` R19) + `25 mA` LDO:** `ΔV(U6.4) = -60.72 mV`, `ΔV(U2.5) = -113.31 mV`, `ΔV(U1.5) = -114.50 mV` -> `V(U6.4) = 4.339 V` on USB and **`3.437 V >= 3.42 V`** down to `V_BAT = 3.55 V` (**`0` LDO dropout**)<br>• **Unthrottled `656 mA` (`GCC = 0xFF`):** `ΔV(U6.4) = -126.74 mV`, `ΔV(U1.5) = -244.88 mV` (guarded in FW by `GCC <= 0x74`, `<= 0x44` charging, foldback `< 3.50 V`) | **Simulated & Passed** |
| **Whole-Board & `U5` Charger Thermal Budget** | `U1/U2` (`5` EP vias each), `U3` (`5` EP vias), `U5` (`2` EP vias), `132` LEDs | `1,309.17 mm²` unbroken `In1.Cu` `plane GND` heat spreader | • **Wearable `300 mA` battery mode (`0.95 W` total):** board rise **`+11.2 °C`** -> **`36.2 °C` at `25 °C` ambient** (`< 45 °C` touch limit)<br>• **`USB500` charging depleted `3.1 V` cell (`297 mA`) + `175 mA` `GCC = 0x44`:** `P(U5) = 0.669 W` -> **`T_J(U5) = 59.8 °C`** (`65.2 °C` margin below `125 °C` `BQ24073` regulation) | **Simulated & Passed** |
| **`DIFF_HS` (`USB 2.0` Full-Speed `12 Mb/s`, `t_r >= 4 ns`)** | `/Power/USB_D*_C`, `USB_DP`/`USB_DM`, `/MCU/USB_D*_MCU` | End-to-end `DP = 18.634 mm`, `DM = 17.642 mm` (`skew = 0.992 mm = 6.6 ps`); `U3 -> R14/15` = `2.54 / 2.46 mm` (`0` vias) | `l_crit = 4000 ps / (2 × 6.6 ps/mm) = 303 mm` (`stackup.md` conservative `125 mm`); actual `18.63 mm = 0.062 × l_crit` (lumped regime), damped by `27 Ω` (`R14`/`R15`) + `USBLC6-2SC6` (`U7`). Inherited FDTD check in `design/sim/p2-132/results/P0`. | **Verified (`<< l_crit`)** |
| **`SE_HS` (`QSPI` `66–104 MHz`, `t_r ~ 1.5 ns`)** | `/MCU/QSPI_SCLK`, `QSPI_SS`, `QSPI_SD0..3` | `9.2–16.8 mm` (`<= 25 mm` `.kicad_dru` rule; `skew = 7.6 mm = 50 ps << 4.8 ns` half-UI) | `< 0.15 × l_crit` (`113.6 mm`), routed over unbroken `In1.Cu` `plane GND` (`1` piece) with `PADS_QSPI.SLEWFAST = 0`. Inherited FDTD eye check in `design/sim/p2-132/results/P1`. | **Simulated & Passed** |
| **`CLOCK` (`12 MHz` crystal) & `SWITCH` (`VREG_LX`)** | `Net-(U3-XIN/XOUT)`, `Net-(C24-Pad1)`, `/MCU/VREG_LX` | Crystal `1.54–6.15 mm` (`0` vias, `B.Cu`); `VREG_LX` `2.183 mm²` pour | `vendor GND` guard pour around `Y1`; `LX cutout L2` (`In1.Cu`) + `LX cutout L3` (`In2.Cu`) prevent any trace or plane coupling beneath `VREG_LX`/`L1.2`. | **Verified** |

## 2. Crosstalk & Parallel-Coupling Audit (`sim_buttons.py` + `audit_phase7_8.py`)
- **`/MCU/USER_C` & `/MCU/USER_D`:** Shunted by `C71/C72 = 100 nF` (`Z < 1.6 Ω` at `>= 1 MHz`) -> **`0.019 mV` peak coupled noise** from `QSPI_SS` / `CS/SW` scan edges (`<< 1.20 V` Schmitt hysteresis margin).
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
    "sub_sparkover_400V_pin1": {"v_gpio_peak_V": 3.874, "i_clamp_peak_mA": 4.8},
    "direct_8kV_pin1_with_0402_flashover": {"open_circuit_charge_share_delta_V": 11.98, "v_gpio_peak_with_clamp_V": 12.71, "i_clamp_peak_A": 1.77, "unbuffered_iec_peak_A": 24.24, "current_attenuation_pct": 92.69, "c71_c72_50V_x7r_margin_V": 37.29}
  },
  "vsys_nodal_pdn": {
    "wearable_budget_300mA_GCC_0x74": {"dv_u6_in_mV": -60.72, "dv_u2_pin5_mV": -113.31, "dv_u1_pin5_mV": -114.5, "v_u6_in_on_usb_4p40V": 4.339, "v_u6_in_at_vbat_3p55V": 3.437, "tps7a0233_vout_min_headroom_ok": true},
    "unthrottled_all_white_656mA_GCC_0xFF": {"dv_u6_in_mV": -126.74, "dv_u2_pin5_mV": -242.27, "dv_u1_pin5_mV": -244.88}
  },
  "thermal_budget": {
    "wearable_battery_300mA_mode": {"p_total_W": 0.95, "board_avg_rise_C": 11.2, "t_surface_at_25C_amb_C": 36.2, "wearable_touch_limit_45C_ok": true},
    "usb500_depleted_cell_charge_plus_GCC_0x44": {"p_u5_bq24073_W": 0.669, "u5_tj_est_at_25C_amb_C": 59.8, "bq24073_tj_reg_125C_margin_C": 65.2}
  },
  "crosstalk_audit": {"user_c_user_d_with_100nF_c71_c72_mV": 0.019, "i2c0_with_1k_pullup_and_aw20198_SRCR_0x07_mV": 84.8, "adc1_light_with_100nF_c70_mV": 0.012}
}
```

## 4. Independent Fresh-Context Review (`agy` `gemini-4-argon-high`) & Dispositions

| ID | Severity | Finding Summary | Resolution |
|---|---|---|---|
| `B1` | BLOCKER | `sim_buttons.py` treated `R46/R47` (`0402`) as linear `1 kΩ` at `1,243 V` (`8 kV` IEC contact), ignoring `0402` air-flashover (`~350 V`) and inherited `SW3/SW4` `1 kΩ`-only ESD note. | **Fixed**: Replaced with physical two-regime ESD solver (`400 V` sub-sparkover + `8 kV` WITH `350 V` `0402` sparkover & `150 pF -> 100 nF` charge sharing: `1.77 A`, `92.69%` attenuation, `37.29 V` `50 V` X7R margin) + insulating plunger / outboard `Pin 2 = GND` shield proof + `SW3/SW4` note. |
| `B2` | BLOCKER | `15 ms` debounce window was `3.83 ms` shorter than worst slow-corner `10 ms` OFF bounce + `8.83 ms` RC rise (`18.83 ms`). | **Fixed**: Increased firmware debounce specification to **`>= 20 ms` symmetrical press + release** across `sim_buttons.py`, `brief.md` §7, `bringup.md` §4, `phase4.md`, and `README.md` §5. |
| `M1–M3` | MAJOR | `phase8.md` cited `design/sim/p2-132/` for PDN, thermal, and switching crosstalk without board-extracted numbers for `p2-132-usb6`. | **Fixed**: Added exact `pcbnew` `VSYS` resistive nodal solver (`solve_vsys_nodal_pdn`), whole-board + `U5` thermal model, and `USER_C/D` / `I2C0` / `ADC1` crosstalk audit directly into `sim_buttons.py` & `debounce_esd.png`, and propagated firmware guards (`GCC <= 0x74`, `SRCR = 0x07`, `SLEWFAST = 0`, `16×` ADC avg) into `bringup.md`. |

**Independent Fresh-Context Re-Review Verdict:** **VERDICT: PASS** (all prior `B1`, `B2`, and `M1–M3` findings verified resolved).
