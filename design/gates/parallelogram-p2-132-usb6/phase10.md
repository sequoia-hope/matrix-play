# Gate 10: release (`parallelogram-p2-132-usb6`)

Status: **awaiting_signoff**

## Checklist (`references/sync-and-release.md` §Gate checklist)
- [x] **All earlier gates current (not stale):** `phase4.md` (`awaiting_signoff`), `phase5.md` (`passed`), `phase6.md` (`passed`), `phase7.md` (`passed`), `phase8.md` (`passed`), `phase9.md` (`passed`)
- [x] **Release sync check passes (`sync_check.py --bom --cpl`):** `231` schematic symbols ↔ `231` PCB footprints ↔ `223` assembled parts in `bom-jlcpcb.csv` & `cpl-jlcpcb.csv` (`8` `in_bom=False` test points `TP1..TP8` excluded cleanly; **`PASS: 0 errors, 0 warnings`**)
- [x] **DRC / ERC / copper / pad-joint / parity checks re-run on final files:**
  - `kicad-cli pcb drc --severity-all --schematic-parity`: **`0` violations, `0` unconnected items, `0` schematic parity issues**
  - `kicad-cli sch erc --severity-all`: **`0` violations across all `5` sheets**
  - `scripts/bga/copper_audit.py`: **`rc == 0`** (`tracks=4921 vias=729 | 0` dangling, `0` cap_gap, `0` mid_graze/stubs, `0` off_via, `0` morph_necks, `0` acute_slivers, `0` collinear_dups, `0` zone_intrusions)
  - `pad_joints.py`: **`PASS: 0 thin pad joints`** across `913` SMD pads
- [x] **Stock & qty-10 BOM cost checked on `2026-11-08`:**
  - `export_and_cost.py --cost --qty 10`: **`$13.25 / board` @ qty 10** (`+$0.39` over live `p2-132-usb` `$12.86`, `35` unique LCSC part codes, `223` assembled parts)
  - Live JLCPCB PCBA SMT assembly API (`selectSmtComponentList/v2`): **`40/40` BOM lines (`35/35` unique LCSC parts) `100%` in stock** for a `10`-board build (`min stock = 529` on `TPS7A0233PDQNR`, `6,887` on `EVQP7J01P` `C2828254`, `1,439` on `AOTA-B201610S3R3-101-T` `C42411119`)
- [x] **CPL rotation & pick-origin verified for every polarized part, IC, connector, & switch (including new `SW5`/`SW6`):** Mirrored-Bottom visual overlay `design/renders/parallelogram-p2-132-usb6/cpl-overlay.png` (matching `3d-bottom.png` & JLCPCB Bottom PCBA viewer) + complete table below with both `KiCad Rot` and `CPL Rot`
- [x] **Gerbers independently parsed & rendered (`gerber_render.py` via `gerbonara`) + Assembly PDFs + 3D STEP:**
  - `hw/parallelogram/p2-132-usb6/fab/parallelogram-p2-132-usb6-gerbers.zip` (`13` files)
  - `hw/parallelogram/p2-132-usb6/fab/{assembly-bottom.pdf,assembly-top.pdf}` + `design/renders/parallelogram-p2-132-usb6/assembly-bottom.png`
  - `hw/parallelogram/p2-132-usb6/fab/parallelogram-p2-132-usb6.step` (`147` 3D STEP/WRL models embedded)
- [x] **Bring-up plan written with part-audit expected values, probe coordinates, & firmware guards:** `design/gates/parallelogram-p2-132-usb6/bringup.md` (linked from `index.html` card)
- [x] **Other variants proven byte-identical (`run_bytecheck.py`):** `53` raw byte-identical files + `2` canonical-identical `.kicad_pcb` files (`0` mismatches across `p2-132-usb` and `p1-66-usb`)
- [ ] **Git tag (`parallelogram-p2-132-usb6-revP1U6`) & User release approval:** Deferred per workspace rule (*"Do not commit or push. The supervising agent will review and commit"*) and awaiting user sign-off below.

---

## 1. Verbatim Release Check Outputs

### A. `sync_check.py --bom --cpl`
```text
sync_check: hw/parallelogram/p2-132-usb6
  schematic parallelogram.kicad_sch: 231 symbols (0 excluded from board)
  board parallelogram.kicad_pcb: 231 footprints (0 board-only)
  BOM bom-jlcpcb.csv: 223 designators
  CPL cpl-jlcpcb.csv: 223 placements
  223 parts to build; required fields: LCSC
  stock not checked: re-check every LCSC part at release (phase 10)

  PASS: 0 errors, 0 warnings
```

