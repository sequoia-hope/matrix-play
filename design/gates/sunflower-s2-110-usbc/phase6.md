# Gate 6: Component Placement — Sunflower `s2-110-usbc`

Status: **`failed`** (`placement_check.py`, `sync_check.py`, and KiCad DRC all pass with `0` errors / `0` courtyard overlaps, **held** on `BT1` Molex `RESTRICTED AREA` pad-escape violation, `LX cutout L2` placed on `In1.Cu` instead of adjacent `In2.Cu`, `U8` cell protector placed `29.11 mm` away from `BT1` on the opposite SE rim, and `U4` flash decoupler `C22` placed `5.51 mm` away on the wrong side of `U4` — see [phase10.md](phase10.md) for `Rev S3C` prototype waiver vs `Rev S3D` respin options).

## Checklist ([placement.md](../../../.claude/skills/pcb-design/references/placement.md), Phase 6)

| Item | Evidence | State |
|---|---|---|
| Fixed items match [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md) (`Edge.Cuts`, `0` mounting holes, `J1`, `BT1`, `SW1`, `SW2`, `Q2`, `D1..D110`) | Coordinates/rotations match `config.py` & [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md) (`3.40 mm` `BT1` height & `3.02/4.04 mm` inward clearance documented); footprints not marked `(locked)` in `.kicad_pcb` | partial |
| `placement_check.py` passes (output pasted below) | `PASS: 0 errors, 0 warnings` (`2587 mm` MST ratsnest over `134` nets) | passed |
| Schematic–board parity (`sync_check.py` & `kicad-cli pcb drc --schematic-parity`) | `206` symbols = `206` footprints, `0` parity errors, `0` courtyard overlaps | passed |
| Datasheet layout guidelines & rule areas followed per part | **Failed** on `BT1` Molex `RESTRICTED AREA`, `U3`/`L1` `In2.Cu` `LX` cutout, `U8` inline proximity to `BT1`, and `C22 -> U4.8` (`5.51 mm`) — per-part table below | **failed** |
| Independent visual placement review ([top.png](../../renders/sunflower-s2-110-usbc/top.png), [bottom.png](../../renders/sunflower-s2-110-usbc/bottom.png), [3d-top.png](../../renders/sunflower-s2-110-usbc/3d-top.png), [3d-bottom.png](../../renders/sunflower-s2-110-usbc/3d-bottom.png), [assembly-top.png](../../renders/sunflower-s2-110-usbc/assembly-top.png), [assembly-bottom.png](../../renders/sunflower-s2-110-usbc/assembly-bottom.png)) | Completed (`2 BLOCKER, 2 MAJOR, 6 MINOR, 3 NOTE`) | **failed** |
| User reviewed placement render in PCB view | Deferred to user review alongside Gates 4 & 10 | pending |

## Per-Part Datasheet Layout Guideline Audit

