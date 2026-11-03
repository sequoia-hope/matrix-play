# Gate 0: design intent

Status: **passed**. User sign-off 2026-11-02, with two choices: through vias, 6 layers, via-in-pad; battery Grepow 5435035.

## Checklist (references/intent-and-brief.md, phase 0)

| Item | Where in intent.md | State |
|---|---|---|
| Purpose | Purpose | done |
| Open source or confidential | Open source, default | done, confirm |
| External interfaces | External interfaces table | done |
| Power: input, rails, sequencing, battery, backfeed | Power, R14–R20, R22 | battery open (R16) |
| Environment | Environment | done |
| Performance targets | R2, R6, R17–R19 | done |
| Mechanical | Mechanical | done, defaults to confirm |
| Manufacturing | Manufacturing | done, defaults to confirm |
| Serviceability | Serviceability, R9 | done |
| Compliance | Compliance | done |
| Known risks and open questions | Known risks | via type open (R13, risk 1) |

## Evidence

- `jlc_parts.py`, 2026-11-02:
  C965834 XL-1010RGB-YG: extended, JLC stock 12489, lifecycle normal.
  C2940604 IS31FL3741A-QFLS4-TR: extended, 455. C2678817 IS31FL3741-QFLS4-TR: extended, 0.
  C2940549 IS31FL3729-QFLS4-TR: extended, 2556, lifecycle normal. C42411118 RP2350A: extended, 4912.
- Site count on a 2 mm grid in 38 mm, land 1.25 mm, 0.35 mm from land to edge, by offset (0,0)/(1,1)/(1,0): 245/256/246.
  At 0.5 mm: 241/248/242.
- `scripts/doctor.sh`: all required tools ok; ngspice missing (phase 8).
- JLC HDI capabilities: https://jlcpcb.com/help/article/hdi-pcb-capabilities-faq (4–24 layers, laser 0.075–0.15 mm, default 0.1 mm).

## Independent review

Reviewer: Fable, fresh context, with intent.md, the checklist and the datasheets only. 2026-11-02. No BLOCKERs.

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | MAJOR | USB-powered case undefined: heat, 500 mA budget, VSYS limit | Fixed: R14, R19, Environment |
| 2 | MAJOR | Sleep budget assumes W25Q16JV, while R8 specifies 128 Mbit | Fixed: deep power-down required, check in phase 1 |
| 3 | MAJOR | Blind vias effectively mandatory | Put to the user, who chose through vias on 6 layers (decisions.md); risk 1 stays open for phase 4 |
| 4 | MAJOR | Escape channel at JLC minimum, unstated | Added R21; 3-track count disputed (decisions.md) |
| 5 | MINOR | Site range 241–256; frame time 6.7 ms | Fixed |
| 6 | MINOR | RP2350 VOL vs default driver VIL | Fixed: LGC = 1 in R6 |
| 7 | MINOR | VSYS typical missing; driver idle current | Fixed: rail table |
| 8 | MINOR | No VBAT sense, brightness, charge indication, LED-face ESD | Added R22, R23; R19; Environment |
| 9 | MINOR | Wake source count unstated | Fixed: R10 |
| 10 | NOTE | I2C pull-downs in sleep cost 40–65 µA each | Added to R17 |

Reviewer re-derived and confirmed: IOUT 12.67 mA, ILED 1.25 mA, full white 878 mA, peak 988 mA, addresses 0x30/0x33, headroom 0.46 V typ, IS31FL3729 45 RGB per chip.
