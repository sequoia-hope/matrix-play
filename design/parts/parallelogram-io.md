# Parallelogram Board-Mounted I/O: USB-C (`J1`), Micro-JST 1.25 (`BT1`), Wing Flat-Face Buttons (`SW3`, `SW4`)

Datasheet audits for the three surface-mount connectors/controls added across all five `-usb` parallelogram variants (`p1-66-usb`, `p2-132-usb`, `p3-162-usb`, `p3-198-usb`, `p4-264-usb`).

---

## 1. `J1` — Korean Hroparts `TYPE-C-31-M-22`, 16-Pin Full-SMT USB-C Receptacle

- **Datasheet:** `design/datasheets/type-c-31-m-22.pdf` (rev A, 2025-08-25, 1 page). Read: all (including 400 DPI verification of land pattern).
- **Supplier:** `C530612 TYPE-C-31-M-22 (Korean Hroparts Elec, SMD): extended, JLC stock 2565, lifecycle normal, checked 2026-11-06` ($0.36 @ qty 10).
- **Drop-in land-pattern alternate:** `C5143397 USB4110-GF-A` (`design/datasheets/usb4110-gf-a.pdf`, stock 2,783, lifecycle `normal`).

### Why `TYPE-C-31-M-22` Instead of `TYPE-C-31-M-12`
Standard horizontal 16-pin receptacles with through-hole shell stakes (`TYPE-C-31-M-12`, `C165948`) punch four plated oval slots all the way through `In1.Cu` and `F.Cu` (`±4.32 mm`), colliding with `F.Cu` LEDs along the `17.75°` slanted South bezel. `TYPE-C-31-M-22` replaces the four through-hole shell stakes with **four gull-wing SMD shell pads (`2.50 × 1.80 mm`) on `B.Cu` only** (zero copper holes through `F.Cu`), plus two short `0.70 mm` plastic locating pegs (`Ø0.50 mm` peg in `Ø0.65 mm` NPTH drill at `±2.89 mm`) that terminate inside the lower half of the `1.6 mm` FR-4 core and sit cleanly in the column gaps between `F.Cu` LED pads (`≥ 0.28 mm` hole-to-copper clearance vs `0.20 mm` DRC across all five LED densities without altering the `25.0 × 70.0 mm` outline or LED lattice).

### Electrical & Mechanical Ratings (p. 1)
- **Rating:** `20 V`, `5 A` (`VBUS` / `GND`), `100 MΩ` min insulation, `100 VAC` dielectric withstand, `40 mΩ` max initial contact resistance.
- **Durability:** `10,000` mating cycles (`5–20 N` insertion, `8–20 N` extraction), `-30 °C` to `+85 °C`.
- **Body:** `8.94 mm` shell width (`11.44 mm` across gull-wing SMD tabs) × `7.35 mm` depth × `3.26 mm` height above `B.Cu` (`4.85 mm` plug insertion depth, leaving `1.80 mm` clearance ahead of a standard `6.65 mm` USB-C plug tongue shoulder).

### Verified Single-Row 12-Pad Land Pattern (Component Top View, p. 1)
Left-to-right across the rear contact row (`y = -2.24 mm`, `Product Edge` at `y = +5.12 mm`):

| Pad # | X (mm) | Size (mm) | Contact(s) | Function | Board Net |
|---|---|---|---|---|---|
| `A1B12` | `-3.20` | `0.60 × 1.15` | `A1 / B12` | Ground | `GND` |
| `A4B9` | `-2.40` | `0.60 × 1.15` | `A4 / B9` | Power | `VBUS` |
| `B8` | `-1.75` | `0.30 × 1.15` | `B8` | `SBU2` | NC (`no_connect`) |
| `A5` | `-1.25` | `0.30 × 1.15` | `A5` | `CC1` | `/Power/CC1` (`5.1 kΩ` `R1` to `GND`) |
| `B7` | `-0.75` | `0.30 × 1.15` | `B7` | `DN2` | `/Power/USB_DM_C` |
| `A6` | `-0.25` | `0.30 × 1.15` | `A6` | `DP1` | `/Power/USB_DP_C` |
| `A7` | `+0.25` | `0.30 × 1.15` | `A7` | `DN1` | `/Power/USB_DM_C` |
| `B6` | `+0.75` | `0.30 × 1.15` | `B6` | `DP2` | `/Power/USB_DP_C` |
| `A8` | `+1.25` | `0.30 × 1.15` | `A8` | `SBU1` | NC (`no_connect`) |
| `B5` | `+1.75` | `0.30 × 1.15` | `B5` | `CC2` | `/Power/CC2` (`5.1 kΩ` `R2` to `GND`) |
| `B4A9` | `+2.40` | `0.60 × 1.15` | `B4 / A9` | Power | `VBUS` |
| `B1A12` | `+3.20` | `0.60 × 1.15` | `B1 / A12` | Ground | `GND` |
| `S1` (×4) | `±5.07` | `2.50 × 1.80` | Shell | Shield (`y = -1.66, +2.24`) | `GND` |
| NPTH (×2) | `±2.89` | `Ø0.65` drill | Locating pegs | `y = -1.17`, `0.70 mm` peg | — |

> **Critical pin-order note:** At `x = +1.25 mm` and `+1.75 mm`, **`A8` (`SBU1`) is inner (`+1.25`) and `B5` (`CC2`) is outer (`+1.75`)** — verified at 400 DPI on `type-c-31-m-22.pdf` p. 1. Both `A6/B6` (`DP1/DP2`) and `A7/B7` (`DN1/DN2`) are joined right at `U7` (`USBLC6-2P6`) for reversible USB 2.0 FS operation, and `A5`/`B5` each have dedicated `5.1 kΩ` Rd pull-downs (`R1`, `R2`) for USB-C 5 V sink negotiation in both cable orientations.

