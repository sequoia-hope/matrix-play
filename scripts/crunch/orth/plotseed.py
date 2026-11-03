#!/usr/bin/env python3
"""plotseed.py dump.json seed.json out.png [x0 y0 x1 y1] [layer]"""
import json, math, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
d = json.load(open(sys.argv[1])); s = json.load(open(sys.argv[2]))
box = list(map(float, sys.argv[4:8])) if len(sys.argv) >= 8 else [-19, -19, 19, 19]
lay = sys.argv[8] if len(sys.argv) > 8 else "F.Cu"
sz = 14
fig, ax = plt.subplots(figsize=(sz, sz*(box[3]-box[1])/(box[2]-box[0])))
for p in d["pads"]:
    if not p["F"] and lay == "F.Cu" and not p["pth"]: continue
    if not p["F"] and lay == "B.Cu" and not p["B"]: continue
    if lay.startswith("In") and not p["pth"] : 
        if not p["ref"].startswith("D"): continue
    a = math.radians(-p["rot"]); c, sn = math.cos(a), math.sin(a); hw, hh = p["w"]/2, p["h"]/2
    col = {"1": "#e66", "2": "#6b6", "3": "#ccc", "4": "#66e"}.get(p["num"], "#aaa") if p["ref"].startswith("D") else "#888"
    ax.add_patch(Polygon([(p["x"]+u*c-v*sn, p["y"]+u*sn+v*c) for u, v in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))], color=col, alpha=.6 if lay == "F.Cu" else .15))
    if p["num"] == "3" and box[2]-box[0] < 15: ax.text(p["x"], p["y"], p["ref"], fontsize=6, ha="center")
for v in d["vias"]:
    ax.add_patch(Circle((v["x"], v["y"]), v["d"]/2, color="k", alpha=.5)); 
for t in d["tracks"]:
    if t["layer"] == lay: ax.plot([t["x1"], t["x2"]], [t["y1"], t["y2"]], "-", color="orange", lw=1)
cols = {}
cm = plt.get_cmap("tab10")
for g in s["segs"]:
    if g["layer"] != lay: continue
    c = cols.setdefault(g["net"], cm(len(cols) % 10))
    ax.plot([g["x1"], g["x2"]], [g["y1"], g["y2"]], "-", color=c, lw=1.5, solid_capstyle="round")
for f in s["fail"]:
    if "a" in f: ax.plot([f["a"][0], f["b"][0]], [f["a"][1], f["b"][1]], "r:", lw=2)
ax.set_xlim(box[0], box[2]); ax.set_ylim(box[3], box[1]); ax.set_aspect("equal")
plt.tight_layout(); plt.savefig(sys.argv[3], dpi=65)