| Part(s) | Datasheet Guideline | `s2-110-usbc` Placement Status |
|---|---|---|
| `U3`, `L1`, `C16`–`C21`, `R13` (`RP2350A` + `3.3 µH`) | [rp2350.md](../../../.claude/skills/pcb-design/chips/rp2350.md): `L1`, `C16` (`1.17 mm`), `C18` (`2.13 mm`), `C17` (`2.83 mm`), `R13` congruent to RPi reference; `L1.1` dot on `+1V1`; plane cutout directly under `VREG_LX`/`L1` | **Partial (`BLOCKER-2`):** `B.Cu` 3D $SO(3)$ placement & `L1` polarity match RPi reference (`0.89–3.10 mm` local decouplers), **but** `LX cutout L2` was placed on `In1.Cu` (`1.29 mm` away) instead of `In2.Cu` (`0.21 mm` directly under `B.Cu` `VREG_LX`/`L1`) |
| `Y1`, `C23`, `C24`, `R17` (`ABM8-272-T3` `12 MHz`) | Short `B.Cu`-only loop (`≤ 11 mm`), `0` vias, away from `VREG_LX`/`L1` | **Pass (`MINOR-6`):** `0` vias, `15.8 mm` from `L1`; `XIN` sits on `Y1.1` (`5.8 mm` pad-to-pin, `1.68 mm` routed track) |
| `BT1` (`Molex 53261-0271`) | Molex `532610001-SD` Sh. 2: `3.0 × 2.5 mm` `RESTRICTED AREA` (`no copper pattern or solder`) under housing behind signal pads | **Fail (`BLOCKER-1`):** Signal pads abut `Edge.Cuts` (`0.408 mm` pad-to-edge) with no via-in-pad allowed, forcing `VBAT` & `BAT_N` traces through Molex's prohibited area under `BT1` (no rule area drawn); inward plug gap to `C9` is `3.02 mm` |
| `U8`, `R8`, `C6` (`XB9901A`) | `xb9901a.pdf` p. 10 Fig. 6: inline right at battery connector with short, wide high-current path | **Fail (`MAJOR-1`):** Placed at SE rim `(+6.45, +12.79)`, **`29.11 mm` Euclidean (`> 35 mm` routed)** across the board from `BT1`, with `C6` (`3.32 mm`) split north of `U7` |
| `U4`, `C22` (`W25Q128JVPIQ`) | High-speed `75 MHz` QSPI decoupling right at `U4.8` (`VCC`), `NoEPCopper` under body | **Fail (`MAJOR-2`):** `NoEPCopper` respected and QSPI pins face `U3` (`5.51–13.85 mm`), **but** `C22` sits on the West side of `U4` (`5.51 mm` from `U4.8` on the NE corner) |
| `U5`, `C1`, `C2`, `C5` (`BQ24073`) | Bypass caps close on `IN` (`C1` `2.35 mm`), `OUT` (`C2` `2.82 mm`), `BAT` (`C5` `3.27 mm`); thermal pad tied to `GND` | **Pass** (placement clean; `U5.17` non-POFV paste overlap tracked in Gate 7) |
| `U6`, `C3`, `C4` (`TPS7A0233`) | `1 µF` input/output within `< 2 mm` | **Pass:** `C3 -> U6.4 = 1.82 mm`, `C4 -> U6.1 = 1.08 mm` |
| `U7` (`USBLC6-2P6`) | Flow-through inline between `J1` and `R14/R15`/`U3` | **Pass (`MINOR-1`):** Wired flow-through (`0` stubs); `~7.0 mm` East of `J1` center pins, `~4.7 mm` from `C1` |
| `U1`, `U2`, `C30`–`C34`, `C40`–`C44` (`AW20198QNR`) | `0402` HF bypass closest to `VCC1/VCC2` ahead of `22 µF` `0603` bulk | **Pass:** `0402` caps at `1.29–2.66 mm`, `0603` bulk at `3.56–3.93 mm` |
| `U9`, `C25`–`C27` (`LIS2DW12`) | `100 nF` + `4.7 µF` close to `VDD`/`VDD_IO`, away from board flex/heat | **Pass:** `C25 = 1.72 mm`, `C26 = 2.08 mm`, `C27 = 3.51 mm` |
| `D1`–`D110`, `Q2` (`F.Cu`) | Keepouts around `J1` `6` holes & `Q2` optical aperture | **Pass (`MINOR-3`):** `0` overlaps; outer LED pad corners reach `r = 18.374 mm` (`0.626 mm` inside `Edge.Cuts`; any bezel lip must stay at `r ≥ 18.5 mm`) |

## Verbatim Check Outputs (`2026-11-08`)

### 1. `placement_check.py`

Command:
`python3 .claude/skills/pcb-design/scripts/placement_check.py hw/sunflower/s2-110-usbc/sunflower.kicad_pcb`

