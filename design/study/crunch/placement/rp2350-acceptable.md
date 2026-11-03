# What counts as an acceptable RP2350 layout on this board

For the owner to read and argue with. Each row says what the documents say, what the board does now, and my judgement. The judgement is mine, not Raspberry Pi's, and nothing here has been measured on a built board. Raspberry Pi's own position is at the bottom of section 1.

**Sources**

- **DS:** `design/datasheets/rp2350.pdf`, RP2350 datasheet (Jul 2025). Page numbers are the printed ones; the PDF page is one higher.
- **HW:** *Hardware design with RP2350* (Aug 2024). It isn't in this project: I read `~/pcb/RP2350/hardware-design-with-rp2350.pdf`.
- **REF:** Raspberry Pi's RP2350A minimal board KiCad file, read at `~/pcb/bluebuzz/design/reference/RP2350_60QFN_minimal.kicad_pcb`. All "reference does X" numbers are measured from it by script.
- **Project:** `design/parts/rp2350-core.md`, `design/parts/flash.md`, `design/stackup.md`, `design/brief.md`, `design/intent.md`, `.claude/skills/pcb-design/chips/rp2350.md`.

## Decisions I need from you

1. **Regulator block.** Keep it to the reference as a rigid block, but allow PGND's two vias to move about 0.7 mm because an LED sits on the reference's spot. Recommended.
2. **Is the rigid block allowed to turn or move?** The documents fix it relative to the chip, not the board. Recommended yes.
3. **Crystal limit.** Raise XIN/XOUT from 6 mm to 11 mm, the reference's own XIN length. Recommended yes.
4. **QSPI.** Keep 25 mm, but allow vias, and make "drop the flash clock" the accepted fix if the bus is marginal. Recommended yes.
5. **USB.** Drop 90 Ω impedance as a goal, and allow one via per line between the ESD part and the 27 Ω resistors if routing needs it. Recommended yes.
6. **Decoupling.** Set a 4 mm limit for U3's 100 nF parts, pad centre to pad centre, which is what the reference itself reaches. Recommended yes.
7. **U3's exposed pad.** Accept foreign vias through it with at least 5 GND vias left. Recommended yes.

## Faults found: U3 was under-built, not over-strict

These aren't relaxations. Fix them before relaxing anything, whatever you decide above. All of this is in `scripts/board.py zones_b` and so in every trial up to and including the shared 8-layer start, `hw/round-pendant/c/route/preroute_8L.kicad_pcb`.

- **The 3V3 band touched no pin.** It's drawn at ±2.8 mm and U3's pad inner ends are at ±3.0 mm. `chips/rp2350.md` says it "reaches the inner ends of the pads". It doesn't, on the vendor board either: same ±2.8, same pads, joined with short tracks. So that sentence in the skill is wrong.
- **A rule area blocked the fix.** "U3 no tracks inside pads" at ±2.9 mm keeps out every net, so all 10 +3V3 and 4 +1V1 pins had to escape outward through the GPIO ring.
- **The 1V1 ring was empty on older boards.** A zone-clearance bug left it with no copper until `preroute_v2`. Don't judge the ring by any board before that.
- **The LX plane cut is on the wrong layer.** `chips/rp2350.md` says "layer 2" and the script cuts In2 (GND). U3 is on the back, so the copper next to LX is the layer above B.Cu: In4 on 6 layers (0.099 mm, and `design/brief.md` itself says "In4 is cut"), In6 on 8 layers. As built, the plane nearest LX runs solid under it and GND is cut for nothing.
- **The crystal and USB pairs were placed crossed.** On the back of the board, XIN (pin 21) sits left of XOUT (pin 22), but Y1's XIN pad was on the right, with R17 between them. USB had the same fault: R14 (D−) was left of R15 (D+), the opposite of the pins and of the reference's order. The router went round: in one first-pass route XIN reached 20.3 mm and USB_DP 47.1 mm. Turning Y1, moving R17, and swapping R14/R15 and C23/C24 (trial y11) gives XIN 12.4 mm, XOUT 1.7 mm plus 2.2 mm, and USB_DP and USB_DM 19.5 and 19.4 mm in the same kind of pass.
- **The regulator's zones aren't on the board.** The VREG_LX, 1V1, 3V3 and PGND zones and PGND's two vias are missing. `design/gates/phase6.md` lists them as a first step of phase 7.

