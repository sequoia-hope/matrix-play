# Design intent: round-pendant

Phase 0. Every item has a number or an explicit "don't care". **(default)** marks a value
the request left open and Claude filled in; the user accepted these at sign-off on 2026-11-02.

## Purpose

A round wearable LED display, worn as a pendant or watch. The whole front is a dense grid of
1 mm RGB LEDs on a 2 mm pitch; all electronics are on the back. It runs from a single LiPo cell,
charges and takes firmware over USB-C, shows animations from an RP2350A, and sleeps at low current
until a button press or movement wakes it. For personal use and small runs.

## Open source or confidential

Open source **(default)**, like the user's other personal boards: CERN-OHL-P-2.0, GitHub repo URL
on silkscreen once a repo exists. Tool: KiCad 9, Boardroom project layout.

## Requirements

| # | Requirement | Value | Checked at |
|---|---|---|---|
| R1 | Outline | Circle, 38.0 mm diameter (±0.2 mm fab tolerance) | Edge.Cuts |
| R2 | LED count | 234 exactly, the two-driver limit (2 × 13 × 9). Grid count: 241–256 sites fit in 38 mm with 0.35–0.5 mm from land to edge, depending on grid offset, so the drivers set the count, not the board | placement |
| R3 | LED grid | 2.000 mm pitch, square, all LEDs same orientation unless routing shows a reason, top side only. The 234 sites nearest the centre (land corners reach ~18.1 mm radius, leaving ~0.9 mm to the edge); offset chosen in phase 4. The 7–22 spare sites are not populated | placement |
| R4 | LED part | XINGLIGHT XL-1010RGB-YG, LCSC C965834. Datasheet p.8: pad 3 common anode; 1 R, 2 G, 4 B cathodes. Land 0.45 × 0.45 mm, 0.35 mm gaps, 1.25 mm overall | footprint |
| R5 | LED drivers | 2 × Lumissil IS31FL3741A-QFLS4-TR, QFN-60 7 × 7 mm, LCSC C2940604. Each 39 CS × 9 SW wired as 13 × 9 RGB. LED anodes on SW, R/G/B cathodes on CS triplets | schematic |
| R6 | Driver control | One shared I2C bus at up to 1 MHz (datasheet: 1 kΩ pull-ups at 1 MHz). 7-bit addresses 0x30 (ADDR = GND) and 0x33 (ADDR = VCC) **(default)**. SDB and INTB of each driver on their own GPIO. Whole-panel update: 702 PWM bytes plus page writes ≈ 6.7 ms at 1 MHz, so ≥ 60 fps at ~44 % bus use. Driver logic threshold set to LGC = 1 (VIL 0.6 V, VIH 2.4 V, datasheet p.6), because the RP2350's VOL max of 0.5 V misses the default VIL of 0.4 V. The write that sets LGC is itself received at 0.4 V: GPIO4/5 at 12 mA drive gives ~0.15 V at 3.3 mA, so this holds in practice, not by spec; measured at bring-up | schematic, firmware |
| R7 | MCU | RP2350A QFN-60, LCSC C42411118. On-chip core regulator with the reference power layout (skill `chips/rp2350.md`). 12 MHz crystal, standard decoupling | phase 1, 6 |
| R8 | Flash | W25Q-series QSPI, 16 MB (128 Mbit) **(default)**; animations live here. Larger parts idle at more current than the W25Q16JV behind the RP2350 table, so R17 requires deep power-down in sleep; the part's figures and release on wake are checked in phase 1, and capacity comes down if they don't close | schematic |
| R9 | Debug | SWD and RUN on test pads, not a connector **(default)**. Test pads on VBAT, VSYS, 3V3, 1V1, I2C | layout |
| R10 | Buttons | Two **(default)**: SW1 user/wake on a GPIO (RP2350 has 4 power-up wake sources, any GPIO, §6.2.3.2; SW1 and the accelerometer use two); SW2 BOOTSEL. Side-actuated, on the bottom side at the board edge, reachable through a housing | schematic, layout |
| R11 | Accelerometer | I2C, low power, with a motion-wake interrupt on a wake-capable GPIO. On its own I2C bus **(default)** so it need not support the drivers' 1 MHz. Part chosen in phase 1; target ≤ 3 µA in wake-on-motion | phase 1 |
| R12 | Assembly | Double-sided at JLC. LEDs top; everything else bottom; no parts other than LEDs on top | release |
| R13 | Layers | 6 layers, through vias with via-in-pad, by the user's decision at sign-off. No blind vias. Rigid FR-4, 1.0 mm finished thickness. JLC-manufacturable | stackup |
| R21 | Matrix escape | Land spacing is 0.75 mm between LEDs. Planned per LED: R and B in the channels (two tracks per channel), G under the body through the 0.35 mm centre gap, anode down one via in pad 3 to rows on In1. Needs 0.1/0.1 mm track/space or finer and a via fitting the 0.45 mm pad. Confirmed against JLC limits in phase 5 | stackup, routing |
| R22 | Battery monitoring | VBAT read by RP2350 ADC0 through a 100 kΩ / 100 kΩ divider switched by GPIO14 with a P+N FET pair (NTZD3155C), zero draw in sleep. The ADC is ratiometric to 3V3, so it only reads true while the LDO regulates: VSYS ≥ 3.5 V. Firmware blanks LEDs and sleeps below 3.5 V, and stays asleep on wake if still below it. This also keeps VREG_AVDD and USB_OTP_VDD above their 3.135 V minimum (RP2350 Table 1441). It costs roughly the lowest 10 % of charge; below this the cell self-drains to the protector's 2.4 V cut-off, and USB recovers it | schematic, firmware |
| R23 | Charge indication | Charger status on a GPIO, shown on the LEDs; no separate status LED **(default)** | schematic |

