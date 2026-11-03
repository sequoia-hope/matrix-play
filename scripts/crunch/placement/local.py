#!/usr/bin/env python3
"""local.py BOARD X Y HALF OUT.png NET...: all copper in a window, one panel per routing layer, highlighting NETs. mm from board centre."""
import sys, pcbnew, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
bd, X, Y, H, out, *nets = sys.argv[1:]; X, Y, H = float(X), float(Y), float(H)
b = pcbnew.LoadBoard(bd); um = pcbnew.ToMM
lay = ["F.Cu", "In1.Cu", "In3.Cu", "In4.Cu", "In6.Cu", "B.Cu"]; ids = {b.GetLayerName(l): l for l in range(64)}
fig, axs = plt.subplots(2, 3, figsize=(18, 12))
hit = lambda n: any(k in n for k in nets)
for ax, L in zip(axs.flat, lay):
    i = ids[L]; ax.set_title(L); ax.set_xlim(X-H, X+H); ax.set_ylim(Y+H, Y-H); ax.set_aspect("equal"); ax.grid(alpha=.3)
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(i): continue
        ps = z.GetFilledPolysList(i)
        for k in range(ps.OutlineCount()):
            o = ps.Outline(k); ax.add_patch(Polygon([(um(o.CPoint(j).x)-100, um(o.CPoint(j).y)-100) for j in range(o.PointCount())], fc="#ddd", ec="none"))
    for f in b.GetFootprints():
        for p in f.Pads():
            if not p.IsOnLayer(i): continue
            q = p.GetBoundingBox(); c = "r" if hit(p.GetNetname()) else "#777"
            ax.add_patch(Rectangle((um(q.GetLeft())-100, um(q.GetTop())-100), um(q.GetWidth()), um(q.GetHeight()), fc=c, alpha=.6))
            ax.text(um(p.GetPosition().x)-100, um(p.GetPosition().y)-100, f"{f.GetReference()}.{p.GetNumber()}", fontsize=6, ha="center", clip_on=True)
    for t in b.GetTracks():
        n = t.GetNetname()
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition(); ax.add_patch(Circle((um(c.x)-100, um(c.y)-100), um(t.GetWidth(i))/2, fc="r" if hit(n) else "k", alpha=.7))
        elif t.GetLayer() == i:
            ax.plot([um(t.GetStart().x)-100, um(t.GetEnd().x)-100], [um(t.GetStart().y)-100, um(t.GetEnd().y)-100], c="r" if hit(n) else "b", lw=um(t.GetWidth())*72*12/ (2*H) * .9, solid_capstyle="round", alpha=.8)
fig.tight_layout(); fig.savefig(out, dpi=80)
