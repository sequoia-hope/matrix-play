#!/usr/bin/env python3
"""footprints_d.py -- project footprints for round-pendant Variant D (BGA drivers + solid exposed pads).

Writes hw/round-pendant/$PENDANT_VARIANT/lib/round_pendant.pretty:
  WLCSP-36_2.9x2.9mm_P0.5mm   IS31FL3745-CLS4-TR datasheet p. 3 & p. 20 (6x6 @ 0.50 mm, 2.895x2.895 mm body, 0.20 mm NSMD lands)
  RP2350-QFN-60-1EP...        Vendor RP2350A footprint with solid 3.4x3.4 mm exposed pad + 4 paste windows (decisions.md 2026-11-04)
  LED_XL-1010RGB              XINGLIGHT 1.0x1.0 mm RGB LED (datasheet p. 8)
  SW_Panasonic_EVQP7C         Panasonic EVQP7C01P side-push switch with bosses
  USB_Pads                    Off-board USB-C wire pads
  BatteryPads                 Battery lead pads
  WSON-8_6x5mm_P1.27mm_NoEPCopper  W25Q128JVPIQ flash without floating center pad
  XySemi_DFN-6_1.8x1.4mm      XB9901A protection IC
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from footprints import (  # noqa: E402
    VENDOR,
    XB,
    battery,
    evqp7c,
    led,
    line,
    rect,
    strip_pads,
    text,
    usb_pads,
)

VARIANT = os.environ.get("PENDANT_VARIANT", "d")
PRETTY = ROOT / f"hw/round-pendant/{VARIANT}/lib/round_pendant.pretty"


def wlcsp36(pad_dia: float = 0.20, mask_margin: float = 0.045) -> str:
    """IS31FL3745-CLS4-TR WLCSP-36: 6x6 @ 0.50 mm pitch, 0.25 mm ball, 2.895x2.895 mm body (p. 20).
    Top View (looking down through silicon die onto F.Cu land pattern): A1 at (-1.25, -1.25).
    """
    rows = "ABCDEF"
    pads = []
    for r_idx, r_ch in enumerate(rows):
        y = round((r_idx - 2.5) * 0.5, 4)
        for c_idx in range(1, 7):
            x = round((c_idx - 3.5) * 0.5, 4)
            name = f"{r_ch}{c_idx}"
            pads.append(
                f'\t(pad "{name}" smd circle (at {x:g} {y:g}) (size {pad_dia:g} {pad_dia:g})'
                f' (property pad_prop_bga) (layers "F.Cu" "F.Mask" "F.Paste")'
                f" (solder_mask_margin {mask_margin:g}))\n"
            )
    # Package body: 2.895 x 2.895 mm => half-size 1.4475 mm, with 0.35 mm pin-1 chamfer on F.Fab.
    h = 1.4475
    ch = 0.35
    fab_pts = [(-h + ch, -h), (h, -h), (h, h), (-h, h), (-h, -h + ch), (-h + ch, -h)]
    fab = "".join(line(a, b, "F.Fab", 0.05) for a, b in zip(fab_pts, fab_pts[1:]))
    # Courtyard: 3.20 x 3.20 mm (+-1.60 mm, ~0.15 mm margin outside body, rounded to 0.05 mm).
    crtyd = rect(1.60, "F.CrtYd", 0.05)
    return (
        '(footprint "WLCSP-36_2.9x2.9mm_P0.5mm"\n'
        '\t(version 20241229)\n'
        '\t(generator "round_pendant_d")\n'
        '\t(layer "F.Cu")\n'
        '\t(descr "ISSI IS31FL3745-CLS4-TR WLCSP-36, 2.895x2.895mm, 6x6 layout, 0.50mm pitch, 0.25mm ball; datasheet p.3 & p.20")\n'
        '\t(attr smd)\n'
        + text("Reference", "REF**", -1.9, "F.Fab", True)
        + text("Value", "IS31FL3745", 1.9, "F.Fab", True)
        + fab
        + crtyd
        + "".join(pads)
        + ")\n"
    )


def rp2350_solid_ep() -> str:
    """RP2350 QFN-60 with solid 3.4 x 3.4 mm exposed pad 61 and 4x 1.1x1.1 mm paste windows."""
    raw = (VENDOR / "RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias.kicad_mod").read_text()
    q = strip_pads(raw, {"61", ""})
    ep = (
        '\t(pad "61" smd roundrect (at 0 0) (size 3.4 3.4) (layers "F.Cu" "F.Mask")'
        " (roundrect_rratio 0.045) (zone_connect 2))\n"
    )
    for px in (-0.975, 0.975):
        for py in (-0.975, 0.975):
            ep += f'\t(pad "" smd rect (at {px} {py}) (size 1.1 1.1) (layers "F.Paste"))\n'
    i = q.rindex(")")
    return q[:i] + ep + q[i:]


def main():
    PRETTY.mkdir(parents=True, exist_ok=True)
    (PRETTY / "WLCSP-36_2.9x2.9mm_P0.5mm.kicad_mod").write_text(wlcsp36())
    (PRETTY / "SW_Panasonic_EVQP7C.kicad_mod").write_text(evqp7c())
    (PRETTY / "USB_Pads.kicad_mod").write_text(usb_pads())
    (PRETTY / "LED_XL-1010RGB.kicad_mod").write_text(led())
    (PRETTY / "BatteryPads.kicad_mod").write_text(battery())
    for name in ("L_pol_2016", "C_0402_1005Metric_small_pads"):
        shutil.copy(VENDOR / f"{name}.kicad_mod", PRETTY / f"{name}.kicad_mod")
    (PRETTY / "RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias.kicad_mod").write_text(rp2350_solid_ep())
    w = Path("/usr/share/kicad/footprints/Package_SON.pretty/WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm.kicad_mod").read_text()
    w = w.replace('"WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm"', '"WSON-8_6x5mm_P1.27mm_NoEPCopper"', 1)
    w = strip_pads(w, {"9", ""})
    (PRETTY / "WSON-8_6x5mm_P1.27mm_NoEPCopper.kicad_mod").write_text(w)
    xb = XB.read_text().replace("DFNFC-6_L1.8-W1.4-P0.50_XB9901A", "XySemi_DFN-6_1.8x1.4mm")
    (PRETTY / "XySemi_DFN-6_1.8x1.4mm.kicad_mod").write_text(xb)
    print("wrote", PRETTY)


if __name__ == "__main__":
    main()
