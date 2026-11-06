# Parallelogram 4-Layer Low-Cost Variant Study (`25.0 × 70.0 mm`)

Visual 5-tier floorplan comparison: [`floorplan.svg`](floorplan.svg) · Routed vector previews: [`p1-66-front.svg`](p1-66-front.svg) / [`p1-66-back.svg`](p1-66-back.svg) · [`p2-132-front.svg`](p2-132-front.svg) / [`p2-132-back.svg`](p2-132-back.svg) · Audits: [`leds-xl1615.md`](../../parts/leds-xl1615.md) · [`drivers-aw20198.md`](../../parts/drivers-aw20198.md) · [`ultraroute-requests.md`](../../ultraroute-requests.md)

## 1. Design Goal & Mechanical Envelope

This study explores how far a **standard 4-layer JLCPCB PCB (`JLC04161H-7628`, `1.6 mm`, zero BGA / zero blind-buried vias)** with **solid exposed ground pads** and **100% locally in-stock JLCPCB PCBA components** can push multiplexed RGB LED matrix density before 4-layer routing saturates — while replacing the expensive custom round smartwatch cell (`~$7/ea`) and 8-layer WLCSP stackup of `round-pendant` Variant D/E with an artistic skewed-parallelogram form factor built around a commodity **`20 × 35 mm` prismatic LiPo pouch cell** (`802035` / `102035`, `~$1.50–$2.20/ea`, thickness unconstrained).