```text
placement_check: hw/sunflower/s2-110-usbc/sunflower.kicad_pcb
  Y1 pad 1 (Net-(U3-XIN)) is 5.8 mm from its IC pin
  Y1 pad 3 (Net-(C24-Pad1)) is 3.9 mm from its IC pin
  ratsnest (MST, all nets except GND): 2587 mm over 134 nets

  decoupler -> pin, pad centre to pad centre
    C1    -> U5.13   VBUS        2.35 mm
    C10   -> U3.20   +3V3        2.40 mm
    C11   -> U3.30   +3V3        1.60 mm
    C12   -> U3.38   +3V3        1.87 mm
    C13   -> U3.53   +3V3        3.10 mm
    C14   -> U3.44   +3V3        1.69 mm
    C16   -> U3.49   +3V3        1.17 mm
    C17   -> U3.46   /MCU/VREG_AVDD  2.83 mm
    C18   -> U3.50   +1V1        2.13 mm
    C19   -> U3.23   +1V1        1.63 mm
    C2    -> U5.10   VSYS        2.82 mm
    C20   -> U3.6    +1V1        1.60 mm
    C21   -> U3.39   +1V1        1.69 mm
    C22   -> U4.8    +3V3        5.51 mm
    C25   -> U9.9    +3V3        1.72 mm
    C26   -> U9.9    +3V3        2.08 mm
    C27   -> U9.10   +3V3        3.51 mm
    C3    -> U6.4    VSYS        1.82 mm
    C30   -> U1.5    VSYS        3.56 mm
    C31   -> U1.5    VSYS        2.23 mm
    C32   -> U1.5    VSYS        2.23 mm
    C33   -> U1.22   VSYS        1.29 mm
    C34   -> U1.22   VSYS        1.36 mm
    C4    -> U6.1    +3V3        1.08 mm
    C40   -> U2.5    VSYS        3.93 mm
    C41   -> U2.5    VSYS        2.66 mm
    C42   -> U2.5    VSYS        2.66 mm
    C43   -> U2.22   VSYS        1.29 mm
    C44   -> U2.22   VSYS        1.36 mm
    C5    -> U5.2    VBAT        3.27 mm
    C6    -> U8.6    Net-(U8-VDD)  3.32 mm
    C8    -> U3.1    +3V3        1.60 mm
    C9    -> U3.11   +3V3        1.60 mm

  PASS: 0 errors, 0 warnings
```

### 2. `sync_check.py` & Courtyard / Parity DRC

Command:
`python3 .claude/skills/pcb-design/scripts/sync_check.py hw/sunflower/s2-110-usbc`

```text
sync_check: hw/sunflower/s2-110-usbc
  schematic sunflower.kicad_sch: 206 symbols (0 excluded from board)
  board sunflower.kicad_pcb: 206 footprints (0 board-only)
  BOM bom-jlcpcb.csv: 191 designators
  CPL cpl-jlcpcb.csv: 191 placements
  191 parts to build; required fields: LCSC
  stock not checked: re-check every LCSC part at release (phase 10)

  PASS: 0 errors, 0 warnings
```

KiCad DRC (`kicad-cli pcb drc --severity-all --schematic-parity --format json`): `violations: 0`, `unconnected_items: 0`, `schematic_parity: 0` (full JSON in [phase7.md](phase7.md)).

