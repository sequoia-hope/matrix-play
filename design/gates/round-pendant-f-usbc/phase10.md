# Gate 10: release (`round-pendant-f-usbc`)

Status: **awaiting_signoff**
Fab package directory: [hw/round-pendant/f-usbc/fab/](../../../hw/round-pendant/f-usbc/fab).
Bring-up plan: [design/bringup-f-usbc.md](../../bringup-f-usbc.md).
Stackup & order specification: [design/stackup.md](../../stackup.md) (**`JLC08101H-1080`**).

---

## Checklist (`references/sync-and-release.md` §Gate checklist)

- [x] **All earlier gates current (not stale):**
  - Parent gates `0–3`: `passed` ([phase0.md](../phase0.md)–[phase3.md](../phase3.md)) + `J1` `TYPE-C-31-M-22` datasheet & schematic verified (`0` ERC violations across `8` sheets)
  - Variant gates: [phase4.md](phase4.md) (`awaiting_signoff`), [phase5.md](phase5.md) (`passed`), [phase6.md](phase6.md) (`passed`), [phase7.md](phase7.md) (`passed`), [phase8.md](phase8.md) (`passed`), [phase9.md](phase9.md) (`passed`) — all updated with final `5,555`-track / `886`-via copper and independent `agy` review records.
- [x] **Release sync check passes (`sync_check.py --bom --cpl`):** **`PASS: 0 errors, 0 warnings`** (`342` schematic symbols ↔ `342` PCB footprints ↔ `333` assembled parts in `bom-jlcpcb.csv` & `cpl-jlcpcb.csv`; `9` unpopulated solder/test footprints `BT1, TP1..TP8` excluded via `in_bom=no`).
- [x] **DRC & ERC re-run on final files:**
  - `kicad-cli sch erc --severity-all`: **`Found 0 violations`** across all `8` sheets.
  - `kicad-cli pcb drc --severity-all --schematic-parity`: **`Found 0 violations`, `Found 0 unconnected items`**, and only the `2` inherited Variant E/F `U3` pin 42/43 `{slash}` unconnected pin-name strings (explicitly named per task instructions rather than hidden).
- [x] **Live stock & qty-10 BOM pricing verified (`2026-11-08`):**
  - **Qty-10 BOM cost (`export_and_cost.py --cost`):** **`$26.62 / board`** (`$26.6179`) vs Variant F **`$26.26 / board`** (`$26.2573`) -> **exact delta `+$0.3606 / board` (`+$3.61` for 10 boards)** for `1× J1 C530612 (TYPE-C-31-M-22)`.
  - **Live JLCPCB PCBA SMT stock (`selectSmtComponentList/v2`, §3 below):** **`31/33` unique LCSC part codes are immediately in stock at JLCPCB PCBA** (`C530612 TYPE-C-31-M-22 = 2,410`, `C42411119 L1 = 1,357`, `C23733 4.7 µF = 1,003,226`, `min stock = 529` on `C2860046 TPS7A0233PDQNR`). Only the **2 inherited Variant F Global-Sourcing parts** (`C2678907 IS31FL3745-CLS4-TR` WLCSP-36 driver and `C146233 ALS-PT19-315C/L177/TR8` light sensor, which also has local JLC drop-in `C47416518`) show `0` local JLC SMT stock (`status.json` `inductor-preorder` & `sensor-part`).
