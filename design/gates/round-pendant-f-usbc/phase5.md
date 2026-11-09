# Gate 5: stackup and design rules (`round-pendant-f-usbc`)

Status: **passed**
Parent gate cited for unchanged stackup & rules: [design/gates/phase5.md](../phase5.md), [design/stackup.md](../../stackup.md), and 8-layer upgrade + `f-usbc` dispositions in [design/decisions.md](../../decisions.md) (`2026-11-04`, `2026-11-08`).

---

## Checklist (`references/stackup-and-rules.md` §Gate checklist)

- [x] **`stackup.md` with source, date, dielectric thicknesses, `Er`, and JLCPCB 8-layer `1.0 mm` stackup code:** Updated in [design/stackup.md](../../stackup.md) (`https://jlcpcb.com/capabilities/pcb-capabilities`, `2026-11-08`, **`JLC08101H-1080`**, `Er = 4.1`, `0.9968 mm ≈ 1.00 mm` finished thickness: `2× 0.035 mm` `1 oz` outer Cu, `6× 0.0152 mm` `0.5 oz` inner Cu, `4× 0.0764 mm` `1080` prepreg, `3× 0.170 mm` core, `2× 0.010 mm` ENIG liquid photoimageable mask, epoxy-filled & capped POFV via-in-pad; `In2.Cu = plane GND`, `In5.Cu = plane VSYS + plane 3V3`, `In4.Cu` signal routing with `0` zones).
- [x] **Impedance widths & USB 2.0 Full-Speed (`12 Mbit/s`) regime documented:** On `JLC08101H-1080` (`Er = 4.1`), `DIFF_HS` (`w = 0.15 mm, s = 0.15 mm`) yields `Z_diff ≈ 108–122 Ω` (`166 Ω` uncoupled upper bound) on `B.Cu` over `In5.Cu` (`h = 0.2616 mm`) and `Z_diff ≈ 72.3 Ω` asymmetric stripline on `In4.Cu` (`0.0764 mm` to `In5.Cu`, `0.2616 mm` to `In2.Cu`). [design/nets-f-usbc.csv](../../nets-f-usbc.csv) records `"90 diff (nominal; FS lumped l<<l_crit)"` on all 6 USB rows: for USB 2.0 Full-Speed (`12 Mbit/s`, `t_r ≥ 4 ns`), `l_crit = t_r · v_p / 6 ≈ 100 mm`, while true point-to-point `J1 -> U7 -> R14/R15 (27 Ω) -> U3` length is **`30.09 / 27.44 mm`** (`Orient. A`) and **`32.28 / 28.54 mm`** (`Orient. B`) (`< 0.33 × l_crit`), and `QSPI` `U3 <-> U4` is `5.45–12.06 mm` (`< 25 mm` limit).
- [x] **Fab minimums entered as board constraints (`round-pendant.kicad_pro`):**
  - Min track width: `0.09 mm`; min clearance: `0.09 mm`
  - Standard through-via: `0.25 mm` pad / `0.15 mm` drill (`3× 0.20 / 0.10 mm` vias inherited inside `U3` `+3V3` band; `min_through_hole_diameter = 0.10 mm`, `min_via_diameter = 0.20 mm`, `min_via_annular_width = 0.05 mm`, subject to `status.json` `jlc-8l-quote`)
  - Hole-to-copper (`min_hole_clearance`) & hole-to-hole (`min_hole_to_hole`): **`0.200 mm`** (`In3.Cu` `CS5_16` nudged to **`0.304 mm`** from `J1` NPTH #1; min across all 8 layers = `0.201 mm`)
  - Copper-to-edge (`min_copper_edge_clearance`): **`0.200 mm`**
  - Solder mask clearance `0.00 mm` (`solder_mask_to_copper_clearance = 0.0`; JLCPCB ENIG min green mask dam = `0.10 mm`, recorded in `stackup.md`)
  - Silkscreen: `min_text_height = 0.80 mm`, **`min_text_thickness = 0.15 mm`**, `min_silk_clearance = 0.15 mm`, `(subtractmaskfromsilk yes)`
- [x] **Net classes in `design/nets-f-usbc.csv` & `round-pendant.kicad_pro` reconciled:** `185` schematic net rows in `nets-f-usbc.csv` (+ `27` `unconnected-(...)` single-pad nets = `212` PCB nets). Inherited Variant F refinements in `.kicad_pro` (`40× SW*` in `SW_SCAN` `0.10/0.09 mm`, `VBAT`/`BAT_N` in `BATTERY` `0.30/0.09 mm`, `VBUS` in `USB_POWER` `0.25/0.09 mm`) tighten routing defaults above `SIGNAL`/`POWER` `0.09 mm` and are documented in [stackup.md](../../stackup.md) and [decisions.md](../../decisions.md).
- [x] **Custom rules written in `round-pendant.kicad_dru` with sources:** Header updated to `design/nets-f-usbc.csv` & `design/brief-f-usbc.md`; enforces current-carrying track widths (`VBUS ≥ 0.25 mm`, `VSYS ≥ 0.20 mm` + `In5.Cu` plane, `VBAT`/`BAT_N ≥ 0.30 mm`, `+3V3 ≥ 0.20 mm`, `SW* ≥ 0.10 mm`), explicit USB length rules (`/Power/USB_DP_C` & `/Power/USB_DM_C ≤ 22 mm`, `USB_DP` & `USB_DM ≤ 25 mm`, `/MCU/USB_DP_MCU` & `/MCU/USB_DM_MCU ≤ 12 mm`), `QSPI_* ≤ 25 mm`, crystal nets (`Net-(U3-XIN)`, `Net-(U3-XOUT)`, `Net-(C24-Pad1)`) `≤ 11 mm` & `0` vias, and `RP2350 ring` / `L1` keepout rules. `BT1.1` (`VBAT`) now has **`2×` parallel `0.30/0.15 mm` vias** (`(100.018, 114.939)` & `(100.860, 115.700)`), and plane-cooled `0.30 mm` `In3.Cu` ampacity (`> 0.8 A` IPC-2152 vs `0.34 A` max continuous / `0.297 A` charge) is justified in [decisions.md](../../decisions.md).
- [x] **DRC severities verified & listed (`round-pendant.kicad_pro`):** Promoted `footprint_symbol_mismatch`, `text_height`, and `text_thickness` to **`"error"`** (`46` `"error"` severities total; full severity table in §1.C below).
- [x] **Strict DRC produces `0` board violations and `0` unconnected items:** `Found 0 violations`, `Found 0 unconnected items`, and only the **`2` inherited Variant E/F `U3` pin 42/43 `{slash}` unconnected pin-name parity strings** (explicitly named per task instructions rather than hidden; justified in `decisions.md`).

---

## 1. Verbatim Net-Class, Rule & DRC Check Outputs

### A. `verify_solid_ep_and_netclasses.py`
```text
  U3.61: solid pad area=11.56 mm², GND_vias=9, foreign_vias=0
  U5.17: solid pad area=2.89 mm², GND_vias=2, foreign_vias=0
  U1, U2, U10, U11, U12: 36 WLCSP balls each, 0 exposed ground pads
  U3 +1V1 B.Cu ring union: 2 piece(s) (RP2350 ring=1), total area=8.72 mm²
  Project netclasses checked (round-pendant.kicad_pro): 212 nets, 0 unexpected classes
PASS: 0 errors
```

### B. `nets_check.py --nets design/nets-f-usbc.csv --routed hw/round-pendant/f-usbc`
```text
nets_check: hw/round-pendant/f-usbc
  169 named nets in round-pendant.kicad_sch, 185 rows in nets-f-usbc.csv
  ...
  routed length (mm, track copper on the net; zones not counted) against nets.csv
    net                 routed  limit vias
    Net-(C24-Pad1)        1.56   11.0    0
    Net-(U3-XIN)          6.06   11.0    0
    Net-(U3-XOUT)         1.54   11.0    0
    USB_DM               13.52   25.0    0
    USB_DP               14.95   25.0    0

  PASS: 0 errors, 195 warnings
```
*(Exact routed copper lengths on hierarchical `/` nets verified in `si_audit.py` & `.kicad_dru`: `/Power/USB_DP_C = 11.94 mm ≤ 22 mm`, `/Power/USB_DM_C = 18.01 mm ≤ 22 mm`, `/MCU/USB_DP_MCU = 5.28 mm ≤ 12 mm`, `/MCU/USB_DM_MCU = 5.94 mm ≤ 12 mm`, `/MCU/QSPI_* = 5.45–12.06 mm ≤ 25 mm`. The `195` warnings match parent [gates/phase5.md](../phase5.md) line 9: KiCad 9 `kicad-cli sch export netlist` emits `Default` on hierarchical nets, and `0.09 mm` is the JLCPCB 8L fab floor required for `0.50 mm` WLCSP-36 escape channels.)*

### C. `.kicad_pro` `rule_severities` & Strict KiCad DRC (`drc_final.json`)
- **`"error"` (`46`):** `annular_width`, `clearance`, `connection_width`, `copper_edge_clearance`, `copper_sliver`, `courtyards_overlap`, `creepage`, `diff_pair_gap_out_of_range`, `diff_pair_uncoupled_length_too_long`, `drill_out_of_range`, `duplicate_footprints`, `extra_footprint`, `footprint`, `footprint_symbol_mismatch`, `hole_clearance`, `hole_to_hole`, `holes_co_located`, `invalid_outline`, `isolated_copper`, `item_on_disabled_layer`, `items_not_allowed`, `length_out_of_range`, `malformed_courtyard`, `microvia_drill_out_of_range`, `missing_footprint`, `net_conflict`, `shorting_items`, `silk_over_copper`, `silk_overlap`, `skew_out_of_range`, `solder_mask_bridge`, `starved_thermal`, `text_height`, `text_on_edge_cuts`, `text_thickness`, `through_hole_pad_without_hole`, `too_many_vias`, `track_angle`, `track_dangling`, `track_segment_length`, `track_width`, `tracks_crossing`, `unconnected_items`, `unresolved_variable`, `via_dangling`, `zones_intersect`.
- **`"warning"` (`5`, `0` triggered):** `lib_footprint_issues`, `mirrored_text_on_front_layer`, `nonmirrored_text_on_back_layer`, `padstack`, `silk_edge_clearance`.
- **`"ignore"` (`6`, intentional):** `footprint_filters_mismatch`, `footprint_type_mismatch`, `lib_footprint_mismatch`, `missing_courtyard` (`0/342` missing), `npth_inside_courtyard`, `pth_inside_courtyard`.

```text
Found 0 violations
Found 0 unconnected items
Found 2 schematic parity issues
DRC violations: 0 unconnected: 0 parity: 2
  - Pad net (unconnected-(U3-GPIO28/ADC2-Pad42)) doesn't match net given by schematic (unconnected-(U3-GPIO28{slash}ADC2-Pad42)).
  - Pad net (unconnected-(U3-GPIO29/ADC3-Pad43)) doesn't match net given by schematic (unconnected-(U3-GPIO29{slash}ADC3-Pad43)).
```

---

## 2. Independent Fresh-Context Review History (`agy` `gemini-4-argon-high`)

### Round 1 Review Summary & Dispositions
- **`B1` (`VBAT` single via at `BT1.1` & `0.30 mm` `In3.Cu` ampacity):** **FIXED + JUSTIFIED in [decisions.md](../../decisions.md)** — added a **2nd parallel `0.30/0.15 mm` `VBAT` via** at `(100.860, 115.700)` (`R_nodal = 48.36 mΩ @ 25 °C / 55.01 mΩ @ 60 °C`, `18.70 mV @ 340 mA`); widening `In3.Cu` beyond `0.30 mm` violates `0.200 mm` `hole_clearance` against adjacent matrix vias, while IPC-2152 internal conductor ampacity of `0.30 mm` `0.5 oz` copper cooled `0.076–0.170 mm` between solid `In2.Cu GND` and `In5.Cu VSYS` exceeds `0.80 A` (`> 2.3×` the `0.34 A` continuous wearable limit / `0.297 A` charge current).
- **`B2` (`2` `U3` pin 42/43 `{slash}` `schematic_parity` strings):** **DISPUTED in [decisions.md](../../decisions.md)** per explicit task instruction (*"0 errors, 0 warnings, 0 unconnected, except the two known U3 pin 42/43 `{slash}` name mismatches F already has; name them, don't hide them"*). Both pins (`GPIO28/ADC2`, `GPIO29/ADC3`) are unconnected `NC` pads inherited verbatim from Variant F.
- **`B3` & `m1` (Missing USB length rules & stale header in `.kicad_dru`, overstated severities in `phase5.md`):** **FIXED** — added explicit `22 / 25 / 12 mm` USB length rules with source comments and updated header in [round-pendant.kicad_dru](../../../hw/round-pendant/f-usbc/round-pendant.kicad_dru), and aligned `VSYS ≥ 0.20 mm`, `XIN/XOUT ≤ 11 mm`, and exact `.kicad_pro` severity names in this file.
- **`M1` (Stale 6-layer `stackup.md` & `In4.Cu` zone claim):** **FIXED** — rewrote [design/stackup.md](../../stackup.md) for the actual 8-layer `1.00 mm` **`JLC08101H-1080`** stackup and corrected `In4.Cu` (`0` zones) in `brief-f-usbc.md` & `phase5.md`.
- **`M2` (`90 diff` in `nets-f-usbc.csv` & `USB_DM_C` `F.Cu` hop):** **FIXED** — moved `USB_DM_C`'s `1.10 mm` `F.Cu` segment to `In6.Cu` (`0` `F.Cu` USB copper) and annotated `nets-f-usbc.csv` as `"90 diff (nominal; FS lumped l<<l_crit)"` with exact 2D stackup `Z_diff` values recorded above.
- **`M3` & `M4` (`.kicad_pro` `SW_SCAN`/`BATTERY`/`USB_POWER` subclasses, inherited northern `0.09 mm` QSPI escapes, `3× 0.20/0.10 mm` `U3` vias, mask dam):** **DOCUMENTED & JUSTIFIED** in [stackup.md](../../stackup.md) and [decisions.md](../../decisions.md) (`2026-11-08`).
- **`M5` (`.kicad_pro` `footprint_symbol_mismatch`/`text_height`/`text_thickness` severities & `min_text_thickness`):** **FIXED** in [round-pendant.kicad_pro](../../../hw/round-pendant/f-usbc/round-pendant.kicad_pro) (promoted to `"error"`, `min_text_thickness = 0.15`, verified `0` DRC violations).
- **`m2` & `m3` (`0.2002 mm` `In3.Cu` NPTH #1 margin, `QSPI` length prose, `BT1` pad size):** **FIXED** — nudged `In3.Cu` `CS5_16` via `(109.450, 108.150)` so NPTH #1 clearance rose from `0.2002 mm` to **`0.304 mm`**, and corrected `QSPI` (`5.45–12.06 mm`) & `BT1` (`1.60 × 2.40 mm`) prose.

### Round 2 Re-Review (`agy` `gemini-4-argon-high`)
- **Verdict:** **`PASS` (`0` BLOCKER, `0` MAJOR, `3` MINOR, `1` NOTE)** — all Round-1 BLOCKER/MAJOR findings (`B1..B3, M1..M5, m1..m3`) verified resolved or validly justified in `decisions.md`.
- **Minor polish applied after R2:** Corrected `41` -> `46` `"error"` severity count and `In4.Cu` asymmetric stripline `Z_diff = 72.3 Ω` (`B.Cu` `108–122 Ω`) above (`MINOR-1`, `MINOR-3`); legacy 6L historical top section in shared `stackup.md` preserved for Variant A history (`MINOR-1`), `3/886` `0.20/0.10 mm` vias flagged in `status.json` `jlc-8l-quote` (`MINOR-2`), and `netclass_patterns` mapping `43` nets (`SW_SCAN`/`BATTERY`/`USB_POWER`) noted (`NOTE-1`).
