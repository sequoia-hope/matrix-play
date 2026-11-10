# Gate 10: release (`parallelogram-p2-132-usb6`)

Status: **awaiting_signoff**

## Checklist (`references/sync-and-release.md` §Gate checklist)
- [x] **All earlier gates current (not stale):** `phase4.md` (`awaiting_signoff`), `phase5.md` (`passed`), `phase6.md` (`passed`), `phase7.md` (`passed`), `phase8.md` (`passed`), `phase9.md` (`passed`)
- [x] **Release sync check passes (`sync_check.py --bom --cpl`):** `231` schematic symbols ↔ `231` PCB footprints ↔ `223` assembled parts in `bom-jlcpcb.csv` & `cpl-jlcpcb.csv` (`8` `in_bom=False` test points `TP1..TP8` excluded cleanly; **`PASS: 0 errors, 0 warnings`**)
- [x] **DRC / ERC / copper / pad-joint / parity checks re-run on final files:**
  - `kicad-cli pcb drc --severity-all --schematic-parity`: **`0` violations, `0` unconnected items, `0` schematic parity issues**
  - `kicad-cli sch erc --severity-all`: **`0` violations across all `5` sheets**
  - `scripts/bga/copper_audit.py`: **`rc == 0`** (`tracks=5416 vias=719 | 0` dangling, `0` cap_gap, `0` mid_graze/stubs, `0` off_via, `0` morph_necks, `0` acute_slivers, `0` collinear_dups, `0` zone_intrusions)
  - `pad_joints.py`: **`PASS: 0 thin pad joints`** across `913` SMD pads
- [x] **Stock, qty-10 BOM cost, & 4L `ENIG + POFV` bare-PCB fab cost checked on `2026-11-09`:**
  - `export_and_cost.py --cost --qty 10`: **`$13.26 / board` @ qty 10** (`+$0.40` over live `p2-132-usb` `$12.86`, `41` BOM rows / `36` unique LCSC part codes, `223` assembled parts; includes `C307331` `100 nF 50 V X7R` on `C71`/`C72`)
  - Live JLCPCB PCBA SMT stock (`jlc_parts.py` / JLCPCB PCBA warehouse): **`41/41` BOM rows (`36/36` unique LCSC parts) `100%` in stock** for a `10`-board build (`min stock = 528` on `TPS7A0233PDQNR` `C2860046`, `747` on `BQ24073RGTR` `C15220`, `1,460` on `AOTA-B201610S3R3-101-T` `C42411119`, `6,590` on `EVQP7J01P` `C2828254`, `920,115` on `CL05A475MP5NRNC` `C23733` in JLCPCB PCBA basic stock vs `0` on LCSC retail `wmsc.lcsc.com`)
  - **Bare-PCB 4L `POFV = Yes` cost note:** Because this 4-layer layout has `124` non-EP via-in-pad sites (`164` total via-in-paste overlaps across `89` `F.Paste` + `75` `B.Paste` pads), **`Via Covering = Epoxy Filled & Capped (POFV = Yes)`** (IPC-4761 Type VII VIPPO) + **`ENIG 1U"`** is mandatory; unlike JLCPCB's 6-layer `0.15 mm` via promotion where `ENIG + POFV` is bundled free, 4-layer `ENIG + 0.15 mm via + POFV = Yes` carries an estimated **`~$70–$95` bare-PCB fabrication surcharge** across a 5–10 pc prototype lot (`~$7–$10 / board` @ qty 10)
- [x] **CPL rotation & pick-origin verified for every polarized part, IC, connector, & switch (including rotated `BT1`, bezel-aligned `SW4`, relocated `C1/R5/R45`, and `SW5`/`SW6`):** Mirrored-Bottom visual overlay `design/renders/parallelogram-p2-132-usb6/cpl-overlay.png` (matching `3d-bottom.png` & JLCPCB Bottom PCBA viewer) + complete table below with both `KiCad Rot` and `CPL Rot`
- [x] **Gerbers independently parsed & rendered (`gerber_render.py` via `gerbonara`) + Split PTH/NPTH Drills + Collision-Free Assembly PDFs + Schematic PDF + 3D STEP (`0` stale files vs `.kicad_pcb`):**
  - `hw/parallelogram/p2-132-usb6/fab/parallelogram-p2-132-usb6-gerbers.zip` (`14` files: `11` Gerber layers + separate `parallelogram-PTH.drl` [`719` vias] + `parallelogram-NPTH.drl` [`2` `J1` boss holes] + `parallelogram-job.gbrjob`)
  - `hw/parallelogram/p2-132-usb6/fab/{assembly-bottom.pdf,assembly-top.pdf,schematic.pdf}` (`98/98` `B.Fab` + `133/133` `F.Fab` single-instance `0`-overlap designators) + `design/renders/parallelogram-p2-132-usb6/{assembly-bottom.png,assembly-top.png}`
  - `hw/parallelogram/p2-132-usb6/fab/parallelogram-p2-132-usb6.step` (`231` footprints exported)