- [x] **CPL rotation & pick-origin verified for `J1` on `B.Cu` and every polarized part/IC (`333/333`):** Verified against live EasyEDA package data (`0.077 mm` RMS pad-for-pad match across all `16` SMD pads of `J1` at `CPL Rotation = 336.05°`, `Mid = (108.2778mm, -112.0309mm)`) + visual overlays [cpl-check-bottom.png](../../renders/round-pendant-f-usbc/cpl-check-bottom.png) and [cpl-check-top.png](../../renders/round-pendant-f-usbc/cpl-check-top.png) (§2 below).
- [x] **Gerbers + split PTH/NPTH drills independently parsed & reviewed (`gerbonara` `gerber_npth_audit.py`):**
  - [round-pendant-f-usbc-gerbers.zip](../../../hw/round-pendant/f-usbc/fab/round-pendant-f-usbc-gerbers.zip) (`18` files: `15` Gerber layers + `round-pendant-PTH.drl` [**`886`** holes] + `round-pendant-NPTH.drl` [**`6`** holes] + `.gbrjob`).
  - High-resolution Gerber zoom of `J1`'s two `Ø0.650 mm` NPTH holes against `F_Cu.gtl`, `F_Mask.gts`, `F_Silkscreen.gto`, and `B_Paste.gbp`: [npth-gerber-zoom.png](../../renders/round-pendant-f-usbc/npth-gerber-zoom.png) + `17` individual layer PNGs in [design/renders/round-pendant-f-usbc/gerbers/](../../renders/round-pendant-f-usbc/gerbers) (§1.C below).
  - Release artifacts in `fab/`: [bom-jlcpcb.csv](../../../hw/round-pendant/f-usbc/fab/bom-jlcpcb.csv), [cpl-jlcpcb.csv](../../../hw/round-pendant/f-usbc/fab/cpl-jlcpcb.csv), [assembly-top.pdf](../../../hw/round-pendant/f-usbc/fab/assembly-top.pdf), [assembly-bottom.pdf](../../../hw/round-pendant/f-usbc/fab/assembly-bottom.pdf), [schematic.pdf](../../../hw/round-pendant/f-usbc/fab/schematic.pdf), and [round-pendant-f-usbc.step](../../../hw/round-pendant/f-usbc/fab/round-pendant-f-usbc.step).
- [x] **Bring-up plan written & verified against netlist (`GPIO14 VBAT_EN`, `PDE=0`, `R14/R15 = 27 Ω`):** [design/bringup-f-usbc.md](../../bringup-f-usbc.md) (linked from `index.html`).
- [x] **Final independent review (`agy` `gemini-4-argon-high`):** Round-1 findings resolved & Round-2 re-review appended in §4 below.
- [ ] **Git tag (`round-pendant-f-usbc-revFU`) & User release approval:** Git commit/tag deferred per supervising-agent workspace rule (*"Do not commit or push"*); user sign-off items listed in §5 below.

---

## 1. Verbatim Release Check & Gerber Audit Outputs

### A. `sync_check.py --bom --cpl`
```text
sync_check: hw/round-pendant/f-usbc
  schematic round-pendant.kicad_sch: 342 symbols (0 excluded from board)
  board round-pendant.kicad_pcb: 342 footprints (0 board-only)
  BOM bom-jlcpcb.csv: 333 designators
  CPL cpl-jlcpcb.csv: 333 placements
  333 parts to build; required fields: LCSC
  stock not checked: re-check every LCSC part at release (phase 10)

  PASS: 0 errors, 0 warnings
```

### B. Final `kicad-cli sch erc --severity-all` & `kicad-cli pcb drc --severity-all --schematic-parity`
```text
Found 0 violations
Saved ERC Report to /tmp/fusbc_erc.json
ERC sheets: 8 violations: 0

Found 0 violations
Found 0 unconnected items
Found 2 schematic parity issues
  - Pad net (unconnected-(U3-GPIO28/ADC2-Pad42)) doesn't match net given by schematic (unconnected-(U3-GPIO28{slash}ADC2-Pad42)).
  - Pad net (unconnected-(U3-GPIO29/ADC3-Pad43)) doesn't match net given by schematic (unconnected-(U3-GPIO29{slash}ADC3-Pad43)).
```

