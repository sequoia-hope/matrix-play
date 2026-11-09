# Gate 7: routing (`parallelogram-p2-132-usb6`)

Status: **passed**

## Checklist (`references/routing.md` §Gate checklist)
- [x] **DRC `0` errors, `0` warnings, `0` unrouted** (`kicad-cli pcb drc --severity-all --schematic-parity`: `0` violations, `0` unconnected items, `0` schematic parity differences — pasted below)
- [x] **No locked copper:** `locked_copper == 0` across all `5416` track segments and `719` vias (only `Edge.Cuts`, `15` rule-area keepouts, `F.SilkS` web, and the `141` fixed footprints are locked)
- [x] **`nets_check.py --rules --routed` passes (`rc == 0`):** every `length_limit` and zero-via constraint in `design/nets-parallelogram-p2-132-usb6.csv` is satisfied (`QSPI = 5.20–13.56 mm` vs `25 mm`, `USB_D*_MCU = 2.51–2.55 mm` `0` vias vs `6 mm`, `USB_D* = 19.63–19.67 mm` end-to-end with **`0.038 mm` (`0.25 ps`) skew**, `XIN/XOUT/C24 <= 6.15 mm` `0` vias vs `11 mm`)
- [x] **`pad_joints.py` passes (`rc == 0`):** `PASS: 0 thin pad joints` (every SMD pad connection meets full fab track width)
- [x] **`scripts/bga/copper_audit.py` passes (`rc == 0`):** `dangling=0`, `cap_gap=0`, `mid_graze/stubs=0`, `off_via=0`, `morph_necks(<86um)=0`, `acute_slivers=0`, `collinear_dups=0`, `strip_zones=0`, `zone_intrusions=0`
- [x] **Current capacity check passes:** all `POWER`, `POWER_HI`, and `SWITCH` nets meet or exceed IPC-2152 `10 °C` rise widths and `1.5×` via counts (table below)
- [x] **Plane & critical zone integrity check passes:** `plane GND` (`In1.Cu`) = `1` piece (`1310.45 mm²`), `RP2350 ring` (`+1V1` `B.Cu`) = `1` piece (`8.61 mm²`), `RP2350 band` (`+3V3` `B.Cu`) = `1` piece (`11.12 mm²`), `0` foreign vias in `U1/U2/U3/U5` solid EPs, `0` high-speed plane-split crossings (the only `In1.Cu` cutout is the `5.43 mm²` `LX cutout L2` under `VREG_LX`/`L1.2`, which no `DIFF_HS`, `SE_HS`, or `CLOCK` net crosses)
- [x] **Every DRC warning explained:** `0` DRC warnings (`--severity-all`)
- [x] **Per-layer copper renders generated & reviewed:** `design/renders/parallelogram-p2-132-usb6/{F.Cu.png,In1.Cu.png,In2.Cu.png,B.Cu.png,top.png,bottom.png}`
- [x] **PCB view regenerated with copper viewer:** `scripts/view.sh build pcbview.toml`

## Verbatim Verification Outputs

### 1. `verify_variant.py p2-132-usb6` (`drc --severity-all` + `copper_audit` + `pad_joints` + `sync_check` + `nets_check --rules --routed`)
```json
{
  "variant": "p2-132-usb6",
  "n_leds": 132,
  "n_drivers": 2,
  "pitch_mm": [3.7, 2.6],
  "tracks": 5416,
  "vias": 719,
  "locked_copper": 0,
  "non_ep_via_in_pad": 124,
  "solid_eps": {
    "U3": {"gnd_vias": 5, "foreign_vias": 0},
    "U5": {"gnd_vias": 2, "foreign_vias": 0},
    "U1": {"gnd_vias": 5, "foreign_vias": 0},
    "U2": {"gnd_vias": 6, "foreign_vias": 0}
  },
  "zones": {
    "RP2350 band": {"pieces": 1, "area_mm2": 11.12},
    "RP2350 ring": {"pieces": 1, "area_mm2": 8.61},
    "plane GND": {"pieces": 1, "area_mm2": 1310.45}
  },
  "drc_errors": 0,
  "drc_warnings": 0,
  "drc_unconnected": 0,
  "drc_error_types": [],
  "drc_warning_types": [],
  "copper_audit_rc": 0,
  "copper_audit_tail": [
    "hw/parallelogram/p2-132-usb6/parallelogram.kicad_pcb: tracks=5416 vias=719 | dangling=0 cap_gap=0 mid_graze/stubs=0 off_via=0 morph_necks(<86um)=0 acute_slivers=0 collinear_dups=0 micro_segs(<40um)=234 strip_zones=0 zone_intrusions=0"
  ],
  "pad_joints_rc": 0,
  "pad_joints_tail": ["", "  PASS: 0 thin pad joints"],
  "sync_check_rc": 0,
  "nets_routed_rc": 0
}
```

