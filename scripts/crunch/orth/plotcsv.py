#!/usr/bin/env python3
import csv, sys, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = list(csv.DictReader(open(sys.argv[1])))
fig, ax = plt.subplots(figsize=(12, 12)); cm = plt.get_cmap("tab20")
g = {(int(r["driver"]), int(r["triplet"]), int(r["sw"])): (float(r["x_mm"]), float(r["y_mm"])) for r in R}
for (d, t, s), p in g.items():
    if (d, t, s+1) in g: q = g[(d, t, s+1)]; ax.plot([p[0], q[0]], [p[1], q[1]], "-", color=cm(t % 20), lw=3)
    if (d, t+1, s) in g: q = g[(d, t+1, s)]; ax.plot([p[0], q[0]], [p[1], q[1]], "-", color="#bbb", lw=1)
    ax.text(p[0], p[1], str(s), fontsize=7, ha="center", va="center")
ax.add_patch(plt.Circle((0, 0), 19, fill=False)); ax.set_aspect("equal"); ax.invert_yaxis()
for x, y in ((-11.4, 3.4), (10.6, 3.4), (-1.4, -6.6)): ax.plot(x, y, "ks", ms=14, alpha=.3)
plt.tight_layout(); plt.savefig(sys.argv[2], dpi=65)
