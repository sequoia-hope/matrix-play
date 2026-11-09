# Gate 5: Stackup & Design Rules — Sunflower `s2-110-usbc`

Status: **`failed`** (held without modifying frozen `Rev S3C` PCB/project files: `nets_check.py --rules` fails with `32` `[netclass]` errors because [sunflower.kicad_pro](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/sunflower.kicad_pro) uses `"netclass_patterns"` with `"netclass_assignments": null`; `RuleArea 18` (`LX cutout L2`) is on `In1.Cu` instead of `In2.Cu` beneath `B.Cu`-mounted `U3`/`L1`; `VSYS` global rule is `0.16 mm` vs `0.25 mm`; `U5.17`/`U3.61` exempt open vias inside `B.Paste` without VIPPO; `solder_mask_min_width` is unset; and `14` `.kicad_pro` DRC severities are `"warning"`/`"ignore"` instead of `"error"`).

## Checklist ([stackup-and-rules.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/stackup-and-rules.md), Phase 5)

| Check | Evidence | State |
|---|---|---|
| Stackup specification with source & date ([stackup-4l.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/stackup-4l.md)) | `JLC04161H-7628` (`1.6 mm`, `1 oz` outer / `0.5 oz` `15.2 µm` inner); documents `B.Cu` ↔ `In2.Cu` vs `In1.Cu` reference-plane inversion | failed (`B2`) |
| Impedance widths computed (`DIFF_HS` & `SE_HS`) | Kirschning–Jansen `~134 Ω` diff (`0.15/0.15 mm` over `1.29 mm` `In1.Cu`) plus `50 Ω` SE (`w ≈ 0.36 mm`) & `90 Ω` diff (`w ≈ 0.27/0.15 mm`) recipes over `0.2104 mm` `7628` documented in [stackup-4l.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/stackup-4l.md) §2 | passed (doc synced) |
| Fab minimums entered with margin in [sunflower.kicad_pro](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/sunflower.kicad_pro) | `0.10 mm` track/space (`+11.1%`), `0.30/0.15 mm` via (`+50%` ring), `0.25 mm` edge (`+25%`); `0%` floor on `min_hole_to_hole`/`min_hole_clearance` and `solder_mask_min_width = 0.0` | failed (`M3`) |
| `nets_check.py --rules` (`0` errors) | Verbatim output below: **`FAIL: 32 errors, 0 warnings`** (`"netclass_assignments": null` in `.kicad_pro` exports `Default` in schematic netlist) + `VSYS >= 0.16 mm` DRU override | failed (`B3`, `M1`) |
| Custom rules in [sunflower.kicad_dru](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/sunflower.kicad_dru) sourced & complete | `48` valid `(version 1)` rules (`0` syntax errors), **but `LX cutout L2` is on `In1.Cu` instead of `In2.Cu`**, `BT1` Molex `RESTRICTED AREA` keepout & diff-pair skew rules are missing, `43/48` lack inline `#` source comments, and `U5.17`/`U3.61` exempt open vias inside paste | failed (`B1`, `M2`, `M4`) |
| DRC severities set in [sunflower.kicad_pro](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/sunflower.kicad_pro) | `43` `"error"`, `8` `"warning"`, `6` `"ignore"` (though `kicad-cli pcb drc --severity-all` reports `0` warnings and `0` exclusions on the board) | failed (`M4`) |

## Real Command Outputs (`2026-11-08`)

### `nets_check.py --rules` (`--nets design/nets-sunflower-s2-110-usbc.csv --rules`)
```text
nets_check: /home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc
  95 named nets in sunflower.kicad_sch, 108 rows in nets-sunflower-s2-110-usbc.csv

  ERRORS (32)
    [netclass] +1V1: KiCad net class Default, nets.csv says POWER
    [netclass] +3V3: KiCad net class Default, nets.csv says POWER
    [netclass] /MCU/LIGHT: KiCad net class Default, nets.csv says ANALOG
    [netclass] /MCU/QSPI_SCLK: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/QSPI_SD0: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/QSPI_SD1: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/QSPI_SD2: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/QSPI_SD3: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/QSPI_SS: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/USB_DM_MCU: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] /MCU/USB_DP_MCU: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] /MCU/VREG_AVDD: KiCad net class Default, nets.csv says ANALOG
    [netclass] /MCU/VREG_LX: KiCad net class Default, nets.csv says SWITCH
    [netclass] /Power/BAT_N: KiCad net class Default, nets.csv says POWER
    [netclass] /Power/USB_DM_C: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] /Power/USB_DP_C: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] GND: KiCad net class Default, nets.csv says POWER
    [netclass] Net-(C24-Pad1): KiCad net class Default, nets.csv says CLOCK
    [netclass] Net-(U1-ISET): KiCad net class Default, nets.csv says ANALOG
    [netclass] Net-(U2-ISET): KiCad net class Default, nets.csv says ANALOG
    [netclass] Net-(U3-XIN): KiCad net class Default, nets.csv says CLOCK
    [netclass] Net-(U3-XOUT): KiCad net class Default, nets.csv says CLOCK
    [netclass] Net-(U5-ILIM): KiCad net class Default, nets.csv says ANALOG
    [netclass] Net-(U5-ISET): KiCad net class Default, nets.csv says ANALOG
    [netclass] Net-(U5-TS): KiCad net class Default, nets.csv says ANALOG
    [netclass] Net-(U8-VDD): KiCad net class Default, nets.csv says ANALOG
    [netclass] USB_DM: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] USB_DP: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] VBAT: KiCad net class Default, nets.csv says POWER
    [netclass] VBAT_SENSE: KiCad net class Default, nets.csv says ANALOG
    [netclass] VBUS: KiCad net class Default, nets.csv says POWER
    [netclass] VSYS: KiCad net class Default, nets.csv says POWER

  FAIL: 32 errors, 0 warnings
```