### C. Independent `gerbonara` 8-Layer Gerber & `NPTH.drl` Audit (`gerber_npth_audit.py`)
```text
gerber_npth_audit: hw/round-pendant/f-usbc/fab/gerbers (board round-pendant)
  top_silk                     round-pendant-F_Silkscreen.gto        2346 objects
  top_paste                    round-pendant-F_Paste.gtp              942 objects
  top_mask                     round-pendant-F_Mask.gts               948 objects
  top_copper                   round-pendant-F_Cu.gtl                3948 objects
  inner_1_copper               round-pendant-In1_Cu.g1               1609 objects
  inner_2_copper               round-pendant-In2_Cu.g2                887 objects
  inner_3_copper               round-pendant-In3_Cu.g3               1443 objects
  inner_4_copper               round-pendant-In4_Cu.g4               1521 objects
  inner_5_copper               round-pendant-In5_Cu.g5                888 objects
  inner_6_copper               round-pendant-In6_Cu.g6               1396 objects
  bottom_copper                round-pendant-B_Cu.gbl                2408 objects
  bottom_mask                  round-pendant-B_Mask.gbs               507 objects
  bottom_paste                 round-pendant-B_Paste.gbp              497 objects
  bottom_silk                  round-pendant-B_Silkscreen.gbo         965 objects
  drill_round-pendant-PTH      round-pendant-PTH.drl                  886 objects
  drill_round-pendant-NPTH     round-pendant-NPTH.drl                   6 objects
  outline                      round-pendant-Edge_Cuts.gm1              2 objects

=== INDEPENDENT GERBONARA NPTH DRILL AUDIT (6 holes in NPTH.drl) ===
  NPTH #1: Gerber (X=104.6710 mm, Y=-111.0300 mm) => KiCad (104.671, 111.030) mm, dia=0.650 mm
  NPTH #2: Gerber (X=109.9530 mm, Y=-108.6840 mm) => KiCad (109.953, 108.684) mm, dia=0.650 mm
  NPTH #3: Gerber (X=83.0190 mm, Y=-93.3960 mm) => KiCad (83.019, 93.396) mm, dia=0.700 mm
  NPTH #4: Gerber (X=84.6960 mm, Y=-94.0490 mm) => KiCad (84.696, 94.049) mm, dia=0.700 mm
  NPTH #5: Gerber (X=115.3590 mm, Y=-94.0270 mm) => KiCad (115.359, 94.027) mm, dia=0.700 mm
  NPTH #6: Gerber (X=117.0370 mm, Y=-93.3750 mm) => KiCad (117.037, 93.375) mm, dia=0.700 mm
```
**Gerber layer object-count & NPTH cross-check ([npth-gerber-zoom.png](../../renders/round-pendant-f-usbc/npth-gerber-zoom.png)):**
- **`top_paste = 942`:** `235` `XL-1010RGB-YG` LEDs × `4` pads (`940`) + `1` `Q2` `ALS-PT19` × `2` pads (`2`) = **`942` exact** (`0` paste on vias).
- **`top_mask = 948`:** `942` top SMD pads + `6` NPTH mask clearances (`2× J1 Ø0.650 mm` + `4× SW1/SW2 Ø0.700 mm`) = **`948` exact** (`100%` tented/capped PTH vias).
- **`inner_2_copper = 887`:** `1` whole `plane GND` polygon + `886` PTH via pads/antipads = **`887` exact**.
- **`inner_5_copper = 888`:** `2` whole power polygons (`plane VSYS` + `plane 3V3`) + `886` PTH via pads/antipads = **`888` exact**.
- **`drill_round-pendant-PTH = 886` & `drill_round-pendant-NPTH = 6`:** Separate Excellon PTH (`744× 0.25/0.15 mm` + `139× 0.30/0.15 mm` + `3× 0.20/0.10 mm`) and NPTH (`2× Ø0.650 mm` + `4× Ø0.700 mm`) drill files ensure JLCPCB never plates `J1`'s or `SW1/SW2`'s plastic peg holes; [npth-gerber-zoom.png](../../renders/round-pendant-f-usbc/npth-gerber-zoom.png) confirms both `Ø0.650 mm` NPTH holes clear every `F_Cu.gtl` LED pad (`0.220 mm`), `F_Cu.gtl` trace (`0.214 mm`), `In3_Cu.g3` trace (**`0.304 mm`**), and `F_Silkscreen.gto` Voronoi web stroke (**`0.199 mm`**), while `B_Paste.gbp` covers all `4` `S1` SMD shell pads + `12` rear USB-C signal/power pads cleanly (`0` paste on `BT1` or `TP1..TP8`).
- **JLCPCB Order Form Specification ([stackup.md](../../stackup.md)):** **8-layer, `1.0 mm` thickness**, controlled-impedance stackup **`JLC08101H-1080`** (`Er = 4.1`, `4× 1080` prepreg `0.0764 mm` + `3× 0.170 mm` core), `1 oz` outer / `0.5 oz` inner copper, **`ENIG 1U"`** finish, **`Via Covering = Epoxy Filled & Capped (POFV = Yes)`**, double-sided PCBA (`Pass 1 = F.Cu ≤ 250 °C`, `Pass 2 = B.Cu ≤ 250 °C`).

