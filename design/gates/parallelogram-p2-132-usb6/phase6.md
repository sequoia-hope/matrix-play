# Gate 6: placement (`parallelogram-p2-132-usb6`)

Status: **passed** *(visual render published to PCB view for user review alongside Phase 4/10 sign-off)*

## Scope & Inherited Placement Baseline
`parallelogram-p2-132-usb6` (`hw/parallelogram/p2-132-usb6/`) preserves 100% of parent `parallelogram-p2-132-usb`'s component positions and orientations — including `J1` at `(-1.24, +26.82)`, `rot = 162.2553°` (`usb_s = -2.45`, `usb_ye = 3.60`), `BT1` at `(+8.40, +20.05)`, `SW1..SW4`, `U1..U9`, `L1`, `Y1`, `Q1`, `Q2`, and all `132` `XL-1615RGBC` front-matrix LEDs (`D1..D132`) — and places **only** the two new West-edge peg-less side-actuated `EVQP7J01P` switches (`SW5`, `SW6`) and their paired `1 kΩ + 100 nF` protection/debounce passives (`R46`/`C71`, `R47`/`C72`):

| Ref | Part / Value | Side | Center `(x, y)` mm | Rot (°) | Courtyard `[x0, x1] × [y0, y1]` mm | Copper `[x0, x1] × [y0, y1]` mm | Locked | Placement Rationale |
|---|---|---|---|---|---|---|---|---|
| `SW5` | `EVQP7J01P` (`USER_C`) | `B.Cu` | `(-10.85, -22.00)` | `+90.0` | `[-13.05, -9.31] × [-24.59, -19.41]` | `[-12.10, -9.60] × [-24.40, -19.60]` | Yes | West long edge North: actuator at `x = -12.95` (`0.45 mm` overhang matching `SW1`/`SW2`), `0.310 mm` courtyard-clear south of `SW3`, `13.310 mm` north of `SW2`, peg-less (`0` drills in `D1..D132` field). |
| `R46` | `1 kΩ` `0402` (`C11702`) | `B.Cu` | `( -7.40, -21.00)` | `180.0` | `[ -8.33, -6.47] × [-21.47, -20.53]` | `[ -8.18, -6.62] × [-21.32, -20.68]` | No | Immediately east (`3.45 mm` DX) of `SW5.1`, centered inside Column 0–1 LED alley (`[-8.40, -6.40]`), `4.313 mm` direct `B.Cu` trace (`0` vias) from `SW5.1`. |
| `C71` | `100 nF` `0402` (`C1525`) | `B.Cu` | `( -7.40, -22.20)` | `180.0` | `[ -8.31, -6.50] × [-22.66, -21.75]` | `[ -8.16, -6.64] × [-22.51, -21.89]` | No | `1.20 mm` south of `R46`, sharing `/MCU/USER_C` at `R46.1` and `GND` via directly into `In1.Cu` `plane GND` (`0` rows/grids; paired directly with `SW5`/`R46`). |
| `SW6` | `EVQP7J01P` (`USER_D`) | `B.Cu` | `(-10.85, +22.80)` | `+90.0` | `[-13.05, -9.31] × [+20.20, +25.39]` | `[-12.10, -9.60] × [+20.40, +25.20]` | Yes | West long edge South: actuator at `x = -12.95`, `1.806 mm` rotated-courtyard clear of `J1`, `2.910 mm` clear of `U4`, `1.070 mm` copper clear of SW `R = 1.00 mm` fillet tangent (`y = +26.270`). |
| `R47` | `1 kΩ` `0402` (`C11702`) | `B.Cu` | `( -7.40, +21.00)` | `180.0` | `[ -8.33, -6.47] × [+20.53, +21.47]` | `[ -8.18, -6.62] × [+20.68, +21.32]` | No | Immediately east (`3.45 mm` DX) of `SW6.1` inside Column 0–1 LED alley (`0.080 mm` courtyard clear of `U4`), `4.612 mm` direct `B.Cu` trace (`0` vias) from `SW6.1`. |
| `C72` | `100 nF` `0402` (`C1525`) | `B.Cu` | `( -7.40, +19.80)` | `180.0` | `[ -8.31, -6.50] × [+19.34, +20.25]` | `[ -8.16, -6.64] × [+19.49, +20.11]` | No | `1.20 mm` north of `R47`, shunting `/MCU/USER_D` directly into `In1.Cu` `plane GND`. |

