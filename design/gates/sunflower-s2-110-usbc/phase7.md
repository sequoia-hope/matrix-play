# Gate 7: PCB Routing, Planes & Copper — Sunflower `s2-110-usbc`

Status: **`failed`** (`kicad-cli pcb drc --severity-all` passes with `0` violations, `0` opens, and `0` parity diffs, and `pad_joints.py` passes with `0` thin joints across `797` SMD pads; however, independent copper & reference-layout audit holds Gate 7 on `5` `BLOCKER`s and `4` `MAJOR`s: `COUT` `Zone 11` has `0` power spokes routing `100%` of core `+1V1` current via `U3.50` `VREG_FB`; `PGND` shares its single via `@(102.43, 99.10)` with `C17` `CFILT`; `In2.Cu` routes `+3V3` `ADC_AVDD` and `VSYS` `0.21 mm` directly beneath `B.Cu` `VREG_LX`/`L1`; `RP2350` `+3V3` band is split into `4` pieces (`9.7561 mm²`) with `11` foreign vias inside `U3 ring`; `U3.61` has `1` via & `U5.17` has `2` open vias clipping `B.Paste` without VIPPO; power transitions use single `0.15 mm` vias (`438 mΩ` PCB battery loop); `VBAT` via `@(86.99, 89.16)` sits `0.107 mm` from `BT1.2`; and `U4.8` Flash decoupling is `8.56 mm` away).

## Checklist ([routing.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/routing.md) & [rp2350.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/chips/rp2350.md), Phase 7)

| Check | Evidence | State |
|---|---|---|
| `kicad-cli pcb drc --severity-all` (`0` errors, `0` opens, `0` parity diffs) | Verbatim JSON output below (`violations=[]`, `unconnected_items=[]`, `schematic_parity=[]`) | passed |
| `pad_joints.py` (`797` SMD pads, `≥ 0.09 mm`) | Verbatim output below (`PASS: 0 thin pad joints`) | passed |
| `copper_audit.py` (`0` dangling/slivers/necks) | Verbatim output below (`morph_necks=0`, `acute_slivers=0`, `micro_segs(<40um)=86`) | passed (minor `m2`) |
| `nets_check.py --rules --routed` (`≤ length_limit`, `"no vias"`) | Verbatim output + `pcbnew` hierarchical net table below (`0` length/via-count errors; `32` `.kicad_pro` `netclass` errors from Gate 5) | failed (`netclass`) |
| `U3` `RP2350` `+1V1` ring, `VREG_FB` Kelvin sense, `PGND` & `CFILT` vias, `LX` cutout, & `+3V3` band | `+1V1` ring = `1` piece (`6.0625 mm²`), **but `COUT` has `0` spokes (`100%` `DVDD` via `U3.50`), `CFILT` shares `PGND`'s single via, `In2.Cu` routes under `VREG_LX`/`L1`, and `+3V3` band is `4` pieces (`9.7561 mm²`)** | failed (`B1`–`B4`) |
| Exposed-pad thermal vias (`U1.41`, `U2.41`, `U3.61`, `U5.17`) & non-VIPPO paste clearance | `U3.61 = 1` via & `U5.17 = 2` vias overlap `B.Paste`; `U1.41 = 0` in-pad vias (`U2.41 = 1` clean) | failed (`B5`) |
| Power rail parallel via arrays, USB FS inline routing, `BT1` via safety, & `U4.8` decoupling | Single-via hops (`438 mΩ` battery loop), split-layer `34.6 / 35.9 mm` USB, `0.107 mm` `VBAT` via to `BT1.2`, `8.56 mm` `U4.8` cap | failed (`M1`–`M4`) |
| `12 MHz` crystal `Y1` routing (`B.Cu`, `0` vias, dedicated `GND` vias) | `XIN = 8.44 mm`, `XOUT = 1.33 mm`, `C24-1 = 1.68 mm`, `0` vias, cap `GND` vias at `0.53 / 0.56 mm` | passed |

## Real Command Outputs (`2026-11-08`)