### B. Final `kicad-cli pcb drc --severity-all --schematic-parity` & `kicad-cli sch erc --severity-all`
```text
Found 0 violations
Found 0 unconnected items
Found 0 schematic parity issues
ERC sheets: 5 total violations: 0
```

### C. Fab Export & Independent Gerber Object-Count Audit (`gerber_render.py`)
```text
Exported hw/parallelogram/p2-132-usb6/fab/parallelogram-p2-132-usb6-gerbers.zip (13 files), bom-jlcpcb.csv (40 lines), cpl-jlcpcb.csv (223 parts)

gerber_render: hw/parallelogram/p2-132-usb6/fab/gerbers (board parallelogram)
  top_silk             parallelogram-F_Silkscreen.gto     827 objects
  top_paste            parallelogram-F_Paste.gtp          530 objects
  top_mask             parallelogram-F_Mask.gts           532 objects
  top_copper           parallelogram-F_Cu.gtl            3747 objects
  inner_1_copper       parallelogram-In1_Cu.g1            730 objects
  inner_2_copper       parallelogram-In2_Cu.g2           1692 objects
  bottom_copper        parallelogram-B_Cu.gbl            2608 objects
  bottom_mask          parallelogram-B_Mask.gbs           405 objects
  bottom_paste         parallelogram-B_Paste.gbp          407 objects
  bottom_silk          parallelogram-B_Silkscreen.gbo    1936 objects
  drill_parallelogram  parallelogram.drl                  731 objects
  outline              parallelogram-Edge_Cuts.gm1          8 objects
  12 layer images in design/renders/parallelogram-p2-132-usb6/gerbers
```
**Gerber structural cross-check:**
- `outline = 8 objects`: `4` straight edges + `4` `R = 1.00 mm` tangent corner arcs (watertight closed loop).
- `drill_parallelogram = 731 objects`: `729` plated through vias + `2` `Ø 0.65 mm` `J1` NPTH locating holes (`729 + 2 = 731` exact).
- `top_paste = 530 objects`: `132` `XL-1615RGBC` LEDs × `4` pads (`528`) + `1` `Q2` `XYC-PT19C-L1` × `2` pads (`2`) = `530` exact (`0` paste on vias).
- `top_mask = 532 objects`: `530` top SMD pads + `2` `J1` NPTH clearances = `532` exact (`100%` tented/capped vias).
- `inner_1_copper = 730 objects`: `1` unbroken `plane GND` polygon (`1,309.17 mm²`) + `729` via pads/antipads = `730` exact.
- `bottom_paste = 407 objects` vs `bottom_mask = 405 objects`: `U6` (`X2SON-4`) splits its central pad paste into small sub-apertures while **all `17` `GND` thermal vias in `U1/U2/U3/U5` solid EPs (`5 + 5 + 5 + 2`) have `0` `B.Paste` overlap**.
- **JLCPCB Order Form Specification:** **`JLC04161H-7628`** (`1.6 mm`, `1 oz` outer / `0.5 oz` inner, **`ENIG 1U"`** surface finish, **`Via Covering = Epoxy Filled & Capped (POFV = Yes)`** for the `118` SMD via-in-pad sites, double-sided PCBA with `Pass 1 = B.Cu` and `Pass 2 = F.Cu <= 245 °C` peak for `Q2` `XYC-PT19C-L1`).

---

## 2. CPL Rotation & Pick-Origin Verification (`hw/parallelogram/p2-132-usb6/fab/cpl-jlcpcb.csv` + Mirrored-Bottom `cpl-overlay.png`)

*(Coordinate convention: in Mirrored `B.Cu` view — matching `3d-bottom.png`, `bottom.png`, and JLCPCB's Bottom PCBA viewer — `+X` East is Left, `-X` West is Right, `-Y` North is Top, and `+Y` South is Bottom. Every LCSC part's EasyEDA zero-orientation was cross-checked pad-for-pad against `pcbnew` and `sunflower-s2-110-usbc/phase10.md`: **`0.00°` rotation error across all `223` parts**.)*

