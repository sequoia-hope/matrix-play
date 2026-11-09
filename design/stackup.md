# Stackup and rules

Sources: JLC capabilities page https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-02. 3313 prepreg Er 4.1, 6-layer via-in-pad filled and capped.

**Thickness estimate.** Layer thicknesses below are worked out to total 1.0 mm from a JLC-style 3313 stack on the user's 6-layer `pendant-nrf52820` (which is 1.6 mm). JLC's exact table for 1.0 mm wasn't reachable by script. Read it from the quote tool before fab. Nothing here depends on impedance control: USB is full speed over a very short run, QSPI is under 25 mm.

| Layer | Copper | Dielectric below | Role |
|---|---|---|---|
| F.Cu | 1 oz finished, 0.035 | 0.0994 prepreg | LED pads, R, G, B columns |
| In1 | 0.5 oz, 0.0152 | 0.2708 core | SW scan trees |
| In2 | 0.5 oz | 0.1088 prepreg | GND plane |
| In3 | 0.5 oz | 0.2708 core | CS jumps, bottom-side signal escape |
| In4 | 0.5 oz | 0.0994 prepreg | VSYS, +3V3 pours, GND |
| B.Cu | 1 oz | — | Parts, short signals, pours |

## Fab limits used (JLC, 6-layer)

| Rule | Value | Source |
|---|---|---|
| Track / clearance | 0.09 / 0.09 mm | Capability page; floor on the user's earlier board |
| Via | 0.25 / 0.15 mm standard; 0.20 / 0.10 mm in U3's 3V3 band only; annular 0.05 mm | Capability page; the smaller one needs board ≤ 1 mm and ENIG, both set |
| Via-in-pad | Filled and capped | Capability page, standard on 6 layers |
| Hole clearance, hole to hole | 0.2 mm | Capability page |
| Copper to edge | 0.2 mm | Capability page; check J1's west front leg, 0.32 mm from the edge: passes |
| Silk | 0.8 mm height, 0.15 width | Skill defaults |

## Net classes

| Class | Track | Clearance | Via | Why |
|---|---|---|---|---|
| SIGNAL, ANALOG | 0.1 | 0.09 | 0.25/0.15 | nets.csv; R21 needs 0.1/0.09 in the LED channels |
| POWER | 0.2 | 0.09 | 0.3/0.15 | Rails, with DRU minimums below, SW lines |
| CLOCK | 0.15 | 0.15 | 0.25/0.15 | Crystal: guard by spacing |
| SE_HS | 0.1 | 0.1 | 0.25/0.15 | QSPI |
| DIFF_HS | 0.15 | 0.15 | 0.25/0.15 | USB FS; pair 0.15/0.15, not impedance controlled |
| SWITCH | 0.4 | 0.12 | 0.3/0.15 | VREG_LX in its zone |

DRU minimums: VBUS 0.25; VSYS, VBAT, BAT_N 0.3; +3V3 0.2; SW lines 0.1. Length limits and "no vias" rows from nets.csv. Rule areas for L1 and U3's ring are drawn with the parts at phase 6.

Severities: silk overlap, silk over copper, track dangling, net conflict, duplicate, extra and missing footprint set to error. Library mismatch ignored for the board-local footprint copies.

---

## 8-Layer Stackup (`1.0 mm` ENIG POFV — Variants E, F, `f-usbc`)

Variants E, F (`hw/round-pendant/f/round-pendant.kicad_pcb`), and `f-usbc` (`hw/round-pendant/f-usbc/round-pendant.kicad_pcb`) upgraded to an **8-layer `1.00 mm` (`0.9968 mm` physical)** stackup (`decisions.md` 2026-11-04) so `In6.Cu` serves as a dedicated bottom-adjacent signal escape layer while keeping `In2.Cu` (`GND`) and `In5.Cu` (`VSYS` + `+3V3` island) unbroken.

