#!/usr/bin/env python3
"""make_wlcsp_model.py -- generate 3dmodels/WLCSP-36_2.9x2.9mm_P0.5mm.step from datasheet p.20.

From design/datasheets/is31fl3745.pdf p.20 (WLCSP-36, 2.895 x 2.895 x 0.400 mm, 6x6 balls at 0.50 mm pitch,
0.25 mm ball diameter):
- 36 solder balls (0.25 mm dia, z = 0.00..0.16 mm) at x, y in {-1.25, -0.75, -0.25, +0.25, +0.75, +1.25} mm
- Silicon/overmold die body 2.895 x 2.895 mm, z = 0.16..0.40 mm
- Pin A1 index dot near (-1.05, +1.05) on top surface (STEP +Y corresponds to KiCad footprint -Y = top-left A1)
"""
from pathlib import Path
import cadquery as cq

OUT = Path(__file__).resolve().parents[2] / "3dmodels/WLCSP-36_2.9x2.9mm_P0.5mm.step"
a = cq.Assembly(name="WLCSP-36_2.9x2.9mm_P0.5mm")

DIE = (0.14, 0.15, 0.17, 1.0)
BALL = (0.80, 0.82, 0.85, 1.0)
MARK = (0.88, 0.88, 0.84, 1.0)

body = cq.Workplane("XY").box(2.895, 2.895, 0.24, centered=(True, True, False)).translate((0.0, 0.0, 0.16))
a.add(body, name="die", color=cq.Color(*DIE))

coords = [-1.25 + 0.5 * i for i in range(6)]
idx = 0
for ix, x in enumerate(coords):
    for iy, y in enumerate(coords):
        idx += 1
        ball = cq.Workplane("XY").cylinder(0.16, 0.125, centered=(True, True, False)).translate((x, y, 0.0))
        a.add(ball, name=f"b{idx}", color=cq.Color(*BALL))

dot = cq.Workplane("XY").cylinder(0.008, 0.14, centered=(True, True, False)).translate((-1.05, 1.05, 0.40))
a.add(dot, name="pin1_mark", color=cq.Color(*MARK))

OUT.parent.mkdir(parents=True, exist_ok=True)
a.export(str(OUT))
print(OUT)