---

## 2. CPL Rotation & Pick-Origin Verification (`cpl-jlcpcb.csv` + EasyEDA Pad-for-Pad Proof)

Visual verification overlays: [cpl-check-bottom.png](../../renders/round-pendant-f-usbc/cpl-check-bottom.png) (Mirrored `B.Cu` view: `+X` Left, `-X` Right) and [cpl-check-top.png](../../renders/round-pendant-f-usbc/cpl-check-top.png).

### `J1` (`TYPE-C-31-M-22`, `C530612`) on `B.Cu` Derivation
- **KiCad footprint pose on `B.Cu`:** `(107.7870, 110.9260) mm`, `KiCad Rot = -156.05°` (`203.95°`).
- **Pick-origin shift (`c_origin` vs KiCad origin):** EasyEDA `C530612`'s pick centroid sits `-1.204 mm` along local `+Y` (toward the front shell mouth relative to KiCad's origin). Rotating `(0, -1.204)` on `B.Cu` at `-156.05°` yields **`Mid X = 108.2778mm`, `Mid Y = -112.0309mm`**.
- **CPL rotation on `Bottom`:** EasyEDA `C530612` `0°` has the `12` signal pins North and mouth South; on mirrored `B.Cu` (`CPL = (180° - KiCad_Rot) mod 360°` = `(180° - (-156.05°)) mod 360°`), **`CPL Rotation = 336.05°`** (`-23.95°`), aligning all `12` `0.50 mm`-pitch rear SMD fingers (`A1B12..B1A12`) and all `4` `S1` shell tabs with **`0.077 mm` RMS pad-center accuracy** and `0.00°` rotation error!

