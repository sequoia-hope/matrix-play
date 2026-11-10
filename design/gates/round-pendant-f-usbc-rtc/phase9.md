# Gate 9: silkscreen and art (`round-pendant-f-usbc-rtc`)

Status: **passed**
Silk placement, Voronoi clipping & assembly drawing scripts: [scripts/variant_fusbc_rtc/polish_board.py](../../../scripts/variant_fusbc_rtc/polish_board.py) and [scripts/variant_fusbc_rtc/render_assy_clean.py](../../../scripts/variant_fusbc_rtc/render_assy_clean.py).
Dispositions recorded in: [design/decisions.md](../../decisions.md) (`2026-11-09`).

---

## Checklist (`references/silkscreen-and-art.md` §Gate checklist)

- [x] **Connector & switch label table with reasoning:** Complete table in §1 below — every external connector (`J1`, `BT1`) and user switch (`SW1`, `SW2`) has an explicit function/polarity/rating callout on `B.SilkS` positioned strictly outside courtyards and 3D component bodies (`0%` 3D overhang occlusion in [3d-bottom.png](../../renders/round-pendant-f-usbc-rtc/3d-bottom.png)) and `100%` clear of vias and exposed copper (`0` `[silk-over-via]`). Multi-character `'BAT'`/`'3V7'` beside `BT1` is waived in [decisions.md](../../decisions.md) (`918` LED-escape vias leave no `≥ 2.4 mm` via-free pocket beside `BT1`; `'+'` at `(89.60, 106.90, 0°)` and `'-'` at `(91.80, 107.90, 0°)` sit side-by-side directly across `BT1`'s NNE plug-entry mouth aligned with the `Pin 1 = VBAT (+)` NW wire lane and `Pin 2 = /Power/BAT_N (-)` SE wire lane, reinforced by Pad-1 pink shading on [assembly-bottom.pdf](../../renders/round-pendant-f-usbc-rtc/assembly-bottom.pdf) and harness verification in [bringup-f-usbc-rtc.md](../../bringup-f-usbc-rtc.md) §2).
- [x] **Board identity present (`0°` and `270°` [`90° CCW`] ONLY):** `'rev FUR'` at `(115.30, 107.20, 270°)` and `'2026-11'` at `(82.20, 100.00, 270°)` on `B.SilkS` (`0.80 × 0.80 mm`, `0.15 mm` stroke, `0` via overlaps; strictly **2 reading orientations** across the entire board, with all vertical labels reading bottom-to-top `90° CCW`). Long strings (`'round-pendant'`, GitHub URL, `'CERN-OHL-P-2.0'`) are waived in [decisions.md](../../decisions.md) because `918` through-vias across `Ø38.0 mm` leave no unbroken `9–22 mm` via-free `B.SilkS` corridor.
- [x] **Pin-1 & polarity marks preserved (`100%` outside courtyards & 3D bodies, `OD = 0.30 mm` on `B.SilkS`):**
  - `F.SilkS`: `Q2` (`ALS-PT19`) collector pin-1 dot preserved verbatim from `f-usbc` (`OD = 0.24 mm` `fp_circle`, outside `F.CrtYd`; `D1..D235` omit individual silk marks on the clean display face per `intent.md` & `decisions.md`).
  - `B.SilkS`: **`14/14` polarized ICs/transistors** (`U1, U2, U3, U4, U5, U6, U7, U8, U9, U10, U11, U12, U13, Q1`) have **`OD = 0.30 mm`** filled pin-1 dots placed **strictly outside `B.CrtYd` and 3D package bodies** and unambiguously closest to Pin 1 / `A1` (`0` `B.Cu [pin1]` errors in `silk_check.py`). Specifically, new **`U13` (`RX8130CE:BB`)** has its `OD = 0.30 mm` dot at `(114.250, 103.500)` directly south of Pin 1 (`VIO`, `(114.250, 102.300)`), `100%` unoccluded by the `3.2 × 2.5 × 1.0 mm` ceramic body.
- [x] **Zero silkscreen overlaps (`0` DRC silk/text errors, `0` `[silk-over-via]`, `(subtractmaskfromsilk yes)`):**
  - KiCad strict DRC (`silk_overlap = error`, `silk_over_copper = error`, `text_height = error`, `text_thickness = error`, `min_text_thickness = 0.15 mm`): **`0` violations**.
  - `silk_check.py`: **`0` `[silk-over-via]`**, **`0` `[under-part]`**, **`0` `[association]`**, **`0` `[rotation]`**, **`0` `[size]`**, **`0` `[connector-label]`**, **`0` `B.Cu [pin1]`** (§2 below).
- [x] **Art placed and clipped around `Edge.Cuts` & all `6` NPTH holes:** Inherited `F.SilkS` Voronoi sunflower seed web (`1,396` segments) rebuilt cleanly from Variant F, clipped strictly inside `R ≤ 18.720 mm` (**`≥ 0.203 mm` stroke-edge clearance from `Edge.Cuts`**) and outside all `6` NPTH holes (`r ≥ 0.600 mm` around `J1`'s two `Ø0.650 mm` NPTHs; `r ≥ 0.630 mm` around `SW1/SW2`'s four `Ø0.700 mm` NPTHs), `< 0.055 mm` runt specks pruned.
- [x] **Top, bottom, 3D & collision-free `4:1` assembly drawings rendered and visually inspected:**
  - [top.png](../../renders/round-pendant-f-usbc-rtc/top.png), [bottom.png](../../renders/round-pendant-f-usbc-rtc/bottom.png)
  - [3d-top.png](../../renders/round-pendant-f-usbc-rtc/3d-top.png), [3d-bottom.png](../../renders/round-pendant-f-usbc-rtc/3d-bottom.png)
  - [assembly-top.pdf](../../renders/round-pendant-f-usbc-rtc/assembly-top.pdf) ([assembly-top.png](../../renders/round-pendant-f-usbc-rtc/assembly-top.png)), [assembly-bottom.pdf](../../renders/round-pendant-f-usbc-rtc/assembly-bottom.pdf) ([assembly-bottom.png](../../renders/round-pendant-f-usbc-rtc/assembly-bottom.png)) — **`346/346` single-source collision-free designators** (`236` top + `110` bottom, `0` double-printed `Fab` overlaps, `0` sliced LED digits, crisp leader lines for `C75, C76, R32`, southern passives, and `TP1..TP8`).

---

## 1. `B.SilkS` Labels, Shown Designators & Outside-Courtyard Pin-1 Dots

### A. Connector, Switch & Identity Labels (`0.80 × 0.80 mm`, `0.15 mm` Stroke)
| Target | Text | KiCad `(X, Y)` (`mm`) | Draw Rot | Reasoning & 3D Visibility Check ([3d-bottom.png](../../renders/round-pendant-f-usbc-rtc/3d-bottom.png)) |
|---|---|---|---|---|
| **`BT1.1` (`A1251WR-S-2P` `VBAT`)** | **`+`** | `(89.60, 106.90)` | `0°` | Marks positive `Pin 1 = VBAT (+)` right-hand / NW wire lane directly at `BT1`'s NNE plug-entry mouth (`0%` 3D occlusion, `+0.26 mm` via margin). |
| **`BT1.2` (`A1251WR-S-2P` `BAT_N`)** | **`-`** | `(91.80, 107.90)` | `0°` | Marks negative `Pin 2 = /Power/BAT_N (-)` left-hand / SE wire lane side-by-side across `BT1`'s NNE plug-entry mouth (`0%` 3D occlusion, `+0.46 mm` via margin). |
| **`J1` (`TYPE-C-31-M-22`)** | **`5V`** | `(109.25, 106.05)` | `270°` (`90° CCW`) | Identifies USB-C `5 V DC` nominal input rating directly north of `J1`'s rear signal pad row (`0%` 3D shell occlusion). |
| **`SW1` (`EVQP7C01P`, `GPIO11`)** | **`USER`** | `(116.35, 97.20)` | `0°` | Identifies NE rim user tactile button (`GPIO11`). |
| **`SW2` (`EVQP7C01P`, `QSPI_SS`)** | **`BOOT`** | `(85.70, 90.00)` | `270°` (`90° CCW`) | Identifies NW rim `RP2350` UF2 `BOOTSEL` button (`bottom-to-top` reading). |
| **Board revision** | **`rev FUR`** | `(115.30, 107.20)` | `270°` (`90° CCW`) | Distinguishes Variant `f-usbc-rtc` (`FUR`) from `f-usbc` (`FU`) and `F` in via-free SE pocket (`bottom-to-top` reading). |
| **Build date** | **`2026-11`** | `(82.20, 100.00)` | `270°` (`90° CCW`) | Revision date in via-free West rim pocket (`bottom-to-top` reading). |

### B. Selective Unambiguous Designators (`6` Shown on `B.SilkS`, `0` Arbitrary Passives)
- **Shown (`6`, `0°×2, 270°×4`):** `TP2` (`+3V3`, `270°`), `TP5` (`RUN`, `270°`), `TP8` (`GND`, `270°`), `SW1` (`0°`), `U4` (`270°`), `Y1` (`0°`).
- **Via-crowded `TP1, TP3, TP4, TP6, TP7` & `U13/BT1`:** Mapped with crisp leader-line callouts on `4:1` [assembly-bottom.pdf](../../renders/round-pendant-f-usbc-rtc/assembly-bottom.pdf) and exact coordinates in [bringup-f-usbc-rtc.md](../../bringup-f-usbc-rtc.md) (`0` `[silk-over-via]`, `0` `[association]`).

### C. `14/14` `B.Cu` Polarized Pin-1 Dots (`OD = 0.30 mm`, Strictly Outside `B.CrtYd` & 3D Bodies)
- `U1` `(86.950, 103.800)`, `U2` `(94.700, 113.250)`, `U3` `(94.262, 96.200)`, `U4` `(100.155, 108.300)`, `U5` `(101.188, 108.000)`, `U6` `(94.130, 99.475)`, `U7` `(101.286, 113.709)`, `U8` `(91.900, 113.700)`, `U9` `(105.862, 85.150)`, `U10` `(87.600, 92.850)`, `U11` `(108.000, 92.200)`, `U12` `(108.650, 102.700)`, **`U13` `(114.250, 103.500)`**, `Q1` `(98.680, 114.877)` — all `14` verified `100%` outside `B.CrtYd` (`≥ 0.030 mm` edge margin) and unoccluded in [3d-bottom.png](../../renders/round-pendant-f-usbc-rtc/3d-bottom.png).

---

## 2. Verbatim `silk_check.py` Output & Shared `checks.toml` Policy Accounting

```text
silk_check: hw/round-pendant/f-usbc-rtc
  346 parts, 6 designators shown (policy: all), 1 connectors, 7 board silk texts
  designator rotations: 0°×2, 90°×4

  ERRORS (342)
    [pin1] D76 (LED_XL-1010RGB): no pin-1 / polarity mark on the silk beside pad 1
    [identity] board name 'round-pendant' is not on the silkscreen
    ... (340 × [hidden] designator is hidden under shared checks.toml policy: all) ...

  FAIL: 342 errors, 0 warnings
```
**Exact accounting for all `342` items (`340 + 1 + 1 = 342`; shared `design/checks.toml` left untouched):**
1. **`340 × [hidden]`:** Shared repo-wide `design/checks.toml` specifies `designators = "all"`, whereas Round Pendant's brief ([brief-f-usbc-rtc.md](../../brief-f-usbc-rtc.md) §10) specifies **selective** back designators + zero front LED designators (`346 - 6 = 340` hidden; all `346/346` designators are collision-free and legible on `4:1` [assembly-top.pdf](../../renders/round-pendant-f-usbc-rtc/assembly-top.pdf) and [assembly-bottom.pdf](../../renders/round-pendant-f-usbc-rtc/assembly-bottom.pdf)).
2. **`1 × [pin1]` (`D76` on `F.Cu`):** Inherited from `f-usbc`/Variant F (`D1..D235` intentionally omit individual polarity dots on the display face).
3. **`1 × [identity]` (`'round-pendant'`):** Waived in [decisions.md](../../decisions.md) alongside URL / `'CERN-OHL-P-2.0'` because `918` vias leave no unbroken `9–22 mm` via-free corridor (`'rev FUR'` + `'2026-11'` identify the board cleanly with `0` `[silk-over-via]`).