## External interfaces

| Connector / link | Direction | Signal | Voltage (normal / worst case) | Current (cont. / peak) | Mates with |
|---|---|---|---|---|---|
| J1 USB-C receptacle, USB 2.0 pins, bottom side, at the edge, facing out | in/bidir | VBUS, D+/D−, CC1/CC2 (5.1 kΩ Rd each, sink only) | 5 V / 5.5 V sustained; a non-compliant charger above 6 V: don't care beyond the charger's own rating. ±8 kV contact ESD on connector pins (hand-plugged by users) | ≤ 500 mA from VBUS, charge plus system, limited in hardware by the charger (R14); no USB PD. The charger gives the load priority: 300 mA LEDs + 40 mA logic leaves ≥ 110 mA for charging while LEDs run at the limit, 300 mA when they don't | any USB-C cable or charger |
| USB data | bidirectional | USB 2.0 full speed, 12 Mb/s from the RP2350 | 3.3 V signalling | — | host PC |
| BT1 battery: pads or a small connector, chosen with R16 | in/out | Single LiPo cell | 3.0–4.2 V; 0 V or absent cell must not stop USB operation; reversed cell: see below | ≤ 1 A peak discharge (R19), ≤ 100 mA charge | the cell |
| SW1, SW2 | in | Buttons | 3.3 V; finger ESD on SW1 clamped or series-protected at the GPIO; SW2 unprotected, as on the Pico | — | finger |
| Reverse cell | — | Don't care if a keyed connector is used; if bare solder pads, marked on silkscreen and not protected | — | — | — |

No radio. No other I/O.

## Power

- **Input:** USB VBUS only for charging.
- **Battery:** R16 below. On-board protection IC (XB9901A), because the listing doesn't say whether the cell has its own; harmless if it does.
- **Power path:** R14 below. Battery and VBUS feed a system rail VSYS, so the board runs with a flat or absent cell and the load does not fight the charge termination.
- **Rails:**

  | Rail | Source | Load | Typ | Max |
  |---|---|---|---|---|
  | VSYS | Power path, 3.0–4.5 V | LED drivers' PVCC/AVCC (the SW lines), per R5 and the request. Each driver draws 3.6–4.5 mA even with PWM = 0 (p.5), so firmware holds SDB low when blank | 8 mA + LEDs | 880 mA (R18), firmware capped at R19 |
  | 3V3 | Low-Iq regulator from VSYS, 3.3 V ±3 %, tracking VSYS in dropout | RP2350 (one core, ~150 MHz, USB) 30 mA typ, 100 mA max; flash 25 mA max; accelerometer; I2C pull-ups 7 mA at 1 MHz | 40 mA | 150 mA |
  | 1V1 | RP2350 on-chip regulator | RP2350 core | — | internal |

