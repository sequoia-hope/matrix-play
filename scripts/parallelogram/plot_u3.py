"""Plot copper within +-8 mm of U3, one panel per layer, coordinates relative to U3."""
import sys, pcbnew, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
b = pcbnew.LoadBoard(sys.argv[1]); out = sys.argv[2]
extra = [tuple(map(float, s.split(","))) for s in sys.argv[3:]]  # marker points x,y
u = b.FindFootprintByReference("U3"); c = u.GetPosition(); CX, CY = pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)
R = lambda x, y: (pcbnew.ToMM(x) - CX, pcbnew.ToMM(y) - CY)
W = float(__import__("os").environ.get("W", "8.0"))
LAY = [("B.Cu", pcbnew.B_Cu), ("In2.Cu", b.GetLayerID("In2.Cu")), ("F.Cu", pcbnew.F_Cu)]
col = lambda n: {"+1V1": "red", "+3V3": "orange", "GND": "0.6", "/MCU/VREG_LX": "purple"}.get(n, "tab:blue")
fig, axs = plt.subplots(1, 3, figsize=(30, 10.5))
for ax, (name, lid) in zip(axs, LAY):
    ax.set_title(name, fontsize=16)
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(lid): continue
        fp = z.GetFilledPolysList(lid)
        for i in range(fp.OutlineCount()):
            o = fp.Outline(i); pts = [R(o.CPoint(k).x, o.CPoint(k).y) for k in range(o.PointCount())]
            ax.add_patch(Polygon(pts, closed=True, fc=col(z.GetNetname()), alpha=0.35, ec="none"))
    for fpr in b.GetFootprints():
        for p in fpr.Pads():
            if not p.IsOnLayer(lid): continue
            sh = p.GetEffectivePolygon(lid)
            for i in range(sh.OutlineCount()):
                o = sh.Outline(i); pts = [R(o.CPoint(k).x, o.CPoint(k).y) for k in range(o.PointCount())]
                if all(abs(x) < W + 1 and abs(y) < W + 1 for x, y in pts):
                    ax.add_patch(Polygon(pts, closed=True, fc=col(p.GetNetname()), alpha=0.8, ec="k", lw=0.3))
            px, py = R(p.GetPosition().x, p.GetPosition().y)
            if abs(px) < W and abs(py) < W and name != "In2.Cu":
                ax.text(px, py, f"{fpr.GetReference()}.{p.GetNumber()}", fontsize=5, ha="center", va="center")
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == "PCB_VIA":
            x, y = R(t.GetPosition().x, t.GetPosition().y)
            if abs(x) < W and abs(y) < W:
                ax.add_patch(Circle((x, y), pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) / 2, fc=col(n), ec="k", lw=0.5))
        elif t.GetLayer() == lid:
            (x0, y0), (x1, y1) = R(t.GetStart().x, t.GetStart().y), R(t.GetEnd().x, t.GetEnd().y)
            if min(abs(x0), abs(x1)) < W + 2 and min(abs(y0), abs(y1)) < W + 2:
                ax.plot([x0, x1], [y0, y1], color=col(n), lw=pcbnew.ToMM(t.GetWidth()) * 72 / 25.4 * 10.5 / (2 * W) * 25.4 * 0.95, solid_capstyle="round", alpha=0.9)
    for x, y in extra:
        ax.plot(x, y, "x", color="lime", ms=12, mew=2)
    ax.set_xlim(-W, W); ax.set_ylim(W, -W); ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.set_xticks(range(-int(W), int(W) + 1))
fig.tight_layout(); fig.savefig(out, dpi=110)
