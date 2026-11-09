# Stackup and design rules: Sunflower `s2-110-usbc` (4-layer)

Phase 5 stackup and constraint specification for [sunflower.kicad_pcb](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/sunflower.kicad_pcb), [sunflower.kicad_pro](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/sunflower.kicad_pro), and [sunflower.kicad_dru](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/sunflower.kicad_dru).

## 1. Stackup (`JLC04161H-7628`, `1.6 mm` 4-layer)
- **Fabricator & stackup code:** JLCPCB standard 4-layer stackup **`JLC04161H-7628`** (`1.6 mm ± 10%` finished thickness, `1 oz` outer / `0.5 oz` inner copper, 1-ply `7628` prepreg outer dielectrics).
- **Source & date:** JLCPCB PCB capabilities & controlled-impedance stackup documentation (`https://jlcpcb.com/capabilities/pcb-capabilities` and `https://jlcpcb.com/impedance`), verified against project rules `2026-11-06` / audited `2026-11-08`.
- **Surface finish & solder mask:** `.kicad_pcb` records `(copper_finish "HAL SnPb")` (**ENIG `1U"` recommended at order time** for RoHS compliance and flat coplanarity across `110× 1615` `F.Cu` LEDs and `0.4 mm`-pitch `B.Cu` QFNs), **standard green LPI solder mask** (`0.01 mm` nominal over copper; green LPI supports `0.08–0.10 mm` dams between `0.20 mm`-gap `0.4 mm`-pitch QFN pads, whereas matte/colored masks require `0.135–0.15 mm`), tented vias (`solder_mask_to_copper_clearance = 0.0 mm`).
- **Impedance control flag:** `(dielectric_constraints no)` — standard non-impedance-controlled 4-layer pool pricing (`see §2`).

| Layer | Type / Material | Finished Thickness (mm) | $\varepsilon_r$ (`.kicad_pcb` / JLC 7628 nom.) | Role on `s2-110-usbc` (`Rev S3C` as-built) |
|---|---|---:|---:|---|
| `F.SilkS` | White LPI legend | — | — | Clipped Voronoi sunflower seed web + rim circle (`0.153 mm` stroke) |
| `F.Mask` | Top solder mask | `0.0100` | — | Opens LED & `Q2` pads only; all `637` vias tented |
| **`F.Cu` (L1)** | **Outer copper (`1 oz`)** | **`0.0350`** | — | `D1..D110` RGB LEDs, `Q2` light sensor, radial `CS` cathode triplets & outer `SW` arcs (`+1` `USB_DP`/`USB_DP_C` detour) |
| Dielectric 1 | Prepreg (`1× 7628` FR-4) | `0.2104` | `4.4` / `4.6` ($\tan\delta = 0.02$) | Outer dielectric (`F.Cu` to `In1.Cu` solid `GND`) |
| **`In1.Cu` (L2)** | **Inner copper (`0.5 oz`)** | **`0.0152`** | — | **Solid `GND` plane** (`928.8 mm²`, `1` piece; cut by `5.4 mm²` `LX cutout L2` — see note below) |
| Dielectric 2 | Core (FR-4) | `1.0650` | `4.6` ($\tan\delta = 0.02$) | Central structural core (`In1.Cu` to `In2.Cu`) |
| **`In2.Cu` (L3)** | **Inner copper (`0.5 oz`)** | **`0.0152`** | — | Circumferential `SW` scan arcs, cross-wedge `CS` jumps, `VSYS`/`+3V3`/`VBAT`/`BAT_N` trunks, `I2C0`, East `+1V1` spoke |
| Dielectric 3 | Prepreg (`1× 7628` FR-4) | `0.2104` | `4.4` / `4.6` ($\tan\delta = 0.02$) | Outer dielectric (`B.Cu` to `In2.Cu`) |
| **`B.Cu` (L4)** | **Outer copper (`1 oz`)** | **`0.0350`** | — | All ICs (`U1..U9`), `J1`, `BT1`, `SW1/2`, passives, test pads, `RP2350` regulator pours, solid `GND` EPs |
| `B.Mask` | Bottom solder mask | `0.0100` | — | Opens `B.Cu` component & test pads; all `637` vias tented |
| **Total** | | **`1.6062 mm`** (`1.5862 mm` Cu+FR4 in `.kicad_pcb`) | | Within `1.6 mm ± 0.16 mm` JLCPCB tolerance |