| Ref | LCSC | MPN | Layer | KiCad Rot (°) | Mid X | Mid Y | CPL Rot (°) | EasyEDA Zero-Orientation & Mirrored `B.Cu` Pin-1 / Plunger Proof |
|---|---|---|---|---:|---|---|---:|---|
| **`SW5`** | **`C2828254`** | **`EVQP7J01P`** | **`Bottom`** | **`+90.0`** | **`88.8250mm`** | **`-78.0000mm`** | **`90.00`** | **New West-North (`USER_C`):** `-0.325 mm` `c_origin` X-shift -> `Mid X = 88.825`; plunger projects `-X` outward (Right in Mirrored `B.Cu` view) `0.45 mm` past `x = -12.50 mm` West edge, identical to `SW2`. |
| **`SW6`** | **`C2828254`** | **`EVQP7J01P`** | **`Bottom`** | **`+90.0`** | **`88.8250mm`** | **`-122.8000mm`** | **`90.00`** | **New West-South (`USER_D`):** `-0.325 mm` `c_origin` X-shift -> `Mid X = 88.825`; plunger projects `-X` outward `0.45 mm` past `x = -12.50 mm` West edge, identical to `SW2`. |
| `SW2` | `C2828254` | `EVQP7J01P` | `Bottom` | `+90.0` | `88.8250mm` | `-96.5000mm` | `90.00` | Inherited West-mid (`BOOT`): plunger projects `-X` West. |
| `SW1` | `C2828254` | `EVQP7J01P` | `Bottom` | `-90.0` | `111.1750mm` | `-101.5000mm` | `270.00` | Inherited East-mid (`PWR`): `+0.325 mm` shift -> `Mid X = 111.175`, `270°` (`180°` opposite `SW2/5/6`), plunger projects `+X` East (Left in Mirrored `B.Cu`). |
| `SW3, SW4` | `C318884` | `TS-1187A-B-A-B` | `Bottom` | `+90.0` | `90.85 / 109.15` | `-71.35 / -128.65` | `90.00` | Symmetric `6.00 × 3.75 mm` flat-face SPST (`90°`). |
| `J1` | `C530612` | `TYPE-C-31-M-22` | `Bottom` | `162.26` | `98.3953mm` | `-127.9761mm` | `17.74` | Slanted South edge (`162.26°` + `c_origin` shift): mouth faces South-West perpendicular to `17.74°` edge; `2 × Ø 0.65 mm` NPTH pegs align cleanly. |
| `BT1` | `C225111` | `A1251WR-S-2P` | `Bottom` | `+90.0` | `108.6000mm` | `-120.0500mm` | `90.00` | Horizontal JST `1.25`: `+0.20 mm` X-shift, mouth faces `-X` West; `Pad 1` (`+` `VBAT`) South (`y = +20.675`), `Pad 2` (`-` `BAT_N`) North (`y = +19.425`). |
| `U1` | `C5137654` | `AW20198QNR` | `Bottom` | **`+90.0`** | `100.0000mm` | `-81.5000mm` | **`0.00`** | **Exact (`0.00°` err):** At `KiCad = +90°` on `B.Cu`, `U1.1` sits at `(+1.80, -83.80)` (`y = -16.20` board-centered) = **Bottom-Left** in Mirrored `B.Cu` view; EasyEDA `C5137654` zero-orientation is `-BL`, so `CPL = 0.00°` aligns Pin 1 at Bottom-Left (matches `3d-bottom.png` dot!). |
| `U2` | `C5137654` | `AW20198QNR` | `Bottom` | **`+90.0`** | `107.4000mm` | `-91.8000mm` | **`0.00`** | **Exact (`0.00°` err):** Identical `KiCad = +90°` -> Pin 1 Bottom-Left in Mirrored `B.Cu` -> `CPL = 0.00°`. |
| `U3` | `C42411118` | `RP2350A` | `Bottom` | **`0.0`** | `100.0000mm` | `-106.4000mm` | **`180.00`** | **Exact (`0.00°` err):** At `KiCad = 0°` on `B.Cu`, `U3.1` sits at `(-2.80, +9.44)` = **Bottom-Right** in Mirrored `B.Cu` (`3d-bottom.png`); EasyEDA `C42411118` `0°` is `-TL`, so `CPL = 180.00°` rotates `-TL -> -BR`! |
| `U4` | `C190862` | `W25Q128JVPIQ` | `Bottom` | `+90.0` | `96.3500mm` | `-117.6000mm` | `0.00` | WSON-8 `6×5`: EasyEDA `0°` = `-BL`; at `KiCad = +90°` on `B.Cu`, `U4.1` is Bottom-Left in Mirrored `B.Cu` -> `CPL = 0.00°`. |
| `U5` | `C15220` | `BQ24073RGTR` | `Bottom` | **`0.0`** | `103.0200mm` | `-118.5500mm` | **`180.00`** | **Exact (`0.00°` err):** EasyEDA `C15220` `0°` = `-TL`; at `KiCad = 0°` on `B.Cu`, `U5.1` (`IN`) is Bottom-Right in Mirrored `B.Cu` -> `CPL = 180.00°`. |
| `U6` | `C2860046` | `TPS7A0233PDQNR` | `Bottom` | `180.0` | `95.3000mm` | `-113.4000mm` | `0.00` | X2SON-4 `1×1`: EasyEDA `0°` = `-BR`; at `KiCad = 180°` on `B.Cu`, `U6.1` (`OUT`) is Top-Left -> `0.00°` matches pad-for-pad (`sunflower-s2-110-usbc/phase10.md` line 175). |
| `U7` | `C15999` | `USBLC6-2P6` | `Bottom` | `180.0` | `102.2000mm` | `-121.9500mm` | `180.00` | SOT-666: `180°`-symmetric diode array (`Pin 1/3` ↔ `Pin 6/4`, `Pin 2` `GND` ↔ `Pin 5` `VBUS`; `U7.1` matches EasyEDA `180.00°`). |
| `U8` | `C669687` | `XB9901A` | `Bottom` | `180.0` | `110.0000mm` | `-112.6000mm` | `0.00` | DFN-6 `1.8×1.4`: EasyEDA `-BL` at `0°` places `U8.1..3` (`GND` bar) Bottom, `U8.4..5` (`BAT_N` bar) Top-Right, `U8.6` (`VDD`) Top-Left (`0.000 mm` pad error). |
| `U9` | `C189624` | `LIS2DW12TR` | `Bottom` | `180.0` | `91.2000mm` | `-105.2000mm` | `270.00` | LGA-12 `2×2`: EasyEDA `-BL` at `270°` places `U9.1` (`SCL`) Top-Left in Mirrored `B.Cu`. |
| `Q1` | `C236117` | `NTZD3155CT1G` | `Bottom` | `180.0` | `109.2000mm` | `-107.6000mm` | `270.00` | SOT-563: EasyEDA `-BL` at `270°` places `Q1.1` (`GND`) Top-Left in Mirrored `B.Cu`. |
| `L1, Y1` | `C42411119` / `C20625731` | `2016` / `3225` | `Bottom` | `0.0` | `102.0 / 98.7` | `-113.6 / -98.2` | `180.00` | `L1` start-dot on `+1V1` (`Pad 1`); `Y1.1` (`XIN`) Bottom-Right (`Pads 2, 4 = GND`, `180°`-symmetric). |
| `Q2` | `C2693594` | `XYC-PT19C-L1` | `Top` | `-17.74` | `100.0000mm` | `-70.1000mm` | `342.26` | Top-bezel phototransistor: Collector `Pad 1` West-NW along `-17.74°` (`342.26°`) North edge. |
| `LED1..132` | `C965840` | `XL-1615RGBC-RF` | `Top` | `0.0` | Grid | Grid | `180.00` | `132` top RGB LEDs: `KiCad = 0° + 180° = 180.00°` per EasyEDA `C965840` tape orientation. |
| `R46, R47, C71, C72` | `C11702` / `C1525` | `0402` R / C | `Bottom` | `180.0` | `92.6000mm` | `-79.0..-119.8` | `0.00` | Non-polarized `0402` passives paired east of `SW5`/`SW6`. |