- [x] **Bring-up plan written with part-audit expected values, probe coordinates, & firmware guards:** `design/gates/parallelogram-p2-132-usb6/bringup.md` (linked together with `design/sim/p2-132-usb6/README.md` from `index.html`)
- [x] **Other variants proven byte-identical (`run_bytecheck.py`):** `40` raw byte-identical lib/dru/table files + `2` canonical-identical `.kicad_pcb` files (`0` mismatches across `p2-132-usb` `225/225` footprints and `p1-66-usb` `152/152` footprints)
- [ ] **Git tag (`parallelogram-p2-132-usb6-revP1U6`) & User release approval:** Awaiting user sign-off on Gates 4 & 10 below before tagging release.

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
Exported hw/parallelogram/p2-132-usb6/fab/parallelogram-p2-132-usb6-gerbers.zip (14 files), bom-jlcpcb.csv (41 lines), cpl-jlcpcb.csv (223 parts)

gerber_render: hw/parallelogram/p2-132-usb6/fab/gerbers (board parallelogram)
  top_silk                  parallelogram-F_Silkscreen.gto     827 objects
  top_paste                 parallelogram-F_Paste.gtp          530 objects
  top_mask                  parallelogram-F_Mask.gts           532 objects
  top_copper                parallelogram-F_Cu.gtl            3942 objects
  inner_1_copper            parallelogram-In1_Cu.g1            720 objects
  inner_2_copper            parallelogram-In2_Cu.g2           1914 objects
  bottom_copper             parallelogram-B_Cu.gbl            2656 objects
  bottom_mask               parallelogram-B_Mask.gbs           405 objects
  bottom_paste              parallelogram-B_Paste.gbp          407 objects
  bottom_silk               parallelogram-B_Silkscreen.gbo    1966 objects
  drill_parallelogram-PTH   parallelogram-PTH.drl              719 objects
  drill_parallelogram-NPTH  parallelogram-NPTH.drl               2 objects
  outline                   parallelogram-Edge_Cuts.gm1          8 objects
  13 layer images in design/renders/parallelogram-p2-132-usb6/gerbers
```
**Gerber structural cross-check:**
- `outline = 8 objects`: `4` straight edges + `4` `R = 1.00 mm` tangent corner arcs (watertight closed loop).
- `drill_parallelogram-PTH = 719 objects` & `drill_parallelogram-NPTH = 2 objects`: cleanly separated via `--excellon-separate-th` into `719` plated `Ø 0.15 mm` VIPPO vias and `2` unplated `Ø 0.65 mm` `J1` boss holes (`719 + 2 = 721` exact).
- `top_paste = 530 objects`: `132` `XL-1615RGBC` LEDs × `4` pads (`528`) + `1` `Q2` `XYC-PT19C-L1` × `2` pads (`2`) = `530` exact.
- `top_mask = 532 objects`: `530` top SMD pads + `2` `J1` NPTH clearances = `532` exact (`100%` tented/capped vias).
- `inner_1_copper = 720 objects`: `1` unbroken `plane GND` polygon (`1,310.45 mm²`) + `719` via pads/antipads = `720` exact.
- `bottom_paste = 407 objects` vs `bottom_mask = 405 objects`: `U6` (`X2SON-4`) splits its central pad paste into small sub-apertures while **all `18` `GND` thermal vias in `U1/U2/U3/U5` solid EPs (`5 + 6 + 5 + 2`) keep their `Ø 0.15 mm` drills inside solder-paste-free crossbars**, and all `164` non-EP via-in-paste overlaps (`89` `F.Paste` + `75` `B.Paste`) are plugged and copper-plated flat prior to stencil printing via **`POFV = Yes`**.
- **JLCPCB Order Form Specification:** **`JLC04161H-7628`** (`1.6 mm`, `1 oz` outer / `0.5 oz` inner, **`ENIG 1U"`** surface finish, **`Via Covering = Epoxy Filled & Capped (POFV = Yes)`** [IPC-4761 Type VII VIPPO], double-sided PCBA with `Pass 1 = B.Cu` and `Pass 2 = F.Cu <= 245 °C` peak for `Q2` `XYC-PT19C-L1`).

