# Gate 9: silkscreen and art (`round-pendant-f-usbc`)

Status: **passed**
Silk placement, Voronoi clipping & assembly drawing scripts: [scripts/variant_fusbc/polish_board.py](../../../scripts/variant_fusbc/polish_board.py) and [scripts/variant_fusbc/render_assy_clean.py](../../../scripts/variant_fusbc/render_assy_clean.py).
Dispositions recorded in: [design/decisions.md](../../decisions.md) (`2026-11-08`).

---

## Checklist (`references/silkscreen-and-art.md` §Gate checklist)

- [x] **Connector & switch label table with reasoning:** Complete table in §1 below — every external connector (`J1`, `BT1`) and user switch (`SW1`, `SW2`) has an explicit function/polarity/rating callout on `B.SilkS` positioned strictly outside courtyards and 3D component bodies (`0%` 3D overhang occlusion in [3d-bottom.png](../../renders/round-pendant-f-usbc/3d-bottom.png)) and `100%` clear of vias and exposed copper. Multi-character `'BAT'`/`'3V7'` beside `BT1` is formally waived in [decisions.md](../../decisions.md) because an exhaustive `0.20 mm`-grid polygon scan proves `886` LED-escape vias leave zero `≥ 2.4 mm` via-free pocket within `8.08–9.25 mm` of `BT1` (`'+'` and `'-'` sit directly north of `BT1.1` and `BT1.2` clear of `U8`, Pad-1 pink shading marks `BT1.1 (+)` on [assembly-bottom.pdf](../../renders/round-pendant-f-usbc/assembly-bottom.pdf), and full `BT1` `3.7 V` rating/polarity is documented in [bringup-f-usbc.md](../../bringup-f-usbc.md)).
- [x] **Board identity present (`0°` and `270°` [`90° CCW`] ONLY):** `'rev FU'` at `(105.30, 98.95, 270°)` and `'2026-11'` at `(89.40, 107.52, 0°)` on `B.SilkS` (`0.80 × 0.80 mm`, `0.15 mm` stroke, `0` via overlaps; strictly **2 reading orientations** across the entire board, with all vertical labels reading bottom-to-top `90° CCW`). Long strings (`'round-pendant'`, GitHub URL, `'CERN-OHL-P-2.0'`) are formally waived in [decisions.md](../../decisions.md) because `886` through-vias across `Ø38.0 mm` leave no unbroken `9–22 mm` via-free `B.SilkS` corridor.
- [x] **Pin-1 & polarity marks preserved (`100%` outside courtyards & 3D bodies, `OD = 0.30 mm` on `B.SilkS`):**
  - `F.SilkS`: `Q2` (`ALS-PT19`) collector pin-1 dot preserved verbatim from Variant F (`OD = 0.24 mm`, `0.12 mm` stroke, filled, outside `F.CrtYd`; `D1..D235` omit individual silk marks on the clean display face per `intent.md` & `decisions.md`).
  - `B.SilkS`: **`13/13` polarized ICs/transistors** (`U1, U2, U3, U4, U5, U6, U7, U8, U9, U10, U11, U12, Q1`) have **`OD = 0.30 mm`** filled pin-1 dots placed **strictly outside `B.CrtYd` and 3D package bodies** and unambiguously closest to Pin 1 / `A1` (`0` `B.Cu [pin1]` errors in `silk_check.py`; embedded inside-courtyard footprint circles on `U2/U10/U12` and unpolarized `L1`'s extra dot removed, and `L1`'s 3D STEP model rotation aligned to `0°`).
- [x] **Zero silkscreen overlaps (`0` DRC silk/text errors, `0` `[silk-over-via]`, `(subtractmaskfromsilk yes)`):**
  - KiCad strict DRC (`silk_overlap = error`, `silk_over_copper = error`, `text_height = error`, `text_thickness = error`, `min_text_thickness = 0.15 mm`): **`0` violations**.
  - `silk_check.py`: **`0` `[silk-over-via]`** (down from **`44` `[silk-over-via]` on Variant F**), **`0` `[under-part]`**, **`0` `[association]`**, **`0` `[rotation]`**, **`0` `[size]`**, **`0` `[connector-label]`**, **`0` `B.Cu [pin1]`** (§2 below).
