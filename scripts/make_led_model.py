#!/usr/bin/env python3
"""make_led_model.py -- 3dmodels/XL-1010RGB-YG.step, drawn from the datasheet because no vendor model exists (LCSC C965834 has none). Needs cadquery (pip install cadquery in a venv).

From design/datasheets/xl-1010rgb-yg.pdf: body 1.0 x 1.0 x 0.4 mm and substrate 0.18 mm (p.8), terminals 0.32 mm with 0.35 mm gaps (p.8), green corner marks at each terminal
(p.8), clear resin, tan lead frame on a pale substrate (picture p.1, "for reference only"). Where the three dies and the top-side copper sit is a guess from that picture, with each
die tinted its colour so it reads in the viewer. Pad 1 R at (-,+) in model coordinates, 2 G (+,+), 3 anode (-,-), 4 B (+,-), matching the footprint.
"""
from pathlib import Path
import cadquery as cq
OUT = Path(__file__).resolve().parents[1] / "3dmodels/XL-1010RGB-YG.step"
a = cq.Assembly(name="XL-1010RGB-YG")
n = [0]


def box(x0, x1, y0, y1, z0, z1, rgba):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); n[0] += 1
    s = cq.Workplane("XY").box(x1-x0, y1-y0, z1-z0, centered=False).translate((x0, y0, z0))
    a.add(s, name=f"p{n[0]}", color=cq.Color(*rgba))


SUB, TAN, GOLD, GREEN, RESIN = (.86, .86, .82, 1), (.87, .68, .45, 1), (.83, .69, .35, 1), (.1, .7, .42, 1), (.93, .95, .95, .25)
box(-.5, .5, -.5, .5, .02, .18, SUB)
for sx in (-1, 1):
    for sy in (-1, 1):
        box(sx*.18, sx*.5, sy*.18, sy*.5, 0, .02, GOLD)                        # terminal, bottom
        box(sx*.40, sx*.5, sy*.40, sy*.5, .02, .18, GREEN)                     # corner mark
        box(sx*.20, sx*.42, sy*.20, sy*.42, .18, .195, TAN)                    # top copper by each terminal
box(-.42, .10, -.09, .09, .18, .195, TAN)                                      # die paddle, joined to the anode corner
box(-.34, -.20, -.20, .09, .18, .195, TAN)
for x, rgb in ((-.24, (.85, .18, .15, 1)), (0, (.2, .75, .3, 1)), (.24, (.2, .3, .9, 1))):
    box(x-.06, x+.06, -.06, .06, .195, .28, rgb)                               # dies
box(-.5, .5, -.5, .5, .195, .40, RESIN)                                        # clear resin
a.export(str(OUT))
print(OUT)
