#!/usr/bin/env python3
"""opens_map.py VARIANT_DIR [OUT.png]: where a routed trial's opens sit, over back-side parts. Reads route/autoroute.json and route/s0.kicad_pcb."""
import json, re, sys, collections, math
from pathlib import Path
import pcbnew
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
D = Path(sys.argv[1]); out = sys.argv[2] if len(sys.argv) > 2 else str(D/"route/opens.png")
j = json.load(open(D/"route/autoroute.json")); run = j["runs"][j.get("best", 0)]
b = pcbnew.LoadBoard(str(D/"route/s0.kicad_pcb")); mm = pcbnew.ToMM
fps = {f.GetReference(): f for f in b.GetFootprints()}
def pad(ref, num):
    for p in fps[ref].Pads():
        if p.GetNumber() == num:
            c = p.GetPosition(); return mm(c.x)-100, mm(c.y)-100
    return None
segs = []; loose = collections.Counter(); kinds = collections.Counter(); nets = collections.Counter()
for s in run["open_items"]:
    net = re.search(r"\[([^\]]+)\]", s).group(1); short = net.split("/")[-1]
    kind = re.sub(r"\d.*$", "", short); kinds[kind] += 1; nets[short] += 1
    pts = [pad(r, n) for n, r in re.findall(r"Pad (\S+) \[[^\]]+\] of (\S+) on", s)]
    pts = [p for p in pts if p]
    if pts: segs.append((pts, kind, s))
print("open", run["open"], "plane", run["plane_open"], "new_err", run["new_errors"], "vias", run["vias"])
print("kinds", kinds.most_common())
# 4x4 mm occupancy of open ends
H = collections.Counter()
for pts, k, s in segs:
    for x, y in pts: H[(math.floor(x/4)*4, math.floor(y/4)*4)] += 1
for y in range(-20, 20, 4): print(f"{y:4d} "+" ".join(f"{H.get((x,y),0):3d}" for x in range(-20, 20, 4)))
# track use by layer
lay = collections.Counter(); via = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA): c = t.GetPosition(); via.append((mm(c.x)-100, mm(c.y)-100))
    else: lay[t.GetLayerName()] += mm(t.GetLength())
print("track mm by layer", {k: round(v) for k, v in lay.items()})
fig, ax = plt.subplots(figsize=(11, 11)); ax.add_patch(Circle((0, 0), 19, fill=False))
for r, f in fps.items():
    if r.startswith("D"): continue
    bb = f.GetBoundingBox(False); ax.add_patch(Rectangle((mm(bb.GetLeft())-100, mm(bb.GetTop())-100), mm(bb.GetWidth()), mm(bb.GetHeight()), fc="#ddd", ec="#555", lw=.5))
    ax.text(mm(f.GetPosition().x)-100, mm(f.GetPosition().y)-100, r, fontsize=6, ha="center", va="center")
ax.scatter(*zip(*via), s=2, c="#39c", alpha=.5)
col = {"CS": "#d33", "SW": "#a3c"}
for pts, k, s in segs:
    c = next((v for q, v in col.items() if k.startswith(q)), "#080")
    if len(pts) == 2: ax.plot(*zip(*pts), c=c, lw=.8)
    for x, y in pts: ax.plot(x, y, ".", c=c, ms=3)
ax.set_xlim(-20, 20); ax.set_ylim(20, -20); ax.set_aspect("equal"); ax.grid(alpha=.2); ax.set_title(f"{D.name}: {run['open']} open"); fig.savefig(out, dpi=110, bbox_inches="tight")
print(out)
