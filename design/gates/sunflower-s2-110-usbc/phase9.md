# Gate 9: Silkscreen, Fab Layers, and Art — Sunflower `s2-110-usbc`

Status: **`failed`** (`silk_check.py` exits with **`240 errors, 1 warnings`**; **held** on `BT1` `+`/`-` and `J1` `USB 5V` labels occluded underneath their own assembled connector bodies, `U1`/`U4`/`U5`/`U6`/`U9` missing `B.SilkS` pin-1 marks and `U1` missing `B.Fab` orientation mark, `20` of `23` `B.SilkS` labels plus `F.SilkS` Voronoi art crossing open non-POFV vias, unlabeled `TP2/TP3/TP5/TP6/TP11/TP13` & missing `F.Fab` LED designators, and unsigned `B.SilkS` identity omission — mitigated for `Rev S3C` bench bring-up by [bringup-map-bottom.png](../../renders/sunflower-s2-110-usbc/bringup-map-bottom.png), see [phase10.md](phase10.md)).

## Checklist ([silkscreen-and-art.md](../../../.claude/skills/pcb-design/references/silkscreen-and-art.md), Phase 9)

| Item | Evidence | State |
|---|---|---|
| Connector label table with reasoning & assembled visibility | Table below; **`BT1` `+`/`-` and `J1` `USB 5V` are covered by their own connector housings in [3d-bottom.png](../../renders/sunflower-s2-110-usbc/3d-bottom.png)** | **failed** |
| Pin-1 & polarity marks visible after assembly | `U2`, `U3`, `Q1`, `Q2`, and `U8` (`B.SilkS` dot confirmed beside `U8.1`, see dispute note below) have visible dots, **but** `U1`, `U4`, `U5`, `U6`, `U9` have no `B.SilkS` pin-1 dots and `U1` has no `B.Fab` chamfer/dot | **failed** |
| Board identity present (`name`, `rev`, `date`, `repo`, `CERN-OHL-P-2.0`) | Omitted on `B.SilkS` (`3` identity errors in `silk_check.py`); waiver in [intent-s2-110-usbc.md](../../study/sunflower/intent-s2-110-usbc.md) `R3` requires user sign-off | **failed** |
| `silk_check.py` passes (verbatim output pasted below) | `FAIL: 240 errors, 1 warnings` (`206` `[hidden]` under `policy: all`, `20` `[silk-over-via]` across `49` non-POFV vias, `11` `[pin1]`, `3` `[identity]`, `1` `[courtyard]` on `NT1`) | **failed** |
| Top & bottom silk and assembly renders reviewed by independent model ([top.png](../../renders/sunflower-s2-110-usbc/top.png), [bottom.png](../../renders/sunflower-s2-110-usbc/bottom.png), [3d-top.png](../../renders/sunflower-s2-110-usbc/3d-top.png), [3d-bottom.png](../../renders/sunflower-s2-110-usbc/3d-bottom.png), [assembly-top.png](../../renders/sunflower-s2-110-usbc/assembly-top.png), [assembly-bottom.png](../../renders/sunflower-s2-110-usbc/assembly-bottom.png)) | Completed (`3 BLOCKER, 4 MAJOR, 2 MINOR, 3 NOTE`); [bringup-map-bottom.png](../../renders/sunflower-s2-110-usbc/bringup-map-bottom.png) generated for unambiguous bench probing | **failed** |
| Art placed, via-clean, and user-approved | `1,027` `F.SilkS` Voronoi sunflower seed-web segments clear all `F.Cu` pads (`0` DRC silk-over-copper), **but** cross open through-vias and require user sign-off vs blank dark mask | **failed** |
| User reviewed silk render in PCB view | Deferred to user sign-off alongside Gates 0, 4, & 10 | pending |

## Connector & User-Control Label Table

