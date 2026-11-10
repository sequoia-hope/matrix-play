# Gate 4: mechanical and layout brief (`round-pendant-f-usbc-rtc`)

Status: **awaiting_signoff**
Parent gates cited for unchanged requirements & parts: [phase0.md](../phase0.md)–[phase4.md](../phase4.md) and [round-pendant-f-usbc/phase4.md](../round-pendant-f-usbc/phase4.md).
Variant brief: [design/brief-f-usbc-rtc.md](../../brief-f-usbc-rtc.md) (delta against [design/brief-f-usbc.md](../../brief-f-usbc.md) and [design/intent.md](../../intent.md)).

---

## Checklist (`references/intent-and-brief.md` §Phase 4)

- [x] **1. Board outline and size:** Unchanged `Ø38.000 mm` circle (`center = (100.000, 100.000) mm`, `radius = 19.000 mm`; [brief-f-usbc-rtc.md](../../brief-f-usbc-rtc.md) §1). `J1` (`TYPE-C-31-M-22`) stays identical to `f-usbc` (`0.440–0.530 mm` `S1` pad-corner clearance); `BT1` (`CJT A1251WR-S-2P`, `C225111`) sits completely recessed inside the SW rim (`≥ 0.65 mm` housing courtyard margin, `0.790 mm` rear signal-pad margin, `0.00 mm` rim overhang); East RTC block (`U13, C75, C76, R32`) maintains `≥ 0.312 mm` copper-to-edge clearance (`CS5_1` via `@(118.493, 101.614)`, `> 1.56×` the `0.200 mm` DRC floor).
- [x] **2. Mounting holes & bezel/runway geometry:** `0` mounting holes (`6` total NPTH locating holes unchanged from `f-usbc`: `2× Ø0.650 mm` for `J1` + `4× Ø0.700 mm` for `SW1/SW2`; `BT1` `A1251WR-S-2P` is pure 4-pad SMT with `0` locating pegs and requires `0` bezel cutouts).
- [x] **3. Connector & RTC placement:**
  - **`BT1` (`CJT A1251WR-S-2P`, `C225111`, `1.25 mm` 2P RA SMT):** Placed on `B.Cu` at **`(89.200, 110.550) mm`, `KiCad rot = -28.00°`** (`CPL = 208.00°`), with its mating mouth `(90.421, 108.254) mm` facing **inward NNE (`+28.00°` East of North)** into a **`4.88 mm` nominal (`4.65 mm` min to `U4`, `5.85 mm` to `C22`) flat plug-insertion runway** (`cjt-a1251.pdf` pp. 1, 3 `A1251H-2P` `4.00 ± 0.25 mm` plug length / `5.80 mm` mated length; `3.20 mm` height matches `J1`'s `3.16–3.26 mm` shell for `0 mm` added stack thickness).
  - **`U13` (`Seiko Epson RX8130CE:BB`, `C1542426`, `3.2 × 2.5 × 1.0 mm` `SMD-10P` RTC):** Placed on `B.Cu` in the vacant East pocket at **`(114.750, 101.200) mm`, `KiCad rot = 0.00°`** (`CPL = 180.00°`), with `C75` (`100 nF`, `1.23 mm` from `U13.8`), `C76` (`1 µF`, `1.23 mm` from `U13.9`), `R32` (`100 kΩ` pull-up on `RTC_INT`), and locked `B.Cu` rule area **`RX8130_xtal_end`** (`[114.30..115.20, 102.30..103.05] mm`) protecting the Pin `1–10` `*1` crystal inspection short side (`ETM50E-10` Fig. 9 p. 11).
  - **`J1`, `SW1`, `SW2`, `Q2`, and all `235` front LEDs (`D1..D235`):** **100% unchanged** (`0.0000 mm / 0.00°` delta from `f-usbc`).
- [x] **4. Assembly sides:** Double-sided turnkey SMT (`0` PTH joints, `0` manual battery-wire PCB soldering; `Pass 1 = F.Cu ≤ 250 °C` for `235× XL-1010RGB-YG` + `Q2`, `Pass 2 = B.Cu ≤ 250 °C` for all `13` ICs, passives, `SW1/SW2`, `J1`, and `BT1`; [brief-f-usbc-rtc.md](../../brief-f-usbc-rtc.md) §4).
- [x] **5. Layer count & stackup:** `8` layers (`JLC08101H-1080`, [stackup.md](../../stackup.md)), `1.0 mm` finished thickness, `ENIG 1U"`, `POFV = Yes` (unchanged from `f-usbc`).
- [x] **6. Density philosophy:** Unchanged `0402` passives, `0603` bulk MLCCs, `0.50 mm` WLCSP-36 drivers, `0.09/0.09 mm` trace/space, `0.25/0.15 mm` & `0.30/0.15 mm` vias (`3×` inherited `0.20/0.10 mm` vias inside `U3` `+3V3` band).
- [x] **7. Block floorplan:** Northern, central, NW, NE, and SE USB-C blocks (`U3` + `147` locked decoupling tracks, `U4`, `Y1`, `L1`, `U9`, `U6`, `U5`, `U7`, `J1`, `U1/U2/U10/U11/U12`, `SW1/SW2`, `D1..D235`, `Q2`) are **100% unchanged** from `f-usbc`. Only `15` SW/South `B.Cu` parts shift locally around `BT1` + `4` new parts (`U13, C75, C76, R32`) populate the vacant East pocket ([brief-f-usbc-rtc.md](../../brief-f-usbc-rtc.md) §7).
- [x] **8. Thermal & sleep budget:** Unchanged `≤ 0.51 W` continuous wearable ceiling (`θ_BA ≈ 32.4 °C/W` free-air / `49.5 °C/W` worn, LED blanking on `~CHG == 0`, `ADC4` foldback); `U13` (`FOUT = OFF`, `FSEL = 11b`) adds `1.50 µA` (`4.95 µW`) on always-on `+3V3` (`~201 µA < 250 µA` total dormant + timed-wake budget).
- [x] **9. Art zone:** Unchanged `F.SilkS` Voronoi sunflower seed web clipped inside `R ≤ 18.720 mm` and outside all `6` NPTHs (`(subtractmaskfromsilk yes)`).
- [x] **10. Silkscreen policy:** Bare `F.SilkS` display face (Voronoi web + `Q2` pin-1 dot); selective `B.SilkS` strictly at **`0°` and `270°` (`90° CCW`)** (`0` `[silk-over-via]`, `0` `[under-part]`, `'rev FUR'` + `'2026-11'` identity, `14/14` `B.Cu` `OD = 0.30 mm` outside-courtyard pin-1 dots incl. `U13`, `'+'`/`'-'`/`'5V'`/`'USER'`/`'BOOT'` labels with `0%` 3D occlusion) + collision-free `346/346` `4:1` A4 assembly maps ([assembly-top.pdf](../../renders/round-pendant-f-usbc-rtc/assembly-top.pdf), [assembly-bottom.pdf](../../renders/round-pendant-f-usbc-rtc/assembly-bottom.pdf)).
- [x] **11. Keepouts & rear LiPo stackup:** Inherited `RP2350`/`L1` rule areas + new **`RX8130_xtal_end`** rule area locked; `35 mm` `403535` LiPo plugs into `BT1` (`3.20 mm` tall) and sits on `0.05 mm` Kapton tape + `3.3–3.5 mm` foam standoff flush with `J1` (`3.26 mm`).
- [x] **12. Test and debug:** All `8` `Ø1.0 mm` `B.Cu` test pads (`TP1..TP8`) preserved (`TP3 VBAT` at `(95.250, 116.750)`); full bench, `BT1` polarity, and `RX8130CE` wake procedure in [design/bringup-f-usbc-rtc.md](../../bringup-f-usbc-rtc.md).
- [ ] **User sign-off on Phase 4 mechanical, inward `BT1` & `U13` RTC brief** (see §2 below).

---

## 1. Renders Inspected
- [top.png](../../renders/round-pendant-f-usbc-rtc/top.png), [bottom.png](../../renders/round-pendant-f-usbc-rtc/bottom.png)
- [3d-top.png](../../renders/round-pendant-f-usbc-rtc/3d-top.png), [3d-bottom.png](../../renders/round-pendant-f-usbc-rtc/3d-bottom.png)
- [assembly-top.png](../../renders/round-pendant-f-usbc-rtc/assembly-top.png), [assembly-bottom.png](../../renders/round-pendant-f-usbc-rtc/assembly-bottom.png)
- [npth-gerber-zoom.png](../../renders/round-pendant-f-usbc-rtc/npth-gerber-zoom.png)

---

## 2. Decisions Requiring User Sign-Off (Gate 4)
1. **Inward-Facing `BT1` (`CJT A1251WR-S-2P`, `C225111`) at SW `(89.200, 110.550, -28.00°)`:** Confirm the NNE-facing (`+28°` E of N) inward battery socket (`4.88 mm` nominal / `4.65 mm` min flat plug-insertion runway to `U4`; plug mates before seating the rear `35 mm` LiPo on its `3.3–3.5 mm` foam standoff; verify Red `+` = `BT1.1` before first plug-in).
2. **East `U13` (`RX8130CE:BB`, `C1542426`) Always-On `+3V3` RTC (`I2C1` `0x32`, Wake on `GPIO19`):** Confirm `RX8130CE:BB` tied to always-on `+3V3` (`VIO = VDD = VBAT = +3V3`, no backup supercap; calendar retained whenever LiPo or USB-C is connected, `1.50 µA` active with `FOUT = OFF`, hardware wake on `U3` Pin `31` `GPIO19`).
3. **Inherited `f-usbc` Mechanical Items:** SSE `J1` (`TYPE-C-31-M-22`) pose (`23.95°` E of S, `4× 2.30 × 1.80 mm` SMD shell pads, two `Ø0.65 mm` front web apertures with recessed `0.70 mm` pegs).
