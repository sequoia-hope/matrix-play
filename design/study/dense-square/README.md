# Ultra-Dense `20 × 20 mm` Square Matrix Study (`25.0 × 50.0 mm`, 8-Layer)

Datasheet audits: [`leds-mhpa0808.md`](../../parts/leds-mhpa0808.md) (`MEIHUA MHPA0808RGBDT`, `LCSC C404279`) · [`drivers-aw20198.md`](../../parts/drivers-aw20198.md) (`AW20198QNR`) · Schematics: [`dense-square-s15-225.pdf`](../../renders/schematic/dense-square-s15-225.pdf) · [`dense-square-s16-256.pdf`](../../renders/schematic/dense-square-s16-256.pdf)

## 1. Design Brief & Mechanical Partitioning

- **Board Envelope:** **`25.0 × 50.0 mm`** rectangular 8-layer `1.0 mm` ENIG PCB (`R = 1.50 mm` rounded corners, `1,248 mm²` total area).
- **North `20.0 × 20.0 mm` Ultra-Dense LED Window (`x ∈ [-10.00, +10.00] mm`, `y ∈ [-22.50, -2.50] mm`):**
  - Populated **exclusively** with **`MEIHUA MHPA0808RGBDT`** (`LCSC C404279`, `0.80 × 0.80 × 0.60 mm` 0808 black-diffused silicone PLCC common-anode RGB LED, `9,370+` in stock at JLCPCB, `$0.0373/ea` at qty 10 boards).
  - **Zero components under the LED array (`B.Cu` 100% clear across `y < -2.00 mm`):** Every IC, driver, passive, crystal, inductor, switch, test point, and connector sits strictly in the **South electronics bay (`y ∈ [-2.00, +25.00] mm`)**, freeing all 8 copper layers directly beneath the `20 × 20 mm` optical window for uninterrupted vertical/horizontal matrix routing and thermal ground stitching.
- **South Electronics Bay (`y ∈ [-2.00, +25.00] mm`, Zero Opposite-Face Pin Shadowing):**
  - **`F.Cu` Outer Rails (`|x| ≥ 6.50 mm`):** `4× AW20198QNR` QFN-40 constant-current matrix drivers (`U1, U2` at `x = -8.90 mm`; `U10, U11` at `x = +8.90 mm`, solid `3.40 × 3.40 mm` `GND` exposed pads) with decoupling and `R_EXT = 30 kΩ` (`13.3 mA` hardware ceiling) in dedicated horizontal bands (`y = 5.85..7.25 mm` and `y = 15.05..16.40 mm`), plus `Q2` (`XYC-PT19C-L1` ambient light sensor at `(0.00, -0.95 mm)`), `SW1`/`SW2` (`EVQP7J01P` peg-less side tactile switches), `U7` (`USBLC6-2SC6`), `U8` (`XB3306D`), `J1` (`USB 5V` pads), and `BT1` (`3.7 V LiPo` pads with `+ / -` silkscreen polarity).
  - **`B.Cu` Central Spine (`|x| ≤ 6.45 mm`):** `RP2350A` QFN-60 (`U3` at `(0.00, +7.60 mm)`, solid `GND` EP + unbroken `+1V1` ring & `+3V3` band), `12 MHz` crystal (`Y1`, `0` vias, `< 5 mm` loop), `AOTA-B201610S3R3-101-T` (`L1`), `BQ24073` LiPo charger (`U5`), `W25Q128JVS` `16 MB` QSPI flash (`U4`), `LIS3DHTR` accelerometer (`U9`), `TLV75533` LDO (`U6`), and `TP1..TP8` debug/SWD test points.
  - Because `F.Cu` QFNs/passives stay at `|x| ≥ 6.50 mm` while `B.Cu` `U3` + decouplers stay inside `[-6.45, +6.45] mm`, **opposite-face IC-pin collisions (`< 0.50 mm`) are identically `0`** across all 9 multi-pin ICs (`198 / 199` inward QFN pins escape in `prefanout`).

