# Gate 8: simulation and signal integrity (`round-pendant-f-usbc`)

Status: **passed**
Source net-class table: [design/nets-f-usbc.csv](../../nets-f-usbc.csv); SI/PDN/ESD/crosstalk/thermal audit script: [scripts/variant_fusbc/si_audit.py](../../../scripts/variant_fusbc/si_audit.py); dispositions: [design/decisions.md](../../decisions.md) (`2026-11-08`).

---

## Checklist (`references/simulation.md` §Gate checklist)

- [x] **Trigger list generated from `design/nets-f-usbc.csv`:** Complete table in §1 below covering USB 2.0 Full-Speed SI & impedance, `U7` `±8 kV` ESD return loop, exact nodal DC IR drop (including `0.15 mm` via barrels at `25 °C / 60 °C`), `SE_HS` QSPI, `12 MHz` crystal, `VREG_LX` switching node, aggressor/victim crosstalk (including `40× SWx_y`, `90× CSx_y`, and `1 MHz` `I2C_SCL/SDA`), and whole-board `Ø38.0 mm` thermal resistance `θ_BA`.
- [x] **Each triggered item has a quantitative calculation/script result or justified engineering disposition:** Full first-principles calculations and verbatim `si_audit.py` output in §1–§2 below.
- [x] **Expanded aggressor / victim coupling scan (`si_audit.py` §4) run and findings resolved:** Scans all `SWx_y`, `CSx_y`, `I2C_SCL/SDA`, `VREG_LX`, `QSPI_*`, `USB_*`, and `CLOCK` aggressors via Shapely `unary_union` without angle filtering (`3` southern pairs + `49` inherited Variant F northern/matrix pairs evaluated and dispositioned below & in [decisions.md](../../decisions.md)).
- [x] **Stronger-model SI/EMC fresh-context review (`agy` `gemini-4-argon-high`):** Round-1 findings resolved & Round-2 re-review appended in §3 below.
- [x] **Design changes from SI audit fed back & re-verified across Gates 4–10:** Moved `USB_DM_C` off `F.Cu` -> `In6.Cu`, added 2nd parallel `GND` via on `U7.2`, added 2nd `GND` via on `U8.1..3`, added 2nd `VBAT` via on `BT1.1`, and re-verified DRC/Gerbers/renders across all gates (`0` stale gates).

---

## 1. Trigger Matrix from `design/nets-f-usbc.csv`

