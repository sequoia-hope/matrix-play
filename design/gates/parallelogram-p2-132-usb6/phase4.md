# Gate 4: mechanical and layout brief (`parallelogram-p2-132-usb6`)

Status: **awaiting_signoff**

## Scope & Inherited Earlier Artifacts
`parallelogram-p2-132-usb6` (`hw/parallelogram/p2-132-usb6/`) diverges from its parent `parallelogram-p2-132-usb` (`hw/parallelogram/p2-132-usb/`) at Phase 4 by adding two peg-less side-actuated Panasonic `EVQP7J01P` (`C2828254`) tactile buttons (`SW5` North `USER_C`, `SW6` South `USER_D`) on one `62.0 mm` vertical long edge, wired active-low to `GND` with internal RP2350 pull-ups, `1 kΩ` series protection resistors (`R46`, `R47`), and `100 nF` debounce capacitors (`C71`, `C72`). Everything else on `p2-132-usb` — including `J1`'s slanted position `(-1.24, +26.82)` and rotation `162.2553°` (`usb_s = -2.45`, `usb_ye = 3.60`) — stays unchanged.

Earlier phases inherited from parent & verified for the delta:
- **Phase 0 (Intent):** `design/intent.md` & `design/study/parallelogram/README.md` §5 (parallelogram family divergences logged in `design/decisions.md`).
- **Phase 1 (Datasheets & Parts):** `design/parts/{rp2350-core.md,buttons.md,parallelogram-io.md,passives.md}` and `design/datasheets/evqp7j01p.pdf` (`EVQP7J01P`: `3.50 × 2.90 × 1.35 mm` SMD side-actuated without boss/pegs, `1.70 mm` knob, push travel `0.20 mm`, rating `10 µA 2 V DC to 50 mA 12 V DC`, max ON/OFF bounce `10 ms`).
- **Phase 2 (Schematic):** `hw/parallelogram/p2-132-usb6/parallelogram.kicad_sch` (`mcu.kicad_sch` adds `SW5`/`R46`/`C71` -> `/MCU/USER_C` on `U3.13` `GPIO9` and `SW6`/`R47`/`C72` -> `/MCU/USER_D` on `U3.2` `GPIO0`; `kicad-cli sch erc --severity-all` = `0` violations across all `5` sheets).
- **Phase 3 (Net classification):** `design/nets-parallelogram-p2-132-usb6.csv` (`118` rows: `114` parent rows + `/MCU/USER_C`, `/MCU/USER_D`, `Net-(R46-Pad2)`, `Net-(R47-Pad2)` in `SIGNAL` `3.4 V`, `0.10 mm` clearance).

## Checklist (`references/intent-and-brief.md` §Phase 4)
- Full mechanical & layout brief: `design/gates/parallelogram-p2-132-usb6/brief.md` (§1–§12: outline, mounting, connectors & edge choice, assembly sides, `1.6 mm` `JLC04161H-7628` 4L stackup lock, density, block floorplan, thermal, art, silkscreen policy, keepouts, test & debug).
- Dimensioned floorplan render (with true rotated polygons, `R = 1.00 mm` corner fillets, `2 × Ø 0.65 mm` `J1` NPTH holes, and `LiPo` envelopes): `design/renders/parallelogram-p2-132-usb6/floorplan.svg` and `design/renders/parallelogram-p2-132-usb6/floorplan.png`.
- Saved outline + connector/placed snapshot: `hw/parallelogram/p2-132-usb6/route/preroute_4L.kicad_pcb` (with companion `preroute_4L.kicad_pro`, `preroute_4L.kicad_dru`, `fp-lib-table`, `lib`).