| Ref | LCSC | MPN | Layer | KiCad Rot (°) | Mid X | Mid Y | CPL Rot (°) | EasyEDA Pad-for-Pad & Polarity Proof |
|---|---|---|---|---:|---|---|---:|---|
| **`J1`** | **`C530612`** | **`TYPE-C-31-M-22`** | **`Bottom`** | **`-156.05`** | **`108.2778mm`** | **`-112.0309mm`** | **`336.05`** | **New SMD USB-C:** `1.204 mm` `c_origin` shift + `336.05°` aligns `12` rear pins NE-NW & mouth SSE (`0.077 mm` pad match across all `16` pads). |
| `SW1` | `C388883` | `EVQP7C01P` | `Bottom` | `-68.75` | `116.5115mm` | `-93.5790mm` | `248.75` | `-0.336 mm` plunger centroid shift; plunger faces outward NE (`0.051 mm` pad match). |
| `SW2` | `C388883` | `EVQP7C01P` | `Bottom` | `+68.75` | `83.5445mm` | `-93.6008mm` | `111.25` | `-0.336 mm` plunger centroid shift; plunger faces outward NW (`0.051 mm` pad match). |
| `U7` | `C15999` | `USBLC6-2P6` | `Bottom` | `+113.95` | `100.1000mm` | `-112.4000mm` | `246.05` | Relocated SOT-666 ESD: `Pin 2 (GND)` NE, `Pin 5 (VBUS)` SW (`0.000 mm` pad match). |
| `U8` | `C669687` | `XB9901A` | `Bottom` | `-90.00` | `96.4000mm` | `-116.4000mm` | `270.00` | Relocated DFN-6 LiPo prot: `Pins 1..3 (GND)` East, `Pin 6 (VDD)` NW, `Pins 4..5 (BAT_N)` SW (`0.000 mm` pad match). |
| `U1,U2,U10..12` | `C2678907` | `IS31FL3745-CLS4-TR` | `Bottom` | `0.00` | *(5 sites)* | *(5 sites)* | `180.00` | `5×` WLCSP-36: `A1` ball Bottom-Right in Mirrored `B.Cu` (`180.00°`, `0.000 mm` match). |
| `U3` | `C42411118` | `RP2350A` | `Bottom` | `0.00` | `98.6000mm` | `-93.4000mm` | `180.00` | QFN-60: EasyEDA `-TL` `0°` -> `180.00°` places `Pin 1` Bottom-Right in Mirrored `B.Cu`. |
| `U4` | `C190862` | `W25Q128JVPIQ` | `Bottom` | `+90.00` | `97.2000mm` | `-105.4000mm` | `0.00` | WSON-8 `6×5`: EasyEDA `-BL` `0°` places `Pin 1` Bottom-Left in Mirrored `B.Cu`. |
| `U5` | `C15220` | `BQ24073RGTR` | `Bottom` | `0.00` | `103.4000mm` | `-106.0000mm` | `180.00` | QFN-16: EasyEDA `-TL` `0°` -> `180.00°` places `Pin 1` Bottom-Right in Mirrored `B.Cu`. |
| `U6` | `C2860046` | `TPS7A0233PDQNR` | `Bottom` | `+180.00` | `93.9000mm` | `-100.4000mm` | `0.00` | X2SON-4 `1×1`: EasyEDA `-TL` `0°` places `Pin 1 (+3V3)` Top-Left `(94.330, 100.075)` in Mirrored `B.Cu`. |
| `U9` | `C189624` | `LIS2DW12TR` | `Bottom` | `+180.00` | `104.4000mm` | `-86.2000mm` | `270.00` | LGA-12 `2×2`: EasyEDA `-BL` `270.00°` places `Pin 1 (SCL)` Top-Left in Mirrored `B.Cu`. |
| `Q1` | `C236117` | `NTZD3155CT1G` | `Bottom` | `+180.00` | `91.8000mm` | `-112.4000mm` | `270.00` | SOT-563 dual FET: `Pin 1 (GND)` Top-Left in Mirrored `B.Cu` (`0.000 mm` match). |
| `L1, Y1` | `C42411119` / `C20625731` | `AOTA-3R3` / `ABM8-272` | `Bottom` | `0.00` | `100.6 / 97.3` | `-100.6 / -85.2` | `180.00` | `L1` `Pad 1 (+1V1)` Right (3D STEP model rotation aligned to `0°`); `Y1` `180°`-symmetric `4`-pad `12 MHz` crystal. |
| `Q2` | `C146233` | `ALS-PT19-315C` | `Top` | `+6.00` | `97.9600mm` | `-81.9600mm` | `6.00` | Top-rim phototransistor: Collector `Pad 1` West, matching `F.SilkS` `OD = 0.30 mm` dot. |
| `D1..D235` | `C965834` | `XL-1010RGB-YG` | `Top` | *spiral* | *spiral* | *spiral* | `(Ki+90)%360` | `235` top RGB LEDs (`D1`: `Ki=+146.42°` -> `CPL=236.42°`, `0.000 mm` 4-pad match). |

---

## 3. Live JLCPCB PCBA SMT Stock & Qty-10 Cost (`2026-11-08`, `selectSmtComponentList/v2`)