### 1. Design Rules Check (`reserve -c 4 -- kicad-cli pcb drc --severity-all --format json`)
```json
{
    "$schema": "https://schemas.kicad.org/drc.v1.json",
    "coordinate_units": "mm",
    "date": "2026-11-08T16:40:21-0800",
    "included_severities": [
        "error",
        "warning",
        "exclusion"
    ],
    "kicad_version": "9.0.8",
    "schematic_parity": [],
    "source": "sunflower.kicad_pcb",
    "unconnected_items": [],
    "violations": []
}
```

### 2. SMD Pad-Joint Neck Check (`pad_joints.py`) & Copper Audit (`copper_audit.py`)
```text
pad_joints: sunflower.kicad_pcb: 797 SMD pads, joints under 0.09 mm:

  PASS: 0 thin pad joints

hw/sunflower/s2-110-usbc/sunflower.kicad_pcb: tracks=4462 vias=637 | dangling=0 cap_gap=0 mid_graze/stubs=0 off_via=0 morph_necks(<86um)=0 acute_slivers=0 collinear_dups=0 micro_segs(<40um)=86 strip_zones=0 zone_intrusions=0
```

### 3. Routed Length & Via Check (`nets_check.py --rules --routed`) + Direct `pcbnew` Hierarchical Net Audit
```text
  routed length (mm, track copper on the net; zones not counted) against nets.csv
    net                 routed  limit vias
    /MCU/QSPI_SCLK        0.00   25.0    0
    /MCU/QSPI_SD0         0.00   25.0    0
    /MCU/QSPI_SD1         0.00   25.0    0
    /MCU/QSPI_SD2         0.00   25.0    0
    /MCU/QSPI_SD3         0.00   25.0    0
    /MCU/QSPI_SS          0.00   25.0    0
    /MCU/USB_DM_MCU       0.00    6.0    0
    /MCU/USB_DP_MCU       0.00    6.0    0
    /MCU/VREG_LX          0.00      -    0
    /Power/USB_DM_C       0.00   25.0    0
    /Power/USB_DP_C       0.00   25.0    0
    Net-(C24-Pad1)        1.68    6.0    0
    Net-(U3-XIN)          8.44   11.0    0
    Net-(U3-XOUT)         1.33    5.0    0
    USB_DM               13.05   25.0    2
    USB_DP               16.05   25.0    2

  FAIL: 32 errors, 11 warnings
```
*(Note: `nets_check.py` `L231` strips leading `/` from `tr.GetNetname()` while keeping `/` in `norm(name)`, causing hierarchical `/MCU/*` and `/Power/*` nets to report `0.00` in `--routed`; direct `pcbnew` extraction below verifies every hierarchical net's exact copper length and via count:)*
```text
  /MCU/VREG_LX           zone=2.1826mm2 tracks=0.00mm vias= 0 (limit: no vias -> PASS)
  /Power/USB_DP_C        len= 15.94mm vias= 3 (limit <=25.0mm -> PASS)
  /Power/USB_DM_C        len= 20.27mm vias= 4 (limit <=25.0mm -> PASS)
  USB_DP                 len= 16.05mm vias= 2 (limit <=25.0mm -> PASS)
  USB_DM                 len= 13.05mm vias= 2 (limit <=25.0mm -> PASS)
  /MCU/USB_DP_MCU        len=  2.56mm vias= 0 (limit <= 6.0mm, no vias -> PASS)
  /MCU/USB_DM_MCU        len=  2.56mm vias= 0 (limit <= 6.0mm, no vias -> PASS)
  /MCU/QSPI_SCLK         len=  6.66mm vias= 2 (limit <=25.0mm -> PASS)
  /MCU/QSPI_SD0          len=  5.61mm vias= 2 (limit <=25.0mm -> PASS)
  /MCU/QSPI_SD1          len= 11.10mm vias= 2 (limit <=25.0mm -> PASS)
  /MCU/QSPI_SD2          len= 13.85mm vias= 4 (limit <=25.0mm -> PASS)
  /MCU/QSPI_SD3          len=  5.51mm vias= 2 (limit <=25.0mm -> PASS)
  /MCU/QSPI_SS           len= 13.34mm vias= 2 (limit <=25.0mm -> PASS)
```

### 4. `pcbnew` Zone Piece, Keepout & Exposed-Pad Audit
```text
  Zone 0: name='RP2350 ring' net='+1V1' layer=B.Cu prio=3 pieces=1 areas_mm2=[6.0625] total_mm2=6.0625
  Zone 1: name='vendor GND' net='GND' layer=B.Cu prio=4 pieces=1 areas_mm2=[1.7578] total_mm2=1.7578
  Zone 3: name='RP2350 band' net='+3V3' layer=B.Cu prio=1 pieces=4 areas_mm2=[1.9164, 4.6139, 0.2974, 2.9284] total_mm2=9.7561
  Zone 5: name='vendor /MCU/VREG_LX' net='/MCU/VREG_LX' layer=B.Cu prio=5 pieces=1 areas_mm2=[2.1826] total_mm2=2.1826
  Zone 11: name='vendor +1V1' net='+1V1' layer=B.Cu prio=6 pieces=1 areas_mm2=[2.6354] total_mm2=2.6354
  Zone 13: name='vendor +3V3' net='+3V3' layer=B.Cu prio=7 pieces=1 areas_mm2=[0.5963] total_mm2=0.5963
  RuleArea 18: name='LX cutout L2' layers=['In1.Cu'] bbox=(100.200,96.150)..(101.900,101.700) no_tracks=True no_vias=False no_pour=True
  Zone 19: name='plane GND' net='GND' layer=In1.Cu prio=0 pieces=1 areas_mm2=[928.7825] total_mm2=928.7825
  U1 pad '41' (3.40x3.40mm @ (87.40,103.00) net='GND'): in_pad=0, same_net_within_4mm=5
  U2 pad '41' (3.40x3.40mm @ (112.60,103.00) net='GND'): in_pad=1, same_net_within_4mm=2
  U3 pad '61' (3.40x3.40mm @ (98.60,93.40) net='GND'): in_pad=1, same_net_within_4mm=2
  U5 pad '17' (1.70x1.70mm @ (103.40,106.00) net='GND'): in_pad=2, same_net_within_4mm=5
  BT1 B.CrtYd bbox=(84.56,84.80)..(92.61,95.14); vias inside=29 (all tented; VBAT via @(86.992,89.164) is 0.107mm from BT1.2)
  L1 @ (100.60,100.60); In2.Cu tracks overlapping 2.0x1.6mm body=1: [('VSYS', 0.2)] (+ '+3V3' under Zone 5 VREG_LX)
```

## Independent Fresh-Context Review (`gemini-4-argon-high`)

| ID | Severity | Reviewer Finding | Disposition & Action Taken |
|---|---|---|---|
| `B1` | `BLOCKER` | `COUT` (`Zone 11`) has `0` power spokes to `+1V1` ring (`Zone 0`); `100%` of core `+1V1` current routes through `U3.50` (`VREG_FB`) on `0.20 mm` wire, and `DVDD` spokes are `0.20 mm` wires | **Confirmed — Gate 7 held (`Rev S3D` fix):** Add dedicated `+1V1` power spoke vias from `Zone 11` to `Zone 0` + `0.60 mm` spokes, and isolate `U3.50` (`VREG_FB`) as a pure Kelvin sense trace to `C18.1` (`4.0 mΩ` DC drop quantified in Gate 8). |
| `B2` | `BLOCKER` | `Zone 1` (`vendor GND` / `PGND`) has `0` internal vias and shares its single `0.15 mm` `GND` via `@(102.43, 99.10)` directly with `C17.2` (`CFILT` on `VREG_AVDD`) | **Confirmed — Gate 7 held (`Rev S3D` fix):** Place `2` dedicated `PGND` vias inside `Zone 1` and give `C17.2` its own separate `GND` via (`~30 mV` HF bounce quantified in Gate 8 §3.2). |
| `B3` | `BLOCKER` | `LX cutout L2` is on `In1.Cu` instead of `In2.Cu` (`0.21 mm` under `B.Cu` `U3`/`L1`), leaving `In2.Cu` `+3V3` (`ADC_AVDD` feed) and `VSYS` directly beneath `VREG_LX`/`L1` | **Confirmed — Gate 7 held (`Rev S3D` fix):** Move `LX` cutout to `In2.Cu`, reroute `+3V3`/`VSYS` clear of `L1`/`VREG_LX`, and restore unbroken `GND` on `In1.Cu` (`19–48 mV_pk` spike modeled in Gate 8 §3.2). |
| `B4` | `BLOCKER` | `RP2350` `+3V3` band (`Zone 3`) fractured into `4` pieces (`[1.9164, 4.6139, 0.2974, 2.9284] mm²`) + `11` foreign LED vias inside `U3 ring` (`±2.85 mm`), pinching off `Piece 2` (`U3.44` `ADC_AVDD`) | **Confirmed — Gate 7 held (`Rev S3D` fix):** Expand `RuleArea 2` (`U3 ring vias`) to full `±2.85 mm` and move `+1V1` spokes off `B.Cu` so `Zone 3` fills as `1` whole piece with local `C14` decoupling on `U3.44`. |
| `B5` | `BLOCKER` | `U3.61` (sole RP2350 `GND` pin) has only `1` via & `U5.17` has `2` open vias overlapping `B.Paste` apertures without VIPPO (`U1.41` has `0` in-pad vias) | **Confirmed — Gate 7 held (`Rev S3D` fix):** Place `5` vias strictly inside the `0.80 mm` paste-free `+` cross corridors of `U1.41`, `U2.41`, and `U3.61`, and shift `U5.17`'s `2` vias into its paste-free cross channel. |
| `M1` | `MAJOR` | Single-via power transitions (`1` via vs `3–5` required), `438.0 mΩ` PCB battery loop (`BT1 ↔ U8/U5`), and `0.16–0.20 mm` `VSYS` (`236.7 mΩ` to `U1.5` vs `53.7 mΩ` to `U2.5`) | **Confirmed — Gate 7 held (`Rev S3D` fix):** Parallel `3`-via arrays + `≥ 0.30–0.40 mm` battery/`VSYS` trunks in `Rev S3D` (`GCC ≤ 107` headroom verified down to `V_cell ≈ 3.59 V` in Gate 8). |
| `M2` | `MAJOR` | `USBLC6-2P6` (`U7`) non-inline (`34.55 / 35.87 mm`, `5–6` vias), `USB_DP` (`F.Cu`+`B.Cu`) & `USB_DM` (`In2.Cu`+`B.Cu`) split across layers | **Confirmed — Gate 7 held (`Rev S3D` fix):** Synced `34.55 / 35.87 mm` (`26.0 ps` skew) in [stackup-4l.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/stackup-4l.md); route inline on `B.Cu` in `Rev S3D`. |
| `M3` | `MAJOR` | Tented `VBAT` via `@(86.992, 89.164)` sits `0.107 mm` edge-to-edge from `BT1` Pad `2` (`/Power/BAT_N`), risking an unprotected LiPo dead short if mask/solder bridges | **Confirmed — Gate 7 held (`Rev S3D` fix; bench DMM continuity check before LiPo attach on `Rev S3C`):** Relocate `VBAT` via outside `BT1` pad zone (`≥ 0.35 mm` clearance) in `Rev S3D`. |
| `M4` | `MAJOR` | `U4.8` Flash nearest cap (`C14`) is `8.56 mm` / `4` vias away (`C22` misplaced); `7` caps have `GND` vias `2.13–3.17 mm` away; `QSPI` vias `1.70–4.21 mm` from `GND` vias | **Confirmed — Gate 7 held (`Rev S3D` fix; 1x/2x SPI XIP fallback on `Rev S3C`):** Move `C22` beside `U4.8` and tighten cap/QSPI `GND` return vias in `Rev S3D`. |
| `m1–m3` | `MINOR` | Sparse rim `GND` stitching (`56` `GND` vias, `4.11 mm` `In1.Cu` antipad slot); `86` sub-`40 µm` micro-segments; `nets_check.py --routed` run | **Addressed / queued for `Rev S3D`:** Ran `nets_check.py --rules --routed` above; prune sub-`40 µm` fragments & stitch perimeter `GND` vias in `Rev S3D`. |
| `N1–N2` | `NOTE` | Clean `B.Cu` `0`-via `12 MHz` crystal `Y1` layout; `0` DRC errors/thin joints & verified `L1` 3D chiral polarity on `B.Cu` | **Confirmed.** |