## Measured Mechanical & Clearance Evidence (`pcbnew` on `preroute_4L.kicad_pcb`)
```text
SW5  pos=(-10.85,-22.00) rot= 90.00 crtyd_x=[-13.05, -9.31] crtyd_y=[-24.59,-19.41] copper_x=[-12.10, -9.60]
R46  pos=( -7.40,-21.00) rot=180.00 crtyd_x=[ -8.33, -6.47] crtyd_y=[-21.47,-20.53] copper_x=[ -8.18, -6.62]
C71  pos=( -7.40,-22.20) rot=180.00 crtyd_x=[ -8.31, -6.50] crtyd_y=[-22.66,-21.75] copper_x=[ -8.16, -6.64]
SW6  pos=(-10.85,+22.80) rot= 90.00 crtyd_x=[-13.05, -9.31] crtyd_y=[+20.20,+25.39] copper_x=[-12.10, -9.60]
R47  pos=( -7.40,+21.00) rot=180.00 crtyd_x=[ -8.33, -6.47] crtyd_y=[+20.53,+21.47] copper_x=[ -8.18, -6.62]
C72  pos=( -7.40,+19.80) rot=180.00 crtyd_x=[ -8.31, -6.50] crtyd_y=[+19.34,+20.25] copper_x=[ -8.16, -6.64]
SW1  pos=(+10.85, +1.50) rot=-90.00 crtyd_x=[ +9.31,+13.05] crtyd_y=[ -1.09, +4.09] copper_x=[ +9.60,+12.10]
SW2  pos=(-10.85, -3.50) rot= 90.00 crtyd_x=[-13.05, -9.31] crtyd_y=[ -6.09, -0.91] copper_x=[-12.10, -9.60]
SW3  pos=( -9.15,-28.65) rot= 90.00 crtyd_x=[-11.94, -6.36] crtyd_y=[-32.39,-24.91] copper_x=[-11.40, -6.90]
SW4  pos=( +9.15,+28.65) rot= 90.00 crtyd_x=[ +6.36,+11.94] crtyd_y=[+24.91,+32.40] copper_x=[ +6.90,+11.40]
J1   pos=( -1.24,+26.82) rot=162.26 crtyd_x=[ -8.22, +5.68] crtyd_y=[+22.10,+31.77] copper_x=[ -8.06, +5.41]
BT1  pos=( +8.40,+20.05) rot= 90.00 crtyd_x=[ +5.31,+12.09] crtyd_y=[+15.33,+24.78] copper_x=[ +6.40,+11.60]
U4   pos=( -3.65,+17.60) rot= 90.00 crtyd_x=[ -6.39, -0.91] crtyd_y=[+14.28,+20.92] copper_x=[ -5.81, -1.50]
Q1   pos=( +9.20, +7.60) rot=180.00 crtyd_x=[ +8.00,+10.39] crtyd_y=[ +6.66, +8.55] copper_x=[ +8.15,+10.25]
U8   pos=(+10.00,+12.60) rot=180.00 crtyd_x=[ +9.11,+10.89] crtyd_y=[+11.75,+13.44] copper_x=[ +9.35,+10.65]
--- True Rotated Polygon Courtyard Clearances ---
SW5 <-> SW3 : 0.310 mm (stroke-bbox +0.210 mm)
SW5 <-> SW2 : 13.310 mm
SW6 <-> J1  : 1.806 mm
SW6 <-> U4  : 2.910 mm
R46 <-> U1  : 3.680 mm
R47 <-> U4  : 0.080 mm
```

### Netlist Proof that `GPIO9` and `GPIO0` Are Spare (`kicad-cli sch export netlist`)
```text
NET /MCU/USER_C: [('C71', '1', ''), ('R46', '1', ''), ('U3', '13', 'GPIO9')]
NET /MCU/USER_D: [('C72', '1', ''), ('R47', '1', ''), ('U3', '2', 'GPIO0')]
NET Net-(R46-Pad2): [('R46', '2', ''), ('SW5', '1', '1')]
NET Net-(R47-Pad2): [('R47', '2', ''), ('SW6', '1', '1')]
```

## Independent Fresh-Context Review (`agy` `gemini-4-argon-high`) & Dispositions
Reviewer independently audited `brief.md`, `phase4.md`, `floorplan.png`, `evqp7j01p.pdf`, `mcu.kicad_sch`, and `preroute_4L.kicad_pcb`, confirming `0` courtyard polygon overlaps, `0.400 mm` copper-to-edge clearance, `100%` (`118/118`) net parity, valid `EVQP7J01P` footprint geometry, and East-edge rejection, while raising documentation/brief findings all resolved below:

