# Gate 10: Sync and Release — Sunflower `s2-110-usbc`

Status: **`awaiting_signoff`** (Gate 10 requires explicit user sign-off per [SKILL.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/SKILL.md) and [sync-and-release.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/sync-and-release.md); independent review recommends **holding `Rev S3C` for `Rev S3D`**, or ordering a conditional `5–10` board bench prototype lot only with explicit user sign-off on the waivers and assembly/firmware guards below).

## Checklist ([sync-and-release.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/sync-and-release.md), Phase 10)

| Item | Evidence | State |
|---|---|---|
| All earlier gates current (`0`–`9`) | `1–3` `passed`; `0, 4` `awaiting_signoff`; `5–9` `failed` on frozen `Rev S3C` copper/rules/silk (table below) | current (`5–9` held unless waived for `Rev S3C` proto) |
| Sync check passes (`--bom` & `--cpl`) | `sync_check.py`: `206` symbols ↔ `206` footprints, `191` BOM/CPL placements (`0` errors, `0` warnings) | **PASS** |
| DRC / ERC re-run on final files: clean | `kicad-cli sch erc --severity-all` = `0`; `kicad-cli pcb drc --severity-all --schematic-parity` = `0` (`0` opens) | **PASS** |
| Stock re-checked at release | `jlc_parts.py show` (`2026-11-08`): **`34/34`** unique LCSC parts `lifecycle normal` & in stock (`min 531` on `U6`; `L1` = `1,520`) | **PASS** |
| CPL rotation & origin verified for every polarized part / IC | Fixed Bottom-layer mirroring & EasyEDA origins in [export_and_cost.py](file:///home/sequoia/pcb/round-pendant/scripts/sunflower/export_and_cost.py); verified all `191` parts (`BT1` `110.00°`, `J1` `0.00°`, `0.000 mm` origin error) | **PASS** |
| Gerbers reviewed in a separate viewer (`gerbonara` + Chrome) | All `12` layers rendered & reconciled in [gerbers/](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/gerbers/); caught `0` paste on `J1`'s `4` PTH slots in `sunflower-B_Paste.gbp` | **FAIL** (`J1` PTH `B.Paste` + `U3.61`/`U5.17` EP paste vias) |
| `U3` (`RP2350A`) `+1V1` ring & `+3V3` band whole-piece zone check | `+1V1` `RP2350 ring` = **`1` piece (`6.0625 mm²`)** (`0` spokes to `Zone 11`); `+3V3` `RP2350 band` = **`4` pieces (`9.7561 mm²`)** | **FAIL** (`4`-piece `+3V3` band + `0`-spoke `COUT`) |
| Final independent review: no blocking findings | Fresh-context `agy` reviewer (`2026-11-08`): **HOLD for `Rev S3D`** (or conditional `5`-board bench proto with waivers); all doc/bring-up findings fixed | **FAIL** (copper/DFM blockers held for user decision) |
| Bring-up plan written & linked from `index.html` | [bringup-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/bringup-s2-110-usbc.md) + [bringup-map-bottom.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/bringup-map-bottom.png), linked in [index.html](file:///home/sequoia/pcb/round-pendant/index.html) | **PASS** |
| Git tagged (`sunflower-s2-110-usbc-revS3C`) | Deferred until supervising commit + user release sign-off (per workspace rules: do not commit/tag yet) | deferred |
| **User approves release** | Listed in §7 below and in [status.json](file:///home/sequoia/pcb/round-pendant/design/status.json) (`s2-110-usbc-release`) | **`awaiting_signoff`** |

### Summary of Earlier Gates (`0`–`9`)

| Gate | File | State | Summary |
|---|---|---|---|
| 0 — Intent | [phase0.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase0.md) | `awaiting_signoff` | [intent-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/intent-s2-110-usbc.md) complete; awaits user sign-off on `BT1` spacer, `403535` C-rate, `ADC4` `GCC` caps, `B.SilkS` identity |
| 1 — Parts | [phase1.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase1.md) | `passed` | `34/34` unique LCSC parts audited, `lifecycle normal`, in stock (`sources.csv` passive rows waived for `Rev S3C`) |
| 2 — Schematic | [phase2.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase2.md) | `passed` | `0` ERC violations across 5 sheets; `Q2`/`U8` polarity proven; `sch_gen.py` style, `C35 = 100 nF`, `BT1` `MP` nails waived |
| 3 — Net Spec | [phase3.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase3.md) | `passed` | `nets_check.py --routed` `PASS` (`0` errors, `109` rows in [nets-sunflower-s2-110-usbc.csv](file:///home/sequoia/pcb/round-pendant/design/nets-sunflower-s2-110-usbc.csv)) |
| 4 — Board Brief | [phase4.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase4.md) | `awaiting_signoff` | [brief-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/brief-s2-110-usbc.md) + exact `B.Fab` [floorplan-s2-110-usbc.svg](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/floorplan-s2-110-usbc.svg); awaits user sign-off |
| 5 — Stackup & Rules | [phase5.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase5.md) | `failed` | `In1.Cu` `GND` (`1.29 mm` from `B.Cu`) vs `In2.Cu` signals (`0.21 mm` from `B.Cu`); `LX cutout L2` on `In1.Cu`; `netclass_assignments: null` |
| 6 — Placement | [phase6.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase6.md) | `failed` | `U4.8` `8.56 mm` from `C14` (`C22` misplaced); `U3.61` (`1`) & `U5.17` (`2`) vias in `B.Paste`; `29` vias in `BT1` Molex keepout; `U8` `29.1 mm` from `BT1` |
| 7 — Routing | [phase7.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase7.md) | `failed` | `0` opens / `0` DRC / `0` `copper_audit` / `0` `pad_joints`, **but** `Zone 11` (`COUT`) `0` spokes (`+1V1` via `U3.50` `VREG_FB`), shared `CFILT`/`PGND` via, `4`-piece `+3V3` band, `0.107 mm` `VBAT` via to `BT1.2` |
| 8 — Simulation | [phase8.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase8.md) | `failed` | [sim/README.md](file:///home/sequoia/pcb/round-pendant/design/sim/sunflower-s2-110-usbc/README.md): `U4.8` `312–554 mV` 4-bit QSPI SSO droop (`1x/2x` SPI safe); `ADC_AVDD` `19–48 mV_pk` `LX` spike; `71.7–93 °C` uncapped thermal rise |
| 9 — Silkscreen | [phase9.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase9.md) | `failed` | `0` silk-over-pad errors, **but** `BT1` `+`/`-` & `J1` `USB 5V` hidden under connector bodies, `5` QFNs/LGAs missing `B.SilkS` pin-1 dots, silk over open vias |

---

## 1. Release Outputs & Order Specification

- **Current release set (`hw/sunflower/s2-110-usbc/fab/`):**
  - [sunflower-s2-110-usbc-gerbers.zip](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/fab/sunflower-s2-110-usbc-gerbers.zip) (11 Gerber X2 files + `sunflower.drl` + `sunflower-job.gbrjob`)
  - [bom-jlcpcb.csv](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/fab/bom-jlcpcb.csv) (`35` BOM lines = `34` unique LCSC PNs, `191` placements)
  - [cpl-jlcpcb.csv](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/fab/cpl-jlcpcb.csv) (`191` placements: `111` `Top`, `80` `Bottom`, Bottom-mirrored & EasyEDA origin-corrected)
  - Stale `01:37` `2026-11-07` KiCad Fabrication Toolkit folder moved aside to `hw/sunflower/s2-110-usbc/production-stale-2026-11-07-0137/`.
- **Drawings, renders & 3D (`design/renders/sunflower-s2-110-usbc/` & `viewer/`):**
  - [schematic.pdf](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/schematic.pdf), [assembly-top.pdf](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/assembly-top.pdf) (≈4:1 on A4), [assembly-bottom.pdf](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/assembly-bottom.pdf) (≈4:1 on A4), [3d-top.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/3d-top.png), [3d-bottom.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/3d-bottom.png), [cpl-check-top.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/cpl-check-top.png), [cpl-check-bottom.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/cpl-check-bottom.png), and `viewer/sunflower-s2-110-usbc/board.glb`.
- **Mandatory JLCPCB order settings ([stackup-4l.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/stackup-4l.md)):**
  - Stackup code: **`JLC04161H-7628`** (`4` layers, `1.6 mm`, `1 oz` outer / `0.5 oz` inner)
  - Surface finish: **`ENIG 1U"`** (overrides `.gbrjob` default `HAL SnPb` for `0.40 mm`-pitch QFNs & `1.0 × 1.0 mm` X2-SON `U6`)
  - Solder mask: **Green LPI** (`0.10 mm` min dam; matte black violates `0.40 mm`-pitch QFN mask-bridge rules); vias: **Tented**
  - PCBA reflow order: **`Pass 1 = B.Cu` (Bottom), `Pass 2 = F.Cu` (Top, peak `≤ 245 °C`)** (`Q2` `XYC-PT19C-L1` allows **1× reflow pass max**); **NO `F.Cu` wave or hand soldering on `J1`** (`0.18–0.29 mm` from `D10`/`D104`/`D110`).

---

## 2. Sync, ERC, DRC & Live Stock Verification

### 2.1 Schematic ↔ PCB ↔ BOM ↔ CPL Sync (`sync_check.py`)

```text
$ python3 .claude/skills/pcb-design/scripts/sync_check.py hw/sunflower/s2-110-usbc \
    --bom hw/sunflower/s2-110-usbc/fab/bom-jlcpcb.csv \
    --cpl hw/sunflower/s2-110-usbc/fab/cpl-jlcpcb.csv
sync_check: /home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc
  schematic sunflower.kicad_sch: 206 symbols (0 excluded from board)
  board sunflower.kicad_pcb: 206 footprints (0 board-only)
  BOM bom-jlcpcb.csv: 191 designators
  CPL cpl-jlcpcb.csv: 191 placements
  191 parts to build; required fields: LCSC
  stock not checked: re-check every LCSC part at release (phase 10)

  PASS: 0 errors, 0 warnings
```

*(The `15` unplaced schematic/board footprints are the `14` bare test pads `TP1..TP8, TP11..TP16` plus net-tie `NT1`.)*

### 2.2 Final ERC & DRC (`kicad-cli --severity-all`)

```text
$ kicad-cli sch erc --severity-all --format json -oerc-s2-110-usbc.json hw/sunflower/s2-110-usbc/sunflower.kicad_sch
{
    "kicad_version": "9.0.8",
    "sheets": [ "/", "/Power/", "/MCU/", "/Driver 1 and matrix/", "/Driver 2 and matrix/" ],
    "violations": 0 across all 5 sheets
}

$ ~/.claude/bin/reserve -c 4 -l "s2-110-usbc gates" -- \
    kicad-cli pcb drc --severity-all --schematic-parity --format json \
    -odrc-s2-110-usbc.json hw/sunflower/s2-110-usbc/sunflower.kicad_pcb
{
    "kicad_version": "9.0.8",
    "schematic_parity": [],
    "source": "sunflower.kicad_pcb",
    "unconnected_items": [],
    "violations": []
}
```

### 2.3 Live JLCPCB Stock Re-Check (`2026-11-08`, `34/34` Unique LCSC Parts)

```text
$ python3 .claude/skills/pcb-design/scripts/jlc_parts.py show C177225 C52923 C86295 C19702 C1525 C23733 C1548 C965840 C165948 C42411119 C236117 C2693594 C25905 C25744 C25784 C25891 C25741 C25076 C25105 C25100 C11702 C25900 C25776 C25768 C2828254 C5137654 C42411118 C190862 C15220 C2860046 C15999 C669687 C189624 C20625731
C177225 532610271 (MOLEX, SMD,P=1.25mm,Surface Mount,Right Angle): extended, JLC stock 24078, lifecycle normal, checked 2026-11-08
C52923 CL05A105KA5NQNC (Samsung Electro-Mechanics, 0402): basic, JLC stock 11484815, lifecycle normal, checked 2026-11-08
C86295 CL10A226MP8NUNE (Samsung Electro-Mechanics, 0603): extended, JLC stock 629210, lifecycle normal, checked 2026-11-08
C19702 CL10A106KP8NNNC (Samsung Electro-Mechanics, 0603): basic, JLC stock 10258539, lifecycle normal, checked 2026-11-08
C1525 CL05B104KO5NNNC (Samsung Electro-Mechanics, 0402): basic, JLC stock 34141448, lifecycle normal, checked 2026-11-08
C23733 CL05A475MP5NRNC (Samsung Electro-Mechanics, 0402): basic, JLC stock 1027471, lifecycle normal, checked 2026-11-08
C1548 0402CG150J500NT (FH, 0402): basic, JLC stock 1202179, lifecycle normal, checked 2026-11-08
C965840 XL-1615RGBC-RF (XINGLIGHT, SMD-4P,1.6x1.5mm): extended, JLC stock 715082, lifecycle normal, checked 2026-11-08
C165948 TYPE-C-31-M-12 (Korean Hroparts Elec, SMD): extended, JLC stock 312252, lifecycle normal, checked 2026-11-08
C42411119 AOTA-B201610S3R3-101-T (ABRACON, 0806): extended, JLC stock 1520, lifecycle normal, checked 2026-11-08
C236117 NTZD3155CT1G (onsemi, SOT-563): extended, JLC stock 7923, lifecycle normal, checked 2026-11-08
C2693594 XYC-PT19C-L1 (NEWOPTO, 0603): extended, JLC stock 25178, lifecycle normal, checked 2026-11-08
C25905 0402WGF5101TCE (UNI-ROYAL, 0402): basic, JLC stock 4483839, lifecycle normal, checked 2026-11-08
C25744 0402WGF1002TCE (UNI-ROYAL, 0402): basic, JLC stock 22721767, lifecycle normal, checked 2026-11-08
C25784 0402WGF3001TCE (UNI-ROYAL, 0402): extended, JLC stock 646696, lifecycle normal, checked 2026-11-08
C25891 0402WGF3601TCE (UNI-ROYAL, 0402): extended, JLC stock 494270, lifecycle normal, checked 2026-11-08
C25741 0402WGF1003TCE (UNI-ROYAL, 0402): basic, JLC stock 8748432, lifecycle normal, checked 2026-11-08
C25076 0402WGF1000TCE (UNI-ROYAL, 0402): basic, JLC stock 11716767, lifecycle normal, checked 2026-11-08
C25105 0402WGF330JTCE (UNI-ROYAL, 0402): basic, JLC stock 3819439, lifecycle normal, checked 2026-11-08
C25100 0402WGF270JTCE (UNI-ROYAL, 0402): extended, JLC stock 704688, lifecycle normal, checked 2026-11-08
C11702 0402WGF1001TCE (UNI-ROYAL, 0402): basic, JLC stock 33681035, lifecycle normal, checked 2026-11-08
C25900 0402WGF4701TCE (UNI-ROYAL, 0402): basic, JLC stock 15709011, lifecycle normal, checked 2026-11-08
C25776 0402WGF3002TCE (UNI-ROYAL, 0402): extended, JLC stock 5297189, lifecycle normal, checked 2026-11-08
C25768 0402WGF2202TCE (UNI-ROYAL, 0402): basic, JLC stock 1043461, lifecycle normal, checked 2026-11-08
C2828254 EVQP7J01P (PANASONIC, SMD,3.6x3.5mm): extended, JLC stock 6887, lifecycle normal, checked 2026-11-08
C5137654 AW20198QNR (AWINIC(Shanghai Awinic Tech), QFN-40L(5x5)): extended, JLC stock 6055, lifecycle normal, checked 2026-11-08
C42411118 RP2350A (Raspberry Pi, QFN-60-EP(7x7)): extended, JLC stock 3175, lifecycle normal, checked 2026-11-08
C190862 W25Q128JVPIQ (Winbond, WSON-8-EP(5x6)): extended, JLC stock 12788, lifecycle normal, checked 2026-11-08
C15220 BQ24073RGTR (TI, QFN-16-EP(3x3)): extended, JLC stock 762, lifecycle normal, checked 2026-11-08
C2860046 TPS7A0233PDQNR (TI, X2-SON-4-EP(1x1)): extended, JLC stock 531, lifecycle normal, checked 2026-11-08
C15999 USBLC6-2P6 (ST, SOT-666-6): extended, JLC stock 20214, lifecycle normal, checked 2026-11-08
C669687 XB9901A (XySemi, DFNFC-6(1.4x1.8)): extended, JLC stock 2947, lifecycle normal, checked 2026-11-08
C189624 LIS2DW12TR (ST, LGA-12(2x2)): extended, JLC stock 51892, lifecycle normal, checked 2026-11-08
C20625731 ABM8-272-T3 (ABRACON, SMD3225-4P): extended, JLC stock 9607, lifecycle normal, checked 2026-11-08
```

---

## 3. CPL Rotation & Pick-Origin Audit (`191` Placements)

### 3.1 Bug Caught & Fixed in `scripts/sunflower/export_and_cost.py`

Auditing the previous `cpl-jlcpcb.csv` against all `34` LCSC EasyEDA footprint JSONs caught two silent PCBA assembly bugs in [export_and_cost.py](file:///home/sequoia/pcb/round-pendant/scripts/sunflower/export_and_cost.py#L185-L218):
1. **Missing Bottom-layer angle reflection:** `export_and_cost.py` computed `(rot_kicad + rot_off) % 360` on both sides instead of `(180.0 - rot_kicad + rot_off) % 360` on `Bottom`, mis-rotating `BT1` (`70°` vs **`110°`**), `J1` (`180°` vs **`0°`**), `U1/U2` (`270°` vs **`0°`**), `U4` (`270°` vs **`0°`**), `Q1` (`90°` vs **`270°`**), `U9` (`90°` vs **`270°`**), and `SW1/SW2` (`291°/69°` vs **`249°/111°`**).
2. **Missing EasyEDA pick-origin offsets on `BT1` and `J1`:** EasyEDA `C177225` (`BT1`) places its origin `+0.950 mm` in local `+Y` from KiCad's `Molex_PicoBlade_53261-0271` origin (`Δ = (-0.8927, -0.3249) mm` at `-110°`), and EasyEDA `C165948` (`J1`) places its origin `+1.571 mm` in local `+Y` from KiCad's `HRO_TYPE-C-31-M-12` origin (`Δ = (0.0000, +1.5710) mm` at `180°`).

Updated [export_and_cost.py](file:///home/sequoia/pcb/round-pendant/scripts/sunflower/export_and_cost.py), re-exported [fab/](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/fab), verified pad-for-pad across all `191` parts, and rendered visual overlays in [cpl-check-top.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/cpl-check-top.png) and [cpl-check-bottom.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/cpl-check-bottom.png):

```text
CPL total rows: 191
Max pad-to-pad overlay error across ALL 191 parts: 0.3127 mm

Polarized / IC / Connector / LED sample CPL verification table:
Ref    MPN                    LCSC      Layer    KiRot   CPL_MidX   CPL_MidY  CPLRot   PadErr
BT1    PicoBlade 2P           C177225   Bottom  -110.0    87.7073   -89.4751  110.00   0.000mm
C1     1u                     C52923    Bottom   180.0   102.9235  -109.6870    0.00   0.060mm
C16    4.7u                   C23733    Bottom     0.0   100.6000   -98.0000  180.00   0.095mm
D1     RGB                    C965840   Top        0.0   100.0000  -100.0000  180.00   0.135mm
D2     RGB                    C965840   Top        0.0    98.9500  -103.9000  180.00   0.135mm
D55    RGB                    C965840   Top        0.0    97.3000   -83.4000  180.00   0.135mm
D56    RGB                    C965840   Top        0.0   100.2000   -97.7000  180.00   0.135mm
D110   RGB                    C965840   Top        0.0   105.8500  -115.1500  180.00   0.135mm
J1     USB-C                  C165948   Bottom   180.0   100.0000  -114.0290    0.00   0.000mm
L1     3.3u                   C42411119 Bottom     0.0   100.6000  -100.6000  180.00   0.300mm
Q1     NTZD3155C              C236117   Bottom   180.0    91.8000  -112.4000  270.00   0.010mm
Q2     XYC-PT19C-L1           C2693594  Top        0.0   100.0000   -81.8000    0.00   0.000mm
SW1    USER / WAKE            C2828254  Bottom   -69.0   116.1509   -93.8002  249.00   0.103mm
SW2    BOOTSEL                C2828254  Bottom    69.0    83.8491   -93.8002  111.00   0.103mm
U1     AW20198QNR             C5137654  Bottom    90.0    87.4000  -103.0000    0.00   0.199mm
U2     AW20198QNR             C5137654  Bottom    90.0   112.6000  -103.0000    0.00   0.199mm
U3     RP2350A                C42411118 Bottom     0.0    98.6000   -93.4000  180.00   0.138mm
U4     W25Q128JVPIQ           C190862   Bottom    90.0    97.2000  -105.4000    0.00   0.313mm
U5     BQ24073                C15220    Bottom     0.0   103.4000  -106.0000  180.00   0.037mm
U6     TPS7A0233              C2860046  Bottom   180.0    93.9000  -100.4000    0.00   0.000mm
U7     USBLC6-2P6             C15999    Bottom   180.0   107.0296  -110.6809  180.00   0.200mm
U8     XB9901A                C669687   Bottom   180.0   106.4528  -112.7886    0.00   0.000mm
U9     LIS2DW12               C189624   Bottom   180.0   104.4000   -86.2000  270.00   0.113mm
Y1     12MHz                  C20625731 Bottom     0.0    97.3000   -85.2000  180.00   0.000mm
```

*(Note: `PadErr = 0.300 mm` on `L1` and `0.313 mm` on `U4` are pure pad-toe length differences between KiCad and EasyEDA footprints; both parts have `(0.000, 0.000)` centroid offset and `0.00°` Pin-1 rotation error.)*

| Ref(s) | LCSC | Layer | KiCad `(X, Y)` / Rot | CPL `(Mid X, Mid Y)` / Rot | Pin-1 / Polarity & Origin Verification |
|---|---|---|---|---|---|
| `BT1` | `C177225` | `Bottom` | `(88.600, 89.800)` / `-110°` (`250°`) | `(87.7073, -89.4751)` / **`110.00°`** | **PASS (`0.000 mm`):** `+0.950 mm` EasyEDA origin shift along `-110°` exact; mouth faces inward `+20°` toward `U3`; Pin 1 (`VBAT`) on upper/northerly signal pad `(86.56, 88.39)` |
| `J1` | `C165948` | `Bottom` | `(100.000, 115.600)` / `180°` | `(100.0000, -114.0290)` / **`0.00°`** | **PASS (`0.000 mm`):** `-1.5710 mm` Y-origin shift exact; tongue overhangs South `+Y` rim; all 12 SMD signal/power fingers match USB-C receptacle pinout (`A5/B5` `CC1/CC2`, `A4B9/B4A9` `VBUS`) |
| `D1..D110` | `C965840` | `Top` | `(100.0, 100.0)..` / `0°` | `(100.0, -100.0)..` / **`180.00°`** | **PASS:** `+180°` EasyEDA offset aligns Pin 1 (`R`) Top-Left and Pin 2 (`Anode +`) Bottom-Left across all `110` RGB LEDs |
| `Q2` | `C2693594` | `Top` | `(100.000, 81.800)` / `0°` | `(100.0000, -81.8000)` / **`0.00°`** | **PASS (`0.000 mm`):** Pin 1 (`Collector` = `/MCU/LIGHT_PWR`) on West (`-X`) pad matching `F.SilkS` dot |
| `U1`, `U2` | `C5137654` | `Bottom` | `(87.4 / 112.6, 103.0)` / `90°` | `(87.4 / 112.6, -103.0)` / **`0.00°`** | **PASS:** EasyEDA `-BL` at `0°` places Pin 1 (`SW1`) Bottom-Left in `B.Cu` view |
| `U3` | `C42411118` | `Bottom` | `(98.600, 93.400)` / `0°` | `(98.6000, -93.4000)` / **`180.00°`** | **PASS:** EasyEDA `-TL` at `180°` places `U3.1` Bottom-Right (`21/22` `Y1` North, `46..60` reg/USB/QSPI South) |
| `U4` | `C190862` | `Bottom` | `(97.200, 105.400)` / `90°` | `(97.2000, -105.4000)` / **`0.00°`** | **PASS:** EasyEDA `-BL` at `0°` places `U4.1` (`~CS`) Bottom-Left and `U4.8` (`VCC`) Top-Left |
| `U5` | `C15220` | `Bottom` | `(103.400, 106.000)` / `0°` | `(103.4000, -106.0000)` / **`180.00°`** | **PASS:** EasyEDA `-TL` at `180°` places `U5.1` (`TS`) Bottom-Right |
| `U6` | `C2860046` | `Bottom` | `(93.900, 100.400)` / `180°` | `(93.9000, -100.4000)` / **`0.00°`** | **PASS (`0.000 mm`):** EasyEDA `-TL` at `0°` places `U6.1` (`OUT` → `C4`) Top-Left |
| `U7` | `C15999` | `Bottom` | `(107.030, 110.681)` / `180°` | `(107.0296, -110.6809)` / **`180.00°`** | **PASS:** EasyEDA `-BR` at `180°` places `U7.1` Top-Left, matching `B.SilkS` dot |
| `U8` | `C669687` | `Bottom` | `(106.453, 112.789)` / `180°` | `(106.4528, -112.7886)` / **`0.00°`** | **PASS (`0.000 mm`):** EasyEDA `-BL` at `0°` places `U8.1..3` (`VM`/`GND` bar) Bottom, `U8.4..5` (`BAT_N` bar) Top-Right, `U8.6` (`VDD`) Top-Left |
| `U9` | `C189624` | `Bottom` | `(104.400, 86.200)` / `180°` | `(104.4000, -86.2000)` / **`270.00°`** | **PASS:** EasyEDA `-BL` at `270°` places `U9.1` (`SCL`) Top-Left |
| `Q1` | `C236117` | `Bottom` | `(91.800, 112.400)` / `180°` | `(91.8000, -112.4000)` / **`270.00°`** | **PASS:** EasyEDA `-BL` at `270°` places `Q1.1` (`GND`) Top-Left |
| `L1`, `Y1` | `C42411119`, `C20625731` | `Bottom` | `0°` | **`180.00°`** | **PASS:** `L1` start dot on West (`+1V1`) pad; `Y1.1` (`XIN`) Top-Right (`2, 4` `GND`) |
| `SW1`, `SW2` | `C2828254` | `Bottom` | `−69° / +69°` | **`249.00° / 111.00°`** | **PASS:** Symmetric (`249° + 111° = 360°`), plungers project `+0.40 mm` outward past NE/NW rim |

---

## 4. Independent Gerber & Excellon Review (`gerber_render.py`)

```text
$ python3 .claude/skills/pcb-design/scripts/gerber_render.py \
    hw/sunflower/s2-110-usbc/fab/gerbers -o design/renders/sunflower-s2-110-usbc/gerbers
gerber_render: hw/sunflower/s2-110-usbc/fab/gerbers (board sunflower)
  top_silk             sunflower-F_Silkscreen.gto        1476 objects
  top_paste            sunflower-F_Paste.gtp              442 objects
  top_mask             sunflower-F_Mask.gts               448 objects
  top_copper           sunflower-F_Cu.gtl                3034 objects
  inner_1_copper       sunflower-In1_Cu.g1                642 objects
  inner_2_copper       sunflower-In2_Cu.g2               1587 objects
  bottom_copper        sunflower-B_Cu.gbl                2599 objects
  bottom_mask          sunflower-B_Mask.gbs               387 objects
  bottom_paste         sunflower-B_Paste.gbp              379 objects
  bottom_silk          sunflower-B_Silkscreen.gbo        1052 objects
  drill_sunflower      sunflower.drl                      643 objects
  outline              sunflower-Edge_Cuts.gm1              2 objects
  12 layer images in design/renders/sunflower-s2-110-usbc/gerbers
```

### Excellon X2 Drill Header (`sunflower.drl`)

```text
M48
; #@! TF.FileFunction,MixedPlating,1,4
; #@! TA.AperFunction,Plated,PTH,ViaDrill
T1C0.150
; #@! TA.AperFunction,Plated,PTH,ComponentDrill
T2C0.600
; #@! TA.AperFunction,NonPlated,NPTH,ComponentDrill
T3C0.650
```

- **Layer-by-layer object reconciliation ([gerbers/](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/gerbers/)):**
  - `outline` (`2` objects): Closed `Ø38.000 mm` circle (`2 × 180°` arcs), `0` gaps.
  - `drill_sunflower` (`643` objects): `637` vias (`T1C0.150` PTH) + `4` `J1` shield slots (`T2C0.600` PTH) + `2` `J1` locating pegs (`T3C0.650` explicitly tagged `NonPlated,NPTH,ComponentDrill`).
  - `top_paste` (`442`) & `top_mask` (`448`): `110 × 4 (LEDs) + 2 (Q2) = 442` SMD paste pads + `4` `J1` PTH + `2` `J1` NPTH = `448` mask openings; all `637` vias tented.
  - `bottom_mask` (`387`) & `bottom_paste` (`379`): `387` mask openings minus `20` paste-free openings (`14` `TP*`, `4` `J1` PTH slots, `2` `J1` NPTH pegs) plus `12` (`2×2` split EP paste windows on `U1`, `U2`, `U3`, `U5`) = `379` paste apertures (`0` mask/paste on `NT1`).
  - **New Gate 10 Gerber DFM catch (`J1` PTH slots missing `B.Paste`):** [bottom_paste.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/gerbers/bottom_paste.png) has **`0` paste apertures** on `J1`'s `4` PTH shield slots (`±4.32, +12.47/+16.65`), while `J1`'s `F.Cu` annular rings sit **`0.18–0.29 mm`** from `D10`, `D104`, and `D110`. Post-SMT `F.Cu` wave/hand soldering would melt adjacent LEDs, whereas SMT-only reflow leaves `J1`'s mechanical shield legs unsoldered unless manually tacked on the outer `B.Cu` slot edges (`Rev S3C`) or replaced by full-SMT `TYPE-C-31-M-22` (`C530612`) / `B.Paste` pin-in-paste (`Rev S3D`).

---

## 5. `U3` (`RP2350A`) `+1V1` Ring & `+3V3` Band Zone Piece-Count Check

Checked directly on `sunflower.kicad_pcb` via `pcbnew` (`scratch/checks/pcbnew_routing_audit.txt`):

```text
=== ZONE & KEEPOUT AUDIT (pcbnew) ===
  Zone 0: name='RP2350 ring' net='+1V1' layer=B.Cu prio=3 pieces=1 areas_mm2=[6.0625] total_mm2=6.0625
  Zone 1: name='vendor GND' net='GND' layer=B.Cu prio=4 pieces=1 areas_mm2=[1.7578] total_mm2=1.7578
  Zone 3: name='RP2350 band' net='+3V3' layer=B.Cu prio=1 pieces=4 areas_mm2=[1.9164, 4.6139, 0.2974, 2.9284] total_mm2=9.7561
  Zone 5: name='vendor /MCU/VREG_LX' net='/MCU/VREG_LX' layer=B.Cu prio=5 pieces=1 areas_mm2=[2.1826] total_mm2=2.1826
  Zone 11: name='vendor +1V1' net='+1V1' layer=B.Cu prio=6 pieces=1 areas_mm2=[2.6354] total_mm2=2.6354
  Zone 13: name='vendor +3V3' net='+3V3' layer=B.Cu prio=7 pieces=1 areas_mm2=[0.5963] total_mm2=0.5963
  RuleArea 18: name='LX cutout L2' layers=['In1.Cu'] bbox=(100.200,96.150)..(101.900,101.700) no_tracks=True no_vias=False no_pour=True
  Zone 19: name='plane GND' net='GND' layer=In1.Cu prio=0 pieces=1 areas_mm2=[928.7825] total_mm2=928.7825
```

- **`+1V1` `RP2350 ring` (`Zone 0`):** Fills as **`1` contiguous whole piece (`6.0625 mm²`)** around `U3.61` with `0` foreign vias inside `RuleArea 2` — **however**, `Zone 11` (`vendor +1V1` on `C18` `COUT`, `2.6354 mm²`) has **`0` power spokes** to `Zone 0`, forcing `100%` of core `+1V1` current through `U3.50` (`VREG_FB` sense finger; Gate 7 `BLOCKER`).
- **`+3V3` `RP2350 band` (`Zone 3`):** **Splits into `4` disconnected `B.Cu` islands** (`[1.9164, 4.6139, 0.2974, 2.9284] mm²`, `9.7561 mm²` total) carved by `11` foreign vias + signal escapes inside `U3 ring` (`0` opens only because `In2.Cu` routes stitch the islands, routing `C14` / `U3.44` `ADC_AVDD` across `In2.Cu` directly beneath `VREG_LX`/`L1`).

---

## 6. Final Independent Review (`2026-11-08`, fresh-context `agy` reviewer)

Reviewer inspected only [intent-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/intent-s2-110-usbc.md), [brief-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/brief-s2-110-usbc.md), [stackup-4l.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/stackup-4l.md), [bringup-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/bringup-s2-110-usbc.md), [sim/README.md](file:///home/sequoia/pcb/round-pendant/design/sim/sunflower-s2-110-usbc/README.md), `design/parts/*.md`, [nets-sunflower-s2-110-usbc.csv](file:///home/sequoia/pcb/round-pendant/design/nets-sunflower-s2-110-usbc.csv), `fab/{bom,cpl}-jlcpcb.csv`, all renders/gerbers, ERC/DRC/sync/stock outputs, `phase0.md`..`phase9.md`, and [sync-and-release.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/sync-and-release.md).

### Reviewer Answers to the Three Phase 10 Release Questions

1. **Would you send this to fab?** **HOLD for `Rev S3D`** (`7` of `10` prior gates are not passed, and all copper/DFM blockers are CAD-only fixes with zero new part lead time). If schedule-critical for a `5`-board firmware/mechanical bench bring-up, `Rev S3C` can be ordered **only** under the conditional waiver & assembly/firmware guards in §7 Option A.
2. **Highest-risk items on this board (ranked):**
   1. Thermal / LiPo charge runaway (`71.7 °C` battery / `86–93 °C` charging at `GCC = 255` with fixed `R3 = 10 kΩ` `TS`) unless firmware gates `GCC ≤ 105` (battery) and `GCC ≤ 9` CC / `≤ 24` CV on `(PGOOD == 0) || (CHG == 0)`.
   2. Unprotected LiPo short & reverse-plugging hazards at `BT1` (`0.107 mm` tented `VBAT` via to `BT1.2` `BAT_N`, `29` vias in Molex keepout, occluded `+`/`-` silk, `U8` `29.1 mm` away).
   3. `J1` PTH shield slots missing `B.Paste` vs `0.18–0.29 mm` `F.Cu` clearance to `D10`/`D104`/`D110`.
   4. `U4` (`W25Q128JVPIQ`) `8.56 mm` decoupling loop (`312–554 mV` 4-bit QSPI SSO droop → cap `Rev S3C` XIP to `1x/2x` SPI `≤ 50–66 MHz`).
   5. `Q2` (`XYC-PT19C-L1`) `1`-reflow-pass ceiling (`Pass 1 = B.Cu`, `Pass 2 = F.Cu ≤ 245 °C`).
   6. `U5.17` (`2`) & `U3.61` (`1`) open vias in `B.Paste` + `U3` regulator/plane coupling (`COUT` `0` spokes, shared `CFILT`/`PGND` via, `In2.Cu` `+3V3` under `L1`/`VREG_LX`).
   7. Rear mechanical stackup (`BT1` inward mating `3.02 mm` to `C9`, `0.05 mm` Kapton + `≥ 2.4 mm` spacer over `3.26 mm` `J1` & `3.40 mm` mated `BT1`).
3. **Anything in `intent-s2-110-usbc.md` or `bringup-s2-110-usbc.md` unmet or mismatched?** All doc/bring-up discrepancies flagged by the reviewer were fixed immediately (table below); copper/CAD items (`R7`, `R8` 4-bit QSPI, `403535` datasheet) remain open for user decision.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| `BLOCKER-1` | BLOCKER | `sunflower-B_Paste.gbp` omits paste on `J1`'s `4` PTH shield slots while `F.Cu` rings sit `0.18–0.29 mm` from `D10`/`D104`/`D110` | Documented in [brief-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/brief-s2-110-usbc.md), [intent-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/intent-s2-110-usbc.md), [bringup-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/bringup-s2-110-usbc.md), and §7 below (`Rev S3C`: forbid `F.Cu` soldering + microscope-tack outer `B.Cu` slot edges; `Rev S3D`: switch to full-SMT `TYPE-C-31-M-22` `C530612`) |
| `BLOCKER-2..4` | BLOCKER | Upheld Gate 5–9 copper/placement/DFM blockers (`U4.8` `C22`, `COUT` `0` spokes, `CFILT`/`PGND` via, `In2.Cu` under `LX`, `4`-piece `+3V3` band, `U3.61`/`U5.17` EP paste vias, `BT1`/`U8` hazards) | Held (`phase5`–`phase9` remain `failed`); user chooses `Rev S3C` bench waivers vs `Rev S3D` respin in §7 |
| `BLOCKER-5` | BLOCKER | `intent-s2-110-usbc.md` `R19` (L36) & `Environment` (L77) still said `GCC ≤ 115–128` / `≤ 48` on `~{CHG} = 0`, contradicting Phase 8 thermal sim (`GCC ≤ 105` / `≤ 9` CC / `≤ 24` CV on `PGOOD == 0 \|\| CHG == 0`) | Fixed in [intent-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/intent-s2-110-usbc.md), [brief-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/brief-s2-110-usbc.md), and [phase0.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase0.md) |
| `MAJOR-1` | MAJOR | `bringup-s2-110-usbc.md` specified `TP1` (`VSYS`) USB window as `4.35–4.45 V` instead of `BQ24073` datasheet `4.30–4.50 V` (`charger.md`) | Fixed in [bringup-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/bringup-s2-110-usbc.md) (`4.30–4.50 V`, `4.40 V` typ) |
| `MAJOR-2` | MAJOR | `bringup-s2-110-usbc.md` Step 1.2 instructed cold-probing `0.40 mm`-pitch QFN pad `U3.31` (`GPIO19`) | Fixed in [bringup-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/bringup-s2-110-usbc.md): removed QFN pin probe (`NT1` is verified cleanly in firmware Smoke-Test Step 1 `ID = 6`) |
| `MINOR-1..4` | MINOR | `XL-1615RGBC-RF` called `MSL-5a` instead of `MSL-3`; `R17` (`≤ 85 µA` typ sleep) bench check missing; `TP2` silk landmark (`under LIPO 403535, N of 1V1`) & `B.Cu` X-mirror handedness note; `phase9.md` L86 `GND`/`VM` bar wording | Fixed across [intent-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/intent-s2-110-usbc.md), [brief-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/brief-s2-110-usbc.md), [bringup-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/bringup-s2-110-usbc.md), and [phase9.md](file:///home/sequoia/pcb/round-pendant/design/gates/sunflower-s2-110-usbc/phase9.md) |

---

## 7. Decisions Required From User for Gate 10 Sign-Off

1. **Release path (`Rev S3C` bench prototype vs `Rev S3D` layout respin):**
   - **Option A — Order `5–10` `Rev S3C` bench prototypes from `hw/sunflower/s2-110-usbc/fab/`:** Formally waive Gates 5–9 and Gate 10's `J1` paste finding for bench bring-up, ordering **`JLC04161H-7628` + `ENIG 1U"` + green LPI mask + tented vias** with PCBA instruction **`Pass 1 = B.Cu`, `Pass 2 = F.Cu (≤ 245 °C)`, NO `F.Cu` wave/hand soldering on `J1`**, then manually tacking `J1`'s outer `B.Cu` slot edges under a microscope, verifying `BT1.1–BT1.2 > 1 MΩ` before battery attach, pre-mating `BT1` upward (`30–45°`) + `0.05 mm` Kapton + `≥ 2.4 mm` rear spacer, and enforcing firmware guards (`1x/2x` SPI XIP `≤ 50–66 MHz`, `ADC4` `GCC ≤ 105` battery / `≤ 9` CC / `≤ 24` CV on `PGOOD == 0 || CHG == 0`, `GPIO4/5` `12 mA` + `GCR = 0xB9`).
   - **Option B — Hold PCBA order and spin `Rev S3D` first (Recommended by reviewer):** Swap `J1` to full-SMT `TYPE-C-31-M-22` (`C530612`), tie `Zone 11` (`COUT`) directly to `+1V1` `RP2350 ring`, give `C17` (`CFILT`) a dedicated `GND` via, move `GND` + `LX cutout L2` to `In2.Cu` (`0.21 mm` under `B.Cu`), move `C22` beside `U4.8`, pull `U3.61`/`U5.17` vias out of `B.Paste`, enforce `BT1` copper keepout + co-locate `U8`, populate `.kicad_pro` `netclass_assignments`, and move `BT1`/`J1` polarity silk outside connector footprints.
2. **Gate 0 & Gate 4 design sign-offs (if not already approved on `phase0.md` / `phase4.md`):**
   - Confirm `403535` LiPo datasheet permits `263–328 mA` (`297 mA` typ, `~0.58–0.82C`) charge current, or change `R4` to `4.7 kΩ` (`189 mA`).
   - Confirm `BT1` inward pre-mating + `0.05 mm` Kapton + `≥ 2.4 mm` spacer (`~9.6 mm` stack) and `SW1/SW2` `+0.40 mm` nominal (`0.00 to −0.20 mm` worst-case) rim projection.
   - Confirm keeping Voronoi `F.SilkS` art (`4,631` clipped segments) and omitting board name/rev/URL on `B.SilkS` (`BOARD_ID = 6` via `NT1` on `GPIO19`).