> **Stackup reference-plane & `LX` cutout audit note (`Rev S3C` finding → `Rev S3D` fix):** On `s2-110-usbc`, all active ICs (`U1..U9`), `75 MHz` QSPI, `12 MHz` crystal `Y1`, buck inductor `L1`, and USB-C (`J1`/`U7`) sit on **`B.Cu` (L4)**, whose adjacent inner layer (`0.2104 mm` across `dielectric 3`) is **`In2.Cu` (L3)** — while **`In1.Cu` (L2)** is `1.2906 mm` away across the `1.065 mm` core (`0.2104 mm` under `F.Cu`). Putting `GND` on `In1.Cu` and `RuleArea 18` (`LX cutout L2`) on `In1.Cu` instead of `In2.Cu` leaves unshielded `In2.Cu` routing (`VSYS` and `+3V3` `ADC_AVDD`) `0.2104 mm` directly beneath `B.Cu` `VREG_LX`/`L1` and increases `B.Cu` return-via loop height `6.1×` (logged in Gate 5 `B1`/`B2` and Gate 7 `B3`; swap `GND` plane + `LX` cutout to `In2.Cu` in `Rev S3D`).

## 2. Impedance analysis (`DIFF_HS` & `SE_HS`)
[nets-sunflower-s2-110-usbc.csv](file:///home/sequoia/pcb/round-pendant/design/nets-sunflower-s2-110-usbc.csv) explicitly specifies uncontrolled Full-Speed USB (`uncontrolled FS (27R damped; ~134R diff)`) and short-run QSPI (`uncontrolled (<=13.85 mm; <10% l_crit)`), matching `(dielectric_constraints no)` (`decisions.md` 2026-11-04 relaxation 5). Analytical Kirschning–Jansen / Hammerstad microstrip values on `B.Cu` (`t = 0.035 mm`) over `h = 0.2104 mm` (`7628` prepreg, if `In2.Cu` is `GND` in `Rev S3D` or at local `In2.Cu` copper crossovers) vs `h = 1.2906 mm` (actual `In1.Cu` `GND`, $\varepsilon_{r,\text{eff}} \approx 4.57$) are:

| Class / Net | Routed Width / Gap | Ref `h = 0.2104 mm` (`7628`, $\varepsilon_r = 4.4 / 4.6$) + Reference `50 Ω` / `90 Ω` Recipe | Actual `Rev S3C` Ref `h = 1.2906 mm` (`In1.Cu` `GND`) | Actual Routed Length vs Electrical Rise-Time Knee |
|---|---|---|---|---|
| `DIFF_HS` (`USB_DP`, `USB_DM`, `*_C`, `*_MCU`) | `0.15 mm` / `0.15 mm` (`0.10 mm` pad necks) | $Z_0 \approx 73.5 / 72.1\ \Omega$, $Z_{\text{diff}} \approx 111.5 / 109.3\ \Omega$ (**`90 Ω` diff recipe at `h = 0.2104 mm`: `w ≈ 0.26–0.28 mm, s = 0.15 mm`** or `w ≈ 0.21 mm, s = 0.10 mm`) | $Z_{\text{diff}} \approx \mathbf{134\ \Omega}$ (`w ≈ 0.72–0.90 mm` needed for `90 Ω` over `1.29 mm`) | Total `J1 → U7 → R14/15 → U3` copper is **`34.55 mm` (`DP`, `5` vias: `15.94 + 16.05 + 2.56 mm`)** and **`35.87 mm` (`DM`, `6` vias: `20.27 + 13.05 + 2.56 mm`)**, true flight-time skew **`25.4 ps`** (`B.Cu`/`F.Cu` vs `B.Cu`/`In2.Cu`). USB 2.0 Full Speed (`12 Mbit/s`, $t_r = 4\text{–}20\text{ ns}$, $l_{\text{crit}} \approx 308\text{ mm}$ at `4 ns`): `35.9 mm` is **`11.6%` of $l_{\text{crit}}$** (`27 Ω` `R14/R15` at `U3` damp reflections). |
| `SE_HS` (`QSPI_SCLK`, `QSPI_SS`, `QSPI_SD0..3`) | `0.10 mm` | $Z_0 \approx 88 / 86\ \Omega$ (**`50 Ω` SE recipe at `h = 0.2104 mm`: `w ≈ 0.36–0.37 mm`**) | $Z_0 \approx \mathbf{150\ \Omega}$ (`w ≈ 2.34 mm` needed for `50 Ω` over `1.29 mm`) | Routed lengths **`5.51–13.85 mm`** (`SCLK = 6.66 mm`, `2` vias each / `4` on `SD2`), well under the `25.0 mm` `.kicad_dru` ceiling (`< 95 ps` flight time, `< 10%` of `115–150 mm` $l_{\text{crit}}$ at `1.5–2 ns` edges). |

## 3. JLCPCB 4-layer fabrication limits vs board minimums (`sunflower.kicad_pro`)

| Parameter | JLCPCB 4L Capability (`1 oz` outer / `0.5 oz` inner, `2026-11`) | Board Constraint (`sunflower.kicad_pro`) | Margin & Audit Note |
|---|---|---|---|
| Min track width | `0.09 mm` (`3.5 mil` 4L+ standard) | **`0.10 mm`** (`min_track_width`) | `+11.1%` (`+0.01 mm`) over JLC 4L floor; required for `0.4 mm`-pitch `QFN-40`/`QFN-60` and spiral channels |
| Min copper-to-copper clearance | `0.09 mm` (`3.5 mil` 4L+ standard) | **`0.10 mm`** (`min_clearance`) | `+11.1%` (`+0.01 mm`) over JLC 4L floor (`zones` explicit `0.20 mm` plane, `0.09 mm` `U3` ring/band) |
| Min connection / neck width | — (DRC topological check) | **`0.09 mm`** (`min_connection`) | `0%` over `0.09 mm` fab floor; prevents partial-rip-up narrow necks (`decisions.md` 2026-11-05) |
| Min through-via (`pad / drill`) | `0.25 / 0.15 mm` (4L+ no-surcharge floor; `0.05 mm` annular) | **`0.30 / 0.15 mm`** (`0.075 mm` annular ring; `0.35 / 0.15` power) | `+20%` pad Ø / `+50%` actual annular ring (`min_via_annular_width` rule floor left at `0.05 mm`, `0%`) |
| Via-in-pad (VIPPO / POFV) | Paid option on 4L unless avoided | **Disallowed outside 4 EPs** (`no via hole in an SMD pad` `.kicad_dru`) | `U2.41`'s `1` via sits in the paste-free cross channel; **however, `U5.17`'s `2` vias and `U3.61`'s `1` via clip `B.Paste` apertures without VIPPO, and `U1.41` has `0` in-pad vias** (Gate 5 `M2` / Gate 7 `B5`) |
| Min drill-to-drill (`hole_to_hole`) | `0.20 mm` same-net via (`0.254 mm` diff-net via, `0.50 mm` PTH) | **`0.20 mm`** (`min_hole_to_hole`) | `0%` on same-net via floor (actual min diff-net via spacing on board passes JLC DFM) |
| Min drill-to-copper (`hole_clearance`) | `0.20 mm` inner/outer | **`0.20 mm`** (`min_hole_clearance`) | `0%` margin (`= JLC` floor) |
| Min plated slot width | `0.50 mm` (`J1` shell legs are `0.60 × 1.50 mm` / `0.60 × 1.80 mm`) | `min_through_hole_diameter = 0.15 mm` | `J1` slots `0.60 mm ≥ 0.50 mm` JLC slot floor (`min_through_hole_diameter` should be raised to `0.20 mm` for PTH pins in `Rev S3D`) |
| Min copper-to-board-edge | `0.20 mm` routed outline | **`0.25 mm`** (`min_copper_edge_clearance`) | `+25%` (`+0.05 mm`) margin; tightest pad on board (`SW1`/`SW2`) is `0.282 mm` |
| Solder mask dam / clearance | `0.038 mm` expansion, `0.08–0.10 mm` green LPI dam | `solder_mask_to_copper_clearance = 0.0 mm` (`solder_mask_min_width` unset) | `0.40 mm` QFN pitch keeps `0.20 mm` copper gap (set `solder_mask_min_width = 0.10 mm` in `Rev S3D`) |
| Silkscreen min width / text height | `0.15 mm` line, `0.80 mm` height | `min_text_height = 0.80 mm`, `min_text_thickness = 0.15 mm`, `min_silk_clearance = 0.15 mm` | Front seed web uses `0.153 mm` stroke (`≥ 0.15 mm` clear of pads); note `.kicad_pro` defaults `silk_line_width = 0.1` should be `0.15` |

*(Note: `min_microvia_diameter = 0.2` / `min_microvia_drill = 0.1` in `.kicad_pro` are unused KiCad defaults; `0` microvias exist on the board — add `(constraint disallow microvia buried_via)` in `Rev S3D`.)*

## 4. Net classes (`sunflower.kicad_pro` vs `design/nets-sunflower-s2-110-usbc.csv`)

All `108` net rows in [nets-sunflower-s2-110-usbc.csv](file:///home/sequoia/pcb/round-pendant/design/nets-sunflower-s2-110-usbc.csv) map via `108` `netclass_patterns` in [sunflower.kicad_pro](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/sunflower.kicad_pro) (`0` nets left in `Default` inside `pcbnew`):

| Net Class | Track Width (mm) | Clearance (mm) | Via `Ø / Drill` (mm) | Diff `W / Gap` (mm) | Assigned Nets & Engineering Source |
|---|---:|---:|---:|---:|---|
| `SIGNAL` | `0.10` | `0.10` | `0.30 / 0.15` | — | `30` `CS` sinks (`13.33 mA` pk, `11.8 mA` trunk avg), `I2C0`/`I2C1`, `CC1/2` (`5.5 V`), `SWD`, `UART1`, `BTN`, `RUN`, `CHG`, `PGOOD`, `BOARD_ID0`, `GPIO29_TP`, `LIGHT_PWR` |
| `SW_SCAN` | `0.10` | `0.10` | `0.30 / 0.15` | — | `22` `SW1_1..11` & `SW2_1..11` scan anodes (`200 mA` peak across `15` `CS` × `255/3168` duty = `16.1 mA` avg / `56.8 mA` RMS; `0.10 mm` fits spiral channels, `decisions.md` 2026-11-03) |
| `ANALOG` | `0.10` | `0.10` | `0.30 / 0.15` | — | `LIGHT`, `VBAT_SENSE`, `VREG_AVDD`, `U1/U2 ISET`, `U5 ILIM/ISET/TS`, `Net-(U8-VDD)` |
| `SE_HS` | `0.10` | `0.10` | `0.30 / 0.15` | — | `6` `QSPI_*` nets (`≤ 25 mm` length rule in `.kicad_dru`) |
| `CLOCK` | `0.15` | `0.15` | `0.30 / 0.15` | — | `U3-XIN`, `U3-XOUT`, `Net-(C24-Pad1)` (`0.15 mm` guard clearance, `≤ 11 mm`, `0` vias in `.kicad_dru`) |
| `DIFF_HS` | `0.15` | `0.15` | `0.30 / 0.15` | `0.15 / 0.15` | `6` `USB_DP`/`USB_DM` nets across `J1 → U7 → R14/15 → U3` |
| `POWER` | `0.20` | `0.10` | `0.30 / 0.15` | — | `VSYS` (DRU min `0.16 mm`; `0.25 mm` target in `Rev S3D`), `+3V3` (DRU min `0.15 mm`), `+1V1`, `GND` |
| `BATTERY` | `0.25` | `0.10` | `0.35 / 0.15` | — | `VBAT`, `/Power/BAT_N` (`0.35 A` capped / `1.0 A` peak, DRU min `0.25 mm`; raise clearance to `≥ 0.20 mm` in `Rev S3D`) |
| `USB_POWER` | `0.25` | `0.10` | `0.35 / 0.15` | — | `VBUS` (`0.50 A` `USB500` input limit, `1.5 A` peak, DRU min `0.25 mm`) |
| `SWITCH` | `0.40` | `0.12` | `0.35 / 0.15` | — | `/MCU/VREG_LX` (`0.10 A` avg / `0.45 A` peak switching node, `0.12 mm` clearance + `B.Cu` pour) |

> **Why `nets_check.py --rules` reports `32` `[netclass]` errors (`Default`):** `sunflower.kicad_pro` sets `"netclass_assignments": null` and defines all `108` mappings in `"netclass_patterns"`, which `pcbnew` applies to the PCB, whereas `kicad-cli sch export netlist` only emits schematic-attached netclass directives (present on the `76` `SIGNAL` nets — including `SW1_*`/`SW2_*` where `SIGNAL` `priority: 1` overrides `SW_SCAN` `priority: 3` at identical `0.10/0.10 mm` rules — and absent on the `32` non-`SIGNAL` nets). Populating `"netclass_assignments"` or schematic netclass directives in `Rev S3D` will resolve `nets_check.py --rules`.

## 5. Custom `.kicad_dru` rules and sources (`sunflower.kicad_dru`)

Custom rules in [sunflower.kicad_dru](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/sunflower.kicad_dru) (`48` rules total; add inline `# source` comments, diff-pair skew rules, and `BT1` Molex `53261-0271` `RESTRICTED AREA` keepout in `Rev S3D`):

1. **Per-rail minimum track widths:**
   - `VBUS >= 0.25 mm`, `VBAT >= 0.25 mm`, `/Power/BAT_N >= 0.25 mm` — current capacity + IR drop (`nets-sunflower-s2-110-usbc.csv`; restrict `VBUS` to outer `1 oz` `B.Cu` or widen inner trunks in `Rev S3D`).
   - `VSYS >= 0.16 mm` — lowered globally in `Rev S3C` to enter `0.20 mm`-wide `AW20198QNR` `PVCC`/`VCC` QFN-40 pads (scope `0.16 mm` strictly to QFN pad neckdowns and enforce `≥ 0.25–0.30 mm` on trunks in `Rev S3D`).
   - `+3V3 >= 0.15 mm` — `150 mA` logic rail (`chips/rp2350.md` `IOVDD` corner stub width).
   - `/Driver {1,2} and matrix/SW{1,2}_{1..11} >= 0.10 mm` — `22` scan anodes (`200 mA` pulsed, `16.1 mA` avg).
2. **High-speed / clock length & via ceilings:**
   - `/MCU/QSPI_{SCLK,SS,SD0..3}`: `length (max 25mm)` (`decisions.md` 2026-11-04 relaxation 4).
   - `Net-(U3-XIN)`, `Net-(U3-XOUT)`, `Net-(C24-Pad1)`: `length (max 11mm)` and `via_count (max 0)` (`rp2350.pdf` crystal layout + `decisions.md` 2026-11-04 relaxation 3).
3. **Solid exposed-pad & no-via-in-pad DFM rules:**
   - `U1/U2/U3/U5 solid EP foreign`: `disallow track via` for any net `!= 'GND'` (`decisions.md` 2026-11-04).
   - `no via hole in an SMD pad`: `physical_hole_clearance (min 0.1mm)` between any `Via` and any `SMD` pad other than `U1.41`, `U2.41`, `U3.61`, `U5.17` (`decisions.md` 2026-11-06; in `Rev S3D`, constrain EP vias strictly to paste-free cross channels).
4. **RP2350 reference regulator & ring protection (`chips/rp2350.md` & `rp2350.pdf` §6.3.8.1):**
   - `U3 ring foreign vias` (`!= '+1V1' && != 'GND'` — expand `RuleArea 2` from `±2.32 mm` to full `±2.85 mm` in `Rev S3D`), `U3 ring foreign tracks` (`!= '+3V3' && != '+1V1' && != 'GND'`).
   - `reg corner foreign`, `L1 window foreign`, and `vendor {+1V1, GND, /MCU/VREG_LX, +3V3} area foreign`.

## 6. DRC severities (`sunflower.kicad_pro` L60–L116, `57` keys)

- **Set to `"error"` (`43` checks):** `annular_width`, `clearance`, `connection_width`, `copper_edge_clearance`, `copper_sliver`, `courtyards_overlap`, `creepage`, `diff_pair_gap_out_of_range`, `diff_pair_uncoupled_length_too_long`, `drill_out_of_range`, `duplicate_footprints`, `extra_footprint`, `footprint`, `hole_clearance`, `hole_to_hole`, `holes_co_located`, `invalid_outline`, `isolated_copper`, `item_on_disabled_layer`, `items_not_allowed`, `length_out_of_range`, `malformed_courtyard`, `microvia_drill_out_of_range`, `missing_footprint`, `net_conflict`, `shorting_items`, `silk_over_copper`, `silk_overlap`, `skew_out_of_range`, `solder_mask_bridge`, `starved_thermal`, `text_on_edge_cuts`, `through_hole_pad_without_hole`, `too_many_vias`, `track_angle`, `track_dangling`, `track_segment_length`, `track_width`, `tracks_crossing`, `unconnected_items`, `unresolved_variable`, `via_dangling`, `zones_intersect`.
- **Left at `"warning"` (`8` checks — audited with `kicad-cli pcb drc --severity-all` = `0` warnings on `sunflower.kicad_pcb`; promote to `"error"` in `Rev S3D`):** `footprint_symbol_mismatch`, `lib_footprint_issues`, `mirrored_text_on_front_layer`, `nonmirrored_text_on_back_layer`, `padstack`, `silk_edge_clearance`, `text_height`, `text_thickness`.
- **Set to `"ignore"` (`6` checks — replace global ignores with targeted exclusions in `Rev S3D`):** `lib_footprint_mismatch`, `footprint_filters_mismatch` (project-local `lib/round_pendant.pretty`), `footprint_type_mismatch` (`TP*` and `NT1` SMD features marked `exclude_from_bom`), `missing_courtyard` (`NT1` net-tie), `npth_inside_courtyard`, `pth_inside_courtyard` (`J1` USB-C shield PTH slots + NPTH pegs inside its own courtyard).
