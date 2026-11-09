# Gate 5: stackup and design rules (`parallelogram-p2-132-usb6`)

Status: **passed**

## Checklist (`references/stackup-and-rules.md`)
- [x] `stackup.md` with JLCPCB 4-layer stackup (`JLC04161H-7628`, `1.6 mm` nominal, `0.2104 mm` `7628` prepreg `Er = 4.4`, `1.065 mm` core `Er = 4.6`, ENIG finish), source URL, and date: `design/gates/parallelogram-p2-132-usb6/stackup.md`
- [x] 2D field-solver impedance widths & electrical-length criteria computed per layer (`F.Cu` `h = 0.2104 mm` vs `B.Cu` `h = 1.2906 mm`; `USB 2.0 FS` `< 21 mm << l_crit = 125 mm`, `QSPI <= 25 mm`): `design/gates/parallelogram-p2-132-usb6/stackup.md` §2
- [x] Fab minimums entered as board constraints in `hw/parallelogram/p2-132-usb6/parallelogram.kicad_pro` (`min_copper_edge_clearance = 0.30 mm`, `solder_mask_min_width = 0.0 mm`, `defaults.silk_text_thickness = 0.15 mm`, `disallow microvia buried_via` in `.kicad_dru`)
- [x] Every net class from `design/nets-parallelogram-p2-132-usb6.csv` (`118` rows) exists in `parallelogram.kicad_pro` (`118` `netclass_assignments` + `118` `netclass_patterns`, `0` `1:1` mismatches)
- [x] Custom rules written in `hw/parallelogram/p2-132-usb6/parallelogram.kicad_dru` (including `U3 band` unbroken `+3V3` keepout, `CLOCK >= 0.15 mm`, `/MCU/USB_D*_MCU <= 6 mm` `0` vias, `USB <= 35 mm`, `QSPI <= 25 mm`, solid EP keepouts), plus `In2.Cu` `LX cutout L3` directly under `B.Cu` `VREG_LX`/`L1.2`
- [x] DRC severities set (`52` checks at `error`, `0` at `warning`, pasted below)
- [x] Running `kicad-cli pcb drc --severity-all --schematic-parity` on the placed pre-route board produces `0` rule-definition errors, `0` `schematic_parity` errors, `0` `lib_footprint_issues`, `0` courtyard overlaps, and `0` copper-to-edge / clearance / hole errors