---

## 2. CPL Rotation & Pick-Origin Verification (`hw/parallelogram/p2-132-usb6/fab/cpl-jlcpcb.csv` + Mirrored-Bottom `cpl-overlay.png`)

*(Coordinate convention: in Mirrored `B.Cu` view — matching `3d-bottom.png`, `bottom.png`, and JLCPCB's Bottom PCBA viewer — `+X` East is Left, `-X` West is Right, `-Y` North is Top, and `+Y` South is Bottom. Every LCSC part's EasyEDA zero-orientation was cross-checked pad-for-pad against `pcbnew` and `sunflower-s2-110-usbc/phase10.md`: **`0.00°` rotation error across all `223` parts**.)*

| Ref | LCSC | MPN | Layer | KiCad Rot (°) | Mid X | Mid Y | CPL Rot (°) | EasyEDA Zero-Orientation & Mirrored `B.Cu` Pin-1 / Plunger Proof |
|---|---|---|---|---:|---|---|---:|---|
| **`SW5`** | **`C2828254`** | **`EVQP7J01P`** | **`Bottom`** | **`+90.0`** | **`88.8250mm`** | **`-78.0000mm`** | **`90.00`** | **New West-North (`USER_C`):** `-0.325 mm` `c_origin` X-shift -> `Mid X = 88.825`; plunger projects `-X` outward (Right in Mirrored `B.Cu` view) `0.45 mm` past `x = -12.50 mm` West edge, identical to `SW2`. |
| **`SW6`** | **`C2828254`** | **`EVQP7J01P`** | **`Bottom`** | **`+90.0`** | **`88.8250mm`** | **`-122.8000mm`** | **`90.00`** | **New West-South (`USER_D`):** `-0.325 mm` `c_origin` X-shift -> `Mid X = 88.825`; plunger projects `-X` outward `0.45 mm` past `x = -12.50 mm` West edge, identical to `SW2`. |
| `SW2` | `C2828254` | `EVQP7J01P` | `Bottom` | `+90.0` | `88.8250mm` | `-96.5000mm` | `90.00` | Inherited West-mid (`BOOT`): plunger projects `-X` West. |
| `SW1` | `C2828254` | `EVQP7J01P` | `Bottom` | `-90.0` | `111.1750mm` | `-101.5000mm` | `270.00` | Inherited East-mid (`PWR`): `+0.325 mm` shift -> `Mid X = 111.175`, `270°` (`180°` opposite `SW2/5/6`), plunger projects `+X` East (Left in Mirrored `B.Cu`). |
| `SW3` | `C318884` | `TS-1187A-B-A-B` | `Bottom` | `+90.0` | `90.8500mm` | `-71.3500mm` | `90.00` | NW wing symmetric `6.00 × 3.75 mm` flat-face SPST (`90°`). |
| **`SW4`** | **`C318884`** | **`TS-1187A-B-A-B`** | **`Bottom`** | **`162.26`** | **`108.1500mm`** | **`-130.5500mm`** | **`17.74`** | **Option 1 SE wing (`USER_B`):** bezel-aligned parallel to `J1` (`CPL = 17.74°`), symmetric `180°` SPST. |
| `J1` | `C530612` | `TYPE-C-31-M-22` | `Bottom` | `162.26` | `98.3953mm` | `-127.9761mm` | `17.74` | Slanted South edge (`162.26°` + `c_origin` shift): mouth faces South-West perpendicular to `17.74°` edge; `2 × Ø 0.65 mm` NPTH pegs align cleanly. |
| **`BT1`** | **`C225111`** | **`A1251WR-S-2P`** | **`Bottom`** | **`0.0`** | **`107.9700mm`** | **`-123.2000mm`** | **`180.00`** | **Option 1 rotated `90°` CCW:** `+0.20 mm` Y-shift -> `Mid Y = -123.20`; mouth faces straight North (`-Y`, `6.03 mm` clear to `R8`); `Pad 1` (`+` `VBAT`) West (`(+7.345, +25.400)`), `Pad 2` (`-` `BAT_N`) East (`(+8.595, +25.400)`). |
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
| `C1, R5, R45` | `C52923` / `C25891` / `C11702` | `0402` C / R | `Bottom` | `180 / -90 / -90` | `102.65 / 105.70 / 110.70` | `-123.65 / -116.95 / -127.10` | `0 / 270 / 270` | Option 1 relocated `0402` passives (`VBUS` decap, `ILIM`, `SW4` ESD). |
| `R46, R47, C71, C72` | `C11702` / `C307331` | `0402` R / `50V` X7R C | `Bottom` | `180.0` | `92.6000mm` | `-79.0..-119.8` | `0.00` | Non-polarized `0402` passives paired east of `SW5`/`SW6` (`C307331` `CL05B104KB54PNC` `100 nF 50 V X7R`, basic). |