**The fix, as built.** `scripts/crunch/placement/u3fix.py` does all of it without moving a part: band out to the pads, 0.2 mm 1V1 fingers from the ring to pins 6, 23, 39 and 50, the ring rule limited to foreign nets, the vendor's four zones, an FB finger from pin 50 to the COUT zone, PGND's two vias, CFILT's own via, the LX cut on In6 and In5, a window under L1, and a 3V3 via in 5 of the band's 6 pieces. The sixth, 0.35 mm², has no free via site. The 1V1 fingers cut the band into pieces, which the reference doesn't do: it reaches DVDD through spoke vias on the far side. Mine has no via in 1V1 at all.

**Routing cost of the fix, measured on 8 layers at 1200 s.** It costs nothing I can detect:

| Board | Signal open | Plane open | New errors | Vias |
|---|---:|---:|---:|---:|
| Shared 8-layer start (`c-layers-v3-8a`) | 56 | 9 | 55 | 961 |
| Same, with `u3fix.py` (`c-placement-y1`) | 57 | 11 | 54 | 956 |

On y1, no +3V3, +1V1, GND, VREG_LX or FB connection at U3 is open, and `pad_joints` passes. 11 other nets are still open, among them XIN, XOUT's capacitor side, USB_DM and four more U3 signals. The router still put 3.7 mm of track on VREG_LX beside the zone, and I haven't looked at why. An earlier 6-layer run of the regulator part alone (x6) scored 128 against 121 for its baseline, on an older base.

## What 8 layers changes

Stack in `scripts/crunch/layers/mk8.py`, an estimate that totals 1.0 mm, not JLC's table: F, In1, **In2 GND**, In3, In4, **In5 VSYS and 3V3**, In6, B.

| Topic | 6 layers | 8 layers | Effect on this list |
|---:|---:|---:|---|
| Copper next to B.Cu | In4 plane, 0.099 mm | In6 signal, 0.076 mm | Under LX keep In6 empty. **The cut now costs routing space, not plane area,** but only about 12 mm² on one layer |
| Nearest plane under the regulator | In4 3V3/VSYS | In5 3V3, about 0.26 mm | I cut In5 too, so LX has no plane within about 0.33 mm |
| GND under the regulator | In2, about 0.48 mm | In2, about 0.57 mm | Further away. The reference has GND on the far layer, which DS p.454 calls out. See the option below |
| PGND and CFILT via paths | 2 vias to In2 | Same, slightly longer | No change in the rule. Keep both short |
| Crystal, QSPI, USB over a plane | Plane next to B.Cu | Plane two layers up | Less stray capacitance, so the crystal relaxation has more room. USB reference is still not GND. Still don't care |
| Decoupling | Via to plane | Via to plane, slightly longer | No change |
| Exposed-pad vias | Pass 4 inner layers | Pass 6 inner layers | Each still blocks every layer. Via count matters the same |

**Option for you: a local GND island on In6 under the regulator.** It would give the block a ground 0.076 mm away, as close as anything gets, joined through PGND's vias. The datasheet says the layer under the regulator is ground in its best-practice layout (DS p.454). It costs In6 routing space under the block. Measured at 1200 s, default cell, it costs no opens I can see: 19 open / 10 plane / 58 errors / 999 vias with the island (y3), against 23 / 12 / 101 / 999 without (y2). But on the complete route (y17) routed copper cut it from 9.9 to 1.8 mm², so it gives almost nothing. I've dropped it. A real plane here would need In6 reserved for it.

## The open question: the 1V1 ring against the LEDs above it

The first complete route (`c-placement-y17`, tidied as `c-placement-y18`) has no opens, but it isn't acceptable. Router vias through the ring cut it from 6.1 to 1.5 mm², so 1V1 relies on about 72 mm of thin inner track between pins, which is the failure `chips/rp2350.md` exists to prevent. LEDs sit over the ring, and their cathodes want a via in the pad.

I routed two ways out:

- **y19:** keep the B.Cu ring and forbid new foreign vias inside ±2.3 mm. Closest to the reference, hardest to route.
- **y20:** replace the ring with a 1V1 pour on In6 under U3, about 70 mm², joined at each DVDD pin and COUT by a via. Only 8 layers makes this possible. It departs from the reference's ring, but it's closer to what the ring is for: low impedance from COUT to every DVDD pin. Foreign vias then punch holes in it, as they do in the planes, without cutting it apart.

