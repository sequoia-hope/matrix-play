#!/usr/bin/env python3
"""mapscore.py CSV...: chain and column metrics of matrix maps. sharp = LEDs whose chain turns over 75 degrees (no LED turn keeps the anode behind both links)."""
import csv, math, sys, statistics as st
for fn in sys.argv[1:]:
    R = list(csv.DictReader(open(fn)))
    g = {(int(r["driver"]), int(r["triplet"]), int(r["sw"])): (float(r["x_mm"]), float(r["y_mm"])) for r in R}
    L = []; sharp = 0; C = []
    for (d, t, s), p in g.items():
        if (d, t, s+1) in g:
            q = g[(d, t, s+1)]; L.append(math.hypot(p[0]-q[0], p[1]-q[1]))
            if (d, t, s-1) in g:
                o = g[(d, t, s-1)]; u = (p[0]-o[0], p[1]-o[1]); v = (q[0]-p[0], q[1]-p[1])
                if (u[0]*v[0]+u[1]*v[1])/(math.hypot(*u)*math.hypot(*v)) < .26: sharp += 1
    print(f"{fn.split('/')[-1]:24s} chain link med {st.median(L):.2f} max {max(L):5.2f} >2.8:{sum(l>2.8 for l in L):3d}  sharp {sharp:3d}")
