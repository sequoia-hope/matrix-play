# Stackup and design rules: parallelogram-p2-132-usb6

Source: JLCPCB 4-layer controlled-impedance stackup & PCB capabilities page (<https://jlcpcb.com/capabilities/pcb-capabilities>), verified 2026-11-02 / 2026-11-08.
Stackup code: **JLC04161H-7628** (`1.6 mm` nominal / `1.5862 mm` bare copper-dielectric height, `1 oz` outer / `0.5 oz` inner, `0.2104 mm` `7628` prepreg `Er = 4.4`, `1.065 mm` FR-4 core `Er = 4.6`). Mandatory order finish & via structure: **`ENIG 1U"`** (`(copper_finish "ENIG")` encoded in `stage_stack`, flat pads for `0.40 mm`-pitch QFNs, `1.0 × 1.0 mm` X2-SON `U6`, & `2.0 × 2.0 mm` LGA-12 `U9`, `0.08–0.10 mm` green LPI solder-mask dam capability, RoHS lead-free wearable contact) + **`POFV = Yes` (JLCPCB 4-layer epoxy-filled & copper-capped via-in-pad, VIPPO)** per `design/study/parallelogram/README.md` §2 so all `118` `0.30/0.15 mm` perimeter/LED via-in-pads are plated flat (`0` open barrels, `0` solder wicking, `0` `F.SilkS` web dimples; exposed thermal pads `U3=5`, `U5=2`, `U1=5`, `U2=5` additionally sit `100%` on solder-paste crossbars with `0` paste overlap). Standard green LPI solder mask (`Er = 3.8`).

## 1. Physical 4-layer stackup (`JLC04161H-7628`, encoded in `pcb_gen.py` `stage_stack`)

| KiCad Layer | Copper weight / thickness | Dielectric below | `Er` | Role |
|---|---|---|---|---|
| `F.Cu` (L1) | `1 oz` finished (`0.035 mm`) | `0.2104 mm` (`7628` prepreg) | `4.4` | `132 × XL-1615RGBC-RF` LED pads, `Q2` phototransistor, `CS` vertical column buses, inter-column escape tracks |
| `In1.Cu` (L2) | `0.5 oz` (`0.0152 mm`) | `1.065 mm` FR-4 core | `4.6` | **Unbroken whole-board `GND` reference plane (`plane GND`, `1` piece)**; `5.43 mm²` `LX cutout L2` under `VREG_LX` (`decisions.md` 2026-11-07) |
| `In2.Cu` (L3) | `0.5 oz` (`0.0152 mm`) | `0.2104 mm` (`7628` prepreg) | `4.4` | Horizontal `SW` matrix scan lines, `VSYS` / `+3V3` / `+1V1` distribution, MCU GPIO & I2C escape; **`LX cutout L3` (`no_tracks`, `no_pour`) blocks copper `0.21 mm` directly beneath `B.Cu` `VREG_LX`/`L1.2`** |
| `B.Cu` (L4) | `1 oz` finished (`0.035 mm`) | — | — | All active ICs (`U1..U9`), `J1`, `BT1`, `SW1..SW6`, passives, `0`-via `12 MHz` crystal, `1`-piece RP2350 `+1V1` ring & `1`-piece `+3V3` band |

## 2. 2D field-solver impedance & electrical-length analysis

`design/nets-parallelogram-p2-132-usb6.csv` classifies USB 2.0 Full-Speed nets (`/Power/USB_DP_C`, `/Power/USB_DM_C`, `USB_DP`, `USB_DM`, `/MCU/USB_DP_MCU`, `/MCU/USB_DM_MCU`) as `DIFF_HS` (`90 diff`) and QSPI (`<= 25 mm`) as `SE_HS`.
- **2D Laplace / Kirschning–Jansen impedance on `JLC04161H-7628` (`t = 0.035 mm`, `10 µm` LPI mask `Er = 3.8`):**
  - Over `h = 0.2104 mm` (`F.Cu` → `In1.Cu` `GND`, `Er = 4.4`): `90 Ω` differential requires `w ≈ 0.30 mm, s = 0.15 mm` (`90.5 Ω`); `50 Ω` single-ended requires `w ≈ 0.36 mm`; routed `0.15 / 0.15 mm` gives `Zdiff = 118.5 Ω` (`Z0 = 78.2 Ω`, `v_p = 180.9 mm/ns`).
  - Over `h = 1.2906 mm` (`B.Cu` → `In1.Cu` `GND`, since `In2.Cu` carries horizontal `SW` matrix buses rather than a second `GND` plane): `0.15 / 0.15 mm` gives `Zdiff = 135.3 Ω` (`v_p = 188.0 mm/ns`), and `0.10 mm` `QSPI` gives `Z0 = 158.3 Ω` (`90 Ω` diff across `h = 1.29 mm` would require `w > 0.65 mm`, incompatible with `0.40 mm`-pitch QFN/USBLC6 escape).
- **Electrical length vs rise time (why lumped-element length bounds govern):**
  - RP2350 USB is **USB 2.0 Full Speed (`12 Mb/s`, `t_r = 4–20 ns` per USB 2.0 §7.1.2.2)** terminated by external `27 Ω` series resistors **`R14` / `R15`**. At `t_r = 4 ns` (`v_p = 188 mm/ns`), `l_crit = t_r · v_p / 6 = 125 mm` (`107 mm` conservative at `160 mm/ns`), whereas `.kicad_dru` bounds `/Power/USB_D*_C <= 35 mm`, `USB_D* <= 35 mm`, and `/MCU/USB_D*_MCU <= 6 mm` (`0` vias) — actual end-to-end routed chain `J1 -> U7 -> R14/R15 -> U3` is **`< 21 mm`** (`< 0.17 × l_crit`, skew `< 2.5 mm ≈ 13 ps`).
  - QSPI (`<= 25 mm` enforced in `.kicad_dru`; actual routed `9.2–16.8 mm` across `U3`–`U4`, `< 25 mm` cap) is `< 0.37 × l_crit` (`l_crit ≈ 45 mm` at `t_r = 1.5 ns`; `PADS_QSPI.SLEWFAST = 0` configured in firmware). Standard non-impedance-surcharged 4L fabrication is therefore used, backed by explicit `.kicad_dru` length caps and Phase 8 SI/PDN verification (`design/sim/p2-132-usb6/results.json`).

## 3. Creepage / HV clearance & JLCPCB 4-layer fab constraints (`parallelogram.kicad_pro`)

- **HV creepage:** `N/A` — peak voltage anywhere on the board is `5.5 V` (`VBUS`), worst-case fault differential `9.8 V` (`VBUS` to `/Power/BAT_N`). IPC-2221B Table 6-1 (`0–15 V`) requires `0.05 mm` internal (`B1`) and `0.10 mm` uncoated external (`B2`), met by `min_clearance = 0.10 mm`.

| Constraint | JLCPCB 4L capability (`1 oz` / `0.5 oz`) | Set in `parallelogram.kicad_pro` / `.kicad_dru` | Margin / Notes |
|---|---|---|---|
| Min track width / clearance | `0.09 mm` / `0.09 mm` (`3.5 mil`) | `0.10 mm` / `0.10 mm` (`min_connection = 0.09 mm`) | `+0.01 mm` margin (`0.40 mm` QFN escape) |
| Min via diameter / drill | `0.25 mm` / `0.15 mm` (`0.05 mm` ring) | `0.30 mm` / `0.15 mm` (`0.075 mm` actual ring; `disallow microvia buried_via` in `.kicad_dru`) | `+0.05 mm` pad margin; **`POFV = Yes` (epoxy-filled & copper-capped)** plates all `118` SMD via-in-pads flat (`0` `B.Paste` overlap on `U1/U2/U3/U5` EPs; `0.15 mm` drill includes JLC 4-wire Kelvin test) |
| Min hole-to-hole / hole-to-copper | `0.20 mm` / `0.20 mm` | `0.20 mm` / `0.20 mm` | Exact JLC 4L spec (`J1` NPTH holes >= `0.294 mm` from `F.Cu` pads) |
| Plated slots / castellations | `0.50 mm` min slot; castellations N/A | `min_groove_width = 0.0` (no slots or castellations on board) | `0` slots (`J1` uses round `Ø 0.65 mm` NPTH drills) |
| Min copper-to-edge (routed) | `0.30 mm` recommended (`0.20 mm` abs) | `0.30 mm` (`min_copper_edge_clearance = 0.30`) | `plane GND` inset `0.30 mm`; `SW1/2/5/6` pads at `0.40 mm` |
| Silkscreen min height / stroke / clr | `0.80 mm` / `0.15 mm` / `0.15 mm` | `0.80 mm` / `0.15 mm` / `0.15 mm` (`defaults.silk_text_thickness = 0.15`) | Exact JLC spec & `design/checks.toml` |
| Solder mask clearance / min dam | `0.0 mm` expansion; `0.08–0.10 mm` dam (green LPI + ENIG) | `solder_mask_to_copper_clearance = 0.0 mm`, `solder_mask_min_width = 0.0 mm` | `0.40 mm`-pitch QFNs (`0.20 mm` orthogonal gap, `0.141 mm` corner gap) & `U9` (`0.150 mm` gap) retain intact green-LPI dams (`0` `solder_mask_bridge` DRC errors) |

## 4. Synchronized net classes (`parallelogram.kicad_pro` & `nets-parallelogram-p2-132-usb6.csv`)

Every one of the `118` rows in `design/nets-parallelogram-p2-132-usb6.csv` maps `1:1` to both `netclass_assignments` and `netclass_patterns` in `parallelogram.kicad_pro` (`0` mismatches in `pcbnew`/DRC; note `nets_check.py --rules` reads `kicad-cli sch export netlist` which prints `Default` for hierarchical sheets per `design/gates/phase5.md` line 9):

| Net Class | Track (mm) | Clearance (mm) | Via (mm) | Diff W/Gap (mm) | Nets (`118` total) |
|---|---|---|---|---|---|
| `SIGNAL` / `Default` | `0.10` | `0.10` | `0.30 / 0.15` | `0.15 / 0.15` | GPIO, I2C, `CS` sinks (`13.3 mA` pk), `SW` scan rows (`68.2 mA` RMS), `USER_A..D` (`SW3..SW6`, `R44..R47`, `C71..C72`) |
| `POWER` | `0.20` | `0.10` | `0.30 / 0.15` | `0.15 / 0.15` | `GND` (`0.50 A` max per pad stub; `1.0/2.0 A` in `In1.Cu` plane), `VSYS`, `+3V3`, `+1V1` |
| `POWER_HI` | `0.25` | `0.10` | `0.35 / 0.15` | `0.15 / 0.15` | `VBAT`, `/Power/BAT_N` (`0.34 A` cont / `1.0 A` pk), `VBUS` (`0.50 A`) |
| `ANALOG` | `0.10` | `0.10` | `0.30 / 0.15` | `0.15 / 0.15` | `VBAT_SENSE`, `/MCU/LIGHT`, `/MCU/VREG_AVDD`, `ISET`/`ILIM`/`TS` nodes |
| `CLOCK` | `0.15` | `0.15` | `0.30 / 0.15` | `0.15 / 0.15` | `12 MHz` crystal (`Net-(U3-XIN)`, `Net-(U3-XOUT)`, `Net-(C24-Pad1)`) |
| `SE_HS` | `0.10` | `0.10` | `0.30 / 0.15` | `0.15 / 0.15` | `/MCU/QSPI_SCLK`, `/MCU/QSPI_SS`, `/MCU/QSPI_SD0..3` |
| `DIFF_HS` | `0.15` | `0.15` | `0.30 / 0.15` | `0.15 / 0.15` | `/Power/USB_D*_C`, `USB_D*`, `/MCU/USB_D*_MCU` |
| `SWITCH` | `0.40` | `0.12` | `0.35 / 0.15` | `0.15 / 0.15` | `/MCU/VREG_LX` buck switch pour |

*(Note on `0.5 oz` `In2.Cu` & zone connections: `VSYS` uses `0.20 mm` `POWER` nominal with a `0.16 mm` `.kicad_dru` floor so traces enter `0.20 mm`-wide `AW20198` `PVCC`/`VCC` pads cleanly; exact routed `p2-132-usb6` `VSYS` nodal IR drop across `In2.Cu`/`B.Cu` is verified in `design/sim/p2-132-usb6/results.json` (`-60.6 mV` at `U6.4`, `-117.6 mV` at `U2.5`, `-117.8 mV` at `U1.5` at `300 mA` `intent.md` R19 LED budget + `25 mA` LDO). Zone pours follow `chips/rp2350.md` reference `FULL` connection on regulator/ring pours while `0402` passives outside regulator pours connect via `0.15–0.20 mm` necked traces to tented `GND` vias, preventing tombstoning.)*

## 5. Custom DRC rules (`parallelogram.kicad_dru`) & sources

1. **Per-net / per-class minimum widths (IPC-2152 & reference layout):** `VBUS >= 0.25 mm`, `VBAT >= 0.25 mm`, `/Power/BAT_N >= 0.25 mm`, `VSYS >= 0.16 mm`, `+3V3 >= 0.15 mm`, `CLOCK >= 0.15 mm`, `/MCU/USB_D*_MCU >= 0.15 mm`, `/Driver */SW* >= 0.10 mm`, plus `disallow microvia buried_via`.
2. **High-speed & clock length / via limits (`nets.csv` & `parts/rp2350-core.md`):**
   - `/MCU/QSPI_SCLK`, `/MCU/QSPI_SS`, `/MCU/QSPI_SD0..3`: `length <= 25 mm`.
   - `/Power/USB_DP_C`, `/Power/USB_DM_C`, `USB_DP`, `USB_DM`: `length <= 35 mm`; `/MCU/USB_DP_MCU`, `/MCU/USB_DM_MCU`: `length <= 6 mm` AND `via_count <= 0`.
   - `Net-(U3-XIN)`, `Net-(U3-XOUT)`, `Net-(C24-Pad1)`: `length <= 11 mm` AND `via_count <= 0` (`0` vias, pure `B.Cu`).
3. **Solid exposed-pad, unbroken `+3V3` band & RP2350 regulator keepouts (`chips/rp2350.md`, `parts/drivers-aw20198.md`, `parts/charger.md`):**
   - `U3 solid EP`, `U5 solid EP`, `U1 solid EP`, `U2 solid EP`: `disallow track via` for any net `!= 'GND'`.
   - `U3 ring vias` (`+1V1`/`GND`), **`U3 band` (`disallow track via` for `!= '+3V3'`, guaranteeing `1` unbroken `+3V3` band piece and outward `DVDD` cap escape per `chips/rp2350.md`)**, `U3 ring`, `reg corner`, `L1 window`, `vendor * area`.

## 6. DRC severities (`parallelogram.kicad_pro`)
`52` checks set to **`error`** (including `footprint_symbol_mismatch`, `lib_footprint_issues`, `missing_courtyard`, `silk_edge_clearance`, `text_height`, `text_thickness`, `mirrored_text_on_front_layer`, `nonmirrored_text_on_back_layer`, `padstack`, `net_conflict`, `connection_width`, `copper_sliver`, `isolated_copper`, `solder_mask_bridge`, `courtyards_overlap`); only `5` library-metadata/NPTH rules (`lib_footprint_mismatch`, `footprint_filters_mismatch`, `footprint_type_mismatch`, `npth_inside_courtyard`, `pth_inside_courtyard`) are `ignore` for project-local `round_pendant.pretty` footprints, and **`0` rules are left at `warning`**.