| Ref | Function & Rating | Current `B.SilkS` Text | Assembled Visibility ([3d-bottom.png](../../renders/sunflower-s2-110-usbc/3d-bottom.png)) | Assessment & Bench Mitigation |
|---|---|---|---|---|
| `J1` (`TYPE-C-31-M-12`) | USB-C `5 V / 0.5 A` power + USB FS (`D±`) | `"USB 5V"` at `(102.47, 116.79)` | **Occluded (`0%` visible)** — placed between `J1`'s `4` PTH shell slots directly underneath `J1`'s metal shell | **Fail (`BLOCKER-1`):** USB-C receptacle is mechanically self-evident & reversible, so usability risk is low, but `"USB 5V"` must move north/side of `J1` shell in `Rev S3D` |
| `BT1` (`Molex 53261-0271`) | `1S LiPo` (`3.7 V nom / 4.2 V max`, `300 mA` charge) — `Pin 1 = VBAT (+)`, `Pin 2 = BAT_N (-)` | `"BATT"`, `"+"`, `"-"`, `"LIPO 403535"` | `"BATT"` & `"LIPO 403535"` visible, **but `"+"` and `"-"` are occluded underneath `BT1`'s cream plastic housing** | **Fail (`BLOCKER-1`, `MINOR-2`):** High reverse-plugging risk on 2-pin `1.25 mm` LiPo header (`U8` `XB9901A` does not block reverse cell polarity cleanly). Bench mitigation in [bringup-s2-110-usbc.md](../../study/sunflower/bringup-s2-110-usbc.md) & [bringup-map-bottom.png](../../renders/sunflower-s2-110-usbc/bringup-map-bottom.png): **Pin 1 (`VBAT +`) = outer/NE pad `(-13.44, -11.61)` (toward `"BATT"` / top rim)**; **Pin 2 (`BAT_N -`) = SW pad `(-13.87, -10.43)` (toward `"BOOT"` / `SW2`)** |
| `SW1` (`EVQP7J01P`) | `GPIO11` user / wake tactile button (not a hard power switch) | `"PWR"` + `"SW1"` | Visible inside NE rim (`8` vias crossed) | **Fail (`MAJOR-2`):** `"PWR"` is misleading because `SW1` cannot hard-cut battery power (`"USER"` or `"WAKE"` recommended in `Rev S3D`) |
| `SW2` (`EVQP7J01P`) | `~{QSPI_SS}` RP2350 `BOOTSEL` tactile button | `"BOOT"` | Visible inside NW rim (`4` vias crossed) | Functional meaning clear (`silk-over-via` flagged in `BLOCKER-3`) |

## Verbatim `silk_check.py` Output (`2026-11-08`)

Command:
`python3 .claude/skills/pcb-design/scripts/silk_check.py hw/sunflower/s2-110-usbc`