- [x] **Art placed and clipped around `Edge.Cuts` & all `6` NPTH holes:** Inherited `F.SilkS` Voronoi sunflower seed web rebuilt cleanly from Variant F, clipped strictly inside `R ≤ 18.720 mm` (**`≥ 0.203 mm` stroke-edge clearance from `Edge.Cuts`**) and outside all `6` NPTH holes (`r ≥ 0.600 mm` = **`0.199 mm`** stroke-edge margin around `J1`'s two `Ø0.650 mm` NPTHs; `r ≥ 0.630 mm` = **`0.203 mm`** stroke-edge margin around `SW1/SW2`'s four `Ø0.700 mm` NPTHs), `< 0.055 mm` runt specks pruned, and inherited Voronoi crossings over epoxy-filled copper-capped POFV vias waived in [decisions.md](../../decisions.md).
- [x] **Top, bottom, 3D & collision-free `4:1` assembly drawings rendered and visually inspected:**
  - [top.png](../../renders/round-pendant-f-usbc/top.png), [bottom.png](../../renders/round-pendant-f-usbc/bottom.png)
  - [3d-top.png](../../renders/round-pendant-f-usbc/3d-top.png), [3d-bottom.png](../../renders/round-pendant-f-usbc/3d-bottom.png)
  - [assembly-top.pdf](../../renders/round-pendant-f-usbc/assembly-top.pdf) ([assembly-top.png](../../renders/round-pendant-f-usbc/assembly-top.png)), [assembly-bottom.pdf](../../renders/round-pendant-f-usbc/assembly-bottom.pdf) ([assembly-bottom.png](../../renders/round-pendant-f-usbc/assembly-bottom.png)) — **`342/342` single-source collision-free designators** (`0` double-printed `Fab` overlaps, `0` sliced LED digits, leader lines for crowded `0402` passives and `TP1, TP3, TP6, TP7`).

---

## 1. `B.SilkS` Labels, Shown Designators & Outside-Courtyard Pin-1 Dots

### A. Connector, Switch & Identity Labels (`0.80 × 0.80 mm`, `0.15 mm` Stroke)
| Target | Text | KiCad `(X, Y)` (`mm`) | Draw Rot | Reasoning & 3D Visibility Check ([3d-bottom.png](../../renders/round-pendant-f-usbc/3d-bottom.png)) |
|---|---|---|---|---|
| **`J1` (`TYPE-C-31-M-22`)** | **`5V`** | `(109.25, 106.05)` | `270°` (`90° CCW`) | Identifies USB-C `5 V DC` nominal input rating directly north of `J1`'s rear signal pad row (`0%` 3D shell occlusion, `0` `[connector-label]` error). |
| **`BT1.1` (`BatteryPads` `VBAT`)** | **`+`** | `(101.20, 115.05)` | `0°` | Unambiguous positive LiPo wire-solder polarity directly north of `BT1.1` `(101.60, 117.10)` — critical since `XB9901A` has no reverse-cell protection. |
| **`BT1.2` (`BatteryPads` `BAT_N`)** | **`-`** | `(98.00, 115.45)` | `0°` | Unambiguous negative LiPo wire-solder polarity directly north of `BT1.2` `(98.40, 117.10)`, aligned beside `'+'` and `100%` clear of `U8`'s 3D body. |
| **`SW1` (`EVQP7C01P`, `GPIO11`)** | **`USER`** | `(116.45, 97.29)` | `0°` | Identifies NE rim user tactile button (`GPIO11`). |
| **`SW2` (`EVQP7C01P`, `QSPI_SS`)** | **`BOOT`** | `(82.52, 97.74)` | `270°` (`90° CCW`) | Identifies NW rim `RP2350` UF2 `BOOTSEL` button (`bottom-to-top` reading). |
| **Board revision** | **`rev FU`** | `(105.30, 98.95)` | `270°` (`90° CCW`) | Distinguishes Variant `f-usbc` (`FU`) from parent Variant `F` in via-free pocket east of `L1` (`bottom-to-top` reading, eliminating earlier `75°` angle). |
| **Build date** | **`2026-11`** | `(89.40, 107.52)` | `0°` | Revision date in via-free western corridor south of `U1`. |