| ID | Severity | Finding Summary | Resolution |
|---|---|---|---|
| `B1` | BLOCKER | `TP1..TP8` net mapping in `brief.md` §12 was scrambled relative to `mcu.kicad_sch` / PCB. | **Fixed** in `brief.md` §12 (`TP1=VSYS`, `TP2=+3V3`, `TP3=VBAT`, `TP4=+1V1`, `TP5=/MCU/RUN`, `TP6=/MCU/SWCLK`, `TP7=/MCU/SWDIO`, `TP8=GND` with exact coordinates). |
| `B2` | BLOCKER | `EVQP7J01P` push travel (`0.20 mm`, not `0.50 mm`), height (`1.35 mm`, not `1.70 mm`), rating (`10 µA 2 V DC – 50 mA 12 V DC`), and bounce (`10 ms` max) misquoted; plunger stops `0.25 mm` proud of `Edge.Cuts` at full stroke (`|x| = 12.75 mm`), never flush. | **Fixed** in `phase4.md`, `brief.md` §3 & §11 (`>= 0.25 mm` bezel stop rule), and `floorplan.png`. |
| `B3` | BLOCKER | `BT1` (`A1251WR-S-2P` horizontal header facing `-X` with `1.28 mm` body gap to `U5`) and `J1` (`TYPE-C-31-M-22` with `2 × Ø 0.65 mm` NPTH holes and `1.52 mm` shell mouth overhang) misdescribed in `brief.md` §3–§4 and omitted from `floorplan.png`. | **Fixed** in `brief.md` §3–§4 and `floorplan.png` (`2 × Ø 0.65 mm` NPTH holes plotted on Front & Back views; `BT1` tilted-plug mating & `J1` overhang documented). |
| `M1` | MAJOR | `SW1`, `SW2`, and `SW5` (`1.35 mm` body to `|x| = 9.40 mm`; `SW5` `y_max = -20.25 mm`) encroach into a `20 × 35 mm` (`x ∈ [-10, +10]`) cell on `1.0 mm` foam tape. | **Fixed** in `brief.md` §3, `floorplan.png`, and User Decision #3 below: `501035` (`10 × 35 mm`) or `<= 18.5 mm` cell fits on `1.0 mm` tape (`4.40 mm` clear); `20 × 35 mm` cell requires `>= 1.5 mm` foam tape. |
| `M2` | MAJOR | Stale coordinates/specs in `brief.md` (`R = 1.00 mm` corner fillets, `3.70 × 2.60 mm` LED grid, `Q2` `(0.00, -29.90)`, `SW4` `U3.31`, `SW1` `/MCU/BTN`, IC centers `U1/U2/U5/U6/U9/L1/Y1`). | **Fixed** across `brief.md` §1, §3, §4, §7, §8 and `phase4.md`. |
| `M3` | MAJOR | `floorplan.png` plotted unrotated boxes for `J1`/`Q2`, omitted NPTH holes & `R = 1.00 mm` fillets, and mislabeled the LiPo pocket. | **Fixed**: regenerated `floorplan.svg`/`floorplan.png` from true rotated KiCad courtyard polygons, sampled `SHAPE_T_ARC` `R = 1.00 mm` fillets, plotted `J1` NPTH holes, and unified all clearance numbers. |
| `M4` | MAJOR | `1 kΩ + 100 nF` (`t_rise = 3.59–8.83 ms`) requires `>= 20 ms` firmware debounce for `10 ms` max OFF bounce + slow-corner rise (`18.83 ms`); RP2350 `POWMAN` (`P1.7`) has `4` hardware GPIO wake generators (`PWRUP0..3`, `2` left after `SW1` + `ACC_INT`). | **Fixed** in `brief.md` §7, `bringup.md` §3, `design/sim/p2-132-usb6/sim_buttons.py`, and User Decision #2 below (`>= 20 ms` press+release SW debounce). |
| `M5` | MAJOR | Dedicated `I2C` SMD test pads & `0 Ω` isolation jumpers (`intent.md` R9) omitted on `25 × 70 mm` parallelogram family without explicit waiver citation. | **Documented** in `brief.md` §12 (`I2C0`/`I2C1` probe on `0402` pull-ups `R21/R22` & `R19/R20`; `USER_C/D` on `R46/R47`) and recorded in `design/decisions.md`. |
| `m1` | MINOR | `R46/C71/R47/C72` at `x = -7.80 mm` encroached `0.18 mm` into Col 0 `F.Cu` LED pad envelope (`x = -8.40 mm`); shifting `0.40 mm` East to `x = -7.40 mm` centers them inside `[-8.40, -6.40]`. | **Fixed** in `pcb_gen.py` (`x = -7.40 mm`, `copper_x ∈ [-8.18, -6.62]`), `brief.md`, `phase4.md`, and `floorplan.png`. |
| `m2` | MINOR | Stackup thickness (`1.6 mm` vs `1.0 mm`), surface finish, & POFV statement needed alignment in `brief.md` §5. | **Fixed** in `brief.md` §5 & `stackup.md`: locked to `1.6 mm` `JLC04161H-7628`, **ENIG 1U"**, and **`POFV = Yes` (VIPPO)** per `design/study/parallelogram/README.md` §2 (`118` through-vias in SMD pads vs `134` on parent `p2-132-usb`; `0` EP paste overlap). |
| `m3` | MINOR | `brief.md` §10 omitted repo-URL policy (`intent.md` §Open source) and `BT1` `+` South / `-` North pin orientation. | **Fixed** in `brief.md` §3 & §10 (`Pad 1` South = `+` `VBAT`, `Pad 2` North = `-` `BAT_N`; contiguous 3-column repo URL `github.com/sequoia-hope/round-pendant` on `B.SilkS`). |
| `N1–N3` | NOTE | Confirmed `0` courtyard overlaps, `LX cutout L2` shape, `.kicad_dru` rule areas, inherited top-side `Q2` (`R12`), and stale `README.md` §5 text. | **Noted** (`README.md` §5 subsection & `"For the project memory"` updated; inherited divergences logged in `decisions.md`). |

