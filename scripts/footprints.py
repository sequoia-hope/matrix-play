#!/usr/bin/env python3
"""footprints.py -- project footprints for round-pendant. Writes hw/round-pendant/a/lib/round_pendant.pretty.

  LED_XL-1010RGB   datasheet p.8 recommended pattern
  QFN-60 EP 5.4    stock QFN-60 outline with the IS31FL3741A land pattern (p.22)
  L_pol_2016, C_0402 small pads, RP2350 QFN-60   Raspberry Pi minimal board RP-006440-DD (chips/rp2350.md)
  XySemi XB9901A   the user's footprint from rp2350-pendant, already built on that board
  BatteryPads      two hand-solder pads for the cell's leads
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import os
VARIANT = os.environ.get("PENDANT_VARIANT", "a")
PRETTY = ROOT / f"hw/round-pendant/{VARIANT}/lib/round_pendant.pretty"
VENDOR = Path.home() / "pcb/RP-006440-DD-2-RP2350A Minimal Board Kicad archive/RP2350_60QFN_minimal.pretty"
XB = Path.home() / "pcb/rp2350-pendant/parts/DFNFC-6_L1.8-W1.4-P0.50_XB9901A.kicad_mod"
STOCK_QFN = Path("/usr/share/kicad/footprints/Package_DFN_QFN.pretty/QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm.kicad_mod")


def line(a, b, layer, w=0.1):
    return f'\t(fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'


def rect(h, layer, w=0.05):
    c = [(-h, -h), (h, -h), (h, h), (-h, h), (-h, -h)]
    return "".join(line(a, b, layer, w) for a, b in zip(c, c[1:]))


def text(kind, value, y, layer, hide=False):
    return (f'\t(property "{kind}" "{value}" (at 0 {y} 0) (layer "{layer}")' + (' (hide yes)' if hide else '') +
            ' (effects (font (size 0.5 0.5) (thickness 0.08))))\n')


def led():
    pads = "".join(f'\t(pad "{n}" smd rect (at {x} {y}) (size 0.45 0.45) (layers "F.Cu" "F.Mask" "F.Paste"))\n'
                   for n, x, y in (("1", -0.4, -0.4), ("2", 0.4, -0.4), ("3", -0.4, 0.4), ("4", 0.4, 0.4)))
    return ('(footprint "LED_XL-1010RGB"\n\t(version 20241229)\n\t(generator "round_pendant")\n\t(layer "F.Cu")\n'
            '\t(descr "XINGLIGHT XL-1010RGB-YG, 1.0 x 1.0 mm RGB, common anode pad 3; datasheet p.8")\n\t(attr smd)\n'
            + text("Reference", "REF**", -1.1, "F.Fab", True) + text("Value", "XL-1010RGB", 1.1, "F.Fab", True)
            + rect(0.5, "F.Fab", 0.05) + rect(0.65, "F.CrtYd")
            + line((-0.5, -0.3), (-0.3, -0.5), "F.Fab", 0.05) + pads + ")\n")


def qfn():
    t = STOCK_QFN.read_text().replace('"QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm"', '"QFN-60-1EP_7x7mm_P0.4mm_EP5.4x5.4mm"', 1)
    t = re.sub(r'\(descr "[^"]*"\)', '(descr "IS31FL3741A QFN-60 7 x 7 mm, land pattern from datasheet p.22: pads 0.74 x 0.22 mm, inner ends 6.05 mm apart, pad 5.40 mm")', t, 1)
    # Signal pads to the datasheet's land.
    def signal(m):
        b = m.group(0)
        at = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)\)', b)
        x, y = float(at.group(1)), float(at.group(2))
        if abs(x) > abs(y):
            nx, ny, size = (3.395 if x > 0 else -3.395), y, "0.74 0.22"
        else:
            nx, ny, size = x, (3.395 if y > 0 else -3.395), "0.22 0.74"
        b = b.replace(at.group(0), f'(at {nx} {ny})')
        return re.sub(r'\(size [\d. ]+\)', f'(size {size})', b)
    t = re.sub(r'\(pad "(?:[1-9]|[1-5]\d|60)" smd roundrect.*?\n\t\)', signal, t, flags=re.S)
    t = strip_pads(t, {"61", ""})
    i = t.rindex(')')
    return t[:i] + split_ep(((-1, 1.3), (1, 1.3), (-2.525, .35), (2.525, .35)), paste=1.0) + t[i:]


def strip_pads(t, names):
    """Remove pads by number from a footprint, by balanced parentheses, whatever their format."""
    out, i = [], 0
    while True:
        m = re.compile(r'\(pad "([^"]*)"').search(t, i)
        if not m:
            out.append(t[i:]); return "".join(out)
        depth, j = 0, m.start()
        while True:
            depth += {"(": 1, ")": -1}.get(t[j], 0); j += 1
            if depth == 0:
                break
        out.append(t[i:m.start()])
        if m.group(1) not in names:
            out.append(t[m.start():j])
        i = j


def split_ep(spans, paste=None, name="61"):
    """Exposed pad as separate rectangles round the LED anode via lines. Spans are (centre, size) on each axis. Thermal vias
    are added per chip on the board (board.py), at LED channel crossings, since a through via reaches the LED side."""
    ep = ""
    for x, sx in spans:
        for y, sy in spans:
            ep += f'\t(pad "{name}" smd rect (at {x} {y}) (size {sx} {sy}) (layers "F.Cu" "F.Mask") (zone_connect 2))\n'
            if paste and sx > .8 and sy > .8:
                ep += f'\t(pad "" smd rect (at {x} {y}) (size {paste} {paste}) (layers "F.Paste"))\n'
    return ep


def battery():
    pads = "".join(f'\t(pad "{n}" smd roundrect (at {x} 0) (size 1.6 2.4) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.15))\n'
                   for n, x in (("1", -1.6), ("2", 1.6)))
    return ('(footprint "BatteryPads"\n\t(version 20241229)\n\t(generator "round_pendant")\n\t(layer "F.Cu")\n'
            '\t(descr "Two hand-solder pads for the cell leads: 1 = +, 2 = -")\n\t(attr smd)\n'
            + text("Reference", "REF**", -2.4, "F.SilkS") + text("Value", "CELL", 2.4, "F.Fab", True)
            + "".join(line(a, b, "F.CrtYd", .05) for a, b in zip(((-2.65, -1.45), (2.65, -1.45), (2.65, 1.45), (-2.65, 1.45)), ((2.65, -1.45), (2.65, 1.45), (-2.65, 1.45), (-2.65, -1.45)))) + pads + ")\n")


def evqp7c():
    """Panasonic EVQP7C01P, side-push with bosses: datasheet p.2, land pattern. Knob towards +y. Pads 1 away from the knob, 2 by it."""
    pads = "".join(f'\t(pad "{n}" smd rect (at {x} {y}) (size 1.4 1.05) (layers "F.Cu" "F.Mask" "F.Paste"))\n'
                   for n, x, y in (("1", -1.8, -.725), ("1", 1.8, -.725), ("2", -1.8, .725), ("2", 1.8, .725)))
    holes = "".join(f'\t(pad "" np_thru_hole circle (at 0 {y}) (size 0.7 0.7) (drill 0.7) (layers "*.Cu" "*.Mask"))\n' for y in (-.9, .9))
    c = ((-2.6, -1.55), (2.6, -1.55), (2.6, 1.55), (.95, 1.55), (.95, 2.2), (-.95, 2.2), (-.95, 1.55), (-2.6, 1.55), (-2.6, -1.55))
    return ('(footprint "SW_Panasonic_EVQP7C"\n\t(version 20241229)\n\t(generator "round_pendant")\n\t(layer "F.Cu")\n'
            '\t(descr "Panasonic EVQP7C01P side-push, with bosses; datasheet p.2. Knob at +y, tip 2.1 from centre")\n\t(attr smd)\n'
            + text("Reference", "REF**", -2.2, "F.SilkS") + text("Value", "EVQP7C01P", 2.8, "F.Fab", True)
            + "".join(line(a, b, "F.CrtYd", .05) for a, b in zip(c, c[1:])) + pads + holes + ")\n")


def usb_pads():
    """Six hand-solder pads for an off-board USB-C receptacle, 1.7 mm pitch."""
    pads = "".join(f'\t(pad "{n}" smd roundrect (at {(i-2.5)*1.7:g} 0) (size 1.2 1.8) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.15))\n'
                   for i, n in enumerate(("1", "2", "3", "4", "5", "6")))
    c = ((-5.0, -1.05), (5.0, -1.05), (5.0, 1.05), (-5.0, 1.05), (-5.0, -1.05))
    return ('(footprint "USB_Pads"\n\t(version 20241229)\n\t(generator "round_pendant")\n\t(layer "F.Cu")\n'
            '\t(descr "Pads for off-board USB-C wires: CC1, CC2, D-, D+, VBUS, GND")\n\t(attr smd)\n'
            + text("Reference", "REF**", -1.7, "F.SilkS") + text("Value", "USB", 1.7, "F.Fab", True)
            + "".join(line(a, b, "F.CrtYd", .05) for a, b in zip(c, c[1:])) + pads + ")\n")


def main():
    PRETTY.mkdir(parents=True, exist_ok=True)
    if VARIANT != "a":
        (PRETTY / "SW_Panasonic_EVQP7C.kicad_mod").write_text(evqp7c())
        (PRETTY / "USB_Pads.kicad_mod").write_text(usb_pads())
    (PRETTY / "LED_XL-1010RGB.kicad_mod").write_text(led())
    (PRETTY / "QFN-60-1EP_7x7mm_P0.4mm_EP5.4x5.4mm.kicad_mod").write_text(qfn())
    (PRETTY / "BatteryPads.kicad_mod").write_text(battery())
    for name in ("L_pol_2016", "C_0402_1005Metric_small_pads", "RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias"):
        shutil.copy(VENDOR / f"{name}.kicad_mod", PRETTY / f"{name}.kicad_mod")
    # RP2350 pad split round the one LED anode via at its centre (brief.md section 10).
    q = strip_pads((VENDOR / "RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias.kicad_mod").read_text(), {"61", ""})
    i = q.rindex(')')
    (PRETTY / "RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias.kicad_mod").write_text(q[:i] + split_ep(((-.975, 1.45), (.975, 1.45)), paste=1.1) + q[i:])
    # Flash with no exposed pad copper: it has no internal connection (datasheet p.69), and LED vias pass under it.
    w = Path("/usr/share/kicad/footprints/Package_SON.pretty/WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm.kicad_mod").read_text()
    w = w.replace('"WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm"', '"WSON-8_6x5mm_P1.27mm_NoEPCopper"', 1)
    w = strip_pads(w, {"9", ""})
    (PRETTY / "WSON-8_6x5mm_P1.27mm_NoEPCopper.kicad_mod").write_text(w)
    xb = XB.read_text().replace("DFNFC-6_L1.8-W1.4-P0.50_XB9901A", "XySemi_DFN-6_1.8x1.4mm")
    (PRETTY / "XySemi_DFN-6_1.8x1.4mm.kicad_mod").write_text(xb)
    print("wrote", PRETTY)


if __name__ == "__main__":
    main()
