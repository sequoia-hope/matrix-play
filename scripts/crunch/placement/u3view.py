#!/usr/bin/env python3
"""u3view.py BOARD OUT.png [--never]: B.Cu fill round U3 and the regulator, for checking zones by eye. Refills; doesn't save."""
import sys, pcbnew, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle
b = pcbnew.LoadBoard(sys.argv[1]); um = pcbnew.ToMM
B = [l for l in range(64) if b.GetLayerName(l) == "B.Cu"][0]
if "--never" in sys.argv:
    for z in b.Zones(): z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
fig, ax = plt.subplots(figsize=(11, 13))
col = {"+3V3": "#e88", "+1V1": "#8c8", "GND": "#999", "/MCU/VREG_LX": "#fc6"}
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetFirstLayer() != B: continue
    ps = z.GetFilledPolysList(B)
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i); ax.add_patch(Polygon([(um(o.CPoint(k).x)-100, um(o.CPoint(k).y)-100) for k in range(o.PointCount())], fc=col.get(z.GetNetname(), "#88c"), ec="k", lw=.3, alpha=.8))
for f in b.GetFootprints():
    r = f.GetReference()
    if r[0] == "D":
        continue
    for p in f.Pads():
        if not p.IsOnLayer(B): continue
        q = p.GetBoundingBox(); ax.add_patch(Rectangle((um(q.GetLeft())-100, um(q.GetTop())-100), um(q.GetWidth()), um(q.GetHeight()), fc="none", ec=("b" if p.GetNetname() in col else "#555"), lw=.8))
for t in b.GetTracks():
    c = t.GetPosition()
    if isinstance(t, pcbnew.PCB_VIA): ax.add_patch(Circle((um(c.x)-100, um(c.y)-100), .1, fc={"+3V3":"r","GND":"k","+1V1":"g"}.get(t.GetNetname(), "c"), ec="k", lw=.2))
    else: ax.plot([um(t.GetStart().x)-100, um(t.GetEnd().x)-100], [um(t.GetStart().y)-100, um(t.GetEnd().y)-100], c="c", lw=1)
ax.set_xlim(-6, 5); ax.set_ylim(3, -11); ax.set_aspect("equal"); ax.grid(alpha=.2); fig.savefig(sys.argv[2], dpi=100, bbox_inches="tight")