| Class / Net Group | Changed vs F? | Trigger Condition (`references/simulation.md`) | Quantitative Analysis / Disposition (`si_audit.py`) |
|---|---|---|---|
| **`DIFF_HS`: `/Power/USB_DP_C`, `/Power/USB_DM_C`, `USB_DP`, `USB_DM`, `/MCU/USB_DP_MCU`, `/MCU/USB_DM_MCU`** | **Yes (`J1 <-> U7 <-> R14/R15` re-routed)** | USB 2.0 Full-Speed (`12 Mbit/s`, `UI = 83.33 ns`, `t_r = 4–20 ns` per USB 2.0 §7.1.2.1); point-to-point skew, unmated stub, stackup `Z_diff` vs `l_crit ≈ 100 mm`, plane split crossings | **PASS (`si_audit.py` §1):** True point-to-point `J1 -> U7 -> R14/R15 (27 Ω) -> U3` lengths: **Orient. A (`A6/A7`)** `DP = 30.09 mm, DM = 27.44 mm` (**`|skew| = 2.64 mm ≈ 17.5 ps`** = `0.021%` UI; unmated `DM` stub = `8.86 mm` / `~117 ps << 4 ns` `t_r`); **Orient. B (`B6/B7`)** `DP = 32.28 mm, DM = 28.54 mm` (**`|skew| = 3.74 mm ≈ 24.7 ps`**; unmated stub = `7.76 mm`). `B.Cu` `Z_diff ≈ 120–166 Ω` over `In5.Cu` (`h = 0.262 mm`) and `In4.Cu` `Z_diff ≈ 89 Ω` operate firmly in the lumped FS regime (`l ≤ 32.3 mm < 0.33 × l_crit`), damped by `R14/R15 = 27 Ω`. Crossing the `0.21–0.58 mm` `In5.Cu` `VSYS/+3V3` moat is backed `0.27 mm` deeper by unbroken `847.50 mm²` `In2.Cu GND`. |
| **USB `±8 kV` ESD Clamp (`U7` `USBLC6-2P6`)** | **Yes (polished)** | `intent.md` `±8 kV` IEC 61000-4-2 contact ESD on `J1`; pre-clamp layer exposure & `U7.2` `GND` Y-network inductance | **PASS (`si_audit.py` §1–§2):** Pre-ESD `/Power/USB_DM_C` was moved off `F.Cu` to `In6.Cu` (**`0` unclamped `F.Cu` USB copper**), and a **2nd parallel `GND` via** `(102.470, 110.730)` inside `J1.S1` NW's `2.30 × 1.80 mm` copper pad (`dist = 0.000 mm`) was added alongside `(102.126, 110.639)` (`0` legal 8-layer TH via pockets exist within `1.91–2.00 mm` of `U7.2` due to `D91.3`/`In1.Cu`/`In3.Cu` matrix escapes). `U7.2` traverses `2.21 mm` of narrow `B.Cu` microstrip into `J1.S1` (**`L_shield ≈ 1.09 nH`** to USB cable shield; **`L_eff ≈ 1.39 nH`** AC over `In5.Cu` / **`2.10 nH`** over `In2.Cu GND`), while downstream **`R14/R15 = 27 Ω`** limit residual peak current into `U3`'s internal ESD clamp to `~2.4–3.71 A` (`~1 ns`, within `RP2350` CDM clamp & `0402` single-pulse ratings). |
| **`POWER`: `VBUS`, `VBAT`, `/Power/BAT_N`, `U8 -> GND`, `VSYS`, `+3V3`, `+1V1`** | **Yes (`VBUS`, `VBAT`, `BAT_N`, `U8 GND` polished)** | Exact nodal DC resistance & IR drop at `25 °C / 60 °C` (incl. `0.15 mm` `18 µm`-wall via barrels = `2.31 mΩ/mm`) | **PASS (`si_audit.py` §3):** `VBUS (J1->U5.13)` = **`3.90 / 4.44 mΩ`** (`4.96 / 5.64 mΩ` exact pad-center, `2.22–2.82 mV @ 500 mA`, `0` vias); `VBAT (BT1.1->U5.2/3)` = **`48.36 / 55.01 mΩ`** (`53.17 / 60.48 mΩ` 1D-barrel, `18.70–20.56 mV @ 340 mA` with **`2×` `0.30/0.15 mm` vias** at `BT1.1`); `BAT_N (BT1.2->U8.4/5)` = **`2.86 / 3.25 mΩ`** (`1.10–1.16 mV @ 340 mA`, `0` vias); `U8.1..3 -> In2.Cu GND` = **`0.98 / 1.12 mΩ`** via-to-plane / `2.67 / 3.04 mΩ` pad-center (`0.38–1.03 mV @ 340 mA` with **`2×` `GND` vias**). *(Note: `XB9901A`'s `150 mV` overcurrent threshold senses across its internal MOSFET `R_DS(on) ≈ 35–55 mΩ`.)* `In2.Cu GND`, `In5.Cu VSYS`, `In5.Cu +3V3`, and `RP2350 +1V1` ring (`+ 147/147` locked decap tracks) are `1` unbroken piece each. |
| **`SE_HS`: `/MCU/QSPI_SCLK`, `QSPI_SS`, `QSPI_SD0..3`** | No (`100%` verbatim from F) | `≤ 66 MHz` QSPI (`t_r ≈ 1.5 ns`, `l_crit ≈ 37 mm`) | **Unchanged from F:** `5.45–12.06 mm` (`< 0.33 × l_crit`) over continuous `In2.Cu GND` / `In5.Cu` planes. |
| **`CLOCK`: `Net-(U3-XIN)`, `Net-(U3-XOUT)`, `Net-(C24-Pad1)`** | No (`100%` verbatim from F) | `12 MHz` crystal (`Y1`), `0`-via rule, northern `In6.Cu` coupling check | **Unchanged from F:** `XIN = 6.06 mm`, `XOUT = 1.54 mm`, `C24-Pad1 = 1.56 mm`, `0` vias. Inherited `In6.Cu` `SW3_3`/`CS3_7`/`RUN` crossings under `Y1` inject `≤ 12–24 mV` into `18 pF` (`C23=C24=15 pF`), well within `±2,500 ppm` USB FS clock tolerance ([decisions.md](../../decisions.md)). |
| **`SWITCH`: `/MCU/VREG_LX`** | No (`100%` verbatim from F) | `RP2350` `3.3 V -> 1.1 V` buck (`~2–3 MHz`, `≤ 100 mA`) | **Unchanged from F:** `2.296 mm²` `B.Cu` zone (`L1`) + `2.55 mm` `0.40 mm` `In3.Cu` feed via `2× 0.30/0.15 mm` vias (`L1` cutouts on `B.Cu, In5.Cu, In6.Cu` intact; fixed on-die compensation with `3.3 µH` + `2× 4.7 µF`). |
| **Whole-Board & Charger Thermal (`Ø38.0 mm` Disc + `403535` LiPo)** | Refined first-principles model | `< 50 °C` wearable skin limit & `< 45 °C` LiPo charge limit (`intent.md`) | **PASS WITH MANDATORY FW ENVELOPE (`si_audit.py` §5, [brief-f-usbc.md](../../brief-f-usbc.md) §8):** Natural convection + `ε = 0.9` radiation on `Ø38.0 mm` (`11.34 cm²`/face) gives **`θ_BA ≈ 32.4 °C/W` free-air** and **`49.5 °C/W` worn** (with rear `35 mm` LiPo). **Continuous wearable power is capped at `≤ 0.51 W` (`~100 mA` total LED avg, `T_worn ≤ 50 °C` @ `25 °C` amb)**; `1.26 W` (`300 mA` LEDs) is restricted to `≤ 15 s` bursts, LEDs blank/`< 5 mA` whenever `~CHG == 0` (`U5` `0.48–0.79 W` hardware-controlled with `~CE = GND`, keeping free-air CC charge `~41 °C < 45 °C`; swap `R4` to `4.3–4.7 kΩ` per [bringup-f-usbc.md](../../bringup-f-usbc.md) §5 if charging enclosed/warm), and `ADC4` enforces closed-loop `GCC` foldback at **`42 °C` (charging)** / **`47 °C` (discharging)**. |

---

## 2. Verbatim `si_audit.py` Output & Crosstalk Dispositions

```text
=== 1. USB 2.0 FULL-SPEED (12 Mbit/s) POINT-TO-POINT SI & IMPEDANCE ===
  /Power/USB_DP_C   : total_copper= 11.94 mm, 0 vias, layers=['B.Cu']
  /Power/USB_DM_C   : total_copper= 18.01 mm, 3 vias, layers=['B.Cu', 'In6.Cu']
  USB_DP            : total_copper= 14.95 mm, 0 vias, layers=['B.Cu']
  USB_DM            : total_copper= 13.52 mm, 0 vias, layers=['B.Cu']
  /MCU/USB_DP_MCU   : total_copper=  5.28 mm, 2 vias, layers=['In4.Cu']
  /MCU/USB_DM_MCU   : total_copper=  5.94 mm, 2 vias, layers=['B.Cu', 'In4.Cu']
  Orient. A (A6/A7) : DP=30.09 mm, DM=27.44 mm -> |skew|=2.64 mm (~17.5 ps), unmated DM stub=8.86 mm
  Orient. B (B6/B7) : DP=32.28 mm, DM=28.54 mm -> |skew|=3.74 mm (~24.7 ps), unmated DM stub=7.76 mm
  Pre-ESD F.Cu check: USB_DM_C on F.Cu = False (layers=['B.Cu', 'In6.Cu'])
  Impedance & termination: R14/R15 = 27 Ohm at U3; B.Cu Zdiff ~ 120-166 Ohm over h=0.262 mm (l=31-33 mm << l_crit=100 mm @ t_r>=4 ns)

=== 2. U7 (USBLC6-2P6) ESD GROUND-RETURN LOOP ===
  U7.2 GND via #1 at (102.470, 110.730): center-path=3.90 mm (dist to J1.S1 2.3x1.8mm pad=0.000 mm)
  U7.2 GND via #2 at (102.126, 110.639): center-path=4.06 mm (dist to J1.S1 2.3x1.8mm pad=0.216 mm)
  Y-network inductance: U7.2 -> J1.S1 shield L_shield ~ 1.09 nH; U7.2 -> In2.Cu GND (2x vias) L_eff ~ 1.39 nH
  Two-stage isolation: R14/R15 = 27 Ohm limits residual peak current into U3 clamp to ~2.4 A (<1 ns) @ 8 kV IEC 61000-4-2

=== 3. EXACT NODAL DC RESISTANCE & IR DROP (25 C / 60 C, incl. 0.15 mm via barrels) ===
  VBUS (J1->U5.13)        : R_25C= 3.90 mOhm, R_60C= 4.44 mOhm -> Vdrop= 2.22 mV @ 500 mA (dual-row USB500)
  VBAT (BT1.1->U5.2/3)    : R_25C=48.36 mOhm, R_60C=55.01 mOhm -> Vdrop=18.70 mV @ 340 mA (340 mA max cont; 2x 0.30/0.15 vias at BT1.1)
  BAT_N (BT1.2->U8.4/5)   : R_25C= 2.86 mOhm, R_60C= 3.25 mOhm -> Vdrop= 1.10 mV @ 340 mA (0-via 1 oz B.Cu)
  U8.1..3 -> In2.Cu GND   : R_25C= 0.98 mOhm, R_60C= 1.12 mOhm -> Vdrop= 0.38 mV @ 340 mA (dual GND vias into solid In2.Cu)

=== 4. FULL AGGRESSOR / VICTIM COUPLING AUDIT (spacing <= 0.45 mm, overlap >= 1.00 mm) ===
  Southern sector victim couplings (>=1.0 mm within 0.45 mm): 3
    /Driver 2 and matrix/CS2_13 (LED_PWM, In3.Cu) <-> Net-(U5-ISET) (ANALOG, In4.Cu): len=2.15 mm, min_d=0.000 mm, Y=[109.8,110.4]
    /Driver 2 and matrix/CS2_7 (LED_PWM, B.Cu) <-> Net-(U2-RSET) (ANALOG, B.Cu): len=1.01 mm, min_d=0.250 mm, Y=[109.9,110.8]
    I2C_SCL (I2C_1MHZ, In6.Cu) <-> Net-(U2-RSET) (ANALOG, B.Cu): len=1.37 mm, min_d=0.000 mm, Y=[109.6,110.8]
  Inherited Variant F northern/matrix couplings (>=1.0 mm within 0.45 mm): 49 total (top 8 by length):
    /Driver 3 and matrix/CS3_6 (LED_PWM, B.Cu) <-> /MCU/RUN (SIGNAL_RESET, In6.Cu): len=6.07 mm, min_d=0.000 mm, Y=[84.9,89.5]
    /Driver 2 and matrix/CS2_5 (LED_PWM, F.Cu) <-> VBAT_SENSE (ANALOG, In1.Cu): len=4.60 mm, min_d=0.000 mm, Y=[105.4,113.5]
    /MCU/SWDIO (LED_SCAN, In6.Cu) <-> /MCU/RUN (SIGNAL_RESET, B.Cu): len=4.26 mm, min_d=0.000 mm, Y=[84.3,89.5]
    /Driver 3 and matrix/CS3_9 (LED_PWM, B.Cu) <-> /MCU/RUN (SIGNAL_RESET, In6.Cu): len=4.07 mm, min_d=0.182 mm, Y=[86.0,89.0]
    /Driver 4 and matrix/SW4_4 (LED_SCAN, In6.Cu) <-> /MCU/RUN (SIGNAL_RESET, B.Cu): len=3.49 mm, min_d=0.000 mm, Y=[84.7,87.9]
    /Driver 2 and matrix/CS2_6 (LED_PWM, F.Cu) <-> VBAT_SENSE (ANALOG, In1.Cu): len=3.43 mm, min_d=0.000 mm, Y=[104.6,111.5]
    /Driver 4 and matrix/CS4_12 (LED_PWM, In4.Cu) <-> /MCU/LIGHT (ANALOG, In3.Cu): len=3.36 mm, min_d=0.000 mm, Y=[86.6,88.9]
    /Driver 4 and matrix/CS4_12 (LED_PWM, In3.Cu) <-> /MCU/LIGHT (ANALOG, In3.Cu): len=3.25 mm, min_d=0.191 mm, Y=[88.4,91.8]

=== 5. WHOLE-BOARD & CHARGER THERMAL ANALYSIS (O38.0 mm Disc + 403535 LiPo) ===
  Disc area/face = 11.34 cm^2; h_conv=7.6 + h_rad=6.0 = 13.6 W/(m^2*K)
  Whole-board theta_BA: free-air = 32.4 C/W, worn (w/ rear 35 mm LiPo) = 49.5 C/W
  Max continuous wearable power (<50 C @ 25 C amb): P_cont,max = 0.51 W (~100 mA avg total LED current)
  Burst 1.26 W (300 mA LEDs) steady-state if unthrottled: 65.8 C free-air / 87.3 C worn -> requires ADC4 closed-loop GCC foldback (42 C charge / 47 C wear)
```

### Quantitative Dispositions of Aggressor / Victim Couplings ([decisions.md](../../decisions.md))
1. **`Net-(U5-ISET)` (`R4 = 3.0 kΩ`) ↔ `CS2_13` (`2.15 mm` across `170 µm` core):** `C_m ≈ 0.16 pF`, `τ = R4·C_node ≈ 9 ns < t_r ≈ 25 ns` -> `I_inj ≈ 22 µA` for `25 ns` every `40 µs` (`0.005%` average charge-current error — negligible).
2. **`Net-(U2-RSET)` (`R33 = 30 kΩ`) ↔ `I2C_SCL` (`1.37 mm` broadside) & `CS2_7` (`1.01 mm` at `0.25 mm` gap):** Inherited from Variant F (`U2`/`R33` untouched). `C_m ≈ 0.14 pF` injects `< 5 ns` `-0.22 V` impulses only during brief `I2C` register-write edges (`0%` duty during static display; `IS31FL3745` reference loop recovers in nanoseconds with zero perceptible brightness shift).
3. **Inherited northern `/MCU/RUN` (`31.89 mm` to `TP5`) ↔ `CS3_6` / `SW4_4` / `CS3_9`:** Worst-case simultaneous LED edge droop `ΔV_RUN ≈ -0.23 to -0.38 V` stays **`> 1.9 V` above `RP2350 VIL(max) = 0.99 V`** (`-2.31 V` droop needed); `TP5` sits under `0.05 mm` Kapton tape + `35 mm` LiPo in worn assembly so finger ESD cannot strike `TP5`.
4. **Inherited `VBAT_SENSE` (`C7 = 100 nF`, `31.8 Hz` RC) & `/MCU/LIGHT` (`C70 = 100 nF`):** Downstream trace inductance (`~18–32 nH` to `ADC0`/`ADC1`) allows `≤ 37 mV` `< 5 ns` damped edge spikes with **`0.0 mV` DC shift** under multi-sample firmware ADC averaging.

---

## 3. Independent Fresh-Context Review History (`agy` `gemini-4-argon-high`)

### Round 1 Review Summary & Dispositions
- **`MAJOR-1` (`U7.2` single `GND` via & `/Power/USB_DM_C` `F.Cu` excursion):** **FIXED** — moved `USB_DM_C`'s `1.10 mm` `F.Cu` segment to `In6.Cu` (`0` `F.Cu` USB copper) and added a **2nd parallel `GND` via** `(102.470, 110.730)` inside `J1.S1` NW (`L_shield ≈ 1.09 nH`, `L_eff ≈ 1.39 nH`).
- **`MAJOR-2` & `MAJOR-3` (`si_audit.py` missing `SWx_y`/`CSx_y`/`I2C` aggressors, `U2-RSET`, northern `/MCU/RUN` & `Y1` couplings):** **SCRIPT FIXED + NORTHERN COPPER JUSTIFIED in [decisions.md](../../decisions.md)** — rewrote [si_audit.py](../../../scripts/variant_fusbc/si_audit.py) §4 with Shapely `unary_union` across all `SW*`, `CS*`, `I2C`, `QSPI`, `USB`, `VREG_LX`, and `CLOCK` nets without angle filtering, and quantitatively dispositioned the inherited Variant F northern couplings without ripping up locked northern Variant F copper.
- **`MAJOR-4` (Whole-board `θ_BA` `1.26 W` steady-state vs `< 50 °C` wear / `< 45 °C` charge):** **FIXED** in `si_audit.py` §5, [brief-f-usbc.md](../../brief-f-usbc.md) §8, [bringup-f-usbc.md](../../bringup-f-usbc.md) §3.4, and [decisions.md](../../decisions.md) (`≤ 0.51 W` continuous wearable ceiling, `1.26 W` burst only, LEDs blanked on `~CHG == 0`, `ADC4` foldback at `42 °C` charge / `47 °C` wear).
- **`MINOR-1..4` (Point-to-point USB skew vs Steiner sum, `R14/R15 = 27 Ω`, `VREG_LX` `In3.Cu` feed, `U8` 2nd `GND` via, Gauss-Seidel nodal IR drop incl. `0.15 mm` via barrels, `XB9901A` `150 mV` `R_DS(on)` note):** **ALL FIXED** in `round-pendant.kicad_pcb`, `si_audit.py`, and this gate file.

### Round 2 Re-Review (`agy` `gemini-4-argon-high`)
- **Verdict:** **`Gate 8 Verdict: PASS (0 BLOCKER, 0 MAJOR, 3 MINOR, 2 NOTE)`** (`review_r2_phase8.txt`).
- **Summary & Minor Refinements:** Independently verified USB 2.0 FS point-to-point skew (`2.19 mm ≈ 14 ps` Orient. A, `3.39 mm ≈ 22 ps` Orient. B, `< 0.03%` UI) and unmated stubs (`8.86 / 7.76 mm`), `0` `F.Cu` USB tracks, `0` legal `0.25/0.15 mm` `GND` via pockets within `1.91 mm` of `U7.2`, inherited northern crosstalk limits, and whole-board `θ_BA = 32.4 °C/W` free-air / `49.5 °C/W` worn (`≤ 0.51 W` continuous worn cap). Noted `MINOR-1..3` in §1 above (`L_eff ≈ 2.10 nH` over `In2.Cu GND` giving `I_U3,pk ≈ 3.71 A` within `RP2350` CDM & `0402` single-pulse limits; exact 1D-barrel nodal values `VBUS = 5.64 mΩ`, `VBAT = 60.48 mΩ`, `U8->In2 = 3.04 mΩ`; and free-air USB charging vs `R4 = 4.3–4.7 kΩ` when enclosed since `U5.~CE = GND`).