## Checklist (`references/placement.md` §Gate checklist)
- [x] **Fixed items match `brief.md` and are locked:** `8` `Edge.Cuts` items (`4` straight edges + `4` `R = 1.00 mm` tangent arcs), `14` rule-area keepout zones (`LX cutout L2/L3`, `U3 ring/band/vias`, `reg corner`, `L1 window`, `vendor * area`, `U1/U2/U3/U5 solid EP`), and all `141` mechanically/optically fixed footprints (`J1`, `BT1`, `SW1..SW6`, `Q2`, `D1..D132`) carry `(locked yes)` in `hw/parallelogram/p2-132-usb6/parallelogram.kicad_pcb`, while all `4921` tracks and `729` vias have `0` locked copper (`locked_copper == 0`).
- [x] **Placement check passes (verbatim output pasted below):** `PASS: 0 errors, 0 warnings` (`Y1.1 = 5.8 mm`, `Y1.3 = 3.9 mm`, all `33` `Decouples` capacitors `1.17–3.56 mm`, `ratsnest = 2892 mm` over `138` nets).
- [x] **Schematic-to-PCB sync check passes:** `231` schematic symbols ↔ `231` PCB footprints (`PASS: 0 errors, 0 warnings`).
- [x] **Datasheet layout guidelines followed per part & enforced via rule areas:**
  - `U3` (`RP2350A`, `design/parts/rp2350-core.md`): Mirrored Raspberry Pi reference buck layout (`L1` `AOTA-B201610S3R3-101-T` `<= 2.5 mm` from `VREG_LX`, `C18`/`C19` `4.7 µF` at `1.63–2.13 mm`, `C8..C17, C20, C21` at `1.17–3.10 mm`, unbroken `RP2350 ring` `+1V1` + `RP2350 band` `+3V3` enforced by `U3 ring` / `U3 band` rule areas, `LX cutout L2` on `In1.Cu` & `LX cutout L3` on `In2.Cu` blocking copper under `VREG_LX`/`L1.2`, `5` `GND` thermal vias in solid EP).
  - `Y1` (`ABM8-272-T3` `12 MHz`): Placed `3.9–5.8 mm` north of `U3` `XIN`/`XOUT` (`0` vias, `B.Cu` only, `C23`/`C24` `15 pF` right at `Y1` pads, `vendor GND` guard pour).
  - `U1`, `U2` (`AW20198QNR`, `design/parts/drivers-aw20198.md`): Diagonally staggered (`12.68 mm` center-to-center) for thermal spreading, `C30..C34` / `C40..C44` within `1.29–3.56 mm` of `PVCC`/`AVCC`, `R30`/`R40` (`R_EXT`) adjacent to pin, solid EP rule areas (`0` foreign vias, `5` paste-free `GND` thermal vias in each EP).
  - `U5` (`BQ24073`), `U6` (`TPS7A0233`), `U7` (`USBLC6-2SC6`), `U8` (`XB9901A`), `Q1` (`NTZD3155C`): Placed in south power block between `J1` (`USB-C`) and `BT1` (`JST 1.25`), `U7` inline on `USB_D+/D-` (`5.77–6.25 mm` from `J1`), `C1`/`C2`/`C5` within `1.48–2.80 mm` of `U5`, `C3`/`C4` within `1.18–1.82 mm` of `U6`, `R8`/`C6` `1.47 mm` from `U8` (`BAT_N` isolated from `GND`).
  - `U4` (`W25Q128JVPIQ`): Placed south-west of `U3` (`QSPI` traces `6.43–15.74 mm <= 25 mm`), `C22` `1.47 mm` from `U4.8`, `NoEPCopper` footprint per Winbond §10.3.
  - `U9` (`LIS2DW12TR`): Placed west of `U3` away from switching/driver heat, `C25..C27` within `1.83–2.48 mm`.
  - `SW5`, `SW6` (`EVQP7J01P`, `design/datasheets/evqp7j01p.pdf`): Peg-less SMD land pattern (`0.40 mm` copper-to-edge clearance at `x = -12.10 mm`), `0.45 mm` rest overhang (`0.25 mm` proud at `0.20 mm` full stroke), `R46`/`C71` and `R47`/`C72` immediately east of Pad 1 so high-impedance finger-contact nodes (`Net-(R46-Pad2)`, `Net-(R47-Pad2)`) stay `< 4.62 mm` on `B.Cu` with `0` vias.
- [x] **Visual review passed & renders generated:** `design/renders/parallelogram-p2-132-usb6/{floorplan.png,top.png,bottom.png,3d-top.png,3d-bottom.png}` + interactive 3D/2D viewer rebuilt via `scripts/view.sh build pcbview.toml`.

## Verbatim Tool Outputs

