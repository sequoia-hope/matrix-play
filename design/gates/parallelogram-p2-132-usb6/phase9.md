# Gate 9: silkscreen and art (`parallelogram-p2-132-usb6`)

Status: **passed** *(visual render published to PCB view for user review alongside Phase 4/10 sign-off)*

## Checklist (`references/silkscreen-and-art.md` §Gate checklist)
- [x] **Connector, button, & `8/8` test-point label table with reasoning (table below — decided first, all placed on `B.SilkS`)**
- [x] **Board identity present (`B.SilkS`):** Board name (`p2-132-usb6`), revision (`rev P1U6`), date (`2026-11`), license (`CERN-OHL-P`), and contiguous 3-column open-source GitHub repo URL block (`github.com/`, `sequoia-hope/`, `round-pendant`) in the NE margin
- [x] **Strict 2-rotation typography (`0.0°` and `90.0°` only):** `36` `B.SilkS` texts (`11` native `fp.Reference()` designators + `25` board labels) across `[0.0°, 90.0°]` (`0` skewed `-17.74°/+17.74°` rotations), `0` passive designators on silk, and **`100%` (`133/133` `F.Fab` + `98/98` `B.Fab`) collision-free assembly designators** in `assembly-top.{png,pdf}` & `assembly-bottom.{png,pdf}`
- [x] **Zero overlaps & zero silk-over-via / silk-over-copper / edge / 3D-body / mis-association violations:**
  - `kicad-cli pcb drc --severity-all`: **`0` `silk_overlap`, `0` `silk_over_copper`, `0` `silk_edge_clearance`, `0` `text_height`, `0` `text_thickness`**
  - `silk_check.py`: **`0` non-LED/non-hidden errors (`[]`)** — **`0` `[under-part]`, `0` `[association]`, `0` `[silk-over-via]`, `0` `[connector-label]`, `0` `[identity]`, `0` `B.Cu` `[pin1]`** (`12/12` `B.Cu` polarized/indexed parts `U1..U9, Q1, L1, Y1` + `Q2` on `F.SilkS` have filled pin-1 dots **outside** 3D package bodies!)
- [x] **Top and bottom silk + Fab renders visually inspected & reviewed:** `design/renders/parallelogram-p2-132-usb6/{top.png,bottom.png,3d-top.png,3d-bottom.png,assembly-top.png,assembly-bottom.png,gerbers/top_silk.png,gerbers/bottom_silk.png}`
- [x] **Art placed & locked (`F.SilkS`):** Inherited parallelogram-family `293`-segment skewed diagonal geometric lattice web along LED cell midpoints (`0.15 mm` stroke, clipped `0.25 mm` clear of all `F.Cu` pads and `0.35 mm` clear of `Q2`, over mandatory `POFV = Yes` Type VII planar capped vias, `(locked yes)`)

## 1. Connector, Button, Native `fp.Reference()`, `8/8` Test-Point, & Identity Label Table (`B.SilkS`, `0.80 mm` Height, `0.15 mm` Stroke)

