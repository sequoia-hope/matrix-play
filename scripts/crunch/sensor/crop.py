#!/usr/bin/env python3
"""crop.py BOARD OUT.png X0 Y0 X1 Y1 [LAYERS]: plot copper by layer in a window (mm from centre), one panel per layer, nets named on tracks."""
import sys, math
import pcbnew, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as P, Circle
b = pcbnew.LoadBoard(sys.argv[1]); out = sys.argv[2]; x0, y0, x1, y1 = map(float, sys.argv[3:7])
LS = (sys.argv[7] if len(sys.argv) > 7 else "F.Cu,In1.Cu,In3.Cu,In4.Cu,In6.Cu,B.Cu").split(",")
C = 100.
fig, ax = plt.subplots(2, 3, figsize=(18, 12)); ax = ax.ravel()
col = lambda n: "C%d" % (hash(n) % 10)
def short(n): return n.split("/")[-1][:10]
for a, l in zip(ax, LS):
    li = b.GetLayerID(l); a.set_title(l); a.set_xlim(x0, x1); a.set_ylim(y1, y0); a.set_aspect("equal"); a.grid(alpha=.2)
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(li): continue
        ps = z.GetFilledPolysList(li)
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i); a.add_patch(P([(o.CPoint(j).x/1e6-C, o.CPoint(j).y/1e6-C) for j in range(o.PointCount())], color=col(z.GetNetname()), alpha=.25))
    for f in b.GetFootprints():
        for p in f.Pads():
            if not p.IsOnLayer(li): continue
            o = p.GetEffectivePolygon(li).Outline(0); pts = [(o.CPoint(j).x/1e6-C, o.CPoint(j).y/1e6-C) for j in range(o.PointCount())]
            a.add_patch(P(pts, color=col(p.GetNetname()), alpha=.7))
            cx, cy = p.GetPosition().x/1e6-C, p.GetPosition().y/1e6-C
            if x0 < cx < x1 and y0 < cy < y1: a.text(cx, cy, f"{f.GetReference()}.{p.GetNumber()}\n{short(p.GetNetname())}", fontsize=5, ha="center", va="center")
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            cx, cy = t.GetPosition().x/1e6-C, t.GetPosition().y/1e6-C
            if x0-1 < cx < x1+1 and y0-1 < cy < y1+1:
                a.add_patch(Circle((cx, cy), t.GetWidth(pcbnew.F_Cu)/2e6, color=col(t.GetNetname()), ec="k", alpha=.9)); a.add_patch(Circle((cx, cy), t.GetDrill()/2e6, color="w"))
                a.text(cx, cy, short(t.GetNetname()), fontsize=4, ha="center")
        elif t.GetLayer() == li:
            s, e = t.GetStart(), t.GetEnd(); xs = (s.x/1e6-C, e.x/1e6-C); ys = (s.y/1e6-C, e.y/1e6-C)
            if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1: continue
            a.plot(xs, ys, color=col(t.GetNetname()), lw=t.GetWidth()/1e6*72*(fig.get_size_inches()[0]/3*.8)/(x1-x0), solid_capstyle="round", alpha=.8)
            mx, my = sum(xs)/2, sum(ys)/2
            if x0 < mx < x1 and y0 < my < y1 and math.hypot(xs[1]-xs[0], ys[1]-ys[0]) > .3: a.text(mx, my, short(t.GetNetname()), fontsize=4)
plt.tight_layout(); plt.savefig(out, dpi=110)
