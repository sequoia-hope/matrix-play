# Gate 8: Simulation & Layout-Coupled Verification — Sunflower `s2-110-usbc`

Status: **`failed`** (all analytical/numerical models, exact `15.2 µm` inner-copper resistances, board-wide aggressor/victim scans, and plots are complete and reproducible in [sim_audit.py](file:///home/sequoia/pcb/round-pendant/design/sim/sunflower-s2-110-usbc/sim_audit.py) and [README.md](file:///home/sequoia/pcb/round-pendant/design/sim/sunflower-s2-110-usbc/README.md); however, per [simulation.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/simulation.md#L38) *"Gate: passed when every triggered analysis shows margin or its layout change is fed back into Phase 7"*, Gate 8 is held because `3` hardware layout defects confirmed by simulation — `U4.8` `312–554 mV` 4-bit QSPI read SSO droop, `C17` `CFILT` shared-via high-pass ground bounce, and `19–48 mV_pk` `VREG_LX → In2.Cu ADC_AVDD` mutual-inductance coupling — have not yet been fed back into PCB copper; complete firmware bench workarounds are documented for `Rev S3C` if ordered as a prototype at Gate 10).

## Checklist ([simulation.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/simulation.md), Phase 8)

| Check | Evidence | State |
|---|---|---|
| Every Phase 3 / Phase 8 trigger audited with reproducible script ([sim_audit.py](file:///home/sequoia/pcb/round-pendant/design/sim/sunflower-s2-110-usbc/sim_audit.py)) | Verbatim output below (`SIM_EXIT=0`, `0` failed path lookups) | passed |
| Crystal `Y1` (`ABM8-272-T3`, `15 pF × 2`, `200 µW` max) & `I2C0` (`1 MHz` Fm+, `R21/R22 = 1.0 kΩ`, `40 pF` bus) | `DL ≈ 85–125 µW ≤ 200 µW`; `I2C0` $t_r(30\text{–}70\%) = 33.9\text{ ns} \le 120\text{ ns}$, $t_{\text{HIGH}} \approx 448\text{ ns} \ge 260\text{ ns}$ | passed |
| USB 2.0 FS (`12 Mbit/s`) flight-time skew & `USBLC6-2P6` (`+31.2 V` clamp) | `DP = 233.4 ps`, `DM = 259.4 ps`, true dielectric-weighted skew **`26.0 ps ≤ 2,000 ps`**; `27 Ω` `R14/15` limit `U7` residual into `U3` | passed (FS) |
| DC IR drop (`VBAT`/`BAT_N` `438 mΩ` PCB / `550 mΩ` total, `VSYS → U1` `236.7 mΩ`) & LED headroom ([pdn_headroom.png](file:///home/sequoia/pcb/round-pendant/design/sim/sunflower-s2-110-usbc/pdn_headroom.png)) | At wearable cap `GCC = 107`, typ G/B LEDs stay in constant-current regulation ($V_{\text{CS}} \ge 300\text{ mV}$) down to `V_cell ≈ 3.59 V` (`+760..+1,240 mV` on `4.40 V` USB) | passed (with `GCC ≤ 107`) |
| `U4.8` (`W25Q128JVPIQ`) QSPI SSO supply droop (`8.56 mm` / `4`-via loop to `C14`, `~9 nH`) | **4-bit Quad-SPI (`0xEB`) droops `312–554 mV` (`VCC_min ≈ 2.75 V` vs `2.70 V` floor)**; `Rev S3C` bench workaround = 1-bit/2-bit XIP (`78–156 mV`); `Rev S3D` = move `C22` to `U4.8` | failed (`B2` copper pending) |
| `RP2350` `CFILT` (`C17`) shared `PGND` via bounce, `VREG_LX → In2.Cu ADC_AVDD` coupling, & `U3.39` `5.9 MHz` anti-resonance | **`~30 mV` HF bounce via `C17` ESL** and **`19–48 mV_pk` (`2.5 ns`) `VREG_LX` spikes on `ADC_AVDD`**; `Rev S3D` = isolate `CFILT` via & move `LX` cutout to `In2.Cu` | failed (`B3` copper pending) |
| Pouch-backed (`35 K/W`, $\tau_{\text{th}} \approx 91\text{ s}$) thermal & `45 °C` LiPo charge protection ([thermal_rise.png](file:///home/sequoia/pcb/round-pendant/design/sim/sunflower-s2-110-usbc/thermal_rise.png)) | Mandatory firmware caps synced into [bringup-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/bringup-s2-110-usbc.md): **`GCC ≤ 105`** battery (`≤ 48 °C` skin), **`GCC ≤ 9` CC / `≤ 24` CV** gated on **`PGOOD == 0 || CHG == 0`** (`≤ 45 °C` LiPo) | passed (firmware gated) |

## Real Command Outputs (`2026-11-08`)

### `python3 design/sim/sunflower-s2-110-usbc/sim_audit.py`
```text
=== 1. PHASE 8 SIMULATION TRIGGER & COPPER SUMMARY (JLC04161H-7628, t_in=15.2 um) ===
  VBUS                   len= 26.11mm vias=10 w=[0.25..0.25] R70_all= 102.8mOhm (B.Cu:9.22, F.Cu:3.44, In2.Cu:13.45)
  VBAT                   len= 69.05mm vias=11 w=[0.25..0.25] R70_all= 279.2mOhm (B.Cu:27.18, F.Cu:3.94, In2.Cu:37.93)
  /Power/BAT_N           len= 53.01mm vias= 4 w=[0.25..0.25] R70_all= 254.5mOhm (B.Cu:10.82, In2.Cu:42.19)
  VSYS                   len= 77.31mm vias=14 w=[0.16..0.20] R70_all= 344.5mOhm (B.Cu:44.89, F.Cu:2.49, In2.Cu:29.93)
  +3V3                   len= 90.89mm vias=24 w=[0.15..0.20] R70_all= 388.5mOhm (B.Cu:58.18, F.Cu:1.91, In2.Cu:30.80)
  +1V1                   len= 29.14mm vias= 3 w=[0.10..0.20] R70_all= 125.9mOhm (B.Cu:20.54, In2.Cu:8.60)
  GND                    len= 75.80mm vias=56 w=[0.20..0.20] R70_all= 245.3mOhm (B.Cu:68.02, F.Cu:2.04, In2.Cu:5.74)
  /MCU/VREG_AVDD         len=  4.55mm vias= 0 w=[0.10..0.10] R70_all=  26.8mOhm (B.Cu:4.55)
  /Power/USB_DP_C        len= 15.94mm vias= 3 w=[0.15..0.15] R70_all=  94.9mOhm (B.Cu:8.78, F.Cu:0.85, In2.Cu:6.31)
  /Power/USB_DM_C        len= 20.27mm vias= 4 w=[0.15..0.15] R70_all= 129.9mOhm (B.Cu:10.44, In2.Cu:9.82)
  USB_DP                 len= 16.05mm vias= 2 w=[0.10..0.15] R70_all=  63.2mOhm (B.Cu:12.68, F.Cu:3.37)
  USB_DM                 len= 13.05mm vias= 2 w=[0.10..0.15] R70_all= 105.5mOhm (B.Cu:2.48, In2.Cu:10.57)
  /MCU/USB_DP_MCU        len=  2.56mm vias= 0 w=[0.15..0.15] R70_all=  10.1mOhm (B.Cu:2.56)
  /MCU/USB_DM_MCU        len=  2.56mm vias= 0 w=[0.15..0.15] R70_all=  10.0mOhm (B.Cu:2.56)
  /MCU/QSPI_SCLK         len=  6.66mm vias= 2 w=[0.10..0.10] R70_all=  85.7mOhm (B.Cu:0.62, In2.Cu:6.04)
  /MCU/QSPI_SD0          len=  5.61mm vias= 2 w=[0.10..0.10] R70_all=  55.2mOhm (B.Cu:2.72, In2.Cu:2.89)
  /MCU/QSPI_SD1          len= 11.10mm vias= 2 w=[0.10..0.10] R70_all= 117.4mOhm (B.Cu:4.33, In2.Cu:6.77)
  /MCU/QSPI_SD2          len= 13.85mm vias= 4 w=[0.10..0.10] R70_all= 146.2mOhm (B.Cu:5.44, In2.Cu:8.41)
  /MCU/QSPI_SD3          len=  5.51mm vias= 2 w=[0.10..0.10] R70_all=  63.9mOhm (B.Cu:1.41, In2.Cu:4.10)
  /MCU/QSPI_SS           len= 13.34mm vias= 2 w=[0.10..0.10] R70_all= 111.9mOhm (B.Cu:9.00, In2.Cu:4.34)
  Net-(R16-Pad2)         len= 16.87mm vias= 4 w=[0.10..0.10] R70_all= 119.7mOhm (B.Cu:13.51, F.Cu:0.71, In2.Cu:2.65)
  Net-(U3-XIN)           len=  8.44mm vias= 0 w=[0.15..0.15] R70_all=  33.2mOhm (B.Cu:8.44)
  Net-(U3-XOUT)          len=  1.33mm vias= 0 w=[0.15..0.15] R70_all=   5.2mOhm (B.Cu:1.33)
  Net-(C24-Pad1)         len=  1.68mm vias= 0 w=[0.15..0.15] R70_all=   6.6mOhm (B.Cu:1.68)
  I2C_SDA                len= 89.07mm vias=17 w=[0.10..0.10] R70_all= 862.3mOhm (B.Cu:30.91, F.Cu:14.18, In2.Cu:43.97)
  I2C_SCL                len= 86.70mm vias=15 w=[0.10..0.10] R70_all= 908.1mOhm (B.Cu:24.76, F.Cu:10.19, In2.Cu:51.75)
  /MCU/ACC_SDA           len= 13.78mm vias= 2 w=[0.10..0.10] R70_all= 155.7mOhm (B.Cu:4.06, In2.Cu:9.71)
  /MCU/ACC_SCL           len= 18.35mm vias= 4 w=[0.10..0.10] R70_all= 212.2mOhm (B.Cu:4.79, In2.Cu:13.56)
  /MCU/LIGHT             len= 16.55mm vias= 3 w=[0.10..0.10] R70_all=  97.5mOhm (B.Cu:8.73, F.Cu:7.81)
  VBAT_SENSE             len= 33.71mm vias= 2 w=[0.10..0.10] R70_all= 328.2mOhm (B.Cu:16.83, In2.Cu:16.88)
  SW worst copper R70  : /Driver 1 and matrix/SW1_5 len=116.29mm R70=845.5mOhm vias=11
  CS worst copper R70  : /Driver 1 and matrix/CS1_15 len=48.86mm R70=460.9mOhm vias=5

=== 2. EXACT SHORTEST-PATH PAD-TO-PAD DC RESISTANCE @ 70 C ===
  VBUS: J1.A4 -> U5.13              : R_70 =  13.40 mOhm, L_track =  2.48 mm, transitions = 4
  VBAT: BT1.1 -> U5.2               : R_70 = 191.42 mOhm, L_track = 44.13 mm, transitions = 6
  BAT_N: BT1.2 -> U8.4              : R_70 = 246.57 mOhm, L_track = 48.59 mm, transitions = 4
  VSYS: U5.10 -> U6.4 (3V3 LDO)     : R_70 = 153.05 mOhm, L_track = 25.66 mm, transitions = 6
  VSYS: U5.10 -> U1.5 (PVCC)        : R_70 = 236.73 mOhm, L_track = 47.57 mm, transitions = 10
  VSYS: U5.10 -> U2.5 (PVCC)        : R_70 =  53.67 mOhm, L_track = 11.99 mm, transitions = 2
  +3V3: U6.1 -> U3.49 (VREG_VIN)    : R_70 =  28.85 mOhm, L_track =  6.45 mm, transitions = 2
  +3V3: U6.1 -> U3.44 (ADC_AVDD)    : R_70 =  46.76 mOhm, L_track =  9.41 mm, transitions = 2
  +3V3: U6.1 -> U4.8 (Flash VCC)    : R_70 =  81.21 mOhm, L_track = 15.98 mm, transitions = 2
  +3V3: C14.1 -> U4.8 (nearest cap) : R_70 =  47.68 mOhm, L_track =  8.56 mm, transitions = 4
  +1V1: C18.1 -> U3.50 (VREG_FB)    : R_70 =   4.00 mOhm, L_track =  1.34 mm, transitions = 0
  +1V1: C18.1 -> U3.23 (DVDD N)     : R_70 =  11.20 mOhm, L_track =  3.61 mm, transitions = 0
  +1V1: C18.1 -> U3.39 (DVDD E)     : R_70 =  46.99 mOhm, L_track =  8.48 mm, transitions = 2
  Combined PCB battery loop (VBAT + BAT_N) @ 70 C = 438.0 mOhm (+ ~112 mOhm conn+U8+U5 FETs = 550.0 mOhm total)

=== 3. BOARD-WIDE AGGRESSOR / VICTIM COUPLING SCAN ===
  [3a] In2.Cu segments under B.Cu VREG_LX pour / L1 (h = 0.2104 mm):
    In2.Cu +3V3             (100.34,96.41)->(101.94,97.31) w=0.20mm L=1.84mm ov_LX_pour=0.09mm ov_L1_body=0.00mm C_mut~=6fF
    In2.Cu VSYS             (104.52,100.76)->(99.72,101.76) w=0.20mm L=4.90mm ov_LX_pour=0.49mm ov_L1_body=0.25mm C_mut~=33fF
  [3b] Top co-planar parallel runs (edge gap <= 0.30 mm, parallel >= 0.80 mm):
    In2.Cu /Driver 2 and matrix/SW2_6   <-> I2C_SDA           : L_par= 9.92 mm, min_gap=0.228 mm
    In2.Cu /Driver 1 and matrix/CS1_15  <-> VBAT_SENSE        : L_par= 6.79 mm, min_gap=0.115 mm
    In2.Cu /Driver 2 and matrix/SW2_6   <-> I2C_SCL           : L_par= 5.30 mm, min_gap=0.122 mm
    In2.Cu /Driver 2 and matrix/SW2_7   <-> I2C_SCL           : L_par= 3.59 mm, min_gap=0.200 mm
  [3c] Top adjacent-layer broadside runs (h = 0.2104 mm, d_cc <= 0.35 mm, parallel >= 0.50 mm):
    B.Cu<->In2.Cu  /Driver 1 and matrix/SW1_5   <-> I2C_SDA           : L_par= 8.94 mm, min_dcc=0.047 mm
    B.Cu<->In2.Cu  /Driver 2 and matrix/SW2_8   <-> I2C_SDA           : L_par= 8.44 mm, min_dcc=0.007 mm
    In2.Cu<->B.Cu  /Driver 2 and matrix/SW2_6   <-> I2C_SCL           : L_par= 7.19 mm, min_dcc=0.272 mm
    In2.Cu<->B.Cu  /Driver 2 and matrix/SW2_3   <-> +1V1              : L_par= 5.29 mm, min_dcc=0.008 mm

=== 4. QUANTITATIVE SI / PI / THERMAL CHECKPOINTS ===
  U4.8 SSO [4-bit Quad-SPI (0xEB, fast edge)]: Q=92.4 pC, dV_droop ~=   554 mV -> V_CC,min ~= 2.75 V (spec >= 2.70 V)
  U4.8 SSO [4-bit Quad-SPI (0xEB, 25% DRV)  ]: Q=92.4 pC, dV_droop ~=   312 mV -> V_CC,min ~= 2.99 V (spec >= 2.70 V)
  U4.8 SSO [2-bit Dual-SPI (0xBB, 25% DRV)  ]: Q=46.2 pC, dV_droop ~=   156 mV -> V_CC,min ~= 3.14 V (spec >= 2.70 V)
  U4.8 SSO [1-bit Fast-Read (0x0B, 25% DRV) ]: Q=23.1 pC, dV_droop ~=    78 mV -> V_CC,min ~= 3.22 V (spec >= 2.70 V)
  USB FS flight time: DP = 233.4 ps (34.55 mm, 5 vias), DM = 259.4 ps (35.87 mm, 6 vias), |dt| = 26.0 ps (FS budget <= 2000 ps)
  I2C0 1 MHz Fm+ (R21/R22=1.0 kOhm, C_bus~=40 pF): tr(30-70%)=33.9 ns (<=120 ns), t(0->2.4V)=52.0 ns -> t_HIGH~=448 ns (>=260 ns)
  Thermal [Wearable Battery (25 C amb, 35 K/W, 48 C skin limit)]: GCC_max = 107 (T@GCC128=51.2 C, T@GCC255=71.7 C)
  Thermal [USB Charging CV taper (25 C amb, 35 K/W, P_chg=0.27W @4.1V, 45 C LiPo limit)]: GCC_max =  27 (T@GCC128=63.3 C, T@GCC255=86.4 C)
  Thermal [USB Charging CC mid (25 C amb, 35 K/W, P_chg=0.36W @3.8V, 45 C LiPo limit)]: GCC_max =   9 (T@GCC128=66.5 C, T@GCC255=89.6 C)
  Thermal [USB Charging low-bat (25 C amb, 35 K/W, P_chg=0.45W @3.5V, 45 C LiPo limit)]: GCC_max =   0 (T@GCC128=69.6 C, T@GCC255=92.7 C)
  Thermal [Hot Ambient Battery (40 C amb, 35 K/W, 60 C LiPo discharge limit)]: GCC_max =  89 (T@GCC128=66.2 C, T@GCC255=86.7 C)
```

## Independent Fresh-Context Review (`gemini-4-argon-high`)

| ID | Severity | Reviewer Finding | Disposition & Action Taken |
|---|---|---|---|
| `B1` | `BLOCKER` | Initial `sim/README.md` omitted `0.16 W` MCU baseline in text, used `28 K/W` instead of pouch-backed `35 K/W` on battery, and gated charging cap only on `CHG == 0` instead of `PGOOD == 0 || CHG == 0` | **Fixed in `sim_audit.py`, `sim/README.md`, `thermal_rise.png`, `intent-s2-110-usbc.md`, & `bringup-s2-110-usbc.md`:** Standardized on `35 K/W` pouch-backed model (`GCC ≤ 105` battery, `GCC ≤ 9` CC / `≤ 24` CV gated on `PGOOD == 0 || CHG == 0` + cold-boot `ADC4` `ΔT` throttling). |
| `B2` | `BLOCKER` | `U4.8` (`W25Q128JVPIQ`) `8.56 mm` / `4`-via decoupling gap (`~9 nH`) causes `312–554 mV` 4-bit QSPI read SSO droop (`U4` drives `SD0..3` on reads, not `U3`) | **Modeled in `sim_audit.py` & Gate 8 held (`Rev S3D` move `C22`):** Documented 1-bit (`0x0B`, `78 mV`) / 2-bit (`0xBB`, `156 mV`) SPI XIP bench mitigation for `Rev S3C` in [bringup-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/bringup-s2-110-usbc.md). |
| `B3` | `BLOCKER` | Initial `sim/README.md` cited Round Pendant `R13 = 2.2 Ω` / missing `C19`, understated `CFILT` high-pass ground bounce via shared `PGND` via, and omitted $M\,dI/dt$ (`19–48 mV_pk`) on `In2.Cu` `ADC_AVDD` + `U3.39` `5.9 MHz` anti-resonance | **Fixed in `sim/README.md` & Gate 8 held (`Rev S3D` copper fixes):** Verified `s2-110-usbc` actually has `R13 = 33 Ω` (`f_c ≈ 2.01 kHz`) and `C19 = 4.7 µF` (`C_eff ≈ 5.0 µF`), and added full `C17` ESL high-pass bounce (`~30 mV`), `M dI/dt` (`19–48 mV_pk`), and `5.9 MHz` (`1.2 Ω`) spoke anti-resonance models. |
| `B4` | `BLOCKER` | Script lived only in scratchpad, failed (`-1.00`) on `BAT_N`/`VBUS`, used `17.5 µm` vs `15.2 µm` inner Cu, and lacked board-wide Aggressor/Victim scan | **Fixed:** Created [sim_audit.py](file:///home/sequoia/pcb/round-pendant/design/sim/sunflower-s2-110-usbc/sim_audit.py) with `t_in = 15.2 µm` (`1.357 mΩ/sq` @ `70 °C`), T-junction/multi-pad Dijkstra solver (`BAT_N = 246.6 mΩ`, `VBAT = 191.4 mΩ`, `VBUS = 13.4 mΩ`), and `4,462`-segment co-planar + broadside scan. |
| `M1` | `MAJOR` | `pdn_headroom.png` plotted against `VSYS` without subtracting `550 mΩ` battery+`U8`+`U5` drop from `V_cell` | **Fixed in `sim_audit.py` & `pdn_headroom.png`:** Plotted directly against `V_cell` (`3.50..4.20 V` with full `550 mΩ` loop drop) + `4.40 V` USB marker. |
| `M2` | `MAJOR` | Reviewer checked `2.2 kΩ` `I2C0` pull-ups (`t_0→2.4V` risk) from stale Round Pendant text | **Resolved (`s2-110-usbc` uses `R21 = R22 = 1.0 kΩ`, `C11702`):** Even at `40 pF` (`89.1 mm`, `17` vias), `1.0 kΩ` gives $t_r(30\text{–}70\%) = 33.9\text{ ns}$ and $t_{0\to 2.4\text{V}} = 52.0\text{ ns}$ ($t_{\text{HIGH}} = 448\text{ ns} \ge 260\text{ ns}$). |
| `M3` | `MAJOR` | Reviewer checked `100 µW` crystal drive limit from stale `X322512MSB4SI` citation | **Resolved (`s2-110-usbc` uses `ABM8-272-T3`, `C20625731`, `15 pF × 2`, `200 µW` max):** `85–125 µW` drive power has ample margin below `200 µW`. |
| `M4–M5` | `MAJOR` | `ADC4` offset & `91 s` thermal time constant; `USBLC6-2P6` `VCL+ = +31.2 V` & `26.0 ps` split-layer USB skew | **Fixed in `sim_audit.py`, `sim/README.md`, & `bringup-s2-110-usbc.md`.** |
| `m1–m4` | `MINOR` | `L1` `Isat = 2.8/2.4 A`, `U6` `[0.5, 22] µF`, `U5` `22 µF` caps & `4.50 V` `VIN-DPM`, `Q2` `30 µA @ 100 lx` (`~440 lx` sat), `OD=1, PUE=0` on `ADC0/1`, `GPIO6` `LED_SDB` `100 nF` note | **Fixed across `sim/README.md` & `bringup-s2-110-usbc.md`.** |