---

## 2. Square-Array Density Proof & Routing Knee (`20.0 × 20.0 mm` Window)

Each `MHPA0808RGBDT` (`round_pendant:LED_MHPA0808RGBDT`) spans `0.90 × 0.90 mm` copper (`4× 0.35 × 0.35 mm` pads on `0.55 mm` centers, `0.20 mm` internal cross gap) and `0.80 × 0.80 mm` package body:

| Tier | Grid inside `20 × 20 mm` | Center Pitch `p` | Copper Span | Inter-LED Copper Gap | Density (`LEDs/cm²`) | Total Conns | Routed (`ultraroute 3de3d83`) | Strict DRC & `copper_audit` | Qty-10 BOM |
|---|---|---:|---|---:|---:|---:|---|---|---:|
| **`s16-256`** | **`16 × 16 = 256` LEDs** | **`1.27 mm`** (`50 mil`) | `19.95 × 19.95 mm` | `0.37 mm` (`1` `F.Cu` track) | **`64.00 / cm²`** (`192.0` RGB dies/cm²) | `1,156` | **`1,156 / 1,156` (`100.00%`, `0` open)**, `8,415` trk, `1,087` vias | **`0` err, `0` warn, `0` `copper_audit`, `0` `pad_joints`** | **`$21.42`** |
| **`s15-225`** | **`15 × 15 = 225` LEDs** | **`1.36 mm`** | `19.94 × 19.94 mm` | `0.46 mm` (`2` `F.Cu` tracks) | **`56.25 / cm²`** (`168.8` RGB dies/cm²) | `1,100` | **`1,100 / 1,100` (`100.00%`, `0` open)**, `5,377` trk, `998` vias | **`0` err, `0` warn, `0` `copper_audit`, `0` `pad_joints`** | **`$20.27`** |
| `17 × 17` *(infeasible)* | `17 × 17 = 289` LEDs | `1.19 mm` | `20.02 mm` (`> 20 mm`) | `0.29 mm` | `72.25 / cm²` | — | `0` legal off-pad `0.25/0.15 mm` via sites in unit cell | Exceeds `20 mm` copper window | — |

### Key Architectural Lessons
1. **Contiguous Fold-Back Column Partitioning (`4× AW20198QNR`):**
   - Each `AW20198QNR` drives a quadrant (`7–8` columns × `15–16` rows = `56–64` RGB LEDs ≤ `66` capacity): rows `0..9` (`10` scan lines `SW_1..10`) map `CS_1..12` across `4` columns (`12` cathode lines), while the remaining `5–6` rows fold onto `SW_7..11` using `CS_13..18` (`triplet 5` in adjacent columns `0..1`, `triplet 6` in adjacent columns `2..3`), eliminating horizontal fold-back leapfrogging across the matrix boundary.
2. **Router Grid Commensurability (`0.05 mm` vs `0.025 mm`):**
   - `s15-225` (`1.36 mm` pitch, `0.46 mm` street) aligns cleanly on `ultraroute`'s `0.05 mm` grid (`889 MB` peak RAM), closing to **`100.00%` (`0` open, `0` DRC)** with `0.09 mm` `In2.Cu` `plane GND` clearance (`1` unbroken `994.5 mm²` reference plane).
   - `s16-256` (`1.27 mm = 50 mil` pitch, `0.37 mm` street — the mathematical maximum square lattice that fits inside `20.0 × 20.0 mm`) requires `--cell 0.025` (`2.64 GB` peak RAM) plus a dedicated `--adopt --shove-plough region` pass (`6` shove passes), closing all `1,156 / 1,156` connections to **`100.00%` (`0` open, `0` DRC, `0` `copper_audit`, `0` thin pad joints)** with `1` unbroken `973.8 mm²` `In2.Cu` `GND` plane!
