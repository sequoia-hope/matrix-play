# Gate 0: Design Intent — Sunflower `s2-110-usbc`

Status: **`awaiting_signoff`** (Gate 0 requires explicit user sign-off per [SKILL.md](../../../.claude/skills/pcb-design/SKILL.md) and [intent-and-brief.md](../../../.claude/skills/pcb-design/references/intent-and-brief.md)).

## Checklist ([intent-and-brief.md](../../../.claude/skills/pcb-design/references/intent-and-brief.md), Phase 0)

| Item | Where in [intent-s2-110-usbc.md](../../study/sunflower/intent-s2-110-usbc.md) | State |
|---|---|---|
| Purpose | `Purpose` | done |
| Open source or confidential | `Open source or confidential` (`CERN-OHL-P-2.0`) | awaiting user sign-off on `B.SilkS` identity omission |
| Every external interface (`J1`, `BT1`, `SW1`, `SW2`, `Q2`, `TP*`) | `External interfaces` | done (updated after review) |
| Power: input, rails, sequencing, battery, backfeed | `Power`, `R14–R20`, `R22` | awaiting user sign-off on `403535` cell `0.58–0.82C` charge rate |
| Environment & thermal ceiling | `Environment`, `R19` | awaiting user sign-off on `ADC4` firmware `GCC` thermal caps |
| Performance targets | `Performance targets`, `R5`, `R7`, `R8`, `R17` | done (added after review) |
| Mechanical | `Mechanical`, `R1`, `R2`, `R10`, `R16` | awaiting user sign-off on `BT1` inward mating + `2.4 mm` spacer + `SW1/SW2` overhang |
| Manufacturing | `Manufacturing`, `R12`, `R13` | done (`Pass 1 = B.Cu`, `Pass 2 = F.Cu ≤ 245 °C` for `Q2` 1× reflow limit) |
| Serviceability | `Serviceability`, `R9` | done |
| Compliance | `Compliance` | done (`none formal`) |
| Known risks and open questions | `Known risks and open questions` | 4 items listed below for user sign-off |

## Tool & Environment Check (`./scripts/doctor.sh`, 2026-11-08)

```text
Required
  ok    kicad-cli 9.0.8
  ok    python 3.14.4
  ok    numpy
  ok    pcbview (26ba32b)
  ok    ultraroute (3de3d83)
  ok    cargo (builds ultraroute, the autorouter)
Recommended
  ok    KiCad python module (pcbnew)
  warn  ngspice
        needed for phase 8 simulations
```

## Independent Review (`2026-11-08`, fresh-context `agy` reviewer)

