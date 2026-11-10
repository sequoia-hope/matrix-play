# Gate 10: release (`round-pendant-f-usbc-rtc`)

Status: **awaiting_signoff**
Fab package directory: [hw/round-pendant/f-usbc-rtc/fab/](../../../hw/round-pendant/f-usbc-rtc/fab).
Bring-up plan: [design/bringup-f-usbc-rtc.md](../../bringup-f-usbc-rtc.md).
Stackup & order specification: [design/stackup.md](../../stackup.md) (**`JLC08101H-1080`**).

---

## Checklist (`references/sync-and-release.md` §Gate checklist)

- [x] **All earlier gates current (not stale):**
  - Variant gates `1–9`: [phase1.md](phase1.md) (`passed`), [phase2.md](phase2.md) (`passed`), [phase3.md](phase3.md) (`passed`), [phase4.md](phase4.md) (`awaiting_signoff`), [phase5.md](phase5.md) (`passed`), [phase6.md](phase6.md) (`passed`), [phase7.md](phase7.md) (`passed`), [phase8.md](phase8.md) (`passed`), [phase9.md](phase9.md) (`passed`) — all synced with final `5,883`-track / `918`-via copper, `14/14` outside-courtyard `B.SilkS` pin-1 dots, and `346/346` collision-free assembly maps.
- [x] **Release sync check passes (`sync_check.py --bom --cpl`):** **`PASS: 0 errors, 0 warnings`** (`346` schematic symbols ↔ `346` PCB footprints ↔ `338` assembled parts in `bom-jlcpcb.csv` & `cpl-jlcpcb.csv`; `8` unpopulated test points `TP1..TP8` excluded via `in_bom=no`).
- [x] **DRC & ERC re-run on final files:**
  - `kicad-cli sch erc --severity-all`: **`Found 0 violations`** across all `8` sheets.
  - `kicad-cli pcb drc --severity-all --schematic-parity`: **`Found 0 violations`, `Found 0 unconnected items`**, and only the `2` inherited Variant E/F `U3` pin 42/43 `{slash}` unconnected pin-name strings.
- [x] **Live stock & qty-10 BOM pricing verified (`2026-11-09`):**
  - **Qty-10 BOM cost (`export_and_cost.py --cost`):** **`$27.44 / board`** (`$27.4368`, `35` unique LCSC codes / `37` BOM lines, `338` parts) vs `round-pendant-f-usbc` **`$26.62 / board`** (`$26.6176`) -> **exact delta `+$0.8192 / board` (`+$8.19` for 10 boards)** (`1× BT1 C225111 = $0.0873`, `1× U13 C1542426 = $0.7216`, `C75+C76+R32 = $0.0103`).
  - **Live JLCPCB PCBA SMT stock (`selectSmtComponentList/v2`, §3 below):** **`33/35` unique LCSC part codes are immediately in stock at JLCPCB PCBA** (`C1542426 RX8130CE:BB = 2,242`, `C225111 A1251WR-S-2P = 74,983`, `C530612 TYPE-C-31-M-22 = 2,400`, `C42411119 L1 = 1,299`, and `C1525`/`C52923`/`C25741` as Basic Parts with `0` extra feeder fee). Only the **2 inherited Variant F Global-Sourcing parts** (`C2678907 IS31FL3745-CLS4-TR` WLCSP-36 driver and `C146233 ALS-PT19-315C/L177/TR8` light sensor, or local JLC drop-in `C47416518`) show `0` local JLC SMT stock.