```text
  C530612    jlc_stock=2410      type=expand   mpn=TYPE-C-31-M-22         [NEW J1: +$0.3606/bd @10]
  C42411118  jlc_stock=3080      type=expand   mpn=RP2350A
  C42411119  jlc_stock=1357      type=expand   mpn=AOTA-B201610S3R3-101-T [Restocked in JLC SMT!]
  C965834    jlc_stock=12842     type=expand   mpn=XL-1010RGB-YG          [2,350 needed for 10 bds]
  C15220     jlc_stock=749       type=expand   mpn=BQ24073RGTR
  C2860046   jlc_stock=529       type=expand   mpn=TPS7A0233PDQNR
  C15999     jlc_stock=20150     type=expand   mpn=USBLC6-2P6
  C669687    jlc_stock=2947      type=expand   mpn=XB9901A
  C190862    jlc_stock=12773     type=expand   mpn=W25Q128JVPIQ
  C189624    jlc_stock=51846     type=expand   mpn=LIS2DW12TR
  C388883    jlc_stock=12451     type=expand   mpn=EVQP7C01P
  C20625731  jlc_stock=9421      type=expand   mpn=ABM8-272-T3
  C236117    jlc_stock=7923      type=expand   mpn=NTZD3155CT1G
  C23733     jlc_stock=1003226   type=base     mpn=CL05A475MP5NRNC
  ... (all remaining 17 passive codes: 494,139 to 33,461,927 in JLC SMT stock) ...
  C2678907   jlc_stock=0         type=expand   mpn=IS31FL3745-CLS4-TR     [Inherited F: Global Sourcing]
  C146233    jlc_stock=0         type=expand   mpn=ALS-PT19-315C/L177/TR8 [Inherited F: Global Sourcing or C47416518]
```

---

## 4. Independent Fresh-Context Release Review History (`agy` `gemini-4-argon-high`)

