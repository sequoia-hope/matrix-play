# Back Silkscreen Tidy Report (`c-silk-gemini`)

## 1. Deliverables & Re-runnable Command

- **Script**: `scripts/crunch/silk/back_silk.py`
  ```bash
  python3 scripts/crunch/silk/back_silk.py \
    hw/round-pendant/c-silk-gemini/round-pendant.kicad_pcb \
    hw/round-pendant/c-silk-gemini/silk.kicad_pcb \
    --stats hw/round-pendant/c-silk-gemini/silk-stats.json
  ```
- **Output board & matched project rules**:
  - `hw/round-pendant/c-silk-gemini/silk.kicad_pcb`
  - `hw/round-pendant/c-silk-gemini/silk.kicad_pro` (copied from `round-pendant.kicad_pro` with `min_text_thickness` matched to `0.10 mm`)
  - `hw/round-pendant/c-silk-gemini/silk.kicad_dru` (copied verbatim from `round-pendant.kicad_dru`)
- **Verification artifacts**:
  - `hw/round-pendant/c-silk-gemini/before-bottom.png` and `hw/round-pendant/c-silk-gemini/after-bottom.png` (`2400 × 2400` raytraced renders via `kicad-cli pcb render --side bottom`)
  - `hw/round-pendant/c-silk-gemini/drc-before.json` and `hw/round-pendant/c-silk-gemini/drc-after.json` (`kicad-cli pcb drc --format json --severity-all --units mm`)
  - `hw/round-pendant/c-silk-gemini/silk-stats.json`

Running `back_silk.py` a second time on `silk.kicad_pcb` is strictly idempotent (produces the exact same 52 kept designators, 45 hidden designators, and 4 board-level pin-1 dots) and leaves all copper tracks, 893 vias, zones, nets, `Edge.Cuts`, all 332 component positions/orientations, `B.Fab`, and all 235 front-side LED footprints (`D1`–`D235` / `F.SilkS`) 100% untouched.

---

## 2. JLCPCB Silkscreen Capabilities & Order Option

Checked directly on JLCPCB's official documentation (fetched 2026-11-03):