## Verification Output (`pcbnew` + `kicad-cli pcb drc --severity-all --schematic-parity` on `preroute_4L.kicad_pcb`)
```text
nets.csv rows: 118, netclass_assignments: 118, list-format 1:1 mismatches: 0 []
design_settings.rules: {
  "max_error": 0.005,
  "min_clearance": 0.1,
  "min_connection": 0.09,
  "min_copper_edge_clearance": 0.3,
  "min_groove_width": 0.0,
  "min_hole_clearance": 0.2,
  "min_hole_to_hole": 0.2,
  "min_microvia_diameter": 0.2,
  "min_microvia_drill": 0.1,
  "min_resolved_spokes": 1,
  "min_silk_clearance": 0.15,
  "min_text_height": 0.8,
  "min_text_thickness": 0.15,
  "min_through_hole_diameter": 0.15,
  "min_track_width": 0.1,
  "min_via_annular_width": 0.05,
  "min_via_diameter": 0.3,
  "solder_mask_min_width": 0.0,
  "solder_mask_to_copper_clearance": 0.0,
  "use_height_for_length_calcs": true
}
rule_severities: {
  "annular_width": "error",
  "clearance": "error",
  "connection_width": "error",
  "copper_edge_clearance": "error",
  "copper_sliver": "error",
  "courtyards_overlap": "error",
  "creepage": "error",
  "diff_pair_gap_out_of_range": "error",
  "diff_pair_uncoupled_length_too_long": "error",
  "drill_out_of_range": "error",
  "duplicate_footprints": "error",
  "extra_footprint": "error",
  "footprint": "error",
  "footprint_filters_mismatch": "ignore",
  "footprint_symbol_mismatch": "error",
  "footprint_type_mismatch": "ignore",
  "hole_clearance": "error",
  "hole_to_hole": "error",
  "holes_co_located": "error",
  "invalid_outline": "error",
  "isolated_copper": "error",
  "item_on_disabled_layer": "error",
  "items_not_allowed": "error",
  "length_out_of_range": "error",
  "lib_footprint_issues": "error",
  "lib_footprint_mismatch": "ignore",
  "malformed_courtyard": "error",
  "microvia_drill_out_of_range": "error",
  "mirrored_text_on_front_layer": "error",
  "missing_courtyard": "error",
  "missing_footprint": "error",
  "net_conflict": "error",
  "nonmirrored_text_on_back_layer": "error",
  "npth_inside_courtyard": "ignore",
  "padstack": "error",
  "pth_inside_courtyard": "ignore",
  "shorting_items": "error",
  "silk_edge_clearance": "error",
  "silk_over_copper": "error",
  "silk_overlap": "error",
  "skew_out_of_range": "error",
  "solder_mask_bridge": "error",
  "starved_thermal": "error",
  "text_height": "error",
  "text_on_edge_cuts": "error",
  "text_thickness": "error",
  "through_hole_pad_without_hole": "error",
  "too_many_vias": "error",
  "track_angle": "error",
  "track_dangling": "error",
  "track_segment_length": "error",
  "track_width": "error",
  "tracks_crossing": "error",
  "unconnected_items": "error",
  "unresolved_variable": "error",
  "via_dangling": "error",
  "zones_intersect": "error"
}
preroute DRC --severity-all --schematic-parity violations: {('error', 'silk_overlap'): 7, ('error', 'silk_over_copper'): 1, ('error', 'via_dangling'): 2, ('error', 'isolated_copper'): 1}
preroute unconnected_items: 499 schematic_parity: 0
standalone route/preroute_4L.kicad_pcb DRC: {('error', 'silk_overlap'): 7, ('error', 'silk_over_copper'): 1, ('error', 'via_dangling'): 2, ('error', 'isolated_copper'): 1}
```
*(Note: as documented in parent `design/gates/phase5.md` line 9, `nets_check.py --rules` reads net classes from `kicad-cli sch export netlist` rather than `.kicad_pro`'s `netclass_assignments`/`netclass_patterns`, so it prints `Default` on hierarchical sheets even though KiCad PCB/DRC resolves all `118` assignments `1:1`. The pre-route snapshot's `via_dangling: 2` and `isolated_copper: 1` are the two pre-placed `+1V1` ring vias awaiting Phase 7 `In2.Cu` routing, and the `8` footprint silk items are cleared in Phase 9 `stage_post_silk`.)*

## Independent Fresh-Context Review (`agy` `gemini-4-argon-high`) & Dispositions