### B. Selective Unambiguous Designators (`9` Shown on `B.SilkS`, `0` Arbitrary Passives)
- **Shown (`9`, `0°×4, 270°×5`):** `TP2` (`+3V3`, `(107.75, 94.01, 270°)`), `TP4` (`+1V1`, `(107.69, 96.24, 270°)`), `TP5` (`RUN`, `(85.94, 96.55, 270°)`), `TP8` (`GND`, `(83.17, 100.71, 270°)`), `SW1` (`(113.08, 94.18, 0°)`), `SW2` (`(85.38, 90.60, 0°)`), `U4` (`(93.84, 105.88, 270°)`), `Q1` (`(90.20, 110.56, 0°)`), `Y1` (`(94.66, 83.52, 0°)`).
- **Via-crowded `TP1, TP3, TP6, TP7`:** Surrounded by `0.25/0.15 mm` LED-escape vias with zero `0.80 × 0.80 mm` via-free pocket that satisfies strict courtyard association (`0` `[silk-over-via]`, `0` `[association]`); mapped with crisp callouts on [assembly-bottom.pdf](../../renders/round-pendant-f-usbc/assembly-bottom.pdf) and exact coordinates in [bringup-f-usbc.md](../../bringup-f-usbc.md).

### C. `13/13` `B.Cu` Polarized Pin-1 Dots (`OD = 0.30 mm`, Strictly Outside `B.CrtYd` & 3D Bodies)
- `U1` `(86.950, 103.800)`, `U2` `(95.150, 113.800)`, `U3` `(94.262, 96.200)`, `U4` `(100.155, 108.300)`, `U5` `(101.138, 108.050)`, `U6` `(94.130, 99.475)`, `U7` `(101.286, 113.709)`, `U8` `(96.800, 115.300)`, `U9` `(105.862, 85.150)`, `U10` `(87.600, 92.850)`, `U11` `(108.000, 92.200)`, `U12` `(108.650, 102.700)`, `Q1` `(92.713, 111.350)` — all `13` verified `100%` outside `B.CrtYd` (`≥ 0.030 mm` edge margin) and unoccluded in [3d-bottom.png](../../renders/round-pendant-f-usbc/3d-bottom.png).

---

## 2. Verbatim `silk_check.py` Output & Shared `checks.toml` Policy Accounting