- [x] **CPL rotation & pick-origin verified for `BT1`, `U13`, `J1`, and every polarized part/IC (`338/338`):** Verified against live EasyEDA package data (`BT1 = 0.050 mm` match across all `4` pads at `CPL = 208.00°`, `U13 = 0.000 mm` match across all `10` pads at `CPL = 180.00°`, `J1 = 0.077 mm` match across all `16` pads at `CPL = 336.05°`) + visual overlays [cpl-check-bottom.png](../../renders/round-pendant-f-usbc-rtc/cpl-check-bottom.png) and [cpl-check-top.png](../../renders/round-pendant-f-usbc-rtc/cpl-check-top.png) (§2 below).
- [x] **Gerbers + split PTH/NPTH drills independently parsed & reviewed (`gerbonara` `gerber_npth_audit.py`):**
  - [round-pendant-f-usbc-rtc-gerbers.zip](../../../hw/round-pendant/f-usbc-rtc/fab/round-pendant-f-usbc-rtc-gerbers.zip) (`18` files: `15` Gerber layers + `round-pendant-PTH.drl` [**`918`** holes] + `round-pendant-NPTH.drl` [**`6`** holes] + `.gbrjob`).
  - High-resolution Gerber zoom of `J1`'s two `Ø0.650 mm` NPTH holes: [npth-gerber-zoom.png](../../renders/round-pendant-f-usbc-rtc/npth-gerber-zoom.png) + `17` individual layer PNGs in [design/renders/round-pendant-f-usbc-rtc/gerbers/](../../renders/round-pendant-f-usbc-rtc/gerbers) (§1.C below).
  - Release artifacts in `fab/`: [bom-jlcpcb.csv](../../../hw/round-pendant/f-usbc-rtc/fab/bom-jlcpcb.csv), [cpl-jlcpcb.csv](../../../hw/round-pendant/f-usbc-rtc/fab/cpl-jlcpcb.csv), [assembly-top.pdf](../../../hw/round-pendant/f-usbc-rtc/fab/assembly-top.pdf), [assembly-bottom.pdf](../../../hw/round-pendant/f-usbc-rtc/fab/assembly-bottom.pdf), [schematic.pdf](../../../hw/round-pendant/f-usbc-rtc/fab/schematic.pdf), and [round-pendant-f-usbc-rtc.step](../../../hw/round-pendant/f-usbc-rtc/fab/round-pendant-f-usbc-rtc.step).
- [x] **Bring-up plan written & verified against netlist (`BT1` polarity check, `RX8130CE` `VLF`/`FOUT=OFF`/`AF` init, `POWMAN` `PWRUP2` `GPIO19` wake, `GPIO14 VBAT_EN`, `PDE=0`):** [design/bringup-f-usbc-rtc.md](../../bringup-f-usbc-rtc.md).
- [x] **Final independent review (`research` subagent, fresh context):** Recorded in §4 below.
- [ ] **User release approval (`needs_user` sign-off):** Sign-off items listed in §5 below.

---

## 1. Verbatim Release Check & Gerber Audit Outputs

### A. `sync_check.py --bom --cpl`
```text
sync_check: hw/round-pendant/f-usbc-rtc
  schematic round-pendant.kicad_sch: 346 symbols (0 excluded from board)
  board round-pendant.kicad_pcb: 346 footprints (0 board-only)
  BOM bom-jlcpcb.csv: 338 designators
  CPL cpl-jlcpcb.csv: 338 placements
  338 parts to build; required fields: LCSC
  stock not checked: re-check every LCSC part at release (phase 10)

  PASS: 0 errors, 0 warnings
```

### B. Final `kicad-cli sch erc --severity-all` & `kicad-cli pcb drc --severity-all --schematic-parity`
```text
Found 0 violations
ERC sheets: 8 violations: 0

Found 0 violations
Found 0 unconnected items
Found 2 schematic parity issues
  - Pad net (unconnected-(U3-GPIO28/ADC2-Pad42)) doesn't match net given by schematic (unconnected-(U3-GPIO28{slash}ADC2-Pad42)).
  - Pad net (unconnected-(U3-GPIO29/ADC3-Pad43)) doesn't match net given by schematic (unconnected-(U3-GPIO29{slash}ADC3-Pad43)).
```