**Result.** Keeping the ring works, so I recommend it. Both at 3000 s, `--cell 0.025`:

| Board | Signal open | Plane open | New errors | Vias | 1V1 copper after routing |
|---|---:|---:|---:|---:|---|
| y19, ring kept, no new foreign vias within ±2.3 mm | 0 | 2 | 5 | 895 | Ring one piece, 6.0 mm² |
| y20, pour on In6 | 1 | 1 | 1 | 897 | Pour in 5 pieces, 30 mm² of 70 mm² |

The LEDs over the ring leave on F.Cu instead, through vias just outside it. 3 anode vias stay in the exposed pad as before.

## 1. Core regulator: loop and inductor copper

**Documents.** This is the one area where the wording is strict.

- "The most critical part of an RP2350 PCB layout is the core voltage regulator... these guidelines must be strictly followed" (DS §6.3.8, p.452).
- Follow the schematic and layout "as closely as possible" (DS p.454). HW p.6 goes further: "if you choose not to use our example, then you do so at your own risk". It also says a layout may 'work' while not "producing the correct output voltage under a range of load current conditions".

**Load on this board.** DS Table 1446 (p.1347) gives 11 to 14.7 mA on VREG_VIN at 3.3 V, for CoreMark single core at 150 MHz and for `hello_usb`. The regulator is rated to 200 mA (Table 1442, p.1344). My estimate is 25 to 40 mA of core current here, so 15 to 20 % of rating. DS §6.3.8.3 (p.456) says orientation matters "especially at higher output currents and for higher load transients". That gives real margin, but it's my inference: no document says the layout rules loosen at low load.

| Feature | Documents | Now | My call | If it's wrong, and how we'd know |
|---|---|---|---|---|
| CIN, L1, COUT same side as chip | "Don't place any of CIN/LX/COUT on the opposite side" (DS p.454) | Same side | **Must keep** | Larger switching loop. Scope 1V1 at COUT |
| CIN, COUT, L1 offsets from chip | Follow Figure 23 (DS p.454) | Exact offsets, mirrored for the back | **Must keep** | Same |
| Whole block moved or turned with the chip | Rules are relative to chip and parts, never the board | Not moved | **Can relax: free**, as one rigid block with its plane cut | None that I can find. Field orientation is relative to its own loop |
| Marked inductor, AOTA-B201610S3R3-101-T, reference rotation | Marked polarity, placed as Figure 23; wrong way round affects output voltage (DS p.455, p.456; HW p.6) | Correct: checked pad 2 (LX) on the right of chip frame, as the reference | **Must keep** | Output voltage error under load. Stock still 1 at JLC (`rp2350-core.md`) |
| Back-side mirroring | Not covered. Seen from its own side the block is identical to the reference | Pins and pads checked | **Fine.** Worth stating because a flip looks like a change | |
| VREG_LX, 1V1, 3V3, PGND as short wide copper | Keep loops "small and low-impedance" (DS p.454) | **Missing**, router lays it | **Must keep**, as zones. Can't be left to routed wire: easy2350 got 35 mm of 0.2 mm 1V1 and a 9 mm FB loop that way (`LESSONS.md`) | Ripple, regulation, EMI |
| PGND to main GND at one point, two adjacent vias | "One single point (using 2 adjacent vias)", "critical" (DS p.455) | **Missing** | **Must keep single point and two vias** | Switching current in the chip's ground |
| Those vias at the reference's spot | Figure 23 | Reference spot, (1.7, -1.7) and (1.7, -1.1), lands on D155's pad 4 | **Can relax:** u3fix uses (1.06, -1.55) and (0.95, -1.14), between CIN's and COUT's own GND pads. About 0.7 mm closer to them and to LX. No LED moved | Slightly different loop; I expect no worse. Scope as above |
| No copper under L1 and LX on the part's layer | Cut away extra copper under the inductor, cut back near LX (DS p.454) | u3fix: "L1 window" rule. One SW2_9 anode via sits inside L1's courtyard, outside its body; DRC flags it and it predates the rule | **Must keep.** Zones plus a rule area. Move or accept that via | Parasitics on LX |
| Cut on the next layer down | "Cut away any copper immediately underneath LX" on 4+ layers, Figure 24 (DS p.455) | Cut on In2, the wrong layer. u3fix: In6 and In5 | **Must keep**, on the layer next to B.Cu. In2 GND then needn't be cut | About 0.8 pF per 2 mm² of LX over a plane 0.1 mm away (my estimate): extra LX switching loss |
| Next layers under LX | Not covered | u3fix: In6 no tracks or copper, In5 no plane. In4 and below free | **Judgement: this depth is enough** | Coupling of 3.3 V edges into signals on In4 |
| CFILT own GND path, not shared | "Don't share any GND vias" with CIN/COUT (DS p.455) | C17 router-joined | **Must keep** | VREG_AVDD noise. It's the named noise-sensitive pin |
| R13, C17 positions | RC filter required (DS p.454). Exact spot only by Figure 23 | 0.5 mm further out than reference (gate 6, foreign via) | **Can relax: up to 1 mm**, no LX-adjacent run. VREG_AVDD draws about 200 µA (HW p.7) | Scope AVDD |
| VREG_FB from COUT, not under L1 | "Fed from the output of COUT, avoiding routing directly underneath LX" (DS p.455) | Pin 50 and COUT zone | **Must keep** | Output voltage error |
| Second 4.7 µF at pin 23, away from LX | "For best performance we recommend" (DS p.455) | C19, 1.87 mm | Keep: costs little. **Can relax distance** up to 4 mm (reference 3.07 mm) | Slightly worse transient |
| Foreign vias near L1 | Not covered specifically | SW nets at (-0.85, 0.12), (1.9, 1.62), (2.52, 1.64), and LED D155 opposite | **Judgement: allowed outside the zones.** Through vias don't count as "copper under" once they're clear of the window | SW lines switch up to 494 mA. See section 8 |