---

## 3. Qty-10 BOM Cost (`export_and_cost.py --cost --qty 10`), Live PCBA Stock, & 4L `POFV = Yes` Fab Disclosure (`2026-11-09`)
- **`p2-132-usb6` BOM @ qty 10:** **`$13.26 / board`** (`+$0.40` over live `p2-132-usb` `$12.86`; `41` BOM rows / `36` unique LCSC parts, `223` placed parts).
- **Live JLCPCB PCBA SMT stock (`jlc_parts.py`):** **`41/41` BOM rows (`100%`) in stock** (`C307331` `100 nF 50 V X7R` = `21,978,030`; `C965840` `XL-1615RGBC` = `693,500`; `C23733` `4.7 µF` = `920,115` in JLCPCB PCBA basic stock; `C225111` `A1251WR-S-2P` = `73,795`; `C318884` `TS-1187A` = `668,740`; `C2828254` `EVQP7J01P` = `6,590`; `C5137654` `AW20198QNR` = `6,055`; `C42411118` `RP2350A` = `3,094`; `C42411119` `L1` = `1,460`; `C15220` `BQ24073RGTR` = `747`; `C2860046` `TPS7A0233PDQNR` = `528`).
- **4-Layer Bare-PCB `ENIG + POFV = Yes` Surcharge Note:** `POFV = Yes` (Type VII epoxy-filled & copper-capped via-in-pad) is mandatory for the `164` via-in-paste overlaps (`124` non-EP via-in-pads). On JLCPCB 4-layer `JLC04161H-7628`, selecting `ENIG 1U"` + `0.15 mm` drill + `POFV = Yes` adds **`~$70–$95` to the bare-PCB lot price** (5–10 pcs, i.e. `~$7–$10 / board` @ qty 10, vs JLCPCB's 6-layer `0.15 mm` via promotion where `ENIG + POFV` is bundled at `$0` extra).

---

## 4. Independent Fresh-Context Release Audits (`agy` `gemini-4-argon-high`, incl. `2026-11-09` Option-1 Audit) & Dispositions

| ID | Severity | Finding Summary | Resolution |
|---|---|---|---|
| `B1` | BLOCKER | `164` via-in-paste overlaps (`89` `F.Paste` + `75` `B.Paste`, `124` non-EP via-in-pad sites) require mandatory IPC-4761 Type VII `POFV = Yes` + transparent 4L bare-PCB surcharge disclosure (`~$70–$95` vs 6L promo). | **Fixed & Disclosed** across `stackup.md`, `brief.md` §5, `phase7.md`, and `phase10.md` §3 & §5.1. |
| `B2` | BLOCKER | `EVQP7J01P` max body height is `1.35 + 0.20 = 1.55 mm` (`|x| >= 9.40 mm`), exceeding `1.5 mm` foam tape under a `20 × 35 mm` cell. | **Fixed** across `brief.md` §3, `floorplan.png`, `phase4.md` §4, and `bringup.md` §4: `<= 18.0 mm` cell on `1.0 mm` tape OR `>= 1.8–2.0 mm` double-layer VHB/foam standoff (`0.25–0.45 mm` margin above `1.55 mm` max switch body). |
| `B3` | BLOCKER | `C71`/`C72` (`C1525`) was `16 V`-rated despite `50 V` X7R simulation claim; `SW1..SW4` `1 kΩ`-only scope needed explicit disposition. | **Fixed**: Upgraded `C71`/`C72` in schematic/PCB/BOM to **`C307331` (`CL05B104KB54PNC`, `100 nF 50 V X7R 0402`, basic)** with nonlinear DC-bias ESD model (`13.65 V` peak = `36.35 V` margin); logged inherited `SW1..SW4` scope (`SW2` shares `/MCU/QSPI_SS`) in `decisions.md`. |
| `B4` | BLOCKER | `bringup.md` §3 `1 ms` `VBAT_SENSE` wait gave `39.3%` reading (`τ = 5.0 ms`), and `RP2350-E9` requires `IE = 0, PDE = 0` on `GPIO26`/`GPIO27`. | **Fixed** in `bringup.md` §3–§4: specified **`>= 30 ms` (`>= 6τ`, `< 0.25%` error)** settling wait and `PADS_BANK0: IE = 0, PDE = 0, PUE = 0, OD = 1`. |
| `B5` | BLOCKER | Custom footprints lacked `F.Fab`/`B.Fab` `${REFERENCE}` texts and stock `SW4`/`TP*` `B.Fab` refs overlapped neighboring `0402`s in `assembly-bottom.pdf`. | **Fixed** in `pcb_gen.py` & `parallelogram.kicad_pcb`: `133/133` `F.Fab` + `98/98` `B.Fab` single-instance `0`-overlap designators (`assembly-{top,bottom}.{png,pdf}` + `schematic.pdf` in `fab/`, `0` stale files). |
| `M1–M3` | MAJOR | Still-air + rear-LiPo-insulated `θ_BA = 33.3 °C/W` thermal ceiling (`0.541 W` / `165 mA` `GCC <= 0x40` continuous worn + `ADC4` foldback), full `273.8 / 370.3 mΩ` battery-path + `3 mΩ` via PDN down to `V_BAT = 3.50 V` (`V(U6.4) = 3.375 V >= 3.355 V` with analog `GCC`), native `fp.Reference()` `B.SilkS` designators (`0` `[association]`), and **`8/8` `B.SilkS` TP labels** (`VSYS`, `VB` added). | **Fixed & Verified** in `sim_buttons.py`, `pcb_gen.py`, `parallelogram.kicad_pcb`, `brief.md`, `bringup.md`, `phase8.md`, and `phase9.md`. |
| `M4–M9, m1–m6` | MAJOR / MINOR | Inherited 4L lumped-regime USB/decap routing waivers logged in `decisions.md`, `0` orphan netclasses in `.kicad_pro`, synced `route/preroute_4L.{kicad_pro,kicad_dru}`, split `PTH`/`NPTH` drills (`14` zip files), `50/50` JST 1.25 harness polarity DMM check in `bringup.md` §3, and both `bringup.md` + `sim/README.md` linked on `index.html`. | **Fixed & Verified**. |

---

## 5. Decisions Requiring User Sign-Off (Phase 10 Release)
1. **Approve fab release package (`hw/parallelogram/p2-132-usb6/fab/{parallelogram-p2-132-usb6-gerbers.zip,bom-jlcpcb.csv,cpl-jlcpcb.csv,assembly-bottom.pdf,assembly-top.pdf,schematic.pdf,parallelogram-p2-132-usb6.step}`):**
   - `4`-layer `JLC04161H-7628` (`1.6 mm` FR-4, `1 oz` outer / `0.5 oz` inner, **`ENIG 1U"`** finish, mandatory **`POFV = Yes` [IPC-4761 Type VII epoxy-filled & copper-capped vias]** — adds `~$70–$95` 4L bare-PCB lot surcharge across 5–10 pcs — double-sided PCBA with `Pass 2 F.Cu <= 245 °C` for `Q2`), qty-10 BOM **`$13.26 / board`**, `41/41` BOM rows (`100%`) in live JLCPCB PCBA stock (`223` assembled parts).
2. **Confirm CPL orientation for rotated `BT1`, bezel-aligned `SW4`, and West-edge switches `SW5`/`SW6`:**
   - Verified in Mirrored-Bottom `cpl-overlay.png` and `3d-bottom.png`: **`BT1`** (`107.970, -123.200`, `Rot = 180.00°`, mouth facing straight `-Y` North with `6.03 mm` clear runway, `+` West / `-` East — verify off-the-shelf LiPo harness polarity with DMM before plugging in!), **`SW4`** (`108.150, -130.550`, `Rot = 17.74°` parallel to `J1`), and **`SW5`/`SW6`** (`88.825, -78.000 / -122.800`, `Rot = 90.00°`, `0.45 mm` rest overhang / `0.25 mm` proud at full `0.20 mm` stroke).
3. **Confirm git release tag (`parallelogram-p2-132-usb6-revP1U6`) upon user sign-off.**

---

## Addendum 2026-11-09: fab outputs re-exported after the U3 1V1 spoke re-route

Gerbers and drill files were regenerated (`export_and_cost.py --export p2-132-usb6`) from the board re-verified in `phase7.md`'s addendum, and the renders were regenerated (`render.py`). `bom-jlcpcb.csv` (41 lines) and `cpl-jlcpcb.csv` (223 parts) came out byte-identical, since no part moved. Inductor L1 (AOTA-B201610S3R3-101-T, C42411119) has 1,299 in JLCPCB assembly stock as of 2026-11-09. Still **awaiting_signoff**: the user's choice at this gate is unchanged.