### C. Independent `gerbonara` 8-Layer Gerber & `NPTH.drl` Audit (`gerber_npth_audit.py`)
```text
gerber_npth_audit: hw/round-pendant/f-usbc-rtc/fab/gerbers (board round-pendant)
  top_silk                     round-pendant-F_Silkscreen.gto        2346 objects
  top_paste                    round-pendant-F_Paste.gtp              942 objects
  top_mask                     round-pendant-F_Mask.gts               948 objects
  top_copper                   round-pendant-F_Cu.gtl                4100 objects
  inner_1_copper               round-pendant-In1_Cu.g1               1663 objects
  inner_2_copper               round-pendant-In2_Cu.g2                919 objects
  inner_3_copper               round-pendant-In3_Cu.g3               1560 objects
  inner_4_copper               round-pendant-In4_Cu.g4               1551 objects
  inner_5_copper               round-pendant-In5_Cu.g5                920 objects
  inner_6_copper               round-pendant-In6_Cu.g6               1484 objects
  bottom_copper                round-pendant-B_Cu.gbl                2505 objects
  bottom_mask                  round-pendant-B_Mask.gbs               525 objects
  bottom_paste                 round-pendant-B_Paste.gbp              517 objects
  bottom_silk                  round-pendant-B_Silkscreen.gbo         922 objects
  drill_round-pendant-PTH      round-pendant-PTH.drl                  918 objects
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
**Gerber layer object-count & NPTH cross-check ([npth-gerber-zoom.png](../../renders/round-pendant-f-usbc-rtc/npth-gerber-zoom.png)):**
- **`top_paste = 942`:** `235` `XL-1010RGB-YG` LEDs × `4` pads (`940`) + `1` `Q2` `ALS-PT19` × `2` pads (`2`) = **`942` exact** (`0` paste on vias).
- **`top_mask = 948`:** `942` top SMD pads + `6` NPTH mask clearances (`2× J1 Ø0.650 mm` + `4× SW1/SW2 Ø0.700 mm`) = **`948` exact** (`100%` tented/capped PTH vias).
- **`inner_2_copper = 919`:** `1` whole `plane GND` polygon + `918` PTH via pads/antipads = **`919` exact**.
- **`inner_5_copper = 920`:** `2` whole power polygons (`plane VSYS` + `plane 3V3`) + `918` PTH via pads/antipads = **`920` exact**.
- **`bottom_paste = 517` & `bottom_mask = 525`:** `497` (`f-usbc` bottom paste) + `4` (`BT1` `2` sig + `2` MP) + `10` (`U13`) + `4` (`C75/C76`) + `2` (`R32`) = **`517` exact**, plus `8` exposed `TP1..TP8` mask openings (`0` paste on `TP1..TP8`) = **`525` exact**.
- **`drill_round-pendant-PTH = 918` & `drill_round-pendant-NPTH = 6`:** Separate Excellon PTH (`776× 0.25/0.15 mm` + `139× 0.30/0.15 mm` + `3× 0.20/0.10 mm` = **`918`**) and NPTH (`2× Ø0.650 mm` + `4× Ø0.700 mm` = **`6`**) drill files.
- **JLCPCB Order Form Specification ([stackup.md](../../stackup.md)):** **8-layer, `1.0 mm` thickness**, controlled-impedance stackup **`JLC08101H-1080`** (`Er = 4.1`), `1 oz` outer / `0.5 oz` inner copper, **`ENIG 1U"`** finish, **`Via Covering = Epoxy Filled & Capped (POFV = Yes)`** (mandatory so the `13` tented vias beneath `BT1`'s body sit completely planar under LPI mask), double-sided PCBA (`Pass 1 = F.Cu ≤ 250 °C`, `Pass 2 = B.Cu ≤ 250 °C`), and PCBA instruction **`DO NOT ULTRASONIC CLEAN`** (`U13` `RX8130CE:BB` `32.768 kHz` tuning-fork crystal per `ETM50E-10` §12.2.(3) p. 20; also do **not** rotate `BT1` away from `CPL = 208.00°` if JLCPCB DFM flags EasyEDA `C225111`'s swapped internal `1`/`2` pad labels — `208.00°` is the unique 4-pad physical fit).

---

## 2. CPL Rotation & Pick-Origin Verification (`cpl-jlcpcb.csv` + EasyEDA Pad-for-Pad Proof)

Visual verification overlays: [cpl-check-bottom.png](../../renders/round-pendant-f-usbc-rtc/cpl-check-bottom.png) (Mirrored `B.Cu` view: `+X` Left, `-X` Right) and [cpl-check-top.png](../../renders/round-pendant-f-usbc-rtc/cpl-check-top.png).

