# Gate 9: silkscreen and art (`parallelogram-p2-132-usb6`)

Status: **passed** *(visual render published to PCB view for user review alongside Phase 4/10 sign-off)*

## Checklist (`references/silkscreen-and-art.md` §Gate checklist)
- [x] **Connector & button label table with reasoning (table below — decided first, all placed on `B.SilkS`)**
- [x] **Board identity present (`B.SilkS`):** Board name (`p2-132-usb6`), revision (`rev P1U6`), date (`2026-11`), license (`CERN-OHL-P`), and contiguous 3-column open-source GitHub repo URL block (`github.com/`, `sequoia-hope/`, `round-pendant`) in the NE margin
- [x] **Strict 2-rotation typography (`0.0°` and `90.0°` only):** `37` `B.SilkS` texts across `[0.0°, 90.0°]` (`0` skewed `-17.74°/+17.74°` rotations), `0` passive designators (`NO R43`)
- [x] **Zero overlaps & zero silk-over-via / silk-over-copper / edge / 3D-body violations:**
  - `kicad-cli pcb drc --severity-all`: **`0` `silk_overlap`, `0` `silk_over_copper`, `0` `silk_edge_clearance`, `0` `text_height`, `0` `text_thickness`**
  - `silk_check.py`: **`0` non-LED errors (`[]`)** — **`0` `[silk-over-via]`, `0` `[connector-label]`, `0` `[identity]`, `0` `B.Cu` `[pin1]`** (`12/12` `B.Cu` polarized/indexed parts `U1..U9, Q1, L1, Y1` + `Q2` on `F.SilkS` have filled pin-1 dots **outside** 3D package bodies!)
- [x] **Top and bottom silk renders visually inspected & reviewed:** `design/renders/parallelogram-p2-132-usb6/{top.png,bottom.png,3d-top.png,3d-bottom.png,assembly-bottom.png,gerbers/top_silk.png,gerbers/bottom_silk.png}`
- [x] **Art placed & locked (`F.SilkS`):** Inherited parallelogram-family `293`-segment skewed diagonal geometric lattice web along LED cell midpoints (`0.15 mm` stroke, clipped `0.25 mm` clear of all `F.Cu` pads and `0.35 mm` clear of `Q2`, over `POFV = Yes` planar capped vias, `(locked yes)`)

## 1. Connector, Button, Designator, Test-Point, & Identity Label Table (`B.SilkS`, `0.80 mm` Height, `0.15 mm` Stroke)

| Target | Placed Text(s) | Board-Centered `(x, y)` mm | Rot (°) | Functional Reasoning |
|---|---|---|---|---|
| `J1` (`TYPE-C-31-M-22`) | `J1`, `5V` | `(-3.90, +22.20)`, `(+1.50, +24.00)` | `0.0`, `0.0` | Places `"5V"` immediately north-east of `J1` (`nearest_ref == J1`, completely outside `BT1` courtyard) and `"J1"` north-west of `J1` at `0.0°`. |
| `BT1` (`A1251WR-S-2P` JST `1.25`) | `+`, `-`, `BATT` | `(+11.70, +21.60)`, `(+11.70, +18.60)`, `(+10.90, +16.00)` | `0.0`, `0.0`, `90.0` | Places `"+"` directly opposite `Pad 1` South (`VBAT`, `y = +20.675`) and `"-"` directly opposite `Pad 2` North (`BAT_N`, `y = +19.425`), plus `"BATT"` right north of `BT1`. |
| **`SW5` (New West-North side button)** | **`USER_C`**, **`SW5`** | **`(-10.90, -17.00)`**, **`(-7.90, -19.20)`** | **`90.0`**, **`0.0`** | Unambiguously labels new North West-edge `EVQP7J01P` switch (`GPIO9`) immediately south of `SW5`, `> 1.40 mm` clear of identity labels. |
| **`SW6` (New West-South side button)** | **`USER_D`**, **`SW6`** | **`(-11.70, +17.80)`**, **`(-10.30, +26.00)`** | **`90.0`**, **`0.0`** | Unambiguously labels new South West-edge `EVQP7J01P` switch (`GPIO0`) along the West margin north of `SW6` and `"SW6"` just south of `SW6`. |
| `SW1` (East-mid side button) | `PWR`, `SW1` | `(+10.90, +5.40)`, `(+9.30, -2.80)` | `0.0`, `90.0` | Marks East-edge power/wake switch (`GPIO11`) south and north of `SW1`. |
| `SW2` (West-mid side button) | `BOOT`, `SW2` | `(-11.30, -7.80)`, `(-7.90, -4.40)` | `90.0`, `0.0` | Marks `BOOTSEL` (`~{QSPI_SS}`) switch along West margin north of `SW2` (completely outside `TP8` courtyard!). |
| `SW3` / `SW4` (NW / SE wing buttons) | `USER_A`, `SW3` / `USR_B`, `SW4` | `(-3.30, -29.60)`, `(-9.70, -33.00)` / `(+10.10, +33.00)`, `(+11.10, +24.40)` | `90.0` / `0.0` | Labels NW (`GPIO7`) and SE (`GPIO19`) wing flat-face push buttons at `0.0°`/`90.0°` inside the `0.25 mm` edge inset. |
| Major `B.Cu` parts & `12/12` Pin-1 dots | `J1, Q1, SW1..SW6, U1..U4, U6, U8, U9, Y1` (`16/20` majors; `0` passives) + `12` dots | Adjacent to each courtyard (`nearest_major == self`) | `0.0` / `90.0` | Zero passive designators; all `12` `B.Cu` polarized/indexed parts (`U1..U9, Q1, L1, Y1`) + `Q2` on `F.SilkS` have filled pin-1 dots **outside** 3D bodies (`assembly-bottom.pdf` covers tight `BT1/U5/U7/L1` refs). |
| Test-point net labels | `DIO` (`TP7`), `GND` (`TP8`), `CLK` (`TP6`), `1V1` (`TP4`) | Adjacent to bare `Ø 1.0 mm` test pads | `0.0` / `90.0` | Labels SWD & core test points where `0.80 mm` text clears surrounding vias/pads (`TP1..TP8` coordinates also tabulated in `bringup.md` §2). |
| Open-hardware identity & Contiguous URL | `p2-132-usb6`, `rev P1U6`, `2026-11`, `CERN-OHL-P`, `github.com/` + `sequoia-hope/` + `round-pendant` | `(-8.7, -12.0)`, `(+11.7, -23.4)`, `(-11.5, +6.8)`, `(+6.1, -24.2)`, NE 3-col `(+11.3/+10.3/+9.1, -15.5..-22.0)` | `90.0` | Complete open-source identity with contiguous 3-column URL block reading left-to-right (`+X -> -X`) in Mirrored Bottom view. |