### Skewed Parallelogram Geometry
- **Envelope:** **`25.00 mm` wide × `70.00 mm` tip-to-tip** (`x ∈ [-12.50, +12.50] mm`, `y ∈ [-31.00 + 0.32x, +31.00 + 0.32x] mm`, `62.00 mm` vertical East/West edges, `1.00 mm` corner fillets, `1,549 mm²` board area vs `1,134 mm²` on the `Ø 38 mm` round pendant).
- **Shear / Skew Angle:** $\alpha = \arctan(0.32) = 17.745^\circ$ (`±4.00 mm` vertical shear across the `25.00 mm` width).
- **Skewed LED Lattice (`F.Cu`):** Every RGB LED (`D1..DN`) sits on the sheared lattice $(x_c,\; v_r + 0.32\,x_c)$ so rows run parallel to the `17.75°` slanted North/South bezels while columns run parallel to the vertical East/West edges (allowing straight vertical `F.Cu` `CS` cathode chains within each column).
  - **Lower-density 6-column tiers (`p1-66` & `p2-132`, `px = 3.70 mm`):** Use **`XL-1615RGBC-RF`** (`C965840`, `1.6 × 1.5 × 0.6 mm`, `Pin 2 = Anode`, `718k+` in JLCPCB stock, `$0.0148–$0.0159/ea`; audit in [`leds-xl1615.md`](../../parts/leds-xl1615.md)). Its `0.80 mm` horizontal intra-pad copper-to-copper gap (`2.3×` wider than `XL-1010RGB`'s `0.35 mm` gap) unlocks intra-LED track/via escape channels, cutting vias by `22–27%` and bringing **both `p1-66` AND `p2-132` to `100.0%` (`0` open, `0` DRC)** on 4 layers!
  - **Higher-density 9–12-column tiers (`p3-162`, `p3-198`, `p4-264`, `px = 2.55 / 2.02 mm`):** Keep **`XL-1010RGB-YG`** (`C965834`, `1.0 × 1.0 × 0.4 mm`, `Pin 3 = Anode`) where `1.6 mm`-wide `1615` bodies would crowd inter-column routing alleys.
- **Front Silkscreen Lattice Web & Top-Bezel Light Sensor (`F.Cu` / `F.SilkS`):**
  - `Q2` (`XYC-PT19C-L1`, `C2693594`, `0603` top-view phototransistor, `100%` land-pattern compatible with `ALS-PT19` `C146233`) sits centered on the slanted North bezel at `(0.00, -29.90 mm, -17.75°)`, powered by `GPIO1` (`0 µA` sleep current) with `R43 = 22 kΩ` and `C70 = 100 nF` directly behind it on `B.Cu`.
  - `F.SilkS` carries a continuous skewed diamond/parallelogram lattice web along cell midpoints, clipped `0.25 mm` clear of `F.Cu` pads and `0.35 mm` clear of `Q2`'s optical window.
- **Centered Prismatic Cell Pocket & Uncovered South Solder End-Zone (`B.Cu`):**
  - Standard **`20.0 × 35.0 mm` prismatic LiPo pouch cell** (`802035` = `8.0 × 20 × 35 mm`, `~550–600 mAh`; `102035` = `10.0 × 20 × 35 mm`, `~700–750 mAh`) centered at `(0.00, -4.00 mm)` (`x ∈ [-10.0, +10.0] mm`, `y ∈ [-21.5, +13.5] mm`, `2.50 mm` inset from both East/West edges so side buttons stay clear of the pouch).
  - Because `B.Cu` SMT components under the pouch (`RP2350A`, `AW20198QNR`, `L1` at `1.0 mm` max height) have smooth reflowed profiles, a `1.0 mm` foam double-sided tape strip mounts the flat prismatic pouch cleanly above `B.Cu` components while leaving the entire **South end-zone (`y = +14..+33 mm`) completely uncovered** for hand-soldering the 6 slanted `J1` USB pads `(0.00, +29.10 mm)` and `BT1` battery pads `(+8.60, +29.85 mm)` with zero risk of iron contact against the LiPo pouch.
- **Peg-less Side Tactile Switches (`B.Cu`):**
  - `SW1` `(+10.85, +1.50 mm)` and `SW2` `(-10.85, -3.50 mm)` use Panasonic **`EVQP7J01P`** (`C2828254`, `6,971` in stock at JLCPCB), eliminating NPTH boss holes that would otherwise punch through the `F.Cu` LED matrix.

---

## 2. 4-Layer Stackup, Solid Exposed Pads & Sourcing

| Layer | Function | Rules & Geometry |
|---|---|---|
| `L1` (`F.Cu`) | Skewed RGB LED matrix + `Q2` sensor | Vertical `CS` cathode chains within columns + short horizontal anode stubs |
| `L2` (`In1.Cu`) | **Unbroken solid `GND` reference plane** | `1` unbroken piece (`1,226–1,377 mm²`), `0.15 mm` clearance, `0.12 mm` min width, `L1` `VREG_LX` switch-node cutout |
| `L3` (`In2.Cu`) | **Single inner signal / `SW` scan highway** | Carries horizontal/diagonal `SW` anode buses, `CS` trunks from `B.Cu` QFNs, `I2C`, `QSPI`, and `VSYS`/`+3V3` links |
| `L4` (`B.Cu`) | All ICs, passives, `J1`/`BT1` pads, RP2350 zones | Solid exposed `GND` pads (`U3.61`, `U5.17`, `U1/U2/U10/U11.41`) + unbroken `RP2350` `+1V1` ring & `+3V3` band |

- **Zero BGA, Zero Blind/Buried Vias, 100% Solid Exposed Ground Pads:**
  - Every `AW20198QNR` (`3.40 × 3.40 mm` solid `GND` EP), `RP2350A` (`4.10 × 4.10 mm` solid `GND` EP), and `BQ24073` (`2.40 × 2.40 mm` solid `GND` EP) is one unbroken solid copper pad on `B.Cu` with `2 × 2` solder-paste stencil windows, collision-checked `0.30/0.15 mm` `GND` thermal vias directly into `In1.Cu`, and `.kicad_dru` keepouts enforcing **`0` foreign vias and `0` foreign `B.Cu` tracks** inside every solid EP.
  - **Same-net via-in-pad note (`ultraroute` behavior):** Because `ultraroute a3ba419` (`board/src/custom.rs`) evaluates `.kicad_dru` hole clearances only between *distinct* nets (`o.net != net`), it places `102` (`p1-66`) to `250` (`p4-264`) `0.30/0.15 mm` same-net vias inside non-EP SMD pads (`0402` passives and `XL-1010RGB` pads). For assembly, either select JLCPCB's 4-layer **`POFV = Yes` (epoxy-filled & capped vias)** or add per-SMD-pad `disallow via` rule areas before production sign-off (easy to fit at `p1-66`'s generous `3.70 × 5.20 mm` pitch).