### New & Relocated Parts (`BT1`, `U13`, `Q1`, `U8`, `C75`, `C76`, `R32`) + `J1`
1. **`BT1` (`CJT A1251WR-S-2P`, `C225111`) on `B.Cu`:**
   - **KiCad footprint pose:** `(89.2000, 110.5500) mm`, `KiCad Rot = -28.00°` (mating mouth facing inward NNE `+28.00°` E of N).
   - **Pick-origin shift (`c_origin` vs KiCad origin):** EasyEDA `C225111`'s `c_origin` sits `+0.200 mm` along local `+Y` (`dx0 = 0.0, dy0 = +0.200 mm`). Rotating `(0, +0.200)` on `B.Cu` at `-28.00°` yields **`Mid X = 89.1061mm`, `Mid Y = -110.7266mm`**.
   - **CPL rotation on `Bottom`:** `(180.0° - (-28.00°) + 0.0°) mod 360° =` **`208.00°`**, aligning both rear signal pads (`(87.521, 112.376)` `VBAT` & `(88.625, 112.962)` `BAT_N`) and both front mechanical mounting tabs (`MP`) with **`0.050 mm` pad-center accuracy** (`0.00°` error; asymmetric front-MP / rear-signal geometry fits only one physical orientation).
2. **`U13` (`Seiko Epson RX8130CE:BB`, `C1542426`) on `B.Cu`:**
   - **KiCad footprint pose:** `(114.7500, 101.2000) mm`, `KiCad Rot = 0.00°`.
   - **Pick-origin & CPL rotation on `Bottom`:** Symmetric `10`-pad `3.2 × 2.5 mm` centroid (`dx0 = 0, dy0 = 0`), **`Mid X = 114.7500mm`, `Mid Y = -101.2000mm`**. EasyEDA `C1542426` `0°` has `Pin 1 (VIO)` Bottom-Left in Top view; on mirrored `B.Cu`, `(180.0° - 0.00°) mod 360° =` **`180.00°`** places `Pin 1` Bottom-Right `(114.250, 102.300)` in Mirrored `B.Cu` with **`0.000 mm` pad-for-pad match** across all `10` pads!

| Ref | LCSC | MPN | Layer | KiCad Rot (°) | Mid X | Mid Y | CPL Rot (°) | EasyEDA Pad-for-Pad & Polarity Proof |
|---|---|---|---|---:|---|---|---:|---|
| **`BT1`** | **`C225111`** | **`A1251WR-S-2P`** | **`Bottom`** | **`-28.00`** | **`89.1061mm`** | **`-110.7266mm`** | **`208.00`** | **New inward battery socket:** `+0.200 mm` `c_origin` shift + `208.00°` aligns `2` rear signal pads + `2` front `MP` tabs (`0.050 mm` match, mouth NNE). |
| **`U13`** | **`C1542426`** | **`RX8130CE:BB`** | **`Bottom`** | **`0.00`** | **`114.7500mm`** | **`-101.2000mm`** | **`180.00`** | **New I2C RTC (`SMD-10P`):** `Pin 1 (VIO)` Bottom-Right `(114.25, 102.30)` in Mirrored `B.Cu` (`0.000 mm` match across all `10` pads). |
| **`C75, C76, R32`** | `C1525` / `C52923` / `C25741` | `0402` passives | `Bottom` | `0.00` | `117.55 / 114.75` | `-101.05..-98.35` | `180.00` | `3×` new `0402` Basic Parts beside `U13` (`0.060–0.077 mm` match). |
| `J1` | `C530612` | `TYPE-C-31-M-22` | `Bottom` | `-156.05` | `108.2778mm` | `-112.0309mm` | `336.05` | Unchanged from `f-usbc` (`0.077 mm` match across all `16` SMD pads). |
| `Q1` | `C236117` | `NTZD3155CT1G` | `Bottom` | `-90.00` | `99.0000mm` | `-116.2500mm` | `180.00` | Relocated SOT-563 dual FET: `Pin 1 (GND)` Top-Right in Mirrored `B.Cu` (`0.010 mm` match). |
| `U8` | `C669687` | `XB9901A` | `Bottom` | `-90.00` | `91.5000mm` | `-114.8000mm` | `270.00` | Relocated DFN-6 LiPo prot: `Pins 1..3 (GND)` East/Left, `Pin 6 (VDD)` NW/Top-Right (`0.257 mm` toe-center match, `0.00°` error). |
| `U1..U7, U9..U12, SW1/2, L1, Y1, Q2, D1..D235` | *(unchanged)* | *(unchanged)* | `Top/Bottom` | *(unchanged)* | *(unchanged)* | *(unchanged)* | *(unchanged)* | Identical poses & CPL rotations to `round-pendant-f-usbc`. |

---

## 3. Live JLCPCB PCBA SMT Stock & Qty-10 Cost (`2026-11-09`, `selectSmtComponentList/v2`)

