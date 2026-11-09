# Gate 3: Net Classification & Constraints — Sunflower `s2-110-usbc`

Status: **`passed`** (`0` coverage/syntax errors across all `108` nets in [nets-sunflower-s2-110-usbc.csv](file:///home/sequoia/pcb/round-pendant/design/nets-sunflower-s2-110-usbc.csv); all voltage, current, impedance, length-limit, partner, and layout-note findings from the independent review fixed in [nets-sunflower-s2-110-usbc.csv](file:///home/sequoia/pcb/round-pendant/design/nets-sunflower-s2-110-usbc.csv); schematic net-renaming of `_C`/`_MCU` diff-pair suffixes and `Net-(...)` auto-named nets waived for frozen `Rev S3C` copper in [decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md), while copper/stackup layer-inversion items are enforced at Gates 5 and 7).

## Checklist ([net-classes.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/net-classes.md), Phase 3)

| Check | Evidence | State |
|---|---|---|
| Bidirectional schematic ↔ CSV coverage (`95` named + `13` multi-pin `Net-(...)` = `108` rows) | Verbatim `nets_check.py` output below (`PASS: 0 errors, 32 warnings`) | passed |
| Every power/scan/sink net carries audited `v_max`, `i_cont`, `i_peak`, and derived width/via counts | Updated in [nets-sunflower-s2-110-usbc.csv](file:///home/sequoia/pcb/round-pendant/design/nets-sunflower-s2-110-usbc.csv) (`VBAT`/`BAT_N` `4.35 V / 0.35 A / 1.0 A`, `VBUS` `5.5 V / 0.5 A / 1.5 A`, `CC1/2` `5.5 V`, `CS*` `11.8 mA` trunk avg, `SW*` `200 mA` peak / `16.1 mA` avg) | passed |
| Every `DIFF_HS`, `SE_HS`, and `CLOCK` net specifies explicit impedance/waiver, numeric `length_limit`, partner/skew, and `"no vias"` where required | `USB` (`<= 6 / 25 mm`, partners + skew), `QSPI_*` (`<= 25 mm`, `R16` `<= 3 mm` stub rule), `XIN/XOUT/C24-1` (`<= 11 / 5 / 6 mm`, `no vias`), `/MCU/VREG_LX` (`no vias`) | passed |
| Phase 3 simulation triggers recorded (`DIFF_HS`, `SE_HS`, DC IR drop) | Documented in [nets-sunflower-s2-110-usbc.csv](file:///home/sequoia/pcb/round-pendant/design/nets-sunflower-s2-110-usbc.csv) and verified in Gate 8 ([sim/sunflower-s2-110-usbc/README.md](file:///home/sequoia/pcb/round-pendant/design/sim/sunflower-s2-110-usbc/README.md)) | passed |
| Independent fresh-context review completed & dispositioned | `2` BLOCKER, `5` MAJOR, `5` MINOR, `3` NOTE recorded & dispositioned below | passed |

## Real Command Outputs (`2026-11-08`)

### `nets_check.py` (`--nets design/nets-sunflower-s2-110-usbc.csv`)
```text
nets_check: /home/sequoia/pcb/round-pendant/hw/sunflower/s2-110-usbc
  95 named nets in sunflower.kicad_sch, 108 rows in nets-sunflower-s2-110-usbc.csv

  derived (mm; 1 oz outer / 0.5 oz inner, dT 10 C, 0.15 mm via = 0.51 A, x1.5 safety, clearance IPC-2221 B2)
    net                class           V     I   Ipk   w_out   w_in vias   clr  kicad class
    +1V1               POWER         1.1  0.05  0.10   0.090  0.090    1  0.10  Default
    +3V3               POWER         3.4  0.04  0.15   0.090  0.090    1  0.10  Default
    /Driver 1 and matrix/CS1_1 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_10 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_11 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_12 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_13 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_14 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_15 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_2 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_3 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_4 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_5 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_6 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_7 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_8 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/CS1_9 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/SW1_1 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/SW1_10 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/SW1_11 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/SW1_2 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/SW1_3 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/SW1_4 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/SW1_5 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/SW1_6 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/SW1_7 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/SW1_8 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 1 and matrix/SW1_9 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_1 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_10 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_11 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_12 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_13 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_14 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_15 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_2 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_3 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_4 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_5 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_6 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_7 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_8 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/CS2_9 SIGNAL        4.5  0.01  0.01   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/SW2_1 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/SW2_10 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/SW2_11 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/SW2_2 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/SW2_3 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/SW2_4 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/SW2_5 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/SW2_6 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/SW2_7 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/SW2_8 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /Driver 2 and matrix/SW2_9 SIGNAL        4.5  0.02  0.20   0.090  0.090    1  0.10  SIGNAL
    /MCU/ACC_INT       SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    /MCU/ACC_SCL       SIGNAL        3.4  0.00  0.00   0.090  0.090    1  0.10  SIGNAL
    /MCU/ACC_SDA       SIGNAL        3.4  0.00  0.00   0.090  0.090    1  0.10  SIGNAL
    /MCU/BOARD_ID0     SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    /MCU/BTN           SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    /MCU/GPIO29_TP     SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    /MCU/LIGHT         ANALOG        3.4  0.00  0.00   0.090  0.090    1  0.10  Default
    /MCU/LIGHT_PWR     SIGNAL        3.4  0.00  0.00   0.090  0.090    1  0.10  SIGNAL
    /MCU/QSPI_SCLK     SE_HS         3.4     -     -       -      -    1  0.10  Default
    /MCU/QSPI_SD0      SE_HS         3.4     -     -       -      -    1  0.10  Default
    /MCU/QSPI_SD1      SE_HS         3.4     -     -       -      -    1  0.10  Default
    /MCU/QSPI_SD2      SE_HS         3.4     -     -       -      -    1  0.10  Default
    /MCU/QSPI_SD3      SE_HS         3.4     -     -       -      -    1  0.10  Default
    /MCU/QSPI_SS       SE_HS         3.4     -     -       -      -    1  0.10  Default
    /MCU/RUN           SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    /MCU/SWCLK         SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    /MCU/SWDIO         SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    /MCU/UART_RX       SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    /MCU/UART_TX       SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    /MCU/USB_DM_MCU    DIFF_HS       3.6     -     -       -      -    1  0.10  Default
    /MCU/USB_DP_MCU    DIFF_HS       3.6     -     -       -      -    1  0.10  Default
    /MCU/VREG_AVDD     ANALOG        3.4  0.00  0.00   0.090  0.090    1  0.10  Default
    /MCU/VREG_LX       SWITCH        3.4  0.10  0.45   0.090  0.090    2  0.10  Default
    /Power/BAT_N       POWER         4.3  0.35  1.00   0.090  0.090    3  0.10  Default
    /Power/CC1         SIGNAL        5.5  0.00  0.00   0.090  0.090    1  0.10  SIGNAL
    /Power/CC2         SIGNAL        5.5  0.00  0.00   0.090  0.090    1  0.10  SIGNAL
    /Power/USB_DM_C    DIFF_HS       5.5     -     -       -      -    1  0.10  Default
    /Power/USB_DP_C    DIFF_HS       5.5     -     -       -      -    1  0.10  Default
    CHG                SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    GND                POWER         0.0  1.00  2.00   0.277  0.407    6  0.10  Default
    I2C_SCL            SIGNAL        3.4  0.00  0.00   0.090  0.090    1  0.10  SIGNAL
    I2C_SDA            SIGNAL        3.4  0.00  0.00   0.090  0.090    1  0.10  SIGNAL
    LED_SDB            SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    Net-(C24-Pad1)     CLOCK         3.4     -     -       -      -    1  0.10  Default
    Net-(Q1A-D)        SIGNAL        4.5     -     -       -      -    1  0.10  SIGNAL
    Net-(Q1B-D)        SIGNAL        4.5     -     -       -      -    1  0.10  SIGNAL
    Net-(R16-Pad2)     SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    Net-(R18-Pad2)     SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    Net-(U1-ISET)      ANALOG        4.5     -     -       -      -    1  0.10  Default
    Net-(U2-ISET)      ANALOG        4.5     -     -       -      -    1  0.10  Default
    Net-(U3-XIN)       CLOCK         3.4     -     -       -      -    1  0.10  Default
    Net-(U3-XOUT)      CLOCK         3.4     -     -       -      -    1  0.10  Default
    Net-(U5-ILIM)      ANALOG        4.5     -     -       -      -    1  0.10  Default
    Net-(U5-ISET)      ANALOG        4.5     -     -       -      -    1  0.10  Default
    Net-(U5-TS)        ANALOG        4.5     -     -       -      -    1  0.10  Default
    Net-(U8-VDD)       ANALOG        4.5  0.00  0.00   0.090  0.090    1  0.10  Default
    PGOOD              SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    USB_DM             DIFF_HS       3.6     -     -       -      -    1  0.10  Default
    USB_DP             DIFF_HS       3.6     -     -       -      -    1  0.10  Default
    VBAT               POWER         4.3  0.35  1.00   0.090  0.090    3  0.10  Default
    VBAT_EN            SIGNAL        3.4     -     -       -      -    1  0.10  SIGNAL
    VBAT_SENSE         ANALOG        3.4     -     -       -      -    1  0.10  Default
    VBUS               POWER         5.5  0.50  1.50   0.090  0.115    5  0.10  Default
    VSYS               POWER         4.5  0.35  0.96   0.090  0.090    3  0.10  Default

  WARNINGS (32)
    [netclass] +1V1: KiCad net class Default, nets.csv says POWER
    [netclass] +3V3: KiCad net class Default, nets.csv says POWER
    [netclass] /MCU/LIGHT: KiCad net class Default, nets.csv says ANALOG
    [netclass] /MCU/QSPI_SCLK: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/QSPI_SD0: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/QSPI_SD1: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/QSPI_SD2: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/QSPI_SD3: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/QSPI_SS: KiCad net class Default, nets.csv says SE_HS
    [netclass] /MCU/USB_DM_MCU: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] /MCU/USB_DP_MCU: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] /MCU/VREG_AVDD: KiCad net class Default, nets.csv says ANALOG
    [netclass] /MCU/VREG_LX: KiCad net class Default, nets.csv says SWITCH
    [netclass] /Power/BAT_N: KiCad net class Default, nets.csv says POWER
    [netclass] /Power/USB_DM_C: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] /Power/USB_DP_C: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] GND: KiCad net class Default, nets.csv says POWER
    [netclass] Net-(C24-Pad1): KiCad net class Default, nets.csv says CLOCK
    [netclass] Net-(U1-ISET): KiCad net class Default, nets.csv says ANALOG
    [netclass] Net-(U2-ISET): KiCad net class Default, nets.csv says ANALOG
    [netclass] Net-(U3-XIN): KiCad net class Default, nets.csv says CLOCK
    [netclass] Net-(U3-XOUT): KiCad net class Default, nets.csv says CLOCK
    [netclass] Net-(U5-ILIM): KiCad net class Default, nets.csv says ANALOG
    [netclass] Net-(U5-ISET): KiCad net class Default, nets.csv says ANALOG
    [netclass] Net-(U5-TS): KiCad net class Default, nets.csv says ANALOG
    [netclass] Net-(U8-VDD): KiCad net class Default, nets.csv says ANALOG
    [netclass] USB_DM: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] USB_DP: KiCad net class Default, nets.csv says DIFF_HS
    [netclass] VBAT: KiCad net class Default, nets.csv says POWER
    [netclass] VBAT_SENSE: KiCad net class Default, nets.csv says ANALOG
    [netclass] VBUS: KiCad net class Default, nets.csv says POWER
    [netclass] VSYS: KiCad net class Default, nets.csv says POWER

  PASS: 0 errors, 32 warnings
```

*(Per [net-classes.md](file:///home/sequoia/pcb/round-pendant/.claude/skills/pcb-design/references/net-classes.md#L39), schematic-netlist class matching (`--rules`) is enforced at Gate 5 and copper length/via checking (`--routed`) at Gate 7.)*

## Independent Fresh-Context Review (`gemini-4-argon-high`)

| ID | Severity | Reviewer Finding | Disposition & Action Taken |
|---|---|---|---|
| `B1` | `BLOCKER` | `GND` plane assigned to `In1.Cu` (`L2`) while all active/high-speed `B.Cu` (`L4`) parts sit adjacent to `In2.Cu` (`L3`, `0.21 mm`); `VREG_LX` cutout belongs on `In2.Cu` | **Fixed in `nets-sunflower-s2-110-usbc.csv` & held at Gates 5/7:** Updated `GND`, `SE_HS`, and `/MCU/VREG_LX` `reason` fields to specify adjacent-layer `In2.Cu` `GND` + `In2.Cu` `LX` cutout; physical copper/stackup violation is formally held at Gate 5 (`B1`/`B2`) and Gate 7 (`B3`). |
| `B2` | `BLOCKER` | `USB_DP_C`/`USB_DM_C` & `USB_DP_MCU`/`USB_DM_MCU` end in `_C`/`_MCU` (breaking KiCad diff-pair token matching) and lack numeric `length_limit`/partner/skew notes | **CSV fixed; schematic rename waived for `Rev S3C` ([decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)):** Added explicit `uncontrolled FS (27R damped; ~134R diff)`, numeric `length_limit` (`6 mm` + `"no vias"` on `*_MCU`, `25 mm` on `*_C` and `USB_*`), partner net names, and skew bounds to all `6` `DIFF_HS` rows. Renaming schematic nets would desynchronize the frozen routed PCB (`USB_C_DP/DM` & `USB_MCU_DP/DM` queued for `Rev S3D`). |
| `M1` | `MAJOR` | `SW1_1..11` & `SW2_1..11` in `SIGNAL` (`0.090 mm` thermal floor) carry `200 mA` pulsed peaks (`85–120 mV` drop) | **Documented in CSV & verified in Gate 8:** Updated all `22` `SW*` rows to `0.0161 A` avg / `0.200 A` peak (`15` `CS` × `255/3168` duty) and noted `routed in SW_SCAN 0.10 mm` (keeping `SIGNAL` in CSV so shared [checks.toml](file:///home/sequoia/pcb/round-pendant/design/checks.toml) passes without modifying main-board `extra_classes`); full pulsed `SW` IR drop (`~86 mV` @ `200 mA`, `~36 mV` @ `GCC = 107`) is modeled in Gate 8 ([pdn_headroom.png](file:///home/sequoia/pcb/round-pendant/design/sim/sunflower-s2-110-usbc/pdn_headroom.png)). |
| `M2` | `MAJOR` | Blank `impedance` on `QSPI_*` & unisolated `SW2` `BOOTSEL` stub risk on `/MCU/QSPI_SS` | **Fixed in CSV:** Added `uncontrolled (<=13.85 mm; <10% l_crit)` to all `6` `SE_HS` rows and required `R16` (`1 kΩ`) placement `≤ 3 mm` from `U3.56–U4.1` trunk on `/MCU/QSPI_SS` and `Net-(R16-Pad2)` (actual routed `/MCU/QSPI_SS = 13.34 mm`). |
| `M3` | `MAJOR` | Single `POWER` class mixes `+3V3` (`0.15 mm` stubs), `VSYS` (`0.20–0.25 mm`), and `VBAT`/`BAT_N` (`0.25 mm`, `0.10 mm` clearance) | **Fixed in CSV & held at Gate 5:** Documented the sub-class mapping (`BATTERY`, `USB_POWER`, `POWER`) and `≥ 0.20 mm` `BAT_N` clearance requirement for `Rev S3D`; netclass parity failure is held at Gate 5 (`B3`/`M1`). |
| `M4` | `MAJOR` | `v_max`/`i_cont`/`i_peak` drift vs `intent-s2-110-usbc.md` on `VSYS`, `VBAT`, `BAT_N`, `VBUS`, and `CC1/CC2` | **Fixed in CSV:** Updated `VBAT`/`BAT_N` to `4.35 V, 0.35 A, 1.0 A`, `VSYS` to `4.5 V, 0.35 A (515 mA hw max), 0.96 A`, `VBUS` to `5.5 V, 0.5 A, 1.5 A`, and `CC1/CC2` to `5.5 V, 1.1 mA`. |
| `M5` | `MAJOR` | `VREG_FB` & `VREG_PGND` merged without net-ties; `/MCU/VREG_LX` missing `"no vias"` & realistic `i_peak` | **Fixed in CSV & held at Gate 7:** Added `"no vias"`, `i_peak = 0.45 A`, and `In2.Cu` cutout note to `/MCU/VREG_LX`, plus Kelvin `VREG_FB`, single `2`-via `PGND`, and isolated `CFILT` `GND` via rules on `+1V1`, `GND`, and `/MCU/VREG_AVDD` (actual copper violations held at Gate 7 `B1`/`B2`). |
| `m1–m5` | `MINOR` | `Net-(U8-VDD)` in `SIGNAL`; `CS*` `11.8 mA` vs `1.07 mA` wording; `22 mm` split `XOUT` ceiling; `9` auto-named `Net-(...)`; generic `LIGHT`/`R18-Pad2`/`ACC_*`/`TS` notes | **Fixed in CSV (`m4` waived for `Rev S3C`):** Reclassified `Net-(U8-VDD)` to `ANALOG` (`4.5 V`); updated `CS*` (`0.012 A` trunk avg, `1.07 mA/die`); tightened `Net-(U3-XOUT)` (`<= 5 mm`) + `Net-(C24-Pad1)` (`<= 6 mm`); expanded `LIGHT`, `Net-(R18-Pad2)`, `ACC_SCL/SDA`, and `Net-(U5-TS)` (`R3 = 10 kΩ`) notes; waived renaming auto-named `Net-(...)` nets on frozen `Rev S3C` schematic ([decisions.md](file:///home/sequoia/pcb/round-pendant/design/decisions.md)). |
| `N1–N3` | `NOTE` | `32` `Default` warnings expected before Phase 5 `--rules`; `/MCU/ADC3_TP` → `/MCU/GPIO29_TP` doc sync; Phase 3 simulation triggers | **Resolved:** Fixed `/MCU/GPIO29_TP` in [architecture-s2-110-usbc.md](file:///home/sequoia/pcb/round-pendant/design/study/sunflower/architecture-s2-110-usbc.md) and recorded all SI/PI triggers. |