| Target | Placed Text(s) | Board-Centered `(x, y)` mm | Rot (°) | Functional Reasoning |
|---|---|---|---|---|
| `J1` (`TYPE-C-31-M-22`) | `5V` | `(-7.90, +24.60)` | `0.0` | Places `"5V"` immediately NW of `J1` (`nearest_part == J1`, completely outside `BT1`/`C1`/`SW6` courtyards; `"J1"` centered on `B.Fab`). |
| `BT1` (`A1251WR-S-2P` JST `1.25`) | `+`, `-`, `BATT 3.7V` | `(+6.30, +25.60)`, `(+9.70, +25.20)`, `(+9.30, +19.20)` | `0.0`, `0.0`, `0.0` | Places `"+"` directly West of `Pad 1` (`VBAT`, `(+7.345, +25.400)`) and `"-"` directly East of `Pad 2` (`BAT_N`, `(+8.595, +25.400)`), plus `"BATT 3.7V"` right at the North-facing (`-Y`) mating mouth (`"BT1"` centered on `B.Fab`). |
| **`SW5` (New West-North side button)** | **`USER_C`**, **`SW5`** | **`(-10.90, -17.00)`**, **`(-8.70, -24.00)`** | **`90.0`**, **`90.0`** | Unambiguously labels North West-edge `EVQP7J01P` switch (`GPIO9`) south of `SW5` (`USER_C`) + native `fp.Reference()` `"SW5"` (`nearest_part == SW5`). |
| **`SW6` (New West-South side button)** | **`USER_D`**, **`SW6`** | **`(-11.30, +17.80)`**, **`(-10.30, +26.00)`** | **`90.0`**, **`0.0`** | Unambiguously labels South West-edge `EVQP7J01P` switch (`GPIO0`) north of `SW6` (`USER_D`) + native `fp.Reference()` `"SW6"` just south of `SW6`. |
| `SW1` (East-mid side button) | `PWR`, `SW1` | `(+10.50, +4.80)`, `(+10.90, -1.60)` | `0.0`, `0.0` | Marks East-edge power/wake switch (`GPIO11`) south (`PWR`) and north (`SW1`) of `SW1`. |
| `SW2` (West-mid side button) | `BOOT`, `SW2` | `(-11.10, -8.00)`, `(-7.90, -4.20)` | `90.0`, `0.0` | Marks `BOOTSEL` (`~{QSPI_SS}`) switch along West margin north of `SW2` (clear of `TP8`) + native `fp.Reference()` `"SW2"`. |
| `SW3` / `SW4` (NW / SE wing buttons) | `USER_A`, `SW3` / `USER_B`, `SW4` | `(-3.70, -28.20)`, `(-9.10, -32.60)` / `(+11.70, +26.60)`, `(+11.50, +31.60)` | `90.0, 0.0` / `90.0, 90.0` | Labels NW (`GPIO7`) and bezel-aligned SE (`GPIO19`) wing flat-face push buttons at `0.0°`/`90.0°` inside the `0.25 mm` edge inset. |
| Native `fp.Reference()` designators & `12/12` Pin-1 dots | `Q1, SW1..SW6, U1, U2, U4, U9` (`11` visible `fp.Reference()`s; `0` passives) + `12` dots | `(+10.9,+8.8)`, `(+3.9,-19.4)`, `(+11.1,-6.8)`, `(-7.1,+17.2)`, `(-10.5,+4.8)` | `0.0` (`×8`) / `90.0` (`×3`) | Audited directly by `silk_check.py` (`0` `[under-part]`, `0` `[association]`: every visible `fp.Reference()` is strictly closer to its own courtyard than to any neighbor!); tight-courtyard ICs (`U3, U5..U8, L1, Y1, J1, BT1`) + all passives appear `1:1` on 4:1 `assembly-bottom.{png,pdf}` (`98/98` `B.Fab`, `0` overlaps). |
| **`8/8` Test-point net labels** | `VSYS` (`TP1`), `3V3` (`TP2`), `VB` (`TP3`), `1V1` (`TP4`), `RUN` (`TP5`), `CLK` (`TP6`), `DIO` (`TP7`), `GND` (`TP8`) | `(+7.3,+15.6)`, `(-8.3,+10.8)`, `(+6.1,+10.4)`, `(-8.3,+12.6)`, `(-7.3,-0.4)`, `(+5.5,+0.6)`, `(+2.7,-4.6)`, `(-4.3,-4.8)` | `0.0` (`×6`) / `90.0` (`×2`) | **All `8/8` bare `Ø 1.0 mm` SMD test points labeled right on `B.SilkS`** (plus `TP1..TP8` on `B.Fab` and coordinates in `bringup.md` §1). |
| Open-hardware identity & Contiguous URL | `p2-132-usb6`, `rev P1U6`, `2026-11`, `CERN-OHL-P`, `github.com/` + `sequoia-hope/` + `round-pendant` | `(-8.7, -12.0)`, `(+11.7, -12.0)`, `(-11.7, +5.8)`, `(+7.5, -26.6)`, NE 3-col `(+11.5/+10.3/+9.1, -21.0..-22.0)` | `90.0` / `0.0` | Complete open-source identity with contiguous 3-column URL block reading left-to-right (`+X -> -X`) in Mirrored Bottom view. |