*(Full `108`-row derived table identical to [phase3.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase3.md); inside `pcbnew`, all `108` PCB nets match exact `netclass_patterns` in `sunflower.kicad_pro` with `0` unmatched nets.)*

## Independent Fresh-Context Review (`gemini-4-argon-high`)

| ID | Severity | Reviewer Finding | Disposition & Action Taken |
|---|---|---|---|
| `B1` | `BLOCKER` | `RuleArea 18` (`LX cutout L2`) is on `In1.Cu` (`1.29 mm` away) instead of `In2.Cu` (`0.21 mm` directly beneath `B.Cu`-mounted `U3`/`L1`), allowing `VSYS` and `+3V3` routing under `L1`/`VREG_LX` | **Confirmed — Gate 5 held (`Rev S3D` fix):** Documented in [stackup-4l.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/stackup-4l.md) §1 and coupled noise quantified (`19–48 mV_pk` on `ADC_AVDD`) in Gate 8. |
| `B2` | `BLOCKER` | Inverted 4L `GND` plane (`In1.Cu` vs `In2.Cu` for `B.Cu` active ICs/QSPI/USB) & stale `90 diff` / `14.1 mm` USB text in initial `stackup-4l.md` | **Doc fixed; stackup inversion held (`Rev S3D` fix):** Synced [nets-sunflower-s2-110-usbc.csv](file:///home/sequoia/pcb/round-pendant/design/nets-sunflower-s2-110-usbc.csv) and [stackup-4l.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/stackup-4l.md) §2 with exact Kirschning–Jansen `~134 Ω` diff impedance, `50 Ω`/`90 Ω` `7628` recipes, and actual `34.55 / 35.87 mm` routed USB lengths. |
| `B3` | `BLOCKER` | `nets_check.py --rules` fails (`32` errors) because `.kicad_pro` uses `"netclass_patterns"` (`"netclass_assignments": null`), plus `SIGNAL` (`priority: 1`) overrides `SW_SCAN` (`priority: 3`) | **Confirmed — Gate 5 held (`Rev S3D` fix):** Corrected the mechanism explanation in [stackup-4l.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/stackup-4l.md) §4; populate `"netclass_assignments"` or schematic directives in `Rev S3D`. |
| `M1` | `MAJOR` | `VSYS` width rule (`0.16 mm` global in `.kicad_dru`, `0.20 mm` in `POWER`) under-sizes `15.2 µm` `In2.Cu` trunks; `VBUS` not restricted to outer `1 oz` copper | **Confirmed — Gate 5 held (`Rev S3D` fix):** Scope `0.16 mm` strictly to QFN pad neckdowns and enforce `≥ 0.25–0.30 mm` on `VSYS`/`VBUS` trunks in `Rev S3D`. |
| `M2` | `MAJOR` | `.kicad_dru` exempts open vias inside `U1.41`/`U2.41`/`U3.61`/`U5.17` without VIPPO/POFV (`U5.17` & `U3.61` overlap `B.Paste`; `U1.41` has `0` thermal vias) | **Confirmed — Gate 5 held (`Rev S3D` fix):** Constrain EP thermal vias strictly to paste-free `+` cross channels (`5` vias on `U1.41`/`U2.41`/`U3.61`) in `Rev S3D`. |
| `M3` | `MAJOR` | Zero-margin drill/hole floors (`0.20 mm`), unset `solder_mask_min_width`, matte vs green LPI dam difference, and microvias not disallowed | **Confirmed — Gate 5 held (`Rev S3D` fix):** Updated [stackup-4l.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/stackup-4l.md) §1/§3 to specify **standard green LPI mask** (`0.08–0.10 mm` QFN dam) and queued `solder_mask_min_width = 0.10 mm` + `(constraint disallow microvia buried_via)` for `Rev S3D`. |
| `M4` | `MAJOR` | `14` `.kicad_pro` DRC severities left at `"warning"`/`"ignore"`, missing diff-pair skew rules, and `43/48` `.kicad_dru` rules missing inline `#` source comments | **Confirmed — Gate 5 held (`Rev S3D` fix):** Verified `0` warnings/exclusions via `kicad-cli pcb drc --severity-all` on `Rev S3C`; promote severities, add targeted `J1`/`NT1` exclusions, and add `#` rule comments in `Rev S3D`. |
| `m1–m3` | `MINOR` | `εr = 4.4` vs `4.6` on `7628`, `1.5862` vs `1.6062 mm` stack height, `43/8/6` severity count in `stackup-4l.md`, `29` vias under `BT1` (`0.10 mm` `BATTERY` clr), `0.10 mm` silk default | **Doc fixed in `stackup-4l.md`; board rules queued for `Rev S3D`:** Added `BT1` Molex `RESTRICTED AREA` keepout and `BATTERY` `≥ 0.20 mm` clearance to `Rev S3D` checklist. |
| `N1–N2` | `NOTE` | All `48` `.kicad_dru` rules parse cleanly; recommend `ENIG` over `HAL SnPb` at order time | **Noted:** Added `ENIG 1U"` order recommendation in [stackup-4l.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/stackup-4l.md) §1. |