Reviewer inspected only [intent-s2-110-usbc.md](../../study/sunflower/intent-s2-110-usbc.md), [intent-and-brief.md](../../../.claude/skills/pcb-design/references/intent-and-brief.md), and `design/datasheets/*.pdf`. Independently re-derived and confirmed: `IOUT,max = 13.33 mA`, `11-SW duty = 0.08049` (`15.9375 / 198 = 255 / 3168`), `ILED,avg = 1.073 mA/die`, `full-white = 354.2 mA` LED typ (`357.8 mA` w/ `2× IACT_VCC`), `400.0 mA` combined scan-slot peak, `1 MHz` `I2C0` frame `3.63–3.84 ms` (`~22–23%` @ `60 fps`), `ICHG = 296.7 mA` (`263.0–328.3 mA`), and `~68–73 µA` de-duplicated typ sleep current.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| `BLOCKER-1` | BLOCKER | `300 mA` continuous full-white (`1.26 W`, `+55 K` rise → `80–95 °C`) violates `EVQP7J01P` (`+70 °C`), `J1` (`+80 °C`), `85 °C` LEDs/ICs, `45/60 °C` LiPo (with fixed `10 kΩ` `TS`), and wearable touch limits | Fixed in [intent-s2-110-usbc.md](../../study/sunflower/intent-s2-110-usbc.md) (`R19`, `Environment`) and [bringup-s2-110-usbc.md](../../study/sunflower/bringup-s2-110-usbc.md): enforced closed-loop `RP2350` `ADC4` cap (`GCC ≤ 105` pouch-backed battery `≤ 48 °C` skin, `GCC ≤ 9` CC / `≤ 24` CV gated on `PGOOD == 0 || CHG == 0` for `≤ 45 °C` LiPo) |
| `BLOCKER-2` | BLOCKER | `Q2` (`XYC-PT19C-L1`, `xyc-pt19c-l1.pdf` p. 11) forbids `> 1` reflow pass (`235–245 °C` peak), conflicting with unspecified double-sided PCBA order | Fixed in `R12` & `Manufacturing`: mandated **`Pass 1 = B.Cu`, `Pass 2 = F.Cu` (`≤ 245 °C`)** so `Q2` sees only 1 reflow pass |
| `BLOCKER-3` | BLOCKER | Misquoted `AW20198QNR` digital input abs max as `VCC + 0.3 V` (datasheet p. 6 is `-0.3 V to VCC`) and overstated fault power-down sequencing | Fixed in `Power — Sequencing`: corrected abs max to `-0.3 V to VCC` and documented `1 kΩ` `R21/R22` `≤ 3.3 mA` current limit under `VO(SC2)` collapse |
| `BLOCKER-4` | BLOCKER | Unresolved `(open — user sign-off)` items (`B.SilkS` identity omission, `BT1` inward mating + battery spacer, `403535` C-rating, pin deltas) | Held at `awaiting_signoff` and listed explicitly below for user decision |
| `MAJOR-1` | MAJOR | `Q2` (`XYC-PT19C-L1`, `850 nm` NIR) across `R43 = 22 kΩ` saturates at `293–313 lx` min / `439–470 lx` typ, failing claimed `1000 lx` linear range | Fixed in `R6` & `External interfaces`: updated linear range to `~5–293 lx` min / `~440 lx` typ (`850 nm` NIR; noted `ALS-PT19` or `R43 = 6.8–10 kΩ` option if `1000 lx` needed) |
| `MAJOR-2` | MAJOR | Missing `Performance targets` section; missing `VSYS` `561–585 mA` slot peak, `USB100` cold-start, `VIN-DPM`, `TP4` `1.21 V` max, and backfeed notes | Fixed: added `Performance targets` section and completed all `External interfaces`, `Power`, and `Environment` columns |
| `MAJOR-3` | MAJOR | `TPS7A0233` (`VDO ≤ 203 mV` @ `150 mA`) + `BQ24073` (`56 mV`) enters benign dropout (`~3.24 V`) near `VBAT = 3.50 V` peak load | Fixed in `R15` & `R22`: raised sleep cutoff to `3.55 V` and documented benign dropout margin above `RP2350` `3.135 V` min |
| `MAJOR-4` | MAJOR | Mechanical heights misquoted (`J1` is `3.26 ± 0.10 mm`, not `3.16 mm`; `BT1` is `3.20 +0.20/−0.05 mm` / `3.40 mm` mated; `Q2` is `0.80 ± 0.15 mm`) | Fixed in `Mechanical`: Front `≤ 0.95 mm`, Back `≤ 3.40 mm` |
| `MAJOR-5` | MAJOR | `BQ24073` mandatory `CE = GND`, `TD = GND` pins omitted in `R14`; `USBLC6-2P6` `> 6 V` non-compliant charger caveat noted | Fixed in `R14` and `External interfaces — J1` |
| `MAJOR-6` | MAJOR | `XB9901A` `IIOV1 = 9 A` typ protects against hard shorts only (`1.0 A` `BT1`) and enters power-down on first cell attach until USB is connected | Fixed in `R16` and documented wake procedure in [bringup-s2-110-usbc.md](../../study/sunflower/bringup-s2-110-usbc.md) §5.2 |
| `MINOR-1..6` | MINOR | `R18` duty formula constants (`255/3168`), `SW` drop (`208 mV` @ `200 mA`), `ICHG` `±1%` range (`263–328 mA`), `RP2350-E9` `IE=0` sleep guard, `12 mA` boot pad drive before `GCR=0xB9`, `R17 = 1 kΩ` crystal damping | Fixed across `R5`, `R7`, `R14`, `R17`, `R18`, and `Known risks #5` |
| `NOTE-1..3` | NOTE | `5.05 kHz` scan / `SSCR.SSE=1` spread-spectrum option, PCBA setup/feeder fee exclusion from `< $15` parts BOM target, `TPS7A0233` `±1.5%` accuracy | Recorded in `Performance targets`, `Manufacturing`, and `R15` |

## Decisions Required From User for Gate 0 Sign-Off

1. **`BT1` inward mating & rear `403535` stack (`~9.6 mm`):** Confirm accepting pre-mating the `1.25 mm` PicoBlade plug into `BT1` `(−11.40, −10.20 mm, −110°)` before bonding the `35 mm` LiPo over `0.05 mm` Kapton tape + a `≥ 2.4 mm` insulating foam/carrier standoff (to clear `3.26 mm` `J1` and `3.40 mm` mated `BT1`).
2. **`403535` cell fast-charge rate (`263–328 mA`):** Confirm the chosen `403535` pouch datasheet permits `~0.6–0.8C` (`297 mA` typ via `R4 = 3.0 kΩ`), or specify increasing `R4` to `4.7 kΩ` (`189 mA`).
3. **Active `ADC4` thermal caps & `SW1/SW2` rim projection:** Confirm firmware `ADC4` continuous brightness ceilings (`GCC ≤ 105` on pouch-backed battery for `≤ 48 °C`, `GCC ≤ 9` CC / `≤ 24` CV gated on `PGOOD == 0 || CHG == 0` for `≤ 45 °C` LiPo) and accept `EVQP7J01P` `+0.40 mm` nominal (`0.00 to −0.20 mm` worst-case tolerance) fingernail rim actuation.
4. **Back silkscreen identity omission & variant firmware deltas:** Confirm omitting board name/rev/URL on `B.SilkS` (tracked via `BOARD_ID = 6` strap `NT1` on `GPIO19`) and accept `s2-110-usbc` firmware deltas (`VBAT_EN` on `GPIO28`, `UART1` on `GPIO24/25`, `AW20198` `GCR = 0xB9`, `≥ 30 ms` `Q1` ADC settle, `Q2` `~293–440 lx` NIR indoor range).