### 1. `placement_check.py`
```text
placement_check: hw/parallelogram/p2-132-usb6/parallelogram.kicad_pcb
  Y1 pad 1 (Net-(U3-XIN)) is 5.8 mm from its IC pin
  Y1 pad 3 (Net-(C24-Pad1)) is 3.9 mm from its IC pin
  ratsnest (MST, all nets except GND): 2892 mm over 138 nets

  decoupler -> pin, pad centre to pad centre
    C1    -> U5.13   VBUS        1.48 mm
    C10   -> U3.20   +3V3        2.40 mm
    C11   -> U3.30   +3V3        1.60 mm
    C12   -> U3.38   +3V3        1.87 mm
    C13   -> U3.53   +3V3        3.10 mm
    C14   -> U3.44   +3V3        1.69 mm
    C16   -> U3.49   +3V3        1.17 mm
    C17   -> U3.46   /MCU/VREG_AVDD  2.83 mm
    C18   -> U3.50   +1V1        2.13 mm
    C19   -> U3.23   +1V1        1.63 mm
    C2    -> U5.10   VSYS        2.80 mm
    C20   -> U3.6    +1V1        1.60 mm
    C21   -> U3.39   +1V1        1.69 mm
    C22   -> U4.8    +3V3        1.47 mm
    C25   -> U9.9    +3V3        1.83 mm
    C26   -> U9.9    +3V3        1.88 mm
    C27   -> U9.10   +3V3        2.48 mm
    C3    -> U6.4    VSYS        1.82 mm
    C30   -> U1.5    VSYS        3.56 mm
    C31   -> U1.5    VSYS        2.23 mm
    C32   -> U1.5    VSYS        2.23 mm
    C33   -> U1.22   VSYS        1.29 mm
    C34   -> U1.22   VSYS        1.36 mm
    C4    -> U6.1    +3V3        1.18 mm
    C40   -> U2.5    VSYS        3.56 mm
    C41   -> U2.5    VSYS        2.23 mm
    C42   -> U2.5    VSYS        2.23 mm
    C43   -> U2.22   VSYS        1.29 mm
    C44   -> U2.22   VSYS        1.36 mm
    C5    -> U5.2    VBAT        1.74 mm
    C6    -> U8.6    Net-(U8-VDD)  1.47 mm
    C8    -> U3.1    +3V3        1.60 mm
    C9    -> U3.11   +3V3        1.60 mm

  PASS: 0 errors, 0 warnings
```

### 2. `sync_check.py`
```text
sync_check: hw/parallelogram/p2-132-usb6
  schematic parallelogram.kicad_sch: 231 symbols (0 excluded from board)
  board parallelogram.kicad_pcb: 231 footprints (0 board-only)
  223 parts to build; required fields: LCSC
  PASS: 0 errors, 0 warnings
```

## Independent Fresh-Context Review (`agy` `gemini-4-argon-high`) & Dispositions
Reviewer independently audited `phase6.md`, `brief.md`, `parallelogram.kicad_pcb`, `top.png`, `bottom.png`, `3d-top.png`, and `3d-bottom.png`, confirming exact `SW5`/`SW6`/`R46`/`C71`/`R47`/`C72` placement coordinates, `0` courtyard overlaps, `placement_check = PASS`, and `sync_check = PASS`:

| ID | Severity | Finding Summary | Resolution |
|---|---|---|---|
| `B1` | BLOCKER | `brief.md` §5 claimed `0` non-EP via-in-pad (`no POFV`), whereas `43` `B.Cu` IC pads and `75` `F.Cu` LED pads (`118` total vs `134` on parent `p2-132-usb`) contain `0.30/0.15 mm` through-vias, and `1` `U2` EP via intruded `0.04 mm` into `B.Paste`. | **Fixed**: Specified **`POFV = Yes` (JLCPCB 4-layer epoxy-filled & copper-capped VIPPO)** across `brief.md` §5, `stackup.md`, and `phase10.md` (per `design/study/parallelogram/README.md` §2), and dropped the redundant 6th `U2` EP via `@(106.036, 91.435)` in `clean_copper_4l.py` so **`0` EP vias touch `B.Paste` anywhere on the board** (`U1=5, U2=5, U3=5, U5=2` paste-free `GND` vias). |
| `B2` | BLOCKER | `14` rule-area keepout zones lacked `(locked yes)` in `parallelogram.kicad_pcb`, and `brief.md` §7 had stale inherited rotations for `Y1` (`0°`, not `180°`) and `U1/U2` (`+90°`, not `180°`). | **Fixed**: Locked all `14` rule-area keepout zones in `pcb_gen.py` `stage_post_silk` while keeping `locked_copper == 0`, and corrected `Y1 = 0°` and `U1/U2 = +90°` in `brief.md` §7. |
| `M1–M4` | MAJOR | Reviewer proposed moving inherited parent `p2-132-usb` parts (`C17` closer to `U3.46`, re-arranging `C1/C2/C5` & `C30..C44` around `U5`/`U1`/`U2`, rotating `Y1` `180°`, and widening `1.28 mm` `BT1`-to-`U5` plug gap). | **Disputed per task brief in `design/decisions.md`**: Task explicitly mandates *"Everything else stays as it is"* from parent `p2-132-usb`; moving parent ICs/decouplers would alter the parent baseline. All `33/33` decouplers pass `placement_check.py` (`1.17–3.56 mm <= 4.0 mm`), `Y1` tracks are `1.54–6.15 mm <= 11 mm` (`0` vias, `B.Cu` only), and `BT1`'s tilted-plug mating (`1.28 mm` gap) is documented in `brief.md` §3 & `bringup.md` §1. |
| `m1–m2` | MINOR | `L1` 3D STEP start-dot (`rot = 180°`) sat opposite `L1` Pad 1 (`+1V1`), and `R46/C71` (`SW5`) vs `R47/C72` (`SW6`) mirror vertically across north/south ends. | **Fixed**: Set `L1` 3D model `rot = 0°` in `pcb_gen.py` `stage_models` so the 3D start-dot aligns with `L1.1` (`+1V1`); north/south RC vertical mirroring keeps `C71`/`C72` inside the clear `x = -7.40 mm` alley away from `SW3` and `U4`. |