**Raspberry Pi's position.** Everything above marked "can relax" is at our own risk, in HW's words. I'm comfortable because the relaxations don't touch the loop itself.

## 2. Decoupling distance

**Documents.** "It is important to place decoupling close to the power pins"; one 100 nF per pin is usual, and pins 53/54 share one to save room (HW p.8). Being further away "could have the effect of limiting the maximum speed"; "for most applications, this trade-off should be acceptable" (HW p.8). No document gives a number. COUT 6 nH maximum (DS p.455) is the only hard parasitic.

**The reference's own distances** are longer than people assume (pad centre to pin centre, measured):

| Pin | 1 | 11 | 20 | 30 | 38 | 45 | 54 | 6 | 23 | 39 | 49 CIN | 50 COUT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Reference, mm | 2.64 | 2.58 | 2.24 | 2.47 | 3.19 | 2.58 | 3.88 | 2.57 | 3.07 | 3.17 | 1.17 | 2.13 |
| This board, mm | 1.60 | 1.60 | 2.40 | 1.60 | 2.73 | 2.61 | 3.10 | 1.60 | 1.87 | 2.61 | 1.17 | 2.13 |

This board's pins 45 and 54 columns are its C14 at pin 44 and C13 at pin 53. It already beats the reference on all but pins 20 and 44/45. `checks.toml`'s 7 mm limit is far looser than U3 needs.

**My call.**

- **Don't care:** bulk distance.
- **Can relax:** U3's 100 nF parts up to 4 mm pad centre to pad centre, about the reference's worst case.
- **Must keep:** CIN and COUT as in section 1.

Check: scope IOVDD and 1V1 at a far pin during full-speed flash and PIO activity. Run a CPU stress test for BOD resets (§7.6.2).

**At this clock:** firmware needs far less than 150 MHz to scan LEDs, and HW names maximum speed as what suffers. That's a real fallback.

## 3. Crystal

**Documents.** Use the ABM8-272-T3 with 15 pF and 1 kΩ, "any deviation... will require extensive testing" (HW p.12, DS Table 597 p.555). PCB stray assumed 3 pF; "try and keep the layout as short as possible" (HW p.12). The documents give no length or via rule.

**Reference, measured.** XIN 10.9 mm, XOUT 3.0 mm to the resistor, then 5.4 mm to the crystal. No vias.