---

## 3. Qty-10 BOM Cost (`export_and_cost.py --cost --qty 10`) & Live JLCPCB PCBA Stock (`2026-11-08`)
- **`p2-132-usb6` BOM @ qty 10:** **`$13.25 / board`** (`+$0.39` over live `p2-132-usb` `$12.86`; `35` unique LCSC parts, `223` placed parts).
- **Live JLCPCB PCBA SMT stock (`selectSmtComponentList/v2`):** **`40/40` BOM lines (`100%`) in stock** (`C2828254` `EVQP7J01P` = `6,887`; `C42411118` `RP2350A` = `3,100`; `C5137654` `AW20198QNR` = `6,055`; `C42411119` `L1` = `1,439`; `C23733` `4.7 µF` = `1,012,436`; `C2860046` `TPS7A0233` = `529`).

---

## 4. Independent Fresh-Context Release Review (`agy` `gemini-4-argon-high`) & Dispositions

| ID | Severity | Finding Summary | Resolution |
|---|---|---|---|
| `B1` | BLOCKER | Earlier `cpl-overlay.png` plotted `B.Cu` in Top-Through coords (`+X` Right) while `3d-bottom.png` is Mirrored Bottom (`+X` Left), making `U1/U2` (`KiCad +90°`, `CPL 0°`) appear mismatched against `U3/U5` (`KiCad 0°`, `CPL 180°`). | **Fixed & Proven**: Re-plotted all `B.Cu` panels in `cpl-overlay.png` in **Mirrored Bottom view (`+X` Left, `-X` Right)** with explicit `K:<KiCad°> C:<CPL°>` labels and added `KiCad Rot` column above (`U1/U2` `KiCad = +90°` + EasyEDA `-BL` -> `CPL = 0.00°`; `U3/U5` `KiCad = 0°` + EasyEDA `-TL` -> `CPL = 180.00°`, `0.00°` error across all `223` parts). |
| `B2` | BLOCKER | `phase10.md` previously omitted `POFV = Yes` for the `118` SMD via-in-pad sites and `1` `U2` EP via touched `B.Paste`. | **Fixed**: Specified **`POFV = Yes` (VIPPO) + `ENIG 1U"`** in §1.C & User Decision #3 below, and removed the redundant 6th `U2` EP via (`729` vias, **`0` EP paste overlaps**). |
| `M1–M4` | MAJOR | `bringup.md` had swapped `C1.1` coords / `R4 = 3.0 kΩ` / `15 ms` debounce and lacked `GCC`/`SRCR` guards; `fab/` lacked `assembly-*.pdf` & `.step`; zip named `gerbers-jlcpcb.zip`. | **Fixed**: Corrected `bringup.md` (`C1.1 = (+4.55, +21.27)`, `R4 = 3.0 kΩ`, `>= 20 ms` debounce, `SRCR = 0x07`, `GCC <= 0x74`/`0x44`, JST polarity + `1.28 mm` `BT1` gap), exported `assembly-bottom.pdf`, `assembly-top.pdf`, & `parallelogram-p2-132-usb6.step`, and exported `parallelogram-p2-132-usb6-gerbers.zip`. |