- **Sequencing constraint (datasheet, IS31FL3741A p.5):** input pins must stay ≤ VCC + 0.3 V. The drivers' VCC is VSYS and their logic is 3V3, so 3V3 must never exceed VSYS + 0.3 V. A regulator fed from VSYS meets this by construction; do not add any other 3V3 source.

| # | Requirement | Value | Checked at |
|---|---|---|---|
| R14 | Charger | Single-cell Li-ion with power path or discrete load sharing; charge 300 mA (0.5 C). BQ24073: input limit 450–500 mA, VSYS regulated 4.3–4.5 V on USB, overvoltage cut-out at 6.6 V, so the drivers never see VBUS. The load has priority over charging | phase 1 |
| R15 | Regulator | TPS7A0233: Iq 25 nA, 200 mA | `parts/ldo.md` |
| R16 | Battery | **Changed 2026-11-03 by the user to a 403535 round pouch cell: 35 mm round, 4 mm thick. Capacity and ratings not confirmed; about 400-450 mAh estimated. The figures that follow are for the earlier cell.** Earlier: Grepow 5435035 round LiPo, user's choice. Listed at 610 mAh, 3.85 V nominal, 1C, 35 × 35.1 × 5.45 mm, 10 g. Sources disagree on voltage (resellers 3.85 V; Grepow's guide lists 4.4 V and 620 mAh), so it is charged to 4.2 V, safe for either and below rated capacity. Sits behind the board's bottom parts. Leads solder to pads BT1 | `parts/battery.md` |
| R17 | Sleep current | ≤ 85 µA from the cell, typical at 25 °C except where noted. RP2350 P1.7 57 µA (Table 1445, with W25Q16JV) + W25Q128 extra standby ~9 µA (ICC1 10 µA typ) + accelerometer 2 µA (1 µA is the 1.8 V figure) + drivers ≤ 2 µA + LDO 0.6 µA (ground current) + charger 6.5 µA (max at 85 °C) + protection 3.9 µA = ~81 µA. About 250–300 days. Flash deep power-down is not assumed: the bootrom's documented exit is XIP exit only, so it needs a warm-boot path in firmware. P1.7 loses SRAM. Firmware clears the latched pad pull-downs on all nine pulled-up pins before sleep (§9.7): GPIO 2–5, 8, 9, 12, 13 and 26, which otherwise cost 15–89 µA each. Bring-up: a freshly soldered cell may need USB plugged in once to release XB9901A (its note 3) | `parts/`, bench |
| R18 | LED current, hardware limit | R_ISET **≈ 30 kΩ (default)**: 12.7 mA peak per channel by IOUT = 383 V/R (datasheet p.17), 1.25 mA average per die at full PWM. Full white 702 × 1.25 mA ≈ 880 mA. LED ratings: 20 mA continuous; 60 mA (R) and 80 mA (G/B) pulsed at ≤ 0.1 ms, ≤ 1/10 duty. OK: tSCAN 32 µs, duty 1/10.125 | phase 1 |
| R19 | LED current, firmware limit | Average ≤ 300 mA on battery and on USB **(default)**, 0.5 C; ~2 hours at the limit. It keeps driver heat down; the 880 mA hardware maximum exceeds the cell's 1C. Typical animations far lower. Brightness target: don't care beyond R18 | firmware note, bring-up |
| R20 | Peak current | 2 × 39 × 12.7 mA ≈ 1.0 A pulses at the scan rate if both drivers align, smoothed by local capacitance at each PVCC | phase 1 |

## Environment

- 0–40 °C ambient, worn on the body, indoors and outdoors. Moisture and vibration: don't care beyond the housing.
- ESD: hand-handled wearable. USB pins protected per the interface table. LED face: don't care, a window or diffuser covers it **(default)**.
- Case heat: drivers dissipate ~0.25 W each at R19 on battery (~150 mA each × ~1.7 V), and up to ~0.38 W with red-only content on USB at 4.5 V. Datasheet θJA is 33 °C/W on a 76 × 114 mm JEDEC board, and likely twice that on 38 mm, so +15 to +25 °C at the limit; this board is smaller, checked in phase 8. Firmware limit is the protection; no temperature sensor beyond the RP2350's own.