```text
  C1542426   jlc_stock=2242      type=expand   mpn=RX8130CE:BB            [NEW U13 RTC: +$0.7216/bd @10]
  C225111    jlc_stock=74983     type=expand   mpn=A1251WR-S-2P           [NEW BT1 1.25mm: +$0.0873/bd @10]
  C1525      jlc_stock=33461927  type=base     mpn=CL05B104KO5NNNC        [C75 100nF Basic Part]
  C52923     jlc_stock=10831245  type=base     mpn=CL05A105KA5NQNC        [C76 1uF Basic Part]
  C25741     jlc_stock=11420934  type=base     mpn=0402WGF1003TCE         [R32 100k Basic Part]
  C530612    jlc_stock=2400      type=expand   mpn=TYPE-C-31-M-22
  C42411118  jlc_stock=3080      type=expand   mpn=RP2350A
  C42411119  jlc_stock=1299      type=expand   mpn=AOTA-B201610S3R3-101-T
  C965834    jlc_stock=12842     type=expand   mpn=XL-1010RGB-YG          [2,350 needed for 10 bds]
  ... (all remaining 24 local codes in JLC SMT stock, min = 529 on C2860046 TPS7A0233PDQNR) ...
  C2678907   jlc_stock=0         type=expand   mpn=IS31FL3745-CLS4-TR     [Inherited F: Global Sourcing]
  C146233    jlc_stock=0         type=expand   mpn=ALS-PT19-315C/L177/TR8 [Inherited F: Global Sourcing or C47416518]
```

---

## 4. Independent Fresh-Context Release Review (`research` Subagent)

### Round 1 Review Summary & Dispositions (`0` BLOCKERs; Physical `fab/` Gerbers / Drills / BOM / CPL = `YES` Ready to Send)
- **Reviewer verdict (`research` subagent `12977fef`):** **`YES`** for the physical `hw/round-pendant/f-usbc-rtc/fab/` manufacturing package (`0` BLOCKERs, `0` schematic/PCB/Gerber/BOM/CPL changes needed), conditional on fixing `2` non-fab documentation items (`MAJOR-1`, `MAJOR-2`) and `2` minor prose items (`MINOR-1`, `MINOR-2`):
  - **`MAJOR-1` (`bringup-f-usbc-rtc.md` §4 Step 3.2 `RX8130CE` wakeup-timer `1Ah/1Bh` endianness + `TE` in `1Ch[4]` + `t_str ≤ 1.0 s` `VLF` poll):** **FIXED** in [design/bringup-f-usbc-rtc.md](../../bringup-f-usbc-rtc.md) §4 and [design/parts/rtc-rx8130ce.md](../../parts/rtc-rx8130ce.md) §4.3 — updated to poll `VLF == 0` across `t_str` (`0.19 s` typ, `1.0 s` max per `ETM50E-10` Table 4 p. 12 & Fig. 42 p. 55), pulse `INIEN` (`1Fh = 0x10 -> 0x00`), write `1Ah = 0x02, 1Bh = 0x00` (LSB/MSB), and start countdown via `1Ch = 0xC2 -> 0xD2` (`TE = 1` in `1Ch[4]`, Fig. 48 p. 59).
  - **`MAJOR-2` (`design/decisions.md` row & `design/status.json` entry):** **FIXED** — added the `2026-11-09` `round-pendant-f-usbc-rtc` architecture & waivers row (including under-`BT1` `13` planar POFV tented vias + `1` masked `SW1_4` trace, `RTC_INT` `0 V/ns` sleep crosstalk, and `B.SilkS` waivers) to [design/decisions.md](../../decisions.md) and registered `round-pendant-f-usbc-rtc` in [design/status.json](../../status.json).
  - **`MINOR-1` (`BT1` NNE flat runway `4.88 mm` nominal / `4.65 mm` min to `U4`, `5.85 mm` to `C22` vs `5.25+ mm`):** **FIXED** across `brief-f-usbc-rtc.md`, `bringup-f-usbc-rtc.md`, `phase4.md`, `phase6.md`, `phase10.md`, `review/notes/`, `index.html`, and `pcbview.toml`.
  - **`MINOR-2` & `NOTE-1..3` (`U13` EasyEDA `C1542426` `x = ±1.100 mm` land pattern note, `U13.6` / `8`-pad prose in `phase7/8.md`, `0.312 mm` East copper-to-edge margin, `≤ 85 µA` `P1.7` vs `< 250 µA` `DORMANT` sleep figures, `CPL = 208.00°` DFM note, `DO NOT ULTRASONIC CLEAN`, and `XB9901A` `R8` `122 mW` reverse-hookup note):** **ALL FIXED** across `rtc-rx8130ce.md`, `bringup-f-usbc-rtc.md`, `brief-f-usbc-rtc.md`, and `phase4/7/8/10.md`.