### 2. Standalone Strict DRC + Schematic Parity (`kicad-cli pcb drc --severity-all --schematic-parity`)
```text
Found 0 violations
Found 0 unconnected items
Found 0 schematic parity issues
DRC violations: 0 unconnected: 0 parity: 0
```

### 3. Constrained Net Lengths, New Button Nets, Power Current Capacity, & Zone Piece Audit
```text
=== 1. CONSTRAINED NET LENGTHS & VIA COUNTS ===
  /MCU/BTN_NW              cls=SIGNAL    len=35.244mm (lim=-       ) vias= 2 min_w=0.100mm layers=['B.Cu', 'In2.Cu']
  /MCU/BTN_SE              cls=SIGNAL    len=31.359mm (lim=-       ) vias= 4 min_w=0.100mm layers=['B.Cu', 'F.Cu']
  /MCU/QSPI_SCLK           cls=SE_HS     len= 5.887mm (lim=25      ) vias= 2 min_w=0.100mm layers=['B.Cu', 'In2.Cu']
  /MCU/QSPI_SD0            cls=SE_HS     len= 6.213mm (lim=25      ) vias= 2 min_w=0.100mm layers=['In2.Cu']
  /MCU/QSPI_SD1            cls=SE_HS     len=11.174mm (lim=25      ) vias= 3 min_w=0.100mm layers=['B.Cu', 'F.Cu', 'In2.Cu']
  /MCU/QSPI_SD2            cls=SE_HS     len=13.559mm (lim=25      ) vias= 3 min_w=0.100mm layers=['B.Cu', 'F.Cu', 'In2.Cu']
  /MCU/QSPI_SD3            cls=SE_HS     len= 5.196mm (lim=25      ) vias= 2 min_w=0.100mm layers=['In2.Cu']
  /MCU/QSPI_SS             cls=SE_HS     len= 9.593mm (lim=25      ) vias= 2 min_w=0.100mm layers=['B.Cu', 'F.Cu']
  /MCU/USB_DM_MCU          cls=DIFF_HS   len= 2.554mm (lim=6       ) vias= 0 min_w=0.150mm layers=['B.Cu']
  /MCU/USB_DP_MCU          cls=DIFF_HS   len= 2.513mm (lim=6       ) vias= 0 min_w=0.150mm layers=['B.Cu']
  /MCU/USER_C              cls=SIGNAL    len=27.235mm (lim=-       ) vias= 2 min_w=0.100mm layers=['B.Cu', 'In2.Cu']
  /MCU/USER_D              cls=SIGNAL    len=14.158mm (lim=-       ) vias= 4 min_w=0.100mm layers=['B.Cu', 'F.Cu', 'In2.Cu']
  /Power/USB_DM_C          cls=DIFF_HS   len= 5.652mm (lim=35      ) vias= 3 min_w=0.150mm layers=['F.Cu', 'In2.Cu']
  /Power/USB_DP_C          cls=DIFF_HS   len= 5.613mm (lim=35      ) vias= 2 min_w=0.100mm layers=['B.Cu', 'In2.Cu']
  Net-(C24-Pad1)           cls=CLOCK     len= 1.954mm (lim=11      ) vias= 0 min_w=0.150mm layers=['B.Cu']
  Net-(R44-Pad2)           cls=SIGNAL    len= 6.088mm (lim=-       ) vias= 0 min_w=0.100mm layers=['B.Cu']
  Net-(R45-Pad2)           cls=SIGNAL    len= 5.500mm (lim=-       ) vias= 0 min_w=0.100mm layers=['B.Cu']
  Net-(R46-Pad2)           cls=SIGNAL    len= 4.313mm (lim=-       ) vias= 0 min_w=0.100mm layers=['B.Cu']
  Net-(R47-Pad2)           cls=SIGNAL    len= 4.612mm (lim=-       ) vias= 0 min_w=0.100mm layers=['B.Cu']
  Net-(U3-XIN)             cls=CLOCK     len= 6.149mm (lim=11      ) vias= 0 min_w=0.150mm layers=['B.Cu']
  Net-(U3-XOUT)            cls=CLOCK     len= 1.543mm (lim=11      ) vias= 0 min_w=0.150mm layers=['B.Cu']
  USB_DM                   cls=DIFF_HS   len=11.427mm (lim=35      ) vias= 2 min_w=0.100mm layers=['B.Cu', 'In2.Cu']
  USB_DP                   cls=DIFF_HS   len=11.544mm (lim=35      ) vias= 0 min_w=0.150mm layers=['B.Cu']
  USB end-to-end DP=19.670mm DM=19.633mm skew=0.038mm
  QSPI span: min=5.196mm max=13.559mm skew=8.363mm

=== 2. POWER / POWER_HI / SWITCH CURRENT CAPACITY ===
  +1V1               Icont=0.05   Ipk=0.1    actW=0.100..0.200mm len= 35.44mm vias=  8 zones=[('RP2350 ring', 'B.Cu', 1, 8.605), ('vendor +1V1', 'B.Cu', 1, 2.635)]
  +3V3               Icont=0.04   Ipk=0.15   actW=0.150..0.225mm len= 64.75mm vias= 12 zones=[('vendor +3V3', 'B.Cu', 1, 0.597), ('RP2350 band', 'B.Cu', 1, 11.117)]
  /MCU/VREG_LX       Icont=0.1    Ipk=0.2    actW=0.000..0.000mm len=  0.00mm vias=  0 zones=[('vendor /MCU/VREG_LX', 'B.Cu', 1, 2.183)]
  /Power/BAT_N       Icont=0.34   Ipk=1.0    actW=0.250..0.250mm len= 13.78mm vias=  0 zones=[]
  GND                Icont=0.50   Ipk=2.0    actW=0.200..0.300mm len= 62.18mm vias= 90 zones=[('vendor GND', 'B.Cu', 1, 1.758), ('plane GND', 'In1.Cu', 1, 1310.452)]
  VBAT               Icont=0.34   Ipk=1.0    actW=0.250..0.250mm len= 34.71mm vias=  8 zones=[]
  VBUS               Icont=0.5    Ipk=0.5    actW=0.250..0.250mm len= 16.47mm vias=  5 zones=[]
  VSYS               Icont=0.34   Ipk=0.96   actW=0.160..0.300mm len=104.25mm vias= 26 zones=[]

=== 3. ZONE PIECE COUNTS ===
  Zone  2 name='vendor GND'          net='GND'            layer=B.Cu    islands=1 area=1.758 mm2
  Zone  4 name='RP2350 ring'         net='+1V1'           layer=B.Cu    islands=1 area=8.605 mm2
  Zone  7 name='vendor /MCU/VREG_LX' net='/MCU/VREG_LX'   layer=B.Cu    islands=1 area=2.183 mm2
  Zone 12 name='vendor +3V3'         net='+3V3'           layer=B.Cu    islands=1 area=0.597 mm2
  Zone 13 name='RP2350 band'         net='+3V3'           layer=B.Cu    islands=1 area=11.117 mm2
  Zone 14 name='vendor +1V1'         net='+1V1'           layer=B.Cu    islands=1 area=2.635 mm2
  Zone 20 name='plane GND'           net='GND'            layer=In1.Cu  islands=1 area=1310.452 mm2
```
*(Note on current capacity: on `1 oz` (`35 µm`) outer copper / `0.5 oz` (`17.5 µm`) inner copper, IPC-2152 `10 °C` rise at `0.34 A` continuous requires `~0.04 mm` outer / `~0.08 mm` inner width, and `0.50 A` `VBUS` requires `~0.07 mm` outer; actual power tracks are `0.160–0.300 mm` (`2.3–7.5×` required width), and each `Ø 0.15 mm` / `20 µm`-plated via carries `~0.85 A` (`1.5×` safety = `1` via up to `0.56 A`), exceeded by `VBUS` (`5` vias), `VBAT` (`8` vias), `VSYS` (`26` vias), and `GND` (`90` vias + `18` EP thermal vias).*
*Note on `non_ep_via_in_pad = 124` (`164` total via-in-paste overlaps across `89` `F.Paste` + `75` `B.Paste` pads): parallelogram 4L routing places `0.30/0.15 mm` vias in SMD pads, ordered with mandatory **`POFV = Yes` (JLCPCB 4-layer IPC-4761 Type VII epoxy-filled & copper-capped VIPPO)** per `design/study/parallelogram/README.md` §2 and `stackup.md` so every SMD pad via is plugged and copper-plated flat before stencil printing (`0` open barrels, `0` solder wicking; plus `0` drill overlaps on `B.Paste` across all `18` `U1/U2/U3/U5` thermal vias). Pre-placed RP2350 `+1V1`/`+3V3`/Kelvin copper is locked + protected by `.kicad_dru` `insideArea` keepouts during `ultraroute` routing and unlocked at Gate 7 completion (`locked_copper = 0`) per `references/routing.md` §Gate checklist.*

## Independent Fresh-Context Review (`agy` `gemini-4-argon-high`) & Dispositions
Reviewer independently verified `0` DRC errors/warnings/unconnected/parity, `0` `copper_audit` defects, `0` thin `pad_joints`, `0` locked copper, unbroken `plane GND` / `RP2350 ring` / `RP2350 band` (`1` piece each), and `0` foreign EP vias:

| ID | Severity | Finding Summary | Resolution |
|---|---|---|---|
| `B1` | BLOCKER | `non_ep_via_in_pad = 124` (`164` total via-in-paste overlaps across `89` `F.Paste` + `75` `B.Paste` pads) requires mandatory `POFV = Yes` (Type VII VIPPO) rather than standard tenting. | **Fixed**: Specified **`POFV = Yes` (Type VII epoxy-filled & copper-capped VIPPO) + `ENIG 1U"`** across `brief.md` §5, `stackup.md`, and `phase10.md` (`vias = 719`, `18` EP `GND` vias `5+6+5+2`, **`0` EP drill overlaps on `B.Paste`**). |
| `B2` | BLOCKER | Autorouted `VSYS` tree (`0.16–0.30 mm` across `B.Cu`/`In2.Cu`) + upstream battery series path (`BT1 + BAT_N + U8 + VBAT + U5 BATFET`) must be solved nodally to prove `+3V3` LDO headroom. | **Quantified & Verified in `design/sim/p2-132-usb6/sim_buttons.py` (`solve_vsys_nodal_pdn`) + Logged in `decisions.md`**: Full nodal solver including `3.0 mΩ` via barrels and `273.8 mΩ` typ / `370.3 mΩ` worst-case battery path gives **`ΔV_VSYS(U6.4) = -4.64 mV`**, **`ΔV(U2.5) = -31.78 mV`**, and **`ΔV(U1.5) = -52.46 mV`** at `300 mA` (`GCC <= 0x74`), keeping `V(U6.4) = 4.395 V` on USB and **`3.406 V` typ / `3.375 V` worst >= `3.355 V`** (`TPS7A0233` `V_OUT + V_DO,max(25 mA)`) at **`V_BAT = 3.50 V`** (`0` LDO dropout). Firmware scales brightness via analog `GCC` (`<= 0x40` continuous worn, `<= 0x74` burst, `<= 0x44` charging; never PWM-only at `GCC = 0xFF`) and folds back below `V_BAT = 3.50 V`. |
| `M1–M4` | MAJOR | Autorouted `B.Cu`/`In2.Cu` detours on decap return paths (`C11` `2.99 mm`, `C41` `2.67 mm`) and `19.67 mm` uncoupled `USB_DP`/`USB_DM` (`0.10 mm` QFN/USBLC6 escape neckdowns, `2–3` layer-change vias). | **Disputed in `decisions.md` & Verified in Gate 8**: Inherited 4L `ultraroute` topology shared with `p2-132-usb`; `USB 2.0` FS (`12 Mb/s`, `t_r >= 4 ns`, `t_pd = 0.105 ns << 4 ns`, `l_crit = 125–303 mm`) is `< 0.16 × l_crit` (lumped regime, **`0.038 mm = 0.25 ps` skew**), `U3.30` shares the `11.12 mm²` `RP2350 band` with `7` parallel `100 nF` caps (`U2.5` has parallel `C42` at `1.41 mm`), and `AW20198` `SRCR = 0x07` + `PADS_QSPI.SLEWFAST = 0` bound switching di/dt (`bringup.md` §4). |
| `m1–m2` | MINOR | Single `GND` vias on `SW5.2`/`SW6.2` and `27.24 mm` routed length on `/MCU/USER_C`. | **Verified in Gate 8**: Each `0.30/0.15 mm` via (`L ≈ 0.6 nH`) ties `SW5.2`/`SW6.2` straight into `1,310 mm²` `In1.Cu` `plane GND`, and `C71 = 100 nF` (`50 V` X7R) shunts `/MCU/USER_C` (`0.019 mV` crosstalk). |