- **100% Locally In-Stock JLCPCB PCBA BOM (`32` unique BOM lines, `0` Global Sourcing lines):**
  - LED Driver: Shanghai Awinic **`AW20198QNR`** (`C5137654`, `QFN-40 5×5 mm`, `0.40 mm` pin pitch, `3.40 × 3.40 mm` solid EP, `18 CS × 11 SW = 66` RGB LEDs/chip, JLCPCB stock `6,055`, `$0.78–$0.89` @ qty 10+; datasheet audit in [`drivers-aw20198.md`](../../parts/drivers-aw20198.md)).
  - Side Switches: Panasonic **`EVQP7J01P`** (`C2828254`, JLCPCB stock `6,971`).
  - Light Sensor: Newopto **`XYC-PT19C-L1`** (`C2693594`, JLCPCB stock `25,206`, `$0.015`).
  - MCU + Core Inductor: **`RP2350A`** (`C42411118`, JLCPCB stock `3,462`) + **`AOTA-B201610S3R3-101-T`** (`C42411119`, JLCPCB PCBA stock `55` — locally stocked for qty 10–50 without Global Sourcing) + `10 kΩ 0402` Basic (`C25744`, JLCPCB PCBA stock `16,999,300`). *(Note: LCSC retail `wmsc.lcsc.com` shows `0` for `C25744` and `C42411119`, whereas `jlc_parts.py show` confirms JLCPCB's PCBA warehouse holds `16,999,300` and `55` respectively.)*

---

## 3. Live Qty-10 Hardware Cost Comparison

Component prices queried live from LCSC/JLCPCB ladders (`scripts/parallelogram/export_and_cost.py --cost --qty 10`, `2026-11-05`):

| Variant | Layers | Grid (`px × py`) | Active RGB LED | Drivers | Active BOM / bd (qty 10) | `XL-1010` / `XL-1615` Alt BOM | Est. PCB + Battery + Global Sourcing Delta (qty 10) |
|---|---|---|---:|---|---:|---:|---|
| **`p1-66`** | **4L** | `6 × 11` (`3.70 × 5.20 mm`, `4.3/cm²`) | **`66× XL-1615RGBC`** (`C965840`) | `1× AW20198QNR` (`$0.89`) | **`$10.61`** (**`$10.05`** w/ `RP2040`) | `$11.45` (`XL-1010`) | `~$0.70–$2.50/bd` 4L PCB + `~$1.80` `802035` LiPo, **`$0` Global Sourcing** |
| **`p2-132`** | **4L** | `6 × 22` (`3.70 × 2.60 mm`, `8.5/cm²`) | **`132× XL-1615RGBC`** (`C965840`) | `2× AW20198QNR` (`$1.77`) | **`$12.60`** (**`$12.04`** w/ `RP2040`) | `$14.06` (`XL-1010`) | Same 4L stackup + `$1.80` `802035` LiPo, **`$0` Global Sourcing** |
| **`p3-162`** | **4L** | `9 × 18` (`2.55 × 3.15 mm`, `10.5/cm²`) | `162× XL-1010RGB` (`C965834`) | `3× AW20198QNR` (`$2.35`) | **`$15.47`** | `$13.33` (`XL-1615`) | Same 4L stackup + `$1.80` `802035` LiPo, **`$0` Global Sourcing** |
| **`p3-198`** | **4L** | `9 × 22` (`2.55 × 2.60 mm`, `12.8/cm²`) | `198× XL-1010RGB` (`C965834`) | `3× AW20198QNR` (`$2.35`) | **`$16.44`** | `$13.83` (`XL-1615`) | Same 4L stackup + `$1.80` `802035` LiPo, **`$0` Global Sourcing** |
| **`p4-264`** | **4L** | `12 × 22` (`2.02 × 2.60 mm`, `17.0/cm²`) | `264× XL-1010RGB` (`C965834`) | `4× AW20198QNR` (`$3.13`) | **`$19.03`** | `$15.55` (`XL-1615`) | Same 4L stackup + `$1.80` `802035` LiPo, **`$0` Global Sourcing** |
| `round-pendant-e` | 8L ENIG VIP | Sunflower (`~2.0 mm`, `20.7/cm²`) | `235× XL-1010RGB` | `5× IS31FL3745` WLCSP (`$11.31`) | `$26.47` | N/A (`1615` doesn't fit) | `~$12–$18/bd` 8L ENIG VIP PCB + `~$7.00` round LiPo + Global Sourcing fees/lead time |

### Extra Cost Levers Identified
1. **`XL-1615RGBC-RF` (`1.6 × 1.5 mm`, `C965840`, JLCPCB stock `720,005`) vs `XL-1010RGB-YG` (`1.0 × 1.0 mm`, `C965834`, stock `12,408`):**
   - At `3.70 × 5.20 mm` (`p1-66`) or `3.70 × 2.60 mm` (`p2-132`), `1.6 × 1.5 mm` LEDs fit with `1.10–3.70 mm` clear body-to-body spacing, cutting LED cost nearly in half (`$0.0138–$0.0159/ea` vs `$0.0270/ea`) — saving **`$0.84/bd` (`p1-66`) to `$3.48/bd` (`p4-264`)** and eliminating any `1.0 × 1.0 mm` fine-pitch assembly surcharge.
2. **`0.30/0.15 mm` vs `0.45/0.20 mm` Through-Via Trade-Off on `0.40 mm`-Pitch QFNs:**
   - JLCPCB's 4-layer `0.20 mm` drill promo (`0.45 mm` pad + `0.10 mm` space = `0.55 mm` via pitch) cannot place adjacent escape vias at `0.40 mm` QFN pin pitch without staggering into two concentric rings, leaving `74` open connections on `p2-132` (`360 s` trial).
   - Stepping down to JLCPCB's standard 4-layer **`0.15 mm` drill / `0.30 mm` pad** (`0.40 mm` center-to-center via pitch) unlocks clean `0.40 mm`-pitch QFN escape on 4 layers.
3. **`RP2040` (`C2040`, `$1.01`, stock `57,974`) vs `RP2350A + L1` (`$1.57`, `L1` stock `55`):**
   - Saves **`$0.56/bd`** and drops `L1` (`AOTA-B201610S3R3-101-T`), bringing **`p1-66` down to `$10.05/bd` BOM** (`~$13.50` all-in including 4L PCB and `802035` LiPo vs `~$45–$50` all-in for the 8L WLCSP round pendant!).

---

## 4. Empirical 4-Layer Routing Density Progression (`ultraroute a3ba419`)

All five variants use the identical 3-stage deterministic `ultraroute a3ba419` pipeline (`scripts/parallelogram/route_variant.py`: Stage 1 unobstructed critical MCU pass -> Stage 2 full matrix `autoroute.py` -> Stage 3 governed `--adopt --shove-plough region` finisher), followed by `verify_variant.py`:

| Tier | Grid & Pitch (`px × py`) | LED Package | Drivers | Total Conns (`Sig + GND`) | Open (`Sig / Plane`) | **% Routed** | Tracks / Vias | Foreign EP Vias | `In1.Cu` `GND` / `+1V1` Ring | Strict DRC (`--severity-all`) |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| **`p1-66`** | `6 × 11` (`3.70 × 5.20 mm`) | **`XL-1615RGBC`** | `1× AW20198` | `475` (`402 + 73`) | **`0` (`0 / 0`)** | **`100.00%`** | `2,604 / 343` (`-27%` vias) | **`0`** | `1 pc (1411 mm²)` / `1 pc (6.36 mm²)` | **`0` err, `0` warn, `0` `copper_audit`, `0` `pad_joints`** |
| **`p2-132`** | `6 × 22` (`3.70 × 2.60 mm`) | **`XL-1615RGBC`** | `2× AW20198` | `761` (`679 + 82`) | **`0` (`0 / 0`)** | **`100.00%`** | `5,782 / 670` (`-22%` vias) | **`0`** | `1 pc (1323 mm²)` / `1 pc (7.18 mm²)` | **`0` err, `0` warn, `0` `copper_audit`, `0` `pad_joints`** |
| **`p3-162`** | `9 × 18` (`2.55 × 3.15 mm`) | `XL-1010RGB` | `3× AW20198` | `901` (`810 + 91`) | **`31` (`28 / 3`)** | **`96.56%`** | `6,289 / 793` | **`0`** | `1 pc (1294 mm²)` / `1 pc (8.24 mm²)` | `31` unconn, `2` err, `0` warn, `0` `pad_joints` |
| **`p3-198`** | `9 × 22` (`2.55 × 2.60 mm`) | `XL-1010RGB` | `3× AW20198` | `1,045` (`954 + 91`) | **`56` (`56 / 0`)** | **`94.64%`** | `7,117 / 955` | **`0`** | `1 pc (1247 mm²)` / `1 pc (7.59 mm²)` | `56` unconn, `8` err, `0` warn, `0` `pad_joints` |
| **`p4-264`** | `12 × 22` (`2.02 × 2.60 mm`) | `XL-1010RGB` | `4× AW20198` | `1,329` (`1,229 + 100`) | **`139` (`139 / 0`)** | **`89.54%`** | `7,945 / 1,041` | **`0`** | `1 pc (1226 mm²)` / `1 pc (8.29 mm²)` | `139` unconn, `8` err, `0` warn, `0` `pad_joints` |

*(Prior `XL-1010RGB` baseline on `p1-66` & `p2-132`: `p1-66` routed `100.0%` with `467` vias; `p2-132` stalled at `99.74%` (`2` open on `U2.10`/`U2.12`) with `859` vias. Swapping both 6-column boards to `XL-1615RGBC-RF` opened a `0.80 mm` horizontal channel inside every LED footprint, dropping vias by `22–27%` and closing `p2-132` to `100.00%` (`0` open, `0` DRC)!)*

### Why the 4-Layer Density Knee Falls Precisely Between `6` Columns (`p1-66` / `p2-132`) and `9` Columns (`p3-162`+)

1. **Solid Exposed-Pad Shadowing (`px = 3.70 mm > 3.40 mm` vs `px = 2.55 / 2.02 mm < 3.40 mm`):**
   - Every `AW20198QNR` (`5 × 5 mm`) has a **`3.40 × 3.40 mm` solid `GND` exposed pad** (and `RP2350A` has a `4.10 × 4.10 mm` solid EP surrounded by unbroken `+1V1`/`+3V3` rings) through which zero signal through-vias may pass.
   - At **`6` columns (`px = 3.70 mm > 3.40 mm`, `p1-66` & `p2-132`)**, column spacing exceeds the QFN exposed-pad width (`2.00 mm` clear alley between `XL-1615` columns + `0.80 mm` horizontal gap inside each `XL-1615` footprint), so `CS` trunks and `SW` vias step cleanly around every solid EP.
   - At **`9` columns (`px = 2.55 mm < 3.40 mm`, `p3-162` & `p3-198`)** and **`12` columns (`px = 2.02 mm < 3.40 mm`, `p4-264`)**, `1–2` LED columns pass directly over each solid QFN/MCU exposed pad on the opposite face, trapping `F.Cu` pads above solid `B.Cu` copper.
2. **Single Inner Signal Highway (`In2.Cu` Alone vs Orthogonal Pair):**
   - Because `In1.Cu` is reserved as an unbroken solid `GND` reference plane (`1` piece across all 5 tiers), **`In2.Cu` is the sole inner routing layer** carrying both horizontal `SW` anode buses (`11` to `44` scan lines) and radial `CS` escapes out of `40`-pin `0.40 mm`-pitch QFNs.
   - **`p1-66` (`1` driver, `66× XL-1615RGBC`, `$10.61` BOM)** and **`p2-132` (`2` drivers, `132× XL-1615RGBC`, `$12.60` BOM)** BOTH route to **`100.00%` (`0` open)** and clean to **`0` DRC / `0` `copper_audit` / `0` `pad_joints`** defects (Gerbers/BOM/CPL/schematic PDF exported in `hw/parallelogram/{p1-66,p2-132}/fab/`).
   - **`p3-198` (`198` LEDs) and `p4-264` (`264` LEDs) on 6 Layers (Zero BGA):** Stepping from 4 layers to JLCPCB's **6-layer stackup** (which includes **free ENIG + free `POFV` epoxy-filled vias** on JLCPCB's `0.15 mm` 6L promo while keeping the cheap `$0.78` `AW20198QNR` QFN drivers and `$1.80` prismatic LiPo!) adds a second orthogonal inner signal layer (`In2.Cu` horizontal + `In3.Cu` vertical) to break through the `9–12` column bottleneck without needing WLCSP BGAs.