### Round 2 Re-Review (`research` Subagent `12977fef`)
- **Final Verdict:** **`YES — Gate 10 PASSES (0 BLOCKER, 0 MAJOR, 0 MINOR)`**.
- **Summary:** Independently verified all Round-1 fixes (`RX8130CE` `t_str ≤ 1.0 s` `VLF == 0` poll + `INIEN` pulse + `1Ah = 0x02, 1Bh = 0x00` + `1Ch = 0xC2 -> 0xD2` `TE = 1` wakeup timer sequence in `bringup-f-usbc-rtc.md`, `2026-11-09` row in `decisions.md`, `status.json` schema & links, `4.88 mm` nominal / `4.65 mm` min `BT1` flat runway to `U4`, `0.312 mm` East copper-to-edge margin, `DO NOT ULTRASONIC CLEAN` & `BT1 CPL = 208.00°` order notes) while `hw/round-pendant/f-usbc-rtc/*.kicad_pcb`, `*.kicad_sch`, and `fab/*` remained untouched (`0` ERC, `0` DRC, `0` unconnected, `PASS: 0 errors, 0 warnings` in `sync_check.py`, `placement_check.py`, `copper_audit.py`, and `pad_joints_fixed.py`).

---

## 5. Decisions Requiring User Sign-Off (Gate 10 Release)

1. **Inward-Facing `BT1` Pose & Pre-Wired `1.25 mm` LiPo Harness Polarity ([phase4.md](phase4.md), [bringup-f-usbc-rtc.md](../../bringup-f-usbc-rtc.md) §2):** Confirm `BT1` (`CJT A1251WR-S-2P`, `C225111`) at SW `(89.200, 110.550, -28.00°)` facing inward NNE (`4.88 mm` nominal / `4.65 mm` min flat plug-insertion runway to `U4`, `3.20 mm` height = `0 mm` added stack thickness; mate `BT1` before adhering rear `35 mm` LiPo), and verify with a DMM before first mate that your LiPo plug's **RED (`+`) wire mates `Pin 1` (`VBAT`, outer NW / right-hand `+` silk mark)** and **BLACK (`-`) wire mates `Pin 2` (`BAT_N`, inner SE / left-hand `-` silk mark)** (`50/50` commercial `1.25 mm` harness polarity split). Keep `CPL = 208.00°` in JLCPCB DFM review.
2. **East `U13` (`RX8130CE:BB`) Tie-Direct `+3V3` Power Architecture & `GPIO19` Wake ([phase1.md](phase1.md), [phase4.md](phase4.md)):** Confirm `U13` (`C1542426`, `+$0.72/bd`, `0x32` on `I2C1`) powered continuously from always-on `+3V3` (`VIO = VDD = VBAT = +3V3`, `1.50 µA` typ with `FOUT = OFF`, `~79–84 µA` in `POWMAN P1.7` / `~201 µA` in `DORMANT`; include **`DO NOT ULTRASONIC CLEAN`** in PCBA notes).
3. **Inherited `f-usbc` / Variant F Sign-Off Items (`status.json`):**
   - SSE `J1` (`TYPE-C-31-M-22`, `C530612`) pose `(107.787, 110.926, -156.05°)` + `0.05 mm` Kapton over `TP1..TP8` + `3.3–3.5 mm` rear foam standoff under `403535` LiPo + `≤ 0.51 W` continuous worn FW thermal cap (LEDs blanked while `~CHG == 0`; `R4 = 3.0 kΩ` `297 mA` charge rate).
   - JLCPCB Global Sourcing / pre-order for `5× IS31FL3745-CLS4-TR` (`C2678907`) and `Q2` `ALS-PT19` (`C146233`, or local JLC `C47416518`), plus **`JLC08101H-1080`** 8-layer `1.0 mm` ENIG + **`POFV = Yes`** quote (`3× 0.20/0.10 mm` vias inside `U3` `+3V3` band).
