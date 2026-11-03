#!/usr/bin/env python3
"""gridmap.py IN_MAP.csv OUT_MAP.csv [--anneal N] [--wr W] : a true 13 x 9 row/column map on the existing sunflower sites.

Rows (one per triplet, F.Cu CS tracks) run E-W, in N-to-S order of triplet for U1 and S-to-N for U2, matching the drivers' clockwise CS pin order.
Columns (one per SW, In1) run N-S, W-to-E of SW for U1 and E-to-W for U2. LED sites do not change; only which LED sits at which site.
Writes the same columns as chip_lsa.csv."""
import argparse, csv, math, random
ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--anneal", type=int, default=400000); ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--wc", type=float, default=.5, help="weight of column links against row links")
ap.add_argument("--wb", type=float, default=2.0, help="weight of row bends")
ap.add_argument("--wsharp", type=float, default=4.0)
ap.add_argument("--split", type=float, default=None, help="x of the boundary line (default: median)")
a = ap.parse_args()
rows = list(csv.DictReader(open(a.inp)))
assert len(rows) == 234
sites = [(float(r["x_mm"]), float(r["y_mm"]), float(r["angle_deg"])) for r in rows]
byref = {(int(r["driver"]), int(r["triplet"]), int(r["sw"])): r["ref"] for r in rows}
sites.sort(key=lambda s: s[0])
half = {1: sites[:117], 2: sites[117:]}
rng = random.Random(a.seed)
def initial(drv):
    s = sorted(half[drv], key=lambda p: p[1] if drv == 1 else -p[1])   # N to S for U1, S to N for U2
    grid = {}
    for t in range(13):
        band = s[9*t:9*t+9]
        band.sort(key=lambda p: p[0] if drv == 1 else -p[0])
        for k, p in enumerate(band):
            grid[(t+1, k+1)] = p
    return grid
def nbrs(t, k):
    for dt, dk, w in ((1, 0, a.wc), (-1, 0, a.wc), (0, 1, 1), (0, -1, 1)):
        q = (t+dt, k+dk)
        if 1 <= q[0] <= 13 and 1 <= q[1] <= 9:
            yield q, w
def bend(g, c):
    """Row bend at c: 1 - cos of the turn, weighted; a straight row keeps its three tracks in one channel."""
    a_, b_ = (c[0], c[1]-1), (c[0], c[1]+1)
    if a_ not in g or b_ not in g: return 0
    p, q, r = g[a_], g[c], g[b_]
    u = (q[0]-p[0], q[1]-p[1]); v = (r[0]-q[0], r[1]-q[1]); n = math.hypot(*u)*math.hypot(*v) or 1
    c_ = (u[0]*v[0]+u[1]*v[1])/n
    return 1-c_ + (a.wsharp*(.25-c_) if c_ < .25 else 0)    # past 75 degrees no LED turn keeps the anode behind both links
def cost_at(g, c):
    p = g[c]; tot = 0
    for q, w in nbrs(*c):
        d2 = (p[0]-g[q][0])**2+(p[1]-g[q][1])**2
        tot += w*d2*d2/16      # quartic: long links are what block F.Cu
    for dk in (-1, 0, 1):
        tot += a.wb*bend(g, (c[0], c[1]+dk))
    return tot
def anneal(g):
    cells = list(g); T0, T1 = 3.0, .02
    near = {}
    for i in range(a.anneal):
        T = T0*(T1/T0)**(i/a.anneal)
        c = rng.choice(cells)
        dt, dk = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1), (2, 0), (-2, 0), (0, 2), (0, -2)])
        e = (c[0]+dt, c[1]+dk)
        if e not in g: continue
        b = cost_at(g, c)+cost_at(g, e)
        g[c], g[e] = g[e], g[c]
        n = cost_at(g, c)+cost_at(g, e)
        if n > b and rng.random() > math.exp((b-n)/T):
            g[c], g[e] = g[e], g[c]
    return g
out = []
import statistics as st
for drv in (1, 2):
    g = anneal(initial(drv))
    L = [math.hypot(g[(t, k)][0]-g[(t, k+1)][0], g[(t, k)][1]-g[(t, k+1)][1]) for t in range(1, 14) for k in range(1, 9)]
    C = [math.hypot(g[(t, k)][0]-g[(t+1, k)][0], g[(t, k)][1]-g[(t+1, k)][1]) for t in range(1, 13) for k in range(1, 10)]
    print(f"U{drv}: mean bend {sum(bend(g,c) for c in g)/len(g):.3f}; row links median {st.median(L):.2f} max {max(L):.2f} >2.8: {sum(l > 2.8 for l in L)}; col links median {st.median(C):.2f} max {max(C):.2f} >3.5: {sum(l > 3.5 for l in C)}")
    for (t, k), p in g.items():
        out.append(dict(ref=byref[(drv, t, k)], driver=drv, sw=k, triplet=t, x_mm=p[0], y_mm=p[1], angle_deg=p[2]))
out.sort(key=lambda r: int(r["ref"][1:]))
w = csv.DictWriter(open(a.out, "w", newline=""), fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
