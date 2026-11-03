# Gate 1: architecture and parts

Status: **passed, with one sourcing item open for the user before ordering**.

## Checklist

| Item | State |
|---|---|
| Block diagram, every block maps to parts | `architecture.md` |
| Every part has an audit with its datasheet | `parts/`; RP2350 values inherited from easy2350's reviewed audit, deltas read and independently checked. Battery has no maker's datasheet: listings only, charge limit chosen to be safe either way |
| Abs max vs worst case | in each audit |
| Chosen values calculated | in each audit, corrected by review |
| MLCC derating | 22 µF, 1 µF, passives |
| Footprints match the package | drawings read by reviewer; project footprints drawn at phase 2 |
| Sourcing `jlc_parts.py show` | below; inductor fails |
| `datasheets/sources.csv` | yes |
| Independent review | three Fable reviewers, 2026-11-02 |

## Sourcing, `jlc_parts.py show`, 2026-11-02
All `lifecycle normal`. U1/U2 C2940604 455; U3 C42411118 4738; U4 C190862 8662; Y1 C20625731 9181; U5 C15220 8360; U6 C2860046 1914; U8 C669687 2947; U9 C189624 45643; J1 C165948 177286; LEDs C965834 12489.
**L1 C42411119: 1. Needs 5.** `chips/rp2350.md` forbids substitution and says to pre-order the MPN or use global sourcing: user action before ordering.

## Review findings

| Sev | Finding | Resolution |
|---|---|---|
| BLOCKER | ADC is ratiometric to 3V3, so VBAT sense can't see low-cell thresholds in LDO dropout; 2.2 MΩ divider has up to 1.1 V error from GPIO leakage | Fixed: switched 100 kΩ divider with Q1; firmware thresholds at ≥ 3.5 V (R22) |
| MAJOR | 3V3 in dropout violates VREG_AVDD and USB_OTP_VDD min 3.135 V | Fixed: firmware stop at 3.5 V |
| MAJOR | Latched pull-downs on all pulled-up GPIOs | Fixed: R17, rp2350-core.md |
| MAJOR | Flash deep power-down not released by bootrom | Budget doesn't rely on it |
| MAJOR | XB9901A R1 missing; EP is cell−, not GND | Fixed: protection.md, net BAT_N |
| MAJOR | LGC startup write at VIL 0.4 V | Recorded: 12 mA drive, measure at bring-up |
| MAJOR | Headroom optimistic, inconsistent | Fixed: 3.65 V typ, ~4.2 V worst, firmware GCC |
| MINOR | Channel 0.325 mm: no via fits; flash §10.3 | Fixed: risk 1, flash.md |
| MINOR | ILIM mandatory, values; term, precharge; dissipation formula | Fixed: charger.md |
| MINOR | LDO dropout and ground current | Fixed: ldo.md |
| MINOR | EN1 flat-cell start | Documented, bench check |
| MINOR | Bulk derating; red-only 0.38 W; θJA board size | Fixed: 10 V caps, intent |
| MINOR | USBLC6 VBR 6 V | Accepted, usb.md |
| MINOR | LIS2DW12 decoupling, current at 3.3 V | Fixed: accel.md, 2 µA budget |
| MINOR | BOOTSEL path with soldered cell | Fixed: rp2350-core.md |
| MINOR | LED reflow 255 °C peak, 240 °C recommended | Note for the order at phase 10 |
| MINOR | LED 180° rotation invisible on placement | CPL check at phase 10 |
| NOTE | Body-diode charge below 2.4 V; XB note 3; 20 mV VCU margin | protection.md |

Reviewers verified: 12.67 mA, 1.25 mA, 875–878 mA, 494 mA; addresses 0x30, 0x33, 0x19; GPIO mux; Table 1445 sum; crystal caps; footprints.

Unresolved independent review: Q1 was added after the reviews. Its role is low risk; checked again in the schematic review at gate 2.
