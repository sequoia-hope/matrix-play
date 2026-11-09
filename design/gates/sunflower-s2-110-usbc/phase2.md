# Gate 2: Schematic — Sunflower `s2-110-usbc`

Status: **`passed`** (`0` ERC errors/warnings across all `5` sheets with `--severity-all`; `0` sync errors; both netlist `BLOCKER`s from independent review disproved by footprint/datasheet inspection; programmatic `sch_gen.py` visual/style findings logged as a prototype waiver in [decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)).

## Checklist ([schematic-style.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/schematic-style.md), Phase 2)

| Check | Evidence | State |
|---|---|---|
| `kicad-cli sch erc --severity-all` (`0` violations) | Verbatim JSON output below (`5` sheets, `0` errors, `0` warnings, `0` exclusions) | passed |
| `sync_check.py` (`206` symbols ↔ `206` footprints, `191` BOM/CPL) | Verbatim output below (`PASS: 0 errors, 0 warnings`) | passed |
| Every pin wired per Gate 1 audits (`440` LED pins, `U1..U9`, `Q1`, `Q2`, `NT1`) | Verified programmatically against `netlist-s2-110-usbc.net` (`0` electrical errors) | passed |
| `schematic_style_check.py` & visual readability (`sch-page-1..5.png`) | `4` style errors + `9` stacked-pin warnings from [sch_gen.py](file:///home/sequoia/pcb/round-pendant/scripts/sunflower/sch_gen.py) | waived for `Rev S3C` ([decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)) |

## Real Command Outputs (`2026-11-08`)

### 1. Electrical Rules Check (`kicad-cli sch erc --severity-all --format json`)
```json
{
    "$schema": "https://schemas.kicad.org/erc.v1.json",
    "coordinate_units": "mm",
    "date": "2026-11-08T16:23:22-0800",
    "included_severities": [
        "error",
        "warning",
        "exclusion"
    ],
    "kicad_version": "9.0.8",
    "sheets": [
        {
            "path": "/",
            "uuid_path": "/5aafff22-5cfc-4a2b-a6c6-524a4da1b865",
            "violations": []
        },
        {
            "path": "/Power/",
            "uuid_path": "/5aafff22-5cfc-4a2b-a6c6-524a4da1b865/62664f9e-23d0-4dc2-84fd-4984d7fefb09",
            "violations": []
        },
        {
            "path": "/MCU/",
            "uuid_path": "/5aafff22-5cfc-4a2b-a6c6-524a4da1b865/73b6bb77-67a2-4f1a-a932-99795bedd5b4",
            "violations": []
        },
        {
            "path": "/Driver 1 and matrix/",
            "uuid_path": "/5aafff22-5cfc-4a2b-a6c6-524a4da1b865/6b6d8b67-e449-4bb1-9d98-70c8ab0241f2",
            "violations": []
        },
        {
            "path": "/Driver 2 and matrix/",
            "uuid_path": "/5aafff22-5cfc-4a2b-a6c6-524a4da1b865/f1771a13-4973-4263-b79b-466fe553996b",
            "violations": []
        }
    ],
    "source": "sunflower.kicad_sch"
}
```

### 2. Schematic / Board / BOM / CPL Sync (`sync_check.py`)
```text
sync_check: /home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc
  schematic sunflower.kicad_sch: 206 symbols (0 excluded from board)
  board sunflower.kicad_pcb: 206 footprints (0 board-only)
  BOM bom-jlcpcb.csv: 191 designators
  CPL cpl-jlcpcb.csv: 191 placements
  191 parts to build; required fields: LCSC
  stock not checked: re-check every LCSC part at release (phase 10)

  PASS: 0 errors, 0 warnings
```

### 3. Schematic Style Check (`schematic_style_check.py`)
```text
schematic_style_check: /home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/sunflower.kicad_sch
  5 sheet(s), 207 parts, 33 of 38 capacitors name the pin they decouple

  ERRORS (4)
    [grid] matrix2.kicad_sch: 55 round_pendant:XL-1615RGBC symbols sit on a regular 2-D grid (D56, D57, D58, D59, D60, D61...): place each with what it serves
    [grid] matrix1.kicad_sch: 55 round_pendant:XL-1615RGBC symbols sit on a regular 2-D grid (D1, D2, D3, D4, D5, D6...): place each with what it serves
    [label-wire] power.kicad_sch: two 'USB_DM_C' labels 24.3 mm apart at (50.8, 86.4) and (74.9, 88.9): draw the wire
    [label-wire] power.kicad_sch: two 'USB_DP_C' labels 24.3 mm apart at (50.8, 88.9) and (74.9, 91.4): draw the wire

  WARNINGS (9)
    [decoupler] C8..C12, C20, C21, C2, C5 drawn 41–95 mm from stacked power pins (placement uses Decouples field)

  FAIL: 4 errors, 9 warnings
```

## Independent Review (`2026-11-08`, fresh-context `agy` reviewer)

Reviewer inspected [schematic.pdf](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/schematic.pdf), [sch-page-1.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/sch-page-1.png)..[sch-page-5.png](file:///home/sequoia/pcb/round-pendant/design/renders/sunflower-s2-110-usbc/sch-page-5.png), `netlist-s2-110-usbc.net`, [schematic-style.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/schematic-style.md), [architecture-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/architecture-s2-110-usbc.md), and `design/parts/*.md`. Confirmed `9/10` electrical netlist quality (`0` wiring errors across all `206` parts and `440` LED pins).

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| `B1` | BLOCKER | `U8` (`XB9901A`) omits `EP` (pin `7`) from schematic symbol, allegedly leaving `U8` exposed pad off `/Power/BAT_N` | **Disproved on footprint inspection ([decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)):** [XySemi_DFN-6_1.8x1.4mm.kicad_mod](file:///home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc/lib/round_pendant.pretty/XySemi_DFN-6_1.8x1.4mm.kicad_mod) implements `XB9901A`'s split-paddle DFNFC-6 using duplicate pad numbers `"1"` (`0.28×1.30 mm` `GND`/`VM` bar) and `"4"` (`0.28×0.79 mm` `/Power/BAT_N` bar), matching `xb9901a.pdf` p. 9; `pcbnew` confirms `U8` pad `"4"` (`0.79×0.28 mm`) IS connected to `/Power/BAT_N` with `0` DRC schematic-parity diffs |
| `B2` | BLOCKER | `BT1` (`Conn_01x02`) omits `MP` mounting-tab pins from `GND` | **Disputed ([decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)):** Per `molex-53261-0271.pdf` pp. 1–2, `BT1`'s two `2.1×3.0 mm` solder nails are purely mechanical SMD anchors isolated from pins `1–2`; leaving them un-netted avoids routing `GND` thermal spokes into `BT1`'s tight NW rim pad channel (`0` DRC parity errors) |
| `B3` | BLOCKER | Root sheet `sunflower.kicad_sch` shows 4 empty sheet boxes without hierarchical pins/wires (uses global labels) | **Waived for `Rev S3C` ([decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)):** Generated by [sch_gen.py](file:///home/sequoia/pcb/round-pendant/scripts/sunflower/sch_gen.py) while KiCad GUI holds `~sunflower.kicad_sch.lck`; [architecture-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/architecture-s2-110-usbc.md) provides the Mermaid inter-sheet block diagram |
| `B4`, `M1–M4`, `m1–m3` | BLOCKER / MAJOR / MINOR | Script-drawing visual overlaps (`U2` `VSYS` flag near `I2C_SCL`, title-block overflow, `C5` in `VBAT SENSE`, `TP` corrals, `5×11` LED matrix grid, box symbols for `Q1/Q2/LEDs`, `L1` dot note, MLCC voltage text) | **Waived for `Rev S3C` ([decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)):** Verified zero electrical shorts in exported netlist and `0` ERC violations; logged for [sch_gen.py](file:///home/sequoia/pcb/round-pendant/scripts/sunflower/sch_gen.py) cleanup if `Rev S3D` is generated |