## 2. Verbatim Check Outputs

### 1. Strict KiCad DRC (`kicad-cli pcb drc --severity-all --schematic-parity`)
```text
Found 0 violations
Found 0 unconnected items
Found 0 schematic parity issues
```

### 2. `silk_check.py` Verification
- **Non-LED / non-hidden `silk_check.py` errors:** **`0` (`[]`)** — zero `[under-part]`, zero `[association]`, zero `silk_overlap`, zero `silk_over_copper`, zero `silk_edge_clearance`, zero `silk-over-via`, zero `connector-label`, zero `identity`, zero `B.Cu` `pin1`, and zero `rotations` errors!
- *(Shared `design/checks.toml` policy note, logged in `design/decisions.md`: only the `220` intentionally hidden passive/LED/tight-IC `fp.Reference()` fields and `63` `F.Cu` `LED` `[pin1]` items report against shared `checks.toml`, because `intent.md` line 98 keeps display-face silkscreen text/dots off the optical LED array while `assembly-top.pdf` [`133/133`] and `assembly-bottom.pdf` [`98/98`] provide `100%` collision-free assembly designators.)*

## 3. Independent Fresh-Context Review (`agy` `gemini-4-argon-high`) & Dispositions

| ID | Severity | Finding Summary | Resolution |
|---|---|---|---|
| `B1` | BLOCKER | `U5`, `U6`, `U7` `B.SilkS` pin-1 dots were hidden underneath opaque 3D IC bodies in `3d-bottom.png`, and `L1`/`Y1` lacked pin-1 dots. | **Fixed**: Built `body_polys` (`B.Fab` + courtyard hulls) BEFORE placing pin-1 dots in `pcb_gen.py` `stage_post_silk` and added `L1` + `Y1` -> **`12/12` `B.SilkS` pin-1 dots now sit visibly outside 3D bodies** (confirmed on `3d-bottom.png`). |
| `B2` | BLOCKER | `BT1` `"+"` / `"-"` polarity, `"5V"` near `J1`, and `"BOOT"` near `TP8` needed unambiguous pad-aligned placement. | **Fixed**: On rotated `-Y` North-facing `BT1`, placed `"+"` at `(+6.30, +25.60)` (West of `Pad 1` `(+7.345, +25.400)`), `"-"` at `(+9.70, +25.20)` (East of `Pad 2` `(+8.595, +25.400)`), `"BATT 3.7V"` at `(+9.30, +19.20)`, `"5V"` at `(-7.90, +24.60)` right NW of `J1` (`nearest_part == J1`), and `"BOOT"` at `(-11.10, -8.00)` clear of `TP8`. |
| `M1–M4` / `2026-11-09 M3 & B5` | MAJOR | Standalone `PCB_TEXT` designators bypassed `silk_check` `[association]` (`U3/U5/U6/U8/Y1/J1/BT1` sat closer to neighboring passives), `TP1`/`TP3` lacked `B.SilkS` labels (`6/8`), and `assembly-bottom.pdf` / `assembly-top.pdf` had missing/overlapping `Fab` refs. | **Fixed**: Switched `major_refs` in `pcb_gen.py` to native `fp.Reference()` (`11` visible `fp.Reference()`s passing `silk_check` with `0` `[association]` & `0` `[under-part]`), added `"VSYS"` (`TP1`) + `"VB"` (`TP3`) so **`8/8` test points are labeled on `B.SilkS`**, and placed `133/133` `F.Fab` + `98/98` `B.Fab` `0`-overlap designators in `parallelogram.kicad_pcb` + 4:1 `assembly-{top,bottom}.{png,pdf}`. |