- **JLCPCB 8-layer `1.0 mm` order stackup code:** **`JLC08101H-1080`** (`1.0 mm ±10%`, `1 oz` outer / `0.5 oz` inner, `1080` `0.0764 mm` prepreg, `0.170 mm` cores, `Er = 4.1`, `ENIG`, epoxy-filled & capped `POFV` via-in-pad). Pin `JLC08101H-1080` explicitly on the JLCPCB order form and confirm acceptance of the `3×` `0.20 / 0.10 mm` (`10:1` aspect ratio) vias inside `U3`'s `+3V3` ring during DFM quote review.

| Layer | Type / Material | Thickness (`mm`) | `Er` | Role in Variants E / F / `f-usbc` |
|---|---|---|---|---|
| `F.SilkS` | White legend ink | — | — | Voronoi sunflower web + `Q2` pin-1 dot |
| `F.Mask` | Matte black LPI soldermask | `0.0100` | `3.8` | Dam min `0.10 mm` (JLC ENIG); `876–886` PTH vias tented/capped, `6` NPTHs relieved `1:1` |
| **`F.Cu`** | **`1 oz` finished Cu** | **`0.0350`** | — | `235×` `1010` LED pads + `Q2` + local matrix escapes |
| Dielectric 1 | `1080` prepreg | `0.0764` | `4.1` | Outer build-up dielectric |
| **`In1.Cu`** | **`0.5 oz` (`15.2 µm`) Cu** | **`0.0152`** | — | `SW`/`CS` matrix trees, `VBUS` branch to `U7.5` |
| Dielectric 2 | FR-4 core | `0.1700` | `4.1` | Inner core 1 |
| **`In2.Cu`** | **`0.5 oz` (`15.2 µm`) Cu** | **`0.0152`** | — | **Continuous `plane GND` (`1` whole piece, `847.5–849.3 mm²`)** |
| Dielectric 3 | `1080` prepreg | `0.0764` | `4.1` | Inner lamination prepreg |
| **`In3.Cu`** | **`0.5 oz` (`15.2 µm`) Cu** | **`0.0152`** | — | `SW`/`CS` routing, plane-cooled `VBAT` trunk (`0.30 mm`) |
| Dielectric 4 | FR-4 core | `0.1700` | `4.1` | Center core |
| **`In4.Cu`** | **`0.5 oz` (`15.2 µm`) Cu** | **`0.0152`** | — | `SW`/`CS` routing, `QSPI` / `USB_D*_MCU` short escapes (`0` zones) |
| Dielectric 5 | `1080` prepreg | `0.0764` | `4.1` | Inner lamination prepreg |
| **`In5.Cu`** | **`0.5 oz` (`15.2 µm`) Cu** | **`0.0152`** | — | **Power plane: `plane VSYS` (`1` piece, `600.4–603.5 mm²`) + `plane 3V3` (`1` piece, `215.8–216.1 mm²`)** |
| Dielectric 6 | FR-4 core | `0.1700` | `4.1` | Inner core 3 |
| **`In6.Cu`** | **`0.5 oz` (`15.2 µm`) Cu** | **`0.0152`** | — | Bottom-adjacent signal escape layer (`0` zones) |
| Dielectric 7 | `1080` prepreg | `0.0764` | `4.1` | Bottom build-up dielectric (`h = 0.2616 mm` from `B.Cu` to `In5.Cu` where `In6.Cu` is clear) |
| **`B.Cu`** | **`1 oz` finished Cu** | **`0.0350`** | — | All ICs, passives, `J1` (`TYPE-C-31-M-22` on `f-usbc`), `BT1`, `SW1/SW2`, `TP1..TP8`, `RP2350` `+1V1`/`+3V3`/`VREG_LX`/`GND` zones |
| `B.Mask` | Matte black LPI soldermask | `0.0100` | `3.8` | Dam min `0.10 mm` (`0.300 mm` CAD copper/`B.Mask` gap = `3.0×` min between `BT1.2` and `U8.1..3` on `f-usbc`) |
| `B.SilkS` | White legend ink | — | — | Pin-1 dots (`OD = 0.30 mm`), polarity/rating/switch labels, selective refs |
| **Total** | **8-Layer Stack** | **`0.9968`** | — | Nominal **`1.00 mm ± 0.10 mm`** |