```text
silk_check: hw/sunflower/s2-110-usbc
  206 parts, 0 designators shown (policy: all), 1 connectors, 23 board silk texts
  designator rotations: none

  ERRORS (240)
    [hidden] D1..D110, Q1..Q2, C1..C44, C70, R1..R22, R30..R33, R43, U1..U9, L1, Y1, J1, BT1, SW1..SW2, NT1, TP1..TP8, TP11..TP16: 206 designator(s) hidden or not on silk (policy: all)
    [silk-over-via] bottom silk 'GND' over 2 via(s), first at (84.17, 99.44)
    [silk-over-via] bottom silk 'U1' over 3 via(s), first at (84.02, 102.44)
    [silk-over-via] bottom silk 'BOOT' over 4 via(s), first at (88.02, 96.06)
    [silk-over-via] bottom silk '+' over 2 via(s), first at (90.92, 89.91)
    [silk-over-via] bottom silk 'U6' over 2 via(s), first at (92.17, 100.21)
    [silk-over-via] bottom silk 'Q1' over 2 via(s), first at (91.47, 110.99)
    [silk-over-via] bottom silk 'BATT' over 1 via(s), first at (92.67, 84.39)
    [silk-over-via] bottom silk 'U4' over 3 via(s), first at (93.14, 106.01)
    [silk-over-via] bottom silk 'USB 5V' over 1 via(s), first at (102.47, 116.79)
    [silk-over-via] bottom silk '1V1' over 2 via(s), first at (107.54, 96.71)
    [silk-over-via] bottom silk 'U8' over 2 via(s), first at (108.07, 112.41)
    [silk-over-via] bottom silk 'U7' over 2 via(s), first at (110.72, 110.64)
    [silk-over-via] bottom silk '29' over 1 via(s), first at (113.19, 90.69)
    [silk-over-via] bottom silk 'RX' over 1 via(s), first at (113.22, 92.26)
    [silk-over-via] bottom silk 'PWR' over 3 via(s), first at (114.89, 95.11)
    [silk-over-via] bottom silk 'SW1' over 5 via(s), first at (116.82, 96.99)
    [silk-over-via] bottom silk 'U2' over 2 via(s), first at (116.14, 103.46)
    [silk-over-via] bottom silk 'LIPO 403535' over 6 via(s), first at (107.39, 89.01)
    [silk-over-via] bottom silk 'VSYS' over 4 via(s), first at (108.99, 104.26)
    [silk-over-via] bottom silk 'DIO' over 1 via(s), first at (110.67, 87.86)
    [pin1] D75 (LED_XL-1615RGBC): no pin-1 / polarity mark on the silk beside pad 1
    [pin1] D10 (LED_XL-1615RGBC): no pin-1 / polarity mark on the silk beside pad 1
    [pin1] D32 (LED_XL-1615RGBC): no pin-1 / polarity mark on the silk beside pad 1
    [pin1] D98 (LED_XL-1615RGBC): no pin-1 / polarity mark on the silk beside pad 1
    [pin1] D19 (LED_XL-1615RGBC): no pin-1 / polarity mark on the silk beside pad 1
    [pin1] U6 (Texas_X2SON-4_1x1mm_P0.65mm): no pin-1 / polarity mark on the silk beside pad 1
    [pin1] U9 (LGA-12_2x2mm_P0.5mm): no pin-1 / polarity mark on the silk beside pad 1
    [pin1] U5 (QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm): no pin-1 / polarity mark on the silk beside pad 1
    [pin1] U8 (XySemi_DFN-6_1.8x1.4mm): no pin-1 / polarity mark on the silk beside pad 1
    [pin1] U4 (WSON-8_6x5mm_P1.27mm_NoEPCopper): no pin-1 / polarity mark on the silk beside pad 1
    [pin1] U1 (AW20198_QFN-40-1EP_5x5mm_P0.4mm_EP3.4x3.4mm): no pin-1 / polarity mark on the silk beside pad 1
    [identity] board name 'sunflower (s2-110-usbc)' is not on the silkscreen
    [identity] no rev on the silkscreen (looked for /(\brev\.?\s*[A-Z0-9]|\bv\d+(\.\d+)+)/)
    [identity] no date on the silkscreen (looked for /\b20\d\d([-/.]\d\d)?\b/)

  WARNINGS (1)
    [courtyard] NT1 (NetTie:NetTie-2_SMD_Pad0.5mm) has no courtyard

  FAIL: 240 errors, 1 warnings
```

*(Note: `design/checks.toml` sits two directories above `hw/sunflower/s2-110-usbc/`; `silk_check.py` defaulted to `policy: all`, accounting for `206` `[hidden]` lines, while `34` errors — `20` `[silk-over-via]`, `11` `[pin1]`, `3` `[identity]` — remain even under `designators = "none"`.)*

