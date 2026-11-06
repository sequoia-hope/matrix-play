# Sunflower: a low-cost 38 mm round board on 4 layers

Started 2026-11-06 at the user's request. The goal was to take the low-cost parallelogram parts (XL-1615RGBC-RF LEDs, AW20198QNR QFN drivers, all in stock at JLC) into a round board, lay the LEDs out in a sunflower pattern at the lower spacing, find how many LEDs a 4-layer board can route, and cost it down. The user first asked for 32–35 mm, then set the diameter at 38 mm, the same as the main round pendant.

Generator: `scripts/sunflower/`, forked from `scripts/parallelogram/`. Boards: `hw/sunflower/<tier>/`.

## Design

- **Outline:** a 38 mm circle. The 35 mm round cell (403535) sits behind the board and is wired to BT1, as on the main pendant.
- **LEDs:** XL-1615RGBC-RF at 0°, laid out as a Vogel spiral with r = 17.2·√((n+a)/(N−1+a)) and θ = n·137.5°. The innermost LED sits at 2.4 mm, so the centre is left for the Q2 light sensor. Density is uniform over the ring. Where diagonal neighbours' 2.0 × 1.9 mm courtyards would overlap, a relaxation step nudges them apart. That step only did anything at 132 LEDs.
- **Matrix map:** LEDs are sorted by angle and cut into wedges of 11. Each wedge is one CS triplet, with cathodes running radially. Within a wedge, the SW line is the LED's radius rank, so SW_m forms a ring across a driver's wedges. U1 takes the west wedges and U2 the east. The table is generated, so firmware reads it from `build_led_cells()`.
- **Back side:** Variant D is also a 38 mm disc, so its proven RP2350, flash, charger, LDO and USB block keeps its exact position (macro offset 0, 0). The rest of the back is placed as follows:

  | Part | Position |
  |---|---|
  | AW20198 drivers | (±12.6, 3) mm |
  | EVQP7J side buttons | north-east and north-west rim (±21°), 0.40 mm proud of the edge |
  | J1 (USB pads), BT1 | Variant D's positions |

- **Stackup:** 4 layers, JLC04161H-7628. In1 is an unbroken GND plane, In2 is the only inner signal layer. Vias are 0.30/0.15 mm. No vias go through the solid exposed pads except their own GND thermal vias.

## Tiers and results (ultraroute 3de3d83)

| Tier | LEDs | Drivers | mm² per LED | Nearest spacing | Opens | Hard DRC | Vias | Vias in SMD pads | BOM/bd @10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| s1-66 (pofv) | 66 | 1 | 13.8 | 3.46 mm | **0** | **0** | 420 | 79 | $10.61 |
| s2-88 (pofv) | 88 | 2 | 10.4 | 3.00 mm | **0** | **0** | 496 | 89 | $11.90 |
| s2-110 (pofv) | 110 | 2 | 8.3 | 2.69 mm | **0** | 2 (`+3V3` 0.10 mm next to U3) | 619 | 118 | $12.25 |
| s2-132 (pofv) | 132 | 2 | 6.9 | 2.38 mm | **0** | 0 (1 thin pad joint on R16.1, 1 dangling stub) | 673 | 125 | $12.60 |

For comparison, the parallelogram's p2-132 used 9.6 mm² per LED and its p3-162 (10.5 LEDs/cm²) did not close. Main round-pendant Variant E is $26.46 per board in parts, on 8 layers with 5 WLCSP drivers.

"pofv" means the router put same-net vias inside SMD pads (79–125 per board, about half of them in LED pads), so the board must be ordered with filled and capped vias (POFV).

**Threshold:** with vias allowed in pads, every tier up to 132 LEDs on the 38 mm disc routes to 0 opens on 4 layers. s2-110 and s2-132 still have small width and joint defects left by the router at tight spots. Unlike the parallelogram, a sunflower has no columns lined up over the drivers' 3.4 mm solid exposed pads: the escapes spread in every direction, so the 4-layer ceiling is not set by column pitch. Past 132 LEDs the limit would come from LED packing first: at 0° the XL-1615 courtyards start to collide at 132 and needed relaxation.

## Cost-down

Per board at qty 10 (live LCSC prices, `cost.json`):

1. **4 layers instead of 8.** This is the largest saving, in fab cost. Fab price was not quoted; read it from JLC's quote tool.
2. **AW20198 QFN instead of IS31FL3745 WLCSP.** $0.89 against about $2.26 each, in stock at JLC, with no Global Sourcing or pre-order. 66 LEDs need 1 driver; 88–132 need 2.
3. **XL-1615 instead of XL-1010.** $0.0159 against $0.027–0.029 each: $0.84 to $1.47 less per board, and 699k in stock against 12.9k.
4. **No vias in pads.** POFV is an added cost on JLC 4-layer boards. The rules generator now writes `no via hole in an SMD pad` (`physical_hole_clearance`, with the solid exposed pads exempt). ultraroute honours it since 0b0f336. Re-route results are below.
5. **Not yet done: RP2040 instead of RP2350 + L1.** $1.01 against $1.57, which also drops the AOTA inductor (43 in stock at JLC). It means a new MCU block, because the current one is copied from Variant D.

### No vias in pads (s1-66, s2-88)

These were re-routed from bare boards with the rule in place. The generator's pre-placed regulator GND vias now also stay out of all pads, which leaves 1 PGND via where there were 2.

| Tier | Opens | Hard DRC (router output) | Vias | Note |
|---|---:|---:|---:|---|
| s2-88 | **0** | 0 opens; 4 dangling vias and 2 thin pad joints (U2.31 CS2_9, C1.1 VBUS) left over | 512 | `clean_copper_4l.py` broke a connection on this board, so the raw router output is kept (`route/novip_raw.kicad_pcb`, the cleaned copy in `route/novip_cleaned_worse.kicad_pcb`). Still needs a copper clean-up pass. |
| s1-66 | 1 (`SW1_2` at U1 pin 4) | 0 | 451 | Three rip-up passes didn't close it, although s2-88 escapes the same U1 position. One driver carrying all 11 SW lines crowds that side of the QFN. |

Keeping vias out of pads costs at most an open or two and some clean-up, so a POFV-free 4-layer order is in reach at 88 LEDs. The filled-via (POFV) routes are kept as `hw/sunflower/s1-66-pofv` and `s2-88-pofv`, each with fab files.

## Open items

- s2-88 (no vias in pads): copper clean-up (dangling vias, 2 thin joints), then fab export.
- s1-66 (no vias in pads): 1 open at U1's SW side. Try U1 turned 90° or 180° so its SW pins face the LED field.
- The RP2350 `+3V3` band and `+1V1` ring zones fill in 1–4 pieces on these routes. The nets are still joined (0 unconnected), but the reference wants them whole, as Variant F did with locked tracks. Worth checking before fab on whichever tier is chosen.
- ultraroute: the necks and sub-width segments near U3 (s2-110 `+3V3` at 0.10 mm under a 0.15 mm rule, the s2-88 CS1_1 neck) are the min-connection-width items already on the ultraroute session's list.