**Now.** nets.csv limits XIN and XOUT to 6 mm with no vias, tighter than the reference on XIN. On y11's first pass, XIN measures 12.4 mm and still fails 6 mm, with C23 on the far side of Y1. XOUT passes. Turning C23 should bring XIN down, not yet tried.

| Feature | My call | Risk and check |
|---|---|---|
| Part and values | **Must keep** (documents are explicit) | |
| Length under 11 mm per net | **Can relax from 6 mm.** My estimate is 0.06 to 0.08 pF/mm over In4, so 11 mm is under 1 pF of the assumed 3 pF | Frequency pull, slower start. USB is the frequency test: it either enumerates or doesn't. Time XOSC `STABLE`, cold and warm; 1 ms is the default wait (DS §8.2.4) |
| Via | **Keep no vias on XIN and XOUT if we can.** One each is an acceptable last resort (about 0.3 pF, my estimate) | Same |
| Scan-line coupling | **Judgement: keep SW lines off B.Cu and In3 next to XIN.** The documents don't address it, but it's the one thing here a reference board doesn't have | XOSC jitter shows up as USB errors with LEDs scanning |
| Load-cap ground | Short route to plane | |

## 4. QSPI

**Documents.** "Should be wired directly to the flash, using short connections" for integrity and crosstalk (HW p.9). No number. No via rule. "Minimise the track length" (DS p.1331, on RP2354's in-package flash).

**Reference, measured.** SCLK 11.0, SD0 8.6, SD1 16.7, SD2 13.0, SD3 12.5, SS 21.5 mm. No vias. No length match.

**This board's firmware.** Flash holds animations. 702 bytes at 60 fps is about 42 kB/s (my figure), far below the bus's capacity.

| Feature | My call | Risk and check |
|---|---|---|
| 25 mm limit | **Keep.** It's above the reference's longest. Flash moves are fine within it | |
| Vias | **Can relax: allowed**, up to 2 per net | About 0.3 pF each; small at these lengths |
| Length match | **Don't care.** Reference doesn't, at these lengths | |
| 75 MHz | **Can relax in firmware.** Lower the divider if read margin is thin. Costs only code fetch speed | Check: flash hash test at each divider, LEDs scanning, on 3 boards |
| Flash EP area | `flash.md`: no exposed vias under pad (W25Q p.69). `NoEPCopper` footprint with vias under it needs **tented or filled vias.** Must keep; can't be waived | Solder wick, shorts |
| QSPI_SS to BOOTSEL | Keep resistor near the flash and chip (HW p.9). R16 sat 15 mm away by SW2, which pushed QSPI_SS over 25 mm on 8-layer trial y5. Trial y6 moves it to (-2.37, -1.90), beside the QSPI pins, and the length error goes. The long run is now on R16's button side, which is slow | Stray on SS. Check: boot from cold |

## 5. USB

**Documents.** 27 Ω "placed close to the chip" (HW p.14; Figure 6's note on p.8 says the same). Aim for 90 Ω with solid ground below, but "USB FS can be quite forgiving" (HW p.14). Reference: 27 Ω to pins 3.9 and 4.1 mm, then 18 mm at 0.8/0.15 mm over ground on the far layer.

| Feature | Now | My call | Risk and check |
|---|---|---|---|
| 27 Ω at pins | 1.2 mm closer than reference | **Must keep** | |
| 90 Ω impedance | Not controlled (`stackup.md`) | **Don't care.** 12 Mb/s over about 12 mm is electrically short (my calculation) | Check: enumerate, bulk transfer, on several cables and hosts |
| Coupled pair, same layer | `--diff-pairs` | **Keep where free.** Skew under 1 mm is plenty | |
| "No vias" ESD to resistor | nets.csv rule | **Can relax: 1 per line.** The rule is ours, not Raspberry Pi's | Same check |
| Solid reference plane | B.Cu's neighbour is In4 (VSYS/3V3), not GND | **Don't care** at this speed, with a cap nearby | EMC isn't a target (intent: none formal) |
| ESD at connector | U7 by J1 | **Must keep** | |

## 6. Exposed pad and ground

**Documents.** GND is the "single external ground connection", through this pad (DS p.16). θJA 40.5, θJB 12.6, θJC 14.3 °C/W (Table 1423, p.1328). Reference: 9 holes in the pad. "Short-as-possible" path from PGND and CFILT back to it (DS p.455). There's no thermal rule and no via count.

**Thermal.** About 53 mW (Table 1446) × 40.5 °C/W gives about 2 °C above the board (my calculation). **Don't care** thermally on this board, even at several times that.

**Electrical.** It's the chip's only ground, so it needs low impedance. That's the actual reason for vias here.

| Feature | Now | My call | Risk and check |
|---|---|---|---|
| Thermal via count | 9 found, plus 3 foreign vias cutting tiles | **Can relax to at least 5**, spread. 9 is reference. About 0.4 nH per via through this 1 mm board (my estimate) | Ground bounce. Check with 1V1 and IOVDD scope above |
| Foreign vias through pad | 3 SW vias, tiled. Trial x13 adds cathode vias for 8 in total, still 9 GND | **Accept**, with 0.3 mm around them. Reference has none | SW lines through the chip's ground pad: see section 8 |
| Paste on tiled pad | **Not added yet** (decisions.md, "needed before release") | **Must fix** before release | Missing paste leaves the chip's only ground unsoldered |
| Tiles at 0.15 mm cells | Fine for JLC? **Not checked** with them | Ask JLC | Fab question, DFM |

## 7. 1V1 ring, spokes and 3V3 band

**Documents.** The datasheet doesn't describe these. They're in REF and `chips/rp2350.md`: ring ±2.2 mm, band ±2.8 mm with short tracks to the pins, four 0.6 mm spokes. So this is good practice in one reference, not a stated requirement.

**Why they matter.** DVDD range is 1.05 to 1.16 V, 1.1 typical (Table 1441), and FB senses at COUT. Each DVDD pin must be low impedance to COUT. 20 mm of 0.2 mm 1 oz is about 50 mΩ (my estimate): at 100 mA peak that's 5 mV of the 50 mV margin. DC isn't the issue. Inductance is, which is what local 100 nF parts handle.

| Feature | My call | Risk and check |
|---|---|---|
| Ring present, joined to pins 6, 23, 39, 50 | **Must keep connection.** They were open in earlier trials. u3fix joins them with B.Cu fingers, so there's nothing left to route | Won't boot reliably |
| Ring whole, no breaks | **Can relax:** breaks allowed if every segment reaches a spoke | Check: DRC connectivity, 1V1 at each pin |
| Vendor's 0.6 mm spokes through vias | **Replace with 0.2 mm fingers on the same layer**, each about 0.8 to 1.3 mm long. Shorter than the vendor's path, narrower, and no via. A departure from REF that I think is better here | As above |
| 3V3 band | **Must reach the pins.** Whole isn't needed: the fingers cut it into 6 pieces, each with a via to the 3V3 plane except one 0.35 mm² piece | Less shared decoupling |
| No foreign tracks in pad ring | **Keep for foreign nets only.** The old rule kept out U3's own power too, which was the fault above | |

## 8. Not in any document: scan lines through the MCU

The reference has no neighbour switching 494 mA peak (nets.csv) every 32 µs. Here 15 SW vias sit inside U3's ±3.5 mm square, and through the pad as well. That worries me more than most relaxations above, and no document covers it. I'd keep the vias, as the sunflower forces them. Bring-up should measure 1V1, VREG_AVDD and XIN with full-white scanning on and off. If that shows a problem, firmware can spread scan edges or lower the clock, but neither is proven.

## Don't care at this clock and power

- USB impedance and reference plane, at 12 Mb/s and short length.
- QSPI length matching.
- U3 thermal vias, as heat paths.
- Bulk capacitor distance.
- Full 150 MHz. Firmware can run slower if decoupling or flash limits show up.

## Bring-up checks for the relaxations

Build 5 boards, not one.

1. **1V1:** at COUT and at pin 6 and 23, under full-white scanning and CPU load. Against ±3 % (Table 1442) and 1.05 to 1.16 V (Table 1441).
2. **VREG_VIN current:** compare against Table 1446, 11 to 15 mA. A big excess means the regulator isn't happy, the symptom HW p.6 describes.
3. **VREG_AVDD:** ripple with scanning on and off.
4. **XOSC:** time to `STABLE`, cold and warm. USB enumeration with LEDs at full.
5. **Flash:** read hash at each clock divider, LEDs scanning.
6. **Reset log:** BOD and watchdog reset causes after a soak test.
