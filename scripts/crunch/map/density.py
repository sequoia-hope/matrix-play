#!/usr/bin/env python3
"""density.py BOARD: through vias and layer use per zone (square rings round each chip's centre, rest of the disc) of a routed board."""
import sys, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); um = pcbnew.ToMM
ch = {"U1": (-11.4, 3.4), "U2": (10.6, 3.4), "U3": (-1.4, -6.6)}
def zone(x, y):
    for r, (a, c) in ch.items():
        m = max(abs(x-a), abs(y-c))
        if m < 3.5: return r+" under"
        if m < 5.3: return r+" ring"
        if m < 7.5: return r+" outer"
    return "rest"
Z = collections.Counter(); kinds = collections.Counter(); L = collections.defaultdict(collections.Counter)
for t in b.GetTracks():
    p = t.GetPosition() if t.GetClass() == "PCB_VIA" else None
    n = t.GetNetname(); fam = "cs" if "/CS" in n else "sw" if "/SW" in n else "other"
    if p is not None:
        z = zone(um(p.x)-100, um(p.y)-100); Z[z] += 1; kinds[(z, fam)] += 1
    else:
        s, e = t.GetStart(), t.GetEnd(); z = zone((um(s.x)+um(e.x))/2-100, (um(s.y)+um(e.y))/2-100)
        L[z][b.GetLayerName(t.GetLayer())] += um(t.GetLength())
import math
area = {"under": 49, "ring": 10.6**2-49, "outer": 15**2-10.6**2}
for z in sorted(Z):
    print(z, "vias", Z[z], "cs", kinds[(z, "cs")], "sw", kinds[(z, "sw")], "other", kinds[(z, "other")], {k[:3]: round(v) for k, v in L[z].items()}, "per mm2 %.2f" % (Z[z]/area.get(z.split()[-1], 1134-3*225)))