## Mechanical

- Housing: not designed yet. Don't care for this revision, beyond the three constraints here **(default)**.
- Top-side height: LEDs only, 0.4 mm. A diffuser or window sits on them.
- Bottom-side height: ≤ 3.5 mm, set by the USB-C receptacle. Stack: 0.4 LED + 1.0 board + 3.5 parts + 5.45 cell ≈ 10.4 mm before the housing.
- Holding: no mounting holes. The spare LED sites and ~0.9 mm rim allow a lanyard hole or edge slots to be added in phase 4 if wanted **(default: none)**.
- USB-C: every 16-pin part checked has four through-hole shell legs and most also have locating pegs; the rear features sit ~6 mm in from the edge, inside the LED field. Phase 4 decides how the grid and connector coexist (risk 5).

## Manufacturing

- JLCPCB PCB and PCBA, double-sided. Quantity 5 assembled **(default)**.
- Stock on 2026-11-02: XL-1010RGB-YG 12,489 (~53 boards); IS31FL3741A-QFLS4-TR 455 (~227 boards); RP2350A 4,738.
- Cost target: don't care for this prototype.

## Serviceability

Hobby board, not repairable in the field. Test pads as R9. Designators on bottom silk where they fit; top side bare, it is the display.

## Compliance

None formal. No radio. **(default)**

## Part substitution from the request

The request named IS31FL3741 with IS31FL3729 as fallback. Found at phase 0:

- IS31FL3741-QFLS4-TR (C2678817) has 0 JLC stock. IS31FL3741A-QFLS4-TR (C2940604) has 455 and is the same 39 × 9 QFN-60 7 × 7 mm with the same 13 × 9 RGB application circuit. Using the A, datasheet Rev. C 2020.
- IS31FL3729 is not needed. It is also not an equal fallback: 15 × 9 dots is 5 × 9 = 45 RGB per chip, so two chips would drive 90 LEDs, not 234.

## Known risks and open questions

1. **Through vias against bottom-side parts: the main layout risk.** Each LED needs one via, on a 2 mm grid, through the whole bottom side, and the three 7 mm QFNs sit under roughly 40 LED sites. The user chose through vias, 6 layers, via-in-pad over blind vias. Under an IC a via must land in a cut-out in the exposed pad, or as a same-net via in a pad. The drivers' channel is only 0.325 mm (pad 5.40 mm, inner pad ends 6.05 mm, p.22), too small for a via, so their options are cut-outs or smaller exposed pads and same-net vias. W25Q128JV §10.3 also says to avoid exposed vias under its pad. `brief.md` §10 has the result: the RP2350's 1V1 ring stays whole, with 1 via in its pad and 8 in its 3V3 band.
2. **Blue and green headroom on a falling cell.** Full-white row, one driver: Vf ~2.8 V (p.6 at 12.7 mA) + SW 0.34 V + CS 0.35 V + path 0.16 V = **3.65 V typ**; top bin with max headroom **~4.2 V**. Most rows are far from all-on, so path drop and SW headroom shrink. Firmware lowers GCC as VBAT falls, which reduces both. Blue and green on bright rows will still dim over part of the discharge, more in a high bin; the request powers the SW lines from the battery, so no boost rail is planned. Worth measuring at bring-up.
3. **Mapping 13 × 9 blocks onto a circle.** Rows and columns of a circle are not 13 or 9 long, so the SW and CS groups cannot be plain straight rows and columns over the whole disc. Any LED can take any (CS triplet, SW) cell, so this is a free assignment; it is worked out in phase 4 for shortest, non-crossing nets.
4. **Stock.** 455 drivers and 12,489 LEDs are enough for the 5 boards under Manufacturing; re-check at release.
5. **USB-C through features in the LED field.** See Mechanical. Standard legs are wider than the 0.75 mm channel between LEDs, so each one displaces LED sites. `brief.md` §11: 5 lost, 3 of them visible as dark spots ~13.5 mm from the centre. Buttons cost 2 rim sites.
6. **Core inductor stock.** AOTA-B201610S3R3-101-T has 1 at JLC (2026-11-02). 5 boards need a pre-order or global sourcing before the order; `chips/rp2350.md` forbids substituting it.