| Process Tier | Min Stroke Width | Min Text Height | Pad-to-Silk Clearance | Character Gap / Edge Margin | Sources |
|---|---:|---:|---:|---|---|
| **Standard Silkscreen** (LPI screen print) | `0.15 mm` (~6 mil / `0.153 mm`) | `1.00 mm` (40 mil; `0.80 mm` in newer LPI summary tables at `0.15 mm` stroke) | `≥ 0.15 mm` (CAM clips silk within `0.15 mm` of exposed mask openings) | `> 0.15 mm` line gap; `≥ 0.20 mm` from routed board outline (`±0.20 mm` regular routing tolerance) | [Capabilities](https://jlcpcb.com/capabilities/Capabilities), [Ordering Instructions §9](https://jlcpcb.com/help/article/instructions-for-ordering), [PCB Silkscreen Guide](https://jlcpcb.com/blog/pcb-silkscreen) |
| **High-Precision Silkscreen** (UV inkjet / Direct Legend Printing) | **`0.10 mm`** | **`0.80 mm`** | `≥ 0.15 mm` (`≥ 0.25 mm` recommended where room exists) | `> 0.15 mm` line gap; `≥ 0.20 mm` from routed board edge | [Character Design Specifications](https://jlcpcb.com/blog/character-design-specifications) (updated 2026-09-08, *High-Precision Characters* section) |

### Notes on JLCPCB documentation & required order option
1. **Documentation nuance**: JLCPCB's main `/capabilities/Capabilities` Legend table only lists the standard `0.15 mm` width / `1.0 mm` height floor (and notes lines `< 0.15 mm` may be blurred or widened on the standard process). Even the summary table at the bottom of `character-design-specifications` lists `0.15 mm` / `0.80 mm`, whereas the *High-Precision Characters* section in the same specification explicitly states **`0.10 mm` minimum stroke width** and **`0.80 mm` minimum character height**.
2. **Required JLCPCB order option**: When ordering, select **`Silkscreen Technology: High-precision Printing Silkscreen`** on the JLCPCB PCB quote/order page (available at a small surcharge on multi-layer orders). If ordered with *Standard Printing Silkscreen*, `0.10 mm` strokes risk under-printing or automatic stroke thickening.
3. **Text size & `.kicad_pro` matching**:
   - Used **`0.80 mm` height × `0.80 mm` width, `0.10 mm` stroke**, mirrored on `B.SilkS`.
   - Matched `board.design_settings.rules.min_text_thickness` from `0.15` to **`0.10`** in `silk.kicad_pro` (`min_text_height` was already `0.80 mm` and `min_silk_clearance` was already `0.15 mm`).
   - Enforced at most **2** readable back-side text orientations when viewing `--side bottom`: `0.0°` horizontal left-to-right (**29** designators) and `-90.0°` vertical bottom-to-top (**23** designators).

---

## 3. Geometric Clearances Enforced by `back_silk.py`

Using KiCad's exact rendered stroke polygons (`PCB_TEXT.TransformTextToPolySet`, normalized to each label's optical ink bounding-box center rather than KiCad's descender-padded text box) and global MILP optimization (`scipy.optimize.milp` / HiGHS), every placed designator satisfies:

- **Exposed pads / solder-mask openings (`B.Mask`)**: `≥ 0.16 mm` clearance (JLC minimum `0.15 mm`).
- **PTH / NPTH drill holes**: `≥ 0.20 mm` clearance.
- **Board outline (`Edge.Cuts`)**: `≥ 0.21 mm` inside the `R = 19.0 mm` outline centerline (`0.16 mm` inside the `0.10 mm` stroke).
- **Component physical bodies (`B.Fab` + pads)**: `≥ 0.055 mm` outside every part body on the board (never under its own or any neighbor's body), and strictly closer (both center-to-body and stroke-to-body) to its own part than to any other part.
- **Kept footprint silk & pin-1 marks**: `≥ 0.17 mm` clearance (`min_silk_clearance = 0.15 mm`).
- **Label-to-label spacing**: `≥ 0.22 mm` hard stroke-to-stroke minimum, `≥ 0.46 mm` hard end-to-end reading-axis gap (so collinear labels never visually merge into one word), plus a continuous soft repulsion penalty inside `0.52 mm` so crowded passives are omitted rather than squeezed.

---

## 4. Designators Kept and Dropped

The board has **332** footprints total: **235** front-side LEDs (`D1`–`D235`, untouched) and **97** back-side components (**24** major parts + **73** passives).

| Category | Total | Kept on `B.SilkS` | Dropped (Hidden) | Coverage |
|---|---:|---:|---:|---:|
| **Major components** (`U*`, `SW*`, `L1`, `Y1`, `Q1`, `J1`, `BT1`, `TP*`) | 24 | **24** | **0** | **100.0%** |
| **Passives** (`C*`, `R*`) | 73 | **28** | **45** | **38.4%** |
| **All back-side parts** | **97** | **52** | **45** | **53.6%** |

### Kept major designators (24 / 24)
`BT1`, `J1`, `L1`, `Q1`, `SW1`, `SW2`, `TP1`, `TP2`, `TP3`, `TP4`, `TP5`, `TP6`, `TP7`, `TP8`, `U1`, `U2`, `U3`, `U4`, `U5`, `U6`, `U7`, `U8`, `U9`, `Y1`

### Kept passive designators (28 / 73)
- **Capacitors (14 / 42)**: `C1`, `C6`, `C7`, `C9`, `C23`, `C24`, `C25`, `C27`, `C37`, `C40`, `C41`, `C44`, `C45`, `C46`
- **Resistors (14 / 31)**: `R1`, `R2`, `R4`, `R5`, `R6`, `R7`, `R8`, `R9`, `R13`, `R18`, `R19`, `R21`, `R31`, `R33`

### Dropped passive designators (45 / 73 — hidden via `SetVisible(False)` to prevent crowding or via-drill breakup)
- **Capacitors (28)**: `C2`, `C3`, `C4`, `C5`, `C8`, `C10`, `C11`, `C12`, `C13`, `C14`, `C16`, `C17`, `C18`, `C19`, `C20`, `C21`, `C22`, `C26`, `C30`, `C31`, `C32`, `C33`, `C34`, `C35`, `C36`, `C42`, `C43`, `C47`
- **Resistors (17)**: `R3`, `R10`, `R11`, `R12`, `R14`, `R15`, `R16`, `R17`, `R20`, `R22`, `R30`, `R32`, `R34`, `R35`, `R40`, `R41`, `R42`

---

## 5. Tented Vias & Chip Pin-1 Audit

### Silk over tented vias
All **893** through vias on `round-pendant.kicad_pcb` are tented on `B.Mask` (and filled/capped per `design/brief.md` §5).
- **Reference designators crossing a tented via drill hole (`Ø 0.15 mm`)**: **`0 / 52`** (none cross a drill hole).
- **Reference designators grazing a tented via under-mask copper ring (`r_via + 0.02 mm`)**: **`6 / 52`** total, each touching **1** tented via ring and **0** via drills:
  - **4 majors** where dense surrounding parts/vias leave zero ring-free spots: `L1`, `TP3`, `TP4`, `U6`.
  - **2 passives**: `C24`, `C25`.
- **Added board-level pin-1 dots over tented vias**: **`0 / 4`**.
- **Kept original footprint silk outline/pin-1 graphics over tented vias**: **`15 / 52`** shapes from the fixed part/via placement (`L1` circle, `Q1` line, `U1`×4, `U2`×3, `U3`×3, `U7` triangle, `Y1`×2). `172` colliding or redundant passive/TP/chip silk graphic items were removed from `B.SilkS`.

### Chip & polarized component pin-1 marks (`12 / 12` verified)
- **Preserved existing pad-clear (`≥ 0.155 mm`) pin-1 marks on 8 parts**: `U1`, `U2`, `U7`, `U9`, `Q1` (filled triangles), `U8`, `L1` (filled circles), and `Y1` (asymmetric corner L-bracket around pad 1).
- **Added `0.26 mm` solid filled silk pin-1 dots (`0.13 mm` width, `0.065 mm` radius) on 4 chips** whose original marks were missing or violated `0.15 mm` pad clearance:
  - `U3` (`RP2350A`, originally had no silk pin-1 mark): added at `(94.434, 96.257)` mm (`0` tented vias).
  - `U4` (`W25Q128JVPIQ`, original triangle hit `R4` pad at `0.000 mm`): added at `(99.105, 108.782)` mm (`0` tented vias).
  - `U5` (`BQ24073`, original triangle hit `R3` pad at `0.000 mm`): added at `(101.406, 107.136)` mm (`0` tented vias).
  - `U6` (`TPS7A0233`, original circle was `0.052 mm` from `C4` pad): added at `(94.809, 100.151)` mm (`0` tented vias).

---

## 6. KiCad DRC Counts (Before vs. After)

Evaluated with `kicad-cli pcb drc --format json --severity-all --units mm`:

| DRC Rule / Category | Severity | Before (`round-pendant.kicad_pcb`) | After (`silk.kicad_pcb` + `silk.kicad_pro`) | Delta |
|---|---|---:|---:|---:|
| `silk_overlap` | error | 180 | **0** | −180 |
| `silk_over_copper` | error | 62 | **0** | −62 |
| `silk_edge_clearance` | warning | 4 | **0** | −4 |
| `text_height` | warning | 4 | **0** | −4 |
| `text_thickness` | warning | 4 | **0** | −4 |
| `mirrored_text_on_front_layer` | warning | 0 | **0** | 0 |
| `nonmirrored_text_on_back_layer` | warning | 0 | **0** | 0 |
| **Total silkscreen violations** | — | **254** | **0** | **−254** |
| `items_not_allowed` (non-silk copper/via rules) | error | 5 | 5 | 0 |
| `length_out_of_range` (`U3-XIN`) | error | 1 | 1 | 0 |
| `copper_sliver` (`B.Cu`) | warning | 1 | 1 | 0 |
| `via_dangling` | warning | 16 | 16 | 0 |
| **Total non-silk violations** | — | **23** | **23** | **0** |
| **Unconnected items** | error | **2** | **2** | **0** |
| **Grand total DRC violations** | — | **277** | **23** | **−254** |

- Forcing all 7 silkscreen rules (`silk_overlap`, `silk_over_copper`, `silk_edge_clearance`, `text_height`, `text_thickness`, `mirrored_text_on_front_layer`, `nonmirrored_text_on_back_layer`) to `"error"` with `--severity-exclusions` enabled also reports **`0` silkscreen violations**.
- If `silk.kicad_pcb` is evaluated against the unmodified `round-pendant.kicad_pro` (`min_text_thickness = 0.15 mm`), DRC still reports **`0`** overlap/copper/edge/height/mirroring violations and **52** `text_thickness` warnings (one per `0.10 mm`-stroke visible designator, confirming why `.kicad_pro` must match the `0.10 mm` high-precision rule).

---

## 7. What Was Not Checked

1. **Front silkscreen (`F.SilkS`)**: Left completely untouched (`D1`–`D235` and board-level `F.SilkS`), as assigned to another person per the brief. Baseline DRC already had `0` front-silk violations.
2. **Board-identity block & functional/polarity callout text**: Phase 9 project-wide items (`board_name`, `rev`, `date`, `repo`, `license`, `BT1 +/-` polarity text, `J1` USB rating/pinout, `SW1`/`SW2` button function text, and `TP*` net names) were not added; this task strictly tidied component reference designators and chip pin-1 marks on a post-route board without pre-reserved silk no-via zones.
3. **3D model rotational markings vs. footprint copper pad 1**: Pin-1 dots were verified against actual copper pad `"1"` geometry in `pcbnew`. Note that `U6`'s EasyEDA 3D STEP model renders its cosmetic package dot on pad 3's corner (`180°` opposite copper pad `"1"` and `B.Fab`'s chamfer); our silk dot correctly marks copper pad `"1"` (`94.33, 100.075`).
4. **Non-silk electrical/routing DRC & live JLCPCB Gerber DFM preview**: The 23 pre-existing copper/via/length violations and 2 unconnected items were verified unchanged rather than edited, and Gerbers were not uploaded to external hosts (`jlcpcb.com` online viewer).