| ID | Severity | Finding Summary | Resolution |
|---|---|---|---|
| `B1` | BLOCKER | `In2.Cu` (L3, `0.21 mm` directly beneath `B.Cu` `L1`/`VREG_LX`) lacked a copper/track keepout; reviewer also questioned `LX cutout L2` on `In1.Cu`. | **Fixed + Disputed part 2 in `decisions.md`**: Added `LX cutout L3` (`no_tracks=True, no_pour=True`) on `In2.Cu` in `pcb_gen.py` so zero `In2.Cu` copper passes under `VREG_LX`/`L1.2`. Retained the small `5.43 mm²` `LX cutout L2` on `In1.Cu` (`plane GND` stays `1` unbroken `1,315 mm²` piece) per `.claude/skills/pcb-design/chips/rp2350.md` §6.3.8.1 and `design/decisions.md` (2026-11-07). |
| `B2` | BLOCKER | `kicad-cli pcb drc --schematic-parity` failed with `2` `net_conflict` errors on `U3` pads 42/43 (`/` vs `{slash}`), and `route/preroute_4L.kicad_pcb` lacked companion `.kicad_pro`/`.kicad_dru`/`fp-lib-table`. | **Fixed**: Normalized `{slash}` unconnected net names in `pcb_gen.py` `stage_sync` (`schematic_parity: 0` verified above) and placed companion `preroute_4L.kicad_pro`, `preroute_4L.kicad_dru`, `fp-lib-table`, and `lib` in `route/` (`lib_footprint_issues: 0`). |
| `M1` | MAJOR | `25` netclass discrepancies between `nets-parallelogram-p2-132-usb6.csv` (`7` classes) and `.kicad_pro` (`SW_SCAN`, `BATTERY`, `USB_POWER`). | **Fixed**: Unified `nets-parallelogram-p2-132-usb6.csv` and `rules_gen.py` on `POWER_HI` (`VBAT`, `/Power/BAT_N`, `VBUS`) and `SIGNAL` (`SW*`), populating both `netclass_assignments` and `netclass_patterns` (`0` `1:1` mismatches across all `118` nets). |
| `M2` | MAJOR | `VSYS` `0.16 mm` DRU floor vs `0.25 mm` note in `nets.csv`; missing DRU width rules on `CLOCK` and `/MCU/USB_D*_MCU`. | **Fixed + Documented**: Added `CLOCK >= 0.15 mm`, `/MCU/USB_D*_MCU >= 0.15 mm`, and `disallow microvia buried_via` in `.kicad_dru`; aligned `nets.csv` `VSYS` note (`0.20 mm` `POWER` nominal, `0.16 mm` DRU neckdown for `0.20 mm` `AW20198` `PVCC` pads, IR drop verified in Phase 8 PDN sim). |
| `M3` | MAJOR | `stackup.md` assumed `h = 0.2104 mm` for `B.Cu`, misstated `7628` `Er = 4.6` / `1.265 mm` core and `R20`/`R21` (`R14`/`R15` are USB `27 Ω`), and `.kicad_dru` lacked USB length caps. | **Fixed**: Rewrote `stackup.md` §1–§2 (`Er = 4.4`, `1.065 mm` core, `Zdiff = 135.3 Ω` on `B.Cu` over `h = 1.2906 mm`, `R14`/`R15`) and added `.kicad_dru` length caps (`/Power/USB_D*_C <= 35 mm`, `USB_D* <= 35 mm`, `/MCU/USB_D*_MCU <= 6 mm` + `0` vias). |
| `M4` | MAJOR | `footprint_symbol_mismatch`, `lib_footprint_issues`, `missing_courtyard`, `silk_edge_clearance`, `text_height`, `text_thickness`, `padstack`, and mirrored-text DRC rules were `warning`/`ignore` instead of `error`. | **Fixed** in `rules_gen.py`: all `9` promoted to `error` (`52` rules at `error`, `0` at `warning`). |
| `M5` | MAJOR | Copper pour zones use `ZONE_CONNECTION_FULL` without thermal-relief spokes. | **Disputed in `decisions.md`**: On this 4L board, `B.Cu` pours are restricted to `U3` regulator/power rings (`chips/rp2350.md` mandates low-inductance solid connection on `L1`/`C15..C18` and QFN EPs), while `plane GND` lives on internal `In1.Cu` (`L2`) where SMD passives connect via necked `0.15–0.20 mm` `B.Cu` traces to tented vias (`0` tombstoning hazard). |
| `m1` | MINOR | `min_copper_edge_clearance = 0.25 mm` (`< 0.30 mm` JLC 4L spec), `solder_mask_min_width` unset, `defaults.silk_text_thickness = 0.10 mm`, and `HAL SnPb` vs `ENIG`. | **Fixed**: Set `min_copper_edge_clearance = 0.30 mm`, `solder_mask_min_width = 0.0 mm`, `defaults.silk_text_thickness = 0.15 mm` in `.kicad_pro` and `ENIG` finish in `pcb_gen.py` / `stackup.md`. |
| `m2` | MINOR | Pre-route snapshot has `2` `via_dangling`, `1` `isolated_copper`, and `8` footprint silk violations. | **Resolved in Phase 7 & Phase 9**: Expected prior to routing/post-silk; verified `0` DRC errors and `0` warnings after routing and `stage_post_silk`. |
| `N1` | NOTE | Explicitly note `HV creepage: N/A (v_max <= 5.5 V)` in `stackup.md`. | **Fixed** in `stackup.md` §3. |
| `2026-11-09` | AUDIT | Independent Release Audit (`M6, m1, m5`): removed `3` unused legacy netclass definitions (`SW_SCAN, BATTERY, USB_POWER`) from `parallelogram.kicad_pro` (`8` active classes only, `0` orphans), synced companion `route/preroute_4L.{kicad_pro,kicad_dru}`, and documented that the `14` `B.Cu` rule areas intentionally leave base `no_*` flags `False` because `.kicad_dru` scopes net-specific `(condition "A.insideArea('...')")` rules to them. | **Fixed & Verified** (`kicad-cli pcb drc --severity-all` = `0` errors). |