## Independent Review (`2026-11-08`, fresh-context `agy` reviewer)

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| `BLOCKER-1` | BLOCKER | `BT1` `+`/`-` LiPo polarity marks and `J1` `USB 5V` label are covered underneath their own connector bodies when assembled ([3d-bottom.png](../../renders/sunflower-s2-110-usbc/3d-bottom.png)) | **Upheld — Gate 9 held (`failed`):** Bench polarity map provided in [bringup-map-bottom.png](../../renders/sunflower-s2-110-usbc/bringup-map-bottom.png) and [bringup-s2-110-usbc.md](../../study/sunflower/bringup-s2-110-usbc.md); move `+`/`-` and `USB 5V` outside connector bodies in `Rev S3D` |
| `BLOCKER-2` | BLOCKER | `U1`, `U4`, `U5`, `U6`, `U9` lack `B.SilkS` pin-1 dots; `U1` lacks any `B.Fab` chamfer/dot; reviewer also claimed `U8` `B.SilkS` dot sits at `pad 3` instead of `pad 1` | **Upheld on `U1/U4/U5/U6/U9`; `U8` wrong-corner sub-claim disputed with proof ([decisions.md](../../decisions.md)):** Verified against [XySemi_DFN-6_1.8x1.4mm.kicad_mod](../../../hw/sunflower/s2-110-usbc/lib/round_pendant.pretty/XySemi_DFN-6_1.8x1.4mm.kicad_mod#L167-L231) and [cpl-check-bottom.png](../../renders/sunflower-s2-110-usbc/cpl-check-bottom.png): `U8` (`180°` on `B.Cu`) has its full-width `GND`/`VM` bar (`pads 1–3`) at the **bottom** and `pad 1` at **bottom-left**, right where the white `B.SilkS` dot sits (`silk_check.py` flagged `U8` only because of the merged bar pad `1` centroid `(0, 0.44)`, while the generic `.wrl` 3D model painted a cosmetic dot `180°` off on `pad 4`). Automated JLCPCB pick-and-place uses fixed `cpl-jlcpcb.csv` (`0.000 mm` pad error); add `B.SilkS`/`B.Fab` marks on `U1/U4/U5/U6/U9` in `Rev S3D` |
| `BLOCKER-3` | BLOCKER | `silk_check.py` fails (`240` errors, `1` warning): `20/23` `B.SilkS` texts (`49` vias) plus front `F.SilkS` Voronoi segments cross open non-POFV vias | **Upheld — Gate 9 held (`failed`):** Cosmetic/legibility defect only (`0` silk-over-pad / solderability impact); fix via no-via silk reservations & Voronoi via-clipping in `Rev S3D` |
| `MAJOR-1` | MAJOR | Front `1,027`-segment white `F.SilkS` Voronoi web lacks explicit `intent` specification and user aesthetic sign-off | Added to user sign-off decisions in [phase0.md](phase0.md) and [phase10.md](phase10.md) (approve Voronoi seed web vs bare dark solder mask) |
| `MAJOR-2` | MAJOR | `6/14` test pads (`TP2`, `TP3`, `TP5`, `TP6`, `TP11`, `TP13`) lack `B.SilkS` net labels; `"PWR"` on `SW1` (`GPIO11`) implies hard power-off | **Upheld — Gate 9 held (`failed`):** Mitigated for bench bring-up via [bringup-map-bottom.png](../../renders/sunflower-s2-110-usbc/bringup-map-bottom.png); relabel `SW1` → `"USER"` and add missing TP labels in `Rev S3D` |
| `MAJOR-3` | MAJOR | [assembly-top.png](../../renders/sunflower-s2-110-usbc/assembly-top.png) omits `D1..D110`/`Q2` `F.Fab` designators; [assembly-bottom.png](../../renders/sunflower-s2-110-usbc/assembly-bottom.png) omits `U1/U2/SW1/SW2/NT1` and overlaps `TP*` text | **Upheld — Gate 9 held (`failed`):** Mitigated for `B.Cu` probing via [bringup-map-bottom.png](../../renders/sunflower-s2-110-usbc/bringup-map-bottom.png); restore `F.Fab`/`B.Fab` designators in `pcb_gen.py` for `Rev S3D` |
| `MAJOR-4` | MAJOR | Open-source board identity (`name`, `rev`, `date`, `repo`, `CERN-OHL-P-2.0`) omitted on `B.SilkS` without confirmed user waiver | Flagged for explicit user waiver sign-off in [phase0.md](phase0.md) and [phase10.md](phase10.md) |
| `MINOR-1, 2` | MINOR | `NT1` lacks courtyard (`1` warning); `BT1` silk omits `3.7V` voltage rating and `Ø35 mm` `B.Fab` circle is uncaptioned | Tracked for `Rev S3D` polish |