---

## 2. `BT1` — CJT `A1251WR-S-2P` / Molex `53261-0271`, Micro-JST 1.25 / MX1.25 Right-Angle SMT Battery Header

- **Datasheets:**
  - `design/datasheets/cjt-a1251.pdf` (pp. 1–5, `A1251WR-S-2P` 90° SMT wafer on p. 5). Read: all.
  - `design/datasheets/molex-53261-0271.pdf` (pp. 1–5, `53261-0271` PicoBlade 1.25 mm 90° SMT on pp. 1–2). Read: all.
- **Primary supplier:** `C225111 A1251WR-S-2P (CJT, SMD,P=1.25mm,Surface Mount,Right Angle): extended, JLC stock 75387, lifecycle normal, checked 2026-11-06` ($0.087 @ qty 10).
- **Exact drop-in second source:** `C177225 532610271 (MOLEX, SMD,P=1.25mm,Surface Mount,Right Angle): extended, JLC stock 27222, lifecycle normal, checked 2026-11-06` ($0.14 @ qty 10).

### Electrical & Mechanical Ratings (`cjt-a1251.pdf` pp. 1, 5; `molex-53261-0271.pdf` pp. 1–2)
- **Rating:** `1.0 A` AC/DC continuous (`> 3×` our `340 mA` avg discharge / `297 mA` charge), `125 V` (`CJT`) / `125 V` (`Molex`), `20 mΩ` max contact resistance, `-40 °C` to `+105 °C`.
- **Profile:** `7.75 mm` wide across solder tabs (`4.30 mm` housing width) × `4.70 mm` depth × **`3.20 mm` height above `B.Cu`** — ultra-low profile (shorter than `USB-C` at `3.26 mm` and less than half the thickness of an `802035` / `102035` prismatic LiPo cell), **100% SMD (0 through-holes)**.
- **Mating housing:** Friction-fit 2-pin `1.25 mm` Micro-JST / MX1.25 / Molex `51021-0200` / CJT `A1251H-2P` LiPo plug.
- **Land pattern:** KiCad standard `Connector_Molex:Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal`:
  - Signal pads `1` (`x = -0.625`, `y = -2.40`) and `2` (`x = +0.625`, `y = -2.40`): `0.80 × 1.60 mm` (`1.25 mm` pitch).
  - Mechanical solder nails `MP` (`x = ±3.175`, `y = +0.50`): `2.10 × 3.00 mm` tied to `GND` for mechanical peel strength (isolated from `/Power/BAT_N`).
- **Polarity & Protection:**
  - Pin `1` = **`VBAT` (`+`)**, Pin `2` = **`/Power/BAT_N` (`-`, cell minus to `U8` `XB9901A` pins 4/5/EP)**.
  - Because aftermarket `1.25 mm` LiPo packs exist in both Red/Black orientations, `B.SilkS` prints explicit **`+`** and **`-`** markers right next to the corresponding sides of `BT1` (and crimp pins in `1.25 mm` housings swap in seconds by lifting the plastic latch tab if a pack arrives reversed; `U8` `XB9901A` also includes reverse-charger/cell protection).

---

## 3. `SW3`, `SW4` — XKB `TS-1187A-B-A-B`, Ultra-Low-Profile Flat-Face Wing Tactile Switches

- **Datasheet:** `design/datasheets/ts-1187a-b-a-b.pdf` (rev A0, 1 page). Read: all.
- **Supplier:** `C318884 TS-1187A-B-A-B (XKB Connection, SMD): basic, JLC stock 968777, lifecycle normal, checked 2026-11-06` (**JLCPCB Basic Part**, $0.02 @ qty 20).

### Electrical & Mechanical Ratings (p. 1)
- **Dimensions:** `5.1 × 5.1 mm` body (`6.4 mm` across gull-wing leads) × **`1.5 mm` total height** (`Code A = 1.5 mm` flat circular brass actuator face), **zero plastic boss pegs (100% SMD)**.
- **Force & Travel:** `Code B = 260 gf` operating force (crisp tactile click that resists accidental pocket/chest presses while worn), `0.25 mm` travel, `100,000` cycles durability, `12 VDC 50 mA` rating.
- **Internal contact bridging (p. 1 Circuit Diagram):**
  - Pads `(1, 2)` at `y = -1.875 mm` (`x = ±3.00 mm`, `1.00 × 0.75 mm`) are internally shorted (`Pin 1` in KiCad `Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A`).
  - Pads `(3, 4)` at `y = +1.875 mm` (`x = ±3.00 mm`, `1.00 × 0.75 mm`) are internally shorted (`Pin 2` in KiCad).
- **Placement & Circuit:**
  - Placed symmetrically on `B.Cu` in the **North-West (`SW3`)** and **South-East (`SW4`)** acute wings, completely outside the `20 × 35 mm` LiPo cell envelope (`y ∈ [-21.5, +13.5]`), giving natural two-thumb / index-finger tactile interaction on the back of both wings alongside the existing side tactile buttons (`SW1` USER/WAKE, `SW2` BOOTSEL).
  - Wired active-low to `GND` through `1 kΩ` `0402` series ESD/pin-conflict resistors (`R44`, `R45`, Basic Part `C11702`) into free `RP2350A` GPIOs (`GPIO7` for `BTN_NW` / `SW3`, `GPIO19` for `BTN_SE` / `SW4`; firmware enables RP2350 internal pull-ups).
