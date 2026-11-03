#!/usr/bin/env python3
"""peek.py BOARD AUTOROUTE_JSON OUT.png X0 Y0 X1 Y1: debug plot of copper per layer in a window, board-centre mm, with open connections in red."""
import json, re, sys, math, pcbnew
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as P, Circle
b = pcbnew.LoadBoard(sys.argv[1]); um = pcbnew.ToMM; X0, Y0, X1, Y1 = map(float, sys.argv[4:8])
LAY = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In3.Cu": pcbnew.In3_Cu, "B.Cu": pcbnew.B_Cu}
fig, ax = plt.subplots(2, 2, figsize=(16, 16))
pads = {}
for f in b.GetFootprints():
    for p in f.Pads():
        c = p.GetPosition(); pads[(f.GetReference(), p.GetNumber())] = (um(c.x)-100, um(c.y)-100)
d = json.load(open(sys.argv[2])); run = d["runs"][d["best"]]
pat = re.compile(r"Pad (\S*) \[[^\]]*\] of (\S+) on")
opens = []
for o in run["open_items"]:
    ms = [pat.search(i) for i in o.split(" / ")]
    if all(ms):
        opens.append([pads[(m.group(2), m.group(1))] for m in ms])
for (name, lay), a in zip(LAY.items(), ax.flat):
    a.set_title(name); a.set_xlim(X0, X1); a.set_ylim(Y1, Y0); a.set_aspect(1)
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(lay) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                bb = p.GetBoundingBox(); fam = p.GetNetname()
                a.add_patch(plt.Rectangle((um(bb.GetLeft())-100, um(bb.GetTop())-100), um(bb.GetWidth()), um(bb.GetHeight()), color="#bbb" if not f.GetReference().startswith("D") else "#9c9", lw=0))
    for t in b.GetTracks():
        n = t.GetNetname(); c = "#1f77b4" if "/CS" in n else "#2ca02c" if "/SW" in n else "#9467bd"
        if t.GetClass() == "PCB_VIA":
            q = t.GetPosition(); a.add_patch(Circle((um(q.x)-100, um(q.y)-100), um(t.GetWidth(pcbnew.F_Cu))/2, color=c, alpha=.8, lw=0))
        elif t.GetLayer() == lay:
            s, e = t.GetStart(), t.GetEnd(); a.plot([um(s.x)-100, um(e.x)-100], [um(s.y)-100, um(e.y)-100], color=c, lw=um(t.GetWidth())*72*16*.45/(X1-X0)*1.0, solid_capstyle="round")
    for q in opens:
        a.plot([q[0][0], q[1][0]], [q[0][1], q[1][1]], "r-", lw=1.2)
fig.tight_layout(); fig.savefig(sys.argv[3], dpi=70)