## 2. Verbatim Check Outputs

### 1. Strict KiCad DRC (`kicad-cli pcb drc --severity-all`)
```text
Found 0 violations
Found 0 unconnected items
Found 0 schematic parity issues
```

### 2. `silk_check.py` Verification
- **Non-LED `silk_check.py` errors:** **`0` (`[]`)** — zero `silk_overlap`, zero `silk_over_copper`, zero `silk_edge_clearance`, zero `silk-over-via`, zero `connector-label`, zero `identity`, zero `B.Cu` `pin1`, and zero `rotations` errors!
- *(Shared `design/checks.toml` policy note, logged in `design/decisions.md`: only the hidden `F.Cu` `LED1..132` reference/cathode fields trigger `[hidden]`/`[pin1]` against shared `checks.toml`, because `intent.md` line 98 keeps display-face silkscreen text/dots off the optical LED array.)*

## 3. Independent Fresh-Context Review (`agy` `gemini-4-argon-high`) & Dispositions

| ID | Severity | Finding Summary | Resolution |
|---|---|---|---|
| `B1` | BLOCKER | `U5`, `U6`, `U7` `B.SilkS` pin-1 dots were hidden underneath opaque 3D IC bodies in `3d-bottom.png`, and `L1`/`Y1` lacked pin-1 dots. | **Fixed**: Built `body_polys` (`B.Fab` + courtyard hulls) BEFORE placing pin-1 dots in `pcb_gen.py` `stage_post_silk` and added `L1` + `Y1` -> **`12/12` `B.SilkS` pin-1 dots now sit visibly outside 3D bodies** (confirmed on `3d-bottom.png`). |
| `B2` | BLOCKER | `BT1` `"+"` (`y = +20.00`) sat between `Pad 1` and `Pad 2` instead of opposite `Pad 1` (`+20.675`), `"5V"` sat inside `BT1`'s courtyard, and `"BOOT"` overlapped `TP8`'s courtyard near `"SW2"`. | **Fixed**: Placed `"+"` at `(+11.70, +21.60)` (south of `Pad 1`), `"-"` at `(+11.70, +18.60)` (north of `Pad 2`), `"BATT"` at `(+10.90, +16.00)`, `"5V"` at `(+1.50, +24.00)` right by `J1` outside `BT1`, and `"BOOT"` at `(-11.30, -7.80)` clear of `TP8`. |
| `M1–M4` | MAJOR | `4` `B.SilkS` rotations (`0°, 90°, ±17.74°`), scattered 3-part URL fragments, lonely passive `"R43"`, unlabeled test points, and `F.SilkS` web over vias. | **Fixed + Documented**: Enforced strict `2`-rotation typography (`[0.0°, 90.0°]`), placed contiguous 3-column URL block at `(+11.3, +10.3, +9.1)`, dropped `"R43"` (`16/20` major refs only + 4:1 `assembly-bottom.pdf`), labeled `DIO, GND, CLK, 1V1` on `B.SilkS`, locked `F.SilkS` web (`POFV = Yes` provides planar capped vias under `F.SilkS`), and synced `brief.md` §10. |

**Independent Fresh-Context Re-Review Verdict:** **VERDICT: PASS** (all prior `B1`, `B2`, and `M1–M4` findings verified resolved across renders and `kicad-cli pcb drc` / `silk_check.py`).
