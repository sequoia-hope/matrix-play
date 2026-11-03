#!/usr/bin/env python3
"""Plot chains + a SW rank's chords. plotmap.py dump.json out.png"""
import sys, math, os
sys.path.insert(0, os.path.dirname(__file__))
from chains import load, parse
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
d, leds = load(sys.argv[1]); ch, info = parse(leds)
fig, ax = plt.subplots(1, 2, figsize=(20, 10))
cm = plt.get_cmap("tab20")
for k, v in ch.items():
    c = cm(k[1] % 20)
    xs = [info[r]["x"] for r in v]; ys = [info[r]["y"] for r in v]
    ax[0].plot(xs, ys, "-", color=c, lw=2)
    for i, r in enumerate(v): ax[0].text(xs[i], ys[i], str(i+1), fontsize=7, ha="center", va="center")
    ax[0].text(xs[0], ys[0]-.5, f"t{k[1]}", fontsize=8, color=c)
    ax[0].plot(xs[0], ys[0], "o", color=c, ms=8, alpha=.4)
for u in ("U1", "U2", "U3"):
    ax[0].plot(d["fps"][u]["x"], d["fps"][u]["y"], "ks", ms=12, alpha=.3)
    ax[1].plot(d["fps"][u]["x"], d["fps"][u]["y"], "ks", ms=12, alpha=.3)
for drv in (1, 2):
    for sw in range(1, 10):
        rs = [r for r, i in info.items() if i["drv"] == drv and i["sw"] == sw]
        # order per chain angle: by tri
        rs.sort(key=lambda r: info[r]["tri"])
        ax[1].scatter([info[r]["x"] for r in rs], [info[r]["y"] for r in rs], color=cm(sw*2), s=30)
        for r in rs: ax[1].text(info[r]["x"], info[r]["y"], str(sw), fontsize=7)
for a in ax:
    a.set_aspect("equal"); a.invert_yaxis(); a.add_patch(plt.Circle((0, 0), 19, fill=False))
plt.tight_layout(); plt.savefig(sys.argv[2], dpi=70)