## Decisions Requiring User Sign-Off (Phase 4)
1. **Approve West long-edge button locations, `0.20 mm` stroke, & bezel stop:**
   - `SW5` (`USER_C`) at `(-10.85, -22.00) mm`, `rot = +90°` (West edge North, `0.31 mm` courtyard-clear south of `SW3`, `18.50 mm` center-to-center north of `SW2`).
   - `SW6` (`USER_D`) at `(-10.85, +22.80) mm`, `rot = +90°` (West edge South, `26.30 mm` center-to-center south of `SW2`, `1.81 mm` rotated-courtyard clear of `J1`, `1.12 mm` terminal / `0.97 mm` pad north of SW `R = 1.00 mm` fillet tangent `y = +26.270 mm`).
   - Both actuators sit at `x = -12.95 mm` at rest (`0.45 mm` overhang past `x = -12.50 mm`, identical to `SW1`/`SW2`) and reach `x = -12.75 mm` (`0.25 mm` proud of `Edge.Cuts`) at full `0.20 mm` push travel; any enclosure bezel must stop `>= 0.25 mm` proud of `x = ±12.50 mm`. `J1` remains untouched at `(-1.24, +26.82)`, `rot = 162.26°`.
2. **Approve firmware GPIO assignment, RC + software debounce, & `POWMAN` wake allocation:**
   - `SW5` (`USER_C`) -> `U3` `GPIO9` (`Pin 13`), `SW6` (`USER_D`) -> `U3` `GPIO0` (`Pin 2`), internal RP2350 pull-up (`50–80 kΩ`), `1 kΩ` series protection (`R46`/`R47`) + `100 nF` capacitor (`C71`/`C72`) to `GND`, paired with a **`>= 20 ms` symmetrical press + release firmware debounce window** across `SW1..SW6` (`10 ms` max `EVQP7J01P` OFF bounce + `8.83 ms` slow-corner RC rise = `18.83 ms`).
   - Because RP2350 `POWMAN` (`P1.7`) deep sleep has `4` hardware GPIO wake slots (`PWRUP0..3`) and `SW1` (`GPIO11`) + `ACC_INT` (`GPIO10`) use `2`, confirm which `2` of `{SW3, SW4, SW5, SW6}` (if any) should wake `P1.7` deep sleep in firmware (all `6` buttons work simultaneously in active and `dormant` modes).
3. **Confirm LiPo cell width / mounting tape thickness:**
   - `1.35 mm`-tall side switches (`SW1`, `SW2`, `SW5`) have plastic bodies reaching `|x| = 9.40 mm` (`18.80 mm` clear span). Confirm either using a `<= 18.5 mm`-wide cell (e.g. `501035` `10 × 35 mm` on `1.0 mm` foam tape) or `>= 1.5 mm` foam tape when mounting a `20 × 35 mm` (`802035`/`102035`) cell.