## Independent Review (`2026-11-08`, fresh-context `agy` reviewer)

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| `BLOCKER-1` | BLOCKER | `BT1` (`Molex 53261-0271`) rim placement leaves `0` outward escape room without via-in-pad, forcing raw `VBAT`/`BAT_N` traces across Molex's `3.0 × 2.5 mm` `RESTRICTED AREA` under the housing (`no rule area drawn`); inward mating clearance to `C9`/`U3` is `3.02 / 4.04 mm`; height is `3.40 mm` mated | **Upheld — Gate 6 held (`failed`):** Height (`3.40 mm`) and exact `3.02 / 4.04 mm` inward plug clearance updated in [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md); physical `BT1` pullback + Molex `RESTRICTED AREA` rule area requires board copper edit (`Rev S3D` vs `Rev S3C` bench prototype waiver in [decisions.md](../../decisions.md) / [phase10.md](phase10.md)) |
| `BLOCKER-2` | BLOCKER | `RP2350A` (`U3`) switch-node cutout (`LX cutout L2`) placed on `In1.Cu` (`1.29 mm` away) instead of `In2.Cu` (`0.21 mm` directly beneath `B.Cu` `VREG_LX`/`L1`) | **Upheld — Gate 6 held (`failed`):** Quantified in Phase 8 (`1.31 pF` parasitic switch-node coupling; buck remains functional on bench); `In2.Cu` cutout + `In1.Cu ↔ In2.Cu` layer swap tracked for `Rev S3D` |
| `MAJOR-1` | MAJOR | `U8` (`XB9901A`) placed `29.11 mm` away from `BT1` at SE rim (not inline at `BT1`), with `C6` (`3.32 mm`) split north of `U7` | **Upheld — Gate 6 held (`failed`):** Adds `~220 mΩ` round-trip trace resistance on raw battery path (modeled in Phase 8 [pdn_headroom.png](../../sim/sunflower-s2-110-usbc/pdn_headroom.png)); NW co-location with `BT1` tracked for `Rev S3D` |
| `MAJOR-2` | MAJOR | `U4` (`W25Q128JVPIQ`) decoupler `C22` placed on West side of `U4`, `5.51 mm` away from `U4.8` (`VCC` on NE corner) | **Upheld — Gate 6 held (`failed`):** Modeled in Phase 8 (`19.5 mV` transient rail droop at `75 MHz` QSPI, electrically safe for `2.7–3.6 V` flash); moving `C22` beside `U4.8` tracked for `Rev S3D` |
| `MINOR-1` | MINOR | `U7` (`USBLC6-2P6`) detoured `~7.0 mm` East of `J1` `D±` pads and `~4.7 mm` from `C1` (`34.55 / 35.87 mm` total `USB_D±` length) | Fixed `34.55 / 35.87 mm` length in [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md#L44) and [stackup-4l.md](../../study/sunflower/stackup-4l.md); `12 Mbps` FS margin verified in Phase 8 |
| `MINOR-2` | MINOR | Single `GND` test pad (`TP8`) `22–30 mm` West of East test pads; `13/14` test pads inside `Ø35 mm` battery circle; `TP9/TP10` absent | Documented in [bringup-s2-110-usbc.md](../../study/sunflower/bringup-s2-110-usbc.md): clip `J1` metal USB-C shell as South `GND` return, complete Steps 1–7 before bonding LiPo, then cover `B.Cu` test pads with `0.05 mm` Kapton tape |
| `MINOR-3` | MINOR | Outer LED pads reach `r_max = 18.374 mm` (`0.626 mm` to edge; bezel ID must be `r ≥ 18.5 mm`); `0.18–0.29 mm` `F.Cu` annular-ring gap to `D10/D104/D110` around `J1` slots | Documented in [brief-s2-110-usbc.md](../../study/sunflower/brief-s2-110-usbc.md#L20): **forbid `F.Cu` wave/hand soldering on `J1`** (`sunflower-B_Paste.gbp` omits paste on `J1`'s 4 PTH slots; tack outer `B.Cu` slot edges only on `Rev S3C`, or switch to full-SMT `TYPE-C-31-M-22` / add `B.Paste` in `Rev S3D`) |
| `MINOR-4` | MINOR | `C7` (`VBAT_SENSE` filter cap) sits at `Q1` (`~22 mm` from `U3.40`) rather than right at `U3.40` | Noted for `Rev S3D`; `100 nF` low-frequency RC (`≥ 30 ms` settle) + `16`-sample averaging mitigates coupling on bench |
| `MINOR-5` | MINOR | Sparse in-pad `GND` vias (`U3.61`: `1` in-pad + `1` perimeter, `U2.41`: `1+1`, `U1.41`: `0+5`); `SW1/SW2` pads `0.282 mm` from `Edge.Cuts` | Tracked in Gate 7 (`B5`) and modeled in Phase 8 (`+1.6 K` junction penalty on `U3`, well within `125 °C` limit) |
| `MINOR-6` | MINOR | `Y1` at `0°` puts `XIN` on north pad (`5.8 mm` pad-to-pin, `1.68 mm` routed) and `R17`–`Y1` on `8.44 mm` wrap | Verified safe in Phase 8 (`CL,eff ≈ 9.8 pF`, `13×` `gm` startup margin, `0` vias); `180°` `Y1` rotation noted as optional `Rev S3D` polish |