**Independent Fresh-Context Re-Review Verdict:** **VERDICT: PASS (ready for user sign-off)** (all technical release checks verified; awaiting user sign-off in §5).

---

## 5. Decisions Requiring User Sign-Off (Phase 10 Release)
1. **Approve fab release package (`hw/parallelogram/p2-132-usb6/fab/{parallelogram-p2-132-usb6-gerbers.zip,bom-jlcpcb.csv,cpl-jlcpcb.csv,assembly-bottom.pdf,assembly-top.pdf,parallelogram-p2-132-usb6.step}`):**
   - `4`-layer `JLC04161H-7628` (`1.6 mm` FR-4, `1 oz` outer / `0.5 oz` inner, **`ENIG 1U"`** finish, **`POFV = Yes` (epoxy-filled & copper-capped vias)**, double-sided PCBA with `Pass 2 F.Cu <= 245 °C` for `Q2`), qty-10 BOM **`$13.25 / board`**, `40/40` BOM rows in JLCPCB PCBA stock (`223` assembled parts).
2. **Confirm CPL orientation & `0.45 mm` West-edge actuator overhang on `SW5` (`USER_C`) and `SW6` (`USER_D`):**
   - Verified in Mirrored-Bottom `cpl-overlay.png` and `3d-bottom.png`: `SW5` (`88.825, -78.000`, `Rot = 90°`) and `SW6` (`88.825, -122.800`, `Rot = 90°`) match `SW2`'s `90°` West-facing plunger orientation (`0.25 mm` proud at `0.20 mm` full stroke), while `J1` remains untouched at its inherited `17.74°` (`KiCad = 162.26°`) South-edge angle.
3. **Confirm git release tag (`parallelogram-p2-132-usb6-revP1U6`) upon commit.**
