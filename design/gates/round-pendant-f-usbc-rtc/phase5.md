# Gate 5: stackup and design rules (`round-pendant-f-usbc-rtc`)

Status: **passed**
Parent gates cited for unchanged stackup & rules: [design/gates/round-pendant-f-usbc/phase5.md](../round-pendant-f-usbc/phase5.md), [design/gates/phase5.md](../phase5.md), and [design/stackup.md](../../stackup.md) (**`JLC08101H-1080`**).

---

## Checklist (`references/stackup-and-rules.md` §Gate checklist)

- [x] **`stackup.md` with source, date, dielectric thicknesses, `Er`, and JLCPCB 8-layer `1.0 mm` stackup code:** Documented in [design/stackup.md](../../stackup.md) (`https://jlcpcb.com/capabilities/pcb-capabilities`, `2026-11-08`, **`JLC08101H-1080`**, `Er = 4.1`, `0.9968 mm ≈ 1.00 mm` finished thickness: `2× 0.035 mm` `1 oz` outer Cu, `6× 0.0152 mm` `0.5 oz` inner Cu, `4× 0.0764 mm` `1080` prepreg, `3× 0.170 mm` core, `ENIG 1U"`, `POFV = Yes`; `In2.Cu = plane GND`, `In5.Cu = plane VSYS + plane 3V3`, `In4.Cu` signal routing with `0` zones).
- [x] **Impedance widths & USB 2.0 Full-Speed (`12 Mbit/s`) + `I2C1` (`400 kHz`) regimes documented:** USB 2.0 FS routes (`J1 -> U7 -> R14/R15 -> U3`, `30.09 / 27.44 mm` Orient. A, `32.28 / 28.54 mm` Orient. B, `< 0.33 × l_crit`) are **100% unchanged** from `f-usbc`. `I2C1` (`ACC_SCL`/`ACC_SDA`, `400 kHz` Fast-Mode max for `U9` + `U13` `RX8130CE:BB`) operates with `R19/R20 = 4.7 kΩ` (`C_bus ≈ 18 pF`, `t_r,30-70% ≈ 72 ns < 300 ns`).
- [x] **Fab minimums entered as board constraints (`round-pendant.kicad_pro`):**
  - Min track width: `0.09 mm`; min clearance: `0.09 mm`
  - Standard through-via: `0.25 mm` pad / `0.15 mm` drill (`0.30 / 0.15 mm` power vias; `3×` inherited `0.20 / 0.10 mm` vias inside `U3` `+3V3` band)
  - Hole-to-copper (`min_hole_clearance`) & hole-to-hole (`min_hole_to_hole`): **`0.200 mm`**
  - Copper-to-edge (`min_copper_edge_clearance`): **`0.200 mm`**
  - Silkscreen: `min_text_height = 0.80 mm`, **`min_text_thickness = 0.15 mm`**, `min_silk_clearance = 0.15 mm`, `(subtractmaskfromsilk yes)`
- [x] **Net classes in `design/nets-f-usbc-rtc.csv` & `round-pendant.kicad_pro` reconciled:** `187` schematic net rows in `nets-f-usbc-rtc.csv` (`+ 28` `unconnected-(...)` single-pad nets = `215` PCB nets), including `/MCU/RTC_INT` (`SIGNAL`) and `/MCU/RTC_VOUT` (`POWER`).
- [x] **Custom rules written in `round-pendant.kicad_dru` & `B.Cu` rule area `RX8130_xtal_end`:** Enforces current-carrying track widths (`VBUS ≥ 0.25 mm`, `VSYS ≥ 0.20 mm` + `In5.Cu` plane, `VBAT`/`BAT_N ≥ 0.30 mm`, `+3V3 ≥ 0.20 mm`, `SW* ≥ 0.10 mm`), USB FS length caps (`22 / 25 / 12 mm`), `QSPI_* ≤ 25 mm`, crystal `≤ 11 mm` & `0` vias, `RP2350 ring` / `L1` keepouts, plus board-enforced **`RX8130_xtal_end`** (`[114.30..115.20, 102.30..103.05] mm` on `B.Cu`, `no_tracks, no_vias, no_pour` per `ETM50E-10` Fig. 9 `*1`).
- [x] **DRC severities verified (`46` `"error"` severities in `round-pendant.kicad_pro`):** Identical strict severity table to [round-pendant-f-usbc/phase5.md](../round-pendant-f-usbc/phase5.md) §1.C (`footprint_symbol_mismatch`, `text_height`, `text_thickness` = `"error"`).
- [x] **Strict DRC produces `0` board violations and `0` unconnected items:** `Found 0 violations`, `Found 0 unconnected items`, and only the `2` inherited Variant E/F `U3` pin 42/43 `{slash}` unconnected pin-name parity strings ([decisions.md](../../decisions.md)).