### Round 1 Review Summary & Dispositions (`0` BLOCKERs; CAD / Gerbers / BOM / CPL = FAB-READY)
- **`MAJOR-1` (`bringup-f-usbc.md` toggling `GPIO28` instead of `GPIO14 VBAT_EN` & omitting `PDE = 0` sleep init):** **FIXED** in [design/bringup-f-usbc.md](../../bringup-f-usbc.md) (§4 Step 3.1 `PDE = 0` on `GPIO2–5, 11, 12, 13`; §5 Steps 4.1–4.2 driving `GPIO14` [`U3` Pin 18] `VBAT_EN`).
- **`MAJOR-2` (Stale 6-layer `stackup.md` without JLCPCB 8L stackup code):** **FIXED** — updated [design/stackup.md](../../stackup.md) with the 8-layer `1.00 mm` **`JLC08101H-1080`** stackup table (`Er = 4.1`), impedance notes, and DRC severity list.
- **`MAJOR-3` (Gate 4–9 review closeout & `2` Global-Sourcing BOM lines `C2678907`, `C146233`):** **FIXED + FLAGGED FOR USER SIGN-OFF (§5 below)** — appended all Round-1 dispositions + Round-2 re-reviews across `phase4.md..phase10.md`, and listed `C2678907` / `C146233` pre-order / `C47416518` substitute in §5.
- **`MINOR-1..6` & `NOTE-2` (`403535` `0.66C–0.81C` C-rate note, `R14/R15 = 27 Ω` & `{D234, D235, D231, D226}`/`{D76, D66, D74, D64}` NPTH callouts, `3× 0.20/0.10 mm` vias count, `L1` 3D STEP dot rotation, `2-Ø0.50 mm` pegs & `U6` `-TL` Pin 1 prose, `0.304 mm` `In3.Cu` NPTH #1 nudge):** **ALL FIXED** across `round-pendant.kicad_pcb`, `bringup-f-usbc.md`, `brief-f-usbc.md`, and `phase4.md..phase10.md`.

### Round 2 Re-Review (`agy` `gemini-4-argon-high`)
**Verdict: YES — Ready to send to fab once the listed user sign-off / Global-Sourcing items in §5 are confirmed (`0 BLOCKER, 0 MAJOR, 2 MINOR, 1 NOTE`)**:
- Independently re-derived `J1` CPL on `B.Cu` (`(107.7870, 110.9260, -156.05°)` -> `Mid = (108.2778mm, -112.0309mm), Bottom, 336.05°`) and visually verified pad-for-pad alignment across all `16` `J1` SMD pads and all `332` other placements (`U1..U12, Q1, Q2, L1, Y1, SW1/SW2, D1..D235`).
- Verified split `PTH` (`886` vias: `744× 0.25 + 139× 0.30 + 3× 0.20`) / `NPTH` (`6` unplated holes) drills, `J1` `Ø0.650 mm` NPTH clearances (`0.220 mm` to `F.Cu` LED pads `D234.4`/`D74.3`, `0.214 mm` to `CS2_12`, `0.304 mm` on `In3.Cu`, `≥ 0.201 mm` on all 8 Cu layers), `342 = 333 + 9` sync, `ERC = 0`, `DRC = 0` (`2` `U3` `{slash}` parity strings), `JLC08101H-1080` stackup, and `bringup-f-usbc.md` (`GPIO14 VBAT_EN`, `PDE = 0`, `12 mA` I2C0 + `LGC = 1`).
- **`MINOR-1`, `MINOR-2`, & `NOTE-1` (Prose callouts: `{D234, D235, D231, D226}` / `{D76, D66, D74, D64}` 4-LED NPTH pockets, `0.300 mm` CAD `BT1.2 ↔ U8.1..3` mask dam + temporary Kapton masking during wire attach, `R4 = C25784`, and `744 + 139 + 3 = 886` via tally):** **FIXED immediately above** in `bringup-f-usbc.md`, `brief-f-usbc.md`, `stackup.md`, `decisions.md`, and `phase4/6/10.md`.

---

## 5. Decisions Requiring User Sign-Off (Gate 10 Release)
1. **SSE Connector Pose & SMD-Only Shell Hold-Down ([phase4.md](phase4.md) §3):** Confirm `J1` (`TYPE-C-31-M-22`, `C530612`, `+$0.36/bd`) at SSE `(107.787, 110.926, -156.05°)` (`23.95°` E of S, `8.35°` non-radial skew, `0` LEDs moved, two `Ø0.65 mm` front mask web apertures with `Ø0.50 × 0.70 mm` pegs recessed `0.30 mm` below `F.Cu`, `4× 2.30 × 1.80 mm` gull-wing SMD shell pads — use straight axial plug insertion or housing capture / corner epoxy).
2. **Inherited Sourcing & 8-Layer Quote Items (`status.json`):**
   - Confirm JLCPCB Global Sourcing / pre-order for `5× IS31FL3745-CLS4-TR` (`C2678907`) and whether `Q2` stays `ALS-PT19` (`C146233` via Global Sourcing) or swaps to local JLC `Tonyu DYWH-ALS-PT19-315C/4T` (`C47416518`). *(Note: `L1` `C42411119` is back in local JLCPCB PCBA stock at `1,357` pcs!)*
   - Confirm JLCPCB quote-tool acceptance of **`JLC08101H-1080`** (`1.0 mm` 8-layer ENIG + `POFV = Yes`) and the **`3×` inherited `0.20/0.10 mm` vias** (`10:1` aspect ratio) inside `U3`'s `+3V3` band (`jlc-8l-quote`), plus inherited plane-only decoupling on `U3` `IOVDD` pins `11/54` (`decap-11-54`).
3. **`403535` LiPo Charge Rate (`R4 = 3.0 kΩ` = `297 mA`) & Rear Mechanical Stackup:** Confirm your `403535` (`~400–450 mAh`) cell datasheet permits `0.66C–0.81C` charging (or swap `R4` to `4.3 kΩ` [`207 mA`] / `4.7 kΩ` [`189 mA`] for `≤ 0.5C`), and confirm `0.05 mm` Kapton tape over `TP1..TP8`/`BT1` + `3.3–3.5 mm` foam standoff matching `J1`'s `3.16–3.26 mm` rear height (with firmware enforcing the `≤ 0.51 W` continuous worn thermal ceiling and LED blanking while `~CHG == 0`).
