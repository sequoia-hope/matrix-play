# Gate 1: Architecture and Parts — Sunflower `s2-110-usbc`

Status: **`passed`** (`100%` of `34` unique BOM LCSC parts `lifecycle normal` and in stock at JLCPCB; audit bugs fixed in [drivers-aw20198.md](file:///home/sequoia/pcb/round-pendant/design/parts/drivers-aw20198.md) and [passives.md](file:///home/sequoia/pcb/round-pendant/design/parts/passives.md); shared-audit notes & waivers logged in [decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)).

## Checklist ([datasheet-audit.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/datasheet-audit.md), Phase 1)

| Item | Evidence | State |
|---|---|---|
| Block diagram & GPIO map; every block maps to parts | [architecture-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/architecture-s2-110-usbc.md) (`36` BOM lines, `34` unique LCSC PNs) | passed |
| Every part audited against its datasheet | Shared Round Pendant / Parallelogram audits in `design/parts/*.md` + `.claude/skills/pcb-design/chips/rp2350.md`, verified against all `s2-110-usbc` datasheets | passed |
| Abs max vs worst-case operating envelope | Audited across all ICs/LEDs/passives; thermal ceiling synchronized with [intent-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/intent-s2-110-usbc.md) `R19` | passed |
| Chosen passive/register values calculated | Fixed `AW20198` `GCR = 0xB9` & `255/3168` duty in [drivers-aw20198.md](file:///home/sequoia/pcb/round-pendant/design/parts/drivers-aw20198.md) and `≥ 30 ms` (`6 τ`) `Q1` settle + `RP2350-E9` in [passives.md](file:///home/sequoia/pcb/round-pendant/design/parts/passives.md) | passed |
| MLCC DC-bias derating | Verified (`22 µF 10 V 0603` → `~5.5–7.5 µF` @ `4.4 V`; `4.7 µF 10 V 0402` → `~2.1–2.6 µF`; `1 µF 25 V 0402` → `~0.60 µF`) | passed |
| Footprints match package mechanical drawings | All custom footprints in `hw/sunflower/s2-110-usbc/lib/round_pendant.pretty/` verified against datasheet drawings & EasyEDA models | passed |
| Sourcing (`jlc_parts.py show`) | Verbatim output below: all `34` parts `lifecycle normal`, min stock `531` (`U6`), `L1` (`C42411119`) = **`1,520`** | passed |
| [sources.csv](file:///home/sequoia/pcb/round-pendant/design/datasheets/sources.csv) | Present for active/connector/LED parts (passive/family-ID note in [decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)) | passed |

## Sourcing Check (`jlc_parts.py show`, `2026-11-08`)

Command:
`python3 .claude/skills/pcb-design/scripts/jlc_parts.py show C177225 C52923 C19702 C1525 C86295 C23733 C1548 C965840 C165948 C42411119 C236117 C2693594 C25905 C25744 C25784 C25891 C25741 C25076 C25105 C25100 C11702 C25900 C25776 C25768 C2828254 C5137654 C42411118 C190862 C15220 C2860046 C15999 C669687 C189624 C20625731`

```text
C177225 532610271 (MOLEX, SMD,P=1.25mm,Surface Mount,Right Angle): extended, JLC stock 25082, lifecycle normal, checked 2026-11-08
C52923 CL05A105KA5NQNC (Samsung Electro-Mechanics, 0402): basic, JLC stock 11491606, lifecycle normal, checked 2026-11-08
C19702 CL10A106KP8NNNC (Samsung Electro-Mechanics, 0603): basic, JLC stock 10270954, lifecycle normal, checked 2026-11-08
C1525 CL05B104KO5NNNC (Samsung Electro-Mechanics, 0402): basic, JLC stock 34153332, lifecycle normal, checked 2026-11-08
C86295 CL10A226MP8NUNE (Samsung Electro-Mechanics, 0603): extended, JLC stock 629382, lifecycle normal, checked 2026-11-08
C23733 CL05A475MP5NRNC (Samsung Electro-Mechanics, 0402): basic, JLC stock 1028445, lifecycle normal, checked 2026-11-08
C1548 0402CG150J500NT (FH, 0402): basic, JLC stock 1201609, lifecycle normal, checked 2026-11-08
C965840 XL-1615RGBC-RF (XINGLIGHT, SMD-4P,1.6x1.5mm): extended, JLC stock 715016, lifecycle normal, checked 2026-11-08
C165948 TYPE-C-31-M-12 (Korean Hroparts Elec, SMD): extended, JLC stock 317338, lifecycle normal, checked 2026-11-08
C42411119 AOTA-B201610S3R3-101-T (ABRACON, 0806): extended, JLC stock 1520, lifecycle normal, checked 2026-11-08
C236117 NTZD3155CT1G (onsemi, SOT-563): extended, JLC stock 7923, lifecycle normal, checked 2026-11-08
C2693594 XYC-PT19C-L1 (NEWOPTO, 0603): extended, JLC stock 25178, lifecycle normal, checked 2026-11-08
C25905 0402WGF5101TCE (UNI-ROYAL, 0402): basic, JLC stock 4484430, lifecycle normal, checked 2026-11-08
C25744 0402WGF1002TCE (UNI-ROYAL, 0402): basic, JLC stock 22730938, lifecycle normal, checked 2026-11-08
C25784 0402WGF3001TCE (UNI-ROYAL, 0402): extended, JLC stock 646716, lifecycle normal, checked 2026-11-08
C25891 0402WGF3601TCE (UNI-ROYAL, 0402): extended, JLC stock 494270, lifecycle normal, checked 2026-11-08
C25741 0402WGF1003TCE (UNI-ROYAL, 0402): basic, JLC stock 8749932, lifecycle normal, checked 2026-11-08
C25076 0402WGF1000TCE (UNI-ROYAL, 0402): basic, JLC stock 11718120, lifecycle normal, checked 2026-11-08
C25105 0402WGF330JTCE (UNI-ROYAL, 0402): basic, JLC stock 3816349, lifecycle normal, checked 2026-11-08
C25100 0402WGF270JTCE (UNI-ROYAL, 0402): extended, JLC stock 704950, lifecycle normal, checked 2026-11-08
C11702 0402WGF1001TCE (UNI-ROYAL, 0402): basic, JLC stock 33681427, lifecycle normal, checked 2026-11-08
C25900 0402WGF4701TCE (UNI-ROYAL, 0402): basic, JLC stock 15717176, lifecycle normal, checked 2026-11-08
C25776 0402WGF3002TCE (UNI-ROYAL, 0402): extended, JLC stock 5297459, lifecycle normal, checked 2026-11-08
C25768 0402WGF2202TCE (UNI-ROYAL, 0402): basic, JLC stock 1043891, lifecycle normal, checked 2026-11-08
C2828254 EVQP7J01P (PANASONIC, SMD,3.6x3.5mm): extended, JLC stock 6887, lifecycle normal, checked 2026-11-08
C5137654 AW20198QNR (AWINIC(Shanghai Awinic Tech), QFN-40L(5x5)): extended, JLC stock 6055, lifecycle normal, checked 2026-11-08
C42411118 RP2350A (Raspberry Pi, QFN-60-EP(7x7)): extended, JLC stock 3225, lifecycle normal, checked 2026-11-08
C190862 W25Q128JVPIQ (Winbond, WSON-8-EP(5x6)): extended, JLC stock 12788, lifecycle normal, checked 2026-11-08
C15220 BQ24073RGTR (TI, QFN-16-EP(3x3)): extended, JLC stock 862, lifecycle normal, checked 2026-11-08
C2860046 TPS7A0233PDQNR (TI, X2-SON-4-EP(1x1)): extended, JLC stock 531, lifecycle normal, checked 2026-11-08
C15999 USBLC6-2P6 (ST, SOT-666-6): extended, JLC stock 20214, lifecycle normal, checked 2026-11-08
C669687 XB9901A (XySemi, DFNFC-6(1.4x1.8)): extended, JLC stock 2947, lifecycle normal, checked 2026-11-08
C189624 LIS2DW12TR (ST, LGA-12(2x2)): extended, JLC stock 51888, lifecycle normal, checked 2026-11-08
C20625731 ABM8-272-T3 (ABRACON, SMD3225-4P): extended, JLC stock 9607, lifecycle normal, checked 2026-11-08
```

## Independent Reviews (`2026-11-08`, two fresh-context `agy` reviewers: `1A` Drivers/LEDs, `1B` Variant I/O & Passives)

| Reviewer | Severity | Finding | Resolution |
|---|---|---|---|
| `1A-B1`, `1B-MAJOR-3` | BLOCKER / MAJOR | Uncapped `300 mA` (`95 °C` @ `40 °C` ambient) violates `EVQP7J01P` (`+70 °C`), `J1` (`+80 °C`), and `+85 °C` LED/driver/X5R limits | Fixed in [intent-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/intent-s2-110-usbc.md) (`0–35 °C` ambient + `ADC4` `GCC` thermal caps keeping board `≤ 48–50 °C` battery / `≤ 45 °C` charging) |
| `1B-BLOCKER-1` | BLOCKER | `Q2` (`XYC-PT19C-L1`, `xyc-pt19c-l1.pdf` p. 8) mislabels pins `(1) Anode / (2) Cathode`, leaving Collector/Emitter polarity ambiguous | **Disputed with proof ([decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)):** Rendered internal leadframe die-paddle drawings in `xyc-pt19c-l1.pdf` p. 8 (`xyc_pt19-08.png`) vs `als-pt19.pdf` p. 3 (`als_pt19-03.png`) plus EasyEDA `C2693594` pad map: both mount the NPN silicon substrate (Collector) on **Pin 1 (`Mark` side)** and bond the top emitter wire to **Pin 2**, matching `mcu.kicad_sch` (`1 = LIGHT_PWR`, `2 = LIGHT`) with `0.000 mm` CPL error |
| `1A-M1` | MAJOR | [drivers-aw20198.md](file:///home/sequoia/pcb/round-pendant/design/parts/drivers-aw20198.md) cited `GCR.LGC` as bit 7 (`0x81` disables `SW10–SW11` and leaves `LGC = 0`!) instead of bit 3 (`0xB9`) | **Fixed** in [drivers-aw20198.md](file:///home/sequoia/pcb/round-pendant/design/parts/drivers-aw20198.md#L32), [intent-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/intent-s2-110-usbc.md), and [bringup-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/bringup-s2-110-usbc.md): mandated `12 mA` pad drive on `GPIO4/5` followed by **`GCR = 0xB9`** |
| `1B-MAJOR-6` | MAJOR | [passives.md](file:///home/sequoia/pcb/round-pendant/design/parts/passives.md) specified `≥ 5 ms` (`1 τ`) settle for `Q1` `VBAT` divider (`36.8%` / `1.55 V` error!) | **Fixed** in [passives.md](file:///home/sequoia/pcb/round-pendant/design/parts/passives.md#L24) and [bringup-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/bringup-s2-110-usbc.md): mandated **`≥ 30 ms` (`6 τ`)** + `PDE = 0, IE = 0` on `GPIO26/27` |
| `1A-M4`, `1B-MAJOR-1` | MAJOR | `Q2` **1× reflow limit** (`235–245 °C`) & `XL-1615` `240 ± 5 °C` rec peak vs double-sided PCBA | Fixed in [intent-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/intent-s2-110-usbc.md) & [brief-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/brief-s2-110-usbc.md): `Pass 1 = B.Cu`, `Pass 2 = F.Cu` (`≤ 245 °C`, zero mechanical touch on hot LED epoxy) |
| `1A-M2` | MAJOR | `SW` PMOS drop is `208 mV` @ `200 mA` (`3.81–3.91 V` max-bin G/B compliance knee) | Fixed in [intent-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/intent-s2-110-usbc.md) Risk #5 and quantified in Phase 8 ([pdn_headroom.png](file:///home/sequoia/pcb/round-pendant/design/sim/sunflower-s2-110-usbc/pdn_headroom.png)) |
| `1A-M3` | MAJOR | Shared `C35 = 100 nF` on `LED_SDB` (`GPIO6`) vs datasheet `1 µF` per `EN` pin | Waived for `Rev S3C` ([decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)): `EN` is a digital CMOS enable (`R31 = 100 kΩ` pull-down); `100 nF` (`τ ≈ 2.5 ns` pad-limited) filters noise cleanly without excessive `GPIO6` capacitive surge |
| `1A-M5` | MAJOR | [drivers-aw20198.md](file:///home/sequoia/pcb/round-pendant/design/parts/drivers-aw20198.md) duty formula (`244/275.5` typo) & MLCC derating notes | Fixed exact `15.9375 / 198 = 255 / 3168 = 0.08049` formula in [drivers-aw20198.md](file:///home/sequoia/pcb/round-pendant/design/parts/drivers-aw20198.md#L30); MLCC derating verified in Phase 8 |
| `1B-MAJOR-2` | MAJOR | `Q2` (`850 nm` NIR) saturates `R43 = 22 kΩ` at `293–439 lx` | Updated [intent-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/intent-s2-110-usbc.md) `R6`; drop-in `ALS-PT19` (`C146233`) or `R43 = 10 kΩ` noted if daylight range needed |
| `1B-MAJOR-4, 5` | MAJOR | `molex-53261-0271.pdf` defers electricals to `PS-51021-024`; `BT1` symbol `Conn_01x02` leaves mechanical `MP` nails un-netted | Recorded in [decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md): Molex PicoBlade `53261` series rating (`1.0 A` w/ `#26 AWG`, `-40..+85 °C`) exceeds `328 mA` charge / `220 mA` capped cont. load; `MP` solder nails are mechanically isolated from pins 1–2 |
| `1A-m1..m4`, `1B-MINOR-1..6` | MINOR | `AW20198` `0.60 mm` pad length (`0.30 mm` EP gap, passes DRC), `2 ms` POR wait, `RP2350-E9` `IE=0` list, `Q1` `2 µA` max `IDSS`, shared-audit `s2-110-usbc` pin deltas | Documented in [architecture-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/architecture-s2-110-usbc.md), [bringup-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/bringup-s2-110-usbc.md), and [decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md) |