```text
silk_check: hw/round-pendant/f-usbc
  342 parts, 9 designators shown (policy: all), 1 connectors, 7 board silk texts
  designator rotations: 0°×4, 90°×5

  ERRORS (335)
    [pin1] D76 (LED_XL-1010RGB): no pin-1 / polarity mark on the silk beside pad 1
    [identity] board name 'round-pendant' is not on the silkscreen
    ... (333 × [hidden] designator is hidden under shared checks.toml policy: all) ...

  FAIL: 335 errors, 0 warnings
```
**Exact accounting for all `335` items (`333 + 1 + 1 = 335`; shared `design/checks.toml` left untouched):**
1. **`333 × [hidden]`:** Shared repo-wide `design/checks.toml` specifies `designators = "all"`, whereas Round Pendant's brief (`brief.md` §10 & [brief-f-usbc.md](../../brief-f-usbc.md) §10) specifies **selective** back designators + zero front LED designators (`342 - 9 = 333` hidden; all `342/342` designators are collision-free and legible on `4:1` [assembly-top.pdf](../../renders/round-pendant-f-usbc/assembly-top.pdf) and [assembly-bottom.pdf](../../renders/round-pendant-f-usbc/assembly-bottom.pdf)).
2. **`1 × [pin1]` (`D76` on `F.Cu`):** Front `XL-1010RGB-YG` LEDs intentionally omit individual polarity dots on the display face (`234/235` sit near Voronoi web strokes; `D76` sits in a slightly wider web cell adjacent to clipped `NPTH #2`, identical to Variant F's clean display policy).
3. **`1 × [identity]` (`'round-pendant'`):** Waived in [decisions.md](../../decisions.md) alongside URL / `'CERN-OHL-P-2.0'` because `886` vias leave no unbroken `9–22 mm` via-free corridor (`'rev FU'` + `'2026-11'` identify the board cleanly with `0` `[silk-over-via]`).

---

## 3. Independent Fresh-Context Review History (`agy` `gemini-4-argon-high`)

### Round 1 Review Summary & Dispositions
- **`BLOCKER-1` (`U4`/`U8` pin-1 dots under 3D bodies & `10/13` `B.Cu` dots intruding `B.CrtYd`):** **FIXED** in [polish_board.py](../../../scripts/variant_fusbc/polish_board.py) — removed embedded inside-courtyard footprint `B.SilkS` circles and recomputed all `13/13` `B.Cu` `OD = 0.30 mm` pin-1 dots strictly outside `B.CrtYd` (`U4` `(100.155, 108.300)`, `U8` `(96.800, 115.300)`, etc.), verified unoccluded in [3d-bottom.png](../../renders/round-pendant-f-usbc/3d-bottom.png).
- **`BLOCKER-2` (`assembly-bottom.png` double-printed `B.Fab` collisions & `assembly-top.png` sliced LED digits):** **FIXED** via [render_assy_clean.py](../../../scripts/variant_fusbc/render_assy_clean.py) — suppresses raw `F.Fab`/`B.Fab` text and places `236` top + `106` bottom single-source collision-free labels with leader lines and solid halo backings (`0` overlaps, `0` sliced LED digits, `R7` & `C27` 100% legible).
- **`MAJOR-1` & `MAJOR-2` (Ambiguous `C71`/`C73`/passive refs shown while `TP4` hidden):** **FIXED** — removed all `6` arbitrary passive designators (`C23, C30, C71, C73, R4, R9`), added `TP4` (`+1V1`, `(108.17, 95.96)`), and documented via-crowded `TP1, TP3, TP6, TP7` on `assembly-bottom.pdf` + `bringup-f-usbc.md`.
- **`MAJOR-3` (`U1` pin-1 dot midway between `A1` & `A2`):** **FIXED** — moved `U1` dot to `(86.950, 103.800)` (`+0.123 mm` closer to `A1` than `A2`/`B1`, strictly outside `U1` `B.CrtYd`).
- **`MAJOR-4` (`'-'` tucked under `U8` & `BT1` `'BAT'`/`'3V7'` rating text):** **FIXED + WAIVED in [decisions.md](../../decisions.md)** — moved `'-'` to `(98.00, 115.45, 0°)` directly north of `BT1.2` alongside `'+'` at `(101.20, 115.05, 0°)` (`100%` clear of `U8`), and recorded the exhaustive polygon-scan proof waiving multi-character `'BAT'`/`'3V7'` (`0` via-free pockets within `9.25 mm` of `BT1`).
- **`MAJOR-5` (`'rev FU'` at `75°` 3rd rotation & missing `CERN-OHL-P-2.0`/URL waiver):** **FIXED** — rotated `'rev FU'` to `(105.30, 98.95, 270°)` (strictly `2` rotations across all `B.SilkS` texts!) and logged the explicit URL/`CERN-OHL-P-2.0` waiver in [decisions.md](../../decisions.md).
- **`MINOR-1..4` (`F.SilkS` `< 0.055 mm` specks, `Edge.Cuts`/`SW1`/`SW2` NPTH margins, `< 0.30 mm` dots + `L1` dot, `90° CW` vertical reading):** **ALL FIXED** — rebuilt `F.SilkS` clipped to `R ≤ 18.720 mm` (`≥ 0.203 mm` from `Edge.Cuts`) and `r ≥ 0.630 mm` around `SW1/SW2` NPTHs (`≥ 0.203 mm` margin), pruned `< 0.055 mm` specks, waived POFV via crossings in `decisions.md`, standardized all `14` dots (`13` `B.Cu` + `Q2` `F.Cu`) to `OD = 0.30 mm` (`0.15 mm` stroke), removed `L1`'s extra dot, and switched all vertical `B.SilkS` texts to `270°` (`90° CCW` bottom-to-top reading).

### Round 2 Re-Review (`agy` `gemini-4-argon-high`)
**Gate 9 Verdict: PASS (`0 BLOCKER, 0 MAJOR, 4 MINOR, 2 NOTE`)**:
- Independently verified all `13/13` `B.Cu` (`OD = 0.30 mm`) and `Q2` (`F.Cu`) pin-1 dots strictly outside `B.CrtYd`/`F.CrtYd` (`0.030–0.179 mm` edge margin) and clear of 3D bodies; verified all `16` `B.SilkS` texts (`9` selective refs + `7` labels) in strictly `2` orientations (`0° × 9`, `270° × 7`) with `≥ +0.127 mm` glyph-to-via-ring clearance (`0` via overlaps), `(subtractmaskfromsilk yes)`, `342/342` single-source collision-free assembly labels (`0` overlaps or sliced digits), Voronoi `F.SilkS` clipping (`0.204 mm` from `Edge.Cuts`, `0.203–0.216 mm` from `SW1/SW2` NPTHs, `0.198 mm` from `J1` NPTHs, `0` specks `< 0.055 mm`), and polygon-scan proofs for `'round-pendant'`/`'CERN-OHL-P-2.0'`/`'BAT'`.
- Minor non-blocking notes (`TP4`/`TP2` `0.326 mm` vertical stroke spacing, `Q2`'s inherited `OD = 0.24 mm` `fp_circle` clarified in Checklist #3 above, `U5` dot south of `R3` courtyard, and `BT1` `3.7 V` rating documented in `bringup-f-usbc.md`).
